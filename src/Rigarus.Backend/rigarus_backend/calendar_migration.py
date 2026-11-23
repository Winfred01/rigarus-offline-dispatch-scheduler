"""Additive schema ten; original records are never rewritten."""

WORKING_CALENDARS = "20261123020000_AddWorkingCalendars"
CALENDAR_TABLES = {"WorkingCalendars", "WorkingCalendarChanges", "WorkingCalendarCells"}

CREATE_WORKING_CALENDARS = (
    """CREATE TABLE WorkingCalendars (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        CrewId INTEGER UNIQUE REFERENCES Crews(Id) ON DELETE RESTRICT,
        ProjectId INTEGER UNIQUE REFERENCES Projects(Id) ON DELETE RESTRICT,
        CHECK ((CrewId IS NOT NULL AND ProjectId IS NULL) OR
               (CrewId IS NULL AND ProjectId IS NOT NULL))
    )""",
    """CREATE TABLE WorkingCalendarChanges (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        CalendarId INTEGER NOT NULL REFERENCES WorkingCalendars(Id) ON DELETE RESTRICT,
        Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
        StartDate TEXT NOT NULL CHECK(length(StartDate)=10 AND StartDate IS strftime('%Y-%m-%d',StartDate,'+0 days') AND substr(StartDate,1,4) BETWEEN '0001' AND '9999'),
        EndDate TEXT NOT NULL CHECK(length(EndDate)=10 AND EndDate IS strftime('%Y-%m-%d',EndDate,'+0 days') AND substr(EndDate,1,4) BETWEEN '0001' AND '9999' AND EndDate>=StartDate),
        Slot TEXT NOT NULL CHECK(Slot IN ('FullDay','AM','PM')),
        State TEXT NOT NULL CHECK(State IN ('Working','NotWorking','Unknown')),
        RecordedAt TEXT NOT NULL,
        UNIQUE(CalendarId,Revision), UNIQUE(Id,CalendarId)
    )""",
    """CREATE TABLE WorkingCalendarCells (
        CalendarId INTEGER NOT NULL REFERENCES WorkingCalendars(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL CHECK(length(LocalDate)=10 AND LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days') AND substr(LocalDate,1,4) BETWEEN '0001' AND '9999'),
        Slot TEXT NOT NULL CHECK(Slot IN ('AM','PM')),
        State TEXT NOT NULL CHECK(State IN ('Working','NotWorking')),
        ChangeId INTEGER NOT NULL,
        PRIMARY KEY(CalendarId,LocalDate,Slot),
        FOREIGN KEY(ChangeId,CalendarId) REFERENCES WorkingCalendarChanges(Id,CalendarId) ON DELETE RESTRICT
    )""",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} "
        "BEGIN SELECT RAISE(ABORT,'Working calendar ownership/history is immutable.'); END"
        for table in ("WorkingCalendars", "WorkingCalendarChanges")
        for action in ("UPDATE", "DELETE")
    ),
)
