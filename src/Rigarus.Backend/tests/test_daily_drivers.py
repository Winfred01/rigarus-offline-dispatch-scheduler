"""Synthetic pure full-date driver rules, with no host-time or resource inference."""

import unittest
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch

from rigarus_backend.daily_personnel_conflicts import DailyStaffedVisit
from rigarus_backend.daily_driver_validation import (
    DailyDriverFact,
    DailyDriverWorker,
    validate_daily_drivers,
)

DAY = "2026-11-23"


def visit(identity=1, crew=1, members=(1,), **changes):
    return replace(
        DailyStaffedVisit(
            "FullDayDraft", identity, 1, 1, crew, DAY, 1, "Draft", True, members
        ),
        **changes,
    )


def worker(identity=1, **changes):
    return DailyDriverWorker(
        identity,
        True,
        (
            replace(
                DailyDriverFact(DAY, "Active", True, True, "Current", "Available", 1),
                **changes,
            ),
        ),
    )


def validate(visits=None, workers=None, **changes):
    return validate_daily_drivers(
        visits if visits is not None else (visit(),),
        workers if workers is not None else (worker(),),
        **(dict(start_date=DAY, end_date=DAY, scope_complete=True) | changes),
    )


class DailyDriverPureTests(unittest.TestCase):
    def test_one_actual_daily_driver_satisfies_only_subcheck(self):
        result = validate()
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(result.checks[0].eligible_employee_ids, (1,))
        self.assertEqual(result.validation_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)

    def test_all_approval_states_and_missing_dates(self):
        for state, expected in (
            ("Active", "Satisfied"),
            ("Unverified", "Pending"),
            ("Suspended", "Blocked"),
            ("Expired", "Blocked"),
        ):
            with self.subTest(state=state):
                self.assertEqual(
                    validate(workers=(worker(approval_state=state),)).state, expected
                )
        self.assertEqual(
            validate(workers=(DailyDriverWorker(1, True, ()),)).state, "Pending"
        )

    def test_company_full_day_and_current_receipt_required(self):
        for changes in (
            dict(company_confirmed=False),
            dict(full_day_confirmed=False),
            dict(
                company_confirmed=False, full_day_confirmed=False, review_status="Stale"
            ),
            dict(
                company_confirmed=False,
                full_day_confirmed=False,
                review_status="NeedsReview",
                change_id=None,
            ),
        ):
            self.assertEqual(validate(workers=(worker(**changes),)).state, "Pending")

    def test_availability_is_independent_and_unknown_never_passes(self):
        self.assertEqual(
            validate(workers=(worker(availability_state="Unknown"),)).state, "Pending"
        )
        self.assertEqual(
            validate(workers=(worker(availability_state="Unavailable"),)).state,
            "Blocked",
        )

    def test_inactive_and_missing_master_context(self):
        self.assertEqual(
            validate(workers=(replace(worker(), active=False),)).state, "Blocked"
        )
        self.assertEqual(validate(workers=()).state, "Pending")

    def test_legacy_attendance_never_claims_full_day_presence(self):
        for half in ("AM", "PM"):
            legacy = visit(record_kind="LegacyHalfDay", legacy_slot=half)
            self.assertEqual(validate((legacy,)).state, "Pending")
        self.assertEqual(
            validate(
                (visit(record_kind="LegacyHalfDay", legacy_slot="AM"),),
                (worker(approval_state="Suspended"),),
            ).state,
            "Blocked",
        )

    def test_old_opposite_halves_and_new_day_collision_disqualify_driver(self):
        a = visit(record_kind="LegacyHalfDay", legacy_slot="AM")
        b = visit(2, 2, record_kind="LegacyHalfDay", legacy_slot="PM")
        self.assertEqual(validate((a, b)).state, "Blocked")
        self.assertEqual(validate((visit(), b)).state, "Blocked")

    def test_another_eligible_driver_does_not_clear_personnel_conflicts(self):
        result = validate((visit(members=(1, 2)), visit(2, 2)), (worker(), worker(2)))
        self.assertEqual(result.checks[0].state, "Satisfied")
        self.assertEqual(result.checks[0].eligible_employee_ids, (2,))
        self.assertEqual(result.personnel.state, "Blocked")
        self.assertFalse(result.applyable)

    def test_missing_alternative_pending_known_all_ineligible_blocked(self):
        self.assertEqual(
            validate(
                (visit(members=(1, 2)),), (worker(approval_state="Suspended"),)
            ).state,
            "Pending",
        )
        self.assertEqual(
            validate(
                (visit(members=(1, 2)),),
                (
                    worker(approval_state="Suspended"),
                    worker(2, approval_state="Expired"),
                ),
            ).state,
            "Blocked",
        )

    def test_configured_zero_and_unconfigured_rosters_differ(self):
        self.assertEqual(validate((visit(members=()),)).state, "Blocked")
        self.assertEqual(
            validate((visit(members=(), staffing_configured=False),)).state, "Pending"
        )
        self.assertEqual(validate((), ()).state, "Pending")

    def test_cancelled_releases_capacity_and_scope_gaps_pending(self):
        self.assertEqual(
            validate((visit(), visit(2, 2, status="Cancelled"))).state, "Satisfied"
        )
        self.assertEqual(validate(scope_complete=False).state, "Pending")
        other = visit(2, 2, members=(), staffing_configured=False)
        self.assertEqual(validate((visit(), other)).state, "Pending")
        self.assertEqual(
            validate((visit(), other), (worker(approval_state="Expired"),))
            .checks[0]
            .state,
            "Blocked",
        )

    def test_strict_facts_ids_dates_duplicates_and_limits(self):
        for changes in (
            dict(local_date="2026-02-30"),
            dict(approval_state="Verified"),
            dict(availability_state=""),
            dict(company_confirmed=1),
            dict(change_id=True),
            dict(change_id=None),
            dict(review_status="Stale"),
        ):
            with self.assertRaises(ValueError):
                worker(**changes)
        with self.assertRaises(ValueError):
            DailyDriverWorker(True, True, ())
        with self.assertRaises(ValueError):
            DailyDriverWorker(1, True, worker().facts * 2)
        with self.assertRaises(ValueError):
            validate(workers=(worker(), worker()))
        with self.assertRaises(ValueError):
            validate(workers=[worker()])
        with self.assertRaises(ValueError):
            validate(workers=(worker(local_date="2026-11-24"),))
        with self.assertRaises(ValueError):
            validate(workers=(worker(),) * 100001)

    def test_cross_year_leap_dst_and_final_date_use_local_dates(self):
        for day in (
            "2026-12-31",
            "2027-01-01",
            "2028-02-29",
            "2027-03-14",
            "9999-12-31",
        ):
            self.assertEqual(
                validate(
                    (visit(local_date=day),),
                    (worker(local_date=day),),
                    start_date=day,
                    end_date=day,
                ).state,
                "Satisfied",
            )

    def test_pure_frozen_deterministic_without_io(self):
        a, b = visit(), visit(2, 2, members=(2,))
        one, two = worker(), worker(2)
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
        ):
            self.assertEqual(validate((a, b), (one, two)), validate((b, a), (two, one)))
        with self.assertRaises(FrozenInstanceError):
            one.active = False

    def test_dense_worker_indexing_preserves_all_actual_checks(self):
        visits = tuple(visit(i, i, members=(i,)) for i in range(1, 1001))
        workers = tuple(worker(i) for i in range(1, 1001))
        result = validate(visits, workers)
        self.assertEqual(result.state, "Satisfied")
        self.assertEqual(len(result.checks), 1000)

    def test_dense_collisions_use_membership_index_and_block_all_drivers(self):
        identities = tuple(range(1, 1001))
        result = validate(
            (visit(members=identities), visit(2, 2, members=identities)),
            tuple(worker(i) for i in identities),
        )
        self.assertEqual(result.state, "Blocked")
        self.assertEqual(len(result.personnel.conflicts), 1000)
