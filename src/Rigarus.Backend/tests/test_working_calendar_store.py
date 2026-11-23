import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_assignments
from migration_fixture import remove_working_calendar_schema
from rigarus_backend.api import create_app
from rigarus_backend.storage import initialize_database
from rigarus_backend.working_calendar_store import (
    WorkingCalendarStore,
    CalendarConflict,
)


class WorkingCalendarStoreTests(unittest.TestCase):
    def setUp(self):
        test_assignments.AssignmentTests.setUp(self)
        self.url = f"/working-calendars/Project/{self.project['id']}"
        self.input = dict(
            start_date="2026-12-31",
            end_date="2027-01-01",
            slot="FullDay",
            state="Working",
            expected_revision=0,
        )

    def read(self, url=None):
        return self.client.get(
            url or self.url,
            params={"start_date": "2026-12-31", "end_date": "2027-01-01"},
        )

    def save(self, url=None, **changes):
        return self.client.put(url or self.url, json={**self.input, **changes})

    def assess(self, **changes):
        return self.client.get(
            "/working-calendars/assessment",
            params={k: v for k, v in {**self.draft, **changes}.items() if k != "notes"},
        )

    def dump(self):
        with closing(sqlite3.connect(self.database)) as c:
            return list(c.iterdump())

    def test_sparse_unknown_read_clear_history_and_restart(self):
        before = self.dump()
        self.assertEqual(self.read().json()["entries"], [])
        self.assertEqual(self.save(state="Unknown").json()["revision"], 0)
        self.assertEqual(self.dump(), before)
        self.assertEqual(len(self.save().json()["entries"]), 4)
        amended = self.save(
            slot="AM", end_date="2026-12-31", state="NotWorking", expected_revision=1
        ).json()
        self.assertEqual(amended["entries"][0]["state"], "NotWorking")
        self.assertEqual(amended["entries"][1]["state"], "Working")
        self.save(
            slot="PM", end_date="2026-12-31", state="Unknown", expected_revision=2
        ).raise_for_status()
        expected = self.read().json()
        self.assertEqual(len(expected["entries"]), 3)
        self.assertEqual(len(self.client.get(self.url + "/history").json()), 3)
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(
                reopened.get(
                    self.url,
                    params={"start_date": "2026-12-31", "end_date": "2027-01-01"},
                ).json(),
                expected,
            )
        self.assertEqual(
            self.save(
                slot="PM", end_date="2026-12-31", state="Unknown", expected_revision=3
            ).json()["revision"],
            3,
        )

    def test_all_workitems_inherit_project_and_advisory_draft_keeps_ids_notes(self):
        first = self.client.post("/draft-assignments", json=self.draft).json()
        second = self.client.post(
            "/draft-assignments",
            json={
                **self.draft,
                "work_item_id": self.project["work_items"][1]["id"],
                "slot": "PM",
            },
        ).json()
        self.assertEqual(
            second["calendar_assessment"]["project_id"], self.project["id"]
        )
        self.save(state="NotWorking").raise_for_status()
        a = self.client.get(f"/draft-assignments/{first['id']}").json()
        b = self.client.get(f"/draft-assignments/{second['id']}").json()
        for old, new in ((first, a), (second, b)):
            self.assertEqual(
                {k: v for k, v in new.items() if k != "calendar_assessment"},
                {k: v for k, v in old.items() if k != "calendar_assessment"},
            )
            self.assertEqual(new["calendar_assessment"]["status"], "Blocked")
            self.assertFalse(new["publishable"])
        saved = self.client.post(
            "/draft-assignments", json={**self.draft, "local_date": "2027-01-01"}
        )
        self.assertEqual(saved.status_code, 201)
        self.assertEqual(saved.json()["calendar_assessment"]["status"], "Blocked")
        self.assertEqual(
            self.client.post("/draft-assignments", json=self.draft).status_code, 409
        )
        self.assertEqual(
            self.client.put(
                f"/draft-assignments/{first['id']}",
                json={
                    **self.draft,
                    "notes": "Synthetic edited note",
                    "expected_revision": 1,
                },
            ).status_code,
            200,
        )

    def test_project_and_crew_isolation_assessment_conflict_and_weekend(self):
        self.save().raise_for_status()
        self.save(
            url=f"/working-calendars/Crew/{self.crew['id']}", state="NotWorking"
        ).raise_for_status()
        result = self.assess().json()
        self.assertEqual(result["status"], "Blocked")
        self.assertIn("CALENDAR_CONFLICT", [r["code"] for r in result["reasons"]])
        self.assertEqual(result["reasons"][1]["scope"], "Project")
        other = self.assess(crew_id=self.other_crew["id"]).json()
        self.assertEqual(other["status"], "Pending")
        self.assertEqual(other["crew_state"], "Unknown")
        weekend = self.assess(local_date="2027-01-02").json()
        self.assertIn(
            "WEEKEND_APPROVAL_PENDING", [r["code"] for r in weekend["reasons"]]
        )
        self.assertFalse(weekend["publishable"])
        self.assertEqual(
            self.read(
                url=f"/working-calendars/WorkItem/{self.project['work_items'][0]['id']}"
            ).status_code,
            422,
        )

    def test_strict_validation_stale_and_storage_errors_never_become_unknown(self):
        before = self.dump()
        for changes in (
            {"slot": "Evening"},
            {"state": "Available"},
            {"expected_revision": True},
            {"start_date": "2027-02-29"},
            {"end_date": "2026-12-30"},
            {"end_date": "2028-01-02"},
            {"publishable": True},
        ):
            self.assertEqual(self.save(**changes).status_code, 422, changes)
        self.assertEqual(
            self.read(url="/working-calendars/Project/900000").status_code, 404
        )
        self.assertEqual(self.dump(), before)
        self.save().raise_for_status()
        before = self.dump()
        self.assertEqual(self.save(state="NotWorking").status_code, 409)
        self.assertEqual(self.dump(), before)
        with patch(
            "rigarus_backend.working_calendar_store.connect",
            side_effect=sqlite3.OperationalError("Synthetic private path"),
        ):
            response = self.read()
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("Synthetic private path", response.text)

    def test_concurrent_saves_one_winner_and_partial_range_failure_rolls_back(self):
        store = WorkingCalendarStore(self.database)

        def write(state):
            try:
                store.save(
                    "Project",
                    self.project["id"],
                    "2026-12-31",
                    "2027-01-01",
                    "FullDay",
                    state,
                    0,
                )
                return "saved"
            except CalendarConflict:
                return "stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(
                list(pool.map(write, ["Working", "NotWorking"])), ["saved", "stale"]
            )
        with closing(sqlite3.connect(self.database)) as c:
            c.execute(
                "CREATE TRIGGER synthetic_calendar_failure BEFORE UPDATE ON WorkingCalendarCells WHEN NEW.Slot='PM' BEGIN SELECT RAISE(ABORT,'Synthetic cell failure'); END"
            )
        before = self.dump()
        current = self.read().json()["entries"][0]["state"]
        self.assertEqual(
            self.save(
                state="NotWorking" if current == "Working" else "Working",
                expected_revision=1,
            ).status_code,
            503,
        )
        self.assertEqual(self.dump(), before)
        with closing(sqlite3.connect(self.database)) as c:
            for table in ("WorkingCalendars", "WorkingCalendarChanges"):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(f"UPDATE {table} SET Id=Id")
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(f"DELETE FROM {table}")
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_schema_nine_upgrade_failure_rollback_retry_preserves_every_original_table(
        self,
    ):
        visit = self.client.post("/draft-assignments", json=self.draft).json()
        person = self.client.post(
            "/employees",
            json={
                "name": "Synthetic migration worker",
                "home_crew_id": self.crew["id"],
                "skill_level": 2,
                "foreman_eligible": True,
                "active": True,
            },
        ).json()
        self.client.put(
            f"/draft-assignments/{visit['id']}/staffing",
            json={"employee_ids": [person["id"]], "expected_revision": 1},
        ).raise_for_status()
        self.client.put(
            f"/employees/{person['id']}/availability",
            json={
                "start_date": "2026-12-31",
                "end_date": "2026-12-31",
                "slot": "AM",
                "state": "Available",
                "expected_revision": 0,
            },
        ).raise_for_status()
        self.client.put(
            f"/crews/{self.crew['id']}/foreman",
            json={"employee_id": person["id"], "expected_revision": 0},
        ).raise_for_status()
        self.client.post(
            "/rigs",
            json={
                "number": "SYN-007",
                "type": "Synthetic truck",
                "notes": "Synthetic retained rig note",
                "default_crew_id": self.crew["id"],
                "active": True,
            },
        ).raise_for_status()
        self.client.put(
            "/demo/note", json={"note": "Synthetic retained migration note"}
        ).raise_for_status()
        with closing(sqlite3.connect(self.database)) as c:
            remove_working_calendar_schema(c)
            c.commit()
            before = {
                t: c.execute(f'SELECT * FROM "{t}"').fetchall()
                for (t,) in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            c.execute(
                "CREATE TRIGGER synthetic_calendar_migration_failure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddWorkingCalendars' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as c:
            self.assertIsNone(
                c.execute(
                    "SELECT name FROM sqlite_schema WHERE name='WorkingCalendars'"
                ).fetchone()
            )
            for t, rows in before.items():
                self.assertEqual(c.execute(f'SELECT * FROM "{t}"').fetchall(), rows)
            c.execute("DROP TRIGGER synthetic_calendar_migration_failure")
        initialize_database(self.database)
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as c:
            for t, rows in before.items():
                if t != "__EFMigrationsHistory":
                    self.assertEqual(c.execute(f'SELECT * FROM "{t}"').fetchall(), rows)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
