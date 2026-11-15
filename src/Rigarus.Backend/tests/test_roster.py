import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from rigarus_backend.api import create_app
from rigarus_backend.storage import initialize_database


class CrewRosterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "rigarus.db"

    def test_create_search_edit_deactivate_and_reopen(self):
        with TestClient(create_app(self.database)) as client:
            civil = client.post(
                "/crews", json={"name": "  Synthetic Civil 01  ", "type": "Civil"}
            )
            self.assertEqual(civil.status_code, 201)
            crew = civil.json()
            self.assertEqual(crew["name"], "Synthetic Civil 01")
            self.assertTrue(crew["active"])
            tower = client.post(
                "/crews", json={"name": "Synthetic Tower 01", "type": "Tower"}
            )
            self.assertEqual(tower.status_code, 201)
            self.assertEqual(
                client.get("/crews", params={"term": " CIVIL "}).json(), [crew]
            )
            self.assertEqual(client.get("/crews", params={"term": "%"}).json(), [])
            edited = client.put(
                f"/crews/{crew['id']}",
                json={"name": "Synthetic Civil 02", "type": "Civil", "active": False},
            )
            self.assertEqual(edited.status_code, 200)
            self.assertEqual(edited.json()["id"], crew["id"])
            self.assertFalse(edited.json()["active"])
            self.assertEqual(client.delete(f"/crews/{crew['id']}").status_code, 405)

        with TestClient(create_app(self.database)) as client:
            self.assertEqual(client.get("/crews").json(), [tower.json(), edited.json()])
            restored = client.put(
                f"/crews/{crew['id']}",
                json={"name": "Synthetic Civil 02", "type": "Civil", "active": True},
            )
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(restored.json()["id"], crew["id"])
            self.assertTrue(restored.json()["active"])

    def test_invalid_and_missing_crews_do_not_write(self):
        with TestClient(create_app(self.database)) as client:
            for payload in (
                {"name": "  ", "type": "Civil"},
                {"name": "x" * 101, "type": "Tower"},
                {"name": "Synthetic", "type": "Small"},
                {"name": "Synthetic", "type": "Tower", "active": "false"},
            ):
                with self.subTest(payload=payload):
                    self.assertEqual(
                        client.post("/crews", json=payload).status_code, 422
                    )
            self.assertEqual(
                client.put(
                    "/crews/77", json={"name": "Synthetic", "type": "Civil"}
                ).status_code,
                404,
            )
            self.assertEqual(client.get("/crews").json(), [])

    def test_failed_roster_upgrade_leaves_project_master_and_can_retry(self):
        fixture = Path(__file__).with_name("fixtures") / "legacy_ef_schema.sql"
        with closing(sqlite3.connect(self.database)) as connection:
            connection.executescript(fixture.read_text(encoding="utf-8"))
            with connection:
                connection.execute(
                    "INSERT INTO Projects VALUES (25, 'P-25', '05', 'Synthetic')"
                )
                connection.execute(
                    """
                    CREATE TRIGGER synthetic_roster_failure
                    BEFORE INSERT ON __EFMigrationsHistory
                    WHEN NEW.MigrationId LIKE '%AddCrewRoster'
                    BEGIN
                        SELECT RAISE(ABORT, 'Synthetic migration failure');
                    END
                    """
                )
            before = connection.execute(
                "SELECT * FROM __EFMigrationsHistory"
            ).fetchall()
            with self.assertRaisesRegex(
                sqlite3.IntegrityError, "Synthetic migration failure"
            ):
                initialize_database(self.database)
            self.assertEqual(
                connection.execute("SELECT * FROM __EFMigrationsHistory").fetchall(),
                before,
            )
            self.assertIsNone(
                connection.execute(
                    "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'Crews'"
                ).fetchone()
            )
            connection.execute("DROP TRIGGER synthetic_roster_failure")
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                connection.execute("SELECT Id FROM Projects").fetchall(), [(25,)]
            )
            self.assertEqual(connection.execute("SELECT * FROM Crews").fetchall(), [])
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
