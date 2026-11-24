import random
import unittest
from dataclasses import FrozenInstanceError, asdict, replace
from itertools import permutations
from unittest.mock import patch

from rigarus_backend import capability_validation as module
from rigarus_backend.capability_validation import (
    CapabilityCrew,
    CapabilityWorkItem,
    CapabilityWorker,
    CapabilitySources,
    CapabilityRequirements,
    RequirementCell,
    QualificationCell,
    validate_capabilities,
)
from rigarus_backend.personnel_conflicts import StaffedVisit

DAY = "2026-11-23"


def visit(number=1, crew=1, ids=(1,), **kw):
    return replace(
        StaffedVisit(number, 1, 1, crew, DAY, "AM", "Draft", True, ids), **kw
    )


def worker(number=1, level=3, active=True, state="Available", day=DAY, half="AM"):
    return CapabilityWorker(number, active, level, ((day, half, state),))


def requirement(minimum=1, levels=(0, 0, 1), mode="Exact", qualifications=()):
    return CapabilityRequirements(minimum, levels, mode, qualifications)


def policy(req=None, work=1, day=DAY, half="AM"):
    return RequirementCell(work, day, half, req or requirement(), 1, True)


def proof(number=1, code="SYN-Q", state="Verified", day=DAY, half="AM"):
    return QualificationCell(number, code, day, half, state, 1, True)


def sources(**kw):
    return replace(
        CapabilitySources(
            (CapabilityCrew(1, "Civil", True),),
            (CapabilityWorkItem(1, 1, "Civil"),),
            (),
            (policy(),),
            (),
            (),
        ),
        **kw,
    )


def validate(visits=(visit(),), workers=(worker(),), source=None, **kw):
    return validate_capabilities(
        visits,
        workers,
        source or sources(),
        start_date=kw.pop("start_date", DAY),
        end_date=kw.pop("end_date", DAY),
        scope_complete=kw.pop("scope_complete", True),
        **kw,
    )


def counts(result, index=0):
    return {c.check: c for c in result.checks[index].counts}


class CapabilityValidationTests(unittest.TestCase):
    def test_normal_explicit_requirements_satisfied_subchecks_foreman_pending(self):
        r = validate()
        self.assertEqual(r.checks[0].crew_state, "Satisfied")
        self.assertTrue(all(c.state == "Satisfied" for c in r.checks[0].counts))
        self.assertEqual(r.state, "Pending")
        self.assertEqual(r.checks[0].foreman_state, "Pending")
        self.assertEqual(r.validation_status, "Pending")
        self.assertFalse(r.applyable or r.publishable)

    def test_no_policy_never_uses_default_staffing_or_level(self):
        r = validate(source=sources(requirements=()))
        self.assertTrue(
            all(c.required is None and c.state == "Pending" for c in r.checks[0].counts)
        )
        self.assertEqual(r.state, "Pending")

    def test_definite_shortage_and_unknown_possible_capacity_are_distinct(self):
        source = sources(requirements=(policy(requirement(2)),))
        r = validate(source=source)
        self.assertEqual(counts(r)["MinimumStaffing"].state, "Blocked")
        r = validate(
            visits=(visit(ids=(1, 2)),),
            workers=(worker(), worker(2, state="Unknown")),
            source=source,
        )
        c = counts(r)["MinimumStaffing"]
        self.assertEqual(
            (c.confirmed_employee_ids, c.possible_employee_ids, c.state),
            ((1,), (1, 2), "Pending"),
        )
        r = validate(
            visits=(visit(ids=(1, 2)),),
            workers=(worker(), worker(2, state="Unavailable")),
            source=source,
        )
        self.assertEqual(counts(r)["MinimumStaffing"].state, "Blocked")

    def test_explicit_exact_and_atleast_modes_no_default_hierarchy(self):
        for mode, expected in (("Exact", "Blocked"), ("AtLeast", "Satisfied")):
            r = validate(
                source=sources(
                    requirements=(policy(requirement(levels=(0, 1, 0), mode=mode)),)
                )
            )
            self.assertEqual(counts(r)["SkillsLevel2"].state, expected)

    def test_level_does_not_create_verified_qualification(self):
        source = sources(
            requirements=(policy(requirement(qualifications=(("SYN-Q", 1),))),)
        )
        self.assertEqual(
            counts(validate(source=source))["Qualification:SYN-Q"].state, "Pending"
        )
        for state, expected in (
            ("Verified", "Satisfied"),
            ("NotVerified", "Blocked"),
            ("Unknown", "Pending"),
        ):
            r = validate(source=replace(source, qualifications=(proof(state=state),)))
            self.assertEqual(counts(r)["Qualification:SYN-Q"].state, expected)

    def test_qualification_codes_have_no_case_or_other_equivalence(self):
        source = sources(
            requirements=(policy(requirement(qualifications=(("SYN-Q", 1),))),),
            qualifications=(proof(code="syn-q"), proof(code="SYN-OTHER")),
        )
        self.assertEqual(
            counts(validate(source=source))["Qualification:SYN-Q"].state, "Pending"
        )

    def test_inactive_unavailable_shared_workers_excluded_and_cancel_releases(self):
        for person in (worker(active=False), worker(state="Unavailable")):
            self.assertEqual(
                counts(validate(workers=(person,)))["MinimumStaffing"].state, "Blocked"
            )
        src = sources(
            crews=(CapabilityCrew(1, "Civil", True), CapabilityCrew(2, "Civil", True))
        )
        r = validate(visits=(visit(), visit(2, 2)), source=src)
        self.assertTrue(
            all(counts(r, i)["MinimumStaffing"].state == "Blocked" for i in (0, 1))
        )
        r = validate(visits=(visit(), visit(2, 2, status="Cancelled")), source=src)
        self.assertEqual(counts(r)["MinimumStaffing"].state, "Satisfied")

    def test_type_inactive_and_unmapped_or_missing_context(self):
        for crew, kind, expected in (
            (CapabilityCrew(1, "Tower", True), "Civil", "Blocked"),
            (CapabilityCrew(1, "Civil", False), "Civil", "Blocked"),
            (CapabilityCrew(1, "Civil", True), "Other", "Pending"),
        ):
            r = validate(
                source=sources(
                    crews=(crew,), work_items=(CapabilityWorkItem(1, 1, kind),)
                )
            )
            self.assertEqual(r.checks[0].crew_state, expected)
        self.assertEqual(
            validate(source=sources(crews=())).checks[0].crew_state, "Pending"
        )
        with self.assertRaises(ValueError):
            validate(source=sources(work_items=(CapabilityWorkItem(1, 99, "Civil"),)))

    def test_empty_unconfigured_no_active_and_partial_scope_do_not_pass(self):
        for visits in (
            (),
            (visit(ids=()),),
            (visit(ids=(), staffing_configured=False),),
            (visit(status="Cancelled"),),
        ):
            self.assertEqual(validate(visits=visits).state, "Pending")
        self.assertEqual(
            counts(validate(scope_complete=False))["MinimumStaffing"].state, "Pending"
        )
        self.assertEqual(
            counts(validate(workers=()))["MinimumStaffing"].state, "Pending"
        )

    def test_borrowing_rechecks_source_and_destination_independently(self):
        src = sources(
            crews=(CapabilityCrew(1, "Civil", True), CapabilityCrew(2, "Civil", True)),
            work_items=(
                CapabilityWorkItem(1, 1, "Civil"),
                CapabilityWorkItem(2, 2, "Civil"),
            ),
            requirements=(policy(requirement(2)), policy(work=2)),
        )
        before = (visit(ids=(1, 2)), visit(2, 2, (3,), work_item_id=2, project_id=2))
        people = (worker(), worker(2, 1), worker(3, 1))
        r = validate(before, people, src)
        self.assertEqual(counts(r)["SkillsLevel3"].state, "Satisfied")
        self.assertEqual(counts(r, 1)["SkillsLevel3"].state, "Blocked")
        after = (
            replace(before[0], employee_ids=(2,)),
            replace(before[1], employee_ids=(1, 3)),
        )
        r = validate(after, people, src)
        self.assertEqual(counts(r)["MinimumStaffing"].state, "Blocked")
        self.assertEqual(counts(r, 1)["SkillsLevel3"].state, "Satisfied")
        self.assertEqual(r.state, "Blocked")

    def test_exact_date_half_and_year_leap_dst_max(self):
        self.assertIsNone(
            counts(validate(visits=(visit(slot="PM"),)))["MinimumStaffing"].required
        )
        for day in (
            "2026-12-31",
            "2028-02-29",
            "2027-03-14",
            "2027-11-07",
            "9999-12-31",
        ):
            r = validate(
                (visit(local_date=day),),
                (worker(day=day),),
                sources(requirements=(policy(day=day),)),
                start_date=day,
                end_date=day,
            )
            self.assertEqual(counts(r)["MinimumStaffing"].state, "Satisfied")

    def test_determinism_immutability_and_pure_io_guards(self):
        inputs = (visit(ids=(1, 2)),)
        people = (worker(), worker(2))
        before = asdict(inputs[0])
        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("time.time", side_effect=AssertionError("clock")),
            patch("time.monotonic", side_effect=AssertionError("clock")),
        ):
            expected = validate(inputs, people)
            for order in permutations(people):
                self.assertEqual(validate(inputs, order), expected)
        self.assertEqual(asdict(inputs[0]), before)
        with self.assertRaises(FrozenInstanceError):
            expected.state = "Satisfied"
        with self.assertRaises(TypeError):
            replace(expected, publishable=True)

    def test_invalid_contract_duplicate_ids_and_bounds(self):
        for changes in (
            dict(minimum_members=0),
            dict(level_minimums=(1, 2)),
            dict(level_mode="Auto"),
            dict(qualification_minimums=(("SYN-Q", 1), ("SYN-Q", 2))),
            dict(level_minimums=(True, 0, 0)),
            dict(qualification_minimums=(("bad code", 1),)),
        ):
            with self.assertRaises(ValueError):
                replace(requirement(), **changes)
        for changes in (
            dict(company_confirmed=False),
            dict(change_id=0),
            dict(local_date="2027-02-29"),
        ):
            with self.assertRaises(ValueError):
                replace(policy(), **changes)
        for changes in (
            dict(workers=(worker(), worker())),
            dict(source=sources(requirements=(policy(), policy()))),
            dict(visits=(visit(), visit())),
        ):
            with self.assertRaises(ValueError):
                validate(**changes)
        with patch.object(module, "MAX_EVIDENCE", 2), self.assertRaises(ValueError):
            validate()
        with self.assertRaises(ValueError):
            validate(source=sources(requirements=(policy(day="2026-11-24"),)))

    def test_bounded_explanations_and_evaluation_limit(self):
        src = sources(
            crews=tuple(CapabilityCrew(i, "Civil", True) for i in range(1, 2001))
        )
        r = validate(tuple(visit(i, i) for i in range(1, 2001)), source=src)
        self.assertEqual(len(r.checks), 2000)
        self.assertEqual(sum(len(c.counts) for c in r.checks), 8000)
        with (
            patch.object(module, "MAX_EVIDENCE", 10000),
            self.assertRaisesRegex(ValueError, "evaluation"),
        ):
            validate(tuple(visit(i, i) for i in range(1, 2001)), source=src)

    def test_seeded_independent_minimum_count_oracle(self):
        rng = random.Random(25)
        for _ in range(50):
            workers = tuple(
                worker(
                    i,
                    rng.randint(1, 3),
                    rng.choice((True, False)),
                    rng.choice(("Available", "Unavailable", "Unknown")),
                )
                for i in range(1, 8)
            )
            minimum = rng.randint(1, 8)
            r = validate(
                (visit(ids=tuple(range(1, 8))),),
                workers,
                sources(requirements=(policy(requirement(minimum, levels=(0, 0, 0))),)),
            )
            definite = sum(
                w.active and w.availability[0][2] == "Available" for w in workers
            )
            possible = sum(
                w.active and w.availability[0][2] != "Unavailable" for w in workers
            )
            expected = (
                "Blocked"
                if possible < minimum
                else "Satisfied"
                if definite >= minimum
                else "Pending"
            )
            self.assertEqual(counts(r)["MinimumStaffing"].state, expected)
