"""Synthetic schema18, consistent consent view, weekend re-proposal and borrowing."""

import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from unittest.mock import patch

import test_day_recommendation_adapter as fixtures
import test_recommendation_adapter as legacy
from migration_fixture import remove_daily_weekend_schema
from rigarus_backend import storage, day_recommendation_adapter as adapter
from rigarus_backend.daily_weekend_consent import WeekendContext, WeekendCrewDay
from rigarus_backend.daily_weekend_store import WeekendConsentStore, WeekendDecision
from rigarus_backend.daily_calendar_store import DailyConflict
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_drafts import DayDraft, ConfirmedRemainingDays
from rigarus_backend.day_personnel_validation import (
    ProposedDayMembers,
    validate_day_candidate_personnel,
)
from rigarus_backend.day_driver_proposal import SourceDayMembers
from rigarus_backend.day_weekend_proposal import (
    validate_day_weekend_proposal,
    check_weekend_proposal_freshness,
)
from rigarus_backend.day_backup import logical_digest

FRI, SAT, SUN, MON = "2026-11-27", "2026-11-28", "2026-11-29", "2026-11-30"


class WeekendSnapshotTests(unittest.TestCase):
    setUp = fixtures.DayAdapterTests.setUp
    daily = fixtures.DayAdapterTests.daily
    calendar = fixtures.DayAdapterTests.calendar
    snapshot = fixtures.DayAdapterTests.snapshot
    employee = fixtures.DayAdapterTests.employee
    day = fixtures.DayAdapterTests.day
    visit = fixtures.DayAdapterTests.visit
    digest = fixtures.DayAdapterTests.digest

    def prepare(self):
        a, b = self.employee(), self.employee("Synthetic worker B", home=self.c2.id)
        self.daily("Project", self.project.id, FRI, MON)
        self.daily("Crew", self.c1.id, FRI, MON)
        self.query = replace(
            self.query,
            crew_ids=(self.c1.id,),
            earliest_start_date=FRI,
            horizon_end_date=MON,
            weekend_members=(WeekendCrewDay(self.c1.id, SAT, (a.id, b.id)),),
        )
        return (
            a,
            b,
            WeekendContext(
                self.work.id, self.project.id, self.c1.id, SAT, (a.id, b.id)
            ),
        )

    def decision(self, ctx, employee, state="Confirmed", revision=0):
        return WeekendConsentStore(self.database).save_planned(
            ctx,
            employee,
            WeekendDecision(
                state, state != "Pending", True, "Synthetic employee decision"
            ),
            revision,
        )

    def candidate(self, snapshot=None):
        return adapter.generate_from_day_snapshot(
            snapshot or self.snapshot()
        ).generated.candidates[0]

    def test_t06_pending_partial_declined_all_confirmed_rescores_finish(self):
        a, b, ctx = self.prepare()
        self.assertEqual(self.candidate().allocated_working_dates, (FRI, MON))
        self.decision(ctx, a.id)
        self.assertEqual(self.candidate().allocated_working_dates, (FRI, MON))
        self.decision(ctx, b.id, "Declined")
        self.assertEqual(self.candidate().allocated_working_dates, (FRI, MON))
        self.decision(ctx, b.id, revision=1)
        r = adapter.generate_from_day_snapshot(self.snapshot())
        self.assertEqual(r.generated.candidates[0].allocated_working_dates, (FRI, SAT))
        self.assertEqual(r.validation_status, "Pending")
        self.assertFalse(r.applyable or r.publishable)
        self.assertEqual(len(WeekendConsentStore(self.database).history(ctx, b.id)), 2)

    def test_latest_pending_never_resurrects_confirmed_and_noop_reopen(self):
        a, b, ctx = self.prepare()
        self.decision(ctx, a.id)
        self.decision(ctx, b.id)
        self.assertEqual(self.decision(ctx, b.id, revision=1), 1)
        self.decision(ctx, b.id, "Pending", 1)
        storage.initialize_database(self.database)
        self.assertEqual(self.candidate().allocated_working_dates, (FRI, MON))
        self.assertEqual(len(WeekendConsentStore(self.database).history(ctx, b.id)), 2)

    def test_available_home_crew_calendars_no_inferred_consent(self):
        a, b, _ = self.prepare()
        for p in (a, b):
            self.daily("Employee", p.id, FRI, MON, "Available")
        self.assertEqual(self.candidate().allocated_working_dates, (FRI, MON))
        self.assertEqual(
            self.candidate(self.snapshot(weekend_members=())).allocated_working_dates,
            (FRI, MON),
        )

    def test_saved_actual_revision_change_and_member_return_needs_review(self):
        a, b, ctx = self.prepare()
        row = self.day(day=SAT, workers=(a.id, b.id))
        store = WeekendConsentStore(self.database)
        for p in (a, b):
            store.save_for_day(
                row["id"],
                row["revision"],
                p.id,
                WeekendDecision("Confirmed", True, True, "Synthetic saved decision"),
                0,
            )
        self.assertEqual(
            adapter.validate_day_snapshot_weekend(self.snapshot()).state, "Satisfied"
        )
        changed = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, SAT, "Synthetic changed", (a.id,)),
            row["id"],
            row["revision"],
        )
        returned = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, SAT, "Synthetic returned", (a.id, b.id)),
            row["id"],
            changed["revision"],
        )
        self.assertEqual(
            adapter.validate_day_snapshot_weekend(self.snapshot()).state, "Pending"
        )
        with self.assertRaises(DailyConflict):
            store.save_for_day(
                row["id"],
                row["revision"],
                a.id,
                WeekendDecision("Confirmed", True, True, "Synthetic"),
                1,
            )
        for p in (a, b):
            store.save_for_day(
                returned["id"],
                returned["revision"],
                p.id,
                WeekendDecision("Confirmed", True, True, "Synthetic reconfirmed"),
                1,
            )
        self.assertEqual(
            adapter.validate_day_snapshot_weekend(self.snapshot()).state, "Satisfied"
        )
        self.assertEqual(ctx.employee_ids, (a.id, b.id))

    def test_saved_empty_unconfigured_weekday_or_nonmember_rejects(self):
        a, b, _ = self.prepare()
        store = WeekendConsentStore(self.database)
        for roster, day in ((None, SAT), ((), SUN), ((a.id,), FRI)):
            row = self.day(day=day, workers=roster)
            with self.assertRaises(ValueError):
                store.save_for_day(
                    row["id"],
                    row["revision"],
                    b.id,
                    WeekendDecision("Confirmed", True, True, "Synthetic"),
                    0,
                )

    def test_target_changed_roster_rejects_even_lower_level_personnel_entry(self):
        a, b, ctx = self.prepare()
        for p in (a, b):
            self.decision(ctx, p.id)
        snap = self.snapshot()
        candidate = self.candidate(snap)
        with self.assertRaises(ValueError):
            validate_day_candidate_personnel(
                snap, candidate, (ProposedDayMembers(SAT, (a.id,)),)
            )
        changed = self.snapshot(
            weekend_members=(WeekendCrewDay(self.c1.id, SAT, (a.id,)),)
        )
        self.assertEqual(self.candidate(changed).allocated_working_dates, (FRI, MON))
        with self.assertRaises(ValueError):
            validate_day_candidate_personnel(changed, candidate, ())

    def test_borrowing_rechecks_source_and_destination_no_implicit_removal(self):
        a, b, ctx = self.prepare()
        source = self.day(crew=self.c2.id, day=SAT, workers=(a.id, b.id))
        store = WeekendConsentStore(self.database)
        for p in (a, b):
            store.save_for_day(
                source["id"],
                source["revision"],
                p.id,
                WeekendDecision("Confirmed", True, True, "Synthetic source consent"),
                0,
            )
            self.decision(ctx, p.id)
        snap = self.snapshot()
        candidate = self.candidate(snap)
        members = (
            ProposedDayMembers(FRI, (a.id, b.id)),
            ProposedDayMembers(SAT, (a.id, b.id)),
        )
        before = self.digest()
        result = validate_day_weekend_proposal(snap, candidate, members)
        self.assertEqual(result.state, "Blocked")
        self.assertTrue(result.comparison.excluded)
        result = validate_day_weekend_proposal(
            snap,
            candidate,
            members,
            (
                SourceDayMembers(
                    "FullDayDraft", source["id"], source["revision"], (b.id,)
                ),
            ),
        )
        self.assertEqual(result.source_checks[0].state, "Pending")
        self.assertEqual(result.target_checks[-1].state, "Satisfied")
        self.assertEqual(
            result.source_checks[0].members[0].reason,
            "WEEKEND_ROSTER_CHANGED_RECONFIRM",
        )
        self.assertEqual(self.digest(), before)
        self.assertFalse(result.applyable or result.publishable)
        self.assertEqual(
            check_weekend_proposal_freshness(self.database, result).status, "Current"
        )

    def test_legacy_am_pm_actual_workers_retained_and_need_review(self):
        from rigarus_backend.staffing_store import StaffingStore

        a, b, ctx = self.prepare()
        for p in (a, b):
            self.decision(ctx, p.id)
        old = self.visit(crew=self.c2.id, day=SAT, half="PM")
        StaffingStore(self.database).save(old.id, (a.id,), old.revision)
        report = adapter.validate_day_snapshot_weekend(self.snapshot())
        self.assertEqual(report.state, "Pending")
        self.assertEqual(report.checks[0].visit.legacy_slot, "PM")
        self.assertIn("LEGACY_HALF_DAY_NEEDS_REVIEW", report.checks[0].reasons)

    def test_snapshot_fingerprint_stale_for_decisions_staff_and_outside_range(self):
        a, b, ctx = self.prepare()
        snap = self.snapshot()
        self.decision(ctx, a.id)
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, snap).status, "Stale"
        )
        snap = self.snapshot()
        outside = replace(ctx, local_date="2026-12-05")
        self.decision(outside, b.id)
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, snap).status, "Stale"
        )
        snap = self.snapshot()
        self.day(crew=self.c2.id, day=SAT, workers=(a.id,))
        self.assertEqual(
            adapter.check_day_snapshot_freshness(self.database, snap).status, "Stale"
        )
        self.assertEqual(adapter.FORMAT, "rigarus-day-recommendation-input-v6")

    def test_one_pinned_consent_and_staff_view_during_concurrent_commit(self):
        a, b, ctx = self.prepare()
        old = self.snapshot()
        original = adapter._read_schema

        def concurrent(c):
            result = original(c)
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(self.decision, ctx, a.id).result()
            return result

        with patch.object(adapter, "_read_schema", side_effect=concurrent):
            self.assertEqual(self.snapshot(), old)
        self.assertNotEqual(self.snapshot(), old)

    def test_concurrent_revision_and_history_immutability(self):
        a, _, ctx = self.prepare()

        def save():
            try:
                self.decision(ctx, a.id)
                return "saved"
            except DailyConflict:
                return "stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(
                sorted(pool.map(lambda _: save(), range(2))), ["saved", "stale"]
            )
        with closing(storage.connect(self.database)) as c, c:
            for sql in (
                "UPDATE WeekendConsentChanges SET State='Confirmed'",
                "DELETE FROM WeekendConsentChanges",
                "DELETE FROM WeekendConsentScopes",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)
        self.assertEqual(len(WeekendConsentStore(self.database).history(ctx, a.id)), 1)

    def test_failed_history_append_rolls_back_scope_identity_and_sequence(self):
        a, _, ctx = self.prepare()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticConsentFailure BEFORE INSERT ON WeekendConsentChanges BEGIN SELECT RAISE(ABORT,'Synthetic failure'); END"
            )
        old = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            self.decision(ctx, a.id)
        self.assertEqual(self.digest(), old)

    def test_bad_query_parent_member_and_bounds_reject(self):
        a, _, ctx = self.prepare()
        for make in (
            lambda: self.snapshot(
                weekend_members=(WeekendCrewDay(self.c2.id, SAT, (a.id,)),)
            ),
            lambda: self.snapshot(
                weekend_members=(WeekendCrewDay(self.c1.id, "2026-12-05", (a.id,)),)
            ),
            lambda: self.snapshot(weekend_members=(self.query.weekend_members[0],) * 2),
            lambda: self.decision(replace(ctx, project_id=99999), a.id),
            lambda: self.decision(ctx, 99999),
            lambda: self.snapshot(remaining=ConfirmedRemainingDays(0, True)),
        ):
            with self.assertRaises(ValueError):
                make()
        with self.assertRaises(adapter.SnapshotNotFound):
            self.snapshot(weekend_members=(WeekendCrewDay(self.c1.id, SAT, (99999,)),))

    def test_read_budget_errors_and_logical_no_writes(self):
        a, b, ctx = self.prepare()
        for p in (a, b):
            self.decision(ctx, p.id)
        snap = self.snapshot()
        before = self.digest()
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
            patch("time.time", side_effect=AssertionError),
        ):
            result = adapter.generate_from_day_snapshot(snap)
            self.assertEqual(result, adapter.generate_from_day_snapshot(snap))
            members = tuple(
                ProposedDayMembers(day, (a.id, b.id))
                for day in result.generated.candidates[0].allocated_working_dates
            )
            validate_day_weekend_proposal(snap, result.generated.candidates[0], members)
        self.assertEqual(before, self.digest())
        for key in ("MAX_READ_BYTES", "MAX_READ_UNITS"):
            with patch.object(adapter, key, 1):
                with self.assertRaises(adapter.SnapshotReadError):
                    self.snapshot()
        self.assertEqual(before, self.digest())

    def test_confirmed_weekend_does_not_override_closed_unknown_or_crew_occupancy(self):
        a, b, ctx = self.prepare()
        for p in (a, b):
            self.decision(ctx, p.id)
        for state in ("Unknown", "NotWorking"):
            self.daily("Crew", self.c1.id, SAT, SAT, state)
            self.assertEqual(self.candidate().allocated_working_dates, (FRI, MON))
        self.daily("Crew", self.c1.id, SAT, SAT)
        self.day(day=SAT, workers=(a.id, b.id))
        self.assertEqual(self.candidate().allocated_working_dates, (FRI, MON))

    def test_dual_sort_and_deterministic_replay_preserved(self):
        a, b, ctx = self.prepare()
        for p in (a, b):
            self.decision(ctx, p.id)
        self.daily("Crew", self.c2.id, FRI, MON)
        self.daily("Crew", self.c2.id, FRI, FRI, "NotWorking")
        for order in ("EarliestFinish", "EarliestStart"):
            snap = self.snapshot(crew_ids=(self.c2.id, self.c1.id), order=order)
            r = adapter.generate_from_day_snapshot(snap)
            self.assertEqual(r, adapter.generate_from_day_snapshot(snap))
            self.assertEqual(
                r.generated.comparison.options[0].option.crew_id, self.c1.id
            )
        self.assertTrue(json.loads(self.snapshot().weekend_source_json))

    def test_borrowed_source_refusal_excludes_even_when_target_consent_passes(self):
        a, b, _ = self.prepare()
        self.query = replace(
            self.query, weekend_members=(WeekendCrewDay(self.c1.id, SAT, (a.id,)),)
        )
        target = WeekendContext(self.work.id, self.project.id, self.c1.id, SAT, (a.id,))
        self.decision(target, a.id)
        source = self.day(crew=self.c2.id, day=SAT, workers=(a.id, b.id))
        WeekendConsentStore(self.database).save_for_day(
            source["id"],
            source["revision"],
            b.id,
            WeekendDecision("Declined", True, True, "Synthetic refusal"),
            0,
        )
        snap = self.snapshot()
        candidate = self.candidate(snap)
        result = validate_day_weekend_proposal(
            snap,
            candidate,
            tuple(
                ProposedDayMembers(d, (a.id,))
                for d in candidate.allocated_working_dates
            ),
            (
                SourceDayMembers(
                    "FullDayDraft", source["id"], source["revision"], (b.id,)
                ),
            ),
        )
        self.assertEqual(result.target_checks[-1].state, "Satisfied")
        self.assertEqual(result.source_checks[0].state, "Blocked")
        self.assertTrue(result.comparison.excluded)
        evidence = result.comparison.excluded[0].option.days[-1].evidence
        self.assertIn(
            ("WeekendConsent", "Blocked"), [(e.check, e.state) for e in evidence]
        )

    def test_sql_invalid_roster_and_saved_context_cannot_be_appended(self):
        a, _, ctx = self.prepare()
        self.decision(ctx, a.id)
        saved = self.day(day=SAT, workers=(a.id,))
        with closing(storage.connect(self.database)) as c, c:
            columns = "ScopeId,Revision,State,EmployeeDecisionConfirmed,FullDayConfirmed,RosterSnapshot,RosterFingerprint,SourceKind,SourceAssignmentId,SourceRevision,Reference,RecordedAt"
            for roster in ("[]", "[1,1]", "{}", "[999999]"):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(
                        f"INSERT INTO WeekendConsentChanges({columns}) SELECT ScopeId,2,State,EmployeeDecisionConfirmed,FullDayConfirmed,?,RosterFingerprint,SourceKind,SourceAssignmentId,SourceRevision,Reference,RecordedAt FROM WeekendConsentChanges WHERE Revision=1",
                        (roster,),
                    )
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(
                    f"""INSERT INTO WeekendConsentChanges({columns})
                  SELECT ScopeId,2,State,EmployeeDecisionConfirmed,FullDayConfirmed,
                  RosterSnapshot,RosterFingerprint,'FullDayDraft',?,?,Reference,RecordedAt
                  FROM WeekendConsentChanges WHERE Revision=1""",
                    (saved["id"], saved["revision"]),
                )
        self.assertEqual(len(WeekendConsentStore(self.database).history(ctx, a.id)), 1)


class WeekendMigrationTests(unittest.TestCase):
    setUp = WeekendSnapshotTests.setUp
    daily = WeekendSnapshotTests.daily
    calendar = WeekendSnapshotTests.calendar
    employee = WeekendSnapshotTests.employee
    day = WeekendSnapshotTests.day
    snapshot = WeekendSnapshotTests.snapshot
    digest = WeekendSnapshotTests.digest

    def old17(self):
        self.day(workers=(self.employee().id,))
        with closing(storage.connect(self.database)) as c, c:
            remove_daily_weekend_schema(c)

    def test_17_to18_verified_backup_all_rows_history_fk_and_idempotence(self):
        self.old17()
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
        with closing(storage.connect(self.database)) as c:
            for table, rows in original.items():
                now = c.execute('SELECT * FROM "' + table + '"').fetchall()
                self.assertEqual(
                    now[: len(rows)] if table == "__EFMigrationsHistory" else now,
                    rows,
                    table,
                )
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
        after = self.digest()
        storage.initialize_database(self.database)
        self.assertEqual(self.digest(), after)
        self.assertEqual(len(self.snapshot().migrations), 21)

    def test_migration_fault_backup_failure_rollback_retry_and_no_read_migration(self):
        self.old17()
        before = self.digest()
        with self.assertRaises(storage.UnsupportedDatabaseError):
            self.snapshot()
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticWeekendMigrationFailure BEFORE INSERT ON __EFMigrationsHistory WHEN NEW.MigrationId LIKE '%AddDailyWeekendConsent' BEGIN SELECT RAISE(ABORT,'Synthetic failure'); END"
            )
        before = self.digest()
        with self.assertRaises(sqlite3.IntegrityError):
            storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticWeekendMigrationFailure")
        before = self.digest()
        with patch.object(
            storage, "verified_upgrade_backup", side_effect=OSError("Synthetic")
        ):
            with self.assertRaises(OSError):
                storage.initialize_database(self.database)
        self.assertEqual(self.digest(), before)
        storage.initialize_database(self.database)
        self.assertEqual(len(self.snapshot().migrations), 21)


class WeekendLegacyGuardTests(unittest.TestCase):
    setUp = legacy.AdapterTests.setUp
    calendar = legacy.AdapterTests.calendar
    snapshot = legacy.AdapterTests.snapshot
    employee = legacy.AdapterTests.employee

    def test_halfday_adapter_refuses_new_pending_consent_and_expires_proof(self):
        old = self.snapshot(earliest_start_date=SAT, horizon_end_date=MON)
        person = self.employee()
        WeekendConsentStore(self.database).save_planned(
            WeekendContext(
                self.work.id, self.project.id, self.c1.id, SAT, (person.id,)
            ),
            person.id,
            WeekendDecision("Pending", False, True, "Synthetic"),
            0,
        )
        from rigarus_backend.recommendation_adapter import (
            SnapshotContextError,
            check_snapshot_freshness,
        )

        with self.assertRaises(SnapshotContextError):
            self.snapshot(earliest_start_date=SAT, horizon_end_date=MON)
        self.assertEqual(
            check_snapshot_freshness(self.database, old).reason,
            "DAILY_WEEKEND_ADAPTER_REQUIRED",
        )
