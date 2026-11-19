import sqlite3
from contextlib import closing
from pathlib import Path

from .domain import DemoProject, validate_note

INITIAL_DEMO = "20261112045924_InitialDemo"
PROJECT_MASTER = "20261112072258_AddProjectsAndWorkItems"
CREW_ROSTER = "20261115031137_AddCrewRoster"
EMPLOYEE_ROSTER = "20261115130213_AddEmployeeRoster"
RIG_INVENTORY = "20261119130000_AddRigInventory"
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


def connect(path: Path, *, create: bool = False) -> sqlite3.Connection:
    location = path if create else f"{path.resolve().as_uri()}?mode=rw"
    connection = sqlite3.connect(
        location,
        uri=not create,
        timeout=5,
        autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL,
    )
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
            elif history != (
                *CREW_HISTORY,
                EMPLOYEE_ROSTER,
                RIG_INVENTORY,
            ) or tables != (CREW_TABLES | {"Employees", "Rigs"}):
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
