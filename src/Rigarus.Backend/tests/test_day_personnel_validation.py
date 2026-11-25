"""Synthetic saved/candidate daily checks, source capture and scoped expiry."""

import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace, asdict, FrozenInstanceError
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_day_recommendation_adapter as fixtures
from rigarus_backend import storage, day_recommendation_adapter as adapter
from rigarus_backend.api import create_app
from rigarus_backend.assignment_store import AssignmentStore
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_recommendation_adapter import (
    generate_from_day_snapshot,
    validate_day_snapshot_personnel,
    check_day_snapshot_freshness,
    SnapshotNotFound,
    SnapshotReadError,
)
from rigarus_backend.day_personnel_validation import (
    ProposedDayMembers,
    validate_day_candidate_personnel,
    check_day_candidate_personnel_freshness,
)
from rigarus_backend.staffing_store import StaffingStore

MON = "2026-11-23"
FRI = "2026-11-27"


class DayPersonnelIntegrationTests(unittest.TestCase):
    setUp = fixtures.DayAdapterTests.setUp
    daily = fixtures.DayAdapterTests.daily
    calendar = fixtures.DayAdapterTests.calendar
    snapshot = fixtures.DayAdapterTests.snapshot
    employee = fixtures.DayAdapterTests.employee
    day = fixtures.DayAdapterTests.day
    visit = fixtures.DayAdapterTests.visit
    digest = fixtures.DayAdapterTests.digest

    def candidate(self, snapshot=None):
        snapshot = snapshot or self.snapshot()
        return next(
            c
            for c in generate_from_day_snapshot(snapshot).generated.candidates
            if c.crew_id == self.c1.id
        )

    def members(self, person):
        return (
            ProposedDayMembers(MON, (person.id,)),
            ProposedDayMembers(FRI, (person.id,)),
        )

    def legacy_worker(self, person, crew=None, half="AM", day=MON):
        row = self.visit(crew=crew or self.c2.id, half=half, day=day)
        StaffingStore(self.database).save(row.id, (person.id,), row.revision)
        return AssignmentStore(self.database).read(row.id)

    def test_saved_daily_cross_crew_actual_worker_report_and_default_candidates_pending(
        self,
    ):
        person = self.employee()
        one = self.day(workers=(person.id,))
        two = self.day(crew=self.c2.id, workers=(person.id,))
        result = generate_from_day_snapshot(self.snapshot())
        report = result.personnel_validation
        self.assertEqual(report.state, "Blocked")
        self.assertEqual(
            {r.record_id for r in report.conflicts[0].visits}, {one["id"], two["id"]}
        )
        self.assertIn("PersonnelConflicts", result.pending_validators)
        self.assertFalse(result.applyable or result.publishable)
        self.assertTrue(
            all(c.validation_status == "Pending" for c in result.generated.candidates)
        )

    def test_daily_and_any_legacy_half_members_conflict_and_equal_ids_remain_distinct(
        self,
    ):
        person = self.employee()
        old = self.legacy_worker(person, half="PM")
        new = self.day(workers=(person.id,))
        self.assertEqual(old.id, new["id"])
        report = validate_day_snapshot_personnel(self.snapshot())
        self.assertEqual(report.state, "Blocked")
        self.assertEqual(
            {r.record_kind for r in report.conflicts[0].visits},
            {"FullDayDraft", "LegacyHalfDay"},
        )
        self.assertEqual(
            next(
                r.legacy_slot
                for r in report.conflicts[0].visits
                if r.record_kind == "LegacyHalfDay"
            ),
            "PM",
        )

    def test_cancel_and_latest_staff_replacement_release_without_history_union(self):
        person = self.employee()
        other = self.employee("Synthetic replacement")
        first = self.day(workers=(person.id,))
        second = self.day(crew=self.c2.id, workers=(person.id,))
        before = self.snapshot()
        DayDraftStore(self.database).save(
            DayDraft(
                self.work.id, self.c2.id, MON, "Synthetic replaced staff", (other.id,)
            ),
            second["id"],
            1,
        )
        self.assertEqual(
            check_day_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(
            validate_day_snapshot_personnel(self.snapshot()).state, "Satisfied"
        )
        DayDraftStore(self.database).cancel(first["id"], 1)
        report = validate_day_snapshot_personnel(self.snapshot())
        self.assertEqual(report.state, "Satisfied")
        self.assertEqual(report.ignored_cancelled[0].record_id, first["id"])
        self.assertEqual(len(DayDraftStore(self.database).history(second["id"])), 2)

    def test_extra_proposed_employee_capture_is_same_view_observation_not_attendance(
        self,
    ):
        person = self.employee(home=self.tower.id)
        self.daily("Employee", person.id, state="Available")
        snapshot = self.snapshot(proposed_employee_ids=(person.id,))
        self.assertEqual([e.employee_id for e in snapshot.employees], [person.id])
        raw = json.loads(
            next(s.payload_json for s in snapshot.daily_inputs if s.scope == "Employee")
        )
        self.assertEqual(raw["entries"][0]["state"], "Available")
        self.assertEqual(snapshot.day_assignments, ())
        self.assertEqual(snapshot.legacy_assignments, ())
        self.assertEqual(validate_day_snapshot_personnel(snapshot).state, "Pending")
        candidate = self.candidate(snapshot)
        result = validate_day_candidate_personnel(
            snapshot, candidate, self.members(person)
        )
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(result.source_crew_revalidation, ())
        self.assertEqual(result.validation_status, "Pending")
        self.assertIn("ApprovedDriver", result.pending_validators)
        self.assertIn("EmployeeAvailability", result.pending_validators)
        self.assertFalse(result.applyable or result.publishable)

    def test_unstaffed_empty_or_uncaptured_candidate_never_passes(self):
        person = self.employee(home=self.tower.id)
        snapshot = self.snapshot()
        candidate = self.candidate(snapshot)
        for members in ((), (ProposedDayMembers(MON, ()),), self.members(person)):
            result = validate_day_candidate_personnel(snapshot, candidate, members)
            self.assertEqual(result.state, "Pending")
            self.assertIn("PersonnelConflicts", result.pending_validators)
        result = validate_day_candidate_personnel(
            snapshot, candidate, self.members(person)
        )
        self.assertEqual(result.missing_employee_ids, (person.id,))
        with self.assertRaises(SnapshotNotFound):
            self.snapshot(proposed_employee_ids=(999999,))

    def test_candidate_borrowing_does_not_remove_source_and_blocked_excluded_by_comparator(
        self,
    ):
        person = self.employee(home=self.c2.id)
        source = self.day(crew=self.c2.id, workers=(person.id,))
        snapshot = self.snapshot()
        before = self.digest()
        result = validate_day_candidate_personnel(
            snapshot, self.candidate(snapshot), self.members(person)
        )
        self.assertEqual(result.state, "Blocked")
        self.assertEqual(result.comparison.options, ())
        self.assertEqual(len(result.comparison.excluded), 1)
        self.assertEqual(result.conflicts[0].employee_id, person.id)
        pending = result.source_crew_revalidation[0]
        self.assertEqual(
            (pending.crew_id, pending.local_date, pending.state),
            (self.c2.id, MON, "Pending"),
        )
        self.assertEqual(pending.visits[0].record_id, source["id"])
        self.assertTrue(
            {"ApprovedDriver", "MinimumStaffing", "Qualifications", "Skills"}.issubset(
                pending.pending_checks
            )
        )
        self.assertEqual(
            DayDraftStore(self.database).read(source["id"])["employee_ids"],
            (person.id,),
        )
        self.assertEqual(self.digest(), before)

    def test_proposal_cannot_ignore_legacy_pm_actual_worker_or_opposite_half_sources(
        self,
    ):
        person = self.employee()
        self.legacy_worker(person, half="PM")
        self.legacy_worker(person, crew=self.tower.id, half="AM")
        snapshot = self.snapshot()
        result = validate_day_candidate_personnel(
            snapshot, self.candidate(snapshot), self.members(person)
        )
        self.assertEqual(result.state, "Blocked")
        self.assertEqual(len(result.conflicts[0].visits), 3)
        self.assertEqual(len(result.source_crew_revalidation), 2)
        self.assertEqual(
            {r.legacy_slot for c in result.source_crew_revalidation for r in c.visits},
            {"AM", "PM"},
        )

    def test_unknown_other_crew_staffing_same_date_keeps_candidate_pending(self):
        person = self.employee()
        self.day(crew=self.c2.id)
        snapshot = self.snapshot()
        result = validate_day_candidate_personnel(
            snapshot, self.candidate(snapshot), self.members(person)
        )
        self.assertEqual(result.state, "Pending")
        self.assertIn("OTHER_CREW_STAFFING_UNKNOWN", result.checks[0].reasons)
        self.assertEqual(len(result.comparison.options), 1)

    def test_unrelated_saved_conflict_is_visible_without_false_candidate_membership(
        self,
    ):
        busy = self.employee()
        free = self.employee("Synthetic separate worker")
        self.day(crew=self.c2.id, workers=(busy.id,))
        self.day(crew=self.tower.id, workers=(busy.id,))
        snapshot = self.snapshot()
        result = validate_day_candidate_personnel(
            snapshot, self.candidate(snapshot), self.members(free)
        )
        self.assertEqual(result.validation.state, "Blocked")
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(result.conflicts, ())
        self.assertEqual(result.validation_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)

    def test_candidate_snapshot_context_and_membership_dates_are_strict(self):
        snapshot = self.snapshot()
        candidate = self.candidate(snapshot)
        for changed in (
            replace(candidate, crew_id=self.c2.id),
            replace(candidate, work_item_id=999999),
            replace(candidate, allocated_working_dates=(MON,)),
            replace(candidate, option=None),
        ):
            with self.assertRaises(ValueError):
                validate_day_candidate_personnel(snapshot, changed)
        for members in (
            [ProposedDayMembers(MON, None)],
            (ProposedDayMembers(MON, None),) * 2,
            (ProposedDayMembers("2026-11-24", None),),
        ):
            with self.assertRaises(ValueError):
                validate_day_candidate_personnel(snapshot, candidate, members)
        for people in ([1], (1, 1), (True,), tuple(range(1, 1002))):
            with self.assertRaises(ValueError):
                ProposedDayMembers(MON, people)
        for ids in ([1], (True,), (1, 1), tuple(range(1, 1002))):
            with self.assertRaises(ValueError):
                replace(self.query, proposed_employee_ids=ids)

    def test_proposed_employee_query_and_plan_fingerprints_are_deterministic_and_distinct(
        self,
    ):
        first = self.employee(home=self.tower.id)
        second = self.employee("Synthetic extra worker", home=self.tower.id)
        snapshot = self.snapshot(proposed_employee_ids=(second.id, first.id))
        self.assertEqual(
            snapshot, self.snapshot(proposed_employee_ids=(first.id, second.id))
        )
        self.assertNotEqual(
            snapshot.input_fingerprint, self.snapshot().input_fingerprint
        )
        self.assertEqual(adapter.FORMAT, "rigarus-day-recommendation-input-v3")
        candidate = self.candidate(snapshot)
        result = validate_day_candidate_personnel(
            snapshot, candidate, self.members(first)
        )
        replay = validate_day_candidate_personnel(
            snapshot, candidate, tuple(reversed(self.members(first)))
        )
        alternative = validate_day_candidate_personnel(
            snapshot, candidate, self.members(second)
        )
        self.assertEqual(result.proposal_fingerprint, replay.proposal_fingerprint)
        self.assertNotEqual(
            result.proposal_fingerprint, alternative.proposal_fingerprint
        )
        self.assertEqual(result.input_fingerprint, snapshot.input_fingerprint)
        self.assertEqual(len(result.proposal_fingerprint), 64)

    def test_candidate_result_expires_on_source_staff_visit_and_extra_employee_changes(
        self,
    ):
        person = self.employee(home=self.tower.id)
        snapshot = self.snapshot(proposed_employee_ids=(person.id,))
        result = validate_day_candidate_personnel(
            snapshot, self.candidate(snapshot), self.members(person)
        )
        self.assertEqual(
            check_day_candidate_personnel_freshness(self.database, result).status,
            "Current",
        )
        row = self.day(crew=self.c2.id, workers=(person.id,))
        self.assertEqual(
            check_day_candidate_personnel_freshness(self.database, result).status,
            "Stale",
        )
        new = self.snapshot(proposed_employee_ids=(person.id,))
        result = validate_day_candidate_personnel(
            new, self.candidate(new), self.members(person)
        )
        DayDraftStore(self.database).cancel(row["id"], 1)
        self.assertEqual(
            check_day_candidate_personnel_freshness(self.database, result).status,
            "Stale",
        )
        new = self.snapshot(proposed_employee_ids=(person.id,))
        result = validate_day_candidate_personnel(
            new, self.candidate(new), self.members(person)
        )
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(MON, MON, "AM", "Unavailable"), 0
        )
        self.assertEqual(
            check_day_candidate_personnel_freshness(self.database, result).status,
            "Stale",
        )

    def test_new_proposed_employee_metadata_daily_availability_and_membership_revisions_expire(
        self,
    ):
        person = self.employee(home=self.tower.id)
        before = self.snapshot(proposed_employee_ids=(person.id,))
        self.daily("Employee", person.id, state="Available")
        self.assertEqual(
            check_day_snapshot_freshness(self.database, before).status, "Stale"
        )
        before = self.snapshot(proposed_employee_ids=(person.id,))
        with closing(storage.connect(self.database)) as c, c:
            c.execute("UPDATE Employees SET Active=0 WHERE Id=?", (person.id,))
        self.assertEqual(
            check_day_snapshot_freshness(self.database, before).status, "Stale"
        )
        source = self.legacy_worker(person)
        before = self.snapshot(proposed_employee_ids=(person.id,))
        StaffingStore(self.database).save(source.id, (), source.revision)
        self.assertEqual(
            check_day_snapshot_freshness(self.database, before).status, "Stale"
        )

    def test_candidate_check_is_frozen_pure_and_logically_readonly(self):
        person = self.employee()
        snapshot = self.snapshot()
        candidate = self.candidate(snapshot)
        before = self.digest()
        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("time.time", side_effect=AssertionError("clock")),
        ):
            result = validate_day_candidate_personnel(
                snapshot, candidate, self.members(person)
            )
        self.assertEqual(self.digest(), before)
        with self.assertRaises(FrozenInstanceError):
            result.state = "Satisfied"
        self.assertEqual(asdict(snapshot), asdict(self.snapshot()))

    def test_pinned_new_employee_and_staffing_observations_never_mix_later_changes(
        self,
    ):
        person = self.employee(home=self.tower.id)
        expected = self.snapshot(proposed_employee_ids=(person.id,))
        original = adapter._read_day_sources

        def mutate_after_pin(*args):
            def commit():
                self.daily("Employee", person.id, state="Unavailable")
                self.day(crew=self.c2.id, workers=(person.id,))

            with ThreadPoolExecutor(1) as pool:
                pool.submit(commit).result(timeout=10)
            return original(*args)

        with patch.object(adapter, "_read_day_sources", side_effect=mutate_after_pin):
            observed = self.snapshot(proposed_employee_ids=(person.id,))
        self.assertEqual(observed, expected)
        self.assertEqual(validate_day_snapshot_personnel(observed).state, "Pending")
        self.assertEqual(
            check_day_snapshot_freshness(self.database, observed).status, "Stale"
        )

    def test_explicit_employee_observations_respect_read_budget_and_errors(self):
        person = self.employee(home=self.tower.id)
        with patch.object(adapter, "MAX_READ_UNITS", 120):
            with self.assertRaises(SnapshotReadError):
                self.snapshot(
                    proposed_employee_ids=(person.id,), horizon_end_date="2027-11-22"
                )
        snapshot = self.snapshot(proposed_employee_ids=(person.id,))
        result = validate_day_candidate_personnel(
            snapshot, self.candidate(snapshot), self.members(person)
        )
        with patch.object(
            adapter.storage,
            "connect",
            side_effect=sqlite3.OperationalError("Synthetic private source failure"),
        ):
            with self.assertRaises(SnapshotReadError):
                check_day_candidate_personnel_freshness(self.database, result)

    def test_production_gates_and_no_candidate_api_remain_unchanged(self):
        snapshot = self.snapshot()
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
            self.assertEqual(
                client.put(
                    f"/daily-calendars/Crew/{self.c1.id}",
                    json=dict(
                        start_date=MON,
                        end_date=MON,
                        state="Working",
                        confirmed_by_operator=True,
                        expected_revision=0,
                        expected_review_token="a" * 64,
                    ),
                ).status_code,
                409,
            )
            self.assertEqual(
                client.post("/day-personnel-validation", json={}).status_code, 404
            )
        self.assertEqual(self.digest(), before)
        self.assertFalse(generate_from_day_snapshot(snapshot).applyable)
