import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_assignments as fixtures
import test_recommendation_adapter as snapshots
from migration_fixture import remove_day_schema
from rigarus_backend import storage, recommendation_adapter as adapter
from rigarus_backend.api import create_app
from rigarus_backend.assignment_store import AssignmentStore
from rigarus_backend.assignments import AssignmentConflict, AssignmentDraft
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.day_compatibility import compatibility_report
from rigarus_backend.day_drafts import (
    DayDraft,
    ConfirmedRemainingDays,
    legacy_day_observation,
)
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.daily_weekend_migration import DAILY_WEEKEND
from rigarus_backend.roster import EmployeeDraft
from rigarus_backend.roster_store import EmployeeStore
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.working_calendar_store import WorkingCalendarStore

DAY = "2026-12-31"


class DayDraftTests(unittest.TestCase):
    setUp = fixtures.AssignmentTests.setUp

    def store(self):
        return DayDraftStore(self.database)

    def day(self, **changes):
        return DayDraft(
            **dict(
                work_item_id=self.draft["work_item_id"],
                crew_id=self.crew["id"],
                local_date=DAY,
                notes="Synthetic full day",
                **changes,
            )
        )

    def legacy(self, slot="AM", **changes):
        return AssignmentStore(self.database).save(
            AssignmentDraft(**(self.draft | dict(slot=slot) | changes))
        )

    def digest(self):
        with closing(storage.connect(self.database, read_only=True)) as c:
            return logical_digest(c)

    def test_daily_create_edit_cancel_restart_history(self):
        store = self.store()
        one = store.save(self.day())
        self.assertEqual(one["scheduling_unit"], "FullDay")
        self.assertNotIn("slot", one)
        self.assertEqual(one["project_id"], self.project["id"])
        self.assertEqual(one["validation_status"], "Pending")
        self.assertFalse(one["applyable"] or one["publishable"])
        edited = store.save(
            replace(self.day(), local_date="2027-01-01", notes="Synthetic edited"),
            one["id"],
            1,
        )
        self.assertEqual(edited["revision"], 2)
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(
                reopened.get(f"/day-draft-assignments/{one['id']}").json()["notes"],
                "Synthetic edited",
            )
        cancelled = store.cancel(one["id"], 2)
        self.assertEqual(cancelled["status"], "Cancelled")
        self.assertEqual(cancelled["revision"], 3)
        self.assertEqual(store.cancel(one["id"], 3), cancelled)
        self.assertEqual(len(store.history(one["id"])), 3)
        self.assertEqual(store.history(one["id"])[-1]["local_date"], DAY)

    def test_same_crew_date_rejected_other_crew_and_other_date_allowed(self):
        one = self.store().save(self.day())
        with self.assertRaisesRegex(AssignmentConflict, "Full-Day Draft"):
            self.store().save(
                replace(self.day(), work_item_id=self.project["work_items"][1]["id"])
            )
        self.store().save(replace(self.day(), crew_id=self.other_crew["id"]))
        self.store().save(replace(self.day(), local_date="2027-01-01"))
        self.assertEqual(len(self.store().list(DAY, "2027-01-01")), 3)
        self.store().cancel(one["id"], 1)
        self.store().save(self.day())

    def test_daily_conflicts_with_either_legacy_half_including_same_workitem(self):
        for half in ("AM", "PM"):
            with self.subTest(half=half):
                row = self.legacy(half)
                before = self.digest()
                with self.assertRaisesRegex(
                    AssignmentConflict, f"Legacy #{row.id} {half}"
                ):
                    self.store().save(self.day())
                self.assertEqual(self.digest(), before)
                AssignmentStore(self.database).cancel(row.id, row.revision)
        self.store().save(self.day())

    def test_legacy_api_cannot_bypass_daily_occupancy_and_cancel_releases(self):
        one = self.store().save(self.day())
        for half in ("AM", "PM"):
            response = self.client.post(
                "/draft-assignments", json=self.draft | dict(slot=half)
            )
            self.assertEqual(response.status_code, 409)
            self.assertIn("Full-Day", response.json()["detail"])
        self.store().cancel(one["id"], 1)
        self.assertEqual(
            self.client.post("/draft-assignments", json=self.draft).status_code, 201
        )

    def test_old_update_cannot_move_into_daily_date(self):
        row = self.legacy(local_date="2027-01-01")
        self.store().save(self.day())
        with self.assertRaises(AssignmentConflict):
            AssignmentStore(self.database).save(
                AssignmentDraft(**self.draft), row.id, row.revision
            )
        self.assertEqual(
            AssignmentStore(self.database).read(row.id).local_date, "2027-01-01"
        )

    def test_daily_edit_collision_rolls_back_and_revision_conflict(self):
        one = self.store().save(self.day())
        two = self.store().save(replace(self.day(), local_date="2027-01-01"))
        before = self.digest()
        with self.assertRaises(AssignmentConflict):
            self.store().save(self.day(), two["id"], 1)
        with self.assertRaises(AssignmentConflict):
            self.store().save(replace(self.day(), notes="Stale"), one["id"], 2)
        self.assertEqual(self.digest(), before)
        self.assertEqual(self.store().save(self.day(), one["id"], 1), one)

    def test_explicit_staffing_empty_unknown_borrowing_and_rollback(self):
        person = EmployeeStore(self.database).save(
            EmployeeDraft("Synthetic borrowed", self.other_crew["id"], 2, False)
        )
        draft = replace(self.day(), employee_ids=(person.id,))
        one = self.store().save(draft)
        self.assertEqual(one["employee_ids"], (person.id,))
        self.assertTrue(one["staffing_configured"])
        before = self.digest()
        with self.assertRaises(ValueError):
            self.store().save(
                replace(draft, employee_ids=(person.id, 999999)), one["id"], 1
            )
        self.assertEqual(self.digest(), before)
        self.store().save(replace(draft, notes="Synthetic note"), one["id"], 1)
        self.assertEqual(self.store().read(one["id"])["employee_ids"], (person.id,))
        empty = self.store().save(replace(draft, employee_ids=()), one["id"], 2)
        self.assertTrue(empty["staffing_configured"])
        self.assertEqual(empty["employee_ids"], ())
        unknown = self.store().save(self.day(), one["id"], 3)
        self.assertFalse(unknown["staffing_configured"])
        self.assertIsNone(unknown["employee_ids"])
        self.assertEqual(
            EmployeeStore(self.database).search("Synthetic borrowed")[0].home_crew_id,
            self.other_crew["id"],
        )
        self.assertEqual(
            self.store().history(one["id"])[-1]["workers"][0][0], person.id
        )

    def test_partial_history_append_failure_rolls_back_entire_create(self):
        before = self.digest()
        with patch(
            "rigarus_backend.day_draft_store.append_change",
            side_effect=sqlite3.OperationalError("Synthetic failure"),
        ):
            with self.assertRaises(sqlite3.Error):
                self.store().save(self.day())
        self.assertEqual(self.digest(), before)

    def test_direct_sql_guards_on_insert_update_and_history(self):
        one = self.store().save(self.day())
        legacy = self.legacy(local_date="2027-01-01")
        with closing(storage.connect(self.database)) as c:
            for sql, args in [
                (
                    "UPDATE DraftAssignments SET LocalDate=? WHERE Id=?",
                    (DAY, legacy.id),
                ),
                (
                    "UPDATE DayDraftAssignments SET LocalDate=? WHERE Id=?",
                    ("2027-01-01", one["id"]),
                ),
                ("UPDATE DayDraftChanges SET Notes='overwrite'", ()),
                ("DELETE FROM DayDraftChanges", ()),
                ("DELETE FROM DayDraftAssignments", ()),
                ("DELETE FROM WorkItems WHERE Id=?", (self.draft["work_item_id"],)),
            ]:
                with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                    with c:
                        c.execute(sql, args)
            with self.assertRaises(sqlite3.IntegrityError), c:
                c.execute(
                    "INSERT INTO DraftAssignments(WorkItemId,CrewId,LocalDate,Slot,Notes,Status,Revision,CreatedAt,UpdatedAt) VALUES(?,?,?,'PM','','Draft',1,'t','t')",
                    (self.draft["work_item_id"], self.crew["id"], DAY),
                )
            with self.assertRaises(sqlite3.IntegrityError), c:
                c.execute(
                    "INSERT INTO DayDraftAssignments(WorkItemId,CrewId,LocalDate,Notes,Status,Revision,CreatedAt,UpdatedAt) VALUES(?,?,?,'','Draft',1,'t','t')",
                    (self.draft["work_item_id"], self.crew["id"], "2027-01-01"),
                )

    def test_concurrent_daily_and_cross_model_writers_cannot_double_book(self):
        for cross, date in ((False, "2027-02-01"), (True, "2027-02-02")):
            barrier = threading.Barrier(2)

            def writer(index):
                barrier.wait()
                try:
                    if cross and index:
                        return self.legacy(local_date=date).id
                    return self.store().save(replace(self.day(), local_date=date))["id"]
                except AssignmentConflict:
                    return "conflict"

            with ThreadPoolExecutor(2) as pool:
                results = list(pool.map(writer, range(2)))
            self.assertEqual(results.count("conflict"), 1)

    def test_api_default_gate_strict_input_and_opt_in_crud(self):
        body = {k: v for k, v in self.draft.items() if k != "slot"}
        self.assertEqual(
            self.client.post("/day-draft-assignments", json=body).status_code, 409
        )
        with TestClient(
            create_app(self.database, enable_day_draft_writes=True)
        ) as daily:
            for changes in (
                {"slot": "AM"},
                {"slot": "PM"},
                {"duration": 0.5},
                {"crew_id": True},
                {"local_date": "2027-02-29"},
                {"employee_ids": [1, 1]},
                {"work_item_id": 999999},
            ):
                with self.subTest(changes=changes):
                    self.assertEqual(
                        daily.post(
                            "/day-draft-assignments", json=body | changes
                        ).status_code,
                        422,
                    )
            one = daily.post("/day-draft-assignments", json=body)
            self.assertEqual(one.status_code, 201)
            one = one.json()
            self.assertEqual(
                daily.get(f"/day-draft-assignments/{one['id']}").json(), one
            )
            self.assertEqual(
                daily.put(
                    f"/day-draft-assignments/{one['id']}",
                    json=body | dict(notes="Synthetic API edit", expected_revision=1),
                ).status_code,
                200,
            )
            self.assertEqual(
                daily.post(
                    f"/day-draft-assignments/{one['id']}/cancel",
                    json=dict(expected_revision=2),
                ).status_code,
                200,
            )
            self.assertEqual(
                len(daily.get(f"/day-draft-assignments/{one['id']}/history").json()), 3
            )
            self.assertEqual(daily.get("/day-draft-assignments/99999").status_code, 404)

    def test_local_date_boundaries_and_invalid_domain_inputs(self):
        for date in (
            "0001-01-01",
            "9999-12-31",
            "2028-02-29",
            "2027-03-14",
            "2027-11-07",
            "2027-01-01",
        ):
            self.assertEqual(
                self.store().save(replace(self.day(), local_date=date))["local_date"],
                date,
            )
        for kwargs in (
            dict(local_date="2027-02-29"),
            dict(work_item_id=False),
            dict(crew_id=0),
            dict(employee_ids=(1, 1)),
            dict(notes="\0"),
        ):
            with self.assertRaises(ValueError):
                replace(self.day(), **kwargs)

    def test_compatibility_report_retains_single_same_and_different_halves(self):
        one = self.legacy()
        two = self.legacy("PM", work_item_id=self.project["work_items"][1]["id"])
        self.legacy(local_date="2027-01-01")
        self.legacy("PM", local_date="2027-01-01")
        self.legacy("PM", local_date="2027-01-02")
        before = self.digest()
        report = compatibility_report(self.database, DAY, "2027-01-02")
        self.assertEqual(len(report["visits"]), 3)
        first = report["visits"][0]
        self.assertIn("Different WorkItems", first["reason"])
        self.assertEqual([r["id"] for r in first["original_records"]], [one.id, two.id])
        self.assertIn("Same WorkItem", report["visits"][1]["reason"])
        self.assertIn("Single", report["visits"][2]["reason"])
        self.assertEqual(report["converted_records"], 0)
        self.assertEqual(self.digest(), before)
        self.assertEqual(
            self.client.get(f"/draft-assignments/{one.id}").json()[
                "compatibility_status"
            ],
            "Needs Review",
        )

    def test_partial_mixed_availability_and_calendar_report_never_grants_day(self):
        person = EmployeeStore(self.database).save(
            EmployeeDraft("Synthetic partial", self.crew["id"], 2, False)
        )
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(DAY, DAY, "AM", "Available"), 0
        )
        WorkingCalendarStore(self.database).save(
            "Crew", self.crew["id"], DAY, DAY, "AM", "Working", 0
        )
        report = compatibility_report(self.database, DAY, DAY)
        self.assertEqual(
            {e["daily_observation"] for e in report["evidence"]}, {"Unknown"}
        )
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(DAY, DAY, "PM", "Unavailable"), 1
        )
        WorkingCalendarStore(self.database).save(
            "Crew", self.crew["id"], DAY, DAY, "PM", "NotWorking", 1
        )
        report = compatibility_report(self.database, DAY, DAY)
        self.assertEqual(
            {e["daily_observation"] for e in report["evidence"]},
            {"Unavailable", "NotWorking"},
        )
        self.assertTrue(
            all(
                e["mixed_or_partial"] and e["conversion_required"]
                for e in report["evidence"]
            )
        )

    def test_compatibility_report_limit_and_sql_failure_are_not_empty_success(self):
        self.assertEqual(
            self.client.get(
                "/day-draft-assignments/legacy-compatibility",
                params=dict(start_date="2027-02-29", end_date=DAY),
            ).status_code,
            422,
        )
        with patch(
            "rigarus_backend.day_compatibility.connect",
            side_effect=sqlite3.OperationalError("Synthetic failure"),
        ):
            r = self.client.get(
                "/day-draft-assignments/legacy-compatibility",
                params=dict(start_date=DAY, end_date=DAY),
            )
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("Synthetic", r.text)

    def test_schema12_backup_upgrade_preserves_all_records_fks_and_history(self):
        am = self.legacy()
        self.legacy("PM", work_item_id=self.project["work_items"][1]["id"])
        person = EmployeeStore(self.database).save(
            EmployeeDraft("Synthetic preserved", self.crew["id"], 3, True)
        )
        StaffingStore(self.database).save(am.id, [person.id], 1)
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(DAY, DAY, "AM", "Available"), 0
        )
        with closing(storage.connect(self.database)) as c, c:
            remove_day_schema(c)
        with closing(storage.connect(self.database)) as c:
            expected = logical_digest(c)
            original = {
                t: c.execute(f'SELECT * FROM "{t}"').fetchall()
                for (t,) in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table'"
                ).fetchall()
            }
        storage.initialize_database(self.database)
        backups = list(self.database.parent.glob("*.before-day-*.bak"))
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as c:
            self.assertEqual(logical_digest(c), expected)
            self.assertEqual(
                c.execute("SELECT count(*) FROM __EFMigrationsHistory").fetchone(),
                (12,),
            )
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
        with closing(storage.connect(self.database)) as c:
            for t, values in original.items():
                current = c.execute(f'SELECT * FROM "{t}"').fetchall()
                self.assertEqual(
                    current[: len(values)] if t == "__EFMigrationsHistory" else current,
                    values,
                )
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(
                c.execute("SELECT count(*) FROM DayDraftAssignments").fetchone(), (0,)
            )
        storage.initialize_database(self.database)
        self.assertEqual(len(list(self.database.parent.glob("*.before-day-*.bak"))), 1)

    def test_migration_ddl_failure_rolls_back_retry_and_backup_failure_no_ddl(self):
        self.legacy()
        with closing(storage.connect(self.database)) as c, c:
            remove_day_schema(c)
            c.execute(
                "CREATE TRIGGER SyntheticDayFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDayDraftCompatibility' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.Error):
            storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticDayFailure")
        before = self.digest()
        with patch.object(
            storage,
            "verified_upgrade_backup",
            side_effect=OSError("Synthetic backup disk error"),
        ):
            with self.assertRaises(OSError):
                storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute(
                    "SELECT MigrationId FROM __EFMigrationsHistory ORDER BY MigrationId DESC LIMIT 1"
                ).fetchone(),
                (DAILY_WEEKEND,),
            )

    def test_daily_id_namespace_does_not_replace_legacy_id(self):
        legacy = self.legacy(local_date="2027-01-01")
        daily = self.store().save(self.day())
        self.assertEqual(legacy.id, daily["id"])
        self.assertEqual(
            self.client.get(f"/draft-assignments/{legacy.id}").json()["local_date"],
            "2027-01-01",
        )
        self.assertEqual(
            self.client.get(f"/day-draft-assignments/{daily['id']}").json()[
                "local_date"
            ],
            DAY,
        )


class DailySnapshotBoundaryTests(unittest.TestCase):
    setUp = snapshots.AdapterTests.setUp
    calendar = snapshots.AdapterTests.calendar
    snapshot = snapshots.AdapterTests.snapshot

    def test_concurrent_day_commit_is_not_mixed_into_a_pinned_legacy_read(self):
        before = self.snapshot()
        original = adapter._read_sources

        def commit_after_pin(*args):
            with ThreadPoolExecutor(1) as pool:
                pool.submit(
                    DayDraftStore(self.database).save,
                    DayDraft(self.work.id, self.c1.id, "2026-11-23"),
                ).result(timeout=5)
            return original(*args)

        with patch.object(adapter, "_read_sources", side_effect=commit_after_pin):
            pinned = self.snapshot()
        self.assertEqual(pinned.input_fingerprint, before.input_fingerprint)
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, pinned).status, "Stale"
        )

    def test_legacy_adapter_refuses_day_data_and_old_snapshot_becomes_stale(self):
        old = self.snapshot()
        day = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2026-11-23")
        )
        with self.assertRaisesRegex(
            adapter.SnapshotContextError, "DAY_BASED_ADAPTER_REQUIRED"
        ):
            self.snapshot()
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, old).status, "Stale"
        )
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, old).reason,
            "DAY_BASED_ADAPTER_REQUIRED",
        )
        DayDraftStore(self.database).cancel(day["id"], 1)
        with self.assertRaises(adapter.SnapshotContextError):
            self.snapshot()

    def test_out_of_horizon_daily_record_does_not_change_legacy_scope(self):
        old = self.snapshot()
        DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2027-01-01")
        )
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, old).status, "Current"
        )


class DayContractTests(unittest.TestCase):
    def test_positive_explicit_days_and_pure_immutable_contract(self):
        with (
            patch("builtins.open", side_effect=AssertionError("No files")),
            patch("sqlite3.connect", side_effect=AssertionError("No SQL")),
        ):
            remaining = ConfirmedRemainingDays(4, True)
            self.assertEqual(remaining.days, 4)
            for value in (None, 0, -1, 0.5, True, "4"):
                with self.assertRaises(ValueError):
                    ConfirmedRemainingDays(value, True)
            with self.assertRaises(ValueError):
                ConfirmedRemainingDays(4, False)
            with self.assertRaises(FrozenInstanceError):
                remaining.days = 5
            result = legacy_day_observation(
                "Calendar",
                [dict(slot="AM", state="Working"), dict(slot="PM", state="Working")],
            )
            self.assertEqual(result["daily_observation"], "Working")
            self.assertTrue(result["conversion_required"])
            with self.assertRaises(ValueError):
                legacy_day_observation(
                    "Availability", [dict(slot="AM", state="Available")] * 2
                )


class AdditionalMigrationTests(unittest.TestCase):
    setUp = fixtures.AssignmentTests.setUp
    store = DayDraftTests.store
    day = DayDraftTests.day
    legacy = DayDraftTests.legacy
    digest = DayDraftTests.digest

    def test_missing_staff_history_or_mismatched_context_fails_closed(self):
        one = self.store().save(self.day())
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "UPDATE DayDraftAssignments SET Notes='Synthetic unexpected change' WHERE Id=?",
                (one["id"],),
            )
        with self.assertRaisesRegex(ValueError, "disagree"):
            self.store().read(one["id"])

    def test_cancelled_rows_cannot_be_reactivated_over_other_model(self):
        one = self.store().save(self.day())
        self.store().cancel(one["id"], 1)
        legacy = self.legacy()
        with closing(storage.connect(self.database)) as c, c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(
                    "UPDATE DayDraftAssignments SET Status='Draft' WHERE Id=?",
                    (one["id"],),
                )
        AssignmentStore(self.database).cancel(legacy.id, 1)
        other = self.store().save(self.day())
        with closing(storage.connect(self.database)) as c, c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(
                    "UPDATE DraftAssignments SET Status='Draft' WHERE Id=?",
                    (legacy.id,),
                )
        self.assertEqual(self.store().read(other["id"])["status"], "Draft")

    def test_backup_verification_failure_removes_only_own_incomplete_file(self):
        self.legacy()
        with closing(storage.connect(self.database)) as c, c:
            remove_day_schema(c)
        before = self.digest()
        from rigarus_backend import day_backup

        real = day_backup.logical_digest
        calls = 0

        def wrong_target(connection, **kwargs):
            nonlocal calls
            calls += 1
            return real(connection, **kwargs) if calls == 1 else "Synthetic mismatch"

        with patch.object(day_backup, "logical_digest", side_effect=wrong_target):
            with self.assertRaisesRegex(sqlite3.DatabaseError, "differs"):
                storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        self.assertEqual(list(self.database.parent.glob("*.before-day-*.bak")), [])

    def test_migration_lock_failure_does_not_change_source_or_create_backup(self):
        with closing(storage.connect(self.database)) as c, c:
            remove_day_schema(c)
        before = self.digest()
        real = storage.connect

        def short_wait(*args, **kwargs):
            c = real(*args, **kwargs)
            c.execute("PRAGMA busy_timeout=25")
            return c

        with closing(real(self.database)) as writer:
            writer.execute("BEGIN IMMEDIATE")
            with patch.object(storage, "connect", side_effect=short_wait):
                with self.assertRaises(sqlite3.OperationalError):
                    storage.initialize_database(self.database)
            writer.rollback()
        self.assertEqual(self.digest(), before)
        self.assertEqual(list(self.database.parent.glob("*.before-day-*.bak")), [])

    def test_compatibility_reader_keeps_one_wal_view_across_sources(self):
        legacy = self.legacy()
        person = EmployeeStore(self.database).save(
            EmployeeDraft("Synthetic concurrent", self.crew["id"], 2, False)
        )
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(DAY, DAY, "FullDay", "Available"), 0
        )
        WorkingCalendarStore(self.database).save(
            "Crew", self.crew["id"], DAY, DAY, "FullDay", "Working", 0
        )
        entered = threading.Event()
        done = threading.Event()
        failures = []

        def writer():
            try:
                if not entered.wait(5):
                    raise AssertionError("Reader did not pin")
                with closing(storage.connect(self.database)) as c, c:
                    c.execute("BEGIN IMMEDIATE")
                    c.execute(
                        "UPDATE DraftAssignments SET Status='Cancelled',Revision=Revision+1 WHERE Id=?",
                        (legacy.id,),
                    )
                    change = c.execute(
                        "INSERT INTO EmployeeAvailabilityChanges(EmployeeId,Revision,StartDate,EndDate,Slot,State,RecordedAt) VALUES(?,2,?,?,'FullDay','Unavailable','synthetic')",
                        (person.id, DAY, DAY),
                    ).lastrowid
                    c.execute(
                        "UPDATE EmployeeAvailability SET State='Unavailable',ChangeId=? WHERE EmployeeId=?",
                        (change, person.id),
                    )
            except BaseException as e:
                failures.append(e)
            finally:
                done.set()

        thread = threading.Thread(target=writer)
        thread.start()
        from rigarus_backend import day_compatibility as module

        original = module.legacy_day_observation

        def paused(kind, halves):
            if kind == "Calendar":
                entered.set()
                if not done.wait(5):
                    raise AssertionError("Writer did not finish")
            return original(kind, halves)

        with patch.object(module, "legacy_day_observation", side_effect=paused):
            old = compatibility_report(self.database, DAY, DAY)
        thread.join(5)
        self.assertFalse(failures)
        new = compatibility_report(self.database, DAY, DAY)
        self.assertTrue(old["visits"][0]["blocks_full_day"])
        self.assertFalse(new["visits"][0]["blocks_full_day"])
        self.assertEqual(
            next(
                e["daily_observation"]
                for e in old["evidence"]
                if e["kind"] == "Availability"
            ),
            "Available",
        )
        self.assertEqual(
            next(
                e["daily_observation"]
                for e in new["evidence"]
                if e["kind"] == "Availability"
            ),
            "Unavailable",
        )


class EvidencePreservationTests(unittest.TestCase):
    def setUp(self):
        import test_capability_store as capability

        capability.CapabilityStoreTests.setUp(self)

    calendar = snapshots.AdapterTests.calendar
    employee = snapshots.AdapterTests.employee
    visit = snapshots.AdapterTests.visit

    def test_all_legacy_evidence_history_survives_backup_and_day_upgrade(self):
        from rigarus_backend.capability_store import CapabilityEvidenceStore
        from rigarus_backend.capability_validation import CapabilityRequirements
        from rigarus_backend.driver_store import DriverApprovalStore
        from rigarus_backend.driver_eligibility import DriverApprovalDraft

        person = self.employee()
        visit = self.visit()
        StaffingStore(self.database).save(visit.id, [person.id], 1)
        proof = CapabilityEvidenceStore(self.database)
        for scope, subject, code, value in (
            (
                "WorkItem",
                self.work.id,
                "",
                CapabilityRequirements(1, (0, 1, 0), "Exact", (("SYN", 1),)),
            ),
            ("Employee", person.id, "SYN", "Verified"),
        ):
            proof.save(
                scope,
                subject,
                code,
                value,
                start_date="2026-11-23",
                end_date="2026-11-23",
                slot="AM",
                company_confirmed=True,
                reference="Synthetic evidence",
                expected_revision=0,
            )
        DriverApprovalStore(self.database).save(
            person.id,
            DriverApprovalDraft(
                "2026-11-23", "2026-11-23", "AM", "Suspended", True, "Synthetic driver"
            ),
            0,
        )
        with closing(storage.connect(self.database)) as c, c:
            remove_day_schema(c)
        with closing(storage.connect(self.database)) as c:
            original = {
                t: c.execute(f'SELECT * FROM "{t}"').fetchall()
                for (t,) in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table'"
                ).fetchall()
            }
        storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c:
            for t, rows in original.items():
                actual = c.execute(f'SELECT * FROM "{t}"').fetchall()
                self.assertEqual(
                    actual[: len(rows)] if t == "__EFMigrationsHistory" else actual,
                    rows,
                )
        report = compatibility_report(self.database, "2026-11-23", "2026-11-23")
        driver = next(e for e in report["evidence"] if e["kind"] == "Driver")
        self.assertEqual(driver["resource_validation"], "Blocked")
        self.assertFalse(driver["complete_legacy_coverage"])
        self.assertTrue(
            all(
                e["resource_validation"] == "Pending"
                for e in report["evidence"]
                if e["kind"] == "Capability"
            )
        )
