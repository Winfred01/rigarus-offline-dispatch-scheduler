"""Slotless full-day planning contracts. No legacy duration conversion."""

from dataclasses import dataclass

from .assignments import local_date


def positive_id(value):
    if type(value) is not int or not 1 <= value <= 2**53 - 1:
        raise ValueError("Supply a positive integer identifier or day count.")


@dataclass(frozen=True)
class ConfirmedRemainingDays:
    days: int
    confirmed_by_operator: bool

    def __post_init__(self):
        positive_id(self.days)
        if self.confirmed_by_operator is not True:
            raise ValueError(
                "Remaining Days must be explicitly confirmed by the operator."
            )


@dataclass(frozen=True)
class DayDraft:
    work_item_id: int
    crew_id: int
    local_date: str
    notes: str = ""
    employee_ids: tuple[int, ...] | None = None

    def __post_init__(self):
        positive_id(self.work_item_id)
        positive_id(self.crew_id)
        local_date(self.local_date)
        if (
            not isinstance(self.notes, str)
            or len(self.notes) > 2000
            or "\0" in self.notes
        ):
            raise ValueError("Notes must contain at most 2000 characters without NUL.")
        if self.employee_ids is not None:
            if type(self.employee_ids) is not tuple or len(self.employee_ids) > 1000:
                raise ValueError("Supply at most 1000 explicit immutable Employee IDs.")
            for value in self.employee_ids:
                positive_id(value)
            if len(set(self.employee_ids)) != len(self.employee_ids):
                raise ValueError("Select each employee only once.")
            object.__setattr__(self, "employee_ids", tuple(sorted(self.employee_ids)))


def legacy_day_observation(kind, halves):
    """Coverage observation only, never conversion or dispatch approval."""
    states = {x["slot"]: x["state"] for x in halves}
    if len(states) != len(halves) or any(s not in ("AM", "PM") for s in states):
        raise ValueError("Duplicate or invalid legacy evidence slots.")
    positive, negative = {
        "Calendar": ("Working", "NotWorking"),
        "Availability": ("Available", "Unavailable"),
    }[kind]
    complete = set(states) == {"AM", "PM"}
    values = set(states.values())
    observation = (
        negative
        if negative in values
        else positive
        if complete and values == {positive}
        else "Unknown"
    )
    return {
        "daily_observation": observation,
        "complete_legacy_coverage": complete,
        "mixed_or_partial": not complete or len(values) > 1,
        "compatibility_status": "Needs Review",
        "conversion_required": True,
        "original_halves": halves,
    }
