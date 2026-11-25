"""Slotless daily evidence resolution, independent of I/O and system time."""

from dataclasses import dataclass
from datetime import date

from .availability import range_dates
from .day_drafts import legacy_day_observation

SCOPES = ("Crew", "Project", "Employee")


def states_for(scope):
    if scope not in SCOPES:
        raise ValueError(
            "Choose Crew, Project or Employee; WorkItems inherit Project calendars."
        )
    return (
        ("Available", "Unavailable", "Unknown")
        if scope == "Employee"
        else ("Working", "NotWorking", "Unknown")
    )


@dataclass(frozen=True)
class DailyInput:
    start_date: str
    end_date: str
    state: str
    confirmed_by_operator: bool
    legacy_reviewed: bool = False
    notes: str = ""

    def __post_init__(self):
        range_dates(self.start_date, self.end_date)
        if self.state not in (
            "Working",
            "NotWorking",
            "Available",
            "Unavailable",
            "Unknown",
        ):
            raise ValueError("Choose an explicit daily state.")
        if self.confirmed_by_operator is not True:
            raise ValueError(
                "Explicit operator confirmation of this daily assertion is required."
            )
        if type(self.legacy_reviewed) is not bool:
            raise ValueError("Legacy review must be explicitly boolean.")
        if (
            not isinstance(self.notes, str)
            or len(self.notes) > 2000
            or "\0" in self.notes
        ):
            raise ValueError("Notes must contain at most 2000 characters without NUL.")


def resolve_daily(scope, daily_state, halves, *, stale=False, legacy_reviewed=False):
    positive, negative, unknown = states_for(scope)
    if daily_state is not None and daily_state not in (positive, negative, unknown):
        raise ValueError("Daily state does not match its owner scope.")
    legacy = legacy_day_observation(
        "Availability" if scope == "Employee" else "Calendar", halves
    )
    blocked = any(r["state"] == negative for r in halves)
    if daily_state is None:
        state = negative if blocked else unknown
        review = "Needs Review" if halves else "Not recorded"
    elif stale or (halves and not legacy_reviewed):
        state = negative if blocked or daily_state == negative else unknown
        review = "Stale" if stale else "Needs Review"
    else:
        state = daily_state
        review = "Current"
    return dict(
        state=state,
        state_label="Not recorded"
        if scope == "Employee" and state == unknown
        else state,
        recorded_state=daily_state,
        review_status=review,
        needs_review=state == unknown or review in ("Stale", "Needs Review"),
        known_blocked=state == negative,
        legacy=legacy,
        legacy_reviewed=legacy_reviewed,
        validation_status="Pending",
        applyable=False,
        publishable=False,
    )


def assess_daily(day, crew, project):
    status = (
        "Blocked"
        if crew["known_blocked"] or project["known_blocked"]
        else "Matched"
        if crew["state"] == project["state"] == "Working"
        else "Pending"
    )
    return dict(
        local_date=day,
        status=status,
        crew=crew,
        project=project,
        weekend_consent="Pending"
        if date.fromisoformat(day).weekday() >= 5
        else "Not applicable",
        validation_status="Pending",
        applyable=False,
        publishable=False,
    )
