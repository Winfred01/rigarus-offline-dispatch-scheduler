import os
import random
import unittest
from dataclasses import FrozenInstanceError, asdict, replace
from itertools import permutations
from unittest.mock import patch

from rigarus_backend import personnel_conflicts as module
from rigarus_backend.personnel_conflicts import (
    StaffedVisit,
    validate_employee_conflicts,
)


def visit(number=1, crew=1, employees=(7,), **changes):
    values = dict(
        assignment_id=number,
        work_item_id=14,
        project_id=6,
        crew_id=crew,
        local_date="2026-11-23",
        slot="AM",
        status="Draft",
        staffing_configured=True,
        employee_ids=employees,
    )
    return StaffedVisit(**{**values, **changes})


def validate(*visits, **changes):
    return validate_employee_conflicts(
        visits,
        **{
            "start_date": "2026-11-23",
            "end_date": "2026-11-27",
            "scope_complete": True,
            **changes,
        },
    )


class PersonnelConflictTests(unittest.TestCase):
    def test_cross_crew_same_employee_identifies_all_context(self):
        a, b = visit(), visit(2, 2, work_item_id=15, project_id=8)
        result = validate(a, b)
        self.assertEqual(result.state, "Blocked")
        conflict = result.conflicts[0]
        self.assertEqual(
            (conflict.employee_id, conflict.local_date, conflict.slot),
            (7, "2026-11-23", "AM"),
        )
        self.assertEqual(
            [v.assignment_id for v in conflict.visits],
            [a.assignment_id, b.assignment_id],
        )
        self.assertEqual([v.project_id for v in conflict.visits], [6, 8])
        self.assertEqual(
            set(asdict(conflict.visits[0])),
            {"assignment_id", "work_item_id", "project_id", "crew_id"},
        )
        self.assertEqual(conflict.code, "EMPLOYEE_DOUBLE_BOOKED")
        self.assertTrue(
            all(
                c.state == "Blocked" and c.conflicting_employee_ids == (7,)
                for c in result.checks
            )
        )

    def test_three_way_and_multiple_workers_have_complete_groups(self):
        result = validate(
            visit(employees=(7, 8)), visit(2, 2, (8, 7)), visit(3, 3, (7,))
        )
        self.assertEqual([c.employee_id for c in result.conflicts], [7, 8])
        self.assertEqual(
            [v.assignment_id for v in result.conflicts[0].visits], [1, 2, 3]
        )
        self.assertEqual([v.assignment_id for v in result.conflicts[1].visits], [1, 2])

    def test_am_pm_dates_and_nonshared_workers_do_not_overlap(self):
        result = validate(
            visit(),
            visit(2, 2, slot="PM"),
            visit(3, 1, local_date="2026-11-24"),
            visit(4, 3, (8,)),
        )
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(result.conflicts, ())
        self.assertTrue(all(c.state == "Satisfied" for c in result.checks))
        self.assertEqual(result.validation_status, "Pending")
        self.assertFalse(result.publishable or result.applyable)

    def test_cancelled_membership_ignored_and_ids_preserved(self):
        result = validate(
            visit(), visit(2, 2, status="Cancelled"), visit(3, 2, status="Cancelled")
        )
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(result.ignored_cancelled_ids, (2, 3))
        self.assertEqual(len(result.checks), 1)

    def test_unconfigured_and_explicit_empty_staffing_stay_pending(self):
        for configured, reason in (
            (False, "ACTUAL_STAFFING_NOT_CONFIGURED"),
            (True, "ACTUAL_STAFFING_EMPTY"),
        ):
            with self.subTest(configured=configured):
                result = validate(visit(employees=(), staffing_configured=configured))
                self.assertEqual(result.state, "Pending")
                self.assertIn(reason, result.checks[0].reasons)

    def test_no_active_evidence_never_passes(self):
        for visits in ((), (visit(status="Cancelled"),)):
            result = validate(*visits)
            self.assertEqual(result.state, "Pending")
            self.assertIn("NO_ACTIVE_ASSIGNMENTS", result.reasons)

    def test_incomplete_scope_never_satisfies_but_known_conflict_blocks(self):
        clear = validate(visit(), scope_complete=False)
        self.assertEqual(clear.state, "Pending")
        self.assertEqual(clear.checks[0].state, "Pending")
        self.assertIn("STAFFING_SCOPE_INCOMPLETE", clear.reasons)
        blocked = validate(visit(), visit(2, 2), scope_complete=False)
        self.assertEqual(blocked.state, "Blocked")

    def test_known_conflicts_and_missing_staffing_both_retained(self):
        result = validate(
            visit(), visit(2, 2), visit(3, 3, (), staffing_configured=False)
        )
        self.assertEqual(result.state, "Blocked")
        self.assertEqual(
            [x.state for x in result.checks], ["Blocked", "Blocked", "Pending"]
        )
        self.assertIn("ACTUAL_STAFFING_REQUIRES_REVIEW", result.reasons)

    def test_canonical_input_order_employee_order_and_immutable_results(self):
        inputs = (visit(employees=(8, 7)), visit(2, 2, (7, 8)), visit(3, 3, (7,)))
        expected = validate(*inputs)
        before = asdict(inputs[0])
        for order in permutations(inputs):
            self.assertEqual(validate(*order), expected)
        self.assertEqual(asdict(inputs[0]), before)
        with self.assertRaises(FrozenInstanceError):
            inputs[0].employee_ids = ()
        for field in ("publishable", "applyable", "validation_status", "scope"):
            with self.assertRaises(TypeError):
                replace(expected, **{field: True})

    def test_duplicate_assignment_employee_and_active_crew_slots_rejected(self):
        with self.assertRaisesRegex(ValueError, "Assignment IDs"):
            validate(visit(), visit())
        with self.assertRaisesRegex(ValueError, "Duplicate employee"):
            visit(employees=(7, 7))
        with self.assertRaisesRegex(ValueError, "occupancy"):
            validate(visit(), visit(2, employees=(8,)))
        with self.assertRaisesRegex(ValueError, "Unconfigured"):
            visit(staffing_configured=False)

    def test_invalid_ids_dates_status_and_mutable_shapes_rejected(self):
        for field in ("assignment_id", "work_item_id", "project_id", "crew_id"):
            for value in (0, -1, True, 1.0, "1", 2**53):
                with (
                    self.subTest(field=field, value=value),
                    self.assertRaises(ValueError),
                ):
                    visit(**{field: value})
        for employees in ([7], (True,), (0,), ("7",)):
            with self.assertRaises(ValueError):
                visit(employees=employees)
        for changes in (
            {"local_date": "2027-02-29"},
            {"local_date": "2026-1-01"},
            {"slot": "FullDay"},
            {"status": "Published"},
            {"staffing_configured": 1},
        ):
            with self.assertRaises(ValueError):
                visit(**changes)
        with self.assertRaises(ValueError):
            validate_employee_conflicts(
                [visit()],
                start_date="2026-11-23",
                end_date="2026-11-27",
                scope_complete=True,
            )
        with self.assertRaises(ValueError):
            validate(visit(), scope_complete=1)
        with self.assertRaises(TypeError):
            validate_employee_conflicts(
                (visit(),), start_date="2026-11-23", end_date="2026-11-27"
            )

    def test_scope_and_workload_boundaries(self):
        with self.assertRaises(ValueError):
            validate(visit(local_date="2026-11-28"))
        with self.assertRaises(ValueError):
            validate(visit(), end_date="2027-11-23")
        a, b = visit(), visit(2, 2)
        with patch.object(module, "MAX_VISITS", 1), self.assertRaises(ValueError):
            validate(a, b)
        with patch.object(module, "MAX_MEMBERSHIPS", 1), self.assertRaises(ValueError):
            validate(a, b)

    def test_weekends_cross_year_leap_dst_and_date_max_are_local(self):
        for day in (
            "2026-12-31",
            "2028-02-29",
            "2027-03-14",
            "2027-11-07",
            "9999-12-31",
        ):
            before = None
            for zone in ("UTC", "America/Toronto", "America/Vancouver"):
                with patch.dict(os.environ, TZ=zone):
                    result = validate(
                        visit(local_date=day),
                        visit(2, 2, local_date=day),
                        start_date=day,
                        end_date=day,
                    )
                self.assertEqual(result.conflicts[0].local_date, day)
                if before is not None:
                    self.assertEqual(result, before)
                before = result

    def test_pure_no_io_sql_network_or_clock(self):
        inputs = (visit(), visit(2, 2))
        before = tuple(asdict(v) for v in inputs)
        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("os.open", side_effect=AssertionError("file")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("time.time", side_effect=AssertionError("clock")),
            patch("time.monotonic", side_effect=AssertionError("clock")),
        ):
            result = validate(*inputs)
        self.assertEqual(result.state, "Blocked")
        self.assertEqual(tuple(asdict(v) for v in inputs), before)

    def test_bounded_scale_reports_all_memberships(self):
        inputs = tuple(visit(i + 1, i + 1, (i // 2 + 1,)) for i in range(2000))
        result = validate(*inputs)
        self.assertEqual(len(result.conflicts), 1000)
        self.assertEqual(sum(len(c.visits) for c in result.conflicts), 2000)
        self.assertTrue(all(c.state == "Blocked" for c in result.checks))

    def test_seeded_independent_grouping_oracle(self):
        rng = random.Random(15)
        for _ in range(50):
            visits = tuple(
                visit(
                    i + 1,
                    i + 1,
                    tuple(rng.sample(range(1, 9), rng.randint(0, 3))),
                    status=rng.choice(("Draft", "Draft", "Cancelled")),
                )
                for i in range(20)
            )
            expected = {}
            for v in visits:
                if v.status == "Draft":
                    for e in v.employee_ids:
                        expected.setdefault(e, []).append(v.assignment_id)
            expected = {e: ids for e, ids in expected.items() if len(ids) > 1}
            actual = {
                c.employee_id: [v.assignment_id for v in c.visits]
                for c in validate(*visits).conflicts
            }
            self.assertEqual(actual, expected)
