import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from rigarus_backend.api import create_app
from rigarus_backend.rig_store import RigStore
from rigarus_backend.rigs import DuplicateRigNumber, RigDraft
from rigarus_backend.storage import RIG_INVENTORY, initialize_database


class RigInventoryTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = Path(folder.name) / "rigarus.db"

    def test_create_edit_retire_reopen_and_reactivate_preserves_identity(self):
        with TestClient(create_app(self.database)) as client:
            crew = client.post(
                "/crews", json={"name": "Synthetic Civil", "type": "Civil"}
            ).json()
            draft = {
                "number": "  0007  ",
                "type": " Synthetic truck ",
                "notes": " Demo winch ",
            }
            response = client.post("/rigs", json=draft)
            self.assertEqual(response.status_code, 201)
            original = response.json()
            self.assertEqual(original["number"], "0007")
            self.assertIsNone(original["default_crew_id"])
            endpoint = f"/rigs/{original['id']}"
            draft = {
                "number": "0007",
                "type": "Synthetic truck",
                "notes": "Edited demo winch",
                "default_crew_id": crew["id"],
                "active": False,
            }
            edited = client.put(endpoint, json=draft)
            self.assertEqual(edited.status_code, 200)
            self.assertEqual(edited.json(), {"id": original["id"], **draft})
            for term in ("0007", "TRUCK", "demo winch"):
                self.assertEqual(
                    client.get("/rigs", params={"term": term}).json(), [edited.json()]
                )
            self.assertEqual(client.get("/rigs", params={"term": "%"}).json(), [])
            self.assertEqual(client.delete(endpoint).status_code, 405)
            client.put(
                f"/crews/{crew['id']}", json={**crew, "active": False}
            ).raise_for_status()

        with TestClient(create_app(self.database)) as client:
            self.assertEqual(client.get("/rigs").json(), [edited.json()])
            restored = client.put(
                endpoint, json={**draft, "active": True, "default_crew_id": None}
            )
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(restored.json()["id"], original["id"])
            self.assertIsNone(restored.json()["default_crew_id"])
            self.assertEqual(len(client.get("/rigs").json()), 1)

    def test_duplicate_numbers_remain_reserved_and_failed_edits_are_atomic(self):
        with TestClient(create_app(self.database)) as client:
            first = client.post(
                "/rigs",
                json={"number": "RIG-007", "type": "Synthetic", "active": False},
            ).json()
            second = client.post(
                "/rigs", json={"number": "RIG-008", "type": "Synthetic"}
            ).json()
            duplicate = {"number": " rig-007 ", "type": "Unsaved", "notes": "Unsaved"}
            for method, url in (("POST", "/rigs"), ("PUT", f"/rigs/{second['id']}")):
                result = client.request(method, url, json=duplicate)
                self.assertEqual(result.status_code, 409)
                self.assertIn("already belongs", result.json()["detail"])
            self.assertEqual(client.get("/rigs").json(), [second, first])

    def test_invalid_fields_and_missing_references_do_not_change_saved_data(self):
        with TestClient(create_app(self.database)) as client:
            original = client.post(
                "/rigs", json={"number": "SYN-01", "type": "Synthetic"}
            ).json()
            for change in (
                {"number": "  "},
                {"number": "x" * 51},
                {"number": "x\x00y"},
                {"type": ""},
                {"type": "x" * 101},
                {"notes": "x" * 2001},
                {"default_crew_id": 999},
                {"default_crew_id": True},
                {"default_crew_id": 1.5},
                {"active": "false"},
                {"scheduling_approved": True},
            ):
                draft = {"number": "SYN-01", "type": "Synthetic", **change}
                with self.subTest(change=change):
                    self.assertEqual(
                        client.put(f"/rigs/{original['id']}", json=draft).status_code,
                        422,
                    )
            self.assertEqual(client.get("/rigs").json(), [original])
            self.assertEqual(
                client.put(
                    "/rigs/999", json={"number": "SYN-02", "type": "Synthetic"}
                ).status_code,
                404,
            )

    def test_concurrent_case_variants_cannot_create_duplicate_rigs(self):
        initialize_database(self.database)
        store = RigStore(self.database)

        def create(number):
            try:
                return store.save(RigDraft(number=number, type="Synthetic")).id
            except DuplicateRigNumber:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, ["SYN-007", "syn-007"]))
        self.assertEqual(sum(value is not None for value in results), 1)
        self.assertEqual(len(store.search("")), 1)

    def test_employee_schema_upgrade_rolls_back_then_retries_preserving_data(self):
        with TestClient(create_app(self.database)) as client:
            client.put(
                "/demo/note", json={"note": "Synthetic retained note"}
            ).raise_for_status()
            crew = client.post(
                "/crews", json={"name": "Synthetic Tower", "type": "Tower"}
            ).json()
            employee = client.post(
                "/employees",
                json={
                    "name": "Synthetic employee",
                    "home_crew_id": crew["id"],
                    "skill_level": 2,
                },
            ).json()
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute("DROP TABLE Rigs")
                connection.execute(
                    "DELETE FROM __EFMigrationsHistory WHERE MigrationId = ?",
                    (RIG_INVENTORY,),
                )
                connection.execute(
                    "INSERT INTO Projects VALUES (44, 'SYN-044', '0044', 'Synthetic yard')"
                )
                connection.execute(
                    "INSERT INTO WorkItems VALUES (55, 44, 'Tower', 1, 3)"
                )
                connection.execute("""
                    CREATE TRIGGER synthetic_rig_failure BEFORE INSERT ON __EFMigrationsHistory
                    WHEN NEW.MigrationId LIKE '%AddRigInventory'
                    BEGIN SELECT RAISE(ABORT, 'Synthetic rig migration failure'); END
                """)
            history = connection.execute(
                "SELECT * FROM __EFMigrationsHistory ORDER BY MigrationId"
            ).fetchall()
            with self.assertRaisesRegex(
                sqlite3.IntegrityError, "Synthetic rig migration failure"
            ):
                initialize_database(self.database)
            self.assertIsNone(
                connection.execute(
                    "SELECT name FROM sqlite_schema WHERE name='Rigs'"
                ).fetchone()
            )
            self.assertEqual(
                connection.execute(
                    "SELECT * FROM __EFMigrationsHistory ORDER BY MigrationId"
                ).fetchall(),
                history,
            )
            connection.execute("DROP TRIGGER synthetic_rig_failure")
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(
                client.get("/demo").json()["note"], "Synthetic retained note"
            )
            self.assertEqual(client.get("/employees").json(), [employee])
            self.assertEqual(client.get("/crews").json(), [crew])
            self.assertEqual(client.get("/rigs").json(), [])
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT Id, ProjectId, EstimatedHalfDays FROM WorkItems"
                ).fetchall(),
                [(55, 44, 3)],
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
