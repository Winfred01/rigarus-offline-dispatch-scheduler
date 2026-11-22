import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from rigarus_backend.api import create_app
from rigarus_backend.foreman_store import ForemanStore
from rigarus_backend.foremen import StaleForemanChange
from rigarus_backend.storage import FOREMAN_HISTORY, initialize_database


class ForemanTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "rigarus.db"
        self.client = TestClient(create_app(self.database))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.crew = self.client.post(
            "/crews", json={"name": "Synthetic Civil", "type": "Civil"}
        ).json()
        self.home = self.client.post(
            "/crews", json={"name": "Synthetic Tower", "type": "Tower"}
        ).json()
        self.people = [
            self.client.post(
                "/employees",
                json={
                    "name": f"Synthetic Foreman {i}",
                    "home_crew_id": self.home["id"],
                    "skill_level": 1,
                    "foreman_eligible": True,
                },
            ).json()
            for i in range(2)
        ]
        self.endpoint = f"/crews/{self.crew['id']}/foreman"

    def save(self, employee_id, revision):
        return self.client.put(
            self.endpoint,
            json={"employee_id": employee_id, "expected_revision": revision},
        )

    def test_appointment_replacement_clear_snapshots_and_restart(self):
        self.assertEqual(self.client.get(self.endpoint).json()["revision"], 0)
        first = self.save(self.people[0]["id"], 0).json()
        self.assertEqual(first["employee_id"], self.people[0]["id"])
        self.assertEqual(
            self.save(self.people[0]["id"], first["revision"]).json(), first
        )
        changed = self.save(self.people[1]["id"], first["revision"]).json()
        self.assertEqual(
            [row["employee_id"] for row in changed["history"]],
            [self.people[1]["id"], self.people[0]["id"]],
        )
        person = self.people[1]
        draft = {
            key: value
            for key, value in person.items()
            if key not in {"id", "driver_status"}
        }
        self.client.put(
            f"/employees/{person['id']}",
            json={
                **draft,
                "name": "Synthetic renamed",
                "active": False,
                "foreman_eligible": False,
            },
        ).raise_for_status()
        self.client.put(
            f"/crews/{self.crew['id']}",
            json={"name": "Synthetic retired crew", "type": "Civil", "active": False},
        ).raise_for_status()
        retained = self.client.get(self.endpoint).json()
        self.assertEqual(retained["revision"], changed["revision"])
        self.assertEqual(retained["employee_name"], "Synthetic renamed")
        self.assertFalse(retained["employee_active"])
        self.assertFalse(retained["employee_eligible"])
        self.assertEqual(retained["history"], changed["history"])
        self.assertEqual(self.save(person["id"], retained["revision"]).json(), retained)
        cleared = self.save(None, changed["revision"]).json()
        self.assertIsNone(cleared["employee_id"])
        self.assertIsNone(cleared["history"][0]["employee_name"])
        self.assertEqual(cleared["history"][0]["crew_name"], "Synthetic retired crew")
        self.assertEqual(cleared["history"][1]["employee_name"], person["name"])
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(reopened.get(self.endpoint).json(), cleared)
            self.assertTrue(
                all(
                    row["home_crew_id"] == self.home["id"]
                    for row in reopened.get("/employees").json()
                )
            )
            self.assertTrue(
                all(
                    row["driver_status"] == "Unverified"
                    for row in reopened.get("/employees").json()
                )
            )
        self.assertEqual(len(cleared["history"]), 3)
        self.assertTrue(
            all(row["recorded_at"].endswith("+00:00") for row in cleared["history"])
        )

    def test_invalid_inputs_and_stale_revision_do_not_write(self):
        inactive = self.client.post(
            "/employees",
            json={
                "name": "Synthetic inactive",
                "home_crew_id": self.home["id"],
                "skill_level": 2,
                "active": False,
                "foreman_eligible": True,
            },
        ).json()
        ineligible = self.client.post(
            "/employees",
            json={
                "name": "Synthetic ineligible",
                "home_crew_id": self.home["id"],
                "skill_level": 3,
            },
        ).json()
        for employee_id in (
            999,
            inactive["id"],
            ineligible["id"],
            True,
            1.5,
            "1",
            0,
            -1,
        ):
            with self.subTest(employee_id=employee_id):
                self.assertEqual(self.save(employee_id, 0).status_code, 422)
        for payload in (
            {"employee_id": None},
            {"employee_id": None, "expected_revision": True},
            {
                "employee_id": None,
                "expected_revision": 0,
                "effective_date": "2020-01-01",
            },
        ):
            self.assertEqual(
                self.client.put(self.endpoint, json=payload).status_code, 422
            )
        self.assertEqual(self.client.get(self.endpoint).json()["history"], [])
        first = self.save(self.people[0]["id"], 0).json()
        self.assertEqual(self.save(self.people[1]["id"], 0).status_code, 409)
        self.assertEqual(self.client.get(self.endpoint).json(), first)
        self.assertEqual(self.client.get("/crews/999/foreman").status_code, 404)
        self.assertEqual(
            self.client.put(
                "/crews/999/foreman", json={"employee_id": None, "expected_revision": 0}
            ).status_code,
            404,
        )
        self.assertEqual(self.client.delete(self.endpoint).status_code, 405)

    def test_concurrent_changes_preserve_one_winner_and_history_is_immutable(self):
        store = ForemanStore(self.database)

        def assign(person):
            try:
                return store.save(self.crew["id"], person["id"], 0).revision
            except StaleForemanChange:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(assign, self.people))
        self.assertEqual(sum(value is not None for value in results), 1)
        state = store.read(self.crew["id"])
        self.assertEqual(len(state.history), 1)
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            for sql in (
                "UPDATE ForemanChanges SET CrewName='Overwrite'",
                "DELETE FROM ForemanChanges",
                f"DELETE FROM Crews WHERE Id={self.crew['id']}",
                f"DELETE FROM Employees WHERE Id={state.employee_id}",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(sql)
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
        self.assertEqual(store.read(self.crew["id"]), state)

    def test_database_write_failure_is_atomic_and_retryable(self):
        first = self.save(self.people[0]["id"], 0).json()
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "CREATE TRIGGER synthetic_foreman_failure BEFORE INSERT ON ForemanChanges BEGIN SELECT RAISE(ABORT, 'Synthetic save failure'); END"
            )
        failed = self.save(self.people[1]["id"], first["revision"])
        self.assertEqual(failed.status_code, 503)
        self.assertNotIn("Synthetic save failure", failed.text)
        self.assertEqual(self.client.get(self.endpoint).json(), first)
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("DROP TRIGGER synthetic_foreman_failure")
        self.assertEqual(
            self.save(self.people[1]["id"], first["revision"]).status_code, 200
        )

    def test_read_failure_does_not_expose_database_diagnostics(self):
        with patch(
            "rigarus_backend.foreman_store.connect",
            side_effect=sqlite3.OperationalError("Synthetic private path"),
        ):
            response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"], "Could not load Foreman. Try Reload Foreman."
        )
        self.assertNotIn("Synthetic private path", response.text)

    def test_rig_schema_migration_rolls_back_then_retries_preserving_all_records(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute("DROP TABLE ForemanChanges")
                connection.execute(
                    "DELETE FROM __EFMigrationsHistory WHERE MigrationId = ?",
                    (FOREMAN_HISTORY,),
                )
                connection.execute(
                    "INSERT INTO Projects VALUES (44, 'SYN-044', '0044', 'Synthetic site')"
                )
                connection.execute(
                    "INSERT INTO WorkItems VALUES (55, 44, 'Tower', 1, 3)"
                )
                connection.execute(
                    "INSERT INTO Rigs VALUES (66, '0007', 'Synthetic drill', 'Synthetic note', ?, 0)",
                    (self.crew["id"],),
                )
                connection.execute(
                    "UPDATE DemoProjects SET Note='Synthetic retained note'"
                )
                connection.execute(
                    "CREATE TRIGGER synthetic_migration_failure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddForemanHistory' BEGIN SELECT RAISE(ABORT, 'Synthetic migration failure'); END"
                )
            before = connection.execute(
                "SELECT * FROM __EFMigrationsHistory ORDER BY MigrationId"
            ).fetchall()
            snapshots = {
                table: connection.execute(f"SELECT * FROM {table}").fetchall()
                for table in (
                    "Projects",
                    "WorkItems",
                    "Crews",
                    "Employees",
                    "Rigs",
                    "DemoProjects",
                )
            }
            with self.assertRaisesRegex(
                sqlite3.IntegrityError, "Synthetic migration failure"
            ):
                initialize_database(self.database)
            self.assertIsNone(
                connection.execute(
                    "SELECT name FROM sqlite_schema WHERE name='ForemanChanges'"
                ).fetchone()
            )
            self.assertEqual(
                connection.execute(
                    "SELECT * FROM __EFMigrationsHistory ORDER BY MigrationId"
                ).fetchall(),
                before,
            )
            connection.execute("DROP TRIGGER synthetic_migration_failure")
            initialize_database(self.database)
            initialize_database(self.database)
            for table, rows in snapshots.items():
                self.assertEqual(
                    connection.execute(f"SELECT * FROM {table}").fetchall(), rows
                )
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchall(), [("ok",)]
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
        self.assertEqual(self.client.get(self.endpoint).json()["history"], [])
