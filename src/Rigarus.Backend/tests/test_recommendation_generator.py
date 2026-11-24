import os
import random
import sqlite3
import unittest
from contextlib import closing
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import date
from itertools import permutations, product
from unittest.mock import patch

import test_assignments
from rigarus_backend.recommendation_comparison import (
    CHECKS,
    ConstraintEvidence,
    ProposedSlot,
)
from rigarus_backend.recommendation_generator import (
    CrewOccupancySnapshot,
    DateSlot,
    GenerationRequest,
    generate_and_compare,
    generate_candidate,
)
from rigarus_backend.work_calendars import WorkCalendar, WorkCalendarCell


def cells(*keys, state="Working"):
    return tuple(WorkCalendarCell(day, half, state) for day, half in keys)


CONTINUOUS = (
    ("2026-11-23", "AM"),
    ("2026-11-23", "PM"),
    ("2026-11-24", "AM"),
    ("2026-11-24", "PM"),
)
GAPPED = (
    ("2026-11-23", "AM"),
    ("2026-11-25", "PM"),
    ("2026-11-26", "AM"),
    ("2026-11-27", "PM"),
)


def request(keys=CONTINUOUS, **changes):
    values = dict(
        option_id=1,
        work_item_id=14,
        project_id=6,
        crew_id=7,
        required_crew_count=1,
        confirmed_remaining_half_days=4,
        remaining_confirmed_by_operator=True,
        earliest_start_date="2026-11-23",
        horizon_end_date="2026-11-27",
        crew_calendar=WorkCalendar("Crew", 7, cells(*keys)),
        project_calendar=WorkCalendar("Project", 6, cells(*keys)),
    )
    return GenerationRequest(**{**values, **changes})


def compare(*requests, **kwargs):
    return generate_and_compare(
        14, 6, requests, max_options=kwargs.pop("max_options", 3), **kwargs
    )


def evidence(day, half="AM", **states):
    return ProposedSlot(
        day,
        half,
        tuple(ConstraintEvidence(name, state) for name, state in states.items()),
    )


class GeneratorTests(unittest.TestCase):
    def test_evidence_order_is_canonical_and_empty_capacity_explains_missing_checks(
        self,
    ):
        e = evidence("2026-11-23", Skills="Pending", ApprovedDriver="Blocked")
        forward = request(slot_evidence=(e,))
        reverse = replace(
            forward, slot_evidence=(replace(e, evidence=tuple(reversed(e.evidence))),)
        )
        self.assertEqual(generate_candidate(forward), generate_candidate(reverse))
        empty = generate_candidate(request(keys=()))
        self.assertTrue(
            any(
                x.check == "CrewCalendar" and x.state == "Pending"
                for x in empty.missing_evidence
            )
        )
        weekend = generate_candidate(
            request(
                keys=(("2026-11-28", "AM"),),
                earliest_start_date="2026-11-28",
                horizon_end_date="2026-11-28",
            )
        )
        self.assertTrue(
            any(
                x.check == "WeekendConsent" and x.source == "Missing"
                for x in weekend.missing_evidence
            )
        )

    def test_reproducible_example_generates_then_sorts(self):
        from rigarus_backend.recommendation_example import synthetic_requests

        result = compare(*synthetic_requests())
        self.assertEqual([x.option.crew_id for x in result.comparison.options], [2, 1])
        self.assertEqual(
            result.candidates[0].proposed_finish, DateSlot("2026-11-27", "PM")
        )

    def test_shared_project_conflicts_rejected_and_empty_unknown_equivalent(self):
        r = request()
        conflicting = replace(
            r, option_id=2, project_calendar=WorkCalendar("Project", 6)
        )
        with self.assertRaisesRegex(ValueError, "shared Project"):
            compare(r, conflicting)
        unknown = request(keys=())
        explicit_unknown = replace(
            unknown,
            option_id=2,
            project_calendar=WorkCalendar(
                "Project", 6, cells(CONTINUOUS[0], state="Unknown")
            ),
        )
        self.assertEqual(compare(unknown, explicit_unknown).comparison.options, ())

    def test_100_scenarios_are_bounded_and_limit_reports_omissions(self):
        r = request()
        result = compare(
            *(replace(r, option_id=i) for i in range(1, 101)), max_options=10
        )
        self.assertEqual(len(result.candidates), 100)
        self.assertEqual(result.comparison.omitted_by_limit, 90)
        self.assertEqual(
            [x.option.option_id for x in result.comparison.options], list(range(1, 11))
        )

    def test_continuous_duration_generates_actual_dates_and_slots(self):
        result = generate_candidate(request())
        self.assertEqual(result.proposed_start, DateSlot("2026-11-23", "AM"))
        self.assertEqual(result.proposed_finish, DateSlot("2026-11-24", "PM"))
        self.assertEqual(
            (result.generated_half_days, result.unfilled_half_days), (4, 0)
        )
        self.assertEqual(tuple(x.key for x in result.slots), CONTINUOUS)
        self.assertEqual((len(result.scanned), result.skipped), (4, ()))
        self.assertEqual(result.status, "Validation pending")
        self.assertIsNotNone(result.option)

    def test_gaps_accumulate_without_reset_and_explain_tuesday_closure(self):
        crew = cells(*GAPPED) + cells(
            ("2026-11-24", "AM"), ("2026-11-24", "PM"), state="NotWorking"
        )
        result = generate_candidate(
            request(GAPPED, crew_calendar=WorkCalendar("Crew", 7, crew))
        )
        self.assertEqual(tuple(x.key for x in result.slots), GAPPED)
        self.assertEqual(result.proposed_finish, DateSlot("2026-11-27", "PM"))
        self.assertEqual((len(result.scanned), len(result.skipped)), (10, 6))
        tuesday = [x for x in result.skipped if x.calendar.local_date == "2026-11-24"]
        self.assertEqual(len(tuesday), 2)
        self.assertTrue(all("CREW_CALENDAR_NOTWORKING" in x.reasons for x in tuesday))
        self.assertEqual(result.calendar_matches, 4)

    def test_all_closed_and_empty_calendars_have_no_fake_finish(self):
        for state in ("Unknown", "NotWorking"):
            result = generate_candidate(
                request(
                    crew_calendar=WorkCalendar(
                        "Crew", 7, cells(*CONTINUOUS, state=state)
                    )
                )
            )
            self.assertEqual(result.status, "Needs Review")
            self.assertEqual(
                (result.slots, result.generated_half_days, result.unfilled_half_days),
                ((), 0, 4),
            )
            self.assertIsNone(result.proposed_start)
            self.assertIsNone(result.proposed_finish)
            self.assertIsNone(result.option)
            self.assertIn("INSUFFICIENT_CAPACITY_WITHIN_HORIZON", result.review_reasons)
            self.assertEqual(len(result.scanned), 10)
        self.assertEqual(generate_candidate(request(keys=())).calendar_unknowns, 10)

    def test_all_nine_calendar_pairs_reuse_closure_conflict_and_unknown_semantics(self):
        for crew, project in product(("Working", "NotWorking", "Unknown"), repeat=2):
            with self.subTest(crew=crew, project=project):
                result = generate_candidate(
                    request(
                        confirmed_remaining_half_days=1,
                        horizon_end_date="2026-11-23",
                        crew_calendar=WorkCalendar(
                            "Crew", 7, cells(CONTINUOUS[0], state=crew)
                        ),
                        project_calendar=WorkCalendar(
                            "Project", 6, cells(CONTINUOUS[0], state=project)
                        ),
                    )
                )
                self.assertEqual(
                    result.generated_half_days, int(crew == project == "Working")
                )
                first = result.scanned[0]
                self.assertEqual(first.calendar.project_id, 6)
                self.assertEqual(
                    "CALENDAR_CONFLICT" in first.reasons,
                    {crew, project} == {"Working", "NotWorking"},
                )
                self.assertEqual(
                    first.calendar.status,
                    "Blocked"
                    if "NotWorking" in (crew, project)
                    else "Pending"
                    if "Unknown" in (crew, project)
                    else "Matched",
                )

    def test_partial_capacity_keeps_accumulation_and_unfilled_no_complete_option(self):
        r = request(keys=CONTINUOUS[:2])
        result = compare(r)
        candidate = result.candidates[0]
        self.assertEqual(
            (candidate.generated_half_days, candidate.unfilled_half_days), (2, 2)
        )
        self.assertEqual(candidate.proposed_start, DateSlot("2026-11-23", "AM"))
        self.assertIsNone(candidate.proposed_finish)
        self.assertEqual(result.comparison.options, ())
        self.assertTrue(candidate.missing_evidence)

    def test_weekend_missing_pending_and_declined_never_shorten_dates(self):
        keys = (("2026-11-28", "AM"), ("2026-11-30", "AM"))
        r = request(
            keys,
            earliest_start_date="2026-11-28",
            horizon_end_date="2026-11-30",
            confirmed_remaining_half_days=1,
        )
        for state in (None, "Pending", "Blocked"):
            with self.subTest(state=state):
                supplied = (
                    ()
                    if state is None
                    else (evidence(keys[0][0], WeekendConsent=state),)
                )
                result = generate_candidate(replace(r, slot_evidence=supplied))
                self.assertEqual(result.proposed_finish, DateSlot("2026-11-30", "AM"))
                self.assertIn(
                    "WEEKEND_CONSENT_NOT_CONFIRMED", result.skipped[0].reasons
                )
        approved = generate_candidate(
            replace(
                r, slot_evidence=(evidence(keys[0][0], WeekendConsent="Satisfied"),)
            )
        )
        self.assertEqual(approved.proposed_finish, DateSlot(*keys[0]))
        self.assertFalse(approved.publishable or approved.applyable)

    def test_known_occupancy_blocks_even_same_workitem_and_coverage_missing_is_pending(
        self,
    ):
        occupied = CrewOccupancySnapshot(
            7, "2026-11-23", "2026-11-23", (DateSlot(*CONTINUOUS[0]),)
        )
        result = generate_candidate(
            request(confirmed_remaining_half_days=2, occupancy=occupied)
        )
        self.assertEqual(tuple(x.key for x in result.slots), CONTINUOUS[1:3])
        self.assertIn("CONSTRAINT_BLOCKED:CrewOccupancy", result.skipped[0].reasons)
        states = [
            next(x.state for x in slot.evidence if x.check == "CrewOccupancy")
            for slot in result.slots
        ]
        self.assertEqual(states, ["Satisfied", "Pending"])
        self.assertTrue(
            any(x.check == "CrewOccupancy" for x in result.missing_evidence)
        )

    def test_every_resource_block_is_skipped_and_late_conflict_does_not_count(self):
        for check in CHECKS:
            if check in (
                "CrewCalendar",
                "ProjectCalendar",
                "CrewOccupancy",
                "WeekendConsent",
            ):
                continue
            with self.subTest(check=check):
                result = generate_candidate(
                    request(
                        confirmed_remaining_half_days=3,
                        slot_evidence=(
                            evidence("2026-11-23", "PM", **{check: "Blocked"}),
                        ),
                    )
                )
                self.assertEqual(
                    tuple(x.key for x in result.slots), (CONTINUOUS[0], *CONTINUOUS[2:])
                )
                self.assertEqual(result.generated_half_days, 3)
                self.assertIn(f"CONSTRAINT_BLOCKED:{check}", result.skipped[0].reasons)

    def test_missing_safety_evidence_never_certifies_or_enables_apply(self):
        r = request(
            slot_evidence=(evidence("2026-11-23", EmployeeAvailability="Satisfied"),)
        )
        result = compare(r)
        missing = {x.check for x in result.candidates[0].missing_evidence}
        for name in (
            "ApprovedDriver",
            "Skills",
            "Qualifications",
            "Foreman",
            "MinimumStaffing",
            "RigAvailability",
            "PersonnelConflicts",
        ):
            self.assertIn(name, missing)
        for record in (
            result,
            result.comparison,
            result.comparison.options[0],
            result.candidates[0],
        ):
            self.assertFalse(record.applyable or record.publishable)
            self.assertEqual(record.validation_status, "Pending")
            with self.assertRaises(TypeError):
                replace(record, publishable=True)

    def test_all_supplied_satisfied_remains_pending(self):
        supplied = tuple(
            evidence(
                day,
                half,
                **{
                    x: "Satisfied"
                    for x in CHECKS
                    if x
                    not in (
                        "CrewCalendar",
                        "ProjectCalendar",
                        "CrewOccupancy",
                        "WeekendConsent",
                    )
                },
            )
            for day, half in CONTINUOUS
        )
        r = request(
            slot_evidence=supplied,
            occupancy=CrewOccupancySnapshot(7, "2026-11-23", "2026-11-27", ()),
        )
        result = compare(r)
        self.assertEqual(
            result.comparison.options[0].evidence_status, "AllSuppliedSatisfied"
        )
        self.assertFalse(result.candidates[0].applyable)
        self.assertEqual(result.candidates[0].missing_evidence, ())

    def test_civil_tower_independent_identity_shared_parent_calendar(self):
        civil = request()
        tower = replace(civil, option_id=2, work_item_id=15)
        a, b = generate_candidate(civil), generate_candidate(tower)
        self.assertEqual((a.project_id, b.project_id), (6, 6))
        self.assertEqual((a.work_item_id, b.work_item_id), (14, 15))
        self.assertTrue(all(x.calendar.project_id == 6 for x in b.scanned))
        self.assertEqual((b.option.work_item_id, b.option.project_id), (15, 6))
        with self.assertRaisesRegex(ValueError, "parent Project"):
            compare(civil, tower)

    def test_multi_crew_requirement_not_simplified_or_compared(self):
        result = compare(request(required_crew_count=2))
        candidate = result.candidates[0]
        self.assertIn("MULTI_CREW_REQUIRES_REVIEW", candidate.review_reasons)
        self.assertEqual(candidate.generated_half_days, 0)
        self.assertEqual(candidate.scanned, ())
        self.assertIsNone(candidate.proposed_finish)
        self.assertEqual(result.comparison.options, ())

    def test_remaining_absent_or_unconfirmed_never_uses_estimates(self):
        for count, confirmed in ((None, True), (None, False), (4, False)):
            result = generate_candidate(
                request(
                    confirmed_remaining_half_days=count,
                    remaining_confirmed_by_operator=confirmed,
                )
            )
            self.assertEqual(result.status, "Needs Review")
            self.assertIsNone(result.option)
            self.assertEqual(result.scanned, ())
            self.assertEqual(result.generated_half_days, 0)
        with self.assertRaises(TypeError):
            replace(request(), estimated_half_days=4)

    def test_cross_year_leap_dst_and_max_date_use_local_dates(self):
        for start, end in (
            ("2026-12-31", "2027-01-01"),
            ("2028-02-28", "2028-02-29"),
            ("2027-03-13", "2027-03-14"),
            ("2027-11-06", "2027-11-07"),
            ("9999-12-31", "9999-12-31"),
        ):
            keys = ((start, "AM"), (end, "PM"))
            supplied = tuple(
                evidence(day, half, WeekendConsent="Satisfied")
                for day, half in keys
                if date.fromisoformat(day).weekday() >= 5
            )
            r = request(
                keys,
                earliest_start_date=start,
                horizon_end_date=end,
                confirmed_remaining_half_days=2,
                slot_evidence=supplied,
            )
            before = None
            for zone in ("UTC", "America/Toronto", "America/Vancouver"):
                with patch.dict(os.environ, TZ=zone):
                    result = generate_candidate(r)
                    self.assertEqual(result.proposed_finish, DateSlot(end, "PM"))
                    if before is not None:
                        self.assertEqual(result, before)
                    before = result

    def test_full_12_month_horizon_exhaustion_and_annual_boundary(self):
        result = generate_candidate(
            request(
                keys=(), earliest_start_date="2028-01-01", horizon_end_date="2028-12-31"
            )
        )
        self.assertEqual(len(result.scanned), 732)
        self.assertEqual(result.unfilled_half_days, 4)
        self.assertIsNone(result.proposed_finish)
        for start, end in (
            ("2028-01-01", "2029-01-01"),
            ("2027-01-01", "2028-01-01"),
            ("2028-02-29", "2029-02-28"),
            ("2026-11-24", "2026-11-23"),
        ):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                request(keys=(), earliest_start_date=start, horizon_end_date=end)
        self.assertIsNotNone(
            request(
                keys=(), earliest_start_date="2028-02-29", horizon_end_date="2029-02-27"
            )
        )

    def test_final_pm_in_horizon_counts_no_scan_beyond_finish(self):
        r = request(keys=(("2026-11-27", "PM"),), confirmed_remaining_half_days=1)
        result = generate_candidate(r)
        self.assertEqual(result.proposed_finish, DateSlot("2026-11-27", "PM"))
        self.assertEqual(len(result.scanned), 10)
        self.assertEqual(
            generate_candidate(
                replace(r, confirmed_remaining_half_days=733)
            ).unfilled_half_days,
            732,
        )

    def test_generated_dates_dual_sort_and_permutation_stability(self):
        c1 = request(GAPPED)
        c2keys = (
            ("2026-11-24", "AM"),
            ("2026-11-24", "PM"),
            ("2026-11-25", "AM"),
            ("2026-11-25", "PM"),
        )
        c2 = request(
            c2keys,
            option_id=2,
            crew_id=8,
            crew_calendar=WorkCalendar("Crew", 8, cells(*c2keys)),
        )
        c3 = request(
            option_id=3,
            crew_id=9,
            crew_calendar=WorkCalendar("Crew", 9, cells(*CONTINUOUS)),
            slot_evidence=tuple(
                evidence(day, half, RigConflicts="Blocked") for day, half in CONTINUOUS
            ),
        )
        # Every option inherits exactly the same Project calendar.
        project = WorkCalendar(
            "Project", 6, cells(*sorted(set(GAPPED + c2keys + CONTINUOUS)))
        )
        c1, c2, c3 = (replace(x, project_calendar=project) for x in (c1, c2, c3))
        for inputs in permutations((c1, c2, c3)):
            finish = compare(*inputs, max_options=1)
            start = compare(*inputs, order="EarliestStart")
            self.assertEqual([x.option.crew_id for x in finish.comparison.options], [8])
            self.assertEqual(
                [x.option.crew_id for x in start.comparison.options], [7, 8]
            )
            self.assertEqual(finish.comparison.omitted_by_limit, 1)
            self.assertEqual(
                start.sort_basis,
                ("Proposed start", "Proposed finish", "Crew ID", "Option ID"),
            )
            self.assertEqual(
                next(x for x in finish.candidates if x.crew_id == 9).status,
                "Needs Review",
            )

    def test_canonical_snapshot_order_and_frozen_input(self):
        r = request(GAPPED)
        reverse = replace(
            r,
            crew_calendar=replace(
                r.crew_calendar, cells=tuple(reversed(r.crew_calendar.cells))
            ),
        )
        before = asdict(reverse)
        self.assertEqual(generate_candidate(r), generate_candidate(reverse))
        self.assertEqual(asdict(reverse), before)
        with self.assertRaises(FrozenInstanceError):
            r.crew_id = 8

    def test_invalid_dates_ids_durations_and_confirmation_are_explicit(self):
        for value in (True, 0, -1, 1.0, "4", 2**53):
            for name in (
                "crew_id",
                "work_item_id",
                "project_id",
                "option_id",
                "required_crew_count",
                "confirmed_remaining_half_days",
            ):
                with (
                    self.subTest(name=name, value=value),
                    self.assertRaises(ValueError),
                ):
                    replace(request(), **{name: value})
        for day in (None, "2027-02-29", "2026-1-01", "2026-11-23T00:00:00Z"):
            with self.assertRaises(ValueError):
                replace(request(), earliest_start_date=day)
        for value in (None, 1, "true"):
            with self.assertRaises(ValueError):
                replace(request(), remaining_confirmed_by_operator=value)
        with self.assertRaises(ValueError):
            DateSlot("2026-11-23", "FullDay")

    def test_wrong_snapshot_ids_scopes_ranges_and_duplicates_reject(self):
        r = request()
        for cal in (
            None,
            WorkCalendar("Crew", 8),
            WorkCalendar("WorkItem", 14),
            WorkCalendar("Project", 6),
        ):
            with self.assertRaises(ValueError):
                replace(r, crew_calendar=cal)
        with self.assertRaises(ValueError):
            replace(r, project_calendar=WorkCalendar("Project", 8))
        with self.assertRaises(ValueError):
            WorkCalendar("Crew", 7, cells(CONTINUOUS[0], CONTINUOUS[0]))
        with self.assertRaises(ValueError):
            replace(
                r, crew_calendar=WorkCalendar("Crew", 7, cells(("2026-11-28", "AM")))
            )
        with self.assertRaises(ValueError):
            replace(r, slot_evidence=(evidence("2026-11-23"), evidence("2026-11-23")))
        for check in ("CrewCalendar", "ProjectCalendar", "CrewOccupancy"):
            with self.assertRaises(ValueError):
                replace(
                    r, slot_evidence=(evidence("2026-11-23", **{check: "Satisfied"}),)
                )
        with self.assertRaises(ValueError):
            replace(
                r, slot_evidence=(evidence("2026-11-28", WeekendConsent="Satisfied"),)
            )
        with self.assertRaises(ValueError):
            replace(r, slot_evidence=[])
        for occupied in (
            [DateSlot(*CONTINUOUS[0])],
            (DateSlot(*CONTINUOUS[0]),) * 2,
            (DateSlot("2026-11-28", "AM"),),
        ):
            with self.assertRaises(ValueError):
                CrewOccupancySnapshot(7, "2026-11-23", "2026-11-27", occupied)
        with self.assertRaises(ValueError):
            replace(
                r, occupancy=CrewOccupancySnapshot(8, "2026-11-23", "2026-11-27", ())
            )

    def test_batch_bounds_wrong_context_and_mixed_duration_reject_before_scan(self):
        r = request()
        for requests in (
            [r],
            (r, r),
            tuple(replace(r, option_id=i + 1) for i in range(101)),
            (replace(r, project_id=8, project_calendar=WorkCalendar("Project", 8)),),
            (r, replace(r, option_id=2, confirmed_remaining_half_days=2)),
        ):
            with (
                patch(
                    "rigarus_backend.recommendation_generator.generate_candidate",
                    side_effect=AssertionError("unexpected scan"),
                ),
                self.assertRaises(ValueError),
            ):
                generate_and_compare(14, 6, requests, max_options=3)
        for settings in (
            {"max_options": 0},
            {"max_options": True},
            {"order": "SafetyWeight"},
        ):
            with self.assertRaises(ValueError):
                compare(r, **settings)
        self.assertEqual(compare().comparison.options, ())
        with self.assertRaises(ValueError):
            generate_candidate(asdict(r))

    def test_no_io_clock_or_mutation_and_scan_complexity_is_linear(self):
        r = request(
            keys=(), earliest_start_date="2028-01-01", horizon_end_date="2028-12-31"
        )
        before = asdict(r)
        from rigarus_backend import recommendation_generator as module

        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("os.open", side_effect=AssertionError("file")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("time.time", side_effect=AssertionError("clock")),
            patch.object(
                module, "assess_project_calendar", wraps=module.assess_project_calendar
            ) as assess,
        ):
            result = generate_candidate(r)
            self.assertEqual(assess.call_count, 732)
            self.assertTrue(
                all(
                    len(call.args[1].cells) == len(call.args[2].cells) == 1
                    for call in assess.call_args_list
                )
            )
            self.assertEqual(generate_candidate(r), result)
        self.assertEqual(asdict(r), before)

    def test_seeded_calendar_oracle_independent_of_generator(self):
        rng = random.Random(28)
        days = ["2026-11-23", "2026-11-24", "2026-11-25", "2026-11-26", "2026-11-27"]
        keys = list(product(days, ("AM", "PM")))
        for _ in range(50):
            crew = [rng.choice(("Working", "NotWorking", "Unknown")) for _ in keys]
            project = [rng.choice(("Working", "NotWorking", "Unknown")) for _ in keys]
            wanted = rng.randint(1, 4)
            expected = [
                key for key, c, p in zip(keys, crew, project) if c == p == "Working"
            ][:wanted]
            r = request(
                keys=(),
                confirmed_remaining_half_days=wanted,
                crew_calendar=WorkCalendar(
                    "Crew",
                    7,
                    tuple(
                        WorkCalendarCell(*key, state) for key, state in zip(keys, crew)
                    ),
                ),
                project_calendar=WorkCalendar(
                    "Project",
                    6,
                    tuple(
                        WorkCalendarCell(*key, state)
                        for key, state in zip(keys, project)
                    ),
                ),
            )
            result = generate_candidate(r)
            self.assertEqual([x.key for x in result.slots], expected)
            self.assertEqual(result.unfilled_half_days, wanted - len(expected))
            self.assertEqual(
                result.proposed_finish,
                DateSlot(*expected[-1]) if len(expected) == wanted else None,
            )


class GeneratorCompatibilityTests(unittest.TestCase):
    def test_whole_synthetic_sqlite_assignments_workers_calendars_unchanged(self):
        test_assignments.AssignmentTests.setUp(self)
        tower = self.project["work_items"][1]
        draft = self.client.post(
            "/draft-assignments", json={**self.draft, "work_item_id": tower["id"]}
        ).json()
        worker = self.client.post(
            "/employees",
            json={
                "name": "Synthetic Generator Worker",
                "home_crew_id": self.crew["id"],
                "skill_level": 2,
                "foreman_eligible": True,
            },
        ).json()
        self.client.put(
            f"/draft-assignments/{draft['id']}/staffing",
            json={"employee_ids": [worker["id"]], "expected_revision": 1},
        ).raise_for_status()
        for scope, entity_id in (
            ("Project", self.project["id"]),
            ("Crew", self.crew["id"]),
        ):
            self.client.put(
                f"/working-calendars/{scope}/{entity_id}",
                json={
                    "start_date": "2026-12-31",
                    "end_date": "2027-01-01",
                    "slot": "FullDay",
                    "state": "Working",
                    "expected_revision": 0,
                },
            ).raise_for_status()
        saved = self.client.get(f"/draft-assignments/{draft['id']}").json()
        with closing(sqlite3.connect(self.database)) as connection:
            before = list(connection.iterdump())
        keys = (
            ("2026-12-31", "AM"),
            ("2026-12-31", "PM"),
            ("2027-01-01", "AM"),
            ("2027-01-01", "PM"),
        )
        r = request(
            keys,
            work_item_id=tower["id"],
            project_id=self.project["id"],
            crew_id=self.crew["id"],
            crew_calendar=WorkCalendar("Crew", self.crew["id"], cells(*keys)),
            project_calendar=WorkCalendar("Project", self.project["id"], cells(*keys)),
            earliest_start_date="2026-12-31",
            horizon_end_date="2027-01-01",
            occupancy=CrewOccupancySnapshot(
                self.crew["id"],
                "2026-12-31",
                "2027-01-01",
                (DateSlot("2026-12-31", "AM"),),
            ),
        )
        result = generate_and_compare(
            tower["id"], self.project["id"], (r,), max_options=3
        )
        self.assertEqual(result.candidates[0].unfilled_half_days, 1)
        self.assertIsNone(result.candidates[0].proposed_finish)
        self.assertEqual(
            self.client.get(f"/draft-assignments/{draft['id']}").json(), saved
        )
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(list(connection.iterdump()), before)
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
