"""Explicit Crew/WorkItem calendars, not dispatch or recommendation eligibility.

No inferred workweek, holiday feed, override precedence, persistence or I/O.
Callers must supply separate crew/work-item snapshots for the intended IDs.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from .assignments import AssignmentDraft, HalfDay, local_date

CalendarScope = Literal["Crew", "WorkItem"]
WorkState = Literal["Working", "NotWorking", "Unknown"]
CalendarStatus = Literal["Matched", "Blocked", "Pending"]


@dataclass(frozen=True)
class WorkCalendarCell:
    local_date: str
    slot: HalfDay
    state: WorkState

    def __post_init__(self):
        local_date(self.local_date)
        if self.slot not in ("AM", "PM"):
            raise ValueError("Select AM or PM.")
        if self.state not in ("Working", "NotWorking", "Unknown"):
            raise ValueError("Select Working, NotWorking or Unknown.")


@dataclass(frozen=True)
class WorkCalendar:
    scope: CalendarScope
    entity_id: int
    cells: tuple[WorkCalendarCell, ...] = ()

    def __post_init__(self):
        if self.scope not in ("Crew", "WorkItem"):
            raise ValueError("Calendar scope must be Crew or WorkItem.")
        if type(self.entity_id) is not int or not 1 <= self.entity_id <= 2**53 - 1:
            raise ValueError("Use a stable Crew or WorkItem ID.")
        if type(self.cells) is not tuple or any(
            not isinstance(cell, WorkCalendarCell) for cell in self.cells
        ):
            raise ValueError("Supply an immutable tuple of calendar cells.")
        keys = [(cell.local_date, cell.slot) for cell in self.cells]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate calendar cells require explicit resolution.")

    def state_at(self, day: str, slot: HalfDay) -> WorkState:
        local_date(day)
        if slot not in ("AM", "PM"):
            raise ValueError("Select AM or PM.")
        return next(
            (
                cell.state
                for cell in self.cells
                if cell.local_date == day and cell.slot == slot
            ),
            "Unknown",
        )


@dataclass(frozen=True)
class CalendarReason:
    code: str
    scope: Literal["Crew", "WorkItem", "Combined", "Weekend"]
    entity_id: int | None


@dataclass(frozen=True)
class CalendarAssessment:
    crew_id: int
    work_item_id: int
    local_date: str
    slot: HalfDay
    crew_state: WorkState
    work_item_state: WorkState
    status: CalendarStatus
    reasons: tuple[CalendarReason, ...]
    # Matched means only the two explicit calendar cells agree on Working.
    # Neither callers nor calendar matching may supply a positive safety flag.
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    publishable: Literal[False] = field(default=False, init=False)


def assess_draft_calendar(
    draft: AssignmentDraft, crew: WorkCalendar, work_item: WorkCalendar
) -> CalendarAssessment:
    """Read-only assessment, retaining every source's explanation in fixed order.

    A known NotWorking blocks even when the other source is unknown. Opposite
    explicit states add a conflict reason; neither calendar overrides the other.
    Weekend approval is intentionally unresolved, including on a Matched cell.
    Employee availability, personnel collisions, driver/skill/Rig checks and
    operator approval are separate responsibilities, never inferred here.
    """
    if not isinstance(draft, AssignmentDraft):
        raise ValueError("Supply an assignment draft, not a persisted status change.")
    if not isinstance(crew, WorkCalendar) or not isinstance(work_item, WorkCalendar):
        raise ValueError("Supply explicit Crew and WorkItem calendars.")
    if (crew.scope, crew.entity_id) != ("Crew", draft.crew_id) or (
        work_item.scope,
        work_item.entity_id,
    ) != ("WorkItem", draft.work_item_id):
        raise ValueError("Calendar scope and ID must match the draft.")
    crew_state = crew.state_at(draft.local_date, draft.slot)
    work_state = work_item.state_at(draft.local_date, draft.slot)
    states = (crew_state, work_state)
    status: CalendarStatus = (
        "Blocked"
        if "NotWorking" in states
        else "Pending"
        if "Unknown" in states
        else "Matched"
    )
    codes = {
        "Working": "RECORDED_WORKING",
        "NotWorking": "RECORDED_NOT_WORKING",
        "Unknown": "CALENDAR_NOT_RECORDED",
    }
    reasons = [
        CalendarReason(codes[crew_state], "Crew", crew.entity_id),
        CalendarReason(codes[work_state], "WorkItem", work_item.entity_id),
    ]
    if set(states) == {"Working", "NotWorking"}:
        reasons.append(CalendarReason("CALENDAR_CONFLICT", "Combined", None))
    if date.fromisoformat(draft.local_date).weekday() >= 5:
        reasons.append(CalendarReason("WEEKEND_APPROVAL_PENDING", "Weekend", None))
    return CalendarAssessment(
        draft.crew_id,
        draft.work_item_id,
        draft.local_date,
        draft.slot,
        crew_state,
        work_state,
        status,
        tuple(reasons),
    )


def assess_calendar_range(
    crew: WorkCalendar, work_item: WorkCalendar, start_date: str, end_date: str
) -> tuple[CalendarAssessment, ...]:
    """At most 366 inclusive local dates, each AM then PM; no instant arithmetic.

    Range length is an engineering workload bound, not a business workweek.
    Returned cells are explanations, not reservations or proposed assignments.
    """
    if not isinstance(crew, WorkCalendar) or not isinstance(work_item, WorkCalendar):
        raise ValueError("Supply explicit Crew and WorkItem calendars.")
    first = date.fromisoformat(local_date(start_date)).toordinal()
    last = date.fromisoformat(local_date(end_date)).toordinal()
    if not 1 <= last - first + 1 <= 366:
        raise ValueError("Choose an ordered range of at most 366 local dates.")
    return tuple(
        assess_draft_calendar(
            AssignmentDraft(work_item.entity_id, crew.entity_id, day, slot),
            crew,
            work_item,
        )
        for ordinal in range(first, last + 1)
        for day in (date.fromordinal(ordinal).isoformat(),)
        for slot in ("AM", "PM")
    )
