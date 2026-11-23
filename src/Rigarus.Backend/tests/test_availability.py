import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_assignments
from migration_fixture import remove_availability_schema
from rigarus_backend.api import create_app
from rigarus_backend.availability import (
    AvailabilityConflict,
    AvailabilityDraft,
    range_dates,
)
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.storage import initialize_database


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        test_assignments.AssignmentTests.setUp(self)
        self.people = [
            self.client.post(
                "/employees",
                json={
                    "name": f"Synthetic available worker {i}",
                    "home_crew_id": self.crew["id"],
                    "skill_level": 2,
                    "foreman_eligible": False,
                    "active": i == 1,
                },
            ).json()
            for i in (1, 2)
        ]
        self.employee_id = self.people[0]["id"]
        self.url = f"/employees/{self.employee_id}/availability"
        self.input = {
            "start_date": "2026-12-31",
            "end_date": "2027-01-01",
            "slot": "FullDay",
            "state": "Available",
            "expected_revision": 0,
        }

    def read(self, **query):
        return self.client.get(
            self.url,
            params={"start_date": "2026-12-27", "end_date": "2027-01-02", **query},
        )

    def save(self, **changes):
        return self.client.put(self.url, json={**self.input, **changes})

    def history(self):
        return self.client.get(self.url + "/history").json()

    def test_blank_unknown_full_day_inclusive_and_restart(self):
        self.assertEqual(self.read().json()["entries"], [])
        self.assertEqual(self.read().json()["revision"], 0)
        saved = self.save().json()
        self.assertEqual(len(saved["entries"]), 4)
        self.assertEqual(
            saved["entries"][0],
            {"local_date": "2026-12-31", "slot": "AM", "state": "Available"},
        )
        self.assertEqual(
            saved["entries"][-1],
            {"local_date": "2027-01-01", "slot": "PM", "state": "Available"},
        )
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(
                reopened.get(
                    self.url,
                    params={
                        "start_date": self.input["start_date"],
                        "end_date": self.input["end_date"],
                    },
                ).json(),
                saved,
            )
        self.assertEqual(self.client.get("/employees").json(), self.people)

    def test_overlap_clear_noop_and_other_employee_slot_preserved(self):
        self.save().raise_for_status()
        result = self.save(
            start_date="2026-12-31",
            end_date="2026-12-31",
            slot="AM",
            state="Unavailable",
            expected_revision=1,
        ).json()
        self.assertEqual(result["entries"][1]["state"], "Available")
        self.assertEqual(result["entries"][0]["state"], "Unavailable")
        cleared = self.save(
            start_date="2026-12-31",
            end_date="2026-12-31",
            slot="PM",
            state="Unknown",
            expected_revision=2,
        ).json()
        self.assertEqual(
            cleared["entries"],
            [{"local_date": "2026-12-31", "slot": "AM", "state": "Unavailable"}],
        )
        self.assertEqual(
            self.save(
                start_date="2026-12-31",
                end_date="2026-12-31",
                slot="PM",
                state="Unknown",
                expected_revision=3,
            ).json(),
            cleared,
        )
        self.assertEqual(len(self.history()), 3)
        self.assertEqual(len(self.read().json()["entries"]), 3)
        other = self.client.get(
            f"/employees/{self.people[1]['id']}/availability",
            params={"start_date": "2026-12-31", "end_date": "2027-01-01"},
        ).json()
        self.assertEqual(other["entries"], [])

    def test_advisory_slot_query_never_changes_visits_or_workers_or_home_crew(self):
        assignment = test_assignments.AssignmentTests.create(self).json()
        assignment = self.client.put(
            f"/draft-assignments/{assignment['id']}/staffing",
            json={"employee_ids": [self.employee_id], "expected_revision": 1},
        ).json()
        self.save(state="Unavailable").raise_for_status()
        slot = self.client.get(
            "/employee-availability", params={"local_date": "2026-12-31", "slot": "AM"}
        ).json()
        self.assertEqual(
            slot,
            {
                "local_date": "2026-12-31",
                "slot": "AM",
                "employees": [
                    {"employee_id": self.employee_id, "state": "Unavailable"},
                    {"employee_id": self.people[1]["id"], "state": "Unknown"},
                ],
            },
        )
        self.assertEqual(
            self.client.get(f"/draft-assignments/{assignment['id']}").json(), assignment
        )
        self.assertFalse(assignment["publishable"])
        self.assertEqual(self.client.get("/employees").json(), self.people)

    def test_inactive_employee_records_are_retained_without_reactivation(self):
        url = f"/employees/{self.people[1]['id']}/availability"
        result = self.client.put(url, json=self.input)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json()["entries"]), 4)
        self.assertFalse(self.client.get("/employees").json()[1]["active"])
        self.assertEqual(
            self.client.get("/employees").json()[1]["driver_status"], "Unverified"
        )

    def test_cancel_read_only_and_history_immutable(self):
        self.save().raise_for_status()

        def contents():
            with closing(sqlite3.connect(self.database)) as c:
                return c.execute(
                    "select * from EmployeeAvailability"
                ).fetchall(), c.execute(
                    "select * from EmployeeAvailabilityChanges"
                ).fetchall()

        before = contents()
        self.read().raise_for_status()
        self.history()
        self.assertEqual(contents(), before)
        with closing(sqlite3.connect(self.database)) as c:
            for sql in (
                "UPDATE EmployeeAvailabilityChanges SET State=State",
                "DELETE FROM EmployeeAvailabilityChanges",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)

    def test_strict_validation_date_limits_and_missing_employee(self):
        for change in (
            {"start_date": "2026-02-29"},
            {"end_date": "2026-12-30"},
            {"start_date": "2026-1-01"},
            {"start_date": "0000-01-01"},
            {"end_date": "2028-01-01"},
            {"slot": "all"},
            {"state": "Approved"},
            {"expected_revision": True},
            {"publishable": True},
        ):
            self.assertEqual(self.save(**change).status_code, 422, change)
        self.assertEqual(
            self.client.put(
                "/employees/9999/availability", json=self.input
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                "/employee-availability",
                params={"local_date": "2026-12-31", "slot": "FullDay"},
            ).status_code,
            422,
        )
        self.assertEqual(self.history(), [])

    def test_stale_and_concurrent_saves_have_one_winner(self):
        store = AvailabilityStore(self.database)

        def save(state):
            try:
                return store.save(
                    self.employee_id,
                    AvailabilityDraft("2026-12-31", "2027-01-01", "AM", state),
                    0,
                )
            except AvailabilityConflict:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(save, ["Available", "Unavailable"]))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(self.save().status_code, 409)
        self.assertEqual(len(self.history()), 1)

    def test_cell_failure_rolls_back_history_and_retry_succeeds(self):
        with closing(sqlite3.connect(self.database)) as c:
            c.execute(
                "CREATE TRIGGER synthetic_availability_failure AFTER INSERT ON EmployeeAvailability WHEN NEW.Slot='PM' BEGIN SELECT RAISE(ABORT,'Synthetic private path'); END"
            )
        result = self.save()
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("Synthetic private path", result.text)
        self.assertEqual(self.read().json()["entries"], [])
        self.assertEqual(self.history(), [])
        with closing(sqlite3.connect(self.database)) as c:
            c.execute("DROP TRIGGER synthetic_availability_failure")
        self.save().raise_for_status()
        with closing(sqlite3.connect(self.database)) as c:
            c.execute(
                "CREATE TRIGGER synthetic_clear_failure AFTER DELETE ON EmployeeAvailability BEGIN SELECT RAISE(ABORT,'Synthetic clear failure'); END"
            )
        self.assertEqual(
            self.save(state="Unknown", expected_revision=1).status_code, 503
        )
        self.assertEqual(len(self.read().json()["entries"]), 4)
        self.assertEqual(len(self.history()), 1)

    def test_migration_eight_to_nine_failure_rollback_retry_preserves_all_tables(self):
        assignment = test_assignments.AssignmentTests.create(self).json()
        self.client.put(
            f"/draft-assignments/{assignment['id']}/staffing",
            json={"employee_ids": [self.employee_id], "expected_revision": 1},
        ).raise_for_status()
        with closing(sqlite3.connect(self.database)) as c:
            remove_availability_schema(c)
            c.commit()
            before = {
                t: c.execute(f'SELECT * FROM "{t}"').fetchall()
                for (t,) in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            c.execute(
                "CREATE TRIGGER synthetic_availability_migration_failure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddEmployeeAvailability' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as c:
            self.assertIsNone(
                c.execute(
                    "SELECT name FROM sqlite_schema WHERE name='EmployeeAvailability'"
                ).fetchone()
            )
            for table, rows in before.items():
                self.assertEqual(c.execute(f'SELECT * FROM "{table}"').fetchall(), rows)
            c.execute("DROP TRIGGER synthetic_availability_migration_failure")
        initialize_database(self.database)
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as c:
            for table, rows in before.items():
                if table != "__EFMigrationsHistory":
                    self.assertEqual(
                        c.execute(f'SELECT * FROM "{table}"').fetchall(), rows
                    )
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_read_failure_is_not_unknown_and_diagnostics_are_sanitized(self):
        with patch(
            "rigarus_backend.availability_store.connect",
            side_effect=sqlite3.OperationalError("Synthetic private path"),
        ):
            for url, params in [
                (self.url, {"start_date": "2026-12-31", "end_date": "2026-12-31"}),
                ("/employee-availability", {"local_date": "2026-12-31", "slot": "AM"}),
                (self.url + "/history", {}),
            ]:
                response = self.client.get(url, params=params)
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("Synthetic private path", response.text)

    def test_leap_day_weekend_and_last_supported_date(self):
        self.assertEqual(
            range_dates("2024-02-28", "2024-03-01"),
            ("2024-02-28", "2024-02-29", "2024-03-01"),
        )
        self.assertEqual(
            self.save(
                start_date="9999-12-31", end_date="9999-12-31", slot="AM"
            ).status_code,
            200,
        )
        data = self.client.get(
            self.url, params={"start_date": "9999-12-31", "end_date": "9999-12-31"}
        ).json()
        self.assertEqual(
            data["entries"],
            [{"local_date": "9999-12-31", "slot": "AM", "state": "Available"}],
        )
        self.assertEqual(len(range_dates("2024-01-01", "2024-12-31")), 366)
