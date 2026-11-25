"""Synthetic pure daily actual Rig safety, no default/eligibility inference."""

import unittest
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch

from test_daily_drivers import visit, DAY
from rigarus_backend.daily_rig_validation import (
    DailyRigMaster,
    RigCondition,
    RigVisit,
    validate_daily_rigs,
)


def observation(identity=1, crew=1, rig=1, **changes):
    return replace(
        RigVisit(visit(identity, crew), rig, rig, rig is not None, True, 0, 1),
        **changes,
    )


def validate(visits=None, rigs=None, conditions=(), **changes):
    return validate_daily_rigs(
        visits if visits is not None else (observation(),),
        rigs
        if rigs is not None
        else (DailyRigMaster(1, True, 1, 0), DailyRigMaster(2, True, None, 0)),
        conditions,
        **(dict(start_date=DAY, end_date=DAY, scope_complete=True) | changes),
    )


class DailyRigPureTests(unittest.TestCase):
    def test_condition_projection_bound_rejects_without_partial_result(self):
        periods = tuple(
            RigCondition(i, 1, "Inspection", "2026-01-01", "2026-12-31", "Active", 1)
            for i in range(1, 276)
        )
        with self.assertRaises(ValueError):
            validate(
                (observation(visit=visit(local_date="2026-01-01")),),
                conditions=periods,
                start_date="2026-01-01",
                end_date="2026-12-31",
            )

    def test_dense_indexed_distinct_resources_and_shared_resource_collision(self):
        observations = tuple(observation(i, i, i) for i in range(1, 1001))
        rigs = tuple(DailyRigMaster(i, True, None, 0) for i in range(1, 1001))
        self.assertEqual(validate(observations, rigs).state, "Satisfied")
        colliding = tuple(replace(o, actual_rig_id=1) for o in observations)
        result = validate(colliding, rigs)
        self.assertEqual(result.state, "Blocked")
        self.assertEqual(len(result.conflicts), 1)
        self.assertEqual(len(result.conflicts[0].visits), 1000)

    def test_explicit_operational_actual_rig_subchecks_not_dispatch(self):
        r = validate()
        self.assertEqual(r.state, "Satisfied")
        self.assertEqual(r.checks[0].driver_category_state, "Pending")
        self.assertEqual(r.validation_status, "Pending")
        self.assertFalse(r.applyable or r.publishable)

    def test_default_original_or_active_alone_never_actual_capacity(self):
        r = validate(
            (observation(rig=None, original_rig_id=1, operational_confirmed=False),)
        )
        self.assertEqual(r.state, "Pending")
        self.assertEqual(r.checks[0].default_rig_ids, (1,))
        self.assertIsNone(r.checks[0].observation.actual_rig_id)
        self.assertEqual(
            validate((observation(operational_confirmed=False),)).state, "Pending"
        )

    def test_same_rig_same_day_different_crews_blocked_all_references(self):
        r = validate((observation(), observation(2, 2)))
        self.assertEqual(r.state, "Blocked")
        self.assertEqual(len(r.conflicts), 1)
        self.assertEqual({ref.crew_id for ref in r.conflicts[0].visits}, {1, 2})
        self.assertTrue(all(c.occupancy_state == "Blocked" for c in r.checks))

    def test_different_rigs_or_days_and_cancelled_release(self):
        self.assertEqual(
            validate((observation(), observation(2, 2, 2))).state, "Satisfied"
        )
        self.assertEqual(
            validate(
                (
                    observation(),
                    observation(2, 2, visit=visit(2, 2, status="Cancelled")),
                )
            ).state,
            "Satisfied",
        )
        self.assertEqual(validate(()).state, "Pending")

    def test_legacy_half_occupies_whole_day_but_never_proves_readiness(self):
        for half in ("AM", "PM"):
            old = observation(
                visit=visit(record_kind="LegacyHalfDay", legacy_slot=half),
                full_day_confirmed=False,
                operational_confirmed=False,
            )
            self.assertEqual(validate((old,)).state, "Pending")
            self.assertEqual(validate((old, observation(2, 2))).state, "Blocked")
        a = observation(
            visit=visit(record_kind="LegacyHalfDay", legacy_slot="AM"),
            full_day_confirmed=False,
            operational_confirmed=False,
        )
        b = replace(a, visit=visit(2, 1, record_kind="LegacyHalfDay", legacy_slot="PM"))
        self.assertFalse(validate((a, b)).conflicts)

    def test_independent_maintenance_inspection_out_of_service_override_positive(self):
        periods = tuple(
            RigCondition(i, 1, kind, DAY, DAY, "Active", 1)
            for i, kind in enumerate(("Maintenance", "Inspection", "OutOfService"), 1)
        )
        r = validate(conditions=periods)
        self.assertEqual(r.state, "Blocked")
        self.assertEqual(r.checks[0].blocked_period_ids, (1, 2, 3))
        r = validate(conditions=(replace(periods[0], status="Cancelled"), *periods[1:]))
        self.assertEqual(r.checks[0].blocked_period_ids, (2, 3))

    def test_inactive_actual_blocks_but_inactive_original_does_not_block_replacement(
        self,
    ):
        rigs = (DailyRigMaster(1, False, 1, 0), DailyRigMaster(2, True, None, 0))
        self.assertEqual(validate(rigs=rigs).state, "Blocked")
        self.assertEqual(
            validate((observation(rig=2, original_rig_id=1),), rigs).state, "Satisfied"
        )

    def test_missing_context_scope_and_unknown_other_crew_pending_known_conflict_wins(
        self,
    ):
        self.assertEqual(validate(rigs=()).state, "Pending")
        self.assertEqual(validate(scope_complete=False).state, "Pending")
        unknown = observation(2, 2, None, operational_confirmed=False)
        self.assertEqual(
            validate((observation(), unknown)).checks[0].occupancy_state, "Pending"
        )
        self.assertEqual(
            validate(
                (
                    observation(),
                    observation(2, 2),
                    observation(3, 3, None, operational_confirmed=False),
                ),
                scope_complete=False,
            ).state,
            "Blocked",
        )

    def test_context_or_condition_revision_stale_never_confirms(self):
        self.assertEqual(validate((observation(context_stale=True),)).state, "Pending")
        self.assertEqual(
            validate(rigs=(DailyRigMaster(1, True, 1, 1),)).state, "Pending"
        )

    def test_stale_recorded_date_reserves_capacity_even_current_date_outside_horizon(
        self,
    ):
        stale = observation(
            visit=visit(local_date="2027-01-01"),
            recorded_date=DAY,
            recorded_crew_id=1,
            context_stale=True,
        )
        self.assertEqual(validate((stale, observation(2, 2))).state, "Blocked")
        self.assertFalse(validate((replace(stale, recorded_crew_id=2),)).conflicts)

    def test_invalid_ids_dates_confirmation_duplicates_and_workload(self):
        for make in (
            lambda: DailyRigMaster(True, True, None, 0),
            lambda: DailyRigMaster(1, 1, None, 0),
            lambda: replace(observation(), condition_revision=-1),
            lambda: replace(observation(), operational_confirmed=1),
            lambda: replace(observation(), recorded_date=DAY),
            lambda: RigCondition(1, 1, "Repair", DAY, DAY, "Active", 1),
            lambda: RigCondition(1, 1, "Inspection", "2026-02-30", DAY, "Active", 1),
            lambda: validate((observation(), observation())),
            lambda: validate(rigs=(DailyRigMaster(1, True, None, 0),) * 100001),
        ):
            with self.assertRaises(ValueError):
                make()

    def test_local_year_leap_dst_last_date_and_frozen_pure_determinism(self):
        for day in (
            "2026-12-31",
            "2027-01-01",
            "2028-02-29",
            "2027-03-14",
            "9999-12-31",
        ):
            self.assertEqual(
                validate(
                    (observation(visit=visit(local_date=day)),),
                    start_date=day,
                    end_date=day,
                ).state,
                "Satisfied",
            )
        a, b = observation(), observation(2, 2, 2)
        with (
            patch("builtins.open", side_effect=AssertionError),
            patch("socket.socket", side_effect=AssertionError),
            patch("sqlite3.connect", side_effect=AssertionError),
            patch("time.time", side_effect=AssertionError),
        ):
            self.assertEqual(validate((a, b)), validate((b, a)))
        with self.assertRaises(FrozenInstanceError):
            a.actual_rig_id = 2
