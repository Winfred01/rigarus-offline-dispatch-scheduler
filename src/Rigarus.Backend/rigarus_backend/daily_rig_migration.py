"""Additive17: explicit actual vehicles, independent condition periods and guards."""

DAILY_RIGS = "20261125020000_AddDailyRigs"
DAILY_RIG_TABLES = {
    "RigAllocations",
    "RigAllocationChanges",
    "RigConditionPeriods",
    "RigConditionChanges",
}


def _date(column):
    return f"{column} TEXT NOT NULL CHECK(length({column})=10 AND substr({column},1,4) BETWEEN '0001' AND '9999' AND {column} IS strftime('%Y-%m-%d',{column},'+0 days'))"


CREATE_DAILY_RIGS = (
    """CREATE TABLE RigConditionPeriods (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      RigId INTEGER NOT NULL REFERENCES Rigs(Id) ON DELETE RESTRICT,
      Kind TEXT NOT NULL CHECK(Kind IN ('Maintenance','Inspection','OutOfService'))
    )""",
    f"""CREATE TABLE RigConditionChanges (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      PeriodId INTEGER NOT NULL REFERENCES RigConditionPeriods(Id) ON DELETE RESTRICT,
      Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
      {_date("StartDate")}, {_date("EndDate")} CHECK(EndDate>=StartDate),
      Status TEXT NOT NULL CHECK(Status IN ('Active','Cancelled')),
      CompanyConfirmed INTEGER NOT NULL CHECK(CompanyConfirmed=1),
      Reference TEXT NOT NULL CHECK(length(trim(Reference)) BETWEEN 1 AND 200 AND instr(Reference,char(0))=0),
      RecordedAt TEXT NOT NULL, UNIQUE(PeriodId,Revision)
    )""",
    """CREATE TABLE RigAllocations (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      DayAssignmentId INTEGER UNIQUE REFERENCES DayDraftAssignments(Id) ON DELETE RESTRICT,
      LegacyAssignmentId INTEGER UNIQUE REFERENCES DraftAssignments(Id) ON DELETE RESTRICT,
      CHECK((DayAssignmentId IS NOT NULL)+(LegacyAssignmentId IS NOT NULL)=1)
    )""",
    f"""CREATE TABLE RigAllocationChanges (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      AllocationId INTEGER NOT NULL REFERENCES RigAllocations(Id) ON DELETE RESTRICT,
      Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
      AssignmentRevision INTEGER NOT NULL CHECK(typeof(AssignmentRevision)='integer' AND AssignmentRevision>0),
      WorkItemId INTEGER NOT NULL REFERENCES WorkItems(Id) ON DELETE RESTRICT,
      ProjectId INTEGER NOT NULL REFERENCES Projects(Id) ON DELETE RESTRICT,
      CrewId INTEGER NOT NULL REFERENCES Crews(Id) ON DELETE RESTRICT,
      {_date("LocalDate")},
      OriginalRigId INTEGER REFERENCES Rigs(Id) ON DELETE RESTRICT,
      ActualRigId INTEGER REFERENCES Rigs(Id) ON DELETE RESTRICT,
      OperationalConfirmed INTEGER NOT NULL CHECK(OperationalConfirmed IN (0,1) AND (OperationalConfirmed=0 OR ActualRigId IS NOT NULL)),
      ConditionRevision INTEGER NOT NULL CHECK(typeof(ConditionRevision)='integer' AND ConditionRevision>=0),
      CompanyConfirmed INTEGER NOT NULL CHECK(CompanyConfirmed=1),
      FullDayConfirmed INTEGER NOT NULL CHECK(FullDayConfirmed IN (0,1)),
      Reference TEXT NOT NULL CHECK(length(trim(Reference)) BETWEEN 1 AND 200 AND instr(Reference,char(0))=0),
      RecordedAt TEXT NOT NULL, UNIQUE(AllocationId,Revision)
    )""",
    "CREATE INDEX IX_RigConditionPeriods_Rig ON RigConditionPeriods(RigId,Id)",
    "CREATE INDEX IX_RigAllocationChanges_ActualRig ON RigAllocationChanges(ActualRigId,AllocationId,Revision)",
    """CREATE VIEW RigCurrentConditions AS SELECT p.Id,p.RigId,p.Kind,h.Id AS ChangeId,h.Revision,h.StartDate,h.EndDate,h.Status,h.Reference
       FROM RigConditionPeriods p JOIN RigConditionChanges h ON h.PeriodId=p.Id
       WHERE h.Revision=(SELECT max(Revision) FROM RigConditionChanges WHERE PeriodId=p.Id)""",
    """CREATE VIEW RigAssignmentContexts AS
       SELECT 'FullDayDraft' AS RecordKind,a.Id AS AssignmentId,a.WorkItemId,w.ProjectId,a.CrewId,a.LocalDate,a.Revision,a.Status,NULL AS Slot
       FROM DayDraftAssignments a JOIN WorkItems w ON w.Id=a.WorkItemId
       UNION ALL
       SELECT 'LegacyHalfDay',a.Id,a.WorkItemId,w.ProjectId,a.CrewId,a.LocalDate,a.Revision,a.Status,a.Slot
       FROM DraftAssignments a JOIN WorkItems w ON w.Id=a.WorkItemId""",
    """CREATE VIEW RigCurrentAllocations AS
       SELECT o.Id AS AllocationId,v.RecordKind,v.AssignmentId,v.WorkItemId,v.ProjectId,v.CrewId,v.LocalDate,v.Revision AS AssignmentRevision,v.Status,v.Slot,
         h.Id AS ChangeId,h.Revision,h.AssignmentRevision AS RecordedRevision,h.WorkItemId AS RecordedWorkItemId,h.ProjectId AS RecordedProjectId,
         h.CrewId AS RecordedCrewId,h.LocalDate AS RecordedDate,h.OriginalRigId,h.ActualRigId,h.OperationalConfirmed,h.ConditionRevision,h.FullDayConfirmed,h.Reference
       FROM RigAllocations o JOIN RigAssignmentContexts v ON v.RecordKind=CASE WHEN o.DayAssignmentId IS NOT NULL THEN 'FullDayDraft' ELSE 'LegacyHalfDay' END
         AND v.AssignmentId=coalesce(o.DayAssignmentId,o.LegacyAssignmentId)
       JOIN RigAllocationChanges h ON h.AllocationId=o.Id
       WHERE h.Revision=(SELECT max(Revision) FROM RigAllocationChanges WHERE AllocationId=o.Id)""",
    """CREATE VIEW RigDailyOccupancy AS
       SELECT AllocationId,ActualRigId AS RigId,CrewId,LocalDate FROM RigCurrentAllocations WHERE Status='Draft' AND ActualRigId IS NOT NULL
       UNION
       SELECT AllocationId,ActualRigId,RecordedCrewId,RecordedDate FROM RigCurrentAllocations WHERE Status='Draft' AND ActualRigId IS NOT NULL""",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Rig ownership/history is immutable.'); END"
        for table in (
            "RigConditionPeriods",
            "RigConditionChanges",
            "RigAllocations",
            "RigAllocationChanges",
        )
        for action in ("UPDATE", "DELETE")
    ),
    """CREATE TRIGGER RigAllocationChanges_Context BEFORE INSERT ON RigAllocationChanges
       WHEN NOT EXISTS(SELECT 1 FROM RigAllocations o JOIN RigAssignmentContexts v
        ON v.RecordKind=CASE WHEN o.DayAssignmentId IS NOT NULL THEN 'FullDayDraft' ELSE 'LegacyHalfDay' END AND v.AssignmentId=coalesce(o.DayAssignmentId,o.LegacyAssignmentId)
        WHERE o.Id=NEW.AllocationId AND v.Status='Draft' AND v.Revision=NEW.AssignmentRevision AND v.WorkItemId=NEW.WorkItemId AND v.ProjectId=NEW.ProjectId
         AND v.CrewId=NEW.CrewId AND v.LocalDate=NEW.LocalDate AND NEW.FullDayConfirmed=CASE WHEN o.DayAssignmentId IS NOT NULL THEN 1 ELSE 0 END
         AND (v.RecordKind='FullDayDraft' OR NEW.OperationalConfirmed=0))
       BEGIN SELECT RAISE(ABORT,'Rig allocation context changed.'); END""",
    """CREATE TRIGGER RigAllocationChanges_Original BEFORE INSERT ON RigAllocationChanges
       WHEN EXISTS(SELECT 1 FROM RigAllocationChanges WHERE AllocationId=NEW.AllocationId AND OriginalRigId IS NOT NULL)
        AND NEW.OriginalRigId IS NOT (SELECT OriginalRigId FROM RigAllocationChanges WHERE AllocationId=NEW.AllocationId AND OriginalRigId IS NOT NULL ORDER BY Revision LIMIT 1)
       BEGIN SELECT RAISE(ABORT,'Retain the original Rig identity.'); END""",
    """CREATE TRIGGER RigAllocationChanges_Collision BEFORE INSERT ON RigAllocationChanges
       WHEN NEW.ActualRigId IS NOT NULL AND EXISTS(SELECT 1 FROM RigDailyOccupancy x
         WHERE x.RigId=NEW.ActualRigId AND x.LocalDate=NEW.LocalDate AND x.CrewId<>NEW.CrewId AND x.AllocationId<>NEW.AllocationId)
       BEGIN SELECT RAISE(ABORT,'Rig already occupies this date for another Crew.'); END""",
    """CREATE TRIGGER RigAllocationChanges_Readiness BEFORE INSERT ON RigAllocationChanges
       WHEN NEW.ConditionRevision<>coalesce((SELECT max(h.Id) FROM RigConditionChanges h JOIN RigConditionPeriods p ON p.Id=h.PeriodId WHERE p.RigId=NEW.ActualRigId),0)
        OR (NEW.OperationalConfirmed=1 AND (
          NOT EXISTS(SELECT 1 FROM Rigs WHERE Id=NEW.ActualRigId AND Active=1)
          OR EXISTS(SELECT 1 FROM RigCurrentConditions WHERE RigId=NEW.ActualRigId AND Status='Active' AND NEW.LocalDate BETWEEN StartDate AND EndDate)))
       BEGIN SELECT RAISE(ABORT,'Rig operational evidence is stale or blocked.'); END""",
    *tuple(
        f"""CREATE TRIGGER {table}_RigMove BEFORE UPDATE ON {table}
       WHEN NEW.Status='Draft' AND EXISTS(SELECT 1 FROM RigCurrentAllocations own JOIN RigDailyOccupancy other ON other.RigId=own.ActualRigId
         WHERE own.RecordKind='{kind}' AND own.AssignmentId=OLD.Id AND other.AllocationId<>own.AllocationId AND other.CrewId<>NEW.CrewId AND other.LocalDate=NEW.LocalDate)
       BEGIN SELECT RAISE(ABORT,'Rig already occupies this date for another Crew.'); END"""
        for table, kind in (
            ("DayDraftAssignments", "FullDayDraft"),
            ("DraftAssignments", "LegacyHalfDay"),
        )
    ),
)
