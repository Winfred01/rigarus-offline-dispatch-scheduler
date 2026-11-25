"""Synthetic daily actual-member scope, preserved legacy identities and bounds."""

import random
import unittest
from dataclasses import asdict, replace, FrozenInstanceError
from unittest.mock import patch

from rigarus_backend import daily_personnel_conflicts as module
from rigarus_backend.daily_personnel_conflicts import (
    DailyStaffedVisit,
    validate_daily_employee_conflicts,
)
from rigarus_backend.personnel_conflicts import (
    StaffedVisit,
    validate_employee_conflicts,
)

DAY = "2026-11-23"


def visit(identity=1, crew=1, people=(7,), **changes):
    return DailyStaffedVisit(
        **(
            dict(
                record_kind="FullDayDraft",
                record_id=identity,
                work_item_id=14,
                project_id=6,
                crew_id=crew,
                local_date=DAY,
                revision=1,
                status="Draft",
                staffing_configured=True,
                employee_ids=people,
            )
            | changes
        )
    )


def validate(*visits, **changes):
    return validate_daily_employee_conflicts(
        visits,
        **(dict(start_date=DAY, end_date="2026-11-27", scope_complete=True) | changes),
    )


class DailyPersonnelTests(unittest.TestCase):
    def test_daily_cross_crew_same_person_blocks_with_all_stable_context(self):
        result = validate(
            visit(), visit(2, 2, work_item_id=15, project_id=8, revision=3)
        )
        self.assertEqual(result.state, "Blocked")
        conflict = result.conflicts[0]
        self.assertEqual(
            (conflict.employee_id, conflict.local_date, conflict.code),
            (7, DAY, "EMPLOYEE_DOUBLE_BOOKED_DAY"),
        )
        self.assertEqual(
            [
                (r.record_kind, r.record_id, r.project_id, r.revision)
                for r in conflict.visits
            ],
            [("FullDayDraft", 1, 6, 1), ("FullDayDraft", 2, 8, 3)],
        )
        self.assertTrue(all(c.state == "Blocked" for c in result.checks))
        self.assertEqual(result.validation_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)

    def test_any_legacy_half_conflicts_with_full_day_without_changing_identity(self):
        for half in ("AM", "PM"):
            old = visit(1, 2, record_kind="LegacyHalfDay", legacy_slot=half)
            result = validate(visit(), old)
            self.assertEqual(result.state, "Blocked")
            self.assertEqual(
                {r.record_kind for r in result.conflicts[0].visits},
                {"FullDayDraft", "LegacyHalfDay"},
            )
            self.assertEqual(
                next(
                    r
                    for r in result.conflicts[0].visits
                    if r.record_kind == "LegacyHalfDay"
                ).legacy_slot,
                half,
            )
            self.assertEqual(old.legacy_slot, half)

    def test_legacy_opposite_halves_are_daily_conflicts_but_old_validator_retains_history_rule(
        self,
    ):
        a = visit(record_kind="LegacyHalfDay", legacy_slot="AM")
        b = visit(2, 2, record_kind="LegacyHalfDay", legacy_slot="PM")
        self.assertEqual(validate(a, b).state, "Blocked")
        legacy = tuple(
            StaffedVisit(
                v.record_id,
                v.work_item_id,
                v.project_id,
                v.crew_id,
                v.local_date,
                v.legacy_slot,
                v.status,
                v.staffing_configured,
                v.employee_ids,
            )
            for v in (a, b)
        )
        old = validate_employee_conflicts(
            legacy, start_date=DAY, end_date="2026-11-27", scope_complete=True
        )
        self.assertEqual(old.state, "Satisfied")

    def test_same_crew_legacy_halves_and_distinct_dates_or_people_do_not_conflict(self):
        a = visit(record_kind="LegacyHalfDay", legacy_slot="AM")
        b = visit(2, 1, record_kind="LegacyHalfDay", legacy_slot="PM")
        result = validate(a, b, visit(3, 2, (8,)), visit(4, 2, local_date="2026-11-24"))
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(result.conflicts, ())

    def test_multiple_people_three_crews_and_both_old_halves_have_complete_references(
        self,
    ):
        result = validate(
            visit(people=(7, 8)),
            visit(2, 2, (8, 7)),
            visit(3, 3, (7,), record_kind="LegacyHalfDay", legacy_slot="AM"),
            visit(4, 3, (7,), record_kind="LegacyHalfDay", legacy_slot="PM"),
        )
        self.assertEqual([c.employee_id for c in result.conflicts], [7, 8])
        self.assertEqual(len(result.conflicts[0].visits), 4)
        self.assertEqual(len(result.conflicts[1].visits), 2)

    def test_cancelled_retains_namespaced_reference_and_releases_daily_capacity(self):
        result = validate(
            visit(),
            visit(
                1, 2, status="Cancelled", record_kind="LegacyHalfDay", legacy_slot="PM"
            ),
        )
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(len(result.checks), 1)
        self.assertEqual(
            (
                result.ignored_cancelled[0].record_kind,
                result.ignored_cancelled[0].record_id,
            ),
            ("LegacyHalfDay", 1),
        )
        self.assertEqual(validate(visit(status="Cancelled")).state, "Pending")

    def test_missing_empty_partial_scope_and_no_active_records_stay_pending(self):
        for v in (visit(people=(), staffing_configured=False), visit(people=())):
            result = validate(v)
            self.assertEqual(result.state, "Pending")
            self.assertTrue(result.checks[0].reasons)
        self.assertEqual(validate(visit(), scope_complete=False).state, "Pending")
        self.assertEqual(validate().state, "Pending")

    def test_unknown_other_crew_on_same_date_prevents_false_clear_but_other_date_does_not(
        self,
    ):
        unknown = visit(2, 2, (), staffing_configured=False)
        result = validate(visit(), unknown)
        self.assertEqual(result.checks[0].state, "Pending")
        self.assertIn("OTHER_CREW_STAFFING_UNKNOWN", result.checks[0].reasons)
        result = validate(visit(), replace(unknown, local_date="2026-11-24"))
        self.assertEqual(
            next(c.state for c in result.checks if c.visit.record_id == 1), "Satisfied"
        )

    def test_known_conflicts_stay_blocked_despite_unknown_members_and_incomplete_scope(
        self,
    ):
        result = validate(
            visit(),
            visit(2, 2),
            visit(3, 3, (), staffing_configured=False),
            scope_complete=False,
        )
        self.assertEqual(result.state, "Blocked")
        self.assertEqual(
            [c.state for c in result.checks], ["Blocked", "Blocked", "Pending"]
        )

    def test_preserves_crew_occupancy_invariants_and_rejects_duplicate_current_records(
        self,
    ):
        for other in (
            visit(2),
            visit(2, record_kind="LegacyHalfDay", legacy_slot="PM"),
        ):
            with self.assertRaises(ValueError):
                validate(visit(), other)
        legacy = visit(record_kind="LegacyHalfDay", legacy_slot="AM")
        with self.assertRaises(ValueError):
            validate(legacy, replace(legacy, record_id=2))
        with self.assertRaises(ValueError):
            validate(visit(), visit(local_date="2026-11-24"))
        with self.assertRaises(ValueError):
            validate(visit(), visit())

    def test_strict_ids_dates_membership_record_kind_and_raw_slot(self):
        v = visit()
        for changes in (
            dict(record_id=True),
            dict(revision=0),
            dict(crew_id=1.0),
            dict(local_date="2026-02-30"),
            dict(local_date="2026-1-01"),
            dict(employee_ids=[7]),
            dict(employee_ids=(7, 7)),
            dict(employee_ids=(True,)),
            dict(staffing_configured=1),
            dict(staffing_configured=False),
            dict(record_kind="Unknown"),
            dict(legacy_slot="AM"),
            dict(status="Published"),
        ):
            with self.assertRaises(ValueError):
                replace(v, **changes)
        with self.assertRaises(ValueError):
            replace(v, record_kind="LegacyHalfDay")
        with self.assertRaises(ValueError):
            replace(v, record_kind="Proposal", status="Cancelled")
        with self.assertRaises(ValueError):
            validate(v, scope_complete=1)
        with self.assertRaises(ValueError):
            validate(replace(v, local_date="2026-11-28"))
        with self.assertRaises(ValueError):
            validate(v, end_date="2027-11-23")

    def test_determinism_immutability_and_no_file_network_sql_or_clock(self):
        visits = (visit(people=(8, 7)), visit(2, 2, (7, 8)), visit(3, 3, (9,)))
        before = tuple(asdict(v) for v in visits)
        expected = validate(*visits)
        randomizer = random.Random(15)
        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("time.time", side_effect=AssertionError("clock")),
        ):
            for _ in range(15):
                shuffled = list(visits)
                randomizer.shuffle(shuffled)
                self.assertEqual(validate(*shuffled), expected)
        self.assertEqual(tuple(asdict(v) for v in visits), before)
        with self.assertRaises(FrozenInstanceError):
            expected.state = "Satisfied"

    def test_year_leap_dst_and_bounded_dense_grouping(self):
        for day in (
            "2026-12-31",
            "2028-02-29",
            "2027-03-14",
            "2027-11-07",
            "9999-12-31",
        ):
            result = validate(
                replace(visit(), local_date=day),
                replace(visit(2, 2), local_date=day),
                start_date=day,
                end_date=day,
            )
            self.assertEqual(result.conflicts[0].local_date, day)
        dense = tuple(visit(i, i, tuple(range(1, 21))) for i in range(1, 101))
        result = validate(*dense)
        self.assertEqual(len(result.conflicts), 20)
        self.assertEqual(sum(len(c.visits) for c in result.conflicts), 2000)
        unknown = tuple(
            visit(i, i, (), staffing_configured=False) for i in range(1, 1001)
        )
        result = validate(*unknown)
        self.assertEqual(len(result.checks), 1000)
        self.assertTrue(all(c.state == "Pending" for c in result.checks))
        with patch.object(module, "MAX_MEMBERSHIPS", 3):
            with self.assertRaises(ValueError):
                validate(visit(people=(7, 8)), visit(2, 2, (7, 8)))
        with patch.object(module, "MAX_VISITS", 1):
            with self.assertRaises(ValueError):
                validate(visit(), visit(2, 2))
