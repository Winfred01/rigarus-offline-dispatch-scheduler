"""Pure single-Crew whole-date proposals. No I/O, clock or half-day conversion."""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from .assignments import local_date
from .day_drafts import ConfirmedRemainingDays, positive_id
from .recommendation_generator import _range
from .recommendation_comparison import (
    CHECKS,
    ConstraintEvidence,
    ProposedDay,
    ExplicitDayOption,
    DayExplanation,
    DayOptionComparison,
    SortOrder,
    compare_day_options,
    explain_day,
)


@dataclass(frozen=True)
class DayCalendarCell:
    local_date: str
    state: Literal["Working", "NotWorking", "Unknown"]
    review_status: str = "Current"

    def __post_init__(self):
        local_date(self.local_date)
        if self.state not in (
            "Working",
            "NotWorking",
            "Unknown",
        ) or self.review_status not in (
            "Current",
            "Stale",
            "Needs Review",
            "Not recorded",
        ):
            raise ValueError("Supply an explicit daily calendar state/review status.")
        if self.state == "Working" and self.review_status != "Current":
            raise ValueError(
                "Unreviewed/stale positive evidence cannot be daily capacity."
            )


@dataclass(frozen=True)
class DayCalendar:
    scope: str
    entity_id: int
    cells: tuple[DayCalendarCell, ...]

    def __post_init__(self):
        positive_id(self.entity_id)
        if (
            self.scope not in ("Crew", "Project")
            or type(self.cells) is not tuple
            or len(self.cells) > 366
            or any(not isinstance(c, DayCalendarCell) for c in self.cells)
        ):
            raise ValueError("Supply immutable Crew/parent Project daily cells.")
        if len({c.local_date for c in self.cells}) != len(self.cells):
            raise ValueError("Duplicate calendar dates require resolution.")


@dataclass(frozen=True)
class DayOccupancy:
    crew_id: int
    start_date: str
    end_date: str
    occupied_dates: tuple[str, ...]

    def __post_init__(self):
        positive_id(self.crew_id)
        _range(self.start_date, self.end_date)
        if type(self.occupied_dates) is not tuple or len(self.occupied_dates) > 366:
            raise ValueError("Supply at most 366 immutable occupied dates.")
        for d in self.occupied_dates:
            local_date(d)
            if not self.start_date <= d <= self.end_date:
                raise ValueError("Occupancy outside declared range.")
        if len(set(self.occupied_dates)) != len(self.occupied_dates):
            raise ValueError("Duplicate occupied dates require resolution.")


@dataclass(frozen=True)
class DayGenerationRequest:
    option_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    required_crew_count: int
    remaining: ConfirmedRemainingDays | None
    earliest_start_date: str
    horizon_end_date: str
    crew_calendar: DayCalendar
    project_calendar: DayCalendar
    occupancy: DayOccupancy | None = None
    day_evidence: tuple[ProposedDay, ...] = ()

    def __post_init__(self):
        for v in (
            self.option_id,
            self.work_item_id,
            self.project_id,
            self.crew_id,
            self.required_crew_count,
        ):
            positive_id(v)
        if (
            self.remaining is not None
            and type(self.remaining) is not ConfirmedRemainingDays
        ):
            raise ValueError(
                "Use independent explicitly ConfirmedRemainingDays, never half-day estimates."
            )
        _range(self.earliest_start_date, self.horizon_end_date)
        for cal, scope, identity in (
            (self.crew_calendar, "Crew", self.crew_id),
            (self.project_calendar, "Project", self.project_id),
        ):
            if not isinstance(cal, DayCalendar) or (cal.scope, cal.entity_id) != (
                scope,
                identity,
            ):
                raise ValueError(
                    "Daily calendars must match Crew and parent Project IDs."
                )
            if any(
                not self.earliest_start_date <= c.local_date <= self.horizon_end_date
                for c in cal.cells
            ):
                raise ValueError("Restrict calendar cells to the requested horizon.")
        if self.occupancy is not None and (
            not isinstance(self.occupancy, DayOccupancy)
            or self.occupancy.crew_id != self.crew_id
            or self.occupancy.start_date < self.earliest_start_date
            or self.occupancy.end_date > self.horizon_end_date
        ):
            raise ValueError("Occupancy context/range must match the Crew scenario.")
        if (
            type(self.day_evidence) is not tuple
            or len(self.day_evidence) > 366
            or any(not isinstance(d, ProposedDay) for d in self.day_evidence)
        ):
            raise ValueError("Supply immutable per-date evidence.")
        if len({d.local_date for d in self.day_evidence}) != len(self.day_evidence):
            raise ValueError("Duplicate evidence dates require resolution.")
        for d in self.day_evidence:
            if (
                not self.earliest_start_date <= d.local_date <= self.horizon_end_date
                or any(
                    e.check in ("CrewCalendar", "ProjectCalendar", "CrewOccupancy")
                    for e in d.evidence
                )
            ):
                raise ValueError(
                    "Evidence dates must match horizon; derive calendars/occupancy only from snapshots."
                )


@dataclass(frozen=True)
class ScannedDay:
    local_date: str
    crew_state: str
    project_state: str
    calendar_status: str
    occupancy_status: str
    accumulated: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedDayCandidate:
    option_id: int
    project_id: int
    work_item_id: int
    crew_id: int
    confirmed_remaining_days: int | None
    proposed_start_date: str | None
    proposed_finish_date: str | None
    allocated_working_dates: tuple[str, ...]
    accumulated_days: int
    unfilled_days: int | None
    scanned: tuple[ScannedDay, ...]
    skipped: tuple[ScannedDay, ...]
    calendar_matches: int
    calendar_conflicts: int
    calendar_unknowns: int
    calendar_blocked: int
    missing_evidence: tuple[DayExplanation, ...]
    review_reasons: tuple[str, ...]
    option: ExplicitDayOption | None
    status: str
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def generate_day_candidate(request: DayGenerationRequest):
    if not isinstance(request, DayGenerationRequest):
        raise ValueError("Supply an immutable DayGenerationRequest.")
    r = request
    review = []
    if r.required_crew_count != 1:
        review.append("MULTI_CREW_REQUIRES_REVIEW")
    if r.remaining is None:
        review.append("CONFIRMED_REMAINING_DAYS_MISSING")
    crew = {c.local_date: c for c in r.crew_calendar.cells}
    project = {c.local_date: c for c in r.project_calendar.cells}
    occupancy = set(r.occupancy.occupied_dates) if r.occupancy else set()
    evidence = {d.local_date: d.evidence for d in r.day_evidence}
    allocated, scanned, missing = [], [], []
    if not review:
        first, last = _range(r.earliest_start_date, r.horizon_end_date)
        for ordinal in range(first, last + 1):
            day = date.fromordinal(ordinal).isoformat()
            a, b = (
                crew.get(day, DayCalendarCell(day, "Unknown", "Not recorded")),
                project.get(day, DayCalendarCell(day, "Unknown", "Not recorded")),
            )
            states = {
                "Working": "Satisfied",
                "NotWorking": "Blocked",
                "Unknown": "Pending",
            }
            occupied = (
                "Blocked"
                if day in occupancy
                else "Satisfied"
                if r.occupancy and r.occupancy.start_date <= day <= r.occupancy.end_date
                else "Pending"
            )
            checks = (
                ConstraintEvidence("CrewCalendar", states[a.state]),
                ConstraintEvidence("ProjectCalendar", states[b.state]),
                ConstraintEvidence("CrewOccupancy", occupied),
                *evidence.get(day, ()),
            )
            checks = tuple(sorted(checks, key=lambda c: CHECKS.index(c.check)))
            proposed = ProposedDay(day, checks)
            missing.extend(e for e in explain_day(proposed) if e.state == "Pending")
            reasons = []
            for scope, cell in (("CREW", a), ("PROJECT", b)):
                if cell.state != "Working":
                    reasons.append(f"{scope}_CALENDAR_{cell.state.upper()}")
                if cell.review_status in ("Stale", "Needs Review"):
                    reasons.append(
                        f"{scope}_CALENDAR_{cell.review_status.upper().replace(' ', '_')}"
                    )
            if {a.state, b.state} == {"Working", "NotWorking"}:
                reasons.append("CALENDAR_CONFLICT")
            reasons.extend(
                f"CONSTRAINT_BLOCKED:{c.check}"
                for c in checks
                if c.state == "Blocked"
                and c.check not in ("CrewCalendar", "ProjectCalendar")
            )
            if occupied == "Pending":
                reasons.append("CREW_OCCUPANCY_UNKNOWN")
            if date.fromordinal(ordinal).weekday() >= 5 and not any(
                e.check == "WeekendConsent" and e.state == "Satisfied" for e in checks
            ):
                reasons.append("WEEKEND_CONSENT_NOT_CONFIRMED")
            status = (
                "Blocked"
                if "NotWorking" in (a.state, b.state)
                else "Matched"
                if a.state == b.state == "Working"
                else "Pending"
            )
            scanned.append(
                ScannedDay(
                    day, a.state, b.state, status, occupied, not reasons, tuple(reasons)
                )
            )
            if not reasons:
                allocated.append(proposed)
            if len(allocated) == r.remaining.days:
                break
        if len(allocated) < r.remaining.days:
            review.append("INSUFFICIENT_CAPACITY_WITHIN_HORIZON")
    complete = not review
    option = (
        ExplicitDayOption(
            r.option_id, r.work_item_id, r.project_id, r.crew_id, tuple(allocated)
        )
        if complete
        else None
    )
    return GeneratedDayCandidate(
        r.option_id,
        r.project_id,
        r.work_item_id,
        r.crew_id,
        r.remaining.days if r.remaining else None,
        allocated[0].local_date if allocated else None,
        allocated[-1].local_date if complete else None,
        tuple(d.local_date for d in allocated),
        len(allocated),
        r.remaining.days - len(allocated) if r.remaining else None,
        tuple(scanned),
        tuple(d for d in scanned if not d.accumulated),
        sum(d.calendar_status == "Matched" for d in scanned),
        sum("CALENDAR_CONFLICT" in d.reasons for d in scanned),
        sum("Unknown" in (d.crew_state, d.project_state) for d in scanned),
        sum(d.calendar_status == "Blocked" for d in scanned),
        tuple(missing),
        tuple(review),
        option,
        "Validation pending" if complete else "Needs Review",
    )


@dataclass(frozen=True)
class DayGenerationComparison:
    candidates: tuple[GeneratedDayCandidate, ...]
    comparison: DayOptionComparison
    sort_basis: tuple[str, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def generate_days_and_compare(
    work_item_id,
    project_id,
    requests,
    *,
    max_options,
    order: SortOrder = "EarliestFinish",
):
    compare_day_options(
        work_item_id, project_id, (), max_options=max_options, order=order
    )
    if (
        type(requests) is not tuple
        or len(requests) > 100
        or any(not isinstance(r, DayGenerationRequest) for r in requests)
    ):
        raise ValueError("Supply at most 100 immutable daily scenarios.")
    if len({r.option_id for r in requests}) != len(requests):
        raise ValueError("Option IDs must be unique.")
    shared = {}
    for r in requests:
        if (r.work_item_id, r.project_id) != (work_item_id, project_id) or (
            r.remaining,
            r.required_crew_count,
        ) != (requests[0].remaining, requests[0].required_crew_count):
            raise ValueError(
                "Scenarios must share WorkItem/parent/confirmed remaining work."
            )
        cells = {c.local_date: c for c in r.project_calendar.cells}
        first, last = _range(r.earliest_start_date, r.horizon_end_date)
        for ordinal in range(first, last + 1):
            day = date.fromordinal(ordinal).isoformat()
            value = cells.get(day, DayCalendarCell(day, "Unknown", "Not recorded"))
            if day in shared and shared[day] != value:
                raise ValueError("Shared Project daily snapshots disagree.")
            shared[day] = value
    candidates = tuple(
        generate_day_candidate(r) for r in sorted(requests, key=lambda r: r.option_id)
    )
    comparison = compare_day_options(
        work_item_id,
        project_id,
        tuple(c.option for c in candidates if c.option is not None),
        max_options=max_options,
        order=order,
    )
    basis = (
        ("ProposedFinishDate", "ProposedStartDate")
        if order == "EarliestFinish"
        else ("ProposedStartDate", "ProposedFinishDate")
    )
    return DayGenerationComparison(
        candidates, comparison, (*basis, "CrewId", "OptionId")
    )
