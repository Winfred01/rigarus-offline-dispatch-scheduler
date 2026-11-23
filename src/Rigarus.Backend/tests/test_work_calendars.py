import os
import sqlite3
import unittest
from contextlib import closing
from dataclasses import FrozenInstanceError, asdict
from itertools import product
from unittest.mock import patch

import test_assignments
from rigarus_backend.assignments import AssignmentDraft
from rigarus_backend.work_calendars import (
    WorkCalendar,
    WorkCalendarCell,
    assess_calendar_range,
    assess_draft_calendar,
)


class WorkCalendarTests(unittest.TestCase):
    def calendars(self, crew="Working", work="Working", day="2026-11-23", slot="AM"):
        return (
            WorkCalendar("Crew", 7, (WorkCalendarCell(day, slot, crew),)),
            WorkCalendar("WorkItem", 14, (WorkCalendarCell(day, slot, work),)),
        )

    def assess(self, crew="Working", work="Working", day="2026-11-23", slot="AM"):
        return assess_draft_calendar(
            AssignmentDraft(14, 7, day, slot),
            *self.calendars(crew, work, day, slot),
        )

    def test_all_nine_state_pairs_explain_each_source_without_overrides(self):
        expected = {
            ("Working", "Working"): "Matched",
            ("Working", "NotWorking"): "Blocked",
            ("Working", "Unknown"): "Pending",
            ("NotWorking", "Working"): "Blocked",
            ("NotWorking", "NotWorking"): "Blocked",
            ("NotWorking", "Unknown"): "Blocked",
            ("Unknown", "Working"): "Pending",
            ("Unknown", "NotWorking"): "Blocked",
            ("Unknown", "Unknown"): "Pending",
        }
        for states in product(("Working", "NotWorking", "Unknown"), repeat=2):
            with self.subTest(states=states):
                result = self.assess(*states)
                self.assertEqual(result.status, expected[states])
                self.assertEqual((result.crew_state, result.work_item_state), states)
                self.assertEqual(
                    [(r.scope, r.entity_id) for r in result.reasons[:2]],
                    [("Crew", 7), ("WorkItem", 14)],
                )
                conflict = {"Working", "NotWorking"} == set(states)
                self.assertEqual(
                    any(r.code == "CALENDAR_CONFLICT" for r in result.reasons),
                    conflict,
                )
                self.assertFalse(result.publishable)
                self.assertEqual(result.validation_status, "Pending")

    def test_empty_weekday_weekend_and_holiday_never_assumed_working(self):
        for day in ("2026-11-23", "2026-11-28", "2026-11-29", "2026-12-25"):
            with self.subTest(day=day):
                result = assess_draft_calendar(
                    AssignmentDraft(14, 7, day, "AM"),
                    WorkCalendar("Crew", 7),
                    WorkCalendar("WorkItem", 14),
                )
                self.assertEqual(result.status, "Pending")
                self.assertEqual(result.crew_state, "Unknown")
                self.assertEqual(result.work_item_state, "Unknown")

    def test_explicit_weekend_match_does_not_grant_consent(self):
        for day in ("2026-11-28", "2026-11-29"):
            result = self.assess(day=day)
            self.assertEqual(result.status, "Matched")
            self.assertEqual(result.reasons[-1].code, "WEEKEND_APPROVAL_PENDING")
            self.assertFalse(result.publishable)
        self.assertNotIn(
            "WEEKEND_APPROVAL_PENDING", [r.code for r in self.assess().reasons]
        )

    def test_am_pm_and_other_dates_remain_independent(self):
        crew, work = self.calendars()
        results = assess_calendar_range(crew, work, "2026-11-23", "2026-11-24")
        self.assertEqual([r.status for r in results], ["Matched"] + ["Pending"] * 3)
        self.assertEqual([r.slot for r in results], ["AM", "PM", "AM", "PM"])

    def test_crew_specific_closed_cell_does_not_change_another_crew(self):
        crew, work = self.calendars(crew="NotWorking")
        other = WorkCalendar("Crew", 8, self.calendars()[0].cells)
        self.assertEqual(
            assess_draft_calendar(
                AssignmentDraft(14, 7, "2026-11-23", "AM"), crew, work
            ).status,
            "Blocked",
        )
        self.assertEqual(
            assess_draft_calendar(
                AssignmentDraft(14, 8, "2026-11-23", "AM"), other, work
            ).status,
            "Matched",
        )

    def test_exact_scope_and_stable_ids_required(self):
        crew, work = self.calendars()
        draft = AssignmentDraft(14, 7, "2026-11-23", "AM")
        for pair in (
            (work, crew),
            (WorkCalendar("Crew", 8), work),
            (crew, WorkCalendar("WorkItem", 15)),
            (None, work),
            (crew, None),
        ):
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                assess_draft_calendar(draft, *pair)
        with self.assertRaises(ValueError):
            assess_draft_calendar(asdict(draft), crew, work)

    def test_duplicate_cells_rejected_even_if_equal_instead_of_last_wins(self):
        cell = WorkCalendarCell("2026-11-23", "AM", "Working")
        for other in (cell, WorkCalendarCell(cell.local_date, cell.slot, "NotWorking")):
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                WorkCalendar("Crew", 7, (cell, other))

    def test_inputs_are_strict_and_snapshots_immutable(self):
        for invalid in (True, 0, -1, "7", 1.0, 2**53):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                WorkCalendar("Crew", invalid)
        for day in ("2027-02-29", "2026-11-23T00:00:00Z", "2026-1-01", None):
            with self.subTest(day=day), self.assertRaises(ValueError):
                WorkCalendarCell(day, "AM", "Working")
        with self.assertRaises(ValueError):
            WorkCalendarCell("2026-11-23", "FullDay", "Working")
        with self.assertRaises(ValueError):
            WorkCalendarCell("2026-11-23", "AM", "Available")
        with self.assertRaises(ValueError):
            WorkCalendar("Employee", 7)
        with self.assertRaises(ValueError):
            WorkCalendar("Crew", 7, [])
        with self.assertRaises(ValueError):
            WorkCalendar("Crew", 7, ("not-a-cell",))
        crew, _ = self.calendars()
        with self.assertRaises(FrozenInstanceError):
            crew.cells = ()
        with self.assertRaises(TypeError):
            type(self.assess())(**asdict(self.assess()))

    def test_cross_year_leap_and_dst_ranges_are_local_dates_in_every_timezone(self):
        for start, end, days in (
            ("2026-12-31", "2027-01-01", ["2026-12-31", "2027-01-01"]),
            ("2028-02-28", "2028-03-01", ["2028-02-28", "2028-02-29", "2028-03-01"]),
            ("2027-03-13", "2027-03-15", ["2027-03-13", "2027-03-14", "2027-03-15"]),
            ("2027-11-06", "2027-11-08", ["2027-11-06", "2027-11-07", "2027-11-08"]),
            ("9999-12-31", "9999-12-31", ["9999-12-31"]),
        ):
            reference = None
            for zone in ("UTC", "America/Toronto", "America/Vancouver"):
                with (
                    self.subTest(start=start, zone=zone),
                    patch.dict(os.environ, TZ=zone),
                ):
                    result = assess_calendar_range(
                        WorkCalendar("Crew", 7),
                        WorkCalendar("WorkItem", 14),
                        start,
                        end,
                    )
                    self.assertEqual([r.local_date for r in result[::2]], days)
                    self.assertEqual(len(result), len(days) * 2)
                    if reference is not None:
                        self.assertEqual(result, reference)
                    reference = result

    def test_range_is_inclusive_and_bounded(self):
        calendars = self.calendars()
        self.assertEqual(
            len(assess_calendar_range(*calendars, "2028-01-01", "2028-12-31")), 732
        )
        for start, end in (
            ("2026-11-24", "2026-11-23"),
            ("2028-01-01", "2029-01-01"),
            ("2027-02-29", "2027-03-01"),
        ):
            with self.subTest(start=start), self.assertRaises(ValueError):
                assess_calendar_range(*calendars, start, end)

    def test_snapshot_order_repeat_visits_and_no_io(self):
        a = WorkCalendarCell("2026-11-23", "AM", "Working")
        b = WorkCalendarCell("2026-11-24", "PM", "NotWorking")
        crew, work = self.calendars()
        draft = AssignmentDraft(14, 7, a.local_date, a.slot, "Synthetic visit")
        with (
            patch("builtins.open", side_effect=AssertionError("Unexpected file I/O")),
            patch("sqlite3.connect", side_effect=AssertionError("Unexpected SQL")),
            patch("socket.socket", side_effect=AssertionError("Unexpected network")),
        ):
            first = assess_draft_calendar(draft, WorkCalendar("Crew", 7, (a, b)), work)
            second = assess_draft_calendar(draft, WorkCalendar("Crew", 7, (b, a)), work)
            self.assertEqual(first, second)
            self.assertEqual(first, assess_draft_calendar(draft, crew, work))
        self.assertEqual(draft.notes, "Synthetic visit")


class WorkCalendarCompatibilityTests(unittest.TestCase):
    def test_assessment_keeps_existing_draft_availability_and_database_unchanged(self):
        test_assignments.AssignmentTests.setUp(self)
        visit = self.client.post("/draft-assignments", json=self.draft).json()
        person = self.client.post(
            "/employees",
            json={
                "name": "Synthetic calendar worker",
                "home_crew_id": self.crew["id"],
                "skill_level": 2,
                "foreman_eligible": False,
                "active": True,
            },
        ).json()
        self.client.put(
            f"/employees/{person['id']}/availability",
            json={
                "start_date": self.draft["local_date"],
                "end_date": self.draft["local_date"],
                "slot": "AM",
                "state": "Available",
                "expected_revision": 0,
            },
        ).raise_for_status()
        with closing(sqlite3.connect(self.database)) as connection:
            before = list(connection.iterdump())
        unknown = assess_draft_calendar(
            AssignmentDraft(**self.draft),
            WorkCalendar("Crew", self.crew["id"]),
            WorkCalendar("WorkItem", self.draft["work_item_id"]),
        )
        self.assertEqual(
            unknown.status, "Pending"
        )  # Available never fills either calendar.
        cells = (WorkCalendarCell(self.draft["local_date"], "AM", "Working"),)
        matched = assess_draft_calendar(
            AssignmentDraft(**self.draft),
            WorkCalendar("Crew", self.crew["id"], cells),
            WorkCalendar("WorkItem", self.draft["work_item_id"], cells),
        )
        self.assertEqual(matched.status, "Matched")
        self.assertFalse(matched.publishable)
        self.assertEqual(person["driver_status"], "Unverified")
        self.assertEqual(
            self.client.get(f"/draft-assignments/{visit['id']}").json(), visit
        )
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(list(connection.iterdump()), before)
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
