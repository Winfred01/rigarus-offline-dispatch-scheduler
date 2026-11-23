import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch

from fastapi.testclient import TestClient

import unittest
import test_assignments
from migration_fixture import remove_staffing_schema
from rigarus_backend.api import create_app
from rigarus_backend.assignments import AssignmentConflict
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.storage import initialize_database


class StaffingTests(unittest.TestCase):
    # Reuse setup only; legacy tests remain in their own suite.
    def setUp(self):
        test_assignments.AssignmentTests.setUp(self)
        self.people = [
            self.client.post(
                "/employees",
                json={
                    "name": f"Synthetic worker {i}",
                    "home_crew_id": self.crew["id"],
                    "skill_level": 2,
                    "foreman_eligible": False,
                    "active": i != 3,
                },
            ).json()
            for i in range(1, 4)
        ]
        self.first = self.create().json()
        self.url = f"/draft-assignments/{self.first['id']}"

    def create(self, **changes):
        return test_assignments.AssignmentTests.create(self, **changes)

    def save_workers(self, ids, revision=1):
        return self.client.put(
            self.url + "/staffing",
            json={"employee_ids": ids, "expected_revision": revision},
        )

    def history(self):
        return self.client.get(self.url + "/staffing-history").json()

    def test_explicit_borrow_and_employee_query_do_not_expand_home_roster(self):
        other = self.create(crew_id=self.other_crew["id"]).json()
        borrowed = self.client.put(
            f"/draft-assignments/{other['id']}/staffing",
            json={"employee_ids": [self.people[0]["id"]], "expected_revision": 1},
        ).json()
        self.assertFalse(self.first["staffing"]["configured"])
        self.assertEqual(
            borrowed["staffing"]["workers"][0]["home_crew_id"], self.crew["id"]
        )
        self.assertFalse(borrowed["publishable"])
        for person, count in [(self.people[0], 1), (self.people[1], 0)]:
            rows = self.client.get(
                "/draft-assignments",
                params={
                    "employee_id": person["id"],
                    "start_date": "2026-12-31",
                    "end_date": "2027-01-01",
                },
            ).json()
            self.assertEqual(len(rows), count)
        self.assertEqual(self.client.get("/employees").json(), self.people)
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(
                reopened.get(f"/draft-assignments/{other['id']}").json(), borrowed
            )

    def test_selection_empty_inactive_noop_and_append_only_history(self):
        worker = self.people[2]["id"]
        saved = self.save_workers([worker]).json()
        self.assertFalse(saved["staffing"]["workers"][0]["active"])
        self.assertEqual(saved["staffing"]["workers"][0]["driver_status"], "Unverified")
        self.assertEqual(saved["revision"], 2)
        self.assertEqual(self.save_workers([worker], 2).json(), saved)
        empty = self.save_workers([], 2).json()
        self.assertTrue(empty["staffing"]["configured"])
        self.assertEqual(empty["staffing"]["workers"], [])
        self.assertEqual(len(self.history()), 2)
        self.assertIs(self.history()[0]["configured"], True)
        self.assertEqual(self.history()[1]["members"][0]["employee_id"], worker)
        with closing(sqlite3.connect(self.database)) as connection:
            for table in ("AssignmentStaffingMembers", "AssignmentStaffingChanges"):
                for sql in (
                    f"UPDATE {table} SET "
                    + (
                        "EmployeeName=EmployeeName"
                        if table.endswith("Members")
                        else "Configured=Configured"
                    ),
                    f"DELETE FROM {table}",
                ):
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(sql)

    def test_notes_keep_membership_but_visit_change_requires_reconfirmation(self):
        saved = self.save_workers([self.people[0]["id"]]).json()
        note = self.client.put(
            self.url,
            json={
                **self.draft,
                "notes": "Edited synthetic note",
                "expected_revision": saved["revision"],
            },
        ).json()
        self.assertEqual(note["staffing"], saved["staffing"])
        moved = self.client.put(
            self.url,
            json={**self.draft, "slot": "PM", "expected_revision": note["revision"]},
        ).json()
        self.assertFalse(moved["staffing"]["configured"])
        self.assertEqual(moved["staffing"]["workers"], [])
        self.assertEqual(self.history()[1]["slot"], "AM")
        self.assertEqual(
            self.client.get(
                "/draft-assignments", params={"employee_id": self.people[0]["id"]}
            ).json(),
            [],
        )
        moved_back = self.client.put(
            self.url, json={**self.draft, "expected_revision": moved["revision"]}
        ).json()
        self.assertFalse(moved_back["staffing"]["configured"])

    def test_cancel_retains_history_and_removes_employee_occupancy(self):
        saved = self.save_workers([self.people[0]["id"]]).json()
        self.assertEqual(
            self.client.post(
                self.url + "/cancel", json={"expected_revision": saved["revision"]}
            ).status_code,
            200,
        )
        self.assertEqual(self.save_workers([], 3).status_code, 409)
        self.assertEqual(len(self.history()), 1)
        self.assertEqual(
            self.client.get(
                "/draft-assignments", params={"employee_id": self.people[0]["id"]}
            ).json(),
            [],
        )

    def test_validation_stale_and_failed_write_are_atomic_and_sanitized(self):
        worker = self.people[0]["id"]
        for ids in ([worker, worker], [True], ["1"], [-1], [999999]):
            self.assertEqual(self.save_workers(ids).status_code, 422)
        self.assertEqual(self.history(), [])
        with closing(sqlite3.connect(self.database)) as c:
            c.execute(
                "CREATE TRIGGER synthetic_staffing_fail AFTER INSERT ON AssignmentStaffingMembers BEGIN SELECT RAISE(ABORT,'Synthetic private detail'); END"
            )
        response = self.save_workers([worker])
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Synthetic private detail", response.text)
        self.assertEqual(self.history(), [])
        self.assertEqual(self.client.get(self.url).json(), self.first)
        with closing(sqlite3.connect(self.database)) as c:
            c.execute("DROP TRIGGER synthetic_staffing_fail")
        self.save_workers([worker]).raise_for_status()
        self.assertEqual(self.save_workers([], 1).status_code, 409)
        self.assertEqual(len(self.history()), 1)

    def test_concurrent_writes_have_one_winner(self):
        store = StaffingStore(self.database)

        def choose(person):
            try:
                return store.save(self.first["id"], [person["id"]], 1)
            except AssignmentConflict:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(choose, self.people[:2]))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(len(self.history()), 1)

    def test_am_pm_independent_and_duplicate_employee_stays_unpublishable(self):
        worker = self.people[0]["id"]
        self.save_workers([worker]).raise_for_status()
        pm = self.create(slot="PM").json()
        other = self.create(crew_id=self.other_crew["id"]).json()
        for visit in (pm, other):
            saved = self.client.put(
                f"/draft-assignments/{visit['id']}/staffing",
                json={"employee_ids": [worker], "expected_revision": 1},
            ).json()
            self.assertFalse(saved["publishable"])
            self.assertEqual(saved["validation_status"], "Pending")
        # #15 later classifies overlapping worker occupancy; Draft choices are not approval.
        self.assertEqual(
            len(
                self.client.get(
                    "/draft-assignments", params={"employee_id": worker}
                ).json()
            ),
            3,
        )

    def test_seven_schema_upgrade_failure_rollback_retry_and_old_records(self):
        with closing(sqlite3.connect(self.database)) as c:
            remove_staffing_schema(c)
            c.commit()
            tables = [
                r[0]
                for r in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            before = {
                table: c.execute(f"SELECT * FROM {table}").fetchall()
                for table in tables
            }
            c.execute(
                "CREATE TRIGGER synthetic_staffing_migration_fail BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddAssignmentStaffing' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as c:
            self.assertIsNone(
                c.execute(
                    "SELECT name FROM sqlite_schema WHERE name='AssignmentStaffingChanges'"
                ).fetchone()
            )
            for table, rows in before.items():
                self.assertEqual(c.execute(f"SELECT * FROM {table}").fetchall(), rows)
            c.execute("DROP TRIGGER synthetic_staffing_migration_fail")
        initialize_database(self.database)
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as c:
            for table, rows in before.items():
                if table != "__EFMigrationsHistory":
                    self.assertEqual(
                        c.execute(f"SELECT * FROM {table}").fetchall(), rows
                    )
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.client.get(self.url).json(), self.first)

    def test_staffing_storage_read_failure_does_not_leak_paths(self):
        with patch(
            "rigarus_backend.staffing_store.connect",
            side_effect=sqlite3.OperationalError("Synthetic private path"),
        ):
            result = self.client.get(self.url + "/staffing-history")
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("Synthetic private path", result.text)

    def test_current_employee_edits_do_not_rewrite_recorded_snapshots(self):
        person = self.people[0]
        self.save_workers([person["id"]]).raise_for_status()
        history = self.history()
        self.client.put(
            f"/employees/{person['id']}",
            json={
                "name": "Synthetic renamed inactive worker",
                "home_crew_id": self.other_crew["id"],
                "skill_level": 2,
                "foreman_eligible": False,
                "active": False,
            },
        ).raise_for_status()
        current = self.client.get(self.url).json()["staffing"]["workers"][0]
        self.assertFalse(current["active"])
        self.assertEqual(current["home_crew_id"], self.other_crew["id"])
        self.assertEqual(self.history(), history)

    def test_context_change_rolls_back_with_audit_and_cannot_resurrect_members(self):
        person = self.people[0]["id"]
        saved = self.save_workers([person]).json()
        with closing(sqlite3.connect(self.database)) as c:
            c.execute(
                "CREATE TRIGGER synthetic_audit_fail AFTER INSERT ON AssignmentStaffingChanges BEGIN SELECT RAISE(ABORT,'Synthetic audit failure'); END"
            )
        response = self.client.put(
            self.url,
            json={
                **self.draft,
                "crew_id": self.other_crew["id"],
                "expected_revision": saved["revision"],
            },
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get(self.url).json(), saved)
        self.assertEqual(len(self.history()), 1)
        with closing(sqlite3.connect(self.database)) as c:
            c.execute("DROP TRIGGER synthetic_audit_fail")
        for change in (
            {"crew_id": self.other_crew["id"]},
            {"local_date": "2027-01-01"},
            {"work_item_id": self.project["work_items"][1]["id"]},
        ):
            saved = self.client.put(
                self.url,
                json={**self.draft, **change, "expected_revision": saved["revision"]},
            ).json()
            self.assertFalse(saved["staffing"]["configured"])
            self.assertEqual(saved["staffing"]["workers"], [])
