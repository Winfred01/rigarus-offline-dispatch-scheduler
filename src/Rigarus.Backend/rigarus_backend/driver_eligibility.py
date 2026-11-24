"""Dated company approval checks, independent of storage and publication."""

from dataclasses import dataclass, field
from typing import Literal

from .assignments import local_date
from .availability import range_dates
from .personnel_conflicts import StaffedVisit, validate_employee_conflicts
from .recommendation_comparison import CheckState, _positive_id

DRIVER_STATES = ("Unverified", "Active", "Suspended", "Expired")
MAX_EVIDENCE = 100_000


@dataclass(frozen=True)
class DriverApprovalDraft:
    start_date: str
    end_date: str
    slot: Literal["AM", "PM", "FullDay"]
    state: Literal["Unverified", "Active", "Suspended", "Expired"]
    company_confirmed: bool
    reference: str

    def __post_init__(self):
        range_dates(self.start_date, self.end_date)
        if self.slot not in ("AM", "PM", "FullDay") or self.state not in DRIVER_STATES:
            raise ValueError("Choose an explicit half-day and company driver state.")
        if self.company_confirmed is not True:
            raise ValueError("Explicit company confirmation is required.")
        if (
            not isinstance(self.reference, str)
            or not 1 <= len(self.reference.strip()) <= 200
            or "\x00" in self.reference
        ):
            raise ValueError(
                "Supply a company evidence reference of 1 to 200 characters."
            )
        object.__setattr__(self, "reference", self.reference.strip())

    def cells(self):
        return tuple(
            (day, half)
            for day in range_dates(self.start_date, self.end_date)
            for half in ("AM", "PM")
            if self.slot in (half, "FullDay")
        )


@dataclass(frozen=True)
class DriverCell:
    employee_id: int
    local_date: str
    slot: Literal["AM", "PM"]
    state: Literal["Unverified", "Active", "Suspended", "Expired"]
    change_id: int
    company_confirmed: bool

    def __post_init__(self):
        _positive_id(self.employee_id)
        _positive_id(self.change_id)
        if self.company_confirmed is not True:
            raise ValueError("Driver cells require explicit company confirmation.")
        local_date(self.local_date)
        if self.slot not in ("AM", "PM") or self.state not in DRIVER_STATES:
            raise ValueError("Supply an explicit dated driver state.")


@dataclass(frozen=True)
class DriverWorker:
    employee_id: int
    active: bool
    # Sparse recorded availability, not inferred attendance.
    availability: tuple[tuple[str, str, str], ...]

    def __post_init__(self):
        _positive_id(self.employee_id)
        if type(self.active) is not bool or type(self.availability) is not tuple:
            raise ValueError("Supply immutable explicit employee observations.")
        if len(self.availability) > 732:
            raise ValueError("Availability exceeds the annual slot bound.")
        seen = set()
        for entry in self.availability:
            if type(entry) is not tuple or len(entry) != 3:
                raise ValueError("Supply dated availability tuples.")
            day, half, state = entry
            local_date(day)
            if half not in ("AM", "PM") or state not in (
                "Available",
                "Unavailable",
                "Unknown",
            ):
                raise ValueError("Invalid recorded availability.")
            if (day, half) in seen:
                raise ValueError("Duplicate availability requires resolution.")
            seen.add((day, half))
        object.__setattr__(self, "availability", tuple(sorted(self.availability)))


@dataclass(frozen=True)
class WorkerDriverCheck:
    employee_id: int
    state: CheckState
    approval_state: str
    approval_change_id: int | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class VisitDriverCheck:
    visit: StaffedVisit
    state: CheckState
    eligible_employee_ids: tuple[int, ...]
    workers: tuple[WorkerDriverCheck, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DriverValidation:
    checks: tuple[VisitDriverCheck, ...]
    state: CheckState
    scope: Literal["SavedDraftCompanyDriverApproval"] = field(
        default="SavedDraftCompanyDriverApproval", init=False
    )
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_drivers(
    visits: tuple[StaffedVisit, ...],
    workers: tuple[DriverWorker, ...],
    approvals: tuple[DriverCell, ...],
    *,
    start_date: str,
    end_date: str,
    scope_complete: bool,
) -> DriverValidation:
    """At least one definitely eligible actual worker, never a home-roster guess.

    Company approval only. Actual Rig/category, weekend consent, other staffing
    requirements and final approval remain independent, including on Satisfied.
    """
    personnel = validate_employee_conflicts(
        visits, start_date=start_date, end_date=end_date, scope_complete=scope_complete
    )
    if (
        type(workers) is not tuple
        or type(approvals) is not tuple
        or len(workers) + len(approvals) > MAX_EVIDENCE
        or any(not isinstance(w, DriverWorker) for w in workers)
        or any(not isinstance(c, DriverCell) for c in approvals)
        or sum(len(w.availability) for w in workers) > MAX_EVIDENCE
    ):
        raise ValueError("Supply bounded immutable driver evidence.")
    people = {w.employee_id: w for w in workers}
    cells = {(c.employee_id, c.local_date, c.slot): c for c in approvals}
    if len(people) != len(workers) or len(cells) != len(approvals):
        raise ValueError("Duplicate driver evidence requires resolution.")
    if any(not start_date <= c.local_date <= end_date for c in approvals):
        raise ValueError("Driver cells must lie inside the declared scope.")
    availability = {
        (w.employee_id, day, half): state
        for w in workers
        for day, half, state in w.availability
    }
    checks = []
    for check in personnel.checks:
        v = check.visit
        assessments = []
        conflicting = set(check.conflicting_employee_ids)
        for employee_id in v.employee_ids:
            worker = people.get(employee_id)
            cell = cells.get((employee_id, v.local_date, v.slot))
            approval = cell.state if cell else "Unverified"
            recorded = availability.get((employee_id, v.local_date, v.slot), "Unknown")
            blocked, missing = [], []
            if employee_id in conflicting:
                blocked.append("DRIVER_DOUBLE_BOOKED")
            if worker is None:
                missing.append("DRIVER_EMPLOYEE_EVIDENCE_MISSING")
            elif not worker.active:
                blocked.append("DRIVER_EMPLOYEE_INACTIVE")
            if approval in ("Suspended", "Expired"):
                blocked.append("DRIVER_APPROVAL_" + approval.upper())
            elif approval == "Unverified":
                missing.append("DRIVER_APPROVAL_UNVERIFIED")
            if recorded == "Unavailable":
                blocked.append("DRIVER_UNAVAILABLE")
            elif recorded == "Unknown":
                missing.append("DRIVER_AVAILABILITY_UNKNOWN")
            if not scope_complete:
                missing.append("STAFFING_SCOPE_INCOMPLETE")
            assessments.append(
                WorkerDriverCheck(
                    employee_id,
                    "Blocked" if blocked else "Pending" if missing else "Satisfied",
                    approval,
                    cell.change_id if cell else None,
                    tuple(blocked + missing),
                )
            )
        eligible = tuple(w.employee_id for w in assessments if w.state == "Satisfied")
        state = (
            "Satisfied"
            if eligible
            else "Pending"
            if not assessments or any(w.state == "Pending" for w in assessments)
            else "Blocked"
        )
        reasons = (
            ()
            if eligible
            else (
                "ACTUAL_STAFFING_REQUIRES_REVIEW"
                if not assessments
                else "DRIVER_EVIDENCE_PENDING"
                if state == "Pending"
                else "NO_ELIGIBLE_APPROVED_DRIVER",
            )
        )
        checks.append(VisitDriverCheck(v, state, eligible, tuple(assessments), reasons))
    overall = (
        "Blocked"
        if any(c.state == "Blocked" for c in checks)
        else "Pending"
        if not checks or any(c.state == "Pending" for c in checks)
        else "Satisfied"
    )
    return DriverValidation(tuple(checks), overall)
