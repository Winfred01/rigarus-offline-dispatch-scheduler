import unittest
from dataclasses import FrozenInstanceError, asdict, replace
from itertools import permutations
from unittest.mock import patch

from rigarus_backend import driver_eligibility as module
from rigarus_backend.driver_eligibility import (
    DriverApprovalDraft,
    DriverCell,
    DriverWorker,
    validate_drivers,
)
from rigarus_backend.personnel_conflicts import StaffedVisit

DAY = "2026-11-23"


def visit(number=1, crew=1, employees=(1,), **changes):
    return replace(
        StaffedVisit(number, 1, 1, crew, DAY, "AM", "Draft", True, employees), **changes
    )


def worker(number=1, active=True, available="Available", day=DAY, half="AM"):
    return DriverWorker(number, active, ((day, half, available),))


def cell(number=1, state="Active", day=DAY, half="AM"):
    return DriverCell(number, day, half, state, number, True)


def validate(visits=(visit(),), workers=(worker(),), cells=(cell(),), **kw):
    return validate_drivers(
        visits,
        workers,
        cells,
        start_date=kw.pop("start_date", DAY),
        end_date=kw.pop("end_date", DAY),
        scope_complete=kw.pop("scope_complete", True),
        **kw,
    )


class DriverEligibilityTests(unittest.TestCase):
    def test_bounded_scale_has_one_assessment_per_actual_membership(self):
        ids = tuple(range(1, 2001))
        r = validate(
            visits=(visit(employees=ids), visit(2, 2, employees=ids)),
            workers=tuple(worker(i) for i in ids),
            cells=tuple(cell(i) for i in ids),
        )
        self.assertEqual(r.state, "Blocked")
        self.assertEqual(sum(len(c.workers) for c in r.checks), 4000)

    def test_actual_active_available_approved_driver_only_satisfies_this_check(self):
        r = validate()
        self.assertEqual(r.state, "Satisfied")
        self.assertEqual(r.checks[0].eligible_employee_ids, (1,))
        self.assertEqual(r.validation_status, "Pending")
        self.assertFalse(r.applyable or r.publishable)

    def test_unverified_missing_and_statuses(self):
        for cells in ((), (cell(state="Unverified"),)):
            self.assertEqual(validate(cells=cells).state, "Pending")
        for state in ("Suspended", "Expired"):
            r = validate(cells=(cell(state=state),))
            self.assertEqual(r.state, "Blocked")
            self.assertIn(
                "DRIVER_APPROVAL_" + state.upper(), r.checks[0].workers[0].reasons
            )

    def test_availability_and_active_are_independent(self):
        self.assertEqual(validate(workers=(worker(active=False),)).state, "Blocked")
        self.assertEqual(
            validate(workers=(worker(available="Unavailable"),)).state, "Blocked"
        )
        self.assertEqual(
            validate(workers=(worker(available="Unknown"),)).state, "Pending"
        )
        self.assertEqual(validate(workers=()).state, "Pending")

    def test_empty_unconfigured_no_active_and_home_roster_not_counted(self):
        for visits in (
            (),
            (visit(employees=()),),
            (visit(employees=(), staffing_configured=False),),
            (visit(status="Cancelled"),),
        ):
            self.assertEqual(validate(visits=visits).state, "Pending")
        self.assertEqual(validate(visits=(visit(employees=(2,)),)).state, "Pending")

    def test_only_eligible_actual_worker_counts_and_pending_alternatives(self):
        r = validate(
            visits=(visit(employees=(1, 2)),),
            workers=(worker(), worker(2)),
            cells=(cell(), cell(2, "Suspended")),
        )
        self.assertEqual(r.checks[0].eligible_employee_ids, (1,))
        r = validate(
            visits=(visit(employees=(1, 2)),),
            workers=(worker(), worker(2)),
            cells=(cell(1, "Expired"),),
        )
        self.assertEqual(r.state, "Pending")

    def test_partial_scope_cannot_satisfy_but_known_disqualification_blocks(self):
        self.assertEqual(validate(scope_complete=False).state, "Pending")
        self.assertEqual(
            validate(cells=(cell(state="Suspended"),), scope_complete=False).state,
            "Blocked",
        )

    def test_shared_driver_cannot_satisfy_two_crews_and_cancel_releases(self):
        visits = (visit(), visit(2, 2))
        self.assertEqual(validate(visits=visits).state, "Blocked")
        self.assertTrue(
            all(
                "DRIVER_DOUBLE_BOOKED" in c.workers[0].reasons
                for c in validate(visits=visits).checks
            )
        )
        self.assertEqual(
            validate(visits=(visits[0], replace(visits[1], status="Cancelled"))).state,
            "Satisfied",
        )

    def test_borrowing_sole_driver_rechecks_source_and_destination(self):
        before = (visit(employees=(1, 2)), visit(2, 2, employees=(3,)))
        people = (worker(), worker(2), worker(3))
        approvals = (cell(), cell(2, "Suspended"), cell(3, "Suspended"))
        r = validate(visits=before, workers=people, cells=approvals)
        self.assertEqual([c.state for c in r.checks], ["Satisfied", "Blocked"])
        after = (
            replace(before[0], employee_ids=(2,)),
            replace(before[1], employee_ids=(1, 3)),
        )
        r = validate(visits=after, workers=people, cells=approvals)
        self.assertEqual([c.state for c in r.checks], ["Blocked", "Satisfied"])
        self.assertFalse(r.publishable)

    def test_exact_half_and_date_only_no_status_carry(self):
        self.assertEqual(validate(visits=(visit(slot="PM"),)).state, "Pending")
        self.assertEqual(
            validate(
                visits=(visit(local_date="2026-11-24"),),
                start_date=DAY,
                end_date="2026-11-24",
            ).state,
            "Pending",
        )

    def test_deterministic_frozen_no_io(self):
        visits = (visit(), visit(2, 2))
        before = asdict(visits[0])
        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("time.time", side_effect=AssertionError("clock")),
        ):
            expected = validate(visits=visits)
            for order in permutations(visits):
                self.assertEqual(validate(visits=order), expected)
        self.assertEqual(asdict(visits[0]), before)
        with self.assertRaises(FrozenInstanceError):
            expected.state = "Satisfied"
        with self.assertRaises(TypeError):
            replace(expected, publishable=True)

    def test_invalid_duplicate_evidence_and_bounds(self):
        for cells, workers in (
            ((cell(), cell()), (worker(),)),
            ((cell(),), (worker(), worker())),
        ):
            with self.assertRaises(ValueError):
                validate(cells=cells, workers=workers)
        with patch.object(module, "MAX_EVIDENCE", 1), self.assertRaises(ValueError):
            validate()
        for args in (
            (0, DAY, "AM", "Active", 1),
            (1, "2027-02-29", "AM", "Active", 1),
            (1, DAY, "FullDay", "Active", 1),
            (1, DAY, "AM", "Approved", 1),
        ):
            with self.assertRaises(ValueError):
                DriverCell(*args, True)
        for value in (1, "yes", None, False):
            with self.assertRaises(ValueError):
                DriverApprovalDraft(
                    DAY, DAY, "AM", "Active", value, "Synthetic reference"
                )

    def test_range_draft_invalid_and_half_day_boundary(self):
        draft = DriverApprovalDraft(
            "2028-02-28", "2028-03-01", "FullDay", "Active", True, " Synthetic ref "
        )
        self.assertEqual(len(draft.cells()), 6)
        self.assertEqual(draft.reference, "Synthetic ref")
        for changes in (
            dict(reference=""),
            dict(state="Approved"),
            dict(start_date="2028-02-30"),
            dict(end_date="2029-12-31"),
            dict(slot="night"),
        ):
            with self.assertRaises(ValueError):
                replace(draft, **changes)

    def test_local_year_leap_dst_and_max(self):
        for day in (
            "2026-12-31",
            "2028-02-29",
            "2027-03-14",
            "2027-11-07",
            "9999-12-31",
        ):
            self.assertEqual(
                validate(
                    visits=(visit(local_date=day),),
                    workers=(worker(day=day),),
                    cells=(cell(day=day),),
                    start_date=day,
                    end_date=day,
                ).state,
                "Satisfied",
            )
