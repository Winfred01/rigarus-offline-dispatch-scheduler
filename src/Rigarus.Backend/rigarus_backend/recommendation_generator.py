"""Pure, bounded single-Crew planning; no safety certification or persistence.

The caller resolves the WorkItem's real parent and supplies context-correct
snapshots. Evidence is scoped to this request's WorkItem/Project/Crew and slot;
no production adapter verifies freshness or actual workers/Rig in this slice.
"""

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from .assignments import AssignmentDraft, HalfDay, local_date
from .recommendation_comparison import (
    MAX_INPUT_OPTIONS,
    ConstraintEvidence,
    ExplicitOption,
    OptionComparison,
    ProposedSlot,
    SlotExplanation,
    SortOrder,
    compare_explicit_options,
)
from .work_calendars import (
    CalendarAssessment,
    WorkCalendar,
    WorkCalendarCell,
    assess_project_calendar,
)


def _positive(value: int, name: str):
    if type(value) is not int or not 1 <= value <= 2**53 - 1:
        raise ValueError(f"{name} must be a positive stable integer.")


def _range(start: str, end: str):
    first = date.fromisoformat(local_date(start))
    last = date.fromisoformat(local_date(end))
    # Exclusive annual anniversary, clamping Feb 29 to Feb 28. Dates near
    # date.max remain usable without overflowing into year 10000.
    anniversary = (
        date(
            first.year + 1,
            first.month,
            min(first.day, monthrange(first.year + 1, first.month)[1]),
        )
        if first.year < 9999
        else None
    )
    if (
        last < first
        or (last - first).days >= 366
        or (anniversary is not None and last >= anniversary)
    ):
        raise ValueError(
            "Use an ordered inclusive horizon within 12 months / 366 dates."
        )
    return first.toordinal(), last.toordinal()


@dataclass(frozen=True, order=True)
class DateSlot:
    local_date: str
    slot: HalfDay

    def __post_init__(self):
        local_date(self.local_date)
        if self.slot not in ("AM", "PM"):
            raise ValueError("Use an explicit AM or PM slot.")


@dataclass(frozen=True)
class CrewOccupancySnapshot:
    """Complete active occupancy for this Crew within the declared range only.

    Empty is explicitly known free in that range. None on a request means
    occupancy is missing, never known free. Saved visits are not work completed.
    """

    crew_id: int
    start_date: str
    end_date: str
    occupied: tuple[DateSlot, ...]

    def __post_init__(self):
        _positive(self.crew_id, "Crew ID")
        _range(self.start_date, self.end_date)
        if (
            type(self.occupied) is not tuple
            or len(self.occupied) > 732
            or any(not isinstance(item, DateSlot) for item in self.occupied)
        ):
            raise ValueError("Supply at most 732 immutable occupied slots.")
        if len(set(self.occupied)) != len(self.occupied):
            raise ValueError("Duplicate occupied slots require resolution.")
        if any(
            not self.start_date <= item.local_date <= self.end_date
            for item in self.occupied
        ):
            raise ValueError("Occupied slots must be within their snapshot range.")


@dataclass(frozen=True)
class GenerationRequest:
    option_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    required_crew_count: int
    confirmed_remaining_half_days: int | None
    remaining_confirmed_by_operator: bool
    earliest_start_date: str
    horizon_end_date: str
    crew_calendar: WorkCalendar
    project_calendar: WorkCalendar
    occupancy: CrewOccupancySnapshot | None = None
    slot_evidence: tuple[ProposedSlot, ...] = ()

    def __post_init__(self):
        for name in (
            "option_id",
            "work_item_id",
            "project_id",
            "crew_id",
            "required_crew_count",
        ):
            _positive(getattr(self, name), name)
        if self.confirmed_remaining_half_days is not None:
            _positive(self.confirmed_remaining_half_days, "Remaining Half-days")
        if type(self.remaining_confirmed_by_operator) is not bool:
            raise ValueError("Explicit operator confirmation must be boolean.")
        _range(self.earliest_start_date, self.horizon_end_date)
        for calendar, scope, entity_id in (
            (self.crew_calendar, "Crew", self.crew_id),
            (self.project_calendar, "Project", self.project_id),
        ):
            if not isinstance(calendar, WorkCalendar) or (
                calendar.scope,
                calendar.entity_id,
            ) != (scope, entity_id):
                raise ValueError(
                    "Calendar scope/ID must match Crew and parent Project."
                )
            if len(calendar.cells) > 732 or any(
                not self.earliest_start_date <= item.local_date <= self.horizon_end_date
                for item in calendar.cells
            ):
                raise ValueError(
                    "Calendar snapshots must be restricted to the requested horizon."
                )
        if self.occupancy is not None and (
            not isinstance(self.occupancy, CrewOccupancySnapshot)
            or self.occupancy.crew_id != self.crew_id
            or self.occupancy.start_date < self.earliest_start_date
            or self.occupancy.end_date > self.horizon_end_date
        ):
            raise ValueError(
                "Occupancy snapshot must match the Crew and requested horizon."
            )
        if (
            type(self.slot_evidence) is not tuple
            or len(self.slot_evidence) > 732
            or any(not isinstance(item, ProposedSlot) for item in self.slot_evidence)
        ):
            raise ValueError("Supply at most 732 immutable per-slot evidence records.")
        if len({item.key for item in self.slot_evidence}) != len(self.slot_evidence):
            raise ValueError("Duplicate evidence slots require resolution.")
        for item in self.slot_evidence:
            if not self.earliest_start_date <= item.local_date <= self.horizon_end_date:
                raise ValueError("Evidence must be within the requested horizon.")
            if any(
                check.check in ("CrewCalendar", "ProjectCalendar", "CrewOccupancy")
                for check in item.evidence
            ):
                raise ValueError(
                    "Calendar/occupancy evidence is derived only from snapshots."
                )


@dataclass(frozen=True)
class ScannedSlot:
    calendar: CalendarAssessment
    accumulated: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedCandidate:
    option_id: int
    project_id: int
    work_item_id: int
    crew_id: int
    confirmed_remaining_half_days: int | None
    remaining_confirmed_by_operator: bool
    proposed_start: DateSlot | None
    proposed_finish: DateSlot | None
    slots: tuple[ProposedSlot, ...]
    generated_half_days: int
    unfilled_half_days: int | None
    scanned: tuple[ScannedSlot, ...]
    skipped: tuple[ScannedSlot, ...]
    calendar_matches: int
    calendar_conflicts: int
    calendar_unknowns: int
    calendar_blocked: int
    missing_evidence: tuple[SlotExplanation, ...]
    review_reasons: tuple[str, ...]
    option: ExplicitOption | None
    status: Literal["Validation pending", "Needs Review"]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def generate_candidate(request: GenerationRequest) -> GeneratedCandidate:
    """Generate the earliest cumulative plan for one explicit Crew scenario.

    Linear scan/index work, H <= 732 half-days; comparator sorts O(H log H).
    Incomplete plans have
    no proposed finish or comparator option. Gaps never reset accumulated work.
    Calendar/consent/known blocks govern accumulation; other missing safety
    evidence permits planning only and remains Pending, including missing
    occupancy coverage. No estimate or saved visit is used as remaining work.
    """
    if not isinstance(request, GenerationRequest):
        raise ValueError("Supply an immutable GenerationRequest.")
    r = request
    review = []
    if r.required_crew_count != 1:
        review.append("MULTI_CREW_REQUIRES_REVIEW")
    if r.confirmed_remaining_half_days is None:
        review.append("REMAINING_HALF_DAYS_MISSING")
    if not r.remaining_confirmed_by_operator:
        review.append("REMAINING_HALF_DAYS_NOT_CONFIRMED")
    crew_cells = {(x.local_date, x.slot): x for x in r.crew_calendar.cells}
    project_cells = {(x.local_date, x.slot): x for x in r.project_calendar.cells}
    evidence = {x.key: x.evidence for x in r.slot_evidence}
    occupied = set(r.occupancy.occupied) if r.occupancy else set()
    scanned, slots = [], []
    if not review:
        first, last = _range(r.earliest_start_date, r.horizon_end_date)
        for ordinal in range(first, last + 1):
            day = date.fromordinal(ordinal).isoformat()
            for half in ("AM", "PM"):
                key = (day, half)
                crew_cell = crew_cells.get(key, WorkCalendarCell(day, half, "Unknown"))
                project_cell = project_cells.get(
                    key, WorkCalendarCell(day, half, "Unknown")
                )
                assessment = assess_project_calendar(
                    AssignmentDraft(r.work_item_id, r.crew_id, day, half),
                    WorkCalendar("Crew", r.crew_id, (crew_cell,)),
                    WorkCalendar("Project", r.project_id, (project_cell,)),
                )
                occupancy_state = (
                    "Blocked"
                    if DateSlot(day, half) in occupied
                    else "Satisfied"
                    if r.occupancy
                    and r.occupancy.start_date <= day <= r.occupancy.end_date
                    else "Pending"
                )
                states = {
                    "Working": "Satisfied",
                    "NotWorking": "Blocked",
                    "Unknown": "Pending",
                }
                checks = (
                    ConstraintEvidence("CrewCalendar", states[crew_cell.state]),
                    ConstraintEvidence("ProjectCalendar", states[project_cell.state]),
                    ConstraintEvidence("CrewOccupancy", occupancy_state),
                    *evidence.get(key, ()),
                )
                supplied = {x.check: x.state for x in checks}
                reasons = [
                    f"{scope.upper()}_CALENDAR_{cell.state.upper()}"
                    for scope, cell in (("Crew", crew_cell), ("Project", project_cell))
                    if cell.state != "Working"
                ]
                if any(x.code == "CALENDAR_CONFLICT" for x in assessment.reasons):
                    reasons.append("CALENDAR_CONFLICT")
                reasons.extend(
                    f"CONSTRAINT_BLOCKED:{x.check}"
                    for x in checks
                    if x.state == "Blocked"
                    and x.check not in ("CrewCalendar", "ProjectCalendar")
                )
                if (
                    date.fromordinal(ordinal).weekday() >= 5
                    and supplied.get("WeekendConsent") != "Satisfied"
                ):
                    reasons.append("WEEKEND_CONSENT_NOT_CONFIRMED")
                scanned.append(ScannedSlot(assessment, not reasons, tuple(reasons)))
                if not reasons:
                    slots.append(ProposedSlot(day, half, checks))
                if len(slots) == r.confirmed_remaining_half_days:
                    break
            if len(slots) == r.confirmed_remaining_half_days:
                break
        if len(slots) < r.confirmed_remaining_half_days:
            review.append("INSUFFICIENT_CAPACITY_WITHIN_HORIZON")
    proposed = (
        ExplicitOption(
            r.option_id, r.work_item_id, r.project_id, r.crew_id, tuple(slots)
        )
        if slots
        else None
    )
    # Reuse the comparator's canonical independent-check explanations even for
    # partial accumulation; never expose that partial plan as a complete option.
    explanations = (
        compare_explicit_options(
            r.work_item_id, r.project_id, (proposed,), max_options=1
        )
        .options[0]
        .explanations
        if proposed
        else ()
    )
    complete = not review
    return GeneratedCandidate(
        option_id=r.option_id,
        project_id=r.project_id,
        work_item_id=r.work_item_id,
        crew_id=r.crew_id,
        confirmed_remaining_half_days=r.confirmed_remaining_half_days,
        remaining_confirmed_by_operator=r.remaining_confirmed_by_operator,
        proposed_start=DateSlot(slots[0].local_date, slots[0].slot) if slots else None,
        proposed_finish=DateSlot(slots[-1].local_date, slots[-1].slot)
        if complete
        else None,
        slots=tuple(slots),
        generated_half_days=len(slots),
        unfilled_half_days=(
            r.confirmed_remaining_half_days - len(slots)
            if r.confirmed_remaining_half_days is not None
            else None
        ),
        scanned=tuple(scanned),
        skipped=tuple(x for x in scanned if not x.accumulated),
        calendar_matches=sum(x.calendar.status == "Matched" for x in scanned),
        calendar_conflicts=sum(
            any(reason.code == "CALENDAR_CONFLICT" for reason in x.calendar.reasons)
            for x in scanned
        ),
        calendar_unknowns=sum(
            "Unknown" in (x.calendar.crew_state, x.calendar.work_item_state)
            for x in scanned
        ),
        calendar_blocked=sum(x.calendar.status == "Blocked" for x in scanned),
        missing_evidence=tuple(x for x in explanations if x.state == "Pending"),
        review_reasons=tuple(review),
        option=proposed if complete else None,
        status="Validation pending" if complete else "Needs Review",
    )


@dataclass(frozen=True)
class GenerationComparison:
    candidates: tuple[GeneratedCandidate, ...]
    comparison: OptionComparison
    sort_basis: tuple[str, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def generate_and_compare(
    work_item_id: int,
    project_id: int,
    requests: tuple[GenerationRequest, ...],
    *,
    max_options: int,
    order: SortOrder = "EarliestFinish",
) -> GenerationComparison:
    """Alternative scenarios, not simultaneous reservations or joint schedules.

    One earliest plan per request; never enumerate an unbounded combinatorial
    search. Keep incomplete diagnostics outside the ranked complete options.
    """
    # Validate comparison settings and context before any scan, including empty.
    compare_explicit_options(
        work_item_id, project_id, (), max_options=max_options, order=order
    )
    if (
        type(requests) is not tuple
        or len(requests) > MAX_INPUT_OPTIONS
        or any(not isinstance(x, GenerationRequest) for x in requests)
    ):
        raise ValueError("Supply at most 100 immutable generation requests.")
    if len({x.option_id for x in requests}) != len(requests):
        raise ValueError("Option IDs must be unique.")
    if any(
        (x.work_item_id, x.project_id) != (work_item_id, project_id) for x in requests
    ):
        raise ValueError("Requests must share the WorkItem and parent Project.")
    if (
        len(
            {
                (
                    x.required_crew_count,
                    x.confirmed_remaining_half_days,
                    x.remaining_confirmed_by_operator,
                )
                for x in requests
            }
        )
        > 1
    ):
        raise ValueError(
            "Compare the same confirmed remaining work and Crew requirement."
        )
    # A shared Project cannot have different working states in overlapping
    # scenarios. Missing cells are Unknown, including an explicitly blank one.
    shared_project = {}
    for request in requests:
        recorded = {
            (x.local_date, x.slot): x.state for x in request.project_calendar.cells
        }
        first, last = _range(request.earliest_start_date, request.horizon_end_date)
        for ordinal in range(first, last + 1):
            for half in ("AM", "PM"):
                key = (date.fromordinal(ordinal).isoformat(), half)
                state = recorded.get(key, "Unknown")
                if shared_project.setdefault(key, state) != state:
                    raise ValueError(
                        "Conflicting shared Project calendar snapshots require resolution."
                    )
    results = tuple(
        generate_candidate(x) for x in sorted(requests, key=lambda x: x.option_id)
    )
    comparison = compare_explicit_options(
        work_item_id,
        project_id,
        tuple(x.option for x in results if x.option is not None),
        max_options=max_options,
        order=order,
    )
    return GenerationComparison(
        results,
        comparison,
        (
            ("Proposed finish", "Proposed start")
            if order == "EarliestFinish"
            else ("Proposed start", "Proposed finish")
        )
        + ("Crew ID", "Option ID"),
    )
