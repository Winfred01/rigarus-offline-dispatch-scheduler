import sqlite3
import threading
import unittest
from contextlib import closing
from unittest.mock import patch

import test_recommendation_adapter as fixtures
from migration_fixture import remove_capability_schema
from rigarus_backend import storage, recommendation_adapter as adapter
from rigarus_backend import capability_store as evidence
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.capability_store import (
    CapabilityEvidenceStore,
    CapabilityEvidenceConflict,
)
from rigarus_backend.capability_validation import CapabilityRequirements
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.roster import EmployeeDraft, CrewDraft
from rigarus_backend.roster_store import EmployeeStore, CrewStore
from rigarus_backend.project_store import ProjectStore
from rigarus_backend.projects import ProjectDraft, WorkItemDraft, WorkType

DAY = "2026-11-23"


class CapabilityStoreTests(unittest.TestCase):
    def test_aggregate_row_budget_stops_before_reading_more_qualification_owners(self):
        person, _ = self.prepare()
        self.record("Employee", person.id, "AAA-SYN", "Verified")
        self.record("Employee", person.id, "ZZZ-SYN", "Verified")
        original = evidence.snapshot
        observed = []

        def counted(connection, scope, *args):
            if scope == "Employee":
                observed.append(args[1])
            return original(connection, scope, *args)

        with (
            patch.object(evidence, "snapshot", side_effect=counted),
            # This case isolates the aggregate evidence budget. Schema14 has
            # more than25 tables; schema workload limits have separate tests.
            patch.object(adapter, "_read_schema", return_value=adapter.CURRENT_HISTORY),
            patch.object(adapter, "MAX_OBSERVED_ROWS", 25),
        ):
            with self.assertRaises(adapter.SnapshotReadError) as caught:
                self.snapshot()
        self.assertEqual(caught.exception.code, "READ_LIMIT_EXCEEDED")
        self.assertEqual(observed, ["AAA-SYN"])

    setUp = fixtures.AdapterTests.setUp
    calendar = fixtures.AdapterTests.calendar
    snapshot = fixtures.AdapterTests.snapshot
    plan = fixtures.AdapterTests.plan
    visit = fixtures.AdapterTests.visit
    employee = fixtures.AdapterTests.employee
    dump = fixtures.AdapterTests.dump

    def record(
        self,
        scope,
        subject,
        code,
        value,
        *,
        slot="AM",
        reference="Synthetic company evidence",
        day=DAY,
        end="2026-11-27",
    ):
        store = CapabilityEvidenceStore(self.database)
        current = store.read(scope, subject, code, day, end)
        return store.save(
            scope,
            subject,
            code,
            value,
            start_date=day,
            end_date=end,
            slot=slot,
            company_confirmed=True,
            reference=reference,
            expected_revision=current["revision"],
        )

    def policy(
        self,
        item=None,
        minimum=1,
        qualifications=(("SYN-Q", 1),),
        mode="Exact",
        levels=(0, 1, 0),
    ):
        return self.record(
            "WorkItem",
            item or self.work.id,
            "",
            CapabilityRequirements(minimum, levels, mode, qualifications),
        )

    def prepare(self, *, policy=True, proof=True):
        person = self.employee(home=self.tower.id)
        visit = self.visit()
        StaffingStore(self.database).save(visit.id, [person.id], visit.revision)
        AvailabilityStore(self.database).save(
            person.id, AvailabilityDraft(DAY, "2026-11-27", "FullDay", "Available"), 0
        )
        if policy:
            self.policy()
        if proof:
            self.record("Employee", person.id, "SYN-Q", "Verified")
        return person, visit

    def checks(self):
        return {c.check: c for c in self.plan().capability_validation.checks[0].counts}

    def test_real_policy_and_qualification_reload_separate_from_level_driver_foreman(
        self,
    ):
        person, visit = self.prepare()
        self.assertTrue(all(c.state == "Satisfied" for c in self.checks().values()))
        report = self.plan()
        self.assertEqual(report.capability_validation.state, "Pending")
        self.assertEqual(
            report.capability_validation.checks[0].foreman_state, "Pending"
        )
        self.assertEqual(report.driver_validation.state, "Pending")
        self.assertFalse(report.applyable or report.publishable)
        self.assertEqual(
            CapabilityEvidenceStore(self.database).read(
                "Employee", person.id, "SYN-Q", DAY, DAY
            )["entries"][0]["value"],
            "Verified",
        )

    def test_absent_policy_and_missing_unknown_notverified_certificates(self):
        person, visit = self.prepare(policy=False, proof=False)
        self.assertTrue(
            all(
                c.required is None and c.state == "Pending"
                for c in self.checks().values()
            )
        )
        self.policy()
        self.assertEqual(self.checks()["Qualification:SYN-Q"].state, "Pending")
        self.record("Employee", person.id, "SYN-Q", "NotVerified")
        self.assertEqual(self.checks()["Qualification:SYN-Q"].state, "Blocked")
        self.record("Employee", person.id, "SYN-Q", "Unknown")
        self.assertEqual(self.checks()["Qualification:SYN-Q"].state, "Pending")
        self.assertEqual(
            len(
                CapabilityEvidenceStore(self.database).history(
                    "Employee", person.id, "SYN-Q"
                )
            ),
            2,
        )

    def test_requirement_and_qualification_changes_stale_not_history_union(self):
        person, visit = self.prepare()
        before = self.snapshot()
        self.policy(minimum=2)
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(self.checks()["MinimumStaffing"].state, "Blocked")
        self.record("Employee", person.id, "SYN-Q", "NotVerified")
        self.assertEqual(self.checks()["Qualification:SYN-Q"].state, "Blocked")
        self.assertEqual(
            len(
                CapabilityEvidenceStore(self.database).history(
                    "WorkItem", self.work.id, ""
                )
            ),
            2,
        )

    def test_native_noop_stale_reference_revision_and_immutable_history(self):
        person, visit = self.prepare()
        store = CapabilityEvidenceStore(self.database)
        before = self.dump()
        self.policy()
        self.assertEqual(before, self.dump())
        value = CapabilityRequirements(1, (0, 1, 0), "Exact", (("SYN-Q", 1),))
        with self.assertRaises(CapabilityEvidenceConflict):
            store.save(
                "WorkItem",
                self.work.id,
                "",
                value,
                start_date=DAY,
                end_date=DAY,
                slot="AM",
                company_confirmed=True,
                reference="Synthetic company evidence",
                expected_revision=0,
            )
        self.assertEqual(before, self.dump())
        self.record(
            "WorkItem", self.work.id, "", value, reference="Synthetic revised reference"
        )
        self.assertEqual(len(store.history("WorkItem", self.work.id, "")), 2)
        with closing(storage.connect(self.database)) as c:
            for table in ("CapabilityEvidenceOwners", "CapabilityEvidenceChanges"):
                for statement in (f"UPDATE {table} SET Id=Id", f"DELETE FROM {table}"):
                    with self.assertRaises(sqlite3.IntegrityError):
                        c.execute(statement)

    def test_invalid_input_subject_and_confirmation_no_write(self):
        person, visit = self.prepare()
        before = self.dump()
        store = CapabilityEvidenceStore(self.database)
        for changes in (
            dict(company_confirmed=False),
            dict(expected_revision=True),
            dict(slot="night"),
            dict(reference=""),
            dict(end_date="2028-12-31"),
        ):
            args = dict(
                start_date=DAY,
                end_date=DAY,
                slot="AM",
                company_confirmed=True,
                reference="Synthetic test",
                expected_revision=1,
            )
            args.update(changes)
            with self.assertRaises(ValueError):
                store.save("Employee", person.id, "SYN-Q", "Verified", **args)
        with self.assertRaises(LookupError):
            store.read("WorkItem", 99999, "", DAY, DAY)
        with self.assertRaises(ValueError):
            self.record("Employee", person.id, "bad code", "Verified")
        self.assertEqual(before, self.dump())

    def test_partial_range_write_rolls_back_owner_history_and_cells(self):
        person, visit = self.prepare(policy=False, proof=False)
        before = self.dump()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticCapabilityFailure BEFORE INSERT ON CapabilityEvidenceCells WHEN NEW.LocalDate='2026-11-24' BEGIN SELECT RAISE(ABORT,'Synthetic rollback'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.policy()
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticCapabilityFailure")
        self.assertEqual(before, self.dump())

    def test_xor_identity_and_cross_owner_cell_fk_are_enforced(self):
        person, visit = self.prepare()
        with closing(storage.connect(self.database)) as c, c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(
                    "INSERT INTO CapabilityEvidenceOwners(WorkItemId,EmployeeId,Code) VALUES (?,?,?)",
                    (self.work.id, person.id, "SYN-X"),
                )
            owners = c.execute(
                "SELECT Id FROM CapabilityEvidenceOwners ORDER BY Id"
            ).fetchall()
            foreign_change = c.execute(
                "SELECT Id FROM CapabilityEvidenceChanges WHERE OwnerId=?",
                (owners[1][0],),
            ).fetchone()[0]
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(
                    "UPDATE CapabilityEvidenceCells SET ChangeId=? WHERE OwnerId=?",
                    (foreign_change, owners[0][0]),
                )
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_malformed_payload_or_context_fails_without_fingerprint(self):
        person, visit = self.prepare()
        for payload, slot in (
            ('{"version":1,"version":1,"state":"Verified"}', "AM"),
            ('{"version":1,"state":"Verified"}', "PM"),
        ):
            with closing(storage.connect(self.database)) as c, c:
                owner = c.execute(
                    "SELECT Id FROM CapabilityEvidenceOwners WHERE EmployeeId=?",
                    (person.id,),
                ).fetchone()[0]
                rev = (
                    c.execute(
                        "SELECT max(Revision) FROM CapabilityEvidenceChanges WHERE OwnerId=?",
                        (owner,),
                    ).fetchone()[0]
                    + 1
                )
                change = c.execute(
                    "INSERT INTO CapabilityEvidenceChanges(OwnerId,Revision,StartDate,EndDate,Slot,Payload,CompanyConfirmed,Reference,RecordedAt) VALUES (?,?,?,?,?,?,1,?,?)",
                    (
                        owner,
                        rev,
                        DAY,
                        DAY,
                        slot,
                        payload,
                        "Synthetic malformed fixture",
                        "Synthetic timestamp",
                    ),
                ).lastrowid
                c.execute(
                    "UPDATE CapabilityEvidenceCells SET ChangeId=? WHERE OwnerId=? AND LocalDate=? AND Slot='AM'",
                    (change, owner, DAY),
                )
            with self.assertRaises(adapter.SnapshotReadError) as caught:
                self.snapshot()
            self.assertEqual(caught.exception.code, "DATABASE_INVALID")

    def test_exact_date_half_and_explicit_policy_clear_to_unknown(self):
        person, visit = self.prepare()
        store = CapabilityEvidenceStore(self.database)
        self.assertEqual(
            store.read("WorkItem", self.work.id, "", DAY, DAY)["entries"][0]["slot"],
            "AM",
        )
        self.assertEqual(
            store.read("Employee", person.id, "SYN-Q", "2026-12-01", "2026-12-01")[
                "entries"
            ],
            [],
        )
        self.record("Employee", person.id, "SYN-Q", "NotVerified", slot="PM")
        self.assertEqual(self.checks()["Qualification:SYN-Q"].state, "Satisfied")

    def test_other_project_unselected_crew_policy_and_master_changes_are_observed(self):
        person, visit = self.prepare()
        project = ProjectStore(self.database).save(
            ProjectDraft(
                "SYN-CAP-OTHER",
                "00250",
                "Synthetic capability site",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 2)],
            )
        )
        other_person = self.employee(
            "Synthetic external capability worker", home=self.c2.id
        )
        other = self.visit(crew=self.c2.id, work_item=project.work_items[0].id)
        StaffingStore(self.database).save(other.id, [other_person.id], other.revision)
        AvailabilityStore(self.database).save(
            other_person.id, AvailabilityDraft(DAY, DAY, "AM", "Available"), 0
        )
        self.policy(item=project.work_items[0].id, qualifications=())
        old = self.snapshot(crew_ids=(self.c1.id,))
        self.policy(item=project.work_items[0].id, minimum=3, qualifications=())
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, old).status, "Stale"
        )
        report = adapter.validate_snapshot_capabilities(
            self.snapshot(crew_ids=(self.c1.id,))
        )
        self.assertEqual(
            {c.visit.project_id for c in report.checks}, {self.project.id, project.id}
        )
        self.assertEqual(report.checks[1].counts[0].state, "Blocked")
        before = self.snapshot(crew_ids=(self.c1.id,))
        CrewStore(self.database).save(
            CrewDraft(self.c2.name, "Tower", False), self.c2.id
        )
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(
            adapter.validate_snapshot_capabilities(
                self.snapshot(crew_ids=(self.c1.id,))
            )
            .checks[1]
            .crew_reason,
            "CREW_INACTIVE",
        )

    def test_employee_level_changes_invalidate_without_certification_equivalence(self):
        person, visit = self.prepare()
        before = self.snapshot()
        EmployeeStore(self.database).save(
            EmployeeDraft(person.name, person.home_crew_id, 1, True, True), person.id
        )
        self.assertEqual(
            adapter.check_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(self.checks()["SkillsLevel2"].state, "Blocked")
        self.assertEqual(self.checks()["Qualification:SYN-Q"].state, "Satisfied")

    def test_two_writers_same_owner_revision_one_wins(self):
        person, visit = self.prepare(policy=False, proof=False)
        barrier = threading.Barrier(2)
        results = []

        def writer(state):
            try:
                barrier.wait(timeout=5)
                CapabilityEvidenceStore(self.database).save(
                    "Employee",
                    person.id,
                    "SYN-Q",
                    state,
                    start_date=DAY,
                    end_date=DAY,
                    slot="AM",
                    company_confirmed=True,
                    reference="Synthetic concurrent",
                    expected_revision=0,
                )
                results.append("Saved")
            except CapabilityEvidenceConflict:
                results.append("Stale")
            except BaseException as error:
                results.append(type(error).__name__)

        threads = [
            threading.Thread(target=writer, args=(state,))
            for state in ("Verified", "NotVerified")
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(8)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sorted(results), ["Saved", "Stale"])

    def test_pure_detached_report_keeps_generated_checks_pending_and_logical_db_equal(
        self,
    ):
        self.prepare()
        source = self.snapshot()
        before = self.dump()
        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("socket.socket", side_effect=AssertionError("network")),
        ):
            report = adapter.generate_from_persisted_snapshot(source)
        self.assertEqual(before, self.dump())
        self.assertTrue(report.generated.comparison.options)
        for option in report.generated.comparison.options:
            for check in ("MinimumStaffing", "Skills", "Qualifications", "Foreman"):
                self.assertIn(check, report.pending_validators)
                self.assertTrue(
                    any(
                        e.check == check and e.state == "Pending"
                        for e in option.explanations
                    )
                )
        self.assertFalse(report.applyable or report.publishable)

    def test_schema_eleven_upgrade_rollback_retry_original_rows_and_readonly_rejection(
        self,
    ):
        self.prepare(policy=False, proof=False)
        with closing(storage.connect(self.database)) as c, c:
            remove_capability_schema(c)
            original = {
                t: c.execute(f'SELECT * FROM "{t}"').fetchall()
                for (t,) in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            c.execute(
                "CREATE TRIGGER SyntheticCapabilityMigrationFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddCapabilityEvidence' BEGIN SELECT RAISE(ABORT,'Synthetic migration rollback'); END"
            )
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):
            storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c, c:
            self.assertIsNone(
                c.execute(
                    "SELECT name FROM sqlite_schema WHERE name='CapabilityEvidenceOwners'"
                ).fetchone()
            )
            for t, rows in original.items():
                self.assertEqual(c.execute(f'SELECT * FROM "{t}"').fetchall(), rows)
            c.execute("DROP TRIGGER SyntheticCapabilityMigrationFailure")
        storage.initialize_database(self.database)
        storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c:
            for t, rows in original.items():
                if t != "__EFMigrationsHistory":
                    self.assertEqual(c.execute(f'SELECT * FROM "{t}"').fetchall(), rows)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_wal_writer_preserves_complete_old_then_new_qualification_view(self):
        person, visit = self.prepare()
        before = self.snapshot()
        start, done = threading.Event(), threading.Event()
        errors = []

        def writer():
            try:
                if not start.wait(5):
                    raise AssertionError("read barrier")
                self.record("Employee", person.id, "SYN-Q", "NotVerified")
            except BaseException as error:
                errors.append(error)
            finally:
                done.set()

        thread = threading.Thread(target=writer)
        original = adapter.capability_snapshot

        def barrier(*args):
            start.set()
            if not done.wait(5):
                raise AssertionError("WAL writer blocked")
            if errors:
                raise errors[0]
            return original(*args)

        thread.start()
        try:
            with patch.object(adapter, "capability_snapshot", side_effect=barrier):
                during = self.snapshot()
        finally:
            start.set()
            thread.join(6)
        self.assertFalse(thread.is_alive())
        self.assertFalse(errors)
        self.assertEqual(during.input_fingerprint, before.input_fingerprint)
        self.assertTrue(
            all(
                c.state == "Satisfied"
                for c in adapter.validate_snapshot_capabilities(during).checks[0].counts
            )
        )
        after = self.snapshot()
        self.assertNotEqual(after.input_fingerprint, before.input_fingerprint)
        self.assertEqual(
            adapter.validate_snapshot_capabilities(after).checks[0].counts[-1].state,
            "Blocked",
        )
