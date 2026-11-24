import hashlib
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from migration_fixture import remove_staffing_schema
from rigarus_backend.api import create_app
from rigarus_backend.assignment_store import AssignmentStore
from rigarus_backend.assignments import AssignmentConflict, AssignmentDraft, local_date
from rigarus_backend.storage import DRAFT_ASSIGNMENTS, initialize_database


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "rigarus.db"
        self.client = TestClient(create_app(self.database))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.project = self.client.post(
            "/projects",
            json={
                "job_number": "SYN-0014",
                "site_id": "0014",
                "site_name": "Synthetic site",
                "work_items": [
                    {
                        "type": "Civil",
                        "required_crew_count": 2,
                        "estimated_half_days": 1,
                    },
                    {
                        "type": "Tower",
                        "required_crew_count": 1,
                        "estimated_half_days": 4,
                    },
                ],
            },
        ).json()
        self.crew = self.client.post(
            "/crews", json={"name": "Synthetic Civil", "type": "Civil"}
        ).json()
        self.other_crew = self.client.post(
            "/crews", json={"name": "Synthetic Tower", "type": "Tower", "active": False}
        ).json()
        self.draft = {
            "work_item_id": self.project["work_items"][0]["id"],
            "crew_id": self.crew["id"],
            "local_date": "2026-12-31",
            "slot": "AM",
            "notes": "Synthetic visit note",
        }

    def create(self, **changes):
        return self.client.post("/draft-assignments", json={**self.draft, **changes})

    def test_am_pm_repeat_visits_date_range_and_restart(self):
        first = self.create().json()
        second = self.create(slot="PM").json()
        third = self.create(local_date="2027-01-01").json()
        # Another crew may contribute a visit without inventing complete staffing approval.
        fourth = self.create(crew_id=self.other_crew["id"]).json()
        self.assertFalse(fourth["crew_active"])
        for row in (first, second, third, fourth):
            self.assertEqual(row["work_item_id"], self.draft["work_item_id"])
            self.assertEqual(row["status"], "Draft")
            self.assertEqual(row["validation_status"], "Pending")
            self.assertFalse(row["publishable"])
            self.assertEqual(row["notes"], self.draft["notes"])
        records = self.client.get(
            "/draft-assignments",
            params={
                "start_date": "2026-12-31",
                "end_date": "2027-01-01",
                "crew_id": self.crew["id"],
            },
        ).json()
        self.assertEqual(
            [row["id"] for row in records], [first["id"], second["id"], third["id"]]
        )
        self.assertEqual(
            self.client.get(
                "/draft-assignments", params={"start_date": "2027-01-02"}
            ).json(),
            [],
        )
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(
                reopened.get(f"/draft-assignments/{first['id']}").json(), first
            )
            self.assertEqual(len(reopened.get("/draft-assignments").json()), 4)
            self.assertEqual(
                reopened.get(f"/projects/{self.project['id']}").json(), self.project
            )

    def test_crew_slot_conflict_is_actionable_and_edit_is_atomic(self):
        first = self.create().json()
        other = self.project["work_items"][1]["id"]
        duplicate = self.create(work_item_id=other)
        self.assertEqual(duplicate.status_code, 409)
        self.assertIn(
            f"Draft Assignment #{first['id']} on 2026-12-31 AM",
            duplicate.json()["detail"],
        )
        second = self.create(work_item_id=other, slot="PM").json()
        endpoint = f"/draft-assignments/{second['id']}"
        failed = self.client.put(
            endpoint,
            json={
                **self.draft,
                "expected_revision": second["revision"],
                "notes": "Unsaved",
            },
        )
        self.assertEqual(failed.status_code, 409)
        self.assertEqual(self.client.get(endpoint).json(), second)
        edited = self.client.put(
            endpoint,
            json={
                **self.draft,
                "work_item_id": other,
                "slot": "PM",
                "notes": "Edited synthetic note",
                "expected_revision": second["revision"],
            },
        ).json()
        self.assertEqual(edited["id"], second["id"])
        self.assertEqual(edited["created_at"], second["created_at"])
        self.assertEqual(edited["revision"], 2)
        self.assertEqual(edited["work_item_id"], other)
        self.assertEqual(
            self.client.put(
                endpoint, json={**self.draft, "expected_revision": 1}
            ).status_code,
            409,
        )
        self.assertEqual(self.client.get(endpoint).json(), edited)

    def test_form_cancel_reads_do_not_write_but_saved_cancel_releases_slot(self):
        first = self.create().json()
        digest = hashlib.sha256(self.database.read_bytes()).digest()
        for _ in range(2):
            self.client.get("/draft-assignments").raise_for_status()
            self.client.get(f"/projects/{self.project['id']}").raise_for_status()
            self.client.get("/crews").raise_for_status()
        # A form cancelled before submit sends reads only, never a write request.
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).digest(), digest)
        endpoint = f"/draft-assignments/{first['id']}"
        cancelled = self.client.post(
            endpoint + "/cancel", json={"expected_revision": 1}
        ).json()
        self.assertEqual(cancelled["status"], "Cancelled")
        self.assertEqual(cancelled["id"], first["id"])
        self.assertEqual(cancelled["work_item_id"], first["work_item_id"])
        self.assertEqual(cancelled["notes"], first["notes"])
        self.assertEqual(self.client.get("/draft-assignments").json(), [])
        self.assertEqual(
            self.client.get("/draft-assignments?include_cancelled=true").json(),
            [cancelled],
        )
        self.assertEqual(
            self.client.post(
                endpoint + "/cancel", json={"expected_revision": 2}
            ).json(),
            cancelled,
        )
        self.assertEqual(
            self.client.put(
                endpoint, json={**self.draft, "expected_revision": 2}
            ).status_code,
            409,
        )
        self.assertEqual(self.create().status_code, 201)
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(reopened.get(endpoint).json(), cancelled)

    def test_strict_inputs_calendar_dates_and_no_publish_path(self):
        for change in (
            {"work_item_id": True},
            {"crew_id": 1.5},
            {"crew_id": "1"},
            {"crew_id": 999},
            {"work_item_id": 999},
            {"slot": "Full day"},
            {"status": "Published"},
            {"publishable": True},
            {"local_date": "2026-02-29"},
            {"local_date": "2026-02-31"},
            {"local_date": "2026-1-01"},
            {"local_date": "0000-01-01"},
            {"local_date": "2026-12-31T00:00:00Z"},
            {"notes": "x\0y"},
            {"notes": "x" * 2001},
        ):
            with self.subTest(change=change):
                self.assertEqual(self.create(**change).status_code, 422)
        for value in ("2024-02-29", "0001-01-01", "9999-12-31"):
            self.assertEqual(local_date(value), value)
            self.assertEqual(self.create(local_date=value).status_code, 201)
        self.assertEqual(
            self.client.get(
                "/draft-assignments?start_date=2027-01-01&end_date=2026-12-31"
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.get("/draft-assignments?end_date=invalid").status_code, 422
        )
        self.assertEqual(self.client.get("/draft-assignments/999").status_code, 404)
        self.assertEqual(
            self.client.post(
                "/draft-assignments/999/cancel", json={"expected_revision": 1}
            ).status_code,
            404,
        )
        first = self.create().json()
        self.assertEqual(
            self.client.post(f"/draft-assignments/{first['id']}/publish").status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(f"/draft-assignments/{first['id']}").status_code, 405
        )
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            for sql in (
                "UPDATE DraftAssignments SET Status='Published'",
                "UPDATE DraftAssignments SET LocalDate='2026-02-31'",
                "UPDATE DraftAssignments SET Slot='Night'",
                f"DELETE FROM WorkItems WHERE Id={self.draft['work_item_id']}",
                f"DELETE FROM Crews WHERE Id={self.crew['id']}",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(sql)

    def test_concurrent_slot_creates_have_one_winner(self):
        store = AssignmentStore(self.database)

        def create(item):
            try:
                return store.save(
                    AssignmentDraft(**{**self.draft, "work_item_id": item["id"]})
                ).id
            except AssignmentConflict:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, self.project["work_items"]))
        self.assertEqual(sum(value is not None for value in results), 1)
        self.assertEqual(len(store.list()), 1)

    def test_read_failure_is_sanitized_and_project_edits_keep_assignment_links(self):
        first = self.create().json()
        project_input = {
            key: value for key, value in self.project.items() if key != "id"
        }
        self.client.put(
            f"/projects/{self.project['id']}",
            json={**project_input, "site_name": "Synthetic renamed site"},
        ).raise_for_status()
        read = self.client.get(f"/draft-assignments/{first['id']}").json()
        self.assertEqual(read["work_item_id"], first["work_item_id"])
        self.assertEqual(read["project_id"], first["project_id"])
        self.assertEqual(read["notes"], first["notes"])
        self.assertEqual(read["site_name"], "Synthetic renamed site")
        with patch(
            "rigarus_backend.assignment_store.connect",
            side_effect=sqlite3.OperationalError("Synthetic private path"),
        ):
            for url in ("/draft-assignments", f"/draft-assignments/{first['id']}"):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("Synthetic private path", response.text)

    def test_concurrent_edits_and_stale_cancel_cannot_overwrite_a_newer_draft(self):
        first = self.create().json()
        store = AssignmentStore(self.database)

        def edit(note):
            try:
                return store.save(
                    AssignmentDraft(**{**self.draft, "notes": note}), first["id"], 1
                )
            except AssignmentConflict:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(edit, ["Synthetic edit A", "Synthetic edit B"]))
        winner = next(row for row in results if row is not None)
        self.assertEqual(sum(row is not None for row in results), 1)
        self.assertEqual(winner.revision, 2)
        endpoint = f"/draft-assignments/{first['id']}"
        self.assertEqual(
            self.client.post(
                endpoint + "/cancel", json={"expected_revision": 1}
            ).status_code,
            409,
        )
        self.assertEqual(self.client.get(endpoint).json()["notes"], winner.notes)

    def test_failed_insert_update_cancel_roll_back_and_retry_without_diagnostics(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "CREATE TRIGGER synthetic_insert_failure AFTER INSERT ON DraftAssignments BEGIN SELECT RAISE(ABORT, 'Synthetic private database detail'); END"
            )
        self.assertEqual(self.create().status_code, 503)
        self.assertEqual(self.client.get("/draft-assignments").json(), [])
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("DROP TRIGGER synthetic_insert_failure")
        first = self.create().json()
        endpoint = f"/draft-assignments/{first['id']}"
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "CREATE TRIGGER synthetic_update_failure AFTER UPDATE ON DraftAssignments BEGIN SELECT RAISE(ABORT, 'Synthetic private database detail'); END"
            )
        for response in (
            self.client.put(
                endpoint,
                json={**self.draft, "notes": "Unsaved", "expected_revision": 1},
            ),
            self.client.post(endpoint + "/cancel", json={"expected_revision": 1}),
        ):
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("Synthetic private database detail", response.text)
            self.assertEqual(self.client.get(endpoint).json(), first)
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("DROP TRIGGER synthetic_update_failure")
        self.assertEqual(
            self.client.post(
                endpoint + "/cancel", json={"expected_revision": 1}
            ).status_code,
            200,
        )

    def test_six_migration_upgrade_preserves_all_data_and_rolls_back_then_retries(self):
        person = self.client.post(
            "/employees",
            json={
                "name": "Synthetic member",
                "home_crew_id": self.crew["id"],
                "skill_level": 2,
                "foreman_eligible": True,
            },
        ).json()
        self.client.put(
            f"/crews/{self.crew['id']}/foreman",
            json={"employee_id": person["id"], "expected_revision": 0},
        ).raise_for_status()
        self.client.post(
            "/rigs",
            json={"number": "0014", "type": "Synthetic", "notes": "Retained rig note"},
        ).raise_for_status()
        self.client.put(
            "/demo/note", json={"note": "Retained synthetic demo note"}
        ).raise_for_status()
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                remove_staffing_schema(connection)
                connection.execute("DROP TABLE DraftAssignments")
                connection.execute(
                    "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?",
                    (DRAFT_ASSIGNMENTS,),
                )
                connection.execute(
                    "CREATE TRIGGER synthetic_assignment_migration_failure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDraftAssignments' BEGIN SELECT RAISE(ABORT, 'Synthetic migration failure'); END"
                )
            tables = [
                "DemoProjects",
                "Projects",
                "WorkItems",
                "Crews",
                "Employees",
                "Rigs",
                "ForemanChanges",
                "__EFMigrationsHistory",
            ]
            original = {
                table: connection.execute(f"SELECT * FROM {table}").fetchall()
                for table in tables
            }
            with self.assertRaisesRegex(
                sqlite3.IntegrityError, "Synthetic migration failure"
            ):
                initialize_database(self.database)
            self.assertIsNone(
                connection.execute(
                    "SELECT name FROM sqlite_schema WHERE name='DraftAssignments'"
                ).fetchone()
            )
            for table, rows in original.items():
                self.assertEqual(
                    connection.execute(f"SELECT * FROM {table}").fetchall(), rows
                )
            connection.execute("DROP TRIGGER synthetic_assignment_migration_failure")
            initialize_database(self.database)
            initialize_database(self.database)
            for table, rows in original.items():
                if table != "__EFMigrationsHistory":
                    self.assertEqual(
                        connection.execute(f"SELECT * FROM {table}").fetchall(), rows
                    )
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM __EFMigrationsHistory"
                ).fetchone(),
                (12,),
            )
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone(), ("ok",)
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
        self.assertEqual(self.create().status_code, 201)


class AssignmentDomainTests(unittest.TestCase):
    def test_draft_domain_rejects_invalid_calendar_dates_ids_and_notes(self):
        valid = {
            "work_item_id": 1,
            "crew_id": 2,
            "local_date": "2024-02-29",
            "slot": "AM",
        }
        self.assertEqual(AssignmentDraft(**valid).local_date, "2024-02-29")
        for changes in (
            {"work_item_id": True},
            {"crew_id": 0},
            {"crew_id": 2.5},
            {"local_date": "1900-02-29"},
            {"local_date": "2026-02-30"},
            {"slot": "Night"},
            {"notes": "x\0y"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                AssignmentDraft(**{**valid, **changes})
        self.assertEqual(
            AssignmentDraft(**{**valid, "notes": "x" * 2000}).notes, "x" * 2000
        )
