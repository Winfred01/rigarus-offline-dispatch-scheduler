"""Pure whole-date occupancy for explicit workers, never dispatch certification."""

from dataclasses import dataclass, field
from typing import Literal

from .assignments import local_date
from .day_drafts import positive_id
from .recommendation_comparison import CheckState
from .recommendation_generator import _range

MAX_VISITS = 100_000
MAX_MEMBERSHIPS = 100_000
RecordKind = Literal["FullDayDraft", "LegacyHalfDay", "Proposal"]


@dataclass(frozen=True)
class DailyStaffedVisit:
    record_kind: RecordKind
    record_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    local_date: str
    revision: int
    status: Literal["Draft", "Cancelled"]
    staffing_configured: bool
    employee_ids: tuple[int, ...]
    legacy_slot: str | None = None

    def __post_init__(self):
        for value in (
            self.record_id,
            self.work_item_id,
            self.project_id,
            self.crew_id,
            self.revision,
        ):
            positive_id(value)
        local_date(self.local_date)
        if self.record_kind not in (
            "FullDayDraft",
            "LegacyHalfDay",
            "Proposal",
        ) or self.status not in ("Draft", "Cancelled"):
            raise ValueError(
                "Supply an explicit dated day/legacy/proposal record kind and status."
            )
        if (
            self.record_kind == "LegacyHalfDay" and self.legacy_slot not in ("AM", "PM")
        ) or (self.record_kind != "LegacyHalfDay" and self.legacy_slot is not None):
            raise ValueError("Only legacy records carry their original AM/PM locator.")
        if self.record_kind == "Proposal" and self.status != "Draft":
            raise ValueError("A proposed visit must be a Draft observation.")
        if (
            type(self.staffing_configured) is not bool
            or type(self.employee_ids) is not tuple
            or len(self.employee_ids) > MAX_MEMBERSHIPS
        ):
            raise ValueError(
                "Supply bounded immutable explicit staffing and a boolean configuration flag."
            )
        for identity in self.employee_ids:
            positive_id(identity)
        if len(set(self.employee_ids)) != len(self.employee_ids):
            raise ValueError("Duplicate employee IDs require resolution.")
        if not self.staffing_configured and self.employee_ids:
            raise ValueError("Unconfigured staffing cannot claim actual workers.")
        object.__setattr__(self, "employee_ids", tuple(sorted(self.employee_ids)))

    @property
    def key(self):
        return self.record_kind, self.record_id, self.local_date


@dataclass(frozen=True)
class DailyAssignmentReference:
    record_kind: RecordKind
    record_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    revision: int
    legacy_slot: str | None


@dataclass(frozen=True)
class DailyEmployeeCollision:
    employee_id: int
    local_date: str
    visits: tuple[DailyAssignmentReference, ...]
    code: Literal["EMPLOYEE_DOUBLE_BOOKED_DAY"] = field(
        default="EMPLOYEE_DOUBLE_BOOKED_DAY", init=False
    )


@dataclass(frozen=True)
class DailyPersonnelVisitCheck:
    visit: DailyStaffedVisit
    state: CheckState
    conflicting_employee_ids: tuple[int, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DailyPersonnelValidation:
    start_date: str
    end_date: str
    scope_complete: bool
    state: CheckState
    checks: tuple[DailyPersonnelVisitCheck, ...]
    conflicts: tuple[DailyEmployeeCollision, ...]
    ignored_cancelled: tuple[DailyAssignmentReference, ...]
    reasons: tuple[str, ...]
    scope: Literal["WholeDateExplicitMembership"] = field(
        default="WholeDateExplicitMembership", init=False
    )
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_daily_employee_conflicts(
    visits: tuple[DailyStaffedVisit, ...],
    *,
    start_date: str,
    end_date: str,
    scope_complete: bool,
):
    """Whole-date grouping, preserving raw legacy locators and every source identity.

    Satisfied proves only this collision check in the supplied complete scope.
    Unknown other-Crew membership on the same date cannot yield a false clear.
    Known collisions remain Blocked even when other evidence is incomplete.
    """
    _range(start_date, end_date)
    if type(scope_complete) is not bool:
        raise ValueError("Declare complete staffing scope explicitly.")
    if (
        type(visits) is not tuple
        or len(visits) > MAX_VISITS
        or any(not isinstance(v, DailyStaffedVisit) for v in visits)
    ):
        raise ValueError("Supply at most 100000 immutable dated staffing records.")
    saved = [
        (v.record_kind, v.record_id) for v in visits if v.record_kind != "Proposal"
    ]
    if len({v.key for v in visits}) != len(visits) or len(set(saved)) != len(saved):
        raise ValueError("Duplicate current record identities require resolution.")
    if any(not start_date <= v.local_date <= end_date for v in visits):
        raise ValueError("Records must lie within the declared local-date scope.")
    if sum(len(v.employee_ids) for v in visits) > MAX_MEMBERSHIPS:
        raise ValueError("Explicit membership workload limit exceeded.")
    active = tuple(
        sorted(
            (v for v in visits if v.status == "Draft"),
            key=lambda v: (v.local_date, v.crew_id, v.record_kind, v.record_id),
        )
    )
    crew_dates = {}
    unknown = {}
    groups = {}
    references = {}
    for visit in active:
        crew_dates.setdefault((visit.crew_id, visit.local_date), []).append(visit)
        references[visit.key] = DailyAssignmentReference(
            visit.record_kind,
            visit.record_id,
            visit.work_item_id,
            visit.project_id,
            visit.crew_id,
            visit.revision,
            visit.legacy_slot,
        )
        if not visit.staffing_configured or not visit.employee_ids:
            unknown.setdefault(visit.local_date, set()).add(visit.crew_id)
        for employee_id in visit.employee_ids:
            groups.setdefault((visit.local_date, employee_id), []).append(visit)
    for members in crew_dates.values():
        if (
            len(members) > 1 and any(v.record_kind != "LegacyHalfDay" for v in members)
        ) or len({v.legacy_slot for v in members}) != len(members):
            raise ValueError(
                "Overlapping active Crew occupancy violates existing day/legacy constraints."
            )
    conflicts, blocked = [], {}
    for (day, employee_id), members in sorted(groups.items()):
        if len({v.crew_id for v in members}) < 2:
            continue
        conflicts.append(
            DailyEmployeeCollision(
                employee_id, day, tuple(references[v.key] for v in members)
            )
        )
        for v in members:
            blocked.setdefault(v.key, set()).add(employee_id)
    checks = []
    for v in active:
        employees = tuple(sorted(blocked.get(v.key, ())))
        reasons = []
        if employees:
            reasons.append("EMPLOYEE_DOUBLE_BOOKED_DAY")
        if not v.staffing_configured:
            reasons.append("ACTUAL_STAFFING_NOT_CONFIGURED")
        elif not v.employee_ids:
            reasons.append("ACTUAL_STAFFING_EMPTY")
        unknown_crews = unknown.get(v.local_date, ())
        if unknown_crews and (len(unknown_crews) > 1 or v.crew_id not in unknown_crews):
            reasons.append("OTHER_CREW_STAFFING_UNKNOWN")
        if not scope_complete:
            reasons.append("STAFFING_SCOPE_INCOMPLETE")
        checks.append(
            DailyPersonnelVisitCheck(
                v,
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
            (bool(conflicts), "EMPLOYEE_DOUBLE_BOOKED_DAY"),
        )
        if condition
    )
    cancelled = tuple(
        DailyAssignmentReference(
            v.record_kind,
            v.record_id,
            v.work_item_id,
            v.project_id,
            v.crew_id,
            v.revision,
            v.legacy_slot,
        )
        for v in sorted(visits, key=lambda v: v.key)
        if v.status == "Cancelled"
    )
    return DailyPersonnelValidation(
        start_date,
        end_date,
        scope_complete,
        state,
        tuple(checks),
        tuple(conflicts),
        cancelled,
        reasons,
    )
