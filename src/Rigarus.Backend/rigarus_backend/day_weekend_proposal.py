"""All relevant actual workers consent before weekend re-proposal; no Apply."""

from dataclasses import dataclass, field, replace
from typing import Literal

from .daily_weekend_consent import (
    WeekendValidation,
    validate_weekend_consent,
    aggregate,
)
from .daily_weekend_store import snapshot_consent_facts
from .day_rig_proposal import DayRigProposal, validate_day_rig_proposal
from .day_recommendation_adapter import day_staffed_visits, check_day_snapshot_freshness
from .recommendation_comparison import (
    ConstraintEvidence,
    DayOptionComparison,
    compare_day_options,
)
from .recommendation_adapter import _digest


@dataclass(frozen=True)
class DayWeekendProposal:
    rig: DayRigProposal
    before: WeekendValidation
    after: WeekendValidation
    target_checks: tuple
    source_checks: tuple
    state: str
    comparison: DayOptionComparison
    input_fingerprint: str
    proposal_fingerprint: str
    pending_validators: tuple[str, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_day_weekend_proposal(
    snapshot, candidate, members=(), source_overrides=(), choices=()
):
    rig = validate_day_rig_proposal(
        snapshot, candidate, members, source_overrides, choices
    )
    facts = snapshot_consent_facts(snapshot)
    before = validate_weekend_consent(day_staffed_visits(snapshot), facts)
    effective = tuple(c.visit for c in rig.capability.driver.after.personnel.checks)
    after = validate_weekend_consent(effective, facts)
    sources = {c.visit.key for c in rig.capability.source_checks}
    target = tuple(c for c in after.checks if c.visit.record_kind == "Proposal")
    source = tuple(c for c in after.checks if c.visit.key in sources)
    by_day = {}
    for c in (*target, *source):
        if "WEEKDAY_CONSENT_NOT_APPLICABLE" not in c.reasons:
            by_day.setdefault(c.visit.local_date, []).append(c.state)
    base = (*rig.comparison.options, *rig.comparison.excluded)[0].option
    option = replace(
        base,
        days=tuple(
            replace(
                day,
                evidence=tuple(e for e in day.evidence if e.check != "WeekendConsent")
                + (
                    (
                        ConstraintEvidence(
                            "WeekendConsent", aggregate(by_day[day.local_date])
                        ),
                    )
                    if day.local_date in by_day
                    else ()
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
    return DayWeekendProposal(
        rig,
        before,
        after,
        target,
        source,
        aggregate([rig.state, *[c.state for c in (*target, *source)]]),
        comparison,
        snapshot.input_fingerprint,
        _digest(
            (
                "rigarus-day-weekend-proposal-v1",
                rig.proposal_fingerprint,
                snapshot.weekend_source_json,
            )
        ),
        tuple(
            v
            for v in rig.pending_validators
            if v != "WeekendConsent"
            or any(c.state == "Pending" for c in (*target, *source))
        ),
    )


def check_weekend_proposal_freshness(path, result):
    if not isinstance(result, DayWeekendProposal):
        raise ValueError("Supply an immutable weekend proposal.")
    return check_day_snapshot_freshness(path, result.rig.capability.driver.snapshot)
