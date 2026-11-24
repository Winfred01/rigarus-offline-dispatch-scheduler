import threading
import unittest
from contextlib import closing
from unittest.mock import patch

import test_recommendation_adapter as fixtures
from rigarus_backend import recommendation_adapter as adapter, storage
from rigarus_backend.assignment_store import AssignmentStore, read_assignment
from rigarus_backend.assignments import AssignmentDraft
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.project_store import ProjectStore
from rigarus_backend.projects import ProjectDraft, WorkItemDraft, WorkType
from rigarus_backend.recommendation_adapter import (
    SnapshotReadError,
    check_snapshot_freshness,
    generate_from_persisted_snapshot,
    validate_snapshot_personnel,
)
from rigarus_backend.staffing_persistence import append_staffing
from rigarus_backend.staffing_store import StaffingStore


class PersonnelSnapshotTests(unittest.TestCase):
    setUp = fixtures.AdapterTests.setUp
    calendar = fixtures.AdapterTests.calendar
    snapshot = fixtures.AdapterTests.snapshot
    plan = fixtures.AdapterTests.plan
    visit = fixtures.AdapterTests.visit
    employee = fixtures.AdapterTests.employee
    dump = fixtures.AdapterTests.dump

    def staff(self, visit, ids):
        current = AssignmentStore(self.database).read(visit.id)
        return StaffingStore(self.database).save(visit.id, list(ids), current.revision)

    def pair(self):
        worker = self.employee(home=self.tower.id)
        a, b = self.visit(), self.visit(crew=self.c2.id)
        return worker, self.staff(a, (worker.id,)), self.staff(b, (worker.id,))

    def test_cross_crew_outside_filter_has_complete_conflict_and_pending_proposals(
        self,
    ):
        worker, a, b = self.pair()
        before = self.dump()
        result = self.plan(crew_ids=(self.c1.id,), confirmed_remaining_half_days=1)
        self.assertEqual(len(result.snapshot.assignments), 1)
        self.assertEqual(len(result.snapshot.personnel_assignments), 2)
        report = result.personnel_validation
        self.assertEqual(report.state, "Blocked")
        self.assertEqual(report.scope, "SavedDraftAssignments")
        self.assertEqual(report.conflicts[0].employee_id, worker.id)
        self.assertEqual(
            {v.assignment_id for v in report.conflicts[0].visits}, {a.id, b.id}
        )
        self.assertEqual(
            {v.crew_id for v in report.conflicts[0].visits}, {self.c1.id, self.c2.id}
        )
        self.assertEqual(self.dump(), before)
        self.assertIn("PersonnelConflicts", result.pending_validators)
        self.assertTrue(result.generated.comparison.options)
        pending = result.generated.comparison.options[0]
        self.assertTrue(
            any(
                x.check == "PersonnelConflicts" and x.state == "Pending"
                for x in pending.explanations
            )
        )
        self.assertFalse(result.applyable or result.publishable)

    def test_cancel_clear_replace_and_latest_membership_not_history_union(self):
        worker, a, b = self.pair()
        original = self.snapshot()
        AssignmentStore(self.database).cancel(b.id, b.revision)
        clear = validate_snapshot_personnel(self.snapshot())
        self.assertEqual(clear.state, "Satisfied")
        self.assertEqual(clear.ignored_cancelled_ids, (b.id,))
        self.assertEqual(
            check_snapshot_freshness(self.database, original).status, "Stale"
        )
        self.staff(a, ())
        empty = validate_snapshot_personnel(self.snapshot())
        self.assertEqual(empty.state, "Pending")
        self.assertIn("ACTUAL_STAFFING_EMPTY", empty.checks[0].reasons)
        other = self.employee("Synthetic replacement")
        self.staff(a, (other.id,))
        current = self.snapshot()
        self.assertEqual(
            current.personnel_assignments[0].actual_employee_ids, (other.id,)
        )
        self.assertEqual(validate_snapshot_personnel(current).state, "Satisfied")

    def test_move_requires_reconfirmation_and_note_edit_keeps_conflict(self):
        worker, a, b = self.pair()
        saved = AssignmentStore(self.database).save(
            AssignmentDraft(
                self.work.id, self.c1.id, a.local_date, a.slot, "Synthetic note update"
            ),
            a.id,
            a.revision,
        )
        self.assertEqual(validate_snapshot_personnel(self.snapshot()).state, "Blocked")
        AssignmentStore(self.database).save(
            AssignmentDraft(self.work.id, self.c1.id, "2026-11-24", "PM"),
            saved.id,
            saved.revision,
        )
        report = validate_snapshot_personnel(self.snapshot())
        self.assertEqual(report.state, "Pending")
        self.assertFalse(report.conflicts)
        changed = next(c for c in report.checks if c.visit.assignment_id == a.id)
        self.assertIn("ACTUAL_STAFFING_NOT_CONFIGURED", changed.reasons)

    def test_type_inactive_home_crew_and_project_do_not_hide_actual_conflict(self):
        worker = self.employee()
        a = self.staff(self.visit(), (worker.id,))
        b = self.staff(
            self.visit(crew=self.tower.id, work_item=self.project.work_items[1].id),
            (worker.id,),
        )
        c = self.staff(self.visit(crew=self.inactive.id), (worker.id,))
        report = validate_snapshot_personnel(self.snapshot(crew_ids=(self.c1.id,)))
        self.assertEqual(
            {v.assignment_id for v in report.conflicts[0].visits}, {a.id, b.id, c.id}
        )
        self.assertEqual(len(report.conflicts[0].visits), 3)

    def test_unselected_crew_staffing_change_marks_snapshot_stale(self):
        worker = self.employee()
        other = self.employee("Synthetic external worker", home=self.tower.id)
        self.staff(self.visit(), (worker.id,))
        external = self.staff(self.visit(crew=self.c2.id), (other.id,))
        before = self.snapshot(crew_ids=(self.c1.id,))
        self.assertEqual(validate_snapshot_personnel(before).state, "Satisfied")
        self.assertIn(other.id, {e.employee_id for e in before.employees})
        self.staff(external, (worker.id,))
        self.assertEqual(
            check_snapshot_freshness(self.database, before).status, "Stale"
        )
        self.assertEqual(
            validate_snapshot_personnel(self.snapshot(crew_ids=(self.c1.id,))).state,
            "Blocked",
        )
        self.assertIn("v3", adapter.FORMAT)

    def test_roster_or_available_without_actual_membership_never_passes(self):
        worker = self.employee()
        AvailabilityStore(self.database).save(
            worker.id,
            AvailabilityDraft("2026-11-23", "2026-11-27", "FullDay", "Available"),
            0,
        )
        self.assertEqual(validate_snapshot_personnel(self.snapshot()).state, "Pending")
        a = self.visit()
        self.assertEqual(
            validate_snapshot_personnel(self.snapshot()).checks[0].reasons,
            ("ACTUAL_STAFFING_NOT_CONFIGURED",),
        )
        self.staff(a, ())
        self.assertEqual(validate_snapshot_personnel(self.snapshot()).state, "Pending")

    def test_scope_only_dates_and_cancelled_unconfigured_not_pending(self):
        worker = self.employee()
        self.staff(self.visit(), (worker.id,))
        cancelled = self.visit(crew=self.c2.id)
        AssignmentStore(self.database).cancel(cancelled.id, cancelled.revision)
        before = self.snapshot()
        self.assertEqual(validate_snapshot_personnel(before).state, "Satisfied")
        outside = self.visit(crew=self.c2.id, day="2026-11-30")
        self.staff(outside, (worker.id,))
        self.assertEqual(before.input_fingerprint, self.snapshot().input_fingerprint)

    def test_malformed_staffing_context_stops_snapshot_before_fingerprint(self):
        worker, a, b = self.pair()
        with closing(storage.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE DraftAssignments SET LocalDate='2026-11-24' WHERE Id=?", (b.id,)
            )
        with self.assertRaises(SnapshotReadError) as caught:
            self.snapshot(crew_ids=(self.c1.id,))
        self.assertEqual(caught.exception.code, "DATABASE_INVALID")

    def test_different_projects_and_workitems_share_real_employee_collision(self):
        worker = self.employee()
        a = self.staff(self.visit(), (worker.id,))
        project = ProjectStore(self.database).save(
            ProjectDraft(
                "SYN-OTHER-15",
                "00150",
                "Synthetic second site",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 2)],
            )
        )
        b = self.staff(
            self.visit(crew=self.c2.id, work_item=project.work_items[0].id),
            (worker.id,),
        )
        source = self.snapshot(crew_ids=(self.c1.id,))
        report = validate_snapshot_personnel(source)
        self.assertEqual(
            {v.assignment_id for v in report.conflicts[0].visits}, {a.id, b.id}
        )
        self.assertEqual(
            {v.project_id for v in report.conflicts[0].visits},
            {self.project.id, project.id},
        )
        self.assertEqual(source.work_item.project_id, self.project.id)

    def test_concurrent_wal_staffing_change_keeps_old_then_new_report(self):
        worker = self.employee()
        other = self.employee("Synthetic independent")
        self.staff(self.visit(), (worker.id,))
        external = self.staff(self.visit(crew=self.c2.id), (other.id,))
        before = self.snapshot(crew_ids=(self.c1.id,))
        start, done = threading.Event(), threading.Event()
        errors = []

        def writer():
            try:
                if not start.wait(5):
                    raise AssertionError("missing read barrier")
                with closing(storage.connect(self.database)) as connection, connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "UPDATE DraftAssignments SET Revision=Revision+1 WHERE Id=?",
                        (external.id,),
                    )
                    append_staffing(
                        connection,
                        read_assignment(connection, external.id),
                        (worker.id,),
                    )
            except BaseException as error:
                errors.append(error)
            finally:
                done.set()

        thread = threading.Thread(target=writer)
        thread.start()
        original = adapter._personnel_sources

        def barrier(connection, query):
            start.set()
            if not done.wait(5):
                raise AssertionError("reader blocked WAL commit")
            if errors:
                raise errors[0]
            return original(connection, query)

        try:
            with patch.object(adapter, "_personnel_sources", side_effect=barrier):
                during = self.snapshot(crew_ids=(self.c1.id,))
        finally:
            start.set()
            thread.join(6)
        self.assertFalse(errors)
        self.assertFalse(thread.is_alive())
        self.assertEqual(during.input_fingerprint, before.input_fingerprint)
        self.assertEqual(validate_snapshot_personnel(during).state, "Satisfied")
        after = self.snapshot(crew_ids=(self.c1.id,))
        self.assertNotEqual(after.input_fingerprint, before.input_fingerprint)
        self.assertEqual(validate_snapshot_personnel(after).state, "Blocked")

    def test_validation_of_detached_snapshot_is_pure_and_data_unchanged(self):
        self.pair()
        source = self.snapshot()
        before = self.dump()
        with (
            patch("sqlite3.connect", side_effect=AssertionError("extra SQL")),
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("socket.socket", side_effect=AssertionError("network")),
        ):
            report = validate_snapshot_personnel(source)
            result = generate_from_persisted_snapshot(source)
        self.assertEqual(report, result.personnel_validation)
        self.assertEqual(self.dump(), before)
        with closing(storage.connect(self.database, read_only=True)) as connection:
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
