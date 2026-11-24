import sqlite3
import threading
import unittest
from contextlib import closing
from unittest.mock import patch

import test_recommendation_adapter as fixtures
from migration_fixture import remove_driver_schema
from rigarus_backend import storage, recommendation_adapter as adapter
from rigarus_backend.availability import AvailabilityDraft, EmployeeNotFound
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.driver_eligibility import DriverApprovalDraft
from rigarus_backend.driver_store import DriverApprovalStore, DriverApprovalConflict
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.assignment_store import AssignmentStore


class DriverStoreTests(unittest.TestCase):
    def test_two_writers_same_revision_only_one_commits(self):
        person, visit = self.prepare()
        barrier = threading.Barrier(2)
        outcomes = []

        def writer(state):
            try:
                barrier.wait(timeout=5)
                DriverApprovalStore(self.database).save(
                    person.id,
                    DriverApprovalDraft(
                        "2026-11-23",
                        "2026-11-23",
                        "AM",
                        state,
                        True,
                        "Synthetic concurrent",
                    ),
                    0,
                )
                outcomes.append("Saved")
            except DriverApprovalConflict:
                outcomes.append("Stale")
            except BaseException as error:
                outcomes.append(type(error).__name__)

        threads = [
            threading.Thread(target=writer, args=(state,))
            for state in ("Active", "Suspended")
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(8)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sorted(outcomes), ["Saved", "Stale"])
        self.assertEqual(len(DriverApprovalStore(self.database).history(person.id)), 1)

    def test_malformed_cell_date_context_fails_without_snapshot(self):
        person, visit = self.prepare()
        self.approve(person)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("UPDATE DriverApprovalCells SET Slot='PM'")
        with self.assertRaises(adapter.SnapshotReadError) as caught:
            self.snapshot()
        self.assertEqual(caught.exception.code, "DATABASE_INVALID")

    setUp = fixtures.AdapterTests.setUp
    calendar = fixtures.AdapterTests.calendar
    snapshot = fixtures.AdapterTests.snapshot
    plan = fixtures.AdapterTests.plan
    visit = fixtures.AdapterTests.visit
    employee = fixtures.AdapterTests.employee
    dump = fixtures.AdapterTests.dump

    def prepare(self):
        person = self.employee(home=self.tower.id)
        visit = self.visit()
        StaffingStore(self.database).save(visit.id, [person.id], visit.revision)
        AvailabilityStore(self.database).save(
            person.id,
            AvailabilityDraft("2026-11-23", "2026-11-27", "FullDay", "Available"),
            0,
        )
        return person, visit

    def approve(
        self,
        person,
        state="Active",
        slot="AM",
        reference="Synthetic company confirmation",
    ):
        store = DriverApprovalStore(self.database)
        current = store.read(person.id, "2026-11-23", "2026-11-27")
        return store.save(
            person.id,
            DriverApprovalDraft(
                "2026-11-23", "2026-11-27", slot, state, True, reference
            ),
            current["revision"],
        )

    def test_real_record_saved_read_reopen_and_company_driver_report(self):
        person, visit = self.prepare()
        self.assertEqual(self.plan().driver_validation.state, "Pending")
        self.approve(person)
        report = self.plan().driver_validation
        self.assertEqual(report.state, "Satisfied")
        self.assertEqual(report.checks[0].eligible_employee_ids, (person.id,))
        self.assertEqual(
            DriverApprovalStore(self.database).history(person.id)[0]["reference"],
            "Synthetic company confirmation",
        )
        self.assertFalse(report.applyable or report.publishable)
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute(
                    "SELECT DriverStatus,HomeCrewId FROM Employees WHERE Id=?",
                    (person.id,),
                ).fetchone(),
                ("Unverified", self.tower.id),
            )

    def test_exact_am_pm_latest_expired_and_unverified_history(self):
        person, visit = self.prepare()
        self.approve(person)
        self.approve(person, "Expired", "PM")
        self.assertEqual(self.plan().driver_validation.state, "Satisfied")
        self.approve(person, "Suspended")
        self.assertEqual(self.plan().driver_validation.state, "Blocked")
        self.approve(person, "Unverified")
        self.assertEqual(self.plan().driver_validation.state, "Pending")
        self.assertEqual(len(DriverApprovalStore(self.database).history(person.id)), 4)

    def test_revision_stale_noop_reference_change_and_no_other_rows_changed(self):
        person, visit = self.prepare()
        store = DriverApprovalStore(self.database)
        draft = DriverApprovalDraft(
            "2026-11-23", "2026-11-27", "AM", "Active", True, "Synthetic ref"
        )
        store.save(person.id, draft, 0)
        before = self.dump()
        self.assertEqual(store.save(person.id, draft, 1)["revision"], 1)
        self.assertEqual(self.dump(), before)
        with self.assertRaises(DriverApprovalConflict):
            store.save(person.id, draft, 0)
        self.assertEqual(self.dump(), before)
        self.approve(person, reference="Synthetic corrected reference")
        self.assertEqual(len(store.history(person.id)), 2)
        self.assertEqual(AssignmentStore(self.database).read(visit.id).revision, 2)

    def test_missing_record_confirmation_and_bad_revision_no_write(self):
        person, visit = self.prepare()
        before = self.dump()
        draft = DriverApprovalDraft(
            "2026-11-23", "2026-11-23", "AM", "Active", True, "Synthetic ref"
        )
        for revision in (True, -1, 1.0):
            with self.assertRaises(ValueError):
                DriverApprovalStore(self.database).save(person.id, draft, revision)
        with self.assertRaises(EmployeeNotFound):
            DriverApprovalStore(self.database).save(99999, draft, 0)
        self.assertEqual(self.dump(), before)

    def test_history_fk_and_context_protection(self):
        person, visit = self.prepare()
        self.approve(person)
        with closing(storage.connect(self.database)) as c:
            for statement in (
                "UPDATE DriverApprovalChanges SET Reference='changed'",
                "DELETE FROM DriverApprovalChanges",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(statement)
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("UPDATE DriverApprovalCells SET State='Suspended'")
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("DELETE FROM Employees WHERE Id=?", (person.id,))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_partial_save_failure_rolls_back_history_and_cells(self):
        person, visit = self.prepare()
        before = self.dump()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticDriverFailure BEFORE INSERT ON DriverApprovalCells WHEN NEW.LocalDate='2026-11-24' BEGIN SELECT RAISE(ABORT,'Synthetic rollback'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.approve(person)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticDriverFailure")
        self.assertEqual(self.dump(), before)

    def test_other_crew_driver_change_stales_snapshot_and_changes_report(self):
        person, visit = self.prepare()
        other = self.visit(crew=self.c2.id, half="PM")
        StaffingStore(self.database).save(other.id, [person.id], other.revision)
        self.approve(person, slot="FullDay")
        before = self.snapshot(crew_ids=(self.c1.id,))
        self.approve(person, "Suspended", slot="PM")
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, before).status, "Stale"
        )
        report = adapter.validate_snapshot_drivers(
            self.snapshot(crew_ids=(self.c1.id,))
        )
        self.assertEqual([c.state for c in report.checks], ["Satisfied", "Blocked"])

    def test_double_booked_driver_cancel_and_actual_membership_only(self):
        person, visit = self.prepare()
        self.approve(person)
        other = self.visit(crew=self.c2.id)
        other = StaffingStore(self.database).save(other.id, [person.id], other.revision)
        self.assertEqual(self.plan().driver_validation.state, "Blocked")
        AssignmentStore(self.database).cancel(other.id, other.revision)
        self.assertEqual(self.plan().driver_validation.state, "Satisfied")
        StaffingStore(self.database).save(
            visit.id, [], AssignmentStore(self.database).read(visit.id).revision
        )
        self.assertEqual(self.plan().driver_validation.state, "Pending")

    def test_pending_proposed_dates_even_when_saved_check_satisfied_and_pure(self):
        person, visit = self.prepare()
        self.approve(person)
        source = self.snapshot()
        before = self.dump()
        with (
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("socket.socket", side_effect=AssertionError("network")),
        ):
            r = adapter.generate_from_persisted_snapshot(source)
        self.assertEqual(r.driver_validation.state, "Satisfied")
        self.assertIn("ApprovedDriver", r.pending_validators)
        for option in r.generated.comparison.options:
            self.assertTrue(
                any(
                    e.check == "ApprovedDriver" and e.state == "Pending"
                    for e in option.explanations
                )
            )
        self.assertFalse(r.applyable or r.publishable)
        self.assertEqual(before, self.dump())

    def test_schema_ten_upgrade_rollback_retry_preserves_every_original_record(self):
        self.prepare()
        with closing(storage.connect(self.database)) as c, c:
            remove_driver_schema(c)
            original = {
                t: c.execute(f'SELECT * FROM "{t}"').fetchall()
                for (t,) in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            c.execute(
                "CREATE TRIGGER SyntheticDriverMigrationFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDriverApprovals' BEGIN SELECT RAISE(ABORT,'Synthetic migration rollback'); END"
            )
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):
            storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c, c:
            self.assertIsNone(
                c.execute(
                    "SELECT name FROM sqlite_schema WHERE name='DriverApprovalCells'"
                ).fetchone()
            )
            for t, rows in original.items():
                self.assertEqual(c.execute(f'SELECT * FROM "{t}"').fetchall(), rows)
            c.execute("DROP TRIGGER SyntheticDriverMigrationFailure")
        storage.initialize_database(self.database)
        storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c:
            for t, rows in original.items():
                if t != "__EFMigrationsHistory":
                    self.assertEqual(c.execute(f'SELECT * FROM "{t}"').fetchall(), rows)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_concurrent_wal_driver_evidence_keeps_pinned_old_then_new(self):
        person, visit = self.prepare()
        self.approve(person)
        before = self.snapshot()
        start, done = threading.Event(), threading.Event()
        errors = []

        def writer():
            try:
                if not start.wait(5):
                    raise AssertionError("read barrier")
                self.approve(person, "Suspended")
            except BaseException as error:
                errors.append(error)
            finally:
                done.set()

        thread = threading.Thread(target=writer)
        original = adapter.driver_snapshot

        def barrier(*args):
            start.set()
            if not done.wait(5):
                raise AssertionError("WAL writer blocked")
            if errors:
                raise errors[0]
            return original(*args)

        thread.start()
        try:
            with patch.object(adapter, "driver_snapshot", side_effect=barrier):
                during = self.snapshot()
        finally:
            start.set()
            thread.join(6)
        self.assertFalse(thread.is_alive())
        self.assertFalse(errors)
        self.assertEqual(during.input_fingerprint, before.input_fingerprint)
        self.assertEqual(adapter.validate_snapshot_drivers(during).state, "Satisfied")
        after = self.snapshot()
        self.assertNotEqual(after.input_fingerprint, before.input_fingerprint)
        self.assertEqual(adapter.validate_snapshot_drivers(after).state, "Blocked")
