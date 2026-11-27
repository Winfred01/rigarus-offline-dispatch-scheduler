"""Synthetic daily input evidence, recovery and concurrency acceptance."""

import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_assignments as fixtures
import test_recommendation_adapter as recommendations
from migration_fixture import remove_daily_calendar_schema
from rigarus_backend import storage, recommendation_adapter as adapter
from rigarus_backend.api import create_app
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.daily_calendars import DailyInput, resolve_daily
from rigarus_backend.daily_calendar_store import (
    DailyCalendarStore,
    DailyConflict,
    DailyNotFound,
    DailySourceError,
    daily_assessment,
    snapshot,
)
from rigarus_backend.daily_calendar_migration import DAILY_TABLES
from rigarus_backend.draft_restore_migration import DRAFT_RESTORE
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.roster import EmployeeDraft
from rigarus_backend.roster_store import EmployeeStore
from rigarus_backend.working_calendar_store import WorkingCalendarStore

DAY = "2026-12-31"


class DailyTests(unittest.TestCase):
    setUp = fixtures.AssignmentTests.setUp

    def read(self, scope="Crew", entity=None, start=DAY, end=DAY):
        return DailyCalendarStore(self.database).read(
            scope, entity or self.crew["id"], start, end
        )

    def save(
        self,
        state="Working",
        scope="Crew",
        entity=None,
        start=DAY,
        end=DAY,
        reviewed=False,
        notes="Synthetic daily assertion",
        before=None,
    ):
        entity = entity or self.crew["id"]
        current = before or self.read(scope, entity, start, end)
        return DailyCalendarStore(self.database).save(
            scope,
            entity,
            DailyInput(start, end, state, True, reviewed, notes),
            current["revision"],
            current["review_token"],
        )

    def legacy(self, scope="Crew", entity=None, half="AM", state="Working", day=DAY):
        entity = entity or self.crew["id"]
        store = WorkingCalendarStore(self.database)
        revision = store.read(scope, entity, day, day)["revision"]
        return store.save(scope, entity, day, day, half, state, revision)

    def digest(self):
        with closing(storage.connect(self.database, read_only=True)) as c:
            return logical_digest(c)

    def employee(self):
        return (
            EmployeeStore(self.database)
            .save(EmployeeDraft("Synthetic daily worker", self.crew["id"], 2, False))
            .id
        )

    def test_new_unknown_does_not_default_weekdays_or_create_rows(self):
        before = self.digest()
        result = self.read(start=DAY, end="2027-01-02")
        self.assertEqual([e["state"] for e in result["entries"]], ["Unknown"] * 3)
        self.assertEqual(result["revision"], 0)
        self.assertFalse(result["applyable"] or result["publishable"])
        self.assertEqual(self.digest(), before)

    def test_daily_save_reopen_history_noop_and_unknown_tombstone(self):
        store = DailyCalendarStore(self.database)
        saved = self.save()
        self.assertEqual(saved["entries"][0]["state"], "Working")
        self.assertEqual(self.save(), saved)
        before = self.digest()
        self.assertEqual(
            DailyCalendarStore(self.database).read("Crew", self.crew["id"], DAY, DAY),
            saved,
        )
        self.assertEqual(self.digest(), before)
        cleared = self.save("Unknown")
        self.assertEqual(cleared["revision"], 2)
        self.assertEqual(cleared["entries"][0]["recorded_state"], "Unknown")
        self.assertIsNotNone(cleared["entries"][0]["change_id"])
        history = store.history("Crew", self.crew["id"])
        self.assertEqual([r["state"] for r in history], ["Unknown", "Working"])
        self.assertEqual(history[1]["notes"], "Synthetic daily assertion")
        self.assertEqual(history[1]["legacy_snapshot"]["entries"], [])

    def test_legacy_positive_pair_and_single_half_are_never_auto_promoted(self):
        self.legacy()
        entry = self.read()["entries"][0]
        self.assertEqual(entry["state"], "Unknown")
        self.assertTrue(entry["legacy"]["mixed_or_partial"])
        self.legacy(half="PM")
        entry = self.read()["entries"][0]
        self.assertEqual(entry["legacy"]["daily_observation"], "Working")
        self.assertEqual(entry["state"], "Unknown")
        self.assertEqual(entry["review_status"], "Needs Review")

    def test_mixed_legacy_negative_blocks_and_raw_values_are_preserved(self):
        self.legacy()
        self.legacy(half="PM", state="NotWorking")
        before = self.digest()
        entry = self.read()["entries"][0]
        self.assertEqual(entry["state"], "NotWorking")
        self.assertTrue(entry["known_blocked"])
        self.assertEqual(
            [r["state"] for r in entry["legacy"]["original_halves"]],
            ["Working", "NotWorking"],
        )
        self.assertEqual(self.digest(), before)

    def test_legacy_review_required_then_explicit_new_assertion_not_conversion(self):
        self.legacy(state="NotWorking")
        before = self.digest()
        with self.assertRaisesRegex(DailyConflict, "explicit review"):
            self.save()
        self.assertEqual(self.digest(), before)
        saved = self.save(reviewed=True)
        entry = saved["entries"][0]
        self.assertEqual(entry["state"], "Working")
        self.assertEqual(entry["legacy"]["original_halves"][0]["state"], "NotWorking")
        self.assertEqual(entry["legacy"]["compatibility_status"], "Needs Review")
        self.assertEqual(
            WorkingCalendarStore(self.database).read("Crew", self.crew["id"], DAY, DAY)[
                "entries"
            ][0]["state"],
            "NotWorking",
        )

    def test_old_edit_invalidates_daily_positive_and_rereview_restores_receipt(self):
        self.legacy()
        self.save(reviewed=True)
        self.legacy(half="PM", state="NotWorking")
        stale = self.read()
        self.assertEqual(stale["entries"][0]["review_status"], "Stale")
        self.assertEqual(stale["entries"][0]["state"], "NotWorking")
        result = self.save(reviewed=True)
        self.assertEqual(result["revision"], 2)
        self.assertEqual(result["entries"][0]["review_status"], "Current")
        history = DailyCalendarStore(self.database).history("Crew", self.crew["id"])
        self.assertEqual(len(history[0]["legacy_snapshot"]["entries"]), 2)
        self.assertEqual(len(history[1]["legacy_snapshot"]["entries"]), 1)

    def test_clear_legacy_positive_stays_unknown_after_legacy_change(self):
        self.legacy(half="FullDay")
        self.save("Unknown", reviewed=True)
        self.legacy(half="AM", state="Unknown")
        entry = self.read()["entries"][0]
        self.assertEqual(entry["state"], "Unknown")
        self.assertEqual(entry["recorded_state"], "Unknown")
        self.assertEqual(entry["review_status"], "Stale")

    def test_even_out_of_range_old_revision_conservatively_invalidates_receipt(self):
        self.save()
        self.legacy(day="2027-01-01")
        entry = self.read()["entries"][0]
        self.assertEqual((entry["state"], entry["review_status"]), ("Unknown", "Stale"))

    def test_daily_negative_remains_blocking_when_receipt_stale(self):
        self.save("NotWorking")
        self.legacy(half="FullDay")
        entry = self.read()["entries"][0]
        self.assertTrue(entry["known_blocked"])
        self.assertEqual(entry["review_status"], "Stale")

    def test_employee_partial_mixed_review_clear_and_no_home_crew_inference(self):
        person = self.employee()
        old = AvailabilityStore(self.database)
        old.save(person, AvailabilityDraft(DAY, DAY, "AM", "Available"), 0)
        entry = self.read("Employee", person)["entries"][0]
        self.assertEqual(
            (entry["state"], entry["state_label"]), ("Unknown", "Not recorded")
        )
        old.save(person, AvailabilityDraft(DAY, DAY, "PM", "Unavailable"), 1)
        self.assertEqual(
            self.read("Employee", person)["entries"][0]["state"], "Unavailable"
        )
        saved = self.save("Available", "Employee", person, reviewed=True)
        self.assertEqual(saved["entries"][0]["state"], "Available")
        self.assertEqual(self.read()["revision"], 0)
        self.save("Unknown", "Employee", person, reviewed=True)
        self.assertEqual(
            self.read("Employee", person)["entries"][0]["state_label"], "Not recorded"
        )
        old.save(person, AvailabilityDraft(DAY, DAY, "FullDay", "Unknown"), 2)
        self.assertEqual(
            self.read("Employee", person)["entries"][0]["review_status"], "Stale"
        )

    def test_workitems_share_parent_calendar_but_independent_ids_and_weekend_pending(
        self,
    ):
        self.save()
        self.save(scope="Project", entity=self.project["id"])
        store = DailyCalendarStore(self.database)
        for work in self.project["work_items"]:
            result = store.assess(work["id"], self.crew["id"], DAY)
            self.assertEqual(result["project_id"], self.project["id"])
            self.assertEqual(result["work_item_id"], work["id"])
            self.assertEqual(result["status"], "Matched")
            self.assertEqual(result["validation_status"], "Pending")
            self.assertFalse(result["applyable"] or result["publishable"])
        self.save(start="2027-01-02", end="2027-01-02")
        self.save(
            scope="Project",
            entity=self.project["id"],
            start="2027-01-02",
            end="2027-01-02",
        )
        weekend = store.assess(
            self.draft["work_item_id"], self.crew["id"], "2027-01-02"
        )
        self.assertEqual(
            (weekend["status"], weekend["weekend_consent"]), ("Matched", "Pending")
        )

    def test_project_or_crew_negative_blocks_calendar_assessment_only(self):
        self.save()
        self.save("NotWorking", "Project", self.project["id"])
        result = DailyCalendarStore(self.database).assess(
            self.draft["work_item_id"], self.crew["id"], DAY
        )
        self.assertEqual(result["status"], "Blocked")
        self.assertEqual(result["validation_status"], "Pending")
        self.assertEqual(self.read(entity=self.other_crew["id"])["revision"], 0)

    def test_review_token_scope_range_and_both_revision_changes_rejected(self):
        original = self.read()
        with self.assertRaises(DailyConflict):
            self.save(entity=self.other_crew["id"], before=original)
        with self.assertRaises(DailyConflict):
            self.save(start=DAY, end="2027-01-01", before=original)
        self.legacy()
        with self.assertRaises(DailyConflict):
            self.save(reviewed=True, before=original)
        original = self.read()
        self.save(reviewed=True)
        with self.assertRaises(DailyConflict):
            self.save("NotWorking", reviewed=True, before=original)

    def test_range_rollback_on_cell_failure_and_history_immutable(self):
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticDailyFailure BEFORE INSERT ON DailyCalendarCells WHEN NEW.LocalDate='2027-01-01' BEGIN SELECT RAISE(ABORT,'Synthetic cell failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            self.save(end="2027-01-01")
        self.assertEqual(self.digest(), before)
        self.save()
        for sql in (
            "UPDATE DailyCalendarChanges SET Notes='changed'",
            "DELETE FROM DailyCalendarChanges",
            "UPDATE DailyCalendarOwners SET CrewId=CrewId",
            "DELETE FROM DailyCalendarOwners",
        ):
            with closing(storage.connect(self.database)) as c, c:
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)

    def test_sql_scope_foreign_key_and_date_context_constraints(self):
        self.save()
        with closing(storage.connect(self.database)) as c, c:
            owner_id, change_id = c.execute(
                "SELECT OwnerId,ChangeId FROM DailyCalendarCells"
            ).fetchone()
            for values in (
                (owner_id, "2027-01-01", "Working", change_id, "a" * 64),
                (owner_id, "2026-02-30", "Working", change_id, "a" * 64),
                (owner_id, DAY, "Unavailable", change_id, "a" * 64),
                (999999, DAY, "Working", change_id, "a" * 64),
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(
                        "INSERT OR REPLACE INTO DailyCalendarCells VALUES(?,?,?,?,?)",
                        values,
                    )
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(
                    "INSERT INTO DailyCalendarChanges(OwnerId,Revision,StartDate,EndDate,State,OperatorConfirmed,LegacyReviewed,LegacyRevision,LegacySnapshot,Notes,RecordedAt) VALUES(?,2,?,?,'Available',1,0,0,'{}','','synthetic')",
                    (owner_id, DAY, DAY),
                )
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_invalid_legacy_context_fails_closed_without_write(self):
        self.legacy()
        # Synthetic corruption: native legacy cells do not have composite history FKs.
        with closing(storage.connect(self.database)) as c, c:
            c.execute("UPDATE WorkingCalendarCells SET State='NotWorking'")
        before = self.digest()
        with self.assertRaises(DailySourceError):
            self.read()
        self.assertEqual(self.digest(), before)
        response = self.client.get(
            f"/daily-calendars/Crew/{self.crew['id']}?start_date={DAY}&end_date={DAY}"
        )
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("SELECT", response.json()["detail"])

    def test_concurrent_writers_exactly_one_wins(self):
        before = self.read()
        barrier = threading.Barrier(2)

        def write(state):
            barrier.wait(timeout=5)
            try:
                return self.save(state, before=before)["revision"]
            except DailyConflict:
                return "Conflict"

        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(write, ("Working", "NotWorking")))
        self.assertCountEqual(results, [1, "Conflict"])
        self.assertEqual(
            len(DailyCalendarStore(self.database).history("Crew", self.crew["id"])), 1
        )

    def test_pinned_daily_read_never_mixes_concurrent_daily_or_legacy_changes(self):
        self.legacy(half="FullDay")
        original = self.save(reviewed=True)
        with closing(storage.connect(self.database)) as c:
            c.execute("PRAGMA journal_mode=WAL")
        with closing(storage.connect(self.database, read_only=True)) as reader, reader:
            reader.execute("BEGIN")
            pinned = snapshot(reader, "Crew", self.crew["id"], DAY, DAY)
            with ThreadPoolExecutor(1) as pool:
                pool.submit(self.save, "NotWorking", reviewed=True).result(timeout=5)
                pool.submit(self.legacy, half="PM", state="NotWorking").result(
                    timeout=5
                )
            self.assertEqual(
                snapshot(reader, "Crew", self.crew["id"], DAY, DAY), pinned
            )
        self.assertEqual(pinned, original)
        self.assertEqual(
            (self.read()["revision"], self.read()["entries"][0]["review_status"]),
            (2, "Stale"),
        )

    def test_pinned_inherited_assessment_uses_same_connection(self):
        self.save()
        self.save(scope="Project", entity=self.project["id"])
        with closing(storage.connect(self.database)) as c:
            c.execute("PRAGMA journal_mode=WAL")
        with closing(storage.connect(self.database, read_only=True)) as c, c:
            c.execute("BEGIN")
            first = daily_assessment(
                c, self.draft["work_item_id"], self.crew["id"], DAY
            )
            with ThreadPoolExecutor(1) as pool:
                pool.submit(
                    self.save, "NotWorking", "Project", self.project["id"]
                ).result(timeout=5)
            self.assertEqual(
                daily_assessment(c, self.draft["work_item_id"], self.crew["id"], DAY),
                first,
            )
        self.assertEqual(
            DailyCalendarStore(self.database).assess(
                self.draft["work_item_id"], self.crew["id"], DAY
            )["status"],
            "Blocked",
        )

    def test_api_default_gate_optin_strict_contract_and_errors(self):
        route = f"/daily-calendars/Crew/{self.crew['id']}"
        query = f"?start_date={DAY}&end_date={DAY}"
        read = self.client.get(route + query).json()
        body = dict(
            start_date=DAY,
            end_date=DAY,
            state="Working",
            confirmed_by_operator=True,
            expected_revision=0,
            expected_review_token=read["review_token"],
        )
        before = self.digest()
        self.assertEqual(self.client.put(route, json=body).status_code, 409)
        self.assertEqual(self.digest(), before)
        with TestClient(
            create_app(self.database, enable_daily_calendar_writes=True)
        ) as client:
            for changes in (
                dict(slot="AM"),
                dict(confirmed_by_operator=1),
                dict(confirmed_by_operator=False),
                dict(expected_revision=True),
                dict(expected_review_token="x" * 64),
                dict(state="Available"),
                dict(start_date="2026-02-30"),
            ):
                self.assertEqual(
                    client.put(route, json=body | changes).status_code, 422, changes
                )
            self.assertEqual(client.put(route, json=body).status_code, 200)
            self.assertEqual(client.put(route, json=body).status_code, 409)
            self.assertEqual(client.get(route + "/history").status_code, 200)
            self.assertEqual(
                client.get(
                    "/daily-calendars/assessment",
                    params=dict(
                        work_item_id=self.draft["work_item_id"],
                        crew_id=self.crew["id"],
                        local_date=DAY,
                    ),
                ).status_code,
                200,
            )
            # Separate day-Draft production gate stays closed even in daily-input test opt-in.
            self.assertEqual(
                client.post(
                    "/day-draft-assignments",
                    json=dict(
                        work_item_id=self.draft["work_item_id"],
                        crew_id=self.crew["id"],
                        local_date=DAY,
                    ),
                ).status_code,
                409,
            )
        self.assertEqual(
            self.client.get("/daily-calendars/WorkItem/1" + query).status_code, 422
        )
        self.assertEqual(
            self.client.get("/daily-calendars/Crew/999999" + query).status_code, 404
        )

    def test_pure_contract_local_dates_leap_dst_year_end_and_no_io(self):
        for first, last, length in (
            ("2026-12-31", "2027-01-01", 2),
            ("2028-02-28", "2028-03-01", 3),
            ("2027-03-13", "2027-03-15", 3),
            ("2027-11-06", "2027-11-08", 3),
            ("2028-01-01", "2028-12-31", 366),
        ):
            result = self.save(start=first, end=last)
            self.assertEqual(len(result["entries"]), length)
        with (
            patch("builtins.open", side_effect=AssertionError("No file I/O")),
            patch("socket.socket", side_effect=AssertionError("No network")),
            patch("sqlite3.connect", side_effect=AssertionError("No SQL")),
        ):
            draft = DailyInput(DAY, DAY, "Working", True)
            self.assertEqual(resolve_daily("Crew", draft.state, ())["state"], "Working")
            with self.assertRaises(FrozenInstanceError):
                draft.state = "Unknown"

    def test_invalid_inputs_and_scope_ids(self):
        for first, last in (
            ("2026-02-30", DAY),
            ("2026-1-01", DAY),
            ("2026-12-31T00:00:00Z", DAY),
            ("2027-01-01", DAY),
            ("2027-01-01", "2028-01-02"),
        ):
            with self.assertRaises(ValueError):
                DailyInput(first, last, "Working", True)
        for changes in (
            dict(state="AM"),
            dict(confirmed_by_operator=False),
            dict(confirmed_by_operator=1),
            dict(legacy_reviewed=1),
            dict(notes="x" * 2001),
            dict(notes="x\0y"),
        ):
            with self.assertRaises(ValueError):
                replace(DailyInput(DAY, DAY, "Working", True), **changes)
        for entity in (0, -1, True, 1.5, "1", 2**53):
            with self.assertRaises(ValueError):
                self.read(entity=entity if entity else -1)
        with self.assertRaises(DailyNotFound):
            DailyCalendarStore(self.database).assess(999999, self.crew["id"], DAY)


class DailyMigrationTests(unittest.TestCase):
    setUp = DailyTests.setUp
    digest = DailyTests.digest
    legacy = DailyTests.legacy
    read = DailyTests.read
    save = DailyTests.save

    def schema13(self):
        self.client.post("/draft-assignments", json=self.draft)
        self.client.post(
            "/draft-assignments",
            json=self.draft
            | dict(slot="PM", work_item_id=self.project["work_items"][1]["id"]),
        )
        DayDraftStore(self.database).save(
            DayDraft(
                self.draft["work_item_id"],
                self.crew["id"],
                "2027-01-01",
                "Synthetic retained daily notes",
            )
        )
        self.legacy()
        self.legacy(half="PM", state="NotWorking")
        person = EmployeeStore(self.database).save(
            EmployeeDraft("Synthetic retained employee", self.crew["id"], 2, False)
        )
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(DAY, DAY, "AM", "Available"), 0
        )
        with closing(storage.connect(self.database)) as c, c:
            remove_daily_calendar_schema(c)

    def test_upgrade13_backup_preserves_all_rows_ids_history_sequences_and_rerun(self):
        self.schema13()
        expected = self.digest()
        with closing(storage.connect(self.database)) as c:
            original = {
                t: c.execute('SELECT * FROM "' + t + '"').fetchall()
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
                (13,),
            )
        with closing(storage.connect(self.database)) as c:
            for t, values in original.items():
                current = c.execute('SELECT * FROM "' + t + '"').fetchall()
                self.assertEqual(
                    current[: len(values)] if t == "__EFMigrationsHistory" else current,
                    values,
                    t,
                )
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            for t in DAILY_TABLES:
                self.assertEqual(
                    c.execute('SELECT count(*) FROM "' + t + '"').fetchone(), (0,)
                )
        before = self.digest()
        storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        self.assertEqual(len(list(self.database.parent.glob("*.before-day-*.bak"))), 1)
        self.assertEqual(self.read()["entries"][0]["state"], "NotWorking")

    def test_ddl_failure_atomic_rollback_backup_failure_then_safe_retry(self):
        self.schema13()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticDailyMigrationFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDailyCalendars' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticDailyMigrationFailure")
        before = self.digest()
        with patch.object(
            storage,
            "verified_upgrade_backup",
            side_effect=OSError("Synthetic backup failure"),
        ):
            with self.assertRaises(OSError):
                storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        storage.initialize_database(self.database)
        self.assertEqual(self.read()["revision"], 0)
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute(
                    "SELECT MigrationId FROM __EFMigrationsHistory ORDER BY MigrationId DESC LIMIT 1"
                ).fetchone(),
                (DRAFT_RESTORE,),
            )

    def test_partial_or_future_schema_rejected_without_modification(self):
        with closing(storage.connect(self.database)) as c, c:
            c.execute("CREATE TABLE SyntheticUnexpected(Id INTEGER)")
        before = self.digest()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)


class DailyRecommendationGuardTests(unittest.TestCase):
    setUp = recommendations.AdapterTests.setUp
    calendar = recommendations.AdapterTests.calendar
    recommendation = recommendations.AdapterTests.snapshot

    def write_daily(self, state="Unknown", day="2026-11-23"):
        store = DailyCalendarStore(self.database)
        before = store.read("Crew", self.c1.id, day, day)
        return store.save(
            "Crew",
            self.c1.id,
            DailyInput(day, day, state, True, True),
            before["revision"],
            before["review_token"],
        )

    def test_daily_unknown_refuses_legacy_generator_and_old_snapshot_becomes_stale(
        self,
    ):
        original = self.recommendation()
        self.write_daily()
        with self.assertRaisesRegex(
            adapter.SnapshotContextError, "DAILY_CALENDAR_ADAPTER_REQUIRED"
        ):
            self.recommendation()
        result = adapter.check_snapshot_freshness(self.database, original)
        self.assertEqual(
            (result.status, result.reason), ("Stale", "DAILY_CALENDAR_ADAPTER_REQUIRED")
        )

    def test_outside_horizon_does_not_enter_or_mutate_legacy_snapshot(self):
        original = self.recommendation()
        self.write_daily(day="2027-01-01")
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, original).status, "Current"
        )

    def test_legacy_snapshot_pinned_before_daily_commit_stays_complete_then_stale(self):
        original = self.recommendation()
        read = adapter._read_sources

        def concurrent_write(*args):
            with ThreadPoolExecutor(1) as pool:
                pool.submit(self.write_daily).result(timeout=5)
            return read(*args)

        with patch.object(adapter, "_read_sources", side_effect=concurrent_write):
            pinned = self.recommendation()
        self.assertEqual(pinned.input_fingerprint, original.input_fingerprint)
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, pinned).reason,
            "DAILY_CALENDAR_ADAPTER_REQUIRED",
        )
