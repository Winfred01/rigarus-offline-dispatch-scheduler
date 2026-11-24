import os
import sqlite3
import unittest
from contextlib import closing
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import date
from itertools import permutations
from unittest.mock import patch

import test_assignments
from rigarus_backend.recommendation_comparison import (
    CHECKS,
    ConstraintEvidence,
    ExplicitOption,
    ProposedSlot,
    compare_explicit_options,
)


def slot(day="2026-11-23", half="AM", *, states=None, complete=True):
    states = states or {}
    checks = CHECKS if date.fromisoformat(day).weekday() >= 5 else CHECKS[:-1]
    evidence = tuple(
        ConstraintEvidence(name, states.get(name, "Satisfied"))
        for name in checks
        if complete or name in states
    )
    return ProposedSlot(day, half, evidence)


def option(number=1, crew=1, slots=None):
    return ExplicitOption(number, 14, 6, crew, slots or (slot(),))


def compare(*options, **kwargs):
    return compare_explicit_options(
        14, 6, options, max_options=kwargs.pop("max_options", 3), **kwargs
    )


class RecommendationComparisonTests(unittest.TestCase):
    def test_c1_c2_c3_filter_before_limit_and_dual_sort(self):
        # C1 starts first but has an explicit gap. C2 finishes first. C3 is unsafe.
        c1 = option(1, 1, (slot(), slot("2026-11-25", "PM")))
        c2 = option(2, 2, (slot("2026-11-24", "AM"), slot("2026-11-24", "PM")))
        c3 = option(3, 3, (slot(states={"RigConflicts": "Blocked"}),))
        finish = compare(c1, c2, c3, max_options=1)
        start = compare(c3, c2, c1, order="EarliestStart")
        self.assertEqual([x.option.crew_id for x in finish.options], [2])
        self.assertEqual(finish.omitted_by_limit, 1)
        self.assertEqual([x.option.crew_id for x in start.options], [1, 2])
        self.assertEqual([x.option.crew_id for x in finish.excluded], [3])
        self.assertEqual(start.options[0].unplanned_half_days_between, 4)
        self.assertEqual(start.options[1].unplanned_half_days_between, 0)

    def test_each_known_hard_failure_excludes_entire_option(self):
        for check in CHECKS:
            with self.subTest(check=check):
                failed = slot("2026-11-28", states={check: "Blocked"})
                result = compare(option(slots=(failed,)))
                self.assertEqual(result.options, ())
                self.assertEqual(len(result.excluded), 1)
                explanation = next(
                    x for x in result.excluded[0].explanations if x.check == check
                )
                self.assertEqual(
                    (
                        explanation.local_date,
                        explanation.slot,
                        explanation.state,
                        explanation.source,
                    ),
                    (failed.local_date, "AM", "Blocked", "Supplied"),
                )

    def test_late_slot_conflict_is_not_hidden_by_safe_first_slot(self):
        result = compare(
            option(
                slots=(
                    slot(),
                    slot(half="PM", states={"PersonnelConflicts": "Blocked"}),
                )
            )
        )
        self.assertFalse(result.options)
        self.assertEqual(result.excluded[0].finish, ("2026-11-23", "PM"))

    def test_calendar_and_available_do_not_imply_driver_rig_or_qualification(self):
        states = {name: "Satisfied" for name in CHECKS[:3]}
        result = compare(option(slots=(slot(states=states, complete=False),)))
        row = result.options[0]
        self.assertEqual(row.evidence_status, "Pending")
        missing = {x.check for x in row.explanations if x.source == "Missing"}
        self.assertIn("ApprovedDriver", missing)
        self.assertIn("RigAvailability", missing)
        self.assertIn("Skills", missing)
        self.assertIn("Qualifications", missing)
        self.assertEqual(row.validation_status, "Pending")
        self.assertFalse(row.applyable or row.publishable)

    def test_even_all_supplied_satisfied_does_not_certify_or_enable_apply(self):
        result = compare(option())
        self.assertEqual(result.options[0].evidence_status, "AllSuppliedSatisfied")
        for record in (result, result.options[0]):
            self.assertEqual(record.validation_status, "Pending")
            self.assertFalse(record.applyable or record.publishable)
            with self.assertRaises(TypeError):
                replace(record, publishable=True)

    def test_weekend_consent_missing_pending_and_declined_are_distinct(self):
        missing = slot("2026-11-28", complete=False)
        result = compare(option(slots=(missing,)))
        reason = next(
            x for x in result.options[0].explanations if x.check == "WeekendConsent"
        )
        self.assertEqual((reason.state, reason.source), ("Pending", "Missing"))
        pending = slot("2026-11-28", states={"WeekendConsent": "Pending"})
        self.assertEqual(
            compare(option(slots=(pending,))).options[0].evidence_status, "Pending"
        )
        declined = slot("2026-11-28", states={"WeekendConsent": "Blocked"})
        self.assertFalse(compare(option(slots=(declined,))).options)
        self.assertFalse(compare(option(slots=(slot("2026-11-28"),))).publishable)

    def test_am_pm_order_is_local_and_independent(self):
        result = compare(
            option(1, slots=(slot(half="PM"),)), option(2, slots=(slot(),))
        )
        self.assertEqual([x.option.option_id for x in result.options], [2, 1])
        self.assertEqual(result.options[0].start, ("2026-11-23", "AM"))

    def test_ties_use_other_date_then_stable_crew_then_option_id(self):
        a = option(8, 3)
        b = option(7, 2)
        c = option(2, 2)
        for inputs in permutations((a, b, c)):
            self.assertEqual(
                [x.option.option_id for x in compare(*inputs).options], [2, 7, 8]
            )

    def test_snapshot_cell_evidence_and_input_order_do_not_change_result(self):
        a = slot()
        b = slot(half="PM")
        forward = option(slots=(a, b))
        reverse = option(slots=(replace(b, evidence=tuple(reversed(b.evidence))), a))
        before = asdict(reverse)
        self.assertEqual(compare(forward), compare(reverse))
        self.assertEqual(asdict(reverse), before)
        with self.assertRaises(FrozenInstanceError):
            reverse.crew_id = 9

    def test_empty_and_all_excluded_stay_empty_without_manual_fallback(self):
        self.assertEqual(compare().options, ())
        result = compare(option(slots=(slot(states={"ApprovedDriver": "Blocked"}),)))
        self.assertEqual((result.options, result.omitted_by_limit), ((), 0))
        self.assertFalse(result.applyable or result.publishable)

    def test_duplicate_option_slot_and_evidence_rejected_without_last_wins(self):
        with self.assertRaisesRegex(ValueError, "Option IDs"):
            compare(option(), option())
        with self.assertRaisesRegex(ValueError, "same proposed slot"):
            option(slots=(slot(), slot()))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            ProposedSlot(
                "2026-11-23",
                "AM",
                (
                    ConstraintEvidence("Skills", "Satisfied"),
                    ConstraintEvidence("Skills", "Blocked"),
                ),
            )

    def test_wrong_context_rejected_instead_of_mixing_projects(self):
        for changes in ({"work_item_id": 15}, {"project_id": 7}):
            with (
                self.subTest(changes=changes),
                self.assertRaisesRegex(ValueError, "parent Project"),
            ):
                compare(replace(option(), **changes))

    def test_strict_unknown_evidence_and_slot_values(self):
        for check, state in (
            ("HomeCrewMeansAttendance", "Satisfied"),
            ("Skills", "Unknown"),
            ("RigConflicts", True),
        ):
            with self.subTest(check=check, state=state), self.assertRaises(ValueError):
                ConstraintEvidence(check, state)
        for day, half in (
            ("2027-02-29", "AM"),
            ("2026-11-23T00:00:00Z", "AM"),
            ("2026-1-01", "AM"),
            ("2026-11-23", "FullDay"),
        ):
            with self.subTest(day=day, half=half), self.assertRaises(ValueError):
                ProposedSlot(day, half)
        with self.assertRaisesRegex(ValueError, "weekend slot"):
            ProposedSlot(
                "2026-11-23", "AM", (ConstraintEvidence("WeekendConsent", "Blocked"),)
            )

    def test_limits_and_strict_ids_no_bool_coercion(self):
        for value in (True, 0, -1, 1.0, "1", 2**53):
            with self.subTest(value=value), self.assertRaises(ValueError):
                option(crew=value)
        for maximum in (True, 0, 11, 1.0):
            with self.subTest(maximum=maximum), self.assertRaises(ValueError):
                compare(option(), max_options=maximum)
        with self.assertRaises(ValueError):
            compare_explicit_options(14, 6, [], max_options=3)
        with self.assertRaises(ValueError):
            compare(*(option(i) for i in range(1, 102)))
        self.assertEqual(
            compare(*(option(i) for i in range(1, 101))).omitted_by_limit, 97
        )
        with self.assertRaises(ValueError):
            compare(option(), order="WeightedSafetyOverride")
        with self.assertRaises(ValueError):
            option(slots=(slot("2028-01-01"), slot("2029-01-01")))

    def test_immutable_input_shapes_not_mutable_snapshots(self):
        with self.assertRaises(ValueError):
            ExplicitOption(1, 14, 6, 1, [slot()])
        with self.assertRaises(ValueError):
            ExplicitOption(1, 14, 6, 1, ())
        with self.assertRaises(ValueError):
            ProposedSlot("2026-11-23", "AM", [])

    def test_cross_year_leap_dst_and_max_date_are_timezone_independent(self):
        for days in (
            ("2026-12-31", "2027-01-01"),
            ("2028-02-28", "2028-02-29"),
            ("2027-03-13", "2027-03-14"),
            ("2027-11-06", "2027-11-07"),
            ("9999-12-31", "9999-12-31"),
        ):
            expected = None
            for zone in ("UTC", "America/Toronto", "America/Vancouver"):
                with (
                    self.subTest(days=days, zone=zone),
                    patch.dict(os.environ, TZ=zone),
                ):
                    result = compare(
                        option(slots=(slot(days[0], "AM"), slot(days[1], "PM")))
                    )
                    self.assertEqual(result.options[0].start, (days[0], "AM"))
                    self.assertEqual(result.options[0].finish, (days[1], "PM"))
                    if expected is not None:
                        self.assertEqual(result, expected)
                    expected = result

    def test_no_files_network_sql_or_input_mutation_during_comparison(self):
        proposed = option()
        before = asdict(proposed)
        with (
            patch("builtins.open", side_effect=AssertionError("file I/O")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("socket.socket", side_effect=AssertionError("network")),
        ):
            first = compare(proposed)
            self.assertEqual(compare(proposed), first)
        self.assertEqual(asdict(proposed), before)


class RecommendationCompatibilityTests(unittest.TestCase):
    def test_comparison_preserves_real_saved_synthetic_draft_calendar_and_ids(self):
        test_assignments.AssignmentTests.setUp(self)
        saved = self.client.post("/draft-assignments", json=self.draft).json()
        with closing(sqlite3.connect(self.database)) as connection:
            before = list(connection.iterdump())
        proposed = ExplicitOption(
            1,
            saved["work_item_id"],
            saved["project_id"],
            saved["crew_id"],
            (ProposedSlot(saved["local_date"], saved["slot"]),),
        )
        result = compare_explicit_options(
            saved["work_item_id"], saved["project_id"], (proposed,), max_options=3
        )
        self.assertEqual(result.options[0].evidence_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)
        self.assertEqual(
            self.client.get(f"/draft-assignments/{saved['id']}").json(), saved
        )
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(list(connection.iterdump()), before)
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
