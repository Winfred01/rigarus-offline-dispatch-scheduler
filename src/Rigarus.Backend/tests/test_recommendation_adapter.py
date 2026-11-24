import os
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
from unittest.mock import patch

from rigarus_backend import recommendation_adapter as adapter, storage
from rigarus_backend.assignment_store import AssignmentStore
from rigarus_backend.assignments import AssignmentDraft
from rigarus_backend.availability import AvailabilityDraft
from rigarus_backend.availability_store import AvailabilityStore
from rigarus_backend.foreman_store import ForemanStore
from rigarus_backend.project_store import ProjectStore
from rigarus_backend.projects import ProjectDraft, WorkItemDraft, WorkType
from rigarus_backend.recommendation_adapter import (
    RecommendationQuery,
    SnapshotContextError,
    SnapshotNotFound,
    SnapshotReadError,
    build_recommendation_snapshot,
    check_snapshot_freshness,
    generate_from_persisted_snapshot,
    generation_requests,
)
from rigarus_backend.recommendation_generator import DateSlot
from rigarus_backend.roster import CrewDraft, EmployeeDraft
from rigarus_backend.roster_store import CrewStore, EmployeeStore
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.working_calendar_store import WorkingCalendarStore


class AdapterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "SYN # snapshot.db"
        storage.initialize_database(self.database)
        self.project = ProjectStore(self.database).save(
            ProjectDraft(
                "SYN-ADAPTER-28",
                "00028",
                "Synthetic adapter site",
                [
                    WorkItemDraft(None, WorkType.CIVIL, 1, 99),
                    WorkItemDraft(None, WorkType.TOWER, 1, 4),
                ],
            )
        )
        self.work = self.project.work_items[0]
        roster = CrewStore(self.database)
        self.c1 = roster.save(CrewDraft("Synthetic C1", "Civil"))
        self.c2 = roster.save(CrewDraft("Synthetic C2", "Civil"))
        self.tower = roster.save(CrewDraft("Synthetic T1", "Tower"))
        self.inactive = roster.save(CrewDraft("Synthetic inactive", "Civil", False))
        self.query = RecommendationQuery(
            self.work.id,
            (self.c1.id, self.c2.id),
            4,
            True,
            "2026-11-23",
            "2026-11-27",
            self.project.id,
        )
        self.calendar("Project", self.project.id, "2026-11-23", "2026-11-27")
        self.gapped = (
            ("2026-11-23", "AM"),
            ("2026-11-25", "PM"),
            ("2026-11-26", "AM"),
            ("2026-11-27", "PM"),
        )
        for day, half in self.gapped:
            self.calendar("Crew", self.c1.id, day, day, half)
        self.calendar(
            "Crew", self.c1.id, "2026-11-24", "2026-11-24", state="NotWorking"
        )
        self.calendar("Crew", self.c2.id, "2026-11-24", "2026-11-25")

    def calendar(self, scope, entity_id, start, end, half="FullDay", state="Working"):
        store = WorkingCalendarStore(self.database)
        revision = store.read(scope, entity_id, start, end)["revision"]
        return store.save(scope, entity_id, start, end, half, state, revision)

    def snapshot(self, **changes):
        return build_recommendation_snapshot(
            self.database, replace(self.query, **changes)
        )

    def plan(self, **changes):
        return generate_from_persisted_snapshot(self.snapshot(**changes))

    def visit(self, crew=None, day="2026-11-23", half="AM", work_item=None):
        return AssignmentStore(self.database).save(
            AssignmentDraft(
                work_item or self.work.id,
                crew or self.c1.id,
                day,
                half,
                "Synthetic preserved visit",
            )
        )

    def employee(self, name="Synthetic worker", home=None):
        return EmployeeStore(self.database).save(
            EmployeeDraft(name, home or self.c1.id, 2, True)
        )

    def dump(self):
        with closing(storage.connect(self.database, read_only=True)) as connection:
            return tuple(connection.iterdump())

    def test_real_fk_sources_and_compatible_requests(self):
        source = self.snapshot()
        self.assertEqual(source.work_item.project_id, self.project.id)
        self.assertEqual(source.work_item.job_number, "SYN-ADAPTER-28")
        self.assertEqual(source.work_item.work_type, "Civil")
        self.assertEqual(source.work_item.estimated_half_days, 99)
        self.assertEqual(source.migrations, adapter.CURRENT_HISTORY)
        self.assertEqual(source.project_calendar.revision, 1)
        requests = generation_requests(source)
        self.assertEqual([x.option_id for x in requests], [self.c1.id, self.c2.id])
        for request in requests:
            self.assertEqual(request.confirmed_remaining_half_days, 4)
            self.assertEqual(request.project_calendar.entity_id, self.project.id)
            self.assertEqual(
                request.occupancy.start_date, self.query.earliest_start_date
            )
            self.assertEqual(request.occupancy.occupied, ())
            self.assertEqual(request.slot_evidence, ())

    def test_persisted_dual_sort_demo_and_gapped_calendar_reasons(self):
        finish = self.plan()
        start = self.plan(
            order="EarliestStart", crew_ids=tuple(reversed(self.query.crew_ids))
        )
        self.assertEqual(
            [x.option.crew_id for x in finish.generated.comparison.options],
            [self.c2.id, self.c1.id],
        )
        self.assertEqual(
            [x.option.crew_id for x in start.generated.comparison.options],
            [self.c1.id, self.c2.id],
        )
        first, second = finish.generated.candidates
        self.assertEqual(tuple(x.key for x in first.slots), self.gapped)
        self.assertEqual(
            (first.proposed_start, first.proposed_finish),
            (DateSlot("2026-11-23", "AM"), DateSlot("2026-11-27", "PM")),
        )
        self.assertEqual(
            (second.proposed_start, second.proposed_finish),
            (DateSlot("2026-11-24", "AM"), DateSlot("2026-11-25", "PM")),
        )
        self.assertTrue(
            any("CREW_CALENDAR_NOTWORKING" in x.reasons for x in first.skipped)
        )
        self.assertIn("ApprovedDriver", finish.pending_validators)
        self.assertEqual(first.generated_half_days, 4)

    def test_wrong_parent_missing_workitem_or_crew_never_fabricated(self):
        with self.assertRaises(SnapshotContextError):
            self.snapshot(expected_project_id=999)
        with self.assertRaises(SnapshotNotFound):
            self.snapshot(work_item_id=999)
        with self.assertRaises(SnapshotNotFound):
            self.snapshot(crew_ids=(999,))
        self.assertEqual(
            self.snapshot(expected_project_id=None).work_item.project_id,
            self.project.id,
        )

    def test_inactive_type_mismatch_and_unmapped_work_type_need_review(self):
        result = self.plan(crew_ids=(self.c1.id, self.tower.id, self.inactive.id))
        self.assertEqual(len(result.generated.candidates), 1)
        reasons = {x.crew_id: x.reasons for x in result.crew_reviews}
        self.assertEqual(reasons[self.tower.id], ("CREW_TYPE_MISMATCH",))
        self.assertEqual(reasons[self.inactive.id], ("CREW_INACTIVE",))
        for review in result.crew_reviews:
            self.assertEqual(review.status, "Needs Review")
            self.assertFalse(review.applyable or review.publishable)
        with closing(storage.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE WorkItems SET Type='Small' WHERE Id=?", (self.work.id,)
            )
        unmapped = self.plan()
        self.assertEqual(unmapped.generated.comparison.options, ())
        self.assertTrue(
            all("WORK_TYPE_MAPPING_PENDING" in x.reasons for x in unmapped.crew_reviews)
        )

    def test_civil_and_tower_keep_independent_workitems_same_parent(self):
        tower_work = self.project.work_items[1]
        self.calendar("Crew", self.tower.id, "2026-11-23", "2026-11-27")
        result = self.plan(work_item_id=tower_work.id, crew_ids=(self.tower.id,))
        candidate = result.generated.candidates[0]
        self.assertEqual(
            (candidate.work_item_id, candidate.project_id),
            (tower_work.id, self.project.id),
        )
        self.assertNotEqual(candidate.work_item_id, self.work.id)

    def test_multi_crew_requirement_never_reduced(self):
        with closing(storage.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE WorkItems SET RequiredCrewCount=2 WHERE Id=?", (self.work.id,)
            )
        result = self.plan()
        self.assertEqual(result.generated.comparison.options, ())
        for candidate in result.generated.candidates:
            self.assertIn("MULTI_CREW_REQUIRES_REVIEW", candidate.review_reasons)
            self.assertEqual(candidate.generated_half_days, 0)
            self.assertIsNone(candidate.proposed_finish)

    def test_calendar_unknown_closure_conflict_and_exhaustion(self):
        self.calendar(
            "Project", self.project.id, "2026-11-23", "2026-11-23", "AM", "NotWorking"
        )
        partial = self.plan(crew_ids=(self.c1.id,)).generated.candidates[0]
        self.assertEqual(
            (partial.generated_half_days, partial.unfilled_half_days), (3, 1)
        )
        self.assertIsNone(partial.proposed_finish)
        self.assertTrue(any("CALENDAR_CONFLICT" in x.reasons for x in partial.skipped))
        self.calendar(
            "Project", self.project.id, "2026-11-23", "2026-11-27", state="Unknown"
        )
        empty = self.plan().generated.candidates
        self.assertTrue(
            all(x.generated_half_days == 0 and x.proposed_finish is None for x in empty)
        )
        self.assertTrue(all(x.calendar_unknowns == 10 for x in empty))

    def test_occupancy_includes_same_work_repeated_visits_and_cancellation_releases(
        self,
    ):
        first = self.visit()
        second = self.visit(day="2026-11-25", half="PM")
        source = self.snapshot(crew_ids=(self.c1.id,))
        self.assertEqual(
            {x.assignment_id for x in source.assignments}, {first.id, second.id}
        )
        candidate = generate_from_persisted_snapshot(source).generated.candidates[0]
        self.assertEqual(
            (candidate.generated_half_days, candidate.unfilled_half_days), (2, 2)
        )
        self.assertIsNone(candidate.proposed_finish)
        self.assertEqual(candidate.confirmed_remaining_half_days, 4)
        AssignmentStore(self.database).cancel(first.id, first.revision)
        current = self.snapshot(crew_ids=(self.c1.id,))
        self.assertEqual(
            next(x for x in current.assignments if x.assignment_id == first.id).status,
            "Cancelled",
        )
        self.assertEqual(
            generation_requests(current)[0].occupancy.occupied,
            (DateSlot(second.local_date, second.slot),),
        )
        self.assertEqual(
            generate_from_persisted_snapshot(current)
            .generated.candidates[0]
            .generated_half_days,
            3,
        )

    def test_other_crew_and_other_am_pm_do_not_block_selected_slot(self):
        self.visit(crew=self.c2.id)
        self.visit(half="PM", work_item=self.project.work_items[1].id)
        candidate = self.plan(
            crew_ids=(self.c1.id,), confirmed_remaining_half_days=1
        ).generated.candidates[0]
        self.assertEqual(candidate.proposed_finish, DateSlot("2026-11-23", "AM"))

    def test_missing_remaining_or_confirmation_never_uses_estimate_or_visits(self):
        self.visit()
        for count, confirmed in ((None, True), (4, False)):
            result = self.plan(
                confirmed_remaining_half_days=count,
                remaining_confirmed_by_operator=confirmed,
            )
            self.assertEqual(result.generated.comparison.options, ())
            self.assertTrue(
                all(
                    x.status == "Needs Review" and not x.scanned
                    for x in result.generated.candidates
                )
            )

    def test_employee_availability_borrowing_and_foreman_are_observations_only(self):
        borrowed = self.employee(home=self.tower.id)
        home = self.employee("Synthetic home available")
        visit = self.visit()
        StaffingStore(self.database).save(visit.id, [borrowed.id], visit.revision)
        AvailabilityStore(self.database).save(
            borrowed.id,
            AvailabilityDraft("2026-11-23", "2026-11-23", "AM", "Unavailable"),
            0,
        )
        AvailabilityStore(self.database).save(
            home.id,
            AvailabilityDraft("2026-11-23", "2026-11-27", "FullDay", "Available"),
            0,
        )
        foreman = ForemanStore(self.database).save(self.c1.id, borrowed.id, 0)
        result = self.plan(crew_ids=(self.c1.id,))
        employees = {x.employee_id: x for x in result.snapshot.employees}
        assignment = result.snapshot.assignments[0]
        self.assertEqual(assignment.actual_employee_ids, (borrowed.id,))
        self.assertNotIn(home.id, assignment.actual_employee_ids)
        self.assertEqual(employees[borrowed.id].home_crew_id, self.tower.id)
        self.assertEqual(employees[borrowed.id].availability[0].state, "Unavailable")
        self.assertEqual(employees[borrowed.id].driver_status, "Unverified")
        self.assertEqual(result.snapshot.crews[0].foreman.change_id, foreman.revision)
        self.assertEqual(result.snapshot.crews[0].foreman.employee_id, borrowed.id)
        self.assertTrue(assignment.staffing_configured)
        self.assertGreater(assignment.staffing_change_id, 0)
        pending = {x.check for x in result.generated.candidates[0].missing_evidence}
        for name in (
            "EmployeeAvailability",
            "ApprovedDriver",
            "Skills",
            "Qualifications",
            "MinimumStaffing",
            "Foreman",
            "RigAvailability",
            "RigConflicts",
        ):
            self.assertIn(name, pending)
        self.assertEqual(
            EmployeeStore(self.database).search("Synthetic worker")[0].home_crew_id,
            self.tower.id,
        )

    def test_weekends_never_derive_consent_from_calendars_or_available_employees(self):
        self.calendar("Crew", self.c1.id, "2026-11-28", "2026-11-30")
        self.calendar("Project", self.project.id, "2026-11-28", "2026-11-30")
        worker = self.employee()
        AvailabilityStore(self.database).save(
            worker.id,
            AvailabilityDraft("2026-11-28", "2026-11-30", "FullDay", "Available"),
            0,
        )
        candidate = self.plan(
            crew_ids=(self.c1.id,),
            earliest_start_date="2026-11-28",
            horizon_end_date="2026-11-30",
            confirmed_remaining_half_days=1,
        ).generated.candidates[0]
        self.assertEqual(candidate.proposed_finish, DateSlot("2026-11-30", "AM"))
        self.assertEqual(len(candidate.skipped), 4)
        self.assertTrue(
            all("WEEKEND_CONSENT_NOT_CONFIRMED" in x.reasons for x in candidate.skipped)
        )

    def test_fingerprint_repeat_order_and_frozen_snapshots(self):
        first = self.snapshot()
        self.assertEqual(
            first, self.snapshot(crew_ids=tuple(reversed(self.query.crew_ids)))
        )
        self.assertEqual(
            check_snapshot_freshness(self.database, first).status, "Current"
        )
        self.assertEqual(len(first.input_fingerprint), 64)
        self.assertNotIn(str(self.database), first.source_id)
        with self.assertRaises(FrozenInstanceError):
            first.work_item.project_id = 9
        with (
            patch(
                "sqlite3.connect",
                side_effect=AssertionError("SQL during pure conversion"),
            ),
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("socket.socket", side_effect=AssertionError("network")),
        ):
            before = asdict(first)
            result = generate_from_persisted_snapshot(first)
            self.assertEqual(asdict(first), before)
            self.assertFalse(result.applyable or result.publishable)
        for record in (
            result,
            result.generated,
            result.generated.comparison,
            *result.generated.candidates,
        ):
            with self.assertRaises(TypeError):
                replace(record, applyable=True)

    def test_unversioned_master_fields_and_each_observed_revision_change_fingerprint(
        self,
    ):
        baseline = self.snapshot()
        mutations = [
            lambda: ProjectStore(self.database).save(
                ProjectDraft(
                    "SYN-ADAPTER-RENAMED", "00028", "Synthetic adapter site", []
                ),
                self.project.id,
            ),
            lambda: CrewStore(self.database).save(
                CrewDraft("Synthetic renamed", "Civil"), self.c1.id
            ),
            lambda: self.calendar("Crew", self.c1.id, "2026-11-23", "2026-11-23", "PM"),
            lambda: self.calendar(
                "Project",
                self.project.id,
                "2026-11-23",
                "2026-11-23",
                "PM",
                "NotWorking",
            ),
            lambda: self.visit(day="2026-11-24"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                mutate()
                current = self.snapshot()
                self.assertNotEqual(
                    baseline.input_fingerprint, current.input_fingerprint
                )
                self.assertEqual(
                    check_snapshot_freshness(self.database, baseline).status, "Stale"
                )
                baseline = current
        worker = self.employee()
        baseline = self.snapshot()
        visit = AssignmentStore(self.database).list()[0]
        StaffingStore(self.database).save(visit.id, [worker.id], visit.revision)
        self.assertNotEqual(
            baseline.input_fingerprint, self.snapshot().input_fingerprint
        )
        baseline = self.snapshot()
        AvailabilityStore(self.database).save(
            worker.id,
            AvailabilityDraft("2026-11-23", "2026-11-23", "AM", "Unavailable"),
            0,
        )
        self.assertNotEqual(
            baseline.input_fingerprint, self.snapshot().input_fingerprint
        )
        baseline = self.snapshot()
        ForemanStore(self.database).save(self.c1.id, worker.id, 0)
        self.assertNotEqual(
            baseline.input_fingerprint, self.snapshot().input_fingerprint
        )
        baseline = self.snapshot()
        EmployeeStore(self.database).save(
            EmployeeDraft(worker.name, worker.home_crew_id, 3, True), worker.id
        )
        self.assertNotEqual(
            baseline.input_fingerprint, self.snapshot().input_fingerprint
        )

    def test_query_confirmation_duration_sort_bounds_and_limit_are_fingerprinted(self):
        baseline = self.snapshot().input_fingerprint
        for changes in (
            {"remaining_confirmed_by_operator": False},
            {"confirmed_remaining_half_days": 3},
            {"order": "EarliestStart"},
            {"max_options": 1},
            {"earliest_start_date": "2026-11-24"},
            {"horizon_end_date": "2026-11-26"},
        ):
            self.assertNotEqual(baseline, self.snapshot(**changes).input_fingerprint)

    def test_scoped_fingerprint_ignores_other_projects_and_physical_checkpoint(self):
        baseline = self.snapshot()
        ProjectStore(self.database).save(
            ProjectDraft("SYN-UNRELATED", "00999", "Synthetic unrelated", [])
        )
        with closing(storage.connect(self.database)) as connection:
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            connection.execute("VACUUM")
        self.assertEqual(baseline.input_fingerprint, self.snapshot().input_fingerprint)
        self.assertEqual(
            check_snapshot_freshness(self.database, baseline).status, "Current"
        )

    def test_stale_deleted_source_and_different_database_scope(self):
        baseline = self.snapshot()
        other = self.database.with_name("SYN-copy.db")
        with (
            closing(storage.connect(self.database, read_only=True)) as src,
            closing(sqlite3.connect(other)) as dest,
        ):
            src.backup(dest)
        self.assertEqual(check_snapshot_freshness(other, baseline).status, "Stale")
        with closing(storage.connect(self.database)) as connection, connection:
            connection.execute("DELETE FROM WorkItems WHERE Id=?", (self.work.id,))
        self.assertEqual(
            check_snapshot_freshness(self.database, baseline).reason,
            "SOURCE_RECORD_MISSING_OR_MOVED",
        )

    def test_concurrent_wal_writer_does_not_mix_source_versions(self):
        before = self.snapshot()
        start, done = threading.Event(), threading.Event()
        errors = []

        def writer():
            try:
                if not start.wait(5):
                    raise AssertionError("reader did not reach barrier")
                with closing(storage.connect(self.database)) as connection, connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "UPDATE WorkItems SET RequiredCrewCount=2,EstimatedHalfDays=100 WHERE Id=?",
                        (self.work.id,),
                    )
                    connection.execute(
                        "UPDATE Crews SET Active=0 WHERE Id=?", (self.c1.id,)
                    )
                    connection.execute(
                        "UPDATE WorkingCalendarCells SET State='NotWorking' WHERE CalendarId=?",
                        (before.project_calendar.calendar_id,),
                    )
                    connection.execute(
                        "INSERT INTO DraftAssignments(WorkItemId,CrewId,LocalDate,Slot,Notes,Status,Revision,CreatedAt,UpdatedAt) VALUES (?,?,?,'AM','','Draft',1,'synthetic','synthetic')",
                        (self.work.id, self.c1.id, "2026-11-23"),
                    )
            except BaseException as error:
                errors.append(error)
            finally:
                done.set()

        thread = threading.Thread(target=writer)
        thread.start()
        original = adapter._calendar_source

        def barrier(connection, scope, entity_id, query):
            if not start.is_set():
                start.set()
                if not done.wait(5):
                    raise AssertionError("WAL writer was blocked by read snapshot")
                if errors:
                    raise errors[0]
            return original(connection, scope, entity_id, query)

        try:
            with patch.object(adapter, "_calendar_source", side_effect=barrier):
                during = self.snapshot()
        finally:
            start.set()
            thread.join(6)
        self.assertFalse(thread.is_alive())
        self.assertFalse(errors)
        self.assertEqual(during.input_fingerprint, before.input_fingerprint)
        after = self.snapshot()
        self.assertNotEqual(after.input_fingerprint, before.input_fingerprint)
        self.assertEqual(after.work_item.required_crew_count, 2)
        self.assertFalse(after.crews[0].active)
        self.assertEqual(len(after.assignments), 1)
        with closing(storage.connect(self.database)) as connection:
            self.assertEqual(
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0], 0
            )

    def test_readonly_mode_query_only_sql_trace_and_logical_data_unchanged(self):
        self.visit()
        before = self.dump()
        statements, connections = [], []
        original = storage.connect

        def tracked(path, **kwargs):
            self.assertEqual(kwargs, {"read_only": True})
            connection = original(path, **kwargs)
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA query_only").fetchone()[0], 1)
            connection.set_trace_callback(statements.append)
            connections.append(connection)
            return connection

        with patch.object(storage, "connect", side_effect=tracked):
            result = self.plan()
        self.assertFalse(result.publishable)
        self.assertEqual(self.dump(), before)
        self.assertEqual(len(connections), 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            connections[0].execute("SELECT 1")
        self.assertTrue(
            all(
                sql.lstrip().split()[0].upper()
                in ("SELECT", "PRAGMA", "BEGIN", "COMMIT", "ROLLBACK")
                for sql in statements
            )
        )
        self.assertEqual(sum(sql == "BEGIN" for sql in statements), 1)
        with closing(original(self.database, read_only=True)) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("UPDATE Projects SET SiteName='changed'")
        self.assertEqual(self.dump(), before)

    def test_read_failure_and_wrong_context_close_connection_without_partial_snapshot(
        self,
    ):
        original = storage.connect
        connections = []

        def track(path, **kwargs):
            connection = original(path, **kwargs)
            connections.append(connection)
            return connection

        with (
            patch.object(storage, "connect", side_effect=track),
            patch.object(
                adapter,
                "_calendar_source",
                side_effect=sqlite3.OperationalError("sensitive raw database detail"),
            ),
        ):
            with self.assertRaises(SnapshotReadError) as caught:
                self.snapshot()
        self.assertEqual(caught.exception.code, "DATABASE_READ_FAILED")
        self.assertNotIn("sensitive", str(caught.exception))
        with self.assertRaises(sqlite3.ProgrammingError):
            connections[0].execute("SELECT 1")
        with (
            patch.object(storage, "connect", side_effect=track),
            self.assertRaises(SnapshotContextError),
        ):
            self.snapshot(expected_project_id=999)
        with self.assertRaises(sqlite3.ProgrammingError):
            connections[-1].execute("SELECT 1")

    def test_missing_corrupt_old_new_or_unknown_database_never_migrates(self):
        missing = self.database.with_name("SYN-missing.db")
        with self.assertRaises(SnapshotReadError) as caught:
            build_recommendation_snapshot(missing, self.query)
        self.assertEqual(caught.exception.code, "DATABASE_UNAVAILABLE")
        self.assertFalse(missing.exists())
        corrupt = self.database.with_name("SYN-corrupt.db")
        corrupt.write_bytes(b"Synthetic invalid SQLite file")
        with self.assertRaises(SnapshotReadError) as caught:
            build_recommendation_snapshot(corrupt, self.query)
        self.assertEqual(caught.exception.code, "DATABASE_INVALID")
        with closing(storage.connect(self.database)) as connection, connection:
            connection.execute(
                "INSERT INTO __EFMigrationsHistory VALUES ('99999999999999_Unknown','synthetic')"
            )
        before = self.dump()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        self.assertEqual(self.dump(), before)
        old = self.database.with_name("SYN-old.db")
        with closing(sqlite3.connect(old)) as connection:
            storage.create_demo_schema(connection)
            connection.commit()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            build_recommendation_snapshot(old, self.query)
        with closing(sqlite3.connect(old)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM __EFMigrationsHistory"
                ).fetchone()[0],
                1,
            )

    def test_busy_corruption_constraints_deadline_and_read_limits_are_explicit(self):
        with closing(storage.connect(self.database)) as connection:
            connection.execute("PRAGMA journal_mode=DELETE")
        original = storage.connect
        with closing(original(self.database)) as lock:
            lock.execute("BEGIN EXCLUSIVE")

            def impatient(path, **kwargs):
                connection = original(path, **kwargs)
                connection.execute("PRAGMA busy_timeout=25")
                return connection

            with (
                patch.object(storage, "connect", side_effect=impatient),
                self.assertRaises(SnapshotReadError) as caught,
            ):
                self.snapshot()
            self.assertEqual(caught.exception.code, "DATABASE_BUSY")
            lock.rollback()
        with (
            patch.object(adapter, "READ_SECONDS", -1),
            self.assertRaises(SnapshotReadError) as caught,
        ):
            self.snapshot()
        self.assertEqual(caught.exception.code, "READ_DEADLINE_EXCEEDED")
        with (
            patch.object(adapter, "MAX_OBSERVED_ROWS", 1),
            self.assertRaises(SnapshotReadError) as caught,
        ):
            self.snapshot()
        self.assertEqual(caught.exception.code, "READ_LIMIT_EXCEEDED")
        with closing(original(self.database)) as connection, connection:
            connection.execute("PRAGMA foreign_keys=OFF")
            connection.execute(
                "UPDATE WorkItems SET ProjectId=999 WHERE Id=?", (self.work.id,)
            )
        with self.assertRaises(SnapshotReadError) as caught:
            self.snapshot()
        self.assertEqual(caught.exception.code, "DATABASE_INVALID")

    def test_cross_year_leap_dst_and_annual_boundary_use_persisted_local_dates(self):
        for start, end in (
            ("2026-12-31", "2027-01-01"),
            ("2028-02-28", "2028-02-29"),
            ("2027-03-12", "2027-03-15"),
            ("2027-11-05", "2027-11-08"),
        ):
            for scope, entity_id in (
                ("Crew", self.c1.id),
                ("Project", self.project.id),
            ):
                self.calendar(scope, entity_id, start, start, "AM")
                self.calendar(scope, entity_id, end, end, "PM")
            before = None
            for zone in ("UTC", "America/Toronto", "America/Vancouver"):
                with patch.dict(os.environ, TZ=zone):
                    result = self.plan(
                        crew_ids=(self.c1.id,),
                        earliest_start_date=start,
                        horizon_end_date=end,
                        confirmed_remaining_half_days=2,
                    )
                self.assertEqual(
                    result.generated.candidates[0].proposed_finish, DateSlot(end, "PM")
                )
                if before is not None:
                    self.assertEqual(result, before)
                before = result
        result = self.plan(
            crew_ids=(self.c1.id,),
            earliest_start_date="2028-01-01",
            horizon_end_date="2028-12-31",
            confirmed_remaining_half_days=733,
        )
        self.assertEqual(len(result.generated.candidates[0].scanned), 732)
        self.assertIsNone(result.generated.candidates[0].proposed_finish)
        with self.assertRaises(ValueError):
            replace(
                self.query,
                earliest_start_date="2028-01-01",
                horizon_end_date="2029-01-01",
            )

    def test_invalid_query_and_readonly_create_are_rejected_before_io(self):
        invalid = (
            {"crew_ids": [1]},
            {"crew_ids": (1, 1)},
            {"crew_ids": ()},
            {"crew_ids": (True,)},
            {"crew_ids": tuple(range(1, 102))},
            {"work_item_id": 0},
            {"expected_project_id": True},
            {"confirmed_remaining_half_days": 0},
            {"remaining_confirmed_by_operator": 1},
            {"max_options": 11},
            {"order": "WeightedSafety"},
            {"earliest_start_date": "2027-02-29"},
        )
        with patch.object(
            storage, "connect", side_effect=AssertionError("unexpected database read")
        ):
            for changes in invalid:
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    replace(self.query, **changes)
        with self.assertRaises(ValueError):
            storage.connect(self.database, create=True, read_only=True)
