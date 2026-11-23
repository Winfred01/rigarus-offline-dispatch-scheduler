import re
from dataclasses import dataclass, field
from datetime import date
from typing import Literal
from .staffing import StaffingState

HalfDay = Literal["AM", "PM"]


def local_date(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value
    ):
        raise ValueError("Enter a local date as YYYY-MM-DD.")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Enter a valid local calendar date.") from error
    return value


@dataclass(frozen=True)
class AssignmentDraft:
    work_item_id: int
    crew_id: int
    local_date: str
    slot: HalfDay
    notes: str = ""

    def __post_init__(self):
        for value in (self.work_item_id, self.crew_id):
            if type(value) is not int or not 1 <= value <= 9_007_199_254_740_991:
                raise ValueError("Select an existing work item and Crew.")
        local_date(self.local_date)
        if self.slot not in ("AM", "PM"):
            raise ValueError("Select AM or PM (provisional Demo B granularity).")
        if (
            not isinstance(self.notes, str)
            or len(self.notes) > 2000
            or "\0" in self.notes
        ):
            raise ValueError(
                "Assignment notes must contain at most 2000 characters and no null character."
            )


@dataclass(frozen=True)
class DraftAssignment:
    id: int
    work_item_id: int
    crew_id: int
    local_date: str
    slot: HalfDay
    notes: str
    status: Literal["Draft", "Cancelled"]
    revision: int
    created_at: str
    updated_at: str
    project_id: int
    job_number: str
    site_id: str
    site_name: str
    work_type: str
    required_crew_count: int
    estimated_half_days: int
    crew_name: str
    crew_active: bool
    validation_status: Literal["Pending"] = "Pending"
    publishable: bool = False
    staffing: StaffingState = field(default_factory=StaffingState)
    calendar_assessment: dict | None = None


class AssignmentNotFound(ValueError):
    pass


class AssignmentConflict(ValueError):
    pass


def check_revision(record: DraftAssignment, expected_revision: int | None):
    if record.revision != expected_revision:
        raise AssignmentConflict(
            "This assignment changed. Reload assignments before saving again."
        )
