"""Read-only driver borrowing preview, with explicit revision-bound source rosters."""

from dataclasses import dataclass, field, asdict, replace
from typing import Literal

from .day_drafts import positive_id
from .day_personnel_validation import (
    ProposedDayMembers,
    validate_day_candidate_personnel,
)
from .daily_driver_validation import (
    DailyDriverValidation,
    DailyDriverVisitCheck,
    validate_daily_drivers,
    day_driver_workers,
    _aggregate,
)
from .daily_personnel_conflicts import DailyStaffedVisit
from .day_recommendation_adapter import (
    DayRecommendationSnapshot,
    day_staffed_visits,
    check_day_snapshot_freshness,
)
from .day_recommendation_generator import GeneratedDayCandidate
from .recommendation_comparison import (
    ConstraintEvidence,
    DayOptionComparison,
    CheckState,
    compare_day_options,
)
from .recommendation_adapter import _digest, PENDING_VALIDATORS


@dataclass(frozen=True)
class SourceDayMembers:
    record_kind: Literal["FullDayDraft", "LegacyHalfDay"]
    record_id: int
    expected_revision: int
    employee_ids: tuple[int, ...]

    def __post_init__(self):
        positive_id(self.record_id)
        positive_id(self.expected_revision)
        if self.record_kind not in ("FullDayDraft", "LegacyHalfDay"):
            raise ValueError("Source must be an existing namespaced saved record.")
        # Reuse strict employee ID normalization and technical member bound.
        normalized = ProposedDayMembers("0001-01-01", self.employee_ids)
        if normalized.employee_ids is None:
            raise ValueError(
                "Source replacement must be an explicitly configured roster."
            )
        object.__setattr__(self, "employee_ids", normalized.employee_ids)


@dataclass(frozen=True)
class DayDriverProposal:
    snapshot: DayRecommendationSnapshot
    candidate: GeneratedDayCandidate
    members: tuple[ProposedDayMembers, ...]
    source_overrides: tuple[SourceDayMembers, ...]
    missing_employee_ids: tuple[int, ...]
    before: DailyDriverValidation
    after: DailyDriverValidation
    target_checks: tuple[DailyDriverVisitCheck, ...]
    source_checks: tuple[DailyDriverVisitCheck, ...]
    state: CheckState
    comparison: DayOptionComparison
    input_fingerprint: str
    proposal_fingerprint: str
    pending_validators: tuple[str, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_day_driver_proposal(snapshot, candidate, members=(), source_overrides=()):
    checked = validate_day_candidate_personnel(snapshot, candidate, members)
    if (
        type(source_overrides) is not tuple
        or len(source_overrides) > 100000
        or any(not isinstance(o, SourceDayMembers) for o in source_overrides)
    ):
        raise ValueError("Supply bounded immutable source roster overrides.")
    normalized = tuple(
        sorted(source_overrides, key=lambda o: (o.record_kind, o.record_id))
    )
    by_key = {(o.record_kind, o.record_id): o for o in normalized}
    if len(by_key) != len(normalized):
        raise ValueError("Duplicate source overrides require resolution.")
    if sum(len(o.employee_ids) for o in normalized) > 100000:
        raise ValueError("Source replacement membership workload limit exceeded.")
    saved = day_staffed_visits(snapshot)
    by_id = {(v.record_kind, v.record_id): v for v in saved}
    proposed = {
        m.local_date: set(m.employee_ids or ()) for m in checked.proposed_members
    }
    for key, o in by_key.items():
        v = by_id.get(key)
        if (
            v is None
            or v.status != "Draft"
            or v.revision != o.expected_revision
            or v.crew_id == candidate.crew_id
            or v.local_date not in proposed
            or not set(v.employee_ids) & proposed[v.local_date]
        ):
            raise ValueError(
                "Source override must match an active borrowed-worker source, date and current revision."
            )
    observed = {e.employee_id for e in snapshot.employees}
    missing = tuple(
        sorted(
            (
                set(checked.missing_employee_ids)
                | {e for o in normalized for e in o.employee_ids}
            )
            - observed
        )
    )
    effective = tuple(
        replace(
            v,
            employee_ids=by_key[v.record_kind, v.record_id].employee_ids,
            staffing_configured=True,
        )
        if (v.record_kind, v.record_id) in by_key
        else v
        for v in saved
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
        for m in checked.proposed_members
    )
    args = dict(
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=not missing,
    )
    workers = day_driver_workers(snapshot)
    before = validate_daily_drivers(saved, workers, **(args | {"scope_complete": True}))
    after = validate_daily_drivers((*effective, *visits), workers, **args)
    target = tuple(c for c in after.checks if c.visit.record_kind == "Proposal")
    # Recheck every known source overlap, even without a replacement (no implicit removal).
    sources = {
        v.key
        for v in saved
        if v.status == "Draft"
        and v.crew_id != candidate.crew_id
        and v.local_date in proposed
        and set(v.employee_ids) & proposed[v.local_date]
    }
    source = tuple(c for c in after.checks if c.visit.key in sources)
    source_personnel = {}
    for check in after.personnel.checks:
        if check.visit.key in sources:
            source_personnel.setdefault(check.visit.local_date, []).append(check.state)
    personnel = {
        c.visit.local_date: _aggregate(
            [c.state] + source_personnel.get(c.visit.local_date, [])
        )
        for c in after.personnel.checks
        if c.visit.record_kind == "Proposal"
    }
    source_states = {}
    for check in source:
        source_states.setdefault(check.visit.local_date, []).append(check.state)
    driver = {
        c.visit.local_date: _aggregate(
            [c.state] + source_states.get(c.visit.local_date, [])
        )
        for c in target
    }
    option = replace(
        candidate.option,
        days=tuple(
            replace(
                day,
                evidence=tuple(
                    e
                    for e in day.evidence
                    if e.check not in ("PersonnelConflicts", "ApprovedDriver")
                )
                + (
                    ConstraintEvidence("PersonnelConflicts", personnel[day.local_date]),
                    ConstraintEvidence("ApprovedDriver", driver[day.local_date]),
                ),
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
    state = _aggregate([*personnel.values(), *driver.values()])
    return DayDriverProposal(
        snapshot,
        candidate,
        checked.proposed_members,
        normalized,
        missing,
        before,
        after,
        target,
        source,
        state,
        comparison,
        snapshot.input_fingerprint,
        _digest(
            (
                "rigarus-day-driver-proposal-v1",
                snapshot.input_fingerprint,
                asdict(candidate.option),
                tuple(asdict(m) for m in checked.proposed_members),
                tuple(asdict(o) for o in normalized),
            )
        ),
        tuple(
            check
            for check in PENDING_VALIDATORS
            if check not in ("PersonnelConflicts", "ApprovedDriver")
            or (check == "PersonnelConflicts" and "Pending" in personnel.values())
            or (check == "ApprovedDriver" and "Pending" in driver.values())
        )
        + ("OperatorReview",),
    )


def check_day_driver_proposal_freshness(path, result):
    if not isinstance(result, DayDriverProposal):
        raise ValueError("Supply an immutable daily driver proposal result.")
    return check_day_snapshot_freshness(path, result.snapshot)
