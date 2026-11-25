"""Synthetic whole-date allocation, shared comparison and immutable input contracts."""

import unittest
from dataclasses import replace, asdict, FrozenInstanceError
from datetime import date
from unittest.mock import patch

from rigarus_backend.day_drafts import ConfirmedRemainingDays
from rigarus_backend.day_recommendation_generator import (
    DayCalendar,
    DayCalendarCell,
    DayOccupancy,
    DayGenerationRequest,
    generate_day_candidate,
    generate_days_and_compare,
)
from rigarus_backend.recommendation_comparison import (
    CHECKS,
    ConstraintEvidence,
    ProposedDay,
    ExplicitDayOption,
    compare_day_options,
)

MON = "2026-11-23"
FRI = "2026-11-27"


class DayGenerationTests(unittest.TestCase):
    def request(self, days=4, crew=1, working=None, start=MON, end=FRI):
        dates = tuple(
            date.fromordinal(n).isoformat()
            for n in range(
                date.fromisoformat(start).toordinal(),
                date.fromisoformat(end).toordinal() + 1,
            )
        )
        cells = tuple(
            DayCalendarCell(
                d, "Working" if working is None or d in working else "NotWorking"
            )
            for d in dates
        )
        return DayGenerationRequest(
            crew,
            10,
            20,
            crew,
            1,
            ConfirmedRemainingDays(days, True),
            start,
            end,
            DayCalendar("Crew", crew, cells),
            DayCalendar(
                "Project", 20, tuple(DayCalendarCell(d, "Working") for d in dates)
            ),
            DayOccupancy(crew, start, end, ()),
        )

    def test_continuous_four_days_and_no_half_day_fields(self):
        result = generate_day_candidate(self.request())
        self.assertEqual(
            result.allocated_working_dates,
            (MON, "2026-11-24", "2026-11-25", "2026-11-26"),
        )
        self.assertEqual(
            (
                result.proposed_start_date,
                result.proposed_finish_date,
                result.accumulated_days,
                result.unfilled_days,
            ),
            (MON, "2026-11-26", 4, 0),
        )
        self.assertEqual(result.status, "Validation pending")
        self.assertFalse(result.applyable or result.publishable)
        self.assertNotIn("slot", str(asdict(result)))

    def test_gaps_accumulate_without_reset_and_retain_skip_explanation(self):
        result = generate_day_candidate(
            self.request(working=(MON, "2026-11-25", "2026-11-26", FRI))
        )
        self.assertEqual(result.proposed_finish_date, FRI)
        self.assertEqual(result.accumulated_days, 4)
        self.assertEqual(result.skipped[0].local_date, "2026-11-24")
        self.assertIn("CREW_CALENDAR_NOTWORKING", result.skipped[0].reasons)
        self.assertEqual(
            (
                result.calendar_matches,
                result.calendar_conflicts,
                result.calendar_blocked,
            ),
            (4, 1, 1),
        )

    def test_all_closed_unknown_and_partial_deficit_never_forge_finish(self):
        for state in ("NotWorking", "Unknown"):
            r = self.request()
            r = replace(
                r,
                crew_calendar=DayCalendar(
                    "Crew",
                    1,
                    tuple(
                        DayCalendarCell(c.local_date, state)
                        for c in r.crew_calendar.cells
                    ),
                ),
            )
            result = generate_day_candidate(r)
            self.assertEqual(
                (
                    result.status,
                    result.proposed_finish_date,
                    result.accumulated_days,
                    result.unfilled_days,
                ),
                ("Needs Review", None, 0, 4),
            )
            self.assertIsNone(result.option)
        result = generate_day_candidate(self.request(working=(MON,)))
        self.assertEqual(
            (
                result.proposed_start_date,
                result.proposed_finish_date,
                result.unfilled_days,
            ),
            (MON, None, 3),
        )

    def test_either_calendar_closure_and_unknown_or_stale_positive_not_capacity(self):
        r = self.request(days=1)
        r = replace(
            r,
            project_calendar=DayCalendar(
                "Project", 20, (DayCalendarCell(MON, "NotWorking"),)
            ),
        )
        result = generate_day_candidate(r)
        self.assertEqual(result.accumulated_days, 0)
        self.assertGreater(result.calendar_unknowns, 0)
        with self.assertRaises(ValueError):
            DayCalendarCell(MON, "Working", "Stale")
        r = replace(
            self.request(days=1),
            crew_calendar=DayCalendar(
                "Crew", 1, (DayCalendarCell(MON, "Unknown", "Stale"),)
            ),
        )
        self.assertIn(
            "CREW_CALENDAR_STALE", generate_day_candidate(r).skipped[0].reasons
        )

    def test_daily_occupancy_and_partial_or_missing_coverage(self):
        r = self.request(days=1)
        result = generate_day_candidate(
            replace(r, occupancy=DayOccupancy(1, MON, FRI, (MON,)))
        )
        self.assertEqual(result.proposed_start_date, "2026-11-24")
        self.assertIn("CONSTRAINT_BLOCKED:CrewOccupancy", result.skipped[0].reasons)
        for occupancy in (None, DayOccupancy(1, FRI, FRI, ())):
            result = generate_day_candidate(
                replace(self.request(days=2), occupancy=occupancy)
            )
            self.assertIsNone(result.proposed_finish_date)
            self.assertIn("CREW_OCCUPANCY_UNKNOWN", result.skipped[0].reasons)

    def test_weekend_requires_exact_full_date_consent_and_all_flags_remain_pending(
        self,
    ):
        r = self.request(days=1, start="2026-11-28", end="2026-11-29")
        blocked = generate_day_candidate(r)
        self.assertEqual(blocked.accumulated_days, 0)
        self.assertTrue(
            all("WEEKEND_CONSENT_NOT_CONFIRMED" in d.reasons for d in blocked.skipped)
        )
        evidence = (
            ProposedDay(
                "2026-11-29", (ConstraintEvidence("WeekendConsent", "Satisfied"),)
            ),
        )
        allowed = generate_day_candidate(replace(r, day_evidence=evidence))
        self.assertEqual(allowed.proposed_finish_date, "2026-11-29")
        self.assertEqual(allowed.validation_status, "Pending")
        self.assertFalse(allowed.applyable or allowed.publishable)

    def test_known_blocked_resource_skips_date_missing_other_checks_stay_pending(self):
        r = replace(
            self.request(days=1),
            day_evidence=(
                ProposedDay(MON, (ConstraintEvidence("RigAvailability", "Blocked"),)),
            ),
        )
        result = generate_day_candidate(r)
        self.assertEqual(result.proposed_start_date, "2026-11-24")
        self.assertIn("CONSTRAINT_BLOCKED:RigAvailability", result.skipped[0].reasons)
        self.assertIn("ApprovedDriver", {e.check for e in result.missing_evidence})
        self.assertTrue(all(e.state == "Pending" for e in result.missing_evidence))

    def test_multi_crew_missing_or_invalid_confirmed_days(self):
        for r, reason in (
            (
                replace(self.request(), required_crew_count=2),
                "MULTI_CREW_REQUIRES_REVIEW",
            ),
            (
                replace(self.request(), remaining=None),
                "CONFIRMED_REMAINING_DAYS_MISSING",
            ),
        ):
            result = generate_day_candidate(r)
            self.assertEqual(result.scanned, ())
            self.assertIsNone(result.proposed_finish_date)
            self.assertIn(reason, result.review_reasons)
        for value in (0, -1, True, 1.0, 0.5, "4", 2**53):
            with self.assertRaises(ValueError):
                ConfirmedRemainingDays(value, True)
        for confirmed in (False, 1, "true", None):
            with self.assertRaises(ValueError):
                ConfirmedRemainingDays(4, confirmed)
        for value in (4, 4.0, True):
            with self.assertRaises(ValueError):
                replace(self.request(), remaining=value)
        with self.assertRaises(TypeError):
            DayGenerationRequest(confirmed_remaining_half_days=4)

    def test_dual_sort_stable_ties_limit_and_incomplete_diagnostics(self):
        one = self.request(working=(MON, "2026-11-25", "2026-11-26", FRI))
        two = self.request(
            crew=2, working=("2026-11-24", "2026-11-25", "2026-11-26", FRI)
        )
        # Same finish; use a shorter confirmed requirement for distinct sort outcomes.
        one, two = (
            replace(one, remaining=ConfirmedRemainingDays(2, True)),
            replace(two, remaining=ConfirmedRemainingDays(2, True)),
        )
        one = replace(
            one,
            crew_calendar=DayCalendar(
                "Crew",
                1,
                (DayCalendarCell(MON, "Working"), DayCalendarCell(FRI, "Working")),
            ),
        )
        requests = (
            two,
            one,
            replace(
                two,
                option_id=3,
                crew_id=3,
                crew_calendar=DayCalendar("Crew", 3, two.crew_calendar.cells),
                occupancy=DayOccupancy(3, MON, FRI, ()),
            ),
        )
        finish = generate_days_and_compare(10, 20, requests, max_options=3)
        start = generate_days_and_compare(
            10, 20, requests, max_options=3, order="EarliestStart"
        )
        self.assertEqual(
            [o.option.crew_id for o in finish.comparison.options], [2, 3, 1]
        )
        self.assertEqual(
            [o.option.crew_id for o in start.comparison.options], [1, 2, 3]
        )
        self.assertEqual(
            finish,
            generate_days_and_compare(10, 20, tuple(reversed(requests)), max_options=3),
        )
        limited = generate_days_and_compare(10, 20, requests, max_options=1)
        self.assertEqual(limited.comparison.omitted_by_limit, 2)
        incomplete = replace(one, remaining=ConfirmedRemainingDays(100, True))
        self.assertEqual(
            generate_days_and_compare(
                10, 20, (incomplete,), max_options=3
            ).comparison.options,
            (),
        )

    def test_comparator_hard_filter_before_limit_and_complete_evidence_still_pending(
        self,
    ):
        blocked = ExplicitDayOption(
            1,
            10,
            20,
            1,
            (ProposedDay(MON, (ConstraintEvidence("ApprovedDriver", "Blocked"),)),),
        )
        clear = ExplicitDayOption(
            2,
            10,
            20,
            2,
            (
                ProposedDay(
                    MON,
                    tuple(
                        ConstraintEvidence(c, "Satisfied")
                        for c in CHECKS
                        if c != "WeekendConsent"
                    ),
                ),
            ),
        )
        result = compare_day_options(10, 20, (blocked, clear), max_options=1)
        self.assertEqual(result.excluded[0].option.option_id, 1)
        self.assertEqual(result.options[0].evidence_status, "AllSuppliedSatisfied")
        self.assertEqual(result.options[0].validation_status, "Pending")
        self.assertFalse(result.applyable or result.publishable)

    def test_year_leap_dst_low_high_date_and_annual_bound(self):
        for first, last in (
            ("2026-12-31", "2027-01-01"),
            ("2028-02-28", "2028-03-01"),
            ("2027-03-12", "2027-03-16"),
            ("2027-11-05", "2027-11-09"),
            ("0001-01-01", "0001-01-01"),
            ("9999-12-31", "9999-12-31"),
        ):
            r = self.request(days=10, start=first, end=last)
            self.assertEqual(generate_day_candidate(r).scanned[-1].local_date, last)
        result = generate_day_candidate(
            self.request(days=1000, start="2027-01-01", end="2027-12-31")
        )
        self.assertEqual(len(result.scanned), 365)
        self.assertIsNone(result.proposed_finish_date)
        self.assertGreater(result.unfilled_days, 0)
        for first, last in (("2027-01-01", "2028-01-01"), ("2028-02-29", "2029-02-28")):
            with self.assertRaises(ValueError):
                self.request(start=first, end=last)

    def test_invalid_context_duplicate_dates_evidence_and_shared_parent(self):
        r = self.request()
        for change in (
            dict(work_item_id=True),
            dict(crew_id=0),
            dict(earliest_start_date="2026-02-30"),
            dict(earliest_start_date="2026-1-01"),
            dict(horizon_end_date="2026-11-22"),
            dict(project_calendar=DayCalendar("Project", 21, ())),
            dict(occupancy=DayOccupancy(2, MON, FRI, ())),
        ):
            with self.assertRaises(ValueError):
                replace(r, **change)
        with self.assertRaises(ValueError):
            DayCalendar("Crew", 1, (DayCalendarCell(MON, "Working"),) * 2)
        with self.assertRaises(ValueError):
            DayOccupancy(1, MON, FRI, (MON, MON))
        with self.assertRaises(ValueError):
            ProposedDay(MON, (ConstraintEvidence("CrewType", "Pending"),) * 2)
        with self.assertRaises(ValueError):
            ProposedDay(MON, (ConstraintEvidence("WeekendConsent", "Satisfied"),))
        with self.assertRaises(ValueError):
            replace(
                r,
                day_evidence=(
                    ProposedDay(
                        MON, (ConstraintEvidence("CrewCalendar", "Satisfied"),)
                    ),
                ),
            )
        with self.assertRaises(ValueError):
            generate_days_and_compare(
                10,
                20,
                (r, replace(r, option_id=2, remaining=ConfirmedRemainingDays(3, True))),
                max_options=3,
            )
        with self.assertRaises(ValueError):
            generate_days_and_compare(
                10,
                20,
                (
                    r,
                    replace(
                        r, option_id=2, project_calendar=DayCalendar("Project", 20, ())
                    ),
                ),
                max_options=3,
            )

    def test_pure_deterministic_frozen_and_no_file_network_sql_or_clock(self):
        r = self.request()
        before = asdict(r)
        with (
            patch("builtins.open", side_effect=AssertionError("file")),
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("sqlite3.connect", side_effect=AssertionError("SQL")),
            patch("time.time", side_effect=AssertionError("clock")),
        ):
            first = generate_day_candidate(r)
            self.assertEqual(first, generate_day_candidate(r))
        self.assertEqual(asdict(r), before)
        with self.assertRaises(FrozenInstanceError):
            r.crew_id = 2
