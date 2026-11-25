"""Pure full-date actual-worker company-driver checks; no dispatch authority."""

from dataclasses import dataclass, field
from typing import Literal

from .assignments import local_date
from .day_drafts import positive_id
from .driver_eligibility import DRIVER_STATES
from .daily_personnel_conflicts import (
    DailyStaffedVisit,
    DailyPersonnelValidation,
    validate_daily_employee_conflicts,
)
from .recommendation_comparison import CheckState


@dataclass(frozen=True)
class DailyDriverFact:
    local_date: str
    approval_state: str
    company_confirmed: bool
    full_day_confirmed: bool
    review_status: str
    availability_state: str
    change_id: int | None = None

    def __post_init__(self):
        local_date(self.local_date)
        if self.approval_state not in DRIVER_STATES or self.availability_state not in (
            "Available",
            "Unavailable",
            "Unknown",
        ):
            raise ValueError("Supply explicit daily approval and availability states.")
        if self.review_status not in ("Current", "Stale", "NeedsReview", "NotRecorded"):
            raise ValueError("Supply explicit approval review status.")
        if (
            type(self.company_confirmed) is not bool
            or type(self.full_day_confirmed) is not bool
        ):
            raise ValueError("Supply explicit boolean full-date company confirmation.")
        if self.change_id is not None:
            positive_id(self.change_id)
        if (self.company_confirmed or self.full_day_confirmed) and (
            self.change_id is None or self.review_status != "Current"
        ):
            raise ValueError(
                "Confirmed daily facts require current independent change identity."
            )


@dataclass(frozen=True)
class DailyDriverWorker:
    employee_id: int
    active: bool
    facts: tuple[DailyDriverFact, ...]

    def __post_init__(self):
        positive_id(self.employee_id)
        if (
            type(self.active) is not bool
            or type(self.facts) is not tuple
            or len(self.facts) > 366
            or any(not isinstance(f, DailyDriverFact) for f in self.facts)
        ):
            raise ValueError("Supply bounded immutable daily worker evidence.")
        if len({f.local_date for f in self.facts}) != len(self.facts):
            raise ValueError("Duplicate daily worker evidence requires resolution.")
        object.__setattr__(
            self, "facts", tuple(sorted(self.facts, key=lambda f: f.local_date))
        )


@dataclass(frozen=True)
class DailyDriverMemberCheck:
    employee_id: int
    state: CheckState
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DailyDriverVisitCheck:
    visit: DailyStaffedVisit
    state: CheckState
    eligible_employee_ids: tuple[int, ...]
    members: tuple[DailyDriverMemberCheck, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DailyDriverValidation:
    personnel: DailyPersonnelValidation
    state: CheckState
    checks: tuple[DailyDriverVisitCheck, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def _aggregate(states):
    return (
        "Blocked"
        if "Blocked" in states
        else "Pending"
        if not states or "Pending" in states
        else "Satisfied"
    )


def validate_daily_drivers(
    visits: tuple[DailyStaffedVisit, ...],
    workers: tuple[DailyDriverWorker, ...],
    *,
    start_date: str,
    end_date: str,
    scope_complete: bool,
):
    """One eligible actual worker satisfies only the company-driver subcheck.

    Missing facts never pass. Explicit negatives survive incomplete scope. Old
    half-day attendance is not full-day attendance, even with daily approval.
    """
    personnel = validate_daily_employee_conflicts(
        visits, start_date=start_date, end_date=end_date, scope_complete=scope_complete
    )
    if (
        type(workers) is not tuple
        or len(workers) > 100000
        or any(not isinstance(w, DailyDriverWorker) for w in workers)
    ):
        raise ValueError("Supply at most 100000 immutable workers.")
    if (
        len({w.employee_id for w in workers}) != len(workers)
        or sum(len(w.facts) for w in workers) > 100000
    ):
        raise ValueError("Duplicate or excessive daily driver evidence.")
    if any(
        not start_date <= f.local_date <= end_date for w in workers for f in w.facts
    ):
        raise ValueError("Daily driver facts must lie within the declared horizon.")
    by_id = {w.employee_id: w for w in workers}
    facts = {(w.employee_id, f.local_date): f for w in workers for f in w.facts}
    checks = []
    for p in personnel.checks:
        v = p.visit
        members = []
        conflicting = set(p.conflicting_employee_ids)
        for identity in v.employee_ids:
            worker = by_id.get(identity)
            fact = facts.get((identity, v.local_date))
            blocked = []
            pending = []
            if worker is None:
                pending.append("WORKER_CONTEXT_MISSING")
            elif not worker.active:
                blocked.append("EMPLOYEE_INACTIVE")
            if identity in conflicting:
                blocked.append("EMPLOYEE_DOUBLE_BOOKED_DAY")
            if fact is None:
                pending.append("DAILY_DRIVER_AND_AVAILABILITY_MISSING")
            else:
                if fact.approval_state in ("Suspended", "Expired"):
                    blocked.append("DRIVER_" + fact.approval_state.upper())
                elif (
                    fact.approval_state != "Active"
                    or not fact.company_confirmed
                    or not fact.full_day_confirmed
                    or fact.review_status != "Current"
                ):
                    pending.append("FULL_DAY_COMPANY_APPROVAL_MISSING_OR_STALE")
                if fact.availability_state == "Unavailable":
                    blocked.append("EMPLOYEE_UNAVAILABLE_DAY")
                elif fact.availability_state != "Available":
                    pending.append("FULL_DAY_AVAILABILITY_MISSING")
            if v.record_kind == "LegacyHalfDay":
                pending.append("LEGACY_HALF_DAY_ATTENDANCE_NEEDS_REVIEW")
            if p.state == "Pending":
                pending.append("PERSONNEL_SCOPE_PENDING")
            state = "Blocked" if blocked else "Pending" if pending else "Satisfied"
            members.append(
                DailyDriverMemberCheck(
                    identity,
                    state,
                    tuple(blocked + pending) or ("FULL_DAY_COMPANY_DRIVER_ELIGIBLE",),
                )
            )
        eligible = tuple(m.employee_id for m in members if m.state == "Satisfied")
        state = (
            "Satisfied"
            if eligible
            else "Pending"
            if not v.staffing_configured or any(m.state == "Pending" for m in members)
            else "Blocked"
        )
        reason = (
            "ELIGIBLE_ACTUAL_FULL_DAY_DRIVER"
            if eligible
            else "ACTUAL_STAFFING_NOT_RECORDED"
            if not v.staffing_configured
            else "NO_ACTUAL_MEMBERS"
            if not members
            else "DRIVER_EVIDENCE_PENDING"
            if state == "Pending"
            else "NO_ELIGIBLE_ACTUAL_DRIVER"
        )
        checks.append(
            DailyDriverVisitCheck(v, state, eligible, tuple(members), (reason,))
        )
    return DailyDriverValidation(
        personnel, _aggregate([c.state for c in checks]), tuple(checks)
    )


def day_driver_workers(snapshot):
    """Detached snapshot conversion only; no SQLite/I/O/clock access."""
    import json

    availability = {
        s.entity_id: json.loads(s.payload_json)
        for s in snapshot.daily_inputs
        if s.scope == "Employee"
    }
    workers = []
    for employee in snapshot.employees:
        available = {
            e["local_date"]: e["state"]
            for e in availability[employee.employee_id]["entries"]
        }
        driver = json.loads(employee.daily_driver_json)
        workers.append(
            DailyDriverWorker(
                employee.employee_id,
                bool(employee.metadata[5]),
                tuple(
                    DailyDriverFact(
                        e["local_date"],
                        e["state"],
                        e["company_confirmed"],
                        e["full_day_confirmed"],
                        e["review_status"],
                        available[e["local_date"]],
                        e["change_id"],
                    )
                    for e in driver["entries"]
                ),
            )
        )
    return tuple(workers)


def validate_day_snapshot_drivers(snapshot):
    from .day_recommendation_adapter import day_staffed_visits

    return validate_daily_drivers(
        day_staffed_visits(snapshot),
        day_driver_workers(snapshot),
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=True,
    )
