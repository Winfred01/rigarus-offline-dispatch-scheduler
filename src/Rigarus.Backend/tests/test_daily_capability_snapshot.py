"""Synthetic daily evidence, coherent source view and both-Crew borrowing checks."""

import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from unittest.mock import patch

import test_daily_driver_snapshot as drivers
import test_recommendation_adapter as legacy
from migration_fixture import remove_daily_capability_schema
from rigarus_backend import storage, day_recommendation_adapter as adapter
from rigarus_backend.capability_validation import CapabilityRequirements
from rigarus_backend.capability_store import CapabilityEvidenceStore
from rigarus_backend.daily_capability_store import (
    DailyCapabilityStore,
    DailyCapabilityInput,
)
from rigarus_backend.daily_calendar_store import DailyConflict
from rigarus_backend.daily_capability_validation import (
    validate_day_snapshot_capabilities,
)
from rigarus_backend.day_capability_proposal import (
    validate_day_capability_proposal,
    check_day_capability_proposal_freshness,
)
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.project_store import ProjectStore
from rigarus_backend.projects import ProjectDraft, WorkItemDraft, WorkType

MON = drivers.MON
FRI = drivers.FRI
REQ = CapabilityRequirements(1, (0, 1, 0), "Exact", (("SYN-Q", 1),))


class DailyCapabilityIntegrationTests(unittest.TestCase):
    setUp = drivers.DailyDriverSnapshotTests.setUp
    daily = drivers.DailyDriverSnapshotTests.daily
    calendar = drivers.DailyDriverSnapshotTests.calendar
    snapshot = drivers.DailyDriverSnapshotTests.snapshot
    employee = drivers.DailyDriverSnapshotTests.employee
    day = drivers.DailyDriverSnapshotTests.day
    visit = drivers.DailyDriverSnapshotTests.visit
    digest = drivers.DailyDriverSnapshotTests.digest
    approve = drivers.DailyDriverSnapshotTests.approve
    available = drivers.DailyDriverSnapshotTests.available
    prepare = drivers.DailyDriverSnapshotTests.prepare
    candidate = drivers.DailyDriverSnapshotTests.candidate
    members = drivers.DailyDriverSnapshotTests.members
    borrowing = drivers.DailyDriverSnapshotTests.borrowing

    def save(
        self,
        scope,
        identity,
        value,
        code="",
        start=MON,
        end=FRI,
        reviewed=True,
        reference="Synthetic daily company requirement/proof",
    ):
        store = DailyCapabilityStore(self.database)
        old = store.read(scope, identity, code, start, end)
        return store.save(
            scope,
            identity,
            code,
            value,
            DailyCapabilityInput(start, end, True, True, reference, reviewed),
            old["revision"],
            old["review_token"],
        )

    def old(self, scope, identity, value, code="", half="FullDay", start=MON, end=FRI):
        store = CapabilityEvidenceStore(self.database)
        return store.save(
            scope,
            identity,
            code,
            value,
            start_date=start,
            end_date=end,
            slot=half,
            company_confirmed=True,
            reference="Synthetic retained half-day evidence",
            expected_revision=store.read(scope, identity, code, start, end)["revision"],
        )

    def counts(self):
        return (
            adapter.generate_from_day_snapshot(self.snapshot())
            .capability_validation.checks[0]
            .counts
        )

    def test_daily_stored_policy_and_certificate_saved_report_noop_reference_history(
        self,
    ):
        p = self.prepare()
        self.save("WorkItem", self.work.id, REQ)
        self.assertEqual(self.counts()[-1].state, "Pending")
        self.save("Employee", p.id, "Verified", "SYN-Q")
        self.assertTrue(all(c.state == "Satisfied" for c in self.counts()))
        self.assertEqual(
            self.save("Employee", p.id, "Verified", "SYN-Q")["revision"], 1
        )
        self.assertEqual(
            self.save(
                "Employee",
                p.id,
                "Verified",
                "SYN-Q",
                reference="Synthetic revised proof",
            )["revision"],
            2,
        )
        self.assertEqual(
            len(DailyCapabilityStore(self.database).history("Employee", p.id, "SYN-Q")),
            2,
        )
        storage.initialize_database(self.database)
        self.assertTrue(all(c.state == "Satisfied" for c in self.counts()))

    def test_both_old_halves_never_promoted_and_legacy_proofs_retained(self):
        p = self.prepare()
        self.old("WorkItem", self.work.id, REQ)
        self.old("Employee", p.id, "Verified", "SYN-Q")
        self.assertTrue(all(c.state == "Pending" for c in self.counts()))
        self.save("WorkItem", self.work.id, REQ)
        self.assertEqual(self.counts()[-1].state, "Pending")
        self.save("Employee", p.id, "Verified", "SYN-Q")
        self.assertTrue(all(c.state == "Satisfied" for c in self.counts()))
        raw = DailyCapabilityStore(self.database).read(
            "Employee", p.id, "SYN-Q", MON, MON
        )
        self.assertEqual(len(raw["legacy_source"]["entries"]), 2)

    def test_old_negative_review_required_unknown_does_not_clear_and_reinstatement(
        self,
    ):
        p = self.prepare()
        self.save("WorkItem", self.work.id, REQ)
        self.old("Employee", p.id, "NotVerified", "SYN-Q", half="PM")
        self.assertEqual(self.counts()[-1].state, "Blocked")
        with self.assertRaises(DailyConflict):
            self.save("Employee", p.id, "Verified", "SYN-Q", reviewed=False)
        self.save("Employee", p.id, "Unknown", "SYN-Q")
        self.assertEqual(self.counts()[-1].state, "Blocked")
        self.save("Employee", p.id, "Verified", "SYN-Q")
        self.assertEqual(self.counts()[-1].state, "Satisfied")

    def test_legacy_edits_in_or_outside_horizon_expire_daily_positives_and_snapshots(
        self,
    ):
        p = self.prepare()
        self.save("WorkItem", self.work.id, REQ)
        self.save("Employee", p.id, "Verified", "SYN-Q")
        before = self.snapshot()
        self.old(
            "Employee", p.id, "Verified", "SYN-Q", start="2027-01-01", end="2027-01-01"
        )
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(self.counts()[-1].state, "Pending")
        self.old("WorkItem", self.work.id, REQ, half="AM")
        self.assertTrue(all(c.state == "Pending" for c in self.counts()))

    def test_explicit_missing_policy_tombstone_and_no_half_day_fallback(self):
        self.prepare()
        self.save("WorkItem", self.work.id, REQ)
        self.old("WorkItem", self.work.id, REQ)
        self.save("WorkItem", self.work.id, None)
        self.assertTrue(all(c.state == "Pending" for c in self.counts()))

    def test_half_day_availability_does_not_supply_daily_staffing_capacity(self):
        from rigarus_backend.availability_store import AvailabilityStore
        from rigarus_backend.availability import AvailabilityDraft

        p = self.employee()
        self.day(workers=(p.id,))
        self.save("WorkItem", self.work.id, REQ)
        self.save("Employee", p.id, "Verified", "SYN-Q")
        AvailabilityStore(self.database).save(
            p.id, AvailabilityDraft(MON, FRI, "AM", "Available"), 0
        )
        self.assertEqual(self.counts()[0].state, "Pending")
        self.available(p)
        self.assertEqual(self.counts()[0].state, "Satisfied")
        AvailabilityStore(self.database).save(
            p.id, AvailabilityDraft(MON, MON, "PM", "Unavailable"), 1
        )
        self.assertEqual(self.counts()[0].state, "Blocked")

    def test_atomic_history_and_range_failure_rollback(self):
        self.save("WorkItem", self.work.id, REQ)
        with closing(storage.connect(self.database)) as c, c:
            for sql in (
                "UPDATE DailyCapabilityChanges SET Reference='changed'",
                "DELETE FROM DailyCapabilityChanges",
                "UPDATE DailyCapabilityCells SET LocalDate='2027-01-01'",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)
            c.execute(
                "CREATE TRIGGER SyntheticDailyCapabilityFailure BEFORE UPDATE ON DailyCapabilityCells WHEN NEW.LocalDate='2026-11-25' BEGIN SELECT RAISE(ABORT,'Synthetic range failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            self.save("WorkItem", self.work.id, replace(REQ, minimum_members=2))
        self.assertEqual(self.digest(), before)

    def test_revision_range_receipt_source_edit_and_concurrent_writers(self):
        store = DailyCapabilityStore(self.database)
        before = store.read("WorkItem", self.work.id, "", MON, FRI)
        draft = DailyCapabilityInput(
            MON, FRI, True, True, "Synthetic concurrent policy"
        )

        def write():
            try:
                store.save(
                    "WorkItem", self.work.id, "", REQ, draft, 0, before["review_token"]
                )
                return "Saved"
            except DailyConflict:
                return "Stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(
                sorted(pool.map(lambda _: write(), range(2))), ["Saved", "Stale"]
            )
        before = store.read("WorkItem", self.work.id, "", MON, FRI)
        self.old("WorkItem", self.work.id, REQ)
        with self.assertRaises(DailyConflict):
            store.save(
                "WorkItem",
                self.work.id,
                "",
                REQ,
                replace(draft, legacy_reviewed=True),
                1,
                before["review_token"],
            )

    def test_strict_input_and_unknown_owner(self):
        valid = DailyCapabilityInput(
            MON, FRI, True, True, "Synthetic explicit daily proof"
        )
        for changes in (
            dict(start_date="2026-02-30"),
            dict(end_date="2028-01-01"),
            dict(company_confirmed=1),
            dict(full_day_confirmed=False),
            dict(reference=""),
            dict(reference="x" * 201),
            dict(legacy_reviewed=1),
        ):
            with self.assertRaises(ValueError):
                replace(valid, **changes)
        with self.assertRaises(LookupError):
            self.save("WorkItem", 999999, REQ)
        with self.assertRaises(ValueError):
            self.save("WorkItem", self.work.id, 1)

    def transfer(self, source_req=None):
        p, r, _, _, source = self.borrowing()
        other = ProjectStore(self.database).save(
            ProjectDraft(
                "SYN-CAP-SOURCE",
                "0109",
                "Synthetic source project",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 99)],
            )
        )
        saved = DayDraftStore(self.database).save(
            DayDraft(
                other.work_items[0].id,
                self.c2.id,
                MON,
                "Synthetic source with two actual members",
                (p.id, r.id),
            ),
            source.record_id,
            source.expected_revision,
        )
        source = replace(
            source, expected_revision=saved["revision"], employee_ids=(r.id,)
        )
        self.save("WorkItem", self.work.id, REQ)
        self.save(
            "WorkItem",
            other.work_items[0].id,
            source_req or replace(REQ, minimum_members=2, level_minimums=(0, 2, 0)),
        )
        self.save("Employee", p.id, "Verified", "SYN-Q")
        self.save("Employee", r.id, "Verified", "SYN-Q")
        snap = self.snapshot(proposed_employee_ids=(p.id, r.id))
        return p, r, snap, self.candidate(snap), source

    def test_source_minimum_shortfall_blocks_despite_driver_on_both_sides(self):
        p, r, snap, candidate, source = self.transfer()
        before = self.digest()
        result = validate_day_capability_proposal(
            snap, candidate, self.members(p), (source,)
        )
        self.assertEqual(result.driver.state, "Satisfied")
        self.assertTrue(
            all(c.state == "Satisfied" for c in result.before.checks[0].counts)
        )
        self.assertEqual(result.source_checks[0].counts[0].state, "Blocked")
        self.assertNotEqual(
            result.source_checks[0].visit.project_id, candidate.project_id
        )
        self.assertEqual(result.state, "Blocked")
        self.assertFalse(result.comparison.options)
        self.assertEqual(self.digest(), before)

    def test_source_unique_qualification_loss_blocks_with_driver_still_valid(self):
        p, r, _, _, source = self.transfer(REQ)
        self.save("Employee", r.id, "NotVerified", "SYN-Q")
        snap = self.snapshot(proposed_employee_ids=(p.id, r.id))
        result = validate_day_capability_proposal(
            snap, self.candidate(snap), self.members(p), (source,)
        )
        self.assertEqual(result.driver.state, "Satisfied")
        self.assertEqual(result.source_checks[0].counts[-1].state, "Blocked")
        self.assertEqual(result.state, "Blocked")

    def test_source_level_shortfall_blocks_even_when_member_minimum_and_driver_pass(
        self,
    ):
        p, r, snap, candidate, source = self.transfer(
            replace(REQ, level_minimums=(0, 2, 0))
        )
        result = validate_day_capability_proposal(
            snap, candidate, self.members(p), (source,)
        )
        self.assertEqual(result.driver.state, "Satisfied")
        self.assertEqual(result.source_checks[0].counts[0].state, "Satisfied")
        self.assertEqual(result.source_checks[0].counts[2].state, "Blocked")
        self.assertEqual(result.state, "Blocked")

    def test_source_missing_proof_pending_and_good_replacement_never_full_approval(
        self,
    ):
        p, r, _, _, source = self.transfer(REQ)
        self.save("Employee", r.id, "Unknown", "SYN-Q")
        snap = self.snapshot(proposed_employee_ids=(p.id, r.id))
        result = validate_day_capability_proposal(
            snap, self.candidate(snap), self.members(p), (source,)
        )
        self.assertEqual(result.state, "Pending")
        self.assertIn("Qualifications", result.pending_validators)
        self.save("Employee", r.id, "Verified", "SYN-Q")
        self.assertEqual(
            check_day_capability_proposal_freshness(self.database, result).status,
            "Stale",
        )
        snap = self.snapshot(proposed_employee_ids=(p.id, r.id))
        result = validate_day_capability_proposal(
            snap, self.candidate(snap), self.members(p), (source,)
        )
        self.assertEqual(result.state, "Satisfied")
        self.assertIn("Foreman", result.pending_validators)
        self.assertNotIn("Qualifications", result.pending_validators)
        self.assertEqual(result.validation_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)

    def test_no_override_cannot_ignore_old_half_membership_or_source_revision(self):
        p, r, snap, candidate, source = self.borrowing(True)
        self.save("WorkItem", self.work.id, REQ)
        self.save("Employee", p.id, "Verified", "SYN-Q")
        snap = self.snapshot(proposed_employee_ids=(p.id, r.id))
        result = validate_day_capability_proposal(
            snap, self.candidate(snap), self.members(p)
        )
        self.assertEqual(result.state, "Blocked")
        with self.assertRaises(ValueError):
            validate_day_capability_proposal(
                snap,
                self.candidate(snap),
                self.members(p),
                (replace(source, expected_revision=999),),
            )

    def test_fingerprint_normalized_proposal_and_daily_or_legacy_source_expiry(self):
        p, r, snap, candidate, source = self.transfer(REQ)
        result = validate_day_capability_proposal(
            snap, candidate, self.members(p), (source,)
        )
        self.assertEqual(
            result,
            validate_day_capability_proposal(
                snap, candidate, tuple(reversed(self.members(p))), (source,)
            ),
        )
        self.assertEqual(adapter.FORMAT, "rigarus-day-recommendation-input-v4")
        self.assertEqual(
            check_day_capability_proposal_freshness(self.database, result).status,
            "Current",
        )
        self.assertNotEqual(
            result.proposal_fingerprint,
            validate_day_capability_proposal(
                snap, candidate, self.members(p)
            ).proposal_fingerprint,
        )
        self.save("WorkItem", self.work.id, replace(REQ, minimum_members=2))
        self.assertEqual(
            check_day_capability_proposal_freshness(self.database, result).status,
            "Stale",
        )

    def test_coherent_pinned_view_during_policy_and_qualification_changes(self):
        p = self.prepare()
        self.save("WorkItem", self.work.id, REQ)
        self.save("Employee", p.id, "Verified", "SYN-Q")
        before = self.snapshot()
        original = adapter._read_schema

        def change(c):
            migrations = original(c)
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(
                    self.save, "WorkItem", self.work.id, replace(REQ, minimum_members=2)
                ).result(timeout=10)
                pool.submit(self.save, "Employee", p.id, "NotVerified", "SYN-Q").result(
                    timeout=10
                )
            return migrations

        with patch.object(adapter, "_read_schema", side_effect=change):
            self.assertEqual(self.snapshot(), before)
        self.assertEqual(
            validate_day_snapshot_capabilities(self.snapshot()).state, "Blocked"
        )
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, before).status, "Stale"
        )

    def test_detached_no_io_full_logical_immutability_and_read_budget(self):
        p, r, snap, candidate, source = self.transfer(REQ)
        before = self.digest()
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
            patch("time.time", side_effect=AssertionError),
        ):
            validate_day_capability_proposal(
                snap, candidate, self.members(p), (source,)
            )
        self.assertEqual(self.digest(), before)
        with patch.object(adapter, "MAX_READ_UNITS", 10):
            with self.assertRaises(adapter.SnapshotReadError):
                self.snapshot()
        with patch.object(adapter, "MAX_READ_BYTES", 1):
            with self.assertRaises(adapter.SnapshotReadError) as error:
                self.snapshot()
        self.assertEqual(error.exception.code, "READ_LIMIT_EXCEEDED")


class DailyCapabilityMigrationTests(unittest.TestCase):
    setUp = DailyCapabilityIntegrationTests.setUp
    daily = DailyCapabilityIntegrationTests.daily
    calendar = DailyCapabilityIntegrationTests.calendar
    snapshot = DailyCapabilityIntegrationTests.snapshot
    employee = DailyCapabilityIntegrationTests.employee
    day = DailyCapabilityIntegrationTests.day
    digest = DailyCapabilityIntegrationTests.digest

    def old15(self):
        p = self.employee()
        self.day(workers=(p.id,))
        with closing(storage.connect(self.database)) as c, c:
            remove_daily_capability_schema(c)

    def test_upgrade15_verified_backup_preserves_rows_history_relations_sequences_reopen(
        self,
    ):
        self.old15()
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
                (15,),
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

    def test_ddl_history_failure_and_backup_failure_roll_back_then_retry(self):
        self.old15()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticCapabilityMigrationFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDailyCapabilities' BEGIN SELECT RAISE(ABORT,'Synthetic migration failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticCapabilityMigrationFailure")
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
        self.assertEqual(len(self.snapshot().migrations), 16)

    def test_readonly15_never_initializes_or_migrates(self):
        self.old15()
        before = self.digest()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        self.assertEqual(self.digest(), before)


class DailyCapabilityLegacyGuardTests(unittest.TestCase):
    setUp = legacy.AdapterTests.setUp
    calendar = legacy.AdapterTests.calendar
    employee = legacy.AdapterTests.employee
    snapshot = legacy.AdapterTests.snapshot

    def test_old_adapter_refuses_daily_unknown_and_marks_earlier_proof_stale(self):
        from rigarus_backend.recommendation_adapter import (
            SnapshotContextError,
            check_snapshot_freshness,
        )

        p = self.employee()
        before = self.snapshot()
        store = DailyCapabilityStore(self.database)
        raw = store.read("Employee", p.id, "SYN-Q", MON, FRI)
        store.save(
            "Employee",
            p.id,
            "SYN-Q",
            "Unknown",
            DailyCapabilityInput(MON, FRI, True, True, "Synthetic explicit unknown"),
            0,
            raw["review_token"],
        )
        with self.assertRaises(SnapshotContextError):
            self.snapshot()
        self.assertEqual(
            check_snapshot_freshness(self.database, before).reason,
            "DAILY_CAPABILITY_ADAPTER_REQUIRED",
        )
