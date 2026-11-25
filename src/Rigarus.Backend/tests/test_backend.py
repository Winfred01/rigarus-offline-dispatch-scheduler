from rigarus_backend.calendar_migration import WORKING_CALENDARS
from rigarus_backend.driver_migration import DRIVER_APPROVALS
from rigarus_backend.capability_migration import CAPABILITY_EVIDENCE
from rigarus_backend.day_migration import DAY_DRAFTS
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from rigarus_backend.api import create_app
from rigarus_backend.storage import UnsupportedDatabaseError, initialize_database

INITIAL = "20261112045924_InitialDemo"
PROJECTS = "20261112072258_AddProjectsAndWorkItems"
CREWS = "20261115031137_AddCrewRoster"
EMPLOYEES = "20261115130213_AddEmployeeRoster"
RIGS = "20261119130000_AddRigInventory"
FOREMEN = "20261122030000_AddForemanHistory"
ASSIGNMENTS = "20261122040000_AddDraftAssignments"
STAFFING = "20261122200000_AddAssignmentStaffing"
AVAILABILITY = "20261123010000_AddEmployeeAvailability"


class BackendTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "data" / "rigarus.db"

    def create_legacy_database(self, include_projects):
        fixture = Path(__file__).with_name("fixtures") / "legacy_ef_schema.sql"
        script = fixture.read_text(encoding="utf-8")
        if not include_projects:
            script = script.split("COMMIT;", 1)[0] + "COMMIT;"
        self.database.parent.mkdir()
        with closing(sqlite3.connect(self.database)) as connection:
            connection.executescript(script)
            with connection:
                connection.execute(
                    "UPDATE DemoProjects SET Note = ? WHERE Id = 1",
                    ("Edited in legacy demo",),
                )
                if include_projects:
                    connection.execute(
                        "INSERT INTO Projects VALUES (32, '00123', '0042', 'Synthetic site')"
                    )
                    connection.execute(
                        "INSERT INTO WorkItems VALUES (75, 32, 'Civil', 2, 3)"
                    )

    def migration_ids(self, connection):
        return [
            migration_id
            for (migration_id,) in connection.execute(
                "SELECT MigrationId FROM __EFMigrationsHistory ORDER BY MigrationId"
            )
        ]

    def test_fresh_database_and_note_survives_app_restart(self):
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(
                client.get("/demo").json(),
                {
                    "id": 1,
                    "job_number": "DEMO-001",
                    "site_name": "Example Site",
                    "note": "Synthetic sample for M0.",
                },
            )
            saved = client.put("/demo/note", json={"note": "Synthetic operator note"})
            self.assertEqual(saved.status_code, 200)

        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(
                reopened.get("/demo").json()["note"], "Synthetic operator note"
            )

        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                self.migration_ids(connection),
                [
                    INITIAL,
                    PROJECTS,
                    CREWS,
                    EMPLOYEES,
                    RIGS,
                    FOREMEN,
                    ASSIGNMENTS,
                    STAFFING,
                    AVAILABILITY,
                    WORKING_CALENDARS,
                    DRIVER_APPROVALS,
                    CAPABILITY_EVIDENCE,
                    DAY_DRAFTS,
                ],
            )
            self.assertEqual(
                connection.execute("PRAGMA journal_mode").fetchone(), ("wal",)
            )

    def test_note_validation_matches_legacy_utf16_limit(self):
        note = "\U0001f642" * 100
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(
                client.put("/demo/note", json={"note": note}).status_code, 200
            )
            self.assertEqual(
                client.put("/demo/note", json={"note": note + "a"}).status_code, 422
            )
            self.assertEqual(
                client.put("/demo/note", json={"note": 123}).status_code, 422
            )
            self.assertEqual(client.get("/demo").json()["note"], note)
            self.assertEqual(
                client.put("/demo/note", json={"note": ""}).status_code, 200
            )
            self.assertEqual(client.get("/demo").json()["note"], "")

    def test_m0_upgrade_preserves_note_and_adds_project_constraints(self):
        self.create_legacy_database(include_projects=False)
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(
                client.get("/demo").json()["note"], "Edited in legacy demo"
            )

        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                self.migration_ids(connection),
                [
                    INITIAL,
                    PROJECTS,
                    CREWS,
                    EMPLOYEES,
                    RIGS,
                    FOREMEN,
                    ASSIGNMENTS,
                    STAFFING,
                    AVAILABILITY,
                    WORKING_CALENDARS,
                    DRIVER_APPROVALS,
                    CAPABILITY_EVIDENCE,
                    DAY_DRAFTS,
                ],
            )
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "INSERT INTO Projects VALUES (7, 'Job-007', '0004', 'Example Site')"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO Projects VALUES (8, 'job-007', '0005', 'Other Site')"
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO WorkItems VALUES (9, 7, 'Civil', 1, 1.5)"
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO WorkItems VALUES (9, 8, 'Civil', 1, 2)")

    def test_existing_project_master_data_survives_reopen_and_note_edit(self):
        self.create_legacy_database(include_projects=True)
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(
                client.get("/demo").json()["note"], "Edited in legacy demo"
            )
            self.assertEqual(
                client.put("/demo/note", json={"note": "Edited in Python"}).status_code,
                200,
            )

        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                self.migration_ids(connection),
                [
                    INITIAL,
                    PROJECTS,
                    CREWS,
                    EMPLOYEES,
                    RIGS,
                    FOREMEN,
                    ASSIGNMENTS,
                    STAFFING,
                    AVAILABILITY,
                    WORKING_CALENDARS,
                    DRIVER_APPROVALS,
                    CAPABILITY_EVIDENCE,
                    DAY_DRAFTS,
                ],
            )
            self.assertEqual(
                connection.execute("SELECT * FROM Projects").fetchall(),
                [(32, "00123", "0042", "Synthetic site")],
            )
            self.assertEqual(
                connection.execute("SELECT * FROM WorkItems").fetchall(),
                [(75, 32, "Civil", 2, 3)],
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )

    def test_failed_migration_rolls_back_and_retries_after_conflict_removed(self):
        self.create_legacy_database(include_projects=False)
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "CREATE INDEX IX_Projects_JobNumber ON DemoProjects (SiteName)"
            )
            with self.assertRaises(sqlite3.OperationalError):
                initialize_database(self.database)

            self.assertEqual(self.migration_ids(connection), [INITIAL])
            self.assertEqual(
                connection.execute(
                    "SELECT name FROM sqlite_schema WHERE name IN ('Projects', 'WorkItems')"
                ).fetchall(),
                [],
            )
            self.assertEqual(
                connection.execute("SELECT Note FROM DemoProjects").fetchone(),
                ("Edited in legacy demo",),
            )
            connection.execute("DROP INDEX IX_Projects_JobNumber")

        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                self.migration_ids(connection),
                [
                    INITIAL,
                    PROJECTS,
                    CREWS,
                    EMPLOYEES,
                    RIGS,
                    FOREMEN,
                    ASSIGNMENTS,
                    STAFFING,
                    AVAILABILITY,
                    WORKING_CALENDARS,
                    DRIVER_APPROVALS,
                    CAPABILITY_EVIDENCE,
                    DAY_DRAFTS,
                ],
            )

    def test_unknown_database_is_rejected_without_adding_schema(self):
        self.database.parent.mkdir()
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("CREATE TABLE Unrelated (Id INTEGER)")
            with self.assertRaises(UnsupportedDatabaseError):
                initialize_database(self.database)
            self.assertEqual(
                connection.execute("SELECT name FROM sqlite_schema").fetchall(),
                [("Unrelated",)],
            )

    def test_future_schema_is_rejected_without_editing_note(self):
        self.create_legacy_database(include_projects=True)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "INSERT INTO __EFMigrationsHistory VALUES ('future', '10.0.15')"
                )
            with self.assertRaises(UnsupportedDatabaseError):
                initialize_database(self.database)
            self.assertEqual(
                self.migration_ids(connection), [INITIAL, PROJECTS, "future"]
            )
            self.assertEqual(
                connection.execute("SELECT Note FROM DemoProjects").fetchone(),
                ("Edited in legacy demo",),
            )
