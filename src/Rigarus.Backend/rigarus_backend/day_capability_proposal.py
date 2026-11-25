"""Detached capability checks on exactly the PR108 before/after borrowing rosters."""

from dataclasses import dataclass, field, replace
from typing import Literal

from .day_driver_proposal import (
    DayDriverProposal,
    validate_day_driver_proposal,
    check_day_driver_proposal_freshness,
)
from .day_recommendation_adapter import day_staffed_visits
from .daily_driver_validation import _aggregate
from .daily_capability_validation import (
    DailyCapabilityValidation,
    DailyCapabilityCheck,
    validate_daily_capabilities,
    snapshot_capability_inputs,
)
from .recommendation_comparison import (
    ConstraintEvidence,
    DayOptionComparison,
    CheckState,
    compare_day_options,
)
from .recommendation_adapter import _digest


def _groups(check):
    counts = check.counts
    return dict(
        CrewType=check.crew_state,
        MinimumStaffing=counts[0].state,
        Skills=_aggregate(
            [c.state for c in counts if c.check.startswith("SkillsLevel")]
        ),
        Qualifications=_aggregate(
            [c.state for c in counts if c.check.startswith("Qualification")]
        )
        if any(c.check.startswith("Qualification") for c in counts)
        else "Satisfied"
        if check.requirement_change_id is not None
        else "Pending",
    )


@dataclass(frozen=True)
class DayCapabilityProposal:
    driver: DayDriverProposal
    before: DailyCapabilityValidation
    after: DailyCapabilityValidation
    target_checks: tuple[DailyCapabilityCheck, ...]
    source_checks: tuple[DailyCapabilityCheck, ...]
    state: CheckState
    comparison: DayOptionComparison
    input_fingerprint: str
    proposal_fingerprint: str
    pending_validators: tuple[str, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_day_capability_proposal(
    snapshot, candidate, members=(), source_overrides=()
):
    driver = validate_day_driver_proposal(
        snapshot, candidate, members, source_overrides
    )
    workers, sources = snapshot_capability_inputs(snapshot)
    saved = day_staffed_visits(snapshot)
    args = dict(
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
    )
    before = validate_daily_capabilities(
        saved, workers, sources, scope_complete=True, **args
    )
    effective = tuple(c.visit for c in driver.after.personnel.checks) + tuple(
        v for v in saved if v.status == "Cancelled"
    )
    after = validate_daily_capabilities(
        effective,
        workers,
        sources,
        scope_complete=not driver.missing_employee_ids,
        **args,
    )
    target = tuple(c for c in after.checks if c.visit.record_kind == "Proposal")
    keys = {c.visit.key for c in driver.source_checks}
    source = tuple(c for c in after.checks if c.visit.key in keys)
    grouped = {c.visit.local_date: [_groups(c)] for c in target}
    for c in source:
        grouped[c.visit.local_date].append(_groups(c))
    by_day = {
        day: {key: _aggregate([g[key] for g in groups]) for key in groups[0]}
        for day, groups in grouped.items()
    }
    # PR108 exposes the evaluated exact alternative even when excluded.
    base = (*driver.comparison.options, *driver.comparison.excluded)[0].option
    option = replace(
        base,
        days=tuple(
            replace(
                day,
                evidence=tuple(
                    e for e in day.evidence if e.check not in by_day[day.local_date]
                )
                + tuple(
                    ConstraintEvidence(key, state)
                    for key, state in by_day[day.local_date].items()
                ),
            )
            for day in base.days
        ),
    )
    comparison = compare_day_options(
        candidate.work_item_id,
        candidate.project_id,
        (option,),
        max_options=1,
        order=snapshot.query.order,
    )
    pending = tuple(
        c
        for c in driver.pending_validators
        if c not in by_day[base.days[0].local_date]
        or any(states[c] == "Pending" for states in by_day.values())
    )
    state = _aggregate(
        [
            driver.state,
            *(state for states in by_day.values() for state in states.values()),
        ]
    )
    return DayCapabilityProposal(
        driver,
        before,
        after,
        target,
        source,
        state,
        comparison,
        snapshot.input_fingerprint,
        _digest(("rigarus-day-capability-proposal-v1", driver.proposal_fingerprint)),
        pending,
    )


def check_day_capability_proposal_freshness(path, result):
    if not isinstance(result, DayCapabilityProposal):
        raise ValueError("Supply an immutable daily capability proposal.")
    return check_day_driver_proposal_freshness(path, result.driver)
