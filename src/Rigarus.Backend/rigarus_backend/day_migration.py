"""Additive schema13; no legacy record or event is rewritten."""

DAY_DRAFTS = "20261124030000_AddDayDraftCompatibility"
DAY_TABLES = {"DayDraftAssignments", "DayDraftChanges", "DayDraftMembers"}

CREATE_DAY_DRAFTS = (
    """CREATE TABLE DayDraftAssignments (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        WorkItemId INTEGER NOT NULL REFERENCES WorkItems(Id) ON DELETE RESTRICT,
        CrewId INTEGER NOT NULL REFERENCES Crews(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL CHECK(length(LocalDate)=10 AND
            LocalDate GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND
            substr(LocalDate,1,4) BETWEEN '0001' AND '9999' AND
            LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days')),
        Notes TEXT NOT NULL CHECK(length(Notes)<=2000 AND instr(Notes,char(0))=0),
        Status TEXT NOT NULL CHECK(Status IN ('Draft','Cancelled')),
        Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
        CreatedAt TEXT NOT NULL, UpdatedAt TEXT NOT NULL
    )""",
    "CREATE UNIQUE INDEX IX_DayDraftAssignments_CrewDate ON DayDraftAssignments(CrewId,LocalDate) WHERE Status='Draft'",
    "CREATE INDEX IX_DayDraftAssignments_Date ON DayDraftAssignments(LocalDate,CrewId,Id)",
    """CREATE TABLE DayDraftChanges (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        AssignmentId INTEGER NOT NULL REFERENCES DayDraftAssignments(Id) ON DELETE RESTRICT,
        Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
        WorkItemId INTEGER NOT NULL REFERENCES WorkItems(Id) ON DELETE RESTRICT,
        CrewId INTEGER NOT NULL REFERENCES Crews(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL, Notes TEXT NOT NULL,
        Status TEXT NOT NULL CHECK(Status IN ('Draft','Cancelled')),
        StaffingConfigured INTEGER NOT NULL CHECK(StaffingConfigured IN (0,1)),
        RecordedAt TEXT NOT NULL, UNIQUE(AssignmentId,Revision)
    )""",
    """CREATE TABLE DayDraftMembers (
        ChangeId INTEGER NOT NULL REFERENCES DayDraftChanges(Id) ON DELETE RESTRICT,
        EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
        EmployeeName TEXT NOT NULL,
        HomeCrewId INTEGER NOT NULL REFERENCES Crews(Id) ON DELETE RESTRICT,
        PRIMARY KEY(ChangeId,EmployeeId)
    )""",
    "CREATE INDEX IX_DayDraftMembers_Employee ON DayDraftMembers(EmployeeId,ChangeId)",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} "
        "BEGIN SELECT RAISE(ABORT,'Day Draft history is immutable.'); END"
        for table in ("DayDraftChanges", "DayDraftMembers")
        for action in ("UPDATE", "DELETE")
    ),
    """CREATE TRIGGER DayDraftAssignments_NoDelete BEFORE DELETE ON DayDraftAssignments
    BEGIN SELECT RAISE(ABORT,'Cancel the Day Draft; preserve its identity.'); END""",
    *tuple(
        f"CREATE TRIGGER DayDraftAssignments_Legacy{action.title()} BEFORE {action} ON DayDraftAssignments "
        "WHEN NEW.Status='Draft' AND EXISTS(SELECT 1 FROM DraftAssignments "
        "WHERE CrewId=NEW.CrewId AND LocalDate=NEW.LocalDate AND Status='Draft') "
        "BEGIN SELECT RAISE(ABORT,'Legacy half-day occupancy requires review.'); END"
        for action in ("INSERT", "UPDATE")
    ),
    *tuple(
        f"CREATE TRIGGER DraftAssignments_Day{action.title()} BEFORE {action} ON DraftAssignments "
        "WHEN NEW.Status='Draft' AND EXISTS(SELECT 1 FROM DayDraftAssignments "
        "WHERE CrewId=NEW.CrewId AND LocalDate=NEW.LocalDate AND Status='Draft') "
        "BEGIN SELECT RAISE(ABORT,'Full-Day Crew occupancy conflict.'); END"
        for action in ("INSERT", "UPDATE")
    ),
)
