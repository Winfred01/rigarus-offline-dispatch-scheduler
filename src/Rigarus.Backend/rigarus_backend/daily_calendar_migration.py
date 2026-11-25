"""Additive schema14. Legacy evidence/history and all saved visits stay untouched."""

DAILY_CALENDARS = "20261124040000_AddDailyCalendars"
DAILY_TABLES = {"DailyCalendarOwners", "DailyCalendarChanges", "DailyCalendarCells"}

CREATE_DAILY_CALENDARS = (
    """CREATE TABLE DailyCalendarOwners (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        CrewId INTEGER UNIQUE REFERENCES Crews(Id) ON DELETE RESTRICT,
        ProjectId INTEGER UNIQUE REFERENCES Projects(Id) ON DELETE RESTRICT,
        EmployeeId INTEGER UNIQUE REFERENCES Employees(Id) ON DELETE RESTRICT,
        CHECK((CrewId IS NOT NULL)+(ProjectId IS NOT NULL)+(EmployeeId IS NOT NULL)=1)
    )""",
    """CREATE TABLE DailyCalendarChanges (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        OwnerId INTEGER NOT NULL REFERENCES DailyCalendarOwners(Id) ON DELETE RESTRICT,
        Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
        StartDate TEXT NOT NULL CHECK(length(StartDate)=10 AND substr(StartDate,1,4) BETWEEN '0001' AND '9999' AND StartDate IS strftime('%Y-%m-%d',StartDate,'+0 days')),
        EndDate TEXT NOT NULL CHECK(length(EndDate)=10 AND substr(EndDate,1,4) BETWEEN '0001' AND '9999' AND EndDate IS strftime('%Y-%m-%d',EndDate,'+0 days') AND EndDate>=StartDate),
        State TEXT NOT NULL CHECK(State IN ('Working','NotWorking','Available','Unavailable','Unknown')),
        OperatorConfirmed INTEGER NOT NULL CHECK(OperatorConfirmed=1),
        LegacyReviewed INTEGER NOT NULL CHECK(LegacyReviewed IN (0,1)),
        LegacyRevision INTEGER NOT NULL CHECK(typeof(LegacyRevision)='integer' AND LegacyRevision>=0),
        LegacySnapshot TEXT NOT NULL CHECK(length(LegacySnapshot)<=250000),
        Notes TEXT NOT NULL CHECK(length(Notes)<=2000 AND instr(Notes,char(0))=0),
        RecordedAt TEXT NOT NULL, UNIQUE(OwnerId,Revision), UNIQUE(Id,OwnerId,State)
    )""",
    """CREATE TABLE DailyCalendarCells (
        OwnerId INTEGER NOT NULL REFERENCES DailyCalendarOwners(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL CHECK(length(LocalDate)=10 AND substr(LocalDate,1,4) BETWEEN '0001' AND '9999' AND LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days')),
        State TEXT NOT NULL,
        ChangeId INTEGER NOT NULL,
        LegacyFingerprint TEXT NOT NULL CHECK(length(LegacyFingerprint)=64 AND LegacyFingerprint NOT GLOB '*[^0-9a-f]*'),
        PRIMARY KEY(OwnerId,LocalDate),
        FOREIGN KEY(ChangeId,OwnerId,State) REFERENCES DailyCalendarChanges(Id,OwnerId,State) ON DELETE RESTRICT
    )""",
    "CREATE INDEX IX_DailyCalendarCells_Date ON DailyCalendarCells(LocalDate,OwnerId)",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} "
        "BEGIN SELECT RAISE(ABORT,'Daily calendar ownership/history is immutable.'); END"
        for table in ("DailyCalendarOwners", "DailyCalendarChanges")
        for action in ("UPDATE", "DELETE")
    ),
    """CREATE TRIGGER DailyCalendarChanges_Scope BEFORE INSERT ON DailyCalendarChanges
        WHEN EXISTS(SELECT 1 FROM DailyCalendarOwners o WHERE o.Id=NEW.OwnerId AND
          ((o.EmployeeId IS NULL AND NEW.State NOT IN ('Working','NotWorking','Unknown')) OR
           (o.EmployeeId IS NOT NULL AND NEW.State NOT IN ('Available','Unavailable','Unknown'))))
        BEGIN SELECT RAISE(ABORT,'Daily state does not match owner scope.'); END""",
    *tuple(
        f"CREATE TRIGGER DailyCalendarCells_Context{action.title()} BEFORE {action} ON DailyCalendarCells "
        "WHEN NOT EXISTS(SELECT 1 FROM DailyCalendarChanges h WHERE h.Id=NEW.ChangeId AND h.OwnerId=NEW.OwnerId AND h.State=NEW.State AND NEW.LocalDate BETWEEN h.StartDate AND h.EndDate) "
        "BEGIN SELECT RAISE(ABORT,'Daily cell history context mismatch.'); END"
        for action in ("INSERT", "UPDATE")
    ),
)
