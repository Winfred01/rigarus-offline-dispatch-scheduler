"""Synthetic dated Rig persistence, SQL guards, coherent views and swap previews."""

import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi.testclient import TestClient
import test_daily_capability_snapshot as capabilities
import test_recommendation_adapter as legacy
from migration_fixture import remove_daily_rig_schema
from rigarus_backend import storage, day_recommendation_adapter as adapter
from rigarus_backend.api import create_app
from rigarus_backend.rigs import RigDraft
from rigarus_backend.rig_store import RigStore
from rigarus_backend.daily_rig_store import (
    DailyRigStore,
    RigAllocationInput,
    RigPeriodInput,
)
from rigarus_backend.daily_rig_validation import validate_day_snapshot_rigs
from rigarus_backend.day_rig_proposal import (
    ProposedDayRig,
    validate_day_rig_proposal,
    validate_saved_rig_change,
    check_rig_proposal_freshness,
)
from rigarus_backend.daily_calendar_store import DailyConflict
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_backup import logical_digest

MON = capabilities.MON
FRI = capabilities.FRI


class DailyRigIntegrationTests(unittest.TestCase):
    setUp = capabilities.DailyCapabilityIntegrationTests.setUp
    daily = capabilities.DailyCapabilityIntegrationTests.daily
    calendar = capabilities.DailyCapabilityIntegrationTests.calendar
    snapshot = capabilities.DailyCapabilityIntegrationTests.snapshot
    employee = capabilities.DailyCapabilityIntegrationTests.employee
    day = capabilities.DailyCapabilityIntegrationTests.day
    visit = capabilities.DailyCapabilityIntegrationTests.visit
    digest = capabilities.DailyCapabilityIntegrationTests.digest
    approve = capabilities.DailyCapabilityIntegrationTests.approve
    available = capabilities.DailyCapabilityIntegrationTests.available
    candidate = capabilities.DailyCapabilityIntegrationTests.candidate
    members = capabilities.DailyCapabilityIntegrationTests.members
    save = capabilities.DailyCapabilityIntegrationTests.save
    borrowing = capabilities.DailyCapabilityIntegrationTests.borrowing
    transfer = capabilities.DailyCapabilityIntegrationTests.transfer

    def rig(self, name="SYN-R1", default=None, active=True):
        return RigStore(self.database).save(
            RigDraft(
                name, "Synthetic vehicle", "Synthetic retained note", default, active
            )
        )

    def allocate(
        self,
        row,
        rig,
        kind="FullDayDraft",
        ready=True,
        original=None,
        reference="Synthetic actual Rig evidence",
    ):
        identity = row["id"] if isinstance(row, dict) else row.id
        store = DailyRigStore(self.database)
        before = store.read_allocation(kind, identity)
        native = (
            store.read_conditions(rig.id, MON, FRI)["condition_revision"] if rig else 0
        )
        orig = (
            original.id
            if original
            else before["original_rig_id"]
            if before["revision"]
            else rig.id
            if rig
            else None
        )
        return store.save_allocation(
            kind,
            identity,
            RigAllocationInput(
                orig,
                rig.id if rig else None,
                ready,
                True,
                kind == "FullDayDraft",
                reference,
                native,
            ),
            before["context"]["assignment_revision"],
            before["revision"],
        )

    def period(
        self,
        rig,
        kind="Maintenance",
        start=MON,
        end=FRI,
        status="Active",
        previous=None,
    ):
        return DailyRigStore(self.database).save_period(
            rig.id,
            kind,
            RigPeriodInput(start, end, status, True, "Synthetic independent condition"),
            previous["period_id"] if previous else None,
            previous["revision"] if previous else 0,
        )

    def test_default_links_never_actual_and_explicit_original_actual_history_noop(self):
        r1 = self.rig(default=self.c1.id)
        r2 = self.rig("SYN-R2", default=self.c1.id)
        row = self.day()
        report = validate_day_snapshot_rigs(self.snapshot())
        self.assertEqual(report.state, "Pending")
        self.assertEqual(report.checks[0].default_rig_ids, (r1.id, r2.id))
        self.assertIsNone(report.checks[0].observation.actual_rig_id)
        allocation = self.allocate(row, r2, original=r1)
        self.assertEqual(self.allocate(row, r2, original=r1)["revision"], 1)
        self.assertEqual(self.allocate(row, r1, original=r1)["revision"], 2)
        self.assertEqual(
            len(
                DailyRigStore(self.database).allocation_history(
                    "FullDayDraft", row["id"]
                )
            ),
            2,
        )
        self.assertEqual(allocation["original_rig_id"], r1.id)
        with self.assertRaises(sqlite3.IntegrityError):
            self.allocate(row, r2, original=r2)
        storage.initialize_database(self.database)
        self.assertEqual(
            validate_day_snapshot_rigs(self.snapshot()).checks[0].availability_state,
            "Satisfied",
        )

    def test_second_crew_same_date_rig_rejected_and_different_rig_allowed(self):
        a, b = self.day(), self.day(crew=self.c2.id)
        r1, r2 = self.rig(), self.rig("SYN-R2")
        self.allocate(a, r1)
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            self.allocate(b, r1)
        self.assertEqual(self.digest(), before)
        self.allocate(b, r2)
        self.assertEqual(validate_day_snapshot_rigs(self.snapshot()).state, "Satisfied")

    def test_same_rig_different_dates_and_cancelled_release_with_sql_restore_guard(
        self,
    ):
        r = self.rig()
        a = self.day()
        self.allocate(a, r)
        DayDraftStore(self.database).cancel(a["id"], a["revision"])
        b = self.day(crew=self.c2.id)
        self.allocate(b, r)
        before = self.digest()
        with closing(storage.connect(self.database)) as c, c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(
                    "UPDATE DayDraftAssignments SET Status='Draft',Revision=Revision+1 WHERE Id=?",
                    (a["id"],),
                )
        self.assertEqual(self.digest(), before)
        self.allocate(self.day(crew=self.c1.id, day=FRI), r)

    def test_legacy_am_pm_same_crew_preserved_and_whole_date_conflicts(self):
        r = self.rig()
        am, pm = self.visit(), self.visit(half="PM")
        self.allocate(am, r, "LegacyHalfDay", False)
        self.allocate(pm, r, "LegacyHalfDay", False)
        report = validate_day_snapshot_rigs(self.snapshot())
        self.assertFalse(report.conflicts)
        self.assertTrue(all(c.availability_state == "Pending" for c in report.checks))
        with self.assertRaises(sqlite3.IntegrityError):
            self.allocate(self.day(crew=self.c2.id), r)
        self.assertEqual(
            {c.observation.visit.legacy_slot for c in report.checks}, {"AM", "PM"}
        )

    def test_independent_overlapping_conditions_do_not_clear_each_other_or_readiness(
        self,
    ):
        r = self.rig()
        row = self.day()
        self.allocate(row, r)
        maintenance = self.period(r)
        inspection = self.period(r, "Inspection")
        self.assertEqual(validate_day_snapshot_rigs(self.snapshot()).state, "Blocked")
        with self.assertRaises(DailyConflict):
            self.allocate(row, r)
        self.period(r, status="Cancelled", previous=maintenance)
        report = validate_day_snapshot_rigs(self.snapshot())
        self.assertEqual(
            report.checks[0].blocked_period_ids, (inspection["period_id"],)
        )
        self.period(r, "Inspection", status="Cancelled", previous=inspection)
        self.assertEqual(
            validate_day_snapshot_rigs(self.snapshot()).checks[0].availability_state,
            "Pending",
        )
        self.allocate(row, r)
        self.assertEqual(
            validate_day_snapshot_rigs(self.snapshot()).checks[0].availability_state,
            "Satisfied",
        )

    def test_master_inactive_and_explicit_out_of_service_block(self):
        r = self.rig()
        row = self.day()
        self.allocate(row, r)
        RigStore(self.database).save(
            RigDraft(r.number, r.type, r.notes, None, False), r.id
        )
        self.assertEqual(validate_day_snapshot_rigs(self.snapshot()).state, "Blocked")
        with self.assertRaises(DailyConflict):
            self.allocate(row, r)
        RigStore(self.database).save(
            RigDraft(r.number, r.type, r.notes, None, True), r.id
        )
        self.period(r, "OutOfService")
        self.assertEqual(validate_day_snapshot_rigs(self.snapshot()).state, "Blocked")

    def test_condition_changes_between_review_and_save_rejected_including_outside_horizon(
        self,
    ):
        r = self.rig()
        row = self.day()
        self.period(r, start="2027-01-01", end="2027-01-01")
        with self.assertRaises(DailyConflict):
            DailyRigStore(self.database).save_allocation(
                "FullDayDraft",
                row["id"],
                RigAllocationInput(
                    r.id, r.id, True, True, True, "Synthetic stale confirmation", 0
                ),
                row["revision"],
                0,
            )

    def test_concurrent_allocation_writers_cannot_double_book_and_rollback_identity(
        self,
    ):
        r = self.rig()
        a, b = self.day(), self.day(crew=self.c2.id)

        def write(row):
            try:
                self.allocate(row, r)
                return "Saved"
            except sqlite3.IntegrityError:
                return "Blocked"

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(write, (a, b))), ["Blocked", "Saved"])
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute("SELECT count(*) FROM RigAllocations").fetchone(), (1,)
            )

    def test_sql_context_move_and_legacy_api_report_rig_conflict_409(self):
        r = self.rig()
        a = self.visit(crew=self.c1.id)
        b = self.visit(crew=self.c2.id, day="2026-11-24")
        self.allocate(a, r, "LegacyHalfDay", False)
        self.allocate(b, r, "LegacyHalfDay", False)
        with TestClient(create_app(self.database)) as client:
            before = self.digest()
            response = client.put(
                f"/draft-assignments/{b.id}",
                json=dict(
                    work_item_id=self.work.id,
                    crew_id=self.c2.id,
                    local_date=MON,
                    slot="AM",
                    notes=b.notes,
                    expected_revision=b.revision,
                ),
            )
            self.assertEqual(response.status_code, 409, response.text)
            self.assertIn("Rig conflict", response.json()["detail"])
            self.assertEqual(self.digest(), before)

    def test_saved_date_move_stales_readiness_and_reserves_old_new_until_explicit_review(
        self,
    ):
        r = self.rig()
        a = self.day()
        self.allocate(a, r)
        moved = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, FRI, "Synthetic moved source", None),
            a["id"],
            a["revision"],
        )
        report = validate_day_snapshot_rigs(self.snapshot())
        self.assertEqual(report.state, "Pending")
        self.assertTrue(report.checks[0].observation.context_stale)
        other = self.day(crew=self.c2.id)
        with self.assertRaises(sqlite3.IntegrityError):
            self.allocate(other, r)
        self.allocate(moved, r)
        self.allocate(other, r)
        self.assertEqual(validate_day_snapshot_rigs(self.snapshot()).state, "Satisfied")

    def test_stale_allocation_recorded_inside_scope_current_outside_cannot_be_ignored(
        self,
    ):
        r = self.rig()
        row = self.day()
        self.allocate(row, r)
        DayDraftStore(self.database).save(
            DayDraft(
                self.work.id, self.c1.id, "2027-01-01", "Synthetic moved outside", None
            ),
            row["id"],
            row["revision"],
        )
        snapshot = self.snapshot()
        self.assertFalse(snapshot.day_assignments)
        report = validate_day_snapshot_rigs(snapshot)
        self.assertEqual(report.state, "Pending")
        self.assertEqual(report.checks[0].observation.recorded_date, MON)
        with self.assertRaises(sqlite3.IntegrityError):
            self.allocate(self.day(crew=self.c2.id), r)

    def test_stale_recorded_occupancy_retains_original_workitem_and_parent_ids(self):
        from rigarus_backend.daily_rig_validation import (
            snapshot_rig_inputs,
            validate_daily_rigs,
            RigVisit,
        )
        from rigarus_backend.daily_personnel_conflicts import DailyStaffedVisit

        r = self.rig()
        row = self.day()
        self.allocate(row, r)
        other = capabilities.ProjectStore(self.database).save(
            capabilities.ProjectDraft(
                "SYN-RIG-MOVED",
                "0111",
                "Synthetic other parent",
                [capabilities.WorkItemDraft(None, capabilities.WorkType.CIVIL, 1, 99)],
            )
        )
        DayDraftStore(self.database).save(
            DayDraft(
                other.work_items[0].id,
                self.c1.id,
                FRI,
                "Synthetic moved work context",
                None,
            ),
            row["id"],
            row["revision"],
        )
        snapshot = self.snapshot()
        observations, rigs, conditions = snapshot_rig_inputs(snapshot)
        self.assertEqual(observations[0].visit.project_id, other.id)
        self.assertEqual(observations[0].recorded_project_id, self.project.id)
        target = DailyStaffedVisit(
            "Proposal",
            999,
            self.work.id,
            self.project.id,
            self.c2.id,
            MON,
            1,
            "Draft",
            False,
            (),
        )
        proposed = RigVisit(
            target, r.id, r.id, True, True, 0, evidence_source="Proposed"
        )
        report = validate_daily_rigs(
            (*observations, proposed),
            rigs,
            conditions,
            start_date=MON,
            end_date=FRI,
            scope_complete=True,
        )
        old = next(
            ref
            for conflict in report.conflicts
            for ref in conflict.visits
            if ref.source == "Recorded"
        )
        self.assertEqual(
            (old.work_item_id, old.project_id), (self.work.id, self.project.id)
        )

    def test_read_revision_identity_history_and_atomic_failure(self):
        r = self.rig()
        row = self.day()
        a = self.allocate(row, r)
        store = DailyRigStore(self.database)
        with self.assertRaises(DailyConflict):
            store.save_allocation(
                "FullDayDraft",
                row["id"],
                RigAllocationInput(r.id, r.id, True, True, True, "Synthetic", 0),
                row["revision"],
                0,
            )
        with closing(storage.connect(self.database)) as c, c:
            for sql in (
                "UPDATE RigAllocationChanges SET Reference='changed'",
                "DELETE FROM RigAllocationChanges",
                "DELETE FROM RigAllocations",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)
            c.execute(
                "CREATE TRIGGER SyntheticRigFailure BEFORE INSERT ON RigAllocationChanges BEGIN SELECT RAISE(ABORT,'Synthetic failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            self.allocate(row, r, reference="Synthetic updated reference")
        self.assertEqual(self.digest(), before)
        self.assertEqual(a["revision"], 1)

    def test_condition_revision_identity_noop_history_and_bad_inputs(self):
        r = self.rig()
        p = self.period(r)
        self.assertEqual(self.period(r, previous=p), p)
        p2 = self.period(r, status="Cancelled", previous=p)
        self.assertEqual(
            len(DailyRigStore(self.database).period_history(p["period_id"])), 2
        )
        with self.assertRaises(DailyConflict):
            self.period(r, previous=p)
        self.assertEqual(p2["revision"], 2)
        for make in (
            lambda: RigPeriodInput("2026-02-30", FRI, "Active", True, "Synthetic"),
            lambda: RigPeriodInput(MON, FRI, "Active", 1, "Synthetic"),
            lambda: RigAllocationInput(r.id, r.id, True, True, False, "Synthetic", 0),
            lambda: RigAllocationInput(r.id, r.id, True, True, True, "", 0),
            lambda: self.period(r, "Invalid"),
            lambda: DailyRigStore(self.database).read_conditions(999999, MON, FRI),
        ):
            with self.assertRaises((ValueError, LookupError)):
                make()

    def candidate_setup(self):
        p = self.employee()
        self.available(p)
        self.approve(p)
        self.save("WorkItem", self.work.id, capabilities.REQ)
        self.save("Employee", p.id, "Verified", "SYN-Q")
        return p

    def test_generated_candidate_explicit_rig_versus_missing_default_unknown_or_blocked(
        self,
    ):
        p = self.candidate_setup()
        r = self.rig(default=self.c1.id)
        snapshot = self.snapshot(
            proposed_employee_ids=(p.id,), proposed_rig_ids=(r.id,)
        )
        c = self.candidate(snapshot)
        missing = validate_day_rig_proposal(snapshot, c, self.members(p))
        self.assertEqual(missing.state, "Pending")
        self.assertTrue(all(choice.actual_rig_id is None for choice in missing.choices))
        choices = tuple(
            ProposedDayRig(d, r.id, True, "Synthetic explicit planning evidence", r.id)
            for d in c.allocated_working_dates
        )
        result = validate_day_rig_proposal(
            snapshot, c, self.members(p), choices=choices
        )
        self.assertEqual(result.state, "Satisfied")
        self.assertIn("RigDriverCategory", result.pending_validators)
        self.assertFalse(result.applyable or result.publishable)
        self.assertEqual(
            result,
            validate_day_rig_proposal(
                snapshot, c, self.members(p), choices=tuple(reversed(choices))
            ),
        )
        self.period(r, "Inspection")
        self.assertEqual(
            check_rig_proposal_freshness(self.database, result).status, "Stale"
        )
        snapshot = self.snapshot(
            proposed_employee_ids=(p.id,), proposed_rig_ids=(r.id,)
        )
        blocked = validate_day_rig_proposal(
            snapshot, self.candidate(snapshot), self.members(p), choices=choices
        )
        self.assertEqual(blocked.state, "Blocked")
        self.assertFalse(blocked.comparison.options)

    def test_borrowed_source_rig_block_propagates_despite_target_and_people_pass(self):
        p, r, _, _, source = self.transfer(capabilities.REQ)
        source_rig, target_rig = self.rig(), self.rig("SYN-R2")
        row = DayDraftStore(self.database).read(source.record_id)
        self.allocate(row, source_rig)
        self.period(source_rig, "Maintenance")
        snapshot = self.snapshot(
            proposed_employee_ids=(p.id, r.id), proposed_rig_ids=(target_rig.id,)
        )
        candidate = self.candidate(snapshot)
        choices = tuple(
            ProposedDayRig(d, target_rig.id, True, "Synthetic target Rig")
            for d in candidate.allocated_working_dates
        )
        result = validate_day_rig_proposal(
            snapshot, candidate, self.members(p), (source,), choices
        )
        self.assertEqual(result.capability.state, "Satisfied")
        self.assertEqual(result.state, "Blocked")
        self.assertFalse(result.comparison.options)
        source_check = next(
            c
            for c in result.after.checks
            if c.observation.visit.record_kind != "Proposal"
        )
        self.assertEqual(source_check.observation.visit.employee_ids, (r.id,))

    def test_rig_query_and_proposal_invalid_contracts(self):
        p = self.candidate_setup()
        r = self.rig()
        snapshot = self.snapshot(
            proposed_employee_ids=(p.id,), proposed_rig_ids=(r.id,)
        )
        candidate = self.candidate(snapshot)
        choice = ProposedDayRig(MON, r.id, True, "Synthetic reference")
        for changes in (
            dict(proposed_rig_ids=(r.id, r.id)),
            dict(proposed_rig_ids=[r.id]),
            dict(proposed_rig_ids=(True,)),
        ):
            with self.assertRaises(ValueError):
                self.snapshot(**changes)
        for choices in (
            (choice, choice),
            (ProposedDayRig("2027-01-01", r.id, True, "Synthetic reference"),),
            [choice],
        ):
            with self.assertRaises(ValueError):
                validate_day_rig_proposal(
                    snapshot, candidate, self.members(p), choices=choices
                )
        for make in (
            lambda: ProposedDayRig("2026-02-30", r.id, True, "Synthetic"),
            lambda: ProposedDayRig(MON, None, True, "Synthetic"),
            lambda: ProposedDayRig(MON, r.id, 1, "Synthetic"),
            lambda: ProposedDayRig(MON, r.id, True, ""),
        ):
            with self.assertRaises(ValueError):
                make()

    def test_saved_swap_keeps_original_and_actual_before_after_without_write(self):
        r1, r2 = self.rig(), self.rig("SYN-R2")
        row = self.day()
        self.allocate(row, r1)
        self.period(r1)
        snapshot = self.snapshot(proposed_rig_ids=(r2.id,))
        before = self.digest()
        choice = ProposedDayRig(
            MON, r2.id, True, "Synthetic replacement planning evidence"
        )
        result = validate_saved_rig_change(
            snapshot, "FullDayDraft", row["id"], row["revision"], 1, choice
        )
        self.assertEqual(result.before.state, "Blocked")
        self.assertEqual(result.state, "Satisfied")
        after = result.after.checks[0].observation
        self.assertEqual(after.evidence_source, "Proposed")
        self.assertEqual((after.original_rig_id, after.actual_rig_id), (r1.id, r2.id))
        self.assertFalse(result.applyable or result.publishable)
        self.assertEqual(self.digest(), before)
        self.assertEqual(
            DailyRigStore(self.database).read_allocation("FullDayDraft", row["id"])[
                "actual_rig_id"
            ],
            r1.id,
        )

    def test_saved_swap_target_occupied_unknown_or_missing_context_never_passes(self):
        r1, r2 = self.rig(), self.rig("SYN-R2")
        one, two = self.day(), self.day(crew=self.c2.id)
        self.allocate(one, r1)
        self.allocate(two, r2)
        snapshot = self.snapshot(proposed_rig_ids=(r2.id,))
        result = validate_saved_rig_change(
            snapshot,
            "FullDayDraft",
            one["id"],
            1,
            1,
            ProposedDayRig(MON, r2.id, True, "Synthetic busy replacement"),
        )
        self.assertEqual(result.state, "Blocked")
        with self.assertRaises(ValueError):
            validate_saved_rig_change(
                snapshot, "FullDayDraft", one["id"], 999, 1, result.choice
            )
        missing = validate_saved_rig_change(
            snapshot,
            "FullDayDraft",
            one["id"],
            1,
            1,
            ProposedDayRig(MON, 999999, True, "Synthetic uncaptured replacement"),
        )
        self.assertEqual(missing.state, "Pending")

    def test_rig_snapshot_query_fingerprints_limits_readonly_and_coherent_concurrent_period(
        self,
    ):
        r = self.rig()
        row = self.day()
        self.allocate(row, r)
        before = self.snapshot(proposed_rig_ids=(r.id,))
        self.assertEqual(adapter.FORMAT, "rigarus-day-recommendation-input-v6")
        self.assertEqual(before, self.snapshot(proposed_rig_ids=(r.id,)))
        with self.assertRaises(adapter.SnapshotNotFound):
            self.snapshot(proposed_rig_ids=(999999,))
        original = adapter._read_schema

        def concurrent(c):
            migrations = original(c)
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(self.period, r, "Inspection").result(timeout=10)
            return migrations

        with patch.object(adapter, "_read_schema", side_effect=concurrent):
            self.assertEqual(self.snapshot(proposed_rig_ids=(r.id,)), before)
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, before).status, "Stale"
        )
        with patch.object(adapter, "MAX_READ_BYTES", 1):
            with self.assertRaises(adapter.SnapshotReadError):
                self.snapshot()

    def test_detached_pure_swap_and_logical_immutability(self):
        r1, r2 = self.rig(), self.rig("SYN-R2")
        row = self.day()
        self.allocate(row, r1)
        snapshot = self.snapshot(proposed_rig_ids=(r2.id,))
        before = self.digest()
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
            patch("time.time", side_effect=AssertionError),
        ):
            validate_saved_rig_change(
                snapshot,
                "FullDayDraft",
                row["id"],
                1,
                1,
                ProposedDayRig(MON, r2.id, True, "Synthetic pure swap"),
            )
        self.assertEqual(self.digest(), before)


class DailyRigMigrationTests(unittest.TestCase):
    setUp = DailyRigIntegrationTests.setUp
    daily = DailyRigIntegrationTests.daily
    calendar = DailyRigIntegrationTests.calendar
    employee = DailyRigIntegrationTests.employee
    day = DailyRigIntegrationTests.day
    snapshot = DailyRigIntegrationTests.snapshot
    digest = DailyRigIntegrationTests.digest
    rig = DailyRigIntegrationTests.rig

    def old16(self):
        self.rig(default=self.c1.id)
        self.day(workers=(self.employee().id,))
        with closing(storage.connect(self.database)) as c, c:
            remove_daily_rig_schema(c)

    def test_verified16_backup_incremental17_preserves_all_old_data_and_idempotence(
        self,
    ):
        self.old16()
        before = self.digest()
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
            self.assertEqual(logical_digest(c), before)
            self.assertEqual(
                c.execute("SELECT count(*) FROM __EFMigrationsHistory").fetchone(),
                (16,),
            )
        with closing(storage.connect(self.database)) as c:
            for table, rows in original.items():
                current = c.execute('SELECT * FROM "' + table + '"').fetchall()
                self.assertEqual(
                    current[: len(rows)]
                    if table == "__EFMigrationsHistory"
                    else current,
                    rows,
                    table,
                )
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
        after = self.digest()
        storage.initialize_database(self.database)
        self.assertEqual(self.digest(), after)

    def test_migration_failure_backup_failure_rollback_and_retry(self):
        self.old16()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticRigMigrationFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDailyRigs' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticRigMigrationFailure")
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
        self.assertEqual(len(self.snapshot().migrations), 21)

    def test_readonly16_rejects_without_migration(self):
        self.old16()
        before = self.digest()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        self.assertEqual(self.digest(), before)


class DailyRigLegacyGuardTests(unittest.TestCase):
    setUp = legacy.AdapterTests.setUp
    calendar = legacy.AdapterTests.calendar
    snapshot = legacy.AdapterTests.snapshot

    def test_old_half_day_adapter_refuses_rig_conditions_and_expires_earlier_proof(
        self,
    ):
        from rigarus_backend.recommendation_adapter import (
            SnapshotContextError,
            check_snapshot_freshness,
        )

        before = self.snapshot()
        r = RigStore(self.database).save(RigDraft("SYN-R1", "Synthetic truck"))
        DailyRigStore(self.database).save_period(
            r.id,
            "Inspection",
            RigPeriodInput(MON, FRI, "Active", True, "Synthetic inspection"),
        )
        with self.assertRaises(SnapshotContextError):
            self.snapshot()
        self.assertEqual(
            check_snapshot_freshness(self.database, before).reason,
            "DAILY_RIG_ADAPTER_REQUIRED",
        )
