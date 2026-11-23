"""Recorded availability is not attendance, leave approval or dispatch eligibility."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from .assignments import local_date

AvailabilityState = Literal["Available", "Unavailable", "Unknown"]
AvailabilitySlot = Literal["FullDay", "AM", "PM"]


class AvailabilityConflict(ValueError):
    pass


class EmployeeNotFound(ValueError):
    pass


def range_dates(start: str, end: str) -> tuple[str, ...]:
    start_day = date.fromisoformat(local_date(start))
    end_day = date.fromisoformat(local_date(end))
    length = (end_day - start_day).days + 1
    if length < 1:
        raise ValueError("End date must be on or after start date.")
    if length > 366:
        raise ValueError("Choose at most 366 dates per operation.")
    return tuple((start_day + timedelta(days=i)).isoformat() for i in range(length))


@dataclass(frozen=True)
class AvailabilityDraft:
    start_date: str
    end_date: str
    slot: AvailabilitySlot
    state: AvailabilityState

    def __post_init__(self):
        range_dates(self.start_date, self.end_date)
        if self.slot not in ("FullDay", "AM", "PM"):
            raise ValueError("Select Full day, AM or PM.")
        if self.state not in ("Available", "Unavailable", "Unknown"):
            raise ValueError("Select Available, Unavailable or Not recorded.")

    def cells(self):
        slots = ("AM", "PM") if self.slot == "FullDay" else (self.slot,)
        return tuple(
            (day, slot)
            for day in range_dates(self.start_date, self.end_date)
            for slot in slots
        )
