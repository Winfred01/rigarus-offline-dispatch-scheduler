"""Read-only comparison of explicit options, not an allocator or safety validator.

Constraint evidence must come from independent, context-correct validators.
There are no production adapters yet. Missing evidence stays Pending; supplied
Satisfied results never certify dispatch or enable Apply/Publish in this slice.
"""

from dataclasses import dataclass, field, replace
from datetime import date
from typing import Literal

from .assignments import HalfDay, local_date

CheckState = Literal["Satisfied", "Blocked", "Pending"]
SortOrder = Literal["EarliestFinish", "EarliestStart"]
CHECKS = (
    "CrewCalendar",
    "ProjectCalendar",
    "EmployeeAvailability",
    "CrewType",
    "CrewOccupancy",
    "PersonnelConflicts",
    "ApprovedDriver",
    "Skills",
    "Qualifications",
    "Foreman",
    "MinimumStaffing",
    "RigAvailability",
    "RigConflicts",
    "WeekendConsent",
)
# Workload bounds, not business limits or a default workweek.
MAX_INPUT_OPTIONS = 100
MAX_HALF_DAYS = 732


def _positive_id(value: int):
    if type(value) is not int or not 1 <= value <= 2**53 - 1:
        raise ValueError("Supply a positive stable integer ID.")


@dataclass(frozen=True)
class ConstraintEvidence:
    check: str
    state: CheckState

    def __post_init__(self):
        if self.check not in CHECKS:
            raise ValueError("Unknown constraint evidence requires explicit support.")
        if self.state not in ("Satisfied", "Blocked", "Pending"):
            raise ValueError("Use Satisfied, Blocked or Pending evidence.")


@dataclass(frozen=True)
class ProposedSlot:
    local_date: str
    slot: HalfDay
    evidence: tuple[ConstraintEvidence, ...] = ()

    def __post_init__(self):
        local_date(self.local_date)
        if self.slot not in ("AM", "PM"):
            raise ValueError("Use an explicit AM or PM slot.")
        if type(self.evidence) is not tuple or any(
            not isinstance(item, ConstraintEvidence) for item in self.evidence
        ):
            raise ValueError("Supply immutable constraint evidence.")
        names = [item.check for item in self.evidence]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate constraint evidence requires resolution.")
        if (
            date.fromisoformat(self.local_date).weekday() < 5
            and "WeekendConsent" in names
        ):
            raise ValueError("Weekend consent evidence must target a weekend slot.")

    @property
    def key(self) -> tuple[str, str]:
        return self.local_date, self.slot


@dataclass(frozen=True)
class ExplicitOption:
    option_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    slots: tuple[ProposedSlot, ...]

    def __post_init__(self):
        for value in (self.option_id, self.work_item_id, self.project_id, self.crew_id):
            _positive_id(value)
        if (
            type(self.slots) is not tuple
            or not 1 <= len(self.slots) <= MAX_HALF_DAYS
            or any(not isinstance(item, ProposedSlot) for item in self.slots)
        ):
            raise ValueError("Supply 1 to 732 explicit immutable half-day slots.")
        keys = [item.key for item in self.slots]
        if len(keys) != len(set(keys)):
            raise ValueError("A Crew cannot occupy the same proposed slot twice.")
        first, last = min(keys)[0], max(keys)[0]
        if (date.fromisoformat(last) - date.fromisoformat(first)).days >= 366:
            raise ValueError("Supply an inclusive horizon of at most 366 local dates.")


@dataclass(frozen=True)
class SlotExplanation:
    local_date: str
    slot: HalfDay
    check: str
    state: CheckState
    source: Literal["Supplied", "Missing"]


@dataclass(frozen=True)
class EvaluatedOption:
    option: ExplicitOption
    start: tuple[str, str]
    finish: tuple[str, str]
    unplanned_half_days_between: int
    evidence_status: Literal["Blocked", "Pending", "AllSuppliedSatisfied"]
    explanations: tuple[SlotExplanation, ...]
    # Even complete supplied evidence is not independently validated here.
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


@dataclass(frozen=True)
class OptionComparison:
    work_item_id: int
    project_id: int
    order: SortOrder
    options: tuple[EvaluatedOption, ...]
    excluded: tuple[EvaluatedOption, ...]
    omitted_by_limit: int
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def _evaluate(option: ExplicitOption) -> EvaluatedOption:
    slots = tuple(
        replace(
            item,
            evidence=tuple(
                sorted(item.evidence, key=lambda check: CHECKS.index(check.check))
            ),
        )
        for item in sorted(option.slots, key=lambda item: item.key)
    )
    explanations = []
    for slot in slots:
        supplied = {item.check: item.state for item in slot.evidence}
        for check in CHECKS:
            if (
                check == "WeekendConsent"
                and date.fromisoformat(slot.local_date).weekday() < 5
            ):
                continue  # Weekday, not inferred consent on a weekend.
            explanations.append(
                SlotExplanation(
                    slot.local_date,
                    slot.slot,
                    check,
                    supplied.get(check, "Pending"),
                    "Supplied" if check in supplied else "Missing",
                )
            )
    states = {item.state for item in explanations}
    status = (
        "Blocked"
        if "Blocked" in states
        else "Pending"
        if "Pending" in states
        else "AllSuppliedSatisfied"
    )
    first, last = slots[0].key, slots[-1].key
    span = (date.fromisoformat(last[0]) - date.fromisoformat(first[0])).days * 2
    span += (last[1] == "PM") - (first[1] == "PM") + 1
    return EvaluatedOption(
        replace(option, slots=slots),
        first,
        last,
        span - len(slots),
        status,
        tuple(explanations),
    )


def compare_explicit_options(
    work_item_id: int,
    project_id: int,
    options: tuple[ExplicitOption, ...],
    *,
    max_options: int,
    order: SortOrder = "EarliestFinish",
) -> OptionComparison:
    """Hard-filter, explain, sort, then limit; never generate dates or write state.

    Compare only options for the same WorkItem/parent Project, supplied by a
    caller. Duration, multi-Crew coverage, actual workers/Rig, locks and source
    revisions still need the future generator/validators/#18 and #29 Apply.
    Dates are proposed boundaries, never certified completion of remaining work.
    """
    _positive_id(work_item_id)
    _positive_id(project_id)
    if order not in ("EarliestFinish", "EarliestStart"):
        raise ValueError("Select EarliestFinish or EarliestStart.")
    if type(max_options) is not int or not 1 <= max_options <= 10:
        raise ValueError("Request 1 to 10 comparison options.")
    if (
        type(options) is not tuple
        or len(options) > MAX_INPUT_OPTIONS
        or any(not isinstance(item, ExplicitOption) for item in options)
    ):
        raise ValueError("Supply at most 100 immutable explicit options.")
    if len({item.option_id for item in options}) != len(options):
        raise ValueError("Option IDs must be unique within the comparison snapshot.")
    if any(
        (item.work_item_id, item.project_id) != (work_item_id, project_id)
        for item in options
    ):
        raise ValueError("Options must share the intended WorkItem and parent Project.")
    evaluated = tuple(_evaluate(item) for item in options)
    excluded = tuple(
        sorted(
            (item for item in evaluated if item.evidence_status == "Blocked"),
            key=lambda item: item.option.option_id,
        )
    )
    remaining = [item for item in evaluated if item.evidence_status != "Blocked"]
    remaining.sort(
        key=lambda item: (
            (item.finish, item.start)
            if order == "EarliestFinish"
            else (item.start, item.finish),
            item.option.crew_id,
            item.option.option_id,
        )
    )
    return OptionComparison(
        work_item_id,
        project_id,
        order,
        tuple(remaining[:max_options]),
        excluded,
        max(0, len(remaining) - max_options),
    )
