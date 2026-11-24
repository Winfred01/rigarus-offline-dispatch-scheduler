"""Pure collision checks for explicitly staffed saved visits, not dispatch approval."""

from dataclasses import dataclass, field
from typing import Literal

from .assignments import HalfDay, local_date
from .recommendation_comparison import CheckState, _positive_id
from .recommendation_generator import _range

MAX_VISITS = 100_000
MAX_MEMBERSHIPS = 100_000


@dataclass(frozen=True)
class StaffedVisit:
    assignment_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    local_date: str
    slot: HalfDay
    status: Literal["Draft", "Cancelled"]
    staffing_configured: bool
    employee_ids: tuple[int, ...]

    def __post_init__(self):
        for value in (
            self.assignment_id,
            self.work_item_id,
            self.project_id,
            self.crew_id,
        ):
            _positive_id(value)
        local_date(self.local_date)
        if self.slot not in ("AM", "PM") or self.status not in ("Draft", "Cancelled"):
            raise ValueError("Supply an explicit AM/PM Draft or Cancelled visit.")
        if type(self.staffing_configured) is not bool:
            raise ValueError("Supply an explicit staffing configuration flag.")
        if (
            type(self.employee_ids) is not tuple
            or len(self.employee_ids) > MAX_MEMBERSHIPS
        ):
            raise ValueError("Supply bounded immutable explicit employee IDs.")
        for employee_id in self.employee_ids:
            _positive_id(employee_id)
        if len(set(self.employee_ids)) != len(self.employee_ids):
            raise ValueError("Duplicate employee IDs require resolution.")
        if not self.staffing_configured and self.employee_ids:
            raise ValueError("Unconfigured staffing cannot claim actual workers.")
        object.__setattr__(self, "employee_ids", tuple(sorted(self.employee_ids)))


@dataclass(frozen=True)
class AssignmentReference:
    assignment_id: int
    work_item_id: int
    project_id: int
    crew_id: int


@dataclass(frozen=True)
class EmployeeCollision:
    employee_id: int
    local_date: str
    slot: HalfDay
    visits: tuple[AssignmentReference, ...]
    code: Literal["EMPLOYEE_DOUBLE_BOOKED"] = field(
        default="EMPLOYEE_DOUBLE_BOOKED", init=False
    )


@dataclass(frozen=True)
class PersonnelVisitCheck:
    visit: StaffedVisit
    state: CheckState
    conflicting_employee_ids: tuple[int, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PersonnelValidation:
    start_date: str
    end_date: str
    scope_complete: bool
    state: CheckState
    checks: tuple[PersonnelVisitCheck, ...]
    conflicts: tuple[EmployeeCollision, ...]
    ignored_cancelled_ids: tuple[int, ...]
    reasons: tuple[str, ...]
    scope: Literal["SavedDraftAssignments"] = field(
        default="SavedDraftAssignments", init=False
    )
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_employee_conflicts(
    visits: tuple[StaffedVisit, ...],
    *,
    start_date: str,
    end_date: str,
    scope_complete: bool,
) -> PersonnelValidation:
    """Group exact local AM/PM memberships; never infer attendance or write state.

    Only explicit nonempty membership in a caller-asserted complete bounded view
    can satisfy this collision check. That never certifies other resource gates
    or proposed workers. Known collisions remain Blocked even in a partial view.
    """
    _range(start_date, end_date)
    if type(scope_complete) is not bool:
        raise ValueError("Explicitly declare whether the staffing view is complete.")
    if (
        type(visits) is not tuple
        or len(visits) > MAX_VISITS
        or any(not isinstance(v, StaffedVisit) for v in visits)
    ):
        raise ValueError("Supply at most 100000 immutable staffed visits.")
    if len({v.assignment_id for v in visits}) != len(visits):
        raise ValueError("Duplicate Assignment IDs require resolution.")
    if any(not start_date <= v.local_date <= end_date for v in visits):
        raise ValueError("Visits must lie within the declared local-date scope.")
    if sum(len(v.employee_ids) for v in visits) > MAX_MEMBERSHIPS:
        raise ValueError("The explicit membership view exceeds its workload bound.")
    active = sorted(
        (v for v in visits if v.status == "Draft"),
        key=lambda v: (v.local_date, v.slot, v.crew_id, v.assignment_id),
    )
    if len({(v.crew_id, v.local_date, v.slot) for v in active}) != len(active):
        raise ValueError("Duplicate active Crew/date/slot violates existing occupancy.")
    groups = {}
    for visit in active:
        for employee_id in visit.employee_ids:
            groups.setdefault((visit.local_date, visit.slot, employee_id), []).append(
                visit
            )
    references = {
        v.assignment_id: AssignmentReference(
            v.assignment_id, v.work_item_id, v.project_id, v.crew_id
        )
        for v in active
    }
    conflicts, blocked = [], {}
    for (day, half, employee_id), members in sorted(groups.items()):
        if len({v.crew_id for v in members}) < 2:
            continue
        conflicts.append(
            EmployeeCollision(
                employee_id,
                day,
                half,
                tuple(references[v.assignment_id] for v in members),
            )
        )
        for visit in members:
            blocked.setdefault(visit.assignment_id, set()).add(employee_id)
    checks = []
    for visit in active:
        employees = tuple(sorted(blocked.get(visit.assignment_id, ())))
        reasons = []
        if employees:
            reasons.append("EMPLOYEE_DOUBLE_BOOKED")
        if not visit.staffing_configured:
            reasons.append("ACTUAL_STAFFING_NOT_CONFIGURED")
        elif not visit.employee_ids:
            reasons.append("ACTUAL_STAFFING_EMPTY")
        if not scope_complete:
            reasons.append("STAFFING_SCOPE_INCOMPLETE")
        checks.append(
            PersonnelVisitCheck(
                visit,
                "Blocked" if employees else "Pending" if reasons else "Satisfied",
                employees,
                tuple(reasons),
            )
        )
    state = (
        "Blocked"
        if conflicts
        else "Pending"
        if not checks or any(c.state == "Pending" for c in checks)
        else "Satisfied"
    )
    reasons = tuple(
        code
        for condition, code in (
            (not active, "NO_ACTIVE_ASSIGNMENTS"),
            (not scope_complete, "STAFFING_SCOPE_INCOMPLETE"),
            (
                any(c.state == "Pending" for c in checks),
                "ACTUAL_STAFFING_REQUIRES_REVIEW",
            ),
            (bool(conflicts), "EMPLOYEE_DOUBLE_BOOKED"),
        )
        if condition
    )
    return PersonnelValidation(
        start_date,
        end_date,
        scope_complete,
        state,
        tuple(checks),
        tuple(conflicts),
        tuple(sorted(v.assignment_id for v in visits if v.status == "Cancelled")),
        reasons,
    )
