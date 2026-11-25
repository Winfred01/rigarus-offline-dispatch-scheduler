"""Synthetic schema15 evidence, coherent snapshots and detached borrowing checks."""

import json
import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch

import test_day_recommendation_adapter as fixtures
import test_recommendation_adapter as legacy_fixtures
from migration_fixture import remove_daily_driver_schema
from rigarus_backend import storage, day_recommendation_adapter as adapter
from rigarus_backend.daily_driver_store import (
    DailyDriverApprovalStore,
    DailyDriverApprovalDraft,
)
from rigarus_backend.daily_calendar_store import DailyConflict, DailySourceError
from rigarus_backend.driver_store import DriverApprovalStore
from rigarus_backend.driver_eligibility import DriverApprovalDraft
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.daily_driver_validation import validate_day_snapshot_drivers
from rigarus_backend.day_personnel_validation import ProposedDayMembers
from rigarus_backend.day_driver_proposal import (
    SourceDayMembers,
    validate_day_driver_proposal,
    check_day_driver_proposal_freshness,
)
from rigarus_backend.recommendation_adapter import SnapshotReadError
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.day_draft_store import DayDraftStore

MON = "2026-11-23"
FRI = "2026-11-27"


class DailyDriverSnapshotTests(unittest.TestCase):
    setUp = fixtures.DayAdapterTests.setUp
    daily = fixtures.DayAdapterTests.daily
    calendar = fixtures.DayAdapterTests.calendar
    snapshot = fixtures.DayAdapterTests.snapshot
    employee = fixtures.DayAdapterTests.employee
    day = fixtures.DayAdapterTests.day
    visit = fixtures.DayAdapterTests.visit
    digest = fixtures.DayAdapterTests.digest

    def approve(
        self,
        person,
        state="Active",
        start=MON,
        end=FRI,
        reviewed=True,
        reference="Synthetic whole-day company assertion",
    ):
        store = DailyDriverApprovalStore(self.database)
        before = store.read(person.id, start, end)
        return store.save(
            person.id,
            DailyDriverApprovalDraft(
                start, end, state, True, True, reference, reviewed
            ),
            before["revision"],
            before["review_token"],
        )

    def old(self, person, state="Active", half="FullDay", start=MON, end=FRI):
        store = DriverApprovalStore(self.database)
        return store.save(
            person.id,
            DriverApprovalDraft(
                start, end, half, state, True, "Synthetic old company statement"
            ),
            store.read(person.id, start, end)["revision"],
        )

    def available(self, person, state="Available"):
        return self.daily("Employee", person.id, MON, FRI, state)

    def prepare(self):
        person = self.employee()
        self.day(workers=(person.id,))
        self.available(person)
        return person

    def candidate(self, snapshot):
        return next(
            c
            for c in adapter.generate_from_day_snapshot(snapshot).generated.candidates
            if c.crew_id == self.c1.id
        )

    def members(self, person):
        return (
            ProposedDayMembers(MON, (person.id,)),
            ProposedDayMembers(FRI, (person.id,)),
        )

    def test_new_daily_company_evidence_saved_report_restart_and_history(self):
        p = self.prepare()
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Pending"
        )
        result = self.approve(p)
        self.assertEqual(result["entries"][0]["state"], "Active")
        plan = adapter.generate_from_day_snapshot(self.snapshot())
        self.assertEqual(plan.driver_validation.state, "Satisfied")
        self.assertFalse(plan.applyable or plan.publishable)
        self.assertEqual(len(DailyDriverApprovalStore(self.database).history(p.id)), 1)
        self.assertEqual(self.approve(p)["revision"], 1)
        self.assertEqual(
            self.approve(p, reference="Synthetic revised reference")["revision"], 2
        )
        self.assertEqual(len(DailyDriverApprovalStore(self.database).history(p.id)), 2)
        storage.initialize_database(self.database)
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Satisfied"
        )

    def test_old_am_pm_even_full_day_history_never_proves_new_full_day(self):
        p = self.prepare()
        for half in ("AM", "PM", "FullDay"):
            self.old(p, half=half)
            result = validate_day_snapshot_drivers(self.snapshot())
            self.assertEqual(result.state, "Pending")
        self.approve(p)
        raw = json.loads(
            next(
                e for e in self.snapshot().employees if e.employee_id == p.id
            ).daily_driver_json
        )
        self.assertTrue(raw["entries"][0]["legacy_needs_review"])
        self.assertEqual(len(raw["entries"][0]["legacy_entries"]), 2)
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Satisfied"
        )

    def test_legacy_negative_review_staleness_and_unknown_do_not_resurrect(self):
        p = self.prepare()
        self.old(p, "Suspended", half="PM")
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Blocked"
        )
        with self.assertRaises(DailyConflict):
            self.approve(p, reviewed=False)
        self.approve(p)
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Satisfied"
        )
        before = self.snapshot()
        self.old(p, "Expired", half="AM")
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Blocked"
        )
        self.approve(p, "Unverified")
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Blocked"
        )
        self.approve(p)
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Satisfied"
        )

    def test_old_out_of_range_edits_expire_positive_receipt(self):
        p = self.prepare()
        self.approve(p)
        before = self.snapshot()
        self.old(p, start="2027-01-01", end="2027-01-01")
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Pending"
        )

    def test_half_day_available_never_daily_available_and_known_unavailable_blocks(
        self,
    ):
        p = self.employee()
        self.day(workers=(p.id,))
        self.approve(p)
        AvailabilityStore(self.database).save(
            p.id, AvailabilityDraft(MON, FRI, "AM", "Available"), 0
        )
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Pending"
        )
        self.available(p)
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Satisfied"
        )
        AvailabilityStore(self.database).save(
            p.id, AvailabilityDraft(MON, MON, "PM", "Unavailable"), 1
        )
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Blocked"
        )

    def test_company_states_explicit_tombstones_and_closed_date_range(self):
        p = self.prepare()
        for state, expected in (
            ("Active", "Satisfied"),
            ("Suspended", "Blocked"),
            ("Expired", "Blocked"),
            ("Unverified", "Pending"),
        ):
            self.approve(p, state)
            self.assertEqual(
                validate_day_snapshot_drivers(self.snapshot()).state, expected
            )
        self.approve(p, start=FRI, end=FRI)
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Pending"
        )

    def test_revision_range_token_and_concurrent_writers(self):
        p = self.employee()
        store = DailyDriverApprovalStore(self.database)
        before = store.read(p.id, MON, FRI)
        draft = DailyDriverApprovalDraft(
            MON, FRI, "Active", True, True, "Synthetic concurrent assertion"
        )

        def write():
            try:
                store.save(p.id, draft, 0, before["review_token"])
                return "Saved"
            except DailyConflict:
                return "Stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(
                sorted(pool.map(lambda _: write(), range(2))), ["Saved", "Stale"]
            )
        with self.assertRaises(DailyConflict):
            store.save(
                p.id,
                replace(draft, end_date=MON),
                1,
                store.read(p.id, MON, FRI)["review_token"],
            )

    def test_source_edit_between_review_and_save_rejected(self):
        p = self.employee()
        store = DailyDriverApprovalStore(self.database)
        before = store.read(p.id, MON, FRI)
        self.old(p)
        with self.assertRaises(DailyConflict):
            store.save(
                p.id,
                DailyDriverApprovalDraft(
                    MON, FRI, "Active", True, True, "Synthetic assertion", True
                ),
                0,
                before["review_token"],
            )

    def test_history_cell_constraints_and_range_write_failure_rollback(self):
        p = self.employee()
        self.approve(p)
        before = self.digest()
        with closing(storage.connect(self.database)) as c, c:
            for sql in (
                "UPDATE DailyDriverApprovalChanges SET Reference='changed'",
                "DELETE FROM DailyDriverApprovalChanges",
                "UPDATE DailyDriverApprovalCells SET LocalDate='2027-01-01'",
                "UPDATE DailyDriverApprovalCells SET State='Expired'",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticDriverFailure BEFORE UPDATE ON DailyDriverApprovalCells WHEN NEW.LocalDate='2026-11-25' BEGIN SELECT RAISE(ABORT,'Synthetic failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            self.approve(p, "Suspended")
        self.assertEqual(self.digest(), before)

    def test_invalid_input_and_unknown_employee(self):
        valid = DailyDriverApprovalDraft(
            MON, FRI, "Active", True, True, "Synthetic assertion"
        )
        for change in (
            dict(start_date="2026-02-30"),
            dict(end_date="2028-01-01"),
            dict(state="Approved"),
            dict(company_confirmed=1),
            dict(full_day_confirmed=False),
            dict(reference=""),
            dict(reference="x" * 201),
            dict(notes="\0"),
            dict(legacy_reviewed=1),
        ):
            with self.assertRaises(ValueError):
                replace(valid, **change)
        with self.assertRaises(ValueError):
            DailyDriverApprovalStore(self.database).read(999999, MON, FRI)

    def test_saved_legacy_attendance_pending_even_new_approval_available(self):
        p = self.employee()
        old = self.visit(crew=self.c2.id, half="PM")
        StaffingStore(self.database).save(old.id, (p.id,), old.revision)
        self.available(p)
        self.approve(p)
        report = validate_day_snapshot_drivers(self.snapshot())
        self.assertEqual(report.state, "Pending")
        self.assertEqual(report.checks[0].visit.legacy_slot, "PM")

    def test_saved_cross_crew_and_cancellation_revalidate_driver(self):
        p = self.prepare()
        self.approve(p)
        other = self.day(crew=self.c2.id, workers=(p.id,))
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Blocked"
        )
        DayDraftStore(self.database).cancel(other["id"], other["revision"])
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Satisfied"
        )

    def borrowing(self, legacy=False):
        p = self.employee(home=self.c2.id)
        replacement = self.employee("Synthetic replacement", home=self.c2.id)
        for person in (p, replacement):
            self.available(person)
            self.approve(person)
        if legacy:
            old = self.visit(crew=self.c2.id, half="PM")
            old = StaffingStore(self.database).save(old.id, (p.id,), old.revision)
            identity, revision = old.id, old.revision
            kind = "LegacyHalfDay"
        else:
            old = self.day(crew=self.c2.id, workers=(p.id,))
            identity, revision = old["id"], old["revision"]
            kind = "FullDayDraft"
        snap = self.snapshot(proposed_employee_ids=(p.id, replacement.id))
        return (
            p,
            replacement,
            snap,
            self.candidate(snap),
            SourceDayMembers(kind, identity, revision, ()),
        )

    def test_borrowing_never_implicitly_removes_source_and_old_pm_counts(self):
        for legacy in (False, True):
            p, replacement, snap, candidate, source = self.borrowing(legacy)
            before = self.digest()
            result = validate_day_driver_proposal(snap, candidate, self.members(p))
            self.assertEqual(result.state, "Blocked")
            self.assertTrue(result.source_checks)
            self.assertEqual(result.source_checks[0].state, "Blocked")
            self.assertFalse(result.comparison.options)
            self.assertEqual(self.digest(), before)
            # Separate fixture for the next record kind.
            if not legacy:
                self.tearDown() if hasattr(self, "tearDown") else None
                self.setUp()

    def test_explicit_sole_driver_removal_blocks_source_even_target_is_eligible(self):
        p, _, snap, candidate, source = self.borrowing()
        result = validate_day_driver_proposal(
            snap, candidate, self.members(p), (source,)
        )
        self.assertEqual(result.before.state, "Satisfied")
        self.assertEqual(result.target_checks[1].state, "Satisfied")
        # Existing2C1 conservatively treats an empty other Crew as unknown scope.
        self.assertEqual(result.target_checks[0].state, "Pending")
        self.assertEqual(result.source_checks[0].state, "Blocked")
        self.assertIn("NO_ACTUAL_MEMBERS", result.source_checks[0].reasons)
        self.assertEqual(result.state, "Blocked")
        self.assertFalse(result.comparison.options)

    def test_explicit_verified_source_replacement_passes_only_driver_subchecks(self):
        p, r, snap, candidate, source = self.borrowing()
        before = self.digest()
        override = replace(source, employee_ids=(r.id,))
        result = validate_day_driver_proposal(
            snap, candidate, self.members(p), (override,)
        )
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(result.source_checks[0].eligible_employee_ids, (r.id,))
        self.assertEqual(len(result.comparison.options), 1)
        self.assertEqual(result.validation_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)
        self.assertIn("MinimumStaffing", result.pending_validators)
        self.assertIn("EmployeeAvailability", result.pending_validators)
        self.assertNotIn("ApprovedDriver", result.pending_validators)
        self.assertEqual(self.digest(), before)
        self.assertEqual(
            check_day_driver_proposal_freshness(self.database, result).status, "Current"
        )
        self.assertEqual(
            result,
            validate_day_driver_proposal(
                snap, candidate, tuple(reversed(self.members(p))), (override,)
            ),
        )
        with self.assertRaises(FrozenInstanceError):
            result.state = "Blocked"

    def test_unknown_replacement_qualification_or_availability_pending(self):
        p, r, snap, candidate, source = self.borrowing()
        self.approve(r, "Unverified")
        snap = self.snapshot(proposed_employee_ids=(p.id, r.id))
        result = validate_day_driver_proposal(
            snap,
            self.candidate(snap),
            self.members(p),
            (replace(source, employee_ids=(r.id,)),),
        )
        self.assertEqual(result.source_checks[0].state, "Pending")
        self.assertEqual(result.state, "Pending")
        self.assertTrue(result.comparison.options)
        self.assertIn("ApprovedDriver", result.pending_validators)

    def test_source_replacement_personnel_conflict_blocks_option_despite_another_driver(
        self,
    ):
        p, r, snap, candidate, source = self.borrowing()
        other = self.employee("Synthetic other eligible source driver", home=self.c2.id)
        self.available(other)
        self.approve(other)
        self.day(crew=self.tower.id, workers=(r.id,))
        snap = self.snapshot(proposed_employee_ids=(p.id, r.id, other.id))
        result = validate_day_driver_proposal(
            snap,
            self.candidate(snap),
            self.members(p),
            (replace(source, employee_ids=(r.id, other.id)),),
        )
        self.assertEqual(result.source_checks[0].state, "Satisfied")
        self.assertEqual(result.state, "Blocked")
        self.assertFalse(result.comparison.options)

    def test_legacy_source_replacement_still_requires_full_day_attendance_review(self):
        p, r, snap, candidate, source = self.borrowing(True)
        result = validate_day_driver_proposal(
            snap, candidate, self.members(p), (replace(source, employee_ids=(r.id,)),)
        )
        self.assertEqual(result.source_checks[0].state, "Pending")
        self.assertEqual(result.state, "Pending")

    def test_source_identity_revision_scope_duplicate_and_candidate_contracts(self):
        p, r, snap, candidate, source = self.borrowing()
        for overrides in (
            (replace(source, expected_revision=999),),
            (replace(source, record_id=99999),),
            (source, source),
            [source],
        ):
            with self.assertRaises(ValueError):
                validate_day_driver_proposal(
                    snap, candidate, self.members(p), overrides
                )
        with self.assertRaises(ValueError):
            validate_day_driver_proposal(
                snap, replace(candidate, crew_id=self.c2.id), self.members(p)
            )
        with self.assertRaises(ValueError):
            SourceDayMembers("Proposal", 1, 1, ())
        with self.assertRaises(ValueError):
            SourceDayMembers("FullDayDraft", 1, 1, None)

    def test_missing_extra_employee_and_empty_target_do_not_pass(self):
        p = self.employee(home=self.tower.id)
        snap = self.snapshot()
        candidate = self.candidate(snap)
        result = validate_day_driver_proposal(snap, candidate, self.members(p))
        self.assertEqual(result.state, "Pending")
        self.assertEqual(result.missing_employee_ids, (p.id,))
        self.assertEqual(validate_day_driver_proposal(snap, candidate).state, "Pending")
        empty = tuple(
            ProposedDayMembers(d, ()) for d in candidate.allocated_working_dates
        )
        self.assertEqual(
            validate_day_driver_proposal(snap, candidate, empty).state, "Blocked"
        )

    def test_driver_source_and_proposal_sha_freshness(self):
        p, r, snap, candidate, source = self.borrowing()
        one = validate_day_driver_proposal(snap, candidate, self.members(p))
        two = validate_day_driver_proposal(
            snap, candidate, self.members(p), (replace(source, employee_ids=(r.id,)),)
        )
        self.assertEqual(adapter.FORMAT, "rigarus-day-recommendation-input-v6")
        self.assertNotEqual(one.proposal_fingerprint, two.proposal_fingerprint)
        self.approve(r, "Suspended")
        self.assertEqual(
            check_day_driver_proposal_freshness(self.database, two).status, "Stale"
        )

    def test_coherent_pinned_old_view_during_concurrent_source_changes(self):
        p = self.prepare()
        self.approve(p)
        before = self.snapshot()
        original = adapter._read_schema

        def concurrent(c):
            migrations = original(c)
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(self.approve, p, "Suspended").result(timeout=10)
                pool.submit(self.available, p, "Unavailable").result(timeout=10)
            return migrations

        with patch.object(adapter, "_read_schema", side_effect=concurrent):
            self.assertEqual(self.snapshot(), before)
        self.assertEqual(validate_day_snapshot_drivers(before).state, "Satisfied")
        self.assertEqual(
            validate_day_snapshot_drivers(self.snapshot()).state, "Blocked"
        )
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, before).status, "Stale"
        )

    def test_detached_no_io_and_logical_no_writes(self):
        p, r, snap, candidate, source = self.borrowing()
        before = self.digest()
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
        ):
            validate_day_snapshot_drivers(snap)
            validate_day_driver_proposal(
                snap,
                candidate,
                self.members(p),
                (replace(source, employee_ids=(r.id,)),),
            )
        self.assertEqual(self.digest(), before)
        self.assertEqual(
            self.snapshot(proposed_employee_ids=snap.query.proposed_employee_ids), snap
        )

    def test_driver_source_limits_and_invalid_history_fail_closed(self):
        p = self.prepare()
        self.approve(p)
        with patch.object(adapter, "MAX_READ_UNITS", 10):
            with self.assertRaises(SnapshotReadError) as caught:
                self.snapshot()
        self.assertEqual(caught.exception.code, "READ_LIMIT_EXCEEDED")
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER DailyDriverApprovalCells_ContextUpdate")
            c.execute("PRAGMA defer_foreign_keys=ON")
            c.execute(
                "UPDATE DailyDriverApprovalCells SET LocalDate='2027-01-01' WHERE LocalDate=?",
                (MON,),
            )
        with self.assertRaises(DailySourceError):
            DailyDriverApprovalStore(self.database).read(
                p.id, "2027-01-01", "2027-01-01"
            )


class DailyDriverMigrationTests(unittest.TestCase):
    setUp = fixtures.DayAdapterTests.setUp
    daily = fixtures.DayAdapterTests.daily
    calendar = fixtures.DayAdapterTests.calendar
    snapshot = fixtures.DayAdapterTests.snapshot
    employee = fixtures.DayAdapterTests.employee
    digest = fixtures.DayAdapterTests.digest
    day = fixtures.DayAdapterTests.day

    def old14(self):
        p = self.employee()
        self.day(workers=(p.id,))
        with closing(storage.connect(self.database)) as c, c:
            remove_daily_driver_schema(c)

    def test_upgrade14_verified_backup_exact_preservation_and_idempotence(self):
        self.old14()
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
                (14,),
            )
        with closing(storage.connect(self.database)) as c:
            for table, values in original.items():
                current = c.execute('SELECT * FROM "' + table + '"').fetchall()
                self.assertEqual(
                    current[: len(values)]
                    if table == "__EFMigrationsHistory"
                    else current,
                    values,
                    table,
                )
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(
                c.execute("SELECT count(*) FROM __EFMigrationsHistory").fetchone(),
                (19,),
            )
        after = self.digest()
        storage.initialize_database(self.database)
        self.assertEqual(self.digest(), after)
        self.assertEqual(len(list(self.database.parent.glob("*.before-day-*.bak"))), 1)

    def test_migration_failure_and_backup_failure_rollback_then_retry(self):
        self.old14()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticDailyDriverMigrationFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDailyDriverApprovals' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticDailyDriverMigrationFailure")
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
        self.assertEqual(len(self.snapshot().migrations), 19)

    def test_read_only_adapter_does_not_migrate14(self):
        self.old14()
        before = self.digest()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        self.assertEqual(self.digest(), before)


class DailyDriverLegacyGuardTests(unittest.TestCase):
    setUp = legacy_fixtures.AdapterTests.setUp
    calendar = legacy_fixtures.AdapterTests.calendar
    employee = legacy_fixtures.AdapterTests.employee
    snapshot = legacy_fixtures.AdapterTests.snapshot

    def test_legacy_adapter_refuses_any_daily_driver_evidence_including_unverified(
        self,
    ):
        from rigarus_backend.recommendation_adapter import (
            SnapshotContextError,
            check_snapshot_freshness,
        )

        p = self.employee()
        before = self.snapshot()
        store = DailyDriverApprovalStore(self.database)
        current = store.read(p.id, MON, FRI)
        store.save(
            p.id,
            DailyDriverApprovalDraft(
                MON, FRI, "Unverified", True, True, "Synthetic explicit unknown"
            ),
            0,
            current["review_token"],
        )
        with self.assertRaises(SnapshotContextError):
            self.snapshot()
        self.assertEqual(
            check_snapshot_freshness(self.database, before).reason,
            "DAILY_DRIVER_ADAPTER_REQUIRED",
        )
