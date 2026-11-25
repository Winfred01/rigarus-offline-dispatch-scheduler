"""Explicit detached daily vehicle choices/swaps, never actual resource writes."""

from dataclasses import dataclass, field, replace, asdict
from typing import Literal

from .assignments import local_date
from .day_drafts import positive_id
from .daily_driver_validation import _aggregate
from .daily_rig_validation import (
    RigVisit,
    DailyRigValidation,
    validate_daily_rigs,
    snapshot_rig_inputs,
)
from .day_capability_proposal import (
    DayCapabilityProposal,
    validate_day_capability_proposal,
)
from .day_recommendation_adapter import (
    DayRecommendationSnapshot,
    check_day_snapshot_freshness,
)
from .recommendation_comparison import (
    DayOptionComparison,
    ConstraintEvidence,
    CheckState,
    compare_day_options,
)
from .recommendation_adapter import _digest


@dataclass(frozen=True)
class ProposedDayRig:
    local_date: str
    actual_rig_id: int | None
    operational_confirmed: bool
    reference: str
    original_rig_id: int | None = None

    def __post_init__(self):
        local_date(self.local_date)
        for identity in (self.actual_rig_id, self.original_rig_id):
            if identity is not None:
                positive_id(identity)
        if type(self.operational_confirmed) is not bool or (
            self.operational_confirmed and self.actual_rig_id is None
        ):
            raise ValueError(
                "Explicitly declare full-date operational planning evidence for an actual Rig."
            )
        if (
            not isinstance(self.reference, str)
            or not 1 <= len(self.reference.strip()) <= 200
            or "\0" in self.reference
        ):
            raise ValueError("Supply a bounded planning evidence reference.")
        object.__setattr__(self, "reference", self.reference.strip())


@dataclass(frozen=True)
class DayRigProposal:
    capability: DayCapabilityProposal
    choices: tuple[ProposedDayRig, ...]
    before: DailyRigValidation
    after: DailyRigValidation
    state: CheckState
    comparison: DayOptionComparison
    input_fingerprint: str
    proposal_fingerprint: str
    missing_rig_ids: tuple[int, ...]
    pending_validators: tuple[str, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def _choice_visit(visit, choice, masters, *, original=None):
    rig = masters.get(choice.actual_rig_id)
    return RigVisit(
        visit,
        original if original is not None else choice.original_rig_id,
        choice.actual_rig_id,
        choice.operational_confirmed,
        visit.record_kind != "LegacyHalfDay",
        rig.condition_revision if rig else 0,
        evidence_source="Proposed",
    )


def validate_day_rig_proposal(
    snapshot, candidate, members=(), source_overrides=(), choices=()
):
    capability = validate_day_capability_proposal(
        snapshot, candidate, members, source_overrides
    )
    if (
        type(choices) is not tuple
        or len(choices) > 366
        or any(not isinstance(c, ProposedDayRig) for c in choices)
    ):
        raise ValueError("Supply immutable bounded per-date Rig choices.")
    supplied = {c.local_date: c for c in choices}
    if len(supplied) != len(choices) or set(supplied) - set(
        candidate.allocated_working_dates
    ):
        raise ValueError("Resolve duplicate or out-of-plan Rig choices.")
    normalized = tuple(
        supplied.get(day, ProposedDayRig(day, None, False, "Actual Rig not recorded"))
        for day in candidate.allocated_working_dates
    )
    saved, rigs, periods = snapshot_rig_inputs(snapshot)
    masters = {r.rig_id: r for r in rigs}
    missing = tuple(
        sorted(
            {
                r
                for c in normalized
                for r in (c.actual_rig_id, c.original_rig_id)
                if r is not None
            }
            - set(masters)
        )
    )
    args = dict(
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
    )
    before = validate_daily_rigs(saved, rigs, periods, scope_complete=True, **args)
    projected = {c.visit.key: c.visit for c in capability.driver.after.personnel.checks}
    effective = tuple(
        replace(o, visit=projected.get(o.visit.key, o.visit)) for o in saved
    )
    targets = {c.visit.local_date: c.visit for c in capability.target_checks}
    proposed = tuple(
        _choice_visit(targets[c.local_date], c, masters) for c in normalized
    )
    after = validate_daily_rigs(
        (*effective, *proposed), rigs, periods, scope_complete=not missing, **args
    )
    source_keys = {c.visit.key for c in capability.source_checks}
    selected = {
        c.observation.visit.local_date: [c]
        for c in after.checks
        if c.observation.visit.record_kind == "Proposal"
    }
    for c in after.checks:
        if c.observation.visit.key in source_keys:
            selected[c.observation.visit.local_date].append(c)
    by_day = {
        day: {
            "RigAvailability": _aggregate([c.availability_state for c in checks]),
            "RigConflicts": _aggregate([c.occupancy_state for c in checks]),
        }
        for day, checks in selected.items()
    }
    base = (*capability.comparison.options, *capability.comparison.excluded)[0].option
    option = replace(
        base,
        days=tuple(
            replace(
                day,
                evidence=tuple(
                    e for e in day.evidence if e.check not in by_day[day.local_date]
                )
                + tuple(
                    ConstraintEvidence(k, v) for k, v in by_day[day.local_date].items()
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
        for c in capability.pending_validators
        if c not in by_day[base.days[0].local_date]
        or any(states[c] == "Pending" for states in by_day.values())
    ) + ("RigDriverCategory",)
    state = _aggregate(
        [
            capability.state,
            *(state for states in by_day.values() for state in states.values()),
        ]
    )
    return DayRigProposal(
        capability,
        normalized,
        before,
        after,
        state,
        comparison,
        snapshot.input_fingerprint,
        _digest(
            (
                "rigarus-day-rig-proposal-v1",
                capability.proposal_fingerprint,
                tuple(asdict(c) for c in normalized),
            )
        ),
        missing,
        pending,
    )


@dataclass(frozen=True)
class SavedRigChangeProposal:
    snapshot: DayRecommendationSnapshot
    record_kind: str
    record_id: int
    expected_assignment_revision: int
    expected_allocation_revision: int
    choice: ProposedDayRig
    before: DailyRigValidation
    after: DailyRigValidation
    state: CheckState
    input_fingerprint: str
    proposal_fingerprint: str
    missing_rig_ids: tuple[int, ...]
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_saved_rig_change(
    snapshot,
    record_kind,
    record_id,
    expected_assignment_revision,
    expected_allocation_revision,
    choice,
):
    if not isinstance(snapshot, DayRecommendationSnapshot) or not isinstance(
        choice, ProposedDayRig
    ):
        raise ValueError("Supply an immutable snapshot and explicit dated Rig choice.")
    positive_id(record_id)
    positive_id(expected_assignment_revision)
    if (
        type(expected_allocation_revision) is not int
        or expected_allocation_revision < 0
    ):
        raise ValueError("Reload allocation revision.")
    saved, rigs, periods = snapshot_rig_inputs(snapshot)
    original = next(
        (
            o
            for o in saved
            if (o.visit.record_kind, o.visit.record_id) == (record_kind, record_id)
        ),
        None,
    )
    if (
        original is None
        or original.visit.status != "Draft"
        or original.visit.revision != expected_assignment_revision
        or original.allocation_revision != expected_allocation_revision
        or original.context_stale
        or choice.local_date != original.visit.local_date
    ):
        raise ValueError(
            "Rig change must match an active current source/date/revision; review stale context first."
        )
    if original.visit.record_kind == "LegacyHalfDay":
        raise ValueError(
            "Legacy occupancy needs review; do not turn it into a new full-day swap."
        )
    if (
        choice.original_rig_id is not None
        and choice.original_rig_id != original.original_rig_id
    ):
        raise ValueError("Retain the source original Rig identity.")
    masters = {r.rig_id: r for r in rigs}
    missing = (
        ()
        if choice.actual_rig_id is None or choice.actual_rig_id in masters
        else (choice.actual_rig_id,)
    )
    args = dict(
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
    )
    before = validate_daily_rigs(saved, rigs, periods, scope_complete=True, **args)
    changed = _choice_visit(
        original.visit, choice, masters, original=original.original_rig_id
    )
    after = validate_daily_rigs(
        tuple(changed if o.visit.key == original.visit.key else o for o in saved),
        rigs,
        periods,
        scope_complete=not missing,
        **args,
    )
    state = next(
        c.state for c in after.checks if c.observation.visit.key == original.visit.key
    )
    return SavedRigChangeProposal(
        snapshot,
        record_kind,
        record_id,
        expected_assignment_revision,
        expected_allocation_revision,
        choice,
        before,
        after,
        state,
        snapshot.input_fingerprint,
        _digest(
            (
                "rigarus-saved-rig-change-v1",
                snapshot.input_fingerprint,
                record_kind,
                record_id,
                expected_assignment_revision,
                expected_allocation_revision,
                asdict(choice),
            )
        ),
        missing,
    )


def check_rig_proposal_freshness(path, result):
    if isinstance(result, DayRigProposal):
        snapshot = result.capability.driver.snapshot
    elif isinstance(result, SavedRigChangeProposal):
        snapshot = result.snapshot
    else:
        raise ValueError("Supply an immutable Rig proposal.")
    return check_day_snapshot_freshness(path, snapshot)
