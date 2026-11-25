"""Pure daily capacity upper bounds and independent qualification evidence."""

import unittest
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch

from test_daily_drivers import visit, DAY
from rigarus_backend.capability_validation import (
    CapabilityRequirements,
    CapabilityCrew,
    CapabilityWorkItem,
)
from rigarus_backend.daily_capability_validation import (
    DailyCapabilityWorker,
    DailyRequirement,
    DailyQualification,
    DailyCapabilitySources,
    validate_daily_capabilities,
)


def worker(identity=1, level=2, state="Available", **changes):
    return replace(
        DailyCapabilityWorker(identity, True, level, ((DAY, state),)), **changes
    )


def policy(minimum=1, levels=(0, 1, 0), mode="Exact", codes=()):
    return DailyRequirement(
        1, DAY, CapabilityRequirements(minimum, levels, mode, codes), 1
    )


def proof(state="Verified", identity=1, code="SYN-Q"):
    return DailyQualification(identity, code, DAY, state, 1, True)


def validate(visits=None, workers=None, policies=None, proofs=(), **changes):
    sources = DailyCapabilitySources(
        (CapabilityCrew(1, "Civil", True), CapabilityCrew(2, "Civil", True)),
        (CapabilityWorkItem(1, 1, "Civil"),),
        policies if policies is not None else (policy(),),
        proofs,
    )
    return validate_daily_capabilities(
        visits if visits is not None else (visit(),),
        workers if workers is not None else (worker(),),
        sources,
        **(dict(start_date=DAY, end_date=DAY, scope_complete=True) | changes),
    )


class DailyCapabilityPureTests(unittest.TestCase):
    def test_explicit_met_counts_remain_pending_foreman_and_false_flags(self):
        r = validate()
        self.assertTrue(all(c.state == "Satisfied" for c in r.checks[0].counts))
        self.assertEqual(r.state, "Pending")
        self.assertEqual(r.checks[0].foreman_state, "Pending")
        self.assertFalse(r.applyable or r.publishable)

    def test_minimum_known_shortfall_and_no_default_policy(self):
        self.assertEqual(validate(policies=(policy(2),)).state, "Blocked")
        r = validate(policies=())
        self.assertTrue(
            all(c.required is None and c.state == "Pending" for c in r.checks[0].counts)
        )

    def test_exact_levels_and_explicit_at_least_counting(self):
        r = validate(workers=(worker(level=3),), policies=(policy(levels=(0, 1, 0)),))
        self.assertEqual(r.state, "Blocked")
        self.assertEqual(
            validate(
                workers=(worker(level=3),),
                policies=(policy(levels=(1, 1, 1), mode="AtLeast"),),
            ).state,
            "Pending",
        )
        r = validate(
            visits=(visit(members=(1, 2, 3)),),
            workers=tuple(worker(i, i) for i in (1, 2, 3)),
            policies=(policy(3, (1, 1, 1)),),
        )
        self.assertTrue(all(c.state == "Satisfied" for c in r.checks[0].counts))

    def test_level_is_not_qualification_and_qualification_is_not_level(self):
        req = policy(codes=(("SYN-Q", 1),))
        for state, expected in (
            (None, "Pending"),
            ("Unknown", "Pending"),
            ("NotVerified", "Blocked"),
            ("Verified", "Satisfied"),
        ):
            r = validate(
                policies=(req,), proofs=() if state is None else (proof(state),)
            )
            self.assertEqual(r.checks[0].counts[-1].state, expected)
        self.assertEqual(
            validate(
                workers=(worker(level=1),), policies=(req,), proofs=(proof(),)
            ).state,
            "Blocked",
        )

    def test_exact_codes_and_independent_overlapping_qualification_minima(self):
        req = policy(codes=(("SYN-Q", 1), ("syn-q", 1)))
        self.assertEqual(
            validate(policies=(req,), proofs=(proof(),)).checks[0].counts[-1].state,
            "Pending",
        )
        self.assertTrue(
            all(
                c.state == "Satisfied"
                for c in validate(
                    policies=(req,), proofs=(proof(), proof(code="syn-q"))
                )
                .checks[0]
                .counts
            )
        )

    def test_unknown_available_possible_not_confirmed_and_unavailable_excluded(self):
        r = validate(workers=(worker(state="Unknown"),))
        self.assertEqual(r.checks[0].counts[0].possible_employee_ids, (1,))
        self.assertEqual(r.checks[0].counts[0].confirmed_employee_ids, ())
        self.assertEqual(
            validate(workers=(worker(state="Unavailable"),)).state, "Blocked"
        )
        self.assertEqual(validate(workers=(worker(active=False),)).state, "Blocked")

    def test_unknown_master_possible_levels_but_known_roster_upper_bound(self):
        self.assertEqual(validate(workers=()).checks[0].counts[2].state, "Pending")
        self.assertEqual(validate(workers=(), policies=(policy(2),)).state, "Blocked")

    def test_configured_zero_versus_unconfigured(self):
        self.assertEqual(validate(visits=(visit(members=()),)).state, "Blocked")
        self.assertEqual(
            validate(visits=(visit(members=(), staffing_configured=False),)).state,
            "Pending",
        )
        self.assertEqual(validate(visits=()).state, "Pending")

    def test_legacy_attendance_and_scope_gaps_never_confirm_daily_capacity(self):
        old = visit(record_kind="LegacyHalfDay", legacy_slot="PM")
        r = validate(visits=(old,))
        self.assertTrue(all(c.state == "Pending" for c in r.checks[0].counts))
        self.assertTrue(
            all(
                c.state == "Pending"
                for c in validate(scope_complete=False).checks[0].counts
            )
        )

    def test_personnel_collision_and_cancelled_release(self):
        second = visit(2, 2)
        self.assertEqual(validate(visits=(visit(), second)).state, "Blocked")
        self.assertTrue(
            all(
                c.state == "Satisfied"
                for c in validate(visits=(visit(), replace(second, status="Cancelled")))
                .checks[0]
                .counts
            )
        )

    def test_crew_context_mismatch_inactive_parent_and_open_mapping(self):
        s = DailyCapabilitySources(
            (CapabilityCrew(1, "Tower", True),),
            (CapabilityWorkItem(1, 1, "Civil"),),
            (policy(),),
            (),
        )
        args = dict(start_date=DAY, end_date=DAY, scope_complete=True)
        self.assertEqual(
            validate_daily_capabilities((visit(),), (worker(),), s, **args).state,
            "Blocked",
        )
        s = replace(s, crews=(CapabilityCrew(1, "Civil", False),))
        self.assertEqual(
            validate_daily_capabilities((visit(),), (worker(),), s, **args).state,
            "Blocked",
        )
        with self.assertRaises(ValueError):
            validate_daily_capabilities((visit(project_id=2),), (worker(),), s, **args)

    def test_invalid_duplicates_and_workload_bounds(self):
        for make in (
            lambda: replace(worker(), employee_id=True),
            lambda: replace(worker(), skill_level=0),
            lambda: replace(
                worker(), availability=((DAY, "Available"), (DAY, "Unknown"))
            ),
            lambda: replace(proof(), full_day_confirmed=False),
            lambda: replace(policy(), requirements=None),
            lambda: validate(workers=(worker(), worker())),
            lambda: validate(policies=(policy(), policy())),
            lambda: validate(proofs=(proof(), proof())),
            lambda: validate(workers=(worker(),) * 100001),
        ):
            with self.assertRaises(ValueError):
                make()

    def test_pure_frozen_and_deterministic_no_io(self):
        a, b = worker(), worker(2)
        v = visit(members=(1, 2))
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
            patch("time.time", side_effect=AssertionError),
        ):
            self.assertEqual(validate((v,), (a, b)), validate((v,), (b, a)))
        with self.assertRaises(FrozenInstanceError):
            a.active = False

    def test_local_cross_year_leap_dst_final_date(self):
        for day in (
            "2026-12-31",
            "2027-01-01",
            "2028-02-29",
            "2027-03-14",
            "9999-12-31",
        ):
            r = validate(
                (visit(local_date=day),),
                (replace(worker(), availability=((day, "Available"),)),),
                (replace(policy(), local_date=day),),
                start_date=day,
                end_date=day,
            )
            self.assertTrue(all(c.state == "Satisfied" for c in r.checks[0].counts))
