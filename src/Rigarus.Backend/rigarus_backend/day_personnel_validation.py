"""Detached explicit candidate workers checked against one coherent daily view."""

from dataclasses import dataclass, field, asdict, replace
from typing import Literal

from .assignments import local_date
from .day_drafts import positive_id
from .daily_personnel_conflicts import (
    DailyStaffedVisit,
    DailyPersonnelValidation,
    DailyPersonnelVisitCheck,
    DailyEmployeeCollision,
    DailyAssignmentReference,
    validate_daily_employee_conflicts,
)
from .day_recommendation_adapter import (
    DayRecommendationSnapshot,
    day_generation_requests,
    day_staffed_visits,
    check_day_snapshot_freshness,
)
from .day_recommendation_generator import GeneratedDayCandidate, generate_day_candidate
from .recommendation_adapter import _digest, PENDING_VALIDATORS
from .recommendation_comparison import (
    ConstraintEvidence,
    DayOptionComparison,
    compare_day_options,
    CheckState,
)


@dataclass(frozen=True)
class ProposedDayMembers:
    local_date: str
    employee_ids: tuple[int, ...] | None

    def __post_init__(self):
        local_date(self.local_date)
        if self.employee_ids is None:
            return
        if type(self.employee_ids) is not tuple or len(self.employee_ids) > 1000:
            raise ValueError(
                "Supply at most 1000 explicit immutable proposed Employee IDs per date."
            )
        for identity in self.employee_ids:
            positive_id(identity)
        if len(set(self.employee_ids)) != len(self.employee_ids):
            raise ValueError("Duplicate proposed employees require resolution.")
        object.__setattr__(self, "employee_ids", tuple(sorted(self.employee_ids)))


@dataclass(frozen=True)
class SourceCrewRevalidation:
    crew_id: int
    local_date: str
    visits: tuple[DailyAssignmentReference, ...]
    pending_checks: tuple[str, ...] = field(
        default=(
            "ApprovedDriver",
            "MinimumStaffing",
            "Skills",
            "Qualifications",
            "EmployeeAvailability",
        ),
        init=False,
    )
    state: Literal["Pending"] = field(default="Pending", init=False)


@dataclass(frozen=True)
class DayCandidatePersonnelValidation:
    snapshot: DayRecommendationSnapshot
    candidate: GeneratedDayCandidate
    proposed_members: tuple[ProposedDayMembers, ...]
    missing_employee_ids: tuple[int, ...]
    validation: DailyPersonnelValidation
    checks: tuple[DailyPersonnelVisitCheck, ...]
    conflicts: tuple[DailyEmployeeCollision, ...]
    source_crew_revalidation: tuple[SourceCrewRevalidation, ...]
    state: CheckState
    comparison: DayOptionComparison
    input_fingerprint: str
    proposal_fingerprint: str
    pending_validators: tuple[str, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_day_candidate_personnel(
    snapshot: DayRecommendationSnapshot,
    candidate: GeneratedDayCandidate,
    members: tuple[ProposedDayMembers, ...] = (),
):
    """One alternative only, never a transfer, saved-staff replacement or approval.

    Bind the exact plan to the snapshot and return missing context as Pending.
    Capturing extra proposed employees in the query is observation, not attendance.
    Source members remain present, so apparent borrowing cannot erase collisions.
    """
    if not isinstance(snapshot, DayRecommendationSnapshot) or not isinstance(
        candidate, GeneratedDayCandidate
    ):
        raise ValueError("Supply a daily snapshot and its actual generated candidate.")
    request = next(
        (
            r
            for r in day_generation_requests(snapshot)
            if r.option_id == candidate.option_id
        ),
        None,
    )
    if (
        request is None
        or generate_day_candidate(request) != candidate
        or candidate.option is None
    ):
        raise ValueError(
            "Candidate must be a complete exact plan generated from this snapshot; rebuild changed context."
        )
    if (
        type(members) is not tuple
        or len(members) > 366
        or any(not isinstance(m, ProposedDayMembers) for m in members)
    ):
        raise ValueError("Supply immutable per-date proposed membership.")
    supplied = {m.local_date: m for m in members}
    if len(supplied) != len(members) or set(supplied) - set(
        candidate.allocated_working_dates
    ):
        raise ValueError("Resolve duplicate or out-of-plan membership dates.")
    proposed = tuple(
        supplied.get(day, ProposedDayMembers(day, None))
        for day in candidate.allocated_working_dates
    )
    weekend_rosters = {
        (m.crew_id, m.local_date): m.employee_ids
        for m in snapshot.query.weekend_members
    }
    from datetime import date

    for m in proposed:
        if date.fromisoformat(
            m.local_date
        ).weekday() >= 5 and m.employee_ids != weekend_rosters.get(
            (candidate.crew_id, m.local_date)
        ):
            raise ValueError(
                "Weekend actual workers changed; rebuild roster-bound consent and candidate."
            )
    observed = {e.employee_id for e in snapshot.employees}
    missing = tuple(
        sorted({e for m in proposed for e in m.employee_ids or ()} - observed)
    )
    visits = tuple(
        DailyStaffedVisit(
            "Proposal",
            candidate.option_id,
            candidate.work_item_id,
            candidate.project_id,
            candidate.crew_id,
            m.local_date,
            1,
            "Draft",
            m.employee_ids is not None,
            m.employee_ids or (),
        )
        for m in proposed
    )
    validation = validate_daily_employee_conflicts(
        (*day_staffed_visits(snapshot), *visits),
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=not missing,
    )
    checks = tuple(c for c in validation.checks if c.visit.record_kind == "Proposal")
    state = (
        "Blocked"
        if any(c.state == "Blocked" for c in checks)
        else "Pending"
        if any(c.state == "Pending" for c in checks)
        else "Satisfied"
    )
    conflicts = tuple(
        c
        for c in validation.conflicts
        if any(v.record_kind == "Proposal" for v in c.visits)
    )
    sources = {}
    for conflict in conflicts:
        for ref in conflict.visits:
            if ref.record_kind != "Proposal":
                sources.setdefault((ref.crew_id, conflict.local_date), set()).add(ref)
    revalidation = tuple(
        SourceCrewRevalidation(
            crew, day, tuple(sorted(refs, key=lambda r: (r.record_kind, r.record_id)))
        )
        for (crew, day), refs in sorted(sources.items())
    )
    by_date = {c.visit.local_date: c.state for c in checks}
    option = replace(
        candidate.option,
        days=tuple(
            replace(
                day,
                evidence=tuple(
                    e for e in day.evidence if e.check != "PersonnelConflicts"
                )
                + (ConstraintEvidence("PersonnelConflicts", by_date[day.local_date]),),
            )
            for day in candidate.option.days
        ),
    )
    comparison = compare_day_options(
        candidate.work_item_id,
        candidate.project_id,
        (option,),
        max_options=1,
        order=snapshot.query.order,
    )
    fingerprint = _digest(
        (
            "rigarus-day-personnel-proposal-v1",
            snapshot.input_fingerprint,
            asdict(candidate.option),
            tuple(asdict(m) for m in proposed),
        )
    )
    pending = tuple(
        c for c in PENDING_VALIDATORS if c != "PersonnelConflicts" or state == "Pending"
    )
    return DayCandidatePersonnelValidation(
        snapshot,
        candidate,
        proposed,
        missing,
        validation,
        checks,
        conflicts,
        revalidation,
        state,
        comparison,
        snapshot.input_fingerprint,
        fingerprint,
        pending,
    )


def check_day_candidate_personnel_freshness(
    path, result: DayCandidatePersonnelValidation
):
    if not isinstance(result, DayCandidatePersonnelValidation):
        raise ValueError("Supply an immutable candidate personnel result.")
    return check_day_snapshot_freshness(path, result.snapshot)
