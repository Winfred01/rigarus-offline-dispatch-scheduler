"""Additive18: explicit full-day actual-worker consent and immutable history."""

from .daily_rig_migration import _date

DAILY_WEEKEND = "20261125030000_AddDailyWeekendConsent"
DAILY_WEEKEND_TABLES = {"WeekendConsentScopes", "WeekendConsentChanges"}
CREATE_DAILY_WEEKEND = (
    f"""CREATE TABLE WeekendConsentScopes (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      WorkItemId INTEGER NOT NULL REFERENCES WorkItems(Id) ON DELETE RESTRICT,
      ProjectId INTEGER NOT NULL REFERENCES Projects(Id) ON DELETE RESTRICT,
      CrewId INTEGER NOT NULL REFERENCES Crews(Id) ON DELETE RESTRICT,
      {_date("LocalDate")} CHECK(strftime('%w',LocalDate) IN ('0','6')),
      EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
      UNIQUE(WorkItemId,ProjectId,CrewId,LocalDate,EmployeeId)
    )""",
    """CREATE TABLE WeekendConsentChanges (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      ScopeId INTEGER NOT NULL REFERENCES WeekendConsentScopes(Id) ON DELETE RESTRICT,
      Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
      State TEXT NOT NULL CHECK(State IN ('Pending','Confirmed','Declined')),
      EmployeeDecisionConfirmed INTEGER NOT NULL CHECK(EmployeeDecisionConfirmed IN (0,1) AND (State='Pending' OR EmployeeDecisionConfirmed=1)),
      FullDayConfirmed INTEGER NOT NULL CHECK(FullDayConfirmed=1),
      RosterSnapshot TEXT NOT NULL CHECK(length(RosterSnapshot) BETWEEN 3 AND 25000 AND json_valid(RosterSnapshot)),
      RosterFingerprint TEXT NOT NULL CHECK(length(RosterFingerprint)=64 AND RosterFingerprint NOT GLOB '*[^0-9a-f]*'),
      SourceKind TEXT NOT NULL CHECK(SourceKind IN ('Proposed','FullDayDraft')),
      SourceAssignmentId INTEGER REFERENCES DayDraftAssignments(Id) ON DELETE RESTRICT,
      SourceRevision INTEGER,
      Reference TEXT NOT NULL CHECK(length(trim(Reference)) BETWEEN 1 AND 200 AND instr(Reference,char(0))=0),
      RecordedAt TEXT NOT NULL, UNIQUE(ScopeId,Revision),
      CHECK((SourceKind='Proposed' AND SourceAssignmentId IS NULL AND SourceRevision IS NULL) OR
            (SourceKind='FullDayDraft' AND SourceAssignmentId IS NOT NULL AND typeof(SourceRevision)='integer' AND SourceRevision>0))
    )""",
    "CREATE INDEX IX_WeekendConsentScopes_Date ON WeekendConsentScopes(LocalDate,WorkItemId)",
    """CREATE TRIGGER WeekendScopeContext BEFORE INSERT ON WeekendConsentScopes
      WHEN NOT EXISTS(SELECT 1 FROM WorkItems WHERE Id=NEW.WorkItemId AND ProjectId=NEW.ProjectId)
      BEGIN SELECT RAISE(ABORT,'Weekend parent context changed.'); END""",
    """CREATE TRIGGER WeekendConsentRevision BEFORE INSERT ON WeekendConsentChanges
      WHEN NEW.Revision != coalesce((SELECT max(Revision) FROM WeekendConsentChanges WHERE ScopeId=NEW.ScopeId),0)+1
      BEGIN SELECT RAISE(ABORT,'Weekend consent revision changed.'); END""",
    """CREATE TRIGGER WeekendConsentRoster BEFORE INSERT ON WeekendConsentChanges
      WHEN json_type(NEW.RosterSnapshot)!='array'
        OR json_array_length(NEW.RosterSnapshot) NOT BETWEEN 1 AND 1000
        OR EXISTS(SELECT 1 FROM json_each(NEW.RosterSnapshot) WHERE type!='integer' OR value<=0
           OR NOT EXISTS(SELECT 1 FROM Employees WHERE Id=value))
        OR (SELECT count(DISTINCT value) FROM json_each(NEW.RosterSnapshot))!=json_array_length(NEW.RosterSnapshot)
        OR NOT EXISTS(SELECT 1 FROM json_each(NEW.RosterSnapshot) j JOIN WeekendConsentScopes s ON s.Id=NEW.ScopeId WHERE j.value=s.EmployeeId)
      BEGIN SELECT RAISE(ABORT,'Explicit weekend roster is invalid.'); END""",
    """CREATE TRIGGER WeekendConsentSavedContext BEFORE INSERT ON WeekendConsentChanges
      WHEN NEW.SourceKind='FullDayDraft' AND NOT EXISTS(
        SELECT 1 FROM DayDraftAssignments a JOIN WorkItems w ON w.Id=a.WorkItemId
        JOIN WeekendConsentScopes s ON s.Id=NEW.ScopeId
        WHERE a.Id=NEW.SourceAssignmentId AND a.Revision=NEW.SourceRevision AND a.Status='Draft'
        AND a.WorkItemId=s.WorkItemId AND w.ProjectId=s.ProjectId AND a.CrewId=s.CrewId AND a.LocalDate=s.LocalDate
        AND EXISTS(SELECT 1 FROM DayDraftChanges d WHERE d.AssignmentId=a.Id AND d.Revision=a.Revision AND d.StaffingConfigured=1
          AND (SELECT count(*) FROM DayDraftMembers WHERE ChangeId=d.Id)=json_array_length(NEW.RosterSnapshot)
          AND NOT EXISTS(SELECT 1 FROM DayDraftMembers m WHERE m.ChangeId=d.Id AND m.EmployeeId NOT IN (SELECT value FROM json_each(NEW.RosterSnapshot)))))
      BEGIN SELECT RAISE(ABORT,'Saved weekend context changed.'); END""",
    *tuple(
        f"""CREATE TRIGGER {table}_{action}_Immutable BEFORE {action} ON {table}
       BEGIN SELECT RAISE(ABORT,'Weekend consent history is immutable.'); END"""
        for table in ("WeekendConsentScopes", "WeekendConsentChanges")
        for action in ("UPDATE", "DELETE")
    ),
)
