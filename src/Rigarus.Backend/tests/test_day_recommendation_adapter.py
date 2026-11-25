"""Synthetic schema14 coherent snapshots, whole-date occupancy and freshness."""

import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace, FrozenInstanceError, asdict
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_recommendation_adapter as fixtures
from migration_fixture import remove_daily_calendar_schema
from rigarus_backend import storage
from rigarus_backend.api import create_app
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.daily_calendars import DailyInput
from rigarus_backend.daily_calendar_store import DailyCalendarStore
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.day_drafts import ConfirmedRemainingDays, DayDraft
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.driver_store import DriverApprovalStore
from rigarus_backend.driver_eligibility import DriverApprovalDraft
from rigarus_backend.recommendation_adapter import (
    SnapshotReadError,
    SnapshotNotFound,
    SnapshotContextError,
)
from rigarus_backend import day_recommendation_adapter as adapter
from rigarus_backend.day_recommendation_adapter import (
    DayRecommendationQuery,
    build_day_recommendation_snapshot,
    check_day_snapshot_freshness,
    generate_from_day_snapshot,
    day_generation_requests,
)
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.capability_store import CapabilityEvidenceStore
from rigarus_backend.capability_validation import CapabilityRequirements

MON = "2026-11-23"
FRI = "2026-11-27"


class DayAdapterTests(unittest.TestCase):
    calendar = fixtures.AdapterTests.calendar
    visit = fixtures.AdapterTests.visit
    employee = fixtures.AdapterTests.employee

    def setUp(self):
        fixtures.AdapterTests.setUp(self)
        self.query = DayRecommendationQuery(
            self.work.id,
            (self.c2.id, self.c1.id),
            ConfirmedRemainingDays(2, True),
            MON,
            FRI,
            self.project.id,
        )
        self.daily("Project", self.project.id, MON, FRI)
        self.daily("Crew", self.c1.id, MON, FRI, "NotWorking")
        self.daily("Crew", self.c1.id, MON, MON)
        self.daily("Crew", self.c1.id, FRI, FRI)
        self.daily("Crew", self.c2.id, MON, FRI)
        self.daily("Crew", self.c2.id, MON, MON, "NotWorking")

    def daily(self, scope, identity, start=MON, end=FRI, state="Working"):
        store = DailyCalendarStore(self.database)
        before = store.read(scope, identity, start, end)
        return store.save(
            scope,
            identity,
            DailyInput(start, end, state, True, True, "Synthetic daily input"),
            before["revision"],
            before["review_token"],
        )

    def snapshot(self, **changes):
        return build_day_recommendation_snapshot(
            self.database, replace(self.query, **changes)
        )

    def digest(self):
        with closing(storage.connect(self.database, read_only=True)) as c:
            return logical_digest(c)

    def day(self, crew=None, day=MON, workers=None):
        return DayDraftStore(self.database).save(
            DayDraft(
                self.work.id, crew or self.c1.id, day, "Synthetic day visit", workers
            )
        )

    def assert_stale(self, before):
        result = check_day_snapshot_freshness(self.database, before)
        self.assertEqual((result.status, result.reason), ("Stale", "INPUTS_CHANGED"))

    def test_real_daily_data_generates_dates_and_two_orders(self):
        snapshot = self.snapshot()
        result = generate_from_day_snapshot(snapshot)
        self.assertEqual(
            [o.option.crew_id for o in result.generated.comparison.options],
            [self.c2.id, self.c1.id],
        )
        self.assertEqual(result.generated.comparison.options[0].finish, "2026-11-25")
        start = generate_from_day_snapshot(self.snapshot(order="EarliestStart"))
        self.assertEqual(
            [o.option.crew_id for o in start.generated.comparison.options],
            [self.c1.id, self.c2.id],
        )
        self.assertEqual(snapshot.work_item.project_id, self.project.id)
        self.assertEqual(snapshot.work_item.estimated_half_days, 99)
        for request in day_generation_requests(snapshot):
            self.assertEqual(request.remaining, ConfirmedRemainingDays(2, True))
            self.assertEqual(request.project_calendar.entity_id, self.project.id)
        self.assertEqual(result.validation_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)
        self.assertIn("ApprovedDriver", result.pending_validators)

    def test_four_days_accumulate_across_tuesday_closure(self):
        self.daily("Crew", self.c1.id, "2026-11-25", "2026-11-26")
        result = generate_from_day_snapshot(
            self.snapshot(
                crew_ids=(self.c1.id,), remaining=ConfirmedRemainingDays(4, True)
            )
        ).generated.candidates[0]
        self.assertEqual(
            result.allocated_working_dates, (MON, "2026-11-25", "2026-11-26", FRI)
        )
        self.assertEqual(
            (
                result.proposed_finish_date,
                result.accumulated_days,
                result.unfilled_days,
            ),
            (FRI, 4, 0),
        )
        self.assertEqual(result.skipped[0].local_date, "2026-11-24")

    def test_daily_draft_occupies_full_date_cancellation_releases_and_same_work_never_deducts(
        self,
    ):
        row = self.day()
        snap = self.snapshot(crew_ids=(self.c1.id,))
        self.assertEqual(snap.day_assignments[0].assignment_id, row["id"])
        request = day_generation_requests(snap)[0]
        self.assertEqual(request.remaining.days, 2)
        self.assertEqual(request.occupancy.occupied_dates, (MON,))
        result = generate_from_day_snapshot(snap).generated.candidates[0]
        self.assertEqual(
            (
                result.accumulated_days,
                result.unfilled_days,
                result.proposed_finish_date,
            ),
            (1, 1, None),
        )
        DayDraftStore(self.database).cancel(row["id"], row["revision"])
        self.assert_stale(snap)
        new = self.snapshot()
        self.assertEqual(new.day_assignments[0].status, "Cancelled")
        self.assertEqual(day_generation_requests(new)[0].occupancy.occupied_dates, ())

    def test_any_old_half_blocks_whole_date_namespaced_ids_do_not_collide(self):
        old = self.visit(day=MON, half="PM")
        new = self.day(crew=self.c2.id, day="2026-11-24")
        self.assertEqual(old.id, new["id"])
        snap = self.snapshot()
        self.assertEqual(snap.legacy_assignments[0].slot, "PM")
        self.assertEqual(snap.day_assignments[0].crew_id, self.c2.id)
        requests = {r.crew_id: r for r in day_generation_requests(snap)}
        self.assertEqual(requests[self.c1.id].occupancy.occupied_dates, (MON,))
        self.assertEqual(requests[self.c2.id].occupancy.occupied_dates, ("2026-11-24",))
        from rigarus_backend.assignment_store import AssignmentStore

        AssignmentStore(self.database).cancel(old.id, old.revision)
        self.assert_stale(snap)

    def test_actual_other_crew_staffing_borrowing_daily_and_old_evidence_same_view(
        self,
    ):
        person = self.employee(home=self.c2.id)
        day = self.day(crew=self.tower.id, workers=(person.id,))
        old = self.visit(crew=self.c2.id, day="2026-11-25")
        StaffingStore(self.database).save(old.id, (person.id,), old.revision)
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(MON, FRI, "AM", "Available"), 0
        )
        self.daily("Employee", person.id, state="Available")
        snap = self.snapshot()
        self.assertEqual(snap.day_assignments[0].assignment_id, day["id"])
        self.assertEqual(snap.day_assignments[0].actual_employee_ids, (person.id,))
        self.assertEqual(snap.legacy_assignments[0].actual_employee_ids, (person.id,))
        raw = json.loads(
            next(s.payload_json for s in snap.daily_inputs if s.scope == "Employee")
        )
        self.assertEqual(raw["entries"][0]["state"], "Available")
        self.assertEqual(raw["legacy_source"]["entries"][0]["slot"], "AM")
        employee = snap.employees[0]
        self.assertEqual(employee.metadata[2], self.c2.id)
        self.assertEqual(json.loads(employee.legacy_driver_json)["entries"], [])
        result = generate_from_day_snapshot(snap)
        self.assertIn("PersonnelConflicts", result.pending_validators)
        self.assertIn("WeekendConsent", result.pending_validators)
        self.assertFalse(result.applyable or result.publishable)

    def test_old_mixed_and_positive_pair_never_automatically_become_daily_capacity(
        self,
    ):
        # Existing unselected Tower calendar has no daily assertion.
        self.calendar("Crew", self.tower.id, MON, FRI)
        self.calendar("Project", self.project.id, MON, MON, state="NotWorking")
        snap = self.snapshot(crew_ids=(self.tower.id,))
        source = json.loads(
            next(s.payload_json for s in snap.daily_inputs if s.scope == "Crew")
        )
        self.assertEqual(source["entries"][0]["state"], "Unknown")
        self.assertEqual(source["entries"][0]["legacy"]["daily_observation"], "Working")
        # Wrong type is a review, never an eligible confirmed option.
        self.assertEqual(
            generate_from_day_snapshot(snap).generated.comparison.options, ()
        )

    def test_old_calendar_change_invalidates_receipt_and_snapshot(self):
        before = self.snapshot()
        self.calendar("Crew", self.c1.id, MON, MON, half="PM", state="NotWorking")
        self.assert_stale(before)
        snap = self.snapshot(crew_ids=(self.c1.id,))
        inputs = json.loads(
            next(s.payload_json for s in snap.daily_inputs if s.scope == "Crew")
        )
        self.assertEqual(inputs["entries"][0]["review_status"], "Stale")
        result = generate_from_day_snapshot(snap).generated.candidates[0]
        self.assertIsNone(result.proposed_finish_date)
        self.assertIn("CREW_CALENDAR_STALE", result.skipped[0].reasons)

    def test_daily_calendar_and_unknown_tombstone_make_snapshot_stale(self):
        before = self.snapshot()
        self.daily("Crew", self.c1.id, MON, MON, "Unknown")
        self.assert_stale(before)
        snap = self.snapshot()
        source = json.loads(
            next(
                s.payload_json
                for s in snap.daily_inputs
                if s.scope == "Crew" and s.entity_id == self.c1.id
            )
        )
        self.assertEqual(source["entries"][0]["recorded_state"], "Unknown")
        self.assertEqual(
            generate_from_day_snapshot(snap).generated.candidates[0].unfilled_days, 1
        )

    def test_related_daily_and_legacy_availability_changes_both_stale(self):
        person = self.employee()
        before = self.snapshot()
        self.daily("Employee", person.id, state="Available")
        self.assert_stale(before)
        before = self.snapshot()
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(MON, MON, "AM", "Unavailable"), 0
        )
        self.assert_stale(before)
        snap = self.snapshot()
        raw = json.loads(
            next(s.payload_json for s in snap.daily_inputs if s.scope == "Employee")
        )
        self.assertEqual(
            (raw["entries"][0]["state"], raw["entries"][0]["review_status"]),
            ("Unavailable", "Stale"),
        )

    def test_new_old_day_and_other_crew_membership_changes_stale(self):
        before = self.snapshot()
        day = self.day(crew=self.tower.id)
        self.assert_stale(before)
        person = self.employee()
        before = self.snapshot()
        DayDraftStore(self.database).save(
            DayDraft(
                self.work.id, self.tower.id, MON, "Synthetic day visit", (person.id,)
            ),
            day["id"],
            1,
        )
        self.assert_stale(before)
        before = self.snapshot()
        old = self.visit(crew=self.c2.id, day="2026-11-25")
        self.assert_stale(before)
        before = self.snapshot()
        StaffingStore(self.database).save(old.id, (person.id,), old.revision)
        self.assert_stale(before)

    def test_unversioned_metadata_and_related_legacy_driver_and_policy_stale(self):
        person = self.employee()
        before = self.snapshot()
        with closing(storage.connect(self.database)) as c, c:
            c.execute("UPDATE Employees SET SkillLevel=3 WHERE Id=?", (person.id,))
        self.assert_stale(before)

        before = self.snapshot()
        CapabilityEvidenceStore(self.database).save(
            "WorkItem",
            self.work.id,
            "",
            CapabilityRequirements(1, (0, 1, 0), "Exact", ()),
            start_date=MON,
            end_date=FRI,
            slot="AM",
            company_confirmed=True,
            reference="Synthetic policy",
            expected_revision=0,
        )
        self.assert_stale(before)
        # Driver API is internal; use its actual confirmation contract.
        store = DriverApprovalStore(self.database)
        before = self.snapshot()
        store.save(
            person.id,
            DriverApprovalDraft(
                MON, FRI, "AM", "Suspended", True, "Synthetic company evidence"
            ),
            0,
        )
        self.assert_stale(before)

    def test_missing_duration_multicrew_wrong_type_inactive_and_parent_context(self):
        result = generate_from_day_snapshot(self.snapshot(remaining=None))
        self.assertTrue(
            all(
                "CONFIRMED_REMAINING_DAYS_MISSING" in c.review_reasons
                for c in result.generated.candidates
            )
        )
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "UPDATE WorkItems SET RequiredCrewCount=2 WHERE Id=?", (self.work.id,)
            )
        result = generate_from_day_snapshot(self.snapshot())
        self.assertTrue(
            all(
                "MULTI_CREW_REQUIRES_REVIEW" in c.review_reasons
                for c in result.generated.candidates
            )
        )
        result = generate_from_day_snapshot(
            self.snapshot(crew_ids=(self.inactive.id, self.tower.id))
        )
        self.assertEqual(result.generated.comparison.options, ())
        self.assertEqual(len(result.crew_reviews), 2)
        with self.assertRaises(SnapshotContextError):
            self.snapshot(expected_project_id=999999)
        with self.assertRaises(SnapshotNotFound):
            self.snapshot(work_item_id=999999)

    def test_civil_tower_workitems_keep_ids_and_share_actual_parent(self):
        first = self.snapshot()
        second = self.snapshot(
            work_item_id=self.project.work_items[1].id, crew_ids=(self.tower.id,)
        )
        self.assertNotEqual(first.work_item.work_item_id, second.work_item.work_item_id)
        self.assertEqual(first.work_item.project_id, second.work_item.project_id)
        self.assertEqual(
            next(s for s in first.daily_inputs if s.scope == "Project"),
            next(s for s in second.daily_inputs if s.scope == "Project"),
        )

    def test_snapshot_determinism_deep_immutability_and_zero_logical_writes(self):
        person = self.employee()
        self.day(workers=(person.id,))
        before = self.digest()
        first = self.snapshot()
        self.assertEqual(
            first, self.snapshot(crew_ids=tuple(reversed(self.query.crew_ids)))
        )
        self.assertEqual(len(first.input_fingerprint), 64)
        self.assertEqual(
            check_day_snapshot_freshness(self.database, first).status, "Current"
        )
        generate_from_day_snapshot(first)
        self.assertEqual(self.digest(), before)
        with self.assertRaises(FrozenInstanceError):
            first.query = self.query
        raw = json.loads(first.daily_inputs[0].payload_json)
        raw["entries"][0]["state"] = "Unknown"
        self.assertNotEqual(raw, json.loads(first.daily_inputs[0].payload_json))
        self.assertEqual(asdict(first), asdict(self.snapshot()))

    def test_pinned_read_returns_complete_old_view_then_stale_after_concurrent_multisource_write(
        self,
    ):
        before = self.snapshot()
        read = adapter._read_day_sources

        def commit_after_pin(*args):
            def mutate():
                self.daily("Crew", self.c1.id, MON, MON, "NotWorking")
                self.day(crew=self.c2.id, day="2026-11-24")

            with ThreadPoolExecutor(1) as pool:
                pool.submit(mutate).result(timeout=10)
            return read(*args)

        with patch.object(adapter, "_read_day_sources", side_effect=commit_after_pin):
            pinned = self.snapshot()
        self.assertEqual(pinned, before)
        self.assert_stale(pinned)
        self.assertEqual(len(self.snapshot().day_assignments), 1)

    def test_concurrent_repeated_atomic_sources_never_mix(self):
        ready = threading.Event()
        stop = threading.Event()
        errors = []

        def writer():
            with closing(storage.connect(self.database)) as c:
                ready.set()
                for n in range(15):
                    with c:
                        c.execute("BEGIN IMMEDIATE")
                        c.execute(
                            "UPDATE Crews SET Name=? WHERE Id=?",
                            (f"Synthetic atomic {n}", self.c1.id),
                        )
                        c.execute(
                            "UPDATE Projects SET JobNumber=? WHERE Id=?",
                            (f"SYN-ATOMIC-{n}", self.project.id),
                        )
            stop.set()

        with ThreadPoolExecutor(1) as pool:
            task = pool.submit(writer)
            ready.wait(5)
            for _ in range(15):
                snap = self.snapshot()
                name = next(c.name for c in snap.crews if c.crew_id == self.c1.id)
                if name.startswith("Synthetic atomic "):
                    if (
                        name.rsplit(" ", 1)[-1]
                        != snap.work_item.job_number.rsplit("-", 1)[-1]
                    ):
                        errors.append(snap.input_fingerprint)
            task.result(timeout=10)
        self.assertEqual(errors, [])

    def test_unrelated_scope_checkpoint_and_read_reopen_do_not_stale(self):
        before = self.snapshot()
        self.daily("Crew", self.tower.id, start="2027-01-01", end="2027-01-01")
        with closing(storage.connect(self.database)) as c:
            c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.assertEqual(
            check_day_snapshot_freshness(self.database, before).status, "Current"
        )
        # Observed owner's native legacy revision deliberately conservatively affects receipts.
        self.calendar("Crew", self.c1.id, "2027-01-01", "2027-01-01")
        self.assert_stale(before)

    def test_readonly_connection_query_only_and_release_on_all_outcomes(self):
        original = storage.connect
        observed = []

        def guarded(*args, **kwargs):
            self.assertTrue(kwargs.get("read_only"))
            c = original(*args, **kwargs)
            observed.append(c)
            with self.assertRaises(sqlite3.OperationalError):
                c.execute("UPDATE Crews SET Name=Name")
            c.rollback()  # Failed DML still starts an implicit transaction.
            return c

        with patch.object(adapter.storage, "connect", side_effect=guarded):
            self.snapshot()
        for c in observed:
            with self.assertRaises(sqlite3.ProgrammingError):
                c.execute("SELECT1")
        with patch.object(adapter, "MAX_READ_UNITS", 20):
            with self.assertRaises(SnapshotReadError) as error:
                self.snapshot()
        self.assertEqual(error.exception.code, "READ_LIMIT_EXCEEDED")
        with closing(original(self.database)) as c, c:
            c.execute("BEGIN IMMEDIATE")

    def test_deadline_projection_quota_and_source_failures_never_return_current(self):
        before = self.snapshot()
        with patch.object(adapter, "READ_SECONDS", -1):
            with self.assertRaises(SnapshotReadError) as caught:
                self.snapshot()
        self.assertEqual(caught.exception.code, "READ_DEADLINE_EXCEEDED")
        with patch.object(adapter, "MAX_READ_UNITS", 200):
            with self.assertRaises(SnapshotReadError):
                self.snapshot(horizon_end_date="2027-11-22")
        with patch.object(
            adapter.storage,
            "connect",
            side_effect=sqlite3.OperationalError("Synthetic private SQL text"),
        ):
            with self.assertRaises(SnapshotReadError) as caught:
                check_day_snapshot_freshness(self.database, before)
        self.assertNotIn("private", str(caught.exception))

    def test_old_future_missing_corrupt_sources_refused_without_initialization(self):
        with closing(storage.connect(self.database)) as c, c:
            remove_daily_calendar_schema(c)
        before = self.digest()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        self.assertEqual(self.digest(), before)
        missing = self.database.parent / "synthetic-missing.db"
        with self.assertRaises(SnapshotReadError):
            build_day_recommendation_snapshot(missing, self.query)
        self.assertFalse(missing.exists())
        corrupt = self.database.parent / "synthetic-corrupt.db"
        corrupt.write_bytes(b"Synthetic non-SQLite only")
        with self.assertRaises(SnapshotReadError):
            build_day_recommendation_snapshot(corrupt, self.query)

    def test_inconsistent_day_history_and_legacy_calendar_fail_closed(self):
        row = self.day()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "UPDATE DayDraftAssignments SET Notes='Synthetic mismatch' WHERE Id=?",
                (row["id"],),
            )
        before = self.digest()
        with self.assertRaises(SnapshotReadError) as caught:
            self.snapshot()
        self.assertEqual(caught.exception.code, "DATABASE_INVALID")
        self.assertEqual(self.digest(), before)

    def test_query_confirmation_sort_and_context_validation(self):
        for changes in (
            dict(remaining=2),
            dict(remaining=0.5),
            dict(crew_ids=(self.c1.id, self.c1.id)),
            dict(work_item_id=True),
            dict(order="Unknown"),
            dict(max_options=True),
            dict(horizon_end_date="2027-11-23"),
        ):
            with self.assertRaises(ValueError):
                replace(self.query, **changes)
        self.assertNotIn("half_days", str(asdict(self.query)))
        with self.assertRaises(ValueError):
            build_day_recommendation_snapshot(
                self.database, fixtures.AdapterTests.snapshot
            )

    def test_production_daily_gates_remain_closed_and_no_recommendation_http_route(
        self,
    ):
        before = self.digest()
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(
                client.post(
                    "/day-draft-assignments",
                    json=dict(
                        work_item_id=self.work.id, crew_id=self.c1.id, local_date=MON
                    ),
                ).status_code,
                409,
            )
            self.assertEqual(client.get("/day-recommendations").status_code, 404)
        self.assertEqual(self.digest(), before)

    def test_invalid_legacy_context_is_not_an_unknown_or_valid_fingerprint(self):
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "UPDATE WorkingCalendarCells SET State='NotWorking' WHERE LocalDate=? AND Slot='AM'",
                (MON,),
            )
        before = self.digest()
        with self.assertRaises(SnapshotReadError) as caught:
            self.snapshot()
        self.assertEqual(caught.exception.code, "DATABASE_INVALID")
        self.assertEqual(self.digest(), before)

    def test_unencodable_stored_metadata_fails_without_partial_fingerprint(self):
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "UPDATE Crews SET Name=? WHERE Id=?",
                (sqlite3.Binary(b"Synthetic invalid text storage"), self.c1.id),
            )
        before = self.digest()
        with self.assertRaises(SnapshotReadError) as caught:
            self.snapshot()
        self.assertEqual(caught.exception.code, "DATABASE_INVALID")
        self.assertEqual(self.digest(), before)

    def test_missing_or_moved_target_is_stale_and_future_schema_is_error(self):
        before = self.snapshot()
        with patch.object(
            adapter,
            "build_day_recommendation_snapshot",
            side_effect=SnapshotNotFound("Synthetic missing"),
        ):
            result = check_day_snapshot_freshness(self.database, before)
        self.assertEqual(
            (result.status, result.reason), ("Stale", "SOURCE_RECORD_MISSING_OR_MOVED")
        )
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "INSERT INTO __EFMigrationsHistory VALUES('29990101000000_SyntheticFuture','synthetic')"
            )
        unchanged = self.digest()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            check_day_snapshot_freshness(self.database, before)
        self.assertEqual(self.digest(), unchanged)

    def test_known_weekend_calendar_matches_do_not_supply_employee_consent(self):
        self.daily("Project", self.project.id, "2026-11-28", "2026-11-29")
        self.daily("Crew", self.c1.id, "2026-11-28", "2026-11-29")
        result = generate_from_day_snapshot(
            self.snapshot(
                crew_ids=(self.c1.id,),
                earliest_start_date="2026-11-28",
                horizon_end_date="2026-11-29",
                remaining=ConfirmedRemainingDays(1, True),
            )
        )
        self.assertEqual(result.generated.candidates[0].accumulated_days, 0)
        self.assertIn(
            "WEEKEND_CONSENT_NOT_CONFIRMED",
            result.generated.candidates[0].skipped[0].reasons,
        )
