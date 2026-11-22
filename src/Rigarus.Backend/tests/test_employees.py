import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from rigarus_backend.api import create_app
from rigarus_backend.storage import EMPLOYEE_ROSTER, RIG_INVENTORY, initialize_database


class EmployeeRosterTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = Path(folder.name) / "rigarus.db"

    def test_employee_lifecycle_and_driver_status(self):
        with TestClient(create_app(self.database)) as client:
            crew = client.post(
                "/crews", json={"name": "Synthetic Civil", "type": "Civil"}
            ).json()
            draft = {
                "name": "  Synthetic Member 01  ",
                "home_crew_id": crew["id"],
                "skill_level": 2,
            }
            created = client.post("/employees", json=draft)
            self.assertEqual(created.status_code, 201)
            employee = created.json()
            self.assertEqual(employee["name"], "Synthetic Member 01")
            self.assertEqual(employee["driver_status"], "Unverified")
            self.assertFalse(employee["foreman_eligible"])
            self.assertTrue(employee["active"])
            self.assertEqual(
                client.get("/employees", params={"term": " member 01 "}).json(),
                [employee],
            )
            self.assertEqual(client.get("/employees", params={"term": "%"}).json(), [])

            # Independent crew deactivation must preserve the Home Crew reference.
            client.put(
                f"/crews/{crew['id']}",
                json={"name": crew["name"], "type": crew["type"], "active": False},
            ).raise_for_status()
            endpoint = f"/employees/{employee['id']}"
            changes = {
                **draft,
                "name": "Synthetic Member 02",
                "skill_level": 3,
                "foreman_eligible": True,
                "active": False,
            }
            edited = client.put(endpoint, json=changes)
            self.assertEqual(edited.status_code, 200)
            self.assertEqual(edited.json(), {**employee, **changes})
            self.assertEqual(client.delete(endpoint).status_code, 405)

        with TestClient(create_app(self.database)) as client:
            self.assertEqual(client.get("/employees").json(), [edited.json()])
            reactivated = client.put(endpoint, json={**changes, "active": True})
            self.assertEqual(reactivated.status_code, 200)
            self.assertEqual(reactivated.json(), {**edited.json(), "active": True})

    def test_invalid_employee_edits_do_not_write(self):
        with TestClient(create_app(self.database)) as client:
            crew = client.post(
                "/crews", json={"name": "Synthetic Tower", "type": "Tower"}
            ).json()
            draft = {
                "name": "Synthetic Member",
                "home_crew_id": crew["id"],
                "skill_level": 1,
            }
            for change in (
                {"skill_level": 0},
                {"skill_level": 4},
                {"skill_level": 2.5},
                {"skill_level": True},
                {"home_crew_id": crew["id"] + 1000},
                {"home_crew_id": None},
                {"driver_status": "Approved"},
                {"name": "   "},
            ):
                with self.subTest(change=change):
                    response = client.post("/employees", json={**draft, **change})
                    self.assertEqual(response.status_code, 422)

            saved = client.post("/employees", json=draft).json()
            response = client.put(
                f"/employees/{saved['id']}",
                json={**draft, "name": "Unsaved", "home_crew_id": crew["id"] + 1000},
            )
            self.assertEqual(response.status_code, 422)
            self.assertEqual(client.get("/employees").json(), [saved])

    def test_crew_only_database_upgrade_is_atomic_and_can_retry(self):
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute("DROP TABLE ForemanChanges")
                connection.execute(
                    "DELETE FROM __EFMigrationsHistory WHERE MigrationId LIKE '%AddForemanHistory'"
                )
                connection.execute("DROP TABLE Rigs")
                connection.execute(
                    "DELETE FROM __EFMigrationsHistory WHERE MigrationId = ?",
                    (RIG_INVENTORY,),
                )
                connection.execute("DROP TABLE Employees")
                connection.execute(
                    "DELETE FROM __EFMigrationsHistory WHERE MigrationId = ?",
                    (EMPLOYEE_ROSTER,),
                )
                connection.execute(
                    "INSERT INTO Crews VALUES (25, 'Synthetic Civil', 'Civil', 0)"
                )
                connection.execute(
                    "UPDATE DemoProjects SET Note='Synthetic saved note' WHERE Id=1"
                )
                connection.execute(
                    """
                    CREATE TRIGGER synthetic_employee_failure
                    BEFORE INSERT ON __EFMigrationsHistory
                    WHEN NEW.MigrationId LIKE '%AddEmployeeRoster'
                    BEGIN
                        SELECT RAISE(ABORT, 'Synthetic employee migration failure');
                    END
                    """
                )
            with self.assertRaisesRegex(
                sqlite3.IntegrityError, "Synthetic employee migration failure"
            ):
                initialize_database(self.database)
            self.assertIsNone(
                connection.execute(
                    "SELECT name FROM sqlite_schema WHERE name = 'Employees'"
                ).fetchone()
            )
            self.assertEqual(
                connection.execute("SELECT Id, Active FROM Crews").fetchall(), [(25, 0)]
            )
            connection.execute("DROP TRIGGER synthetic_employee_failure")

        with TestClient(create_app(self.database)) as client:
            self.assertEqual(client.get("/demo").json()["note"], "Synthetic saved note")
            self.assertEqual(client.get("/employees").json(), [])
            self.assertEqual(client.get("/crews").json()[0]["id"], 25)

        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
