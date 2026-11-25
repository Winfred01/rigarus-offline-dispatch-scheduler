import sqlite3
from contextlib import closing
from pathlib import Path

from .domain import DemoProject, validate_note
from .day_migration import DAY_DRAFTS, DAY_TABLES, CREATE_DAY_DRAFTS
from .daily_driver_migration import (
    DAILY_DRIVERS,
    DAILY_DRIVER_TABLES,
    CREATE_DAILY_DRIVERS,
)
from .day_backup import verified_upgrade_backup
from .daily_calendar_migration import (
    DAILY_CALENDARS,
    DAILY_TABLES,
    CREATE_DAILY_CALENDARS,
)
from .calendar_migration import (
    WORKING_CALENDARS,
    CALENDAR_TABLES,
    CREATE_WORKING_CALENDARS,
)

from .driver_migration import DRIVER_APPROVALS, DRIVER_TABLES, CREATE_DRIVER_APPROVALS

from .capability_migration import (
    CAPABILITY_EVIDENCE,
    CAPABILITY_TABLES,
    CREATE_CAPABILITY_EVIDENCE,
)

INITIAL_DEMO = "20261112045924_InitialDemo"
PROJECT_MASTER = "20261112072258_AddProjectsAndWorkItems"
CREW_ROSTER = "20261115031137_AddCrewRoster"
EMPLOYEE_ROSTER = "20261115130213_AddEmployeeRoster"
RIG_INVENTORY = "20261119130000_AddRigInventory"
FOREMAN_HISTORY = "20261122030000_AddForemanHistory"
DRAFT_ASSIGNMENTS = "20261122040000_AddDraftAssignments"
ASSIGNMENT_STAFFING = "20261122200000_AddAssignmentStaffing"
EMPLOYEE_AVAILABILITY = "20261123010000_AddEmployeeAvailability"
EF_VERSION = "10.0.15"

# Keep the on-disk format compatible with the two released EF Core migrations.
CREATE_PROJECT_MASTER = (
    """
    CREATE TABLE Projects (
        Id INTEGER NOT NULL CONSTRAINT PK_Projects PRIMARY KEY AUTOINCREMENT,
        JobNumber TEXT COLLATE NOCASE NOT NULL,
        SiteId TEXT NOT NULL,
        SiteName TEXT NOT NULL,
        CONSTRAINT CK_Projects_JobNumber CHECK (length(JobNumber) > 0 AND JobNumber = trim(JobNumber)),
        CONSTRAINT CK_Projects_SiteId CHECK (length(trim(SiteId)) > 0),
        CONSTRAINT CK_Projects_SiteName CHECK (length(trim(SiteName)) > 0)
    )
    """,
    """
    CREATE TABLE WorkItems (
        Id INTEGER NOT NULL CONSTRAINT PK_WorkItems PRIMARY KEY AUTOINCREMENT,
        ProjectId INTEGER NOT NULL,
        Type TEXT NOT NULL,
        RequiredCrewCount INTEGER NOT NULL,
        EstimatedHalfDays INTEGER NOT NULL,
        CONSTRAINT CK_WorkItems_EstimatedHalfDays
            CHECK (typeof(EstimatedHalfDays) = 'integer' AND EstimatedHalfDays BETWEEN 1 AND 2147483647),
        CONSTRAINT CK_WorkItems_RequiredCrewCount
            CHECK (typeof(RequiredCrewCount) = 'integer' AND RequiredCrewCount BETWEEN 1 AND 2147483647),
        CONSTRAINT CK_WorkItems_Type CHECK (Type IN ('Small', 'Civil', 'Tower', 'Other')),
        CONSTRAINT FK_WorkItems_Projects_ProjectId FOREIGN KEY (ProjectId) REFERENCES Projects (Id) ON DELETE RESTRICT
    )
    """,
    "CREATE UNIQUE INDEX IX_Projects_JobNumber ON Projects (JobNumber)",
    "CREATE INDEX IX_WorkItems_ProjectId ON WorkItems (ProjectId)",
)


PROJECT_TABLES = {"__EFMigrationsHistory", "DemoProjects", "Projects", "WorkItems"}
CREW_TABLES = PROJECT_TABLES | {"Crews"}
CREW_HISTORY = (INITIAL_DEMO, PROJECT_MASTER, CREW_ROSTER)
CREATE_CREWS = """
    CREATE TABLE Crews (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL CHECK (length(trim(Name)) BETWEEN 1 AND 100),
        Type TEXT NOT NULL CHECK (Type IN ('Civil', 'Tower')),
        Active INTEGER NOT NULL CHECK (Active IN (0, 1))
    )
"""


CREATE_EMPLOYEES = """
    CREATE TABLE Employees (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL CHECK (length(trim(Name)) BETWEEN 1 AND 100),
        HomeCrewId INTEGER NOT NULL REFERENCES Crews (Id) ON DELETE RESTRICT,
        SkillLevel INTEGER NOT NULL CHECK (typeof(SkillLevel) = 'integer' AND SkillLevel BETWEEN 1 AND 3),
        ForemanEligible INTEGER NOT NULL CHECK (ForemanEligible IN (0, 1)),
        Active INTEGER NOT NULL CHECK (Active IN (0, 1)),
        DriverStatus TEXT NOT NULL DEFAULT 'Unverified' CHECK (DriverStatus = 'Unverified')
    )
"""

CREATE_RIGS = """
    CREATE TABLE Rigs (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Number TEXT COLLATE NOCASE NOT NULL CHECK (length(Number) BETWEEN 1 AND 50 AND Number = trim(Number)),
        Type TEXT NOT NULL CHECK (length(trim(Type)) BETWEEN 1 AND 100),
        Notes TEXT NOT NULL CHECK (length(Notes) <= 2000),
        DefaultCrewId INTEGER REFERENCES Crews (Id) ON DELETE RESTRICT,
        Active INTEGER NOT NULL CHECK (Active IN (0, 1))
    )
"""


class UnsupportedDatabaseError(RuntimeError):
    """The database needs review before the application can open it."""


CREATE_FOREMAN_HISTORY = (
    """
    CREATE TABLE ForemanChanges (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        CrewId INTEGER NOT NULL REFERENCES Crews (Id) ON DELETE RESTRICT,
        EmployeeId INTEGER REFERENCES Employees (Id) ON DELETE RESTRICT,
        CrewName TEXT NOT NULL,
        EmployeeName TEXT,
        RecordedAt TEXT NOT NULL,
        CHECK ((EmployeeId IS NULL AND EmployeeName IS NULL)
            OR (EmployeeId IS NOT NULL AND EmployeeName IS NOT NULL))
    )
    """,
    "CREATE INDEX IX_ForemanChanges_CrewId_Id ON ForemanChanges (CrewId, Id)",
    """
    CREATE TRIGGER ForemanChanges_NoUpdate BEFORE UPDATE ON ForemanChanges
    BEGIN SELECT RAISE(ABORT, 'Foreman history is append-only.'); END
    """,
    """
    CREATE TRIGGER ForemanChanges_NoDelete BEFORE DELETE ON ForemanChanges
    BEGIN SELECT RAISE(ABORT, 'Foreman history is append-only.'); END
    """,
)

CREATE_DRAFT_ASSIGNMENTS = (
    """
    CREATE TABLE DraftAssignments (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        WorkItemId INTEGER NOT NULL REFERENCES WorkItems (Id) ON DELETE RESTRICT,
        CrewId INTEGER NOT NULL REFERENCES Crews (Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL CHECK (
            length(LocalDate) = 10 AND LocalDate GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
            AND substr(LocalDate, 1, 4) BETWEEN '0001' AND '9999'
            AND LocalDate IS strftime('%Y-%m-%d', LocalDate, '+0 days')),
        Slot TEXT NOT NULL CHECK (Slot IN ('AM', 'PM')),
        Notes TEXT NOT NULL CHECK (length(Notes) <= 2000 AND instr(Notes, char(0)) = 0),
        Status TEXT NOT NULL CHECK (Status IN ('Draft', 'Cancelled')),
        Revision INTEGER NOT NULL CHECK (typeof(Revision) = 'integer' AND Revision >= 1),
        CreatedAt TEXT NOT NULL,
        UpdatedAt TEXT NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX IX_DraftAssignments_CrewSlot ON DraftAssignments (CrewId, LocalDate, Slot) WHERE Status = 'Draft'",
    "CREATE INDEX IX_DraftAssignments_LocalDate ON DraftAssignments (LocalDate, Slot, CrewId, Id)",
    "CREATE INDEX IX_DraftAssignments_WorkItemId ON DraftAssignments (WorkItemId)",
)


CREATE_ASSIGNMENT_STAFFING = (
    """CREATE TABLE AssignmentStaffingChanges (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        AssignmentId INTEGER NOT NULL REFERENCES DraftAssignments(Id) ON DELETE RESTRICT,
        AssignmentRevision INTEGER NOT NULL CHECK (AssignmentRevision > 0),
        WorkItemId INTEGER NOT NULL REFERENCES WorkItems(Id) ON DELETE RESTRICT,
        CrewId INTEGER NOT NULL REFERENCES Crews(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL,
        Slot TEXT NOT NULL CHECK (Slot IN ('AM', 'PM')),
        Configured INTEGER NOT NULL CHECK (Configured IN (0, 1)),
        RecordedAt TEXT NOT NULL,
        UNIQUE (AssignmentId, AssignmentRevision)
    )""",
    "CREATE INDEX IX_AssignmentStaffingChanges_AssignmentId_Id ON AssignmentStaffingChanges(AssignmentId, Id)",
    """CREATE TABLE AssignmentStaffingMembers (
        ChangeId INTEGER NOT NULL REFERENCES AssignmentStaffingChanges(Id) ON DELETE RESTRICT,
        EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
        EmployeeName TEXT NOT NULL,
        HomeCrewId INTEGER NOT NULL REFERENCES Crews(Id) ON DELETE RESTRICT,
        PRIMARY KEY (ChangeId, EmployeeId)
    )""",
    "CREATE INDEX IX_AssignmentStaffingMembers_EmployeeId ON AssignmentStaffingMembers(EmployeeId, ChangeId)",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'Staffing history is append-only.'); END"
        for table in ("AssignmentStaffingChanges", "AssignmentStaffingMembers")
        for action in ("UPDATE", "DELETE")
    ),
)


CREATE_EMPLOYEE_AVAILABILITY = (
    """CREATE TABLE EmployeeAvailabilityChanges (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
        Revision INTEGER NOT NULL CHECK (typeof(Revision)='integer' AND Revision>0),
        StartDate TEXT NOT NULL CHECK (length(StartDate)=10 AND StartDate IS strftime('%Y-%m-%d',StartDate,'+0 days') AND substr(StartDate,1,4) BETWEEN '0001' AND '9999'),
        EndDate TEXT NOT NULL CHECK (length(EndDate)=10 AND EndDate IS strftime('%Y-%m-%d',EndDate,'+0 days') AND substr(EndDate,1,4) BETWEEN '0001' AND '9999' AND EndDate>=StartDate),
        Slot TEXT NOT NULL CHECK (Slot IN ('FullDay','AM','PM')),
        State TEXT NOT NULL CHECK (State IN ('Available','Unavailable','Unknown')),
        RecordedAt TEXT NOT NULL,
        UNIQUE(EmployeeId,Revision), UNIQUE(Id,EmployeeId)
    )""",
    """CREATE TABLE EmployeeAvailability (
        EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL CHECK (length(LocalDate)=10 AND LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days') AND substr(LocalDate,1,4) BETWEEN '0001' AND '9999'),
        Slot TEXT NOT NULL CHECK (Slot IN ('AM','PM')),
        State TEXT NOT NULL CHECK (State IN ('Available','Unavailable')),
        ChangeId INTEGER NOT NULL,
        PRIMARY KEY(EmployeeId,LocalDate,Slot),
        FOREIGN KEY(ChangeId,EmployeeId) REFERENCES EmployeeAvailabilityChanges(Id,EmployeeId) ON DELETE RESTRICT
    )""",
    "CREATE INDEX IX_EmployeeAvailability_DateSlot ON EmployeeAvailability(LocalDate,Slot,EmployeeId)",
    *tuple(
        f"CREATE TRIGGER EmployeeAvailabilityChanges_No{action.title()} BEFORE {action} ON EmployeeAvailabilityChanges "
        "BEGIN SELECT RAISE(ABORT,'Availability history is append-only.'); END"
        for action in ("UPDATE", "DELETE")
    ),
)


def connect(
    path: Path, *, create: bool = False, read_only: bool = False
) -> sqlite3.Connection:
    if create and read_only:
        raise ValueError("A read-only connection cannot create a database.")
    mode = "ro" if read_only else "rw"
    location = path if create else f"{path.resolve().as_uri()}?mode={mode}"
    connection = sqlite3.connect(
        location,
        uri=not create,
        timeout=5,
        autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL,
    )
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        if read_only:
            connection.execute("PRAGMA query_only = ON")
    except BaseException:
        connection.close()
        raise
    return connection


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.is_file() and path.stat().st_size > 0
    with closing(connect(path, create=True)) as connection:
        # Acquire the write reservation before reading migration history.
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            tables = {
                name
                for (name,) in connection.execute(
                    "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT GLOB 'sqlite_*'"
                )
            }
            if not tables:
                create_demo_schema(connection)
                tables = {"__EFMigrationsHistory", "DemoProjects"}
            if "__EFMigrationsHistory" not in tables:
                raise UnsupportedDatabaseError(
                    "This file is not a recognized Rigarus database."
                )

            history = tuple(
                row[0]
                for row in connection.execute(
                    "SELECT MigrationId FROM __EFMigrationsHistory ORDER BY MigrationId"
                )
            )
            previous = (
                *CREW_HISTORY,
                EMPLOYEE_ROSTER,
                RIG_INVENTORY,
                FOREMAN_HISTORY,
                DRAFT_ASSIGNMENTS,
                ASSIGNMENT_STAFFING,
                EMPLOYEE_AVAILABILITY,
                WORKING_CALENDARS,
                DRIVER_APPROVALS,
                CAPABILITY_EVIDENCE,
                DAY_DRAFTS,
                DAILY_CALENDARS,
            )
            if (
                existing
                and history
                and history in tuple(previous[:i] for i in range(1, len(previous) + 1))
            ):
                # No DDL has run. The write reservation prevents a newer commit
                # from falling between the verified recovery point and upgrade.
                verified_upgrade_backup(path)
            if history == (INITIAL_DEMO,) and tables == {
                "__EFMigrationsHistory",
                "DemoProjects",
            }:
                for statement in CREATE_PROJECT_MASTER:
                    connection.execute(statement)
                record_migration(connection, PROJECT_MASTER)
                history = (INITIAL_DEMO, PROJECT_MASTER)
                tables = PROJECT_TABLES

            if history == (INITIAL_DEMO, PROJECT_MASTER) and tables == PROJECT_TABLES:
                connection.execute(CREATE_CREWS)
                record_migration(
                    connection, CREW_ROSTER, product_version="Rigarus 0.1.0"
                )
                history = CREW_HISTORY
                tables = CREW_TABLES

            if history == CREW_HISTORY and tables == CREW_TABLES:
                connection.execute(CREATE_EMPLOYEES)
                connection.execute(
                    "CREATE INDEX IX_Employees_HomeCrewId ON Employees (HomeCrewId)"
                )
                record_migration(
                    connection, EMPLOYEE_ROSTER, product_version="Rigarus 0.1.0"
                )
                history = (*CREW_HISTORY, EMPLOYEE_ROSTER)
                tables = CREW_TABLES | {"Employees"}

            if history == (*CREW_HISTORY, EMPLOYEE_ROSTER) and tables == (
                CREW_TABLES | {"Employees"}
            ):
                connection.execute(CREATE_RIGS)
                connection.execute(
                    "CREATE UNIQUE INDEX IX_Rigs_Number ON Rigs (Number)"
                )
                connection.execute(
                    "CREATE INDEX IX_Rigs_DefaultCrewId ON Rigs (DefaultCrewId)"
                )
                record_migration(
                    connection, RIG_INVENTORY, product_version="Rigarus 0.1.0"
                )
                history = (*CREW_HISTORY, EMPLOYEE_ROSTER, RIG_INVENTORY)
                tables = CREW_TABLES | {"Employees", "Rigs"}

            rig_history = (*CREW_HISTORY, EMPLOYEE_ROSTER, RIG_INVENTORY)
            rig_tables = CREW_TABLES | {"Employees", "Rigs"}
            if history == rig_history and tables == rig_tables:
                for statement in CREATE_FOREMAN_HISTORY:
                    connection.execute(statement)
                record_migration(
                    connection, FOREMAN_HISTORY, product_version="Rigarus 0.1.0"
                )
                history = (*rig_history, FOREMAN_HISTORY)
                tables = rig_tables | {"ForemanChanges"}
            foreman_history = (*rig_history, FOREMAN_HISTORY)
            foreman_tables = rig_tables | {"ForemanChanges"}
            if history == foreman_history and tables == foreman_tables:
                for statement in CREATE_DRAFT_ASSIGNMENTS:
                    connection.execute(statement)
                record_migration(
                    connection, DRAFT_ASSIGNMENTS, product_version="Rigarus 0.1.0"
                )
                history = (*foreman_history, DRAFT_ASSIGNMENTS)
                tables = foreman_tables | {"DraftAssignments"}
            draft_history = (*foreman_history, DRAFT_ASSIGNMENTS)
            draft_tables = foreman_tables | {"DraftAssignments"}
            if history == draft_history and tables == draft_tables:
                for statement in CREATE_ASSIGNMENT_STAFFING:
                    connection.execute(statement)
                record_migration(
                    connection, ASSIGNMENT_STAFFING, product_version="Rigarus 0.1.0"
                )
                history = (*draft_history, ASSIGNMENT_STAFFING)
                tables = draft_tables | {
                    "AssignmentStaffingChanges",
                    "AssignmentStaffingMembers",
                }
            staffing_history = (*draft_history, ASSIGNMENT_STAFFING)
            staffing_tables = draft_tables | {
                "AssignmentStaffingChanges",
                "AssignmentStaffingMembers",
            }
            if history == staffing_history and tables == staffing_tables:
                for statement in CREATE_EMPLOYEE_AVAILABILITY:
                    connection.execute(statement)
                record_migration(
                    connection, EMPLOYEE_AVAILABILITY, product_version="Rigarus 0.1.0"
                )
                history = (*staffing_history, EMPLOYEE_AVAILABILITY)
                tables = staffing_tables | {
                    "EmployeeAvailabilityChanges",
                    "EmployeeAvailability",
                }
            availability_history = (*staffing_history, EMPLOYEE_AVAILABILITY)
            availability_tables = staffing_tables | {
                "EmployeeAvailabilityChanges",
                "EmployeeAvailability",
            }
            if history == availability_history and tables == availability_tables:
                for statement in CREATE_WORKING_CALENDARS:
                    connection.execute(statement)
                record_migration(
                    connection, WORKING_CALENDARS, product_version="Rigarus 0.1.0"
                )
                history = (*availability_history, WORKING_CALENDARS)
                tables = availability_tables | CALENDAR_TABLES
            calendar_history = (*availability_history, WORKING_CALENDARS)
            calendar_tables = availability_tables | CALENDAR_TABLES
            if history == calendar_history and tables == calendar_tables:
                for statement in CREATE_DRIVER_APPROVALS:
                    connection.execute(statement)
                record_migration(
                    connection, DRIVER_APPROVALS, product_version="Rigarus 0.1.0"
                )
                history = (*calendar_history, DRIVER_APPROVALS)
                tables = calendar_tables | DRIVER_TABLES
            driver_history = (*calendar_history, DRIVER_APPROVALS)
            driver_tables = calendar_tables | DRIVER_TABLES
            if history == driver_history and tables == driver_tables:
                for statement in CREATE_CAPABILITY_EVIDENCE:
                    connection.execute(statement)
                record_migration(
                    connection, CAPABILITY_EVIDENCE, product_version="Rigarus 0.1.0"
                )
                history = (*driver_history, CAPABILITY_EVIDENCE)
                tables = driver_tables | CAPABILITY_TABLES
            capability_history = (*driver_history, CAPABILITY_EVIDENCE)
            capability_tables = driver_tables | CAPABILITY_TABLES
            if history == capability_history and tables == capability_tables:
                for statement in CREATE_DAY_DRAFTS:
                    connection.execute(statement)
                record_migration(
                    connection, DAY_DRAFTS, product_version="Rigarus 0.1.0"
                )
                history = (*capability_history, DAY_DRAFTS)
                tables = capability_tables | DAY_TABLES
            day_history = (*capability_history, DAY_DRAFTS)
            day_tables = capability_tables | DAY_TABLES
            if history == day_history and tables == day_tables:
                for statement in CREATE_DAILY_CALENDARS:
                    connection.execute(statement)
                record_migration(
                    connection, DAILY_CALENDARS, product_version="Rigarus 0.1.0"
                )
                history = (*day_history, DAILY_CALENDARS)
                tables = day_tables | DAILY_TABLES
            daily_history = (*day_history, DAILY_CALENDARS)
            daily_tables = day_tables | DAILY_TABLES
            if history == daily_history and tables == daily_tables:
                for statement in CREATE_DAILY_DRIVERS:
                    connection.execute(statement)
                record_migration(
                    connection, DAILY_DRIVERS, product_version="Rigarus 0.1.0"
                )
            elif history != (*daily_history, DAILY_DRIVERS) or tables != (
                daily_tables | DAILY_DRIVER_TABLES
            ):
                raise UnsupportedDatabaseError(
                    "This Rigarus database has an unsupported schema. Open it with a compatible version."
                )

            read_demo(connection)
            connection.execute(
                "SELECT Id, JobNumber, SiteId, SiteName FROM Projects LIMIT 0"
            )
            connection.execute(
                "SELECT Id, ProjectId, Type, RequiredCrewCount, EstimatedHalfDays FROM WorkItems LIMIT 0"
            )

            connection.execute("SELECT Id, Name, Type, Active FROM Crews LIMIT 0")
            connection.execute(
                "SELECT Id, Name, HomeCrewId, SkillLevel, ForemanEligible, Active, DriverStatus FROM Employees LIMIT 0"
            )
            connection.execute(
                "SELECT Id, Number, Type, Notes, DefaultCrewId, Active FROM Rigs LIMIT 0"
            )
            connection.execute(
                "SELECT Id, CrewId, EmployeeId, CrewName, EmployeeName, RecordedAt FROM ForemanChanges LIMIT 0"
            )
            connection.execute(
                "SELECT Id, WorkItemId, CrewId, LocalDate, Slot, Notes, Status, Revision, CreatedAt, UpdatedAt FROM DraftAssignments LIMIT 0"
            )

        mode = connection.execute("PRAGMA journal_mode = WAL").fetchone()
        if mode != ("wal",):
            raise sqlite3.OperationalError("SQLite could not enable WAL mode.")


def create_demo_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE __EFMigrationsHistory (
            MigrationId TEXT NOT NULL CONSTRAINT PK___EFMigrationsHistory PRIMARY KEY,
            ProductVersion TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE DemoProjects (
            Id INTEGER NOT NULL CONSTRAINT PK_DemoProjects PRIMARY KEY,
            JobNumber TEXT NOT NULL,
            SiteName TEXT NOT NULL,
            Note TEXT NOT NULL,
            CONSTRAINT CK_DemoProjects_NoteLength CHECK (length(Note) <= 200)
        )
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX IX_DemoProjects_JobNumber ON DemoProjects (JobNumber)"
    )
    connection.execute(
        """
        INSERT INTO DemoProjects (Id, JobNumber, SiteName, Note)
        VALUES (1, 'DEMO-001', 'Example Site', 'Synthetic sample for M0.')
        """
    )
    record_migration(connection, INITIAL_DEMO)


def record_migration(
    connection: sqlite3.Connection,
    migration_id: str,
    *,
    product_version: str = EF_VERSION,
) -> None:
    connection.execute(
        "INSERT INTO __EFMigrationsHistory (MigrationId, ProductVersion) VALUES (?, ?)",
        (migration_id, product_version),
    )


def read_demo(connection: sqlite3.Connection) -> DemoProject:
    row = connection.execute(
        "SELECT Id, JobNumber, SiteName, Note FROM DemoProjects WHERE Id = 1"
    ).fetchone()
    if row is None:
        raise UnsupportedDatabaseError(
            "The demo project is missing from the Rigarus database."
        )
    return DemoProject(*row)


class DemoStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self) -> DemoProject:
        with closing(connect(self.path)) as connection:
            return read_demo(connection)

    def save_note(self, note: str) -> DemoProject:
        validate_note(note)
        with closing(connect(self.path)) as connection, connection:
            connection.execute("UPDATE DemoProjects SET Note = ? WHERE Id = 1", (note,))
            return read_demo(connection)
