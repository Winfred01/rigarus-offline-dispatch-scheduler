"""Synthetic actual-worker consent: exact whole-day scope, no inferred approval."""

import unittest
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch

from rigarus_backend.daily_personnel_conflicts import DailyStaffedVisit
from rigarus_backend.daily_weekend_consent import (
    WeekendContext,
    WeekendConsentFact,
    WeekendCrewDay,
    validate_weekend_consent,
)
from rigarus_backend.daily_weekend_store import WeekendDecision

SAT = "2026-11-28"


def visit(**changes):
    return replace(
        DailyStaffedVisit("Proposal", 1, 1, 1, 1, SAT, 1, "Draft", True, (1, 2)),
        **changes,
    )


def fact(employee=1, state="Confirmed", context=None, **changes):
    return replace(
        WeekendConsentFact(
            context or WeekendContext(1, 1, 1, SAT, (1, 2)),
            employee,
            state,
            1,
            employee,
            "Synthetic employee decision",
            "Proposed",
        ),
        **changes,
    )


def check(visits=None, facts=(), **changes):
    return validate_weekend_consent(
        (visit(),) if visits is None else visits, facts, **changes
    )


class DailyWeekendPureTests(unittest.TestCase):
    def test_pending_partial_all_confirmed_subcheck_only(self):
        self.assertEqual(check().state, "Pending")
        self.assertEqual(check(facts=(fact(),)).state, "Pending")
        r = check(facts=(fact(), fact(2)))
        self.assertEqual(r.state, "Satisfied")
        self.assertEqual(r.validation_status, "Pending")
        self.assertFalse(r.applyable or r.publishable)

    def test_declined_wins_missing_stale_roster_and_partial_scope(self):
        old = WeekendContext(1, 1, 1, SAT, (1, 3))
        r = check(facts=(fact(state="Declined", context=old),), scope_complete=False)
        self.assertEqual(r.state, "Blocked")
        self.assertEqual(r.checks[0].members[0].reason, "ACTUAL_WORKER_DECLINED")

    def test_changed_roster_requires_remaining_workers_reconfirmation(self):
        r = check((visit(employee_ids=(1, 3)),), (fact(),))
        self.assertEqual(r.state, "Pending")
        self.assertEqual(
            r.checks[0].members[0].reason, "WEEKEND_ROSTER_CHANGED_RECONFIRM"
        )

    def test_removed_worker_refusal_not_required_anymore(self):
        v = visit(employee_ids=(2,))
        r = check(
            (v,),
            (
                fact(state="Declined"),
                fact(2, context=WeekendContext(1, 1, 1, SAT, (2,))),
            ),
        )
        self.assertEqual(r.state, "Satisfied")

    def test_work_project_crew_and_date_are_not_global_employee_permission(self):
        for change in (
            dict(work_item_id=2),
            dict(project_id=2),
            dict(crew_id=2),
            dict(local_date="2026-11-29"),
        ):
            self.assertEqual(
                check((visit(**change),), (fact(), fact(2))).state, "Pending"
            )

    def test_saved_revision_and_identity_require_review(self):
        facts = (
            fact(source_kind="FullDayDraft", source_id=1, source_revision=1),
            fact(2, source_kind="FullDayDraft", source_id=1, source_revision=1),
        )
        self.assertEqual(
            check((visit(record_kind="FullDayDraft"),), facts).state, "Satisfied"
        )
        for v in (
            visit(),
            visit(record_kind="FullDayDraft", revision=2),
            visit(record_kind="FullDayDraft", record_id=2),
        ):
            self.assertEqual(check((v,), facts).state, "Pending")

    def test_planned_consent_does_not_fabricate_saved_attendance(self):
        self.assertEqual(
            check((visit(record_kind="FullDayDraft"),), (fact(), fact(2))).state,
            "Pending",
        )

    def test_legacy_half_never_full_day_positive_known_refusal_still_blocks(self):
        for half in ("AM", "PM"):
            v = visit(record_kind="LegacyHalfDay", legacy_slot=half)
            self.assertEqual(check((v,), (fact(), fact(2))).state, "Pending")
            self.assertEqual(check((v,), (fact(state="Declined"),)).state, "Blocked")

    def test_unconfigured_empty_cancelled_and_weekday(self):
        for configured in (False, True):
            self.assertEqual(
                check((visit(staffing_configured=configured, employee_ids=()),)).state,
                "Pending",
            )
        self.assertEqual(
            check(
                (visit(record_kind="FullDayDraft", status="Cancelled"),),
                (fact(state="Declined"),),
            ).checks,
            (),
        )
        self.assertEqual(check((visit(local_date="2026-11-27"),)).state, "Satisfied")
        self.assertEqual(
            check(facts=(fact(), fact(2)), scope_complete=False).state, "Pending"
        )

    def test_strict_scope_ids_states_rosters_and_explicit_decisions(self):
        for make in (
            lambda: WeekendContext(True, 1, 1, SAT, (1,)),
            lambda: WeekendContext(1, 1, 1, "2026-02-30", (1,)),
            lambda: WeekendContext(1, 1, 1, "2026-11-27", (1,)),
            lambda: WeekendCrewDay(1, SAT, ()),
            lambda: WeekendCrewDay(1, SAT, (1, 1)),
            lambda: fact(state="Approved"),
            lambda: fact(employee=3),
            lambda: fact(source_kind="LegacyHalfDay"),
            lambda: WeekendDecision("Confirmed", False, True, "Synthetic"),
            lambda: WeekendDecision("Confirmed", True, False, "Synthetic"),
            lambda: WeekendDecision("Confirmed", 1, True, "Synthetic"),
            lambda: WeekendDecision("Pending", False, True, ""),
            lambda: check(facts=(fact(), fact())),
            lambda: check((visit(), visit())),
            lambda: check(facts=(fact(),) * 100001),
        ):
            with self.assertRaises(ValueError):
                make()

    def test_technical_membership_bounds_and_dense_linear_index(self):
        visits = tuple(
            visit(record_id=i, crew_id=i, employee_ids=(i,)) for i in range(1, 1001)
        )
        facts = tuple(
            fact(i, context=WeekendContext(1, 1, i, SAT, (i,))) for i in range(1, 1001)
        )
        self.assertEqual(check(visits, facts).state, "Satisfied")
        dense = tuple(
            fact(i, context=WeekendContext(1, 1, 1, SAT, tuple(range(1, 1001))))
            for i in range(1, 102)
        )
        with self.assertRaises(ValueError):
            check(facts=dense)

    def test_year_leap_dst_determinism_frozen_and_no_io(self):
        for day in (
            "2026-12-26",
            "2028-02-26",
            "2027-03-14",
            "2027-11-07",
            "9999-12-25",
        ):
            v = visit(local_date=day)
            ctx = WeekendContext(1, 1, 1, day, (1, 2))
            self.assertEqual(
                check((v,), (fact(context=ctx), fact(2, context=ctx))).state,
                "Satisfied",
            )
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
            patch("time.time", side_effect=AssertionError),
        ):
            self.assertEqual(
                check(facts=(fact(), fact(2))), check(facts=(fact(2), fact()))
            )
        with self.assertRaises(FrozenInstanceError):
            fact().state = "Declined"
