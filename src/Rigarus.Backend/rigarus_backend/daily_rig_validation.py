"""Pure whole-date actual Rig safety, never vehicle-category or dispatch approval."""

from dataclasses import dataclass, field
from typing import Literal

from .assignments import local_date
from .availability import range_dates
from .day_drafts import positive_id
from .daily_personnel_conflicts import DailyStaffedVisit
from .daily_driver_validation import _aggregate
from .recommendation_comparison import CheckState
from .recommendation_generator import _range


@dataclass(frozen=True)
class DailyRigMaster:
    rig_id: int
    active: bool
    default_crew_id: int | None
    condition_revision: int

    def __post_init__(self):
        positive_id(self.rig_id)
        if self.default_crew_id is not None:
            positive_id(self.default_crew_id)
        if (
            type(self.active) is not bool
            or type(self.condition_revision) is not int
            or self.condition_revision < 0
        ):
            raise ValueError(
                "Supply explicit Rig master state/native condition revision."
            )


@dataclass(frozen=True)
class RigCondition:
    period_id: int
    rig_id: int
    kind: str
    start_date: str
    end_date: str
    status: str
    revision: int

    def __post_init__(self):
        for identity in (self.period_id, self.rig_id, self.revision):
            positive_id(identity)
        range_dates(self.start_date, self.end_date)
        if self.kind not in (
            "Maintenance",
            "Inspection",
            "OutOfService",
        ) or self.status not in ("Active", "Cancelled"):
            raise ValueError("Supply independent dated condition identity/state.")


@dataclass(frozen=True)
class RigVisit:
    visit: DailyStaffedVisit
    original_rig_id: int | None
    actual_rig_id: int | None
    operational_confirmed: bool
    full_day_confirmed: bool
    condition_revision: int
    allocation_revision: int = 0
    context_stale: bool = False
    recorded_date: str | None = None
    recorded_crew_id: int | None = None
    evidence_source: Literal["Saved", "Proposed"] = "Saved"
    recorded_work_item_id: int | None = None
    recorded_project_id: int | None = None

    def __post_init__(self):
        if self.evidence_source not in ("Saved", "Proposed"):
            raise ValueError("Identify saved versus projected Rig evidence explicitly.")
        if not isinstance(self.visit, DailyStaffedVisit):
            raise ValueError("Supply an exact namespaced visit.")
        for identity in (
            self.original_rig_id,
            self.actual_rig_id,
            self.recorded_crew_id,
            self.recorded_work_item_id,
            self.recorded_project_id,
        ):
            if identity is not None:
                positive_id(identity)
        if any(
            type(b) is not bool
            for b in (
                self.operational_confirmed,
                self.full_day_confirmed,
                self.context_stale,
            )
        ):
            raise ValueError("Declare operational/full-date/context state explicitly.")
        if any(
            type(n) is not int or n < 0
            for n in (self.condition_revision, self.allocation_revision)
        ):
            raise ValueError("Supply nonnegative native revisions.")
        if (self.recorded_date is None) != (self.recorded_crew_id is None):
            raise ValueError("Recorded date/Crew context must be complete.")
        if self.recorded_date is not None:
            local_date(self.recorded_date)
        if (self.recorded_work_item_id is None) != (
            self.recorded_project_id is None
        ) or (self.recorded_work_item_id is not None and self.recorded_date is None):
            raise ValueError(
                "Recorded WorkItem/Project context must be complete and dated."
            )
        if self.full_day_confirmed and self.visit.record_kind == "LegacyHalfDay":
            raise ValueError("Legacy half-day occupancy is never full-date readiness.")
        if self.operational_confirmed and (
            self.actual_rig_id is None or not self.full_day_confirmed
        ):
            raise ValueError(
                "Operational confirmation requires explicit full-day actual Rig."
            )
        if (
            self.operational_confirmed
            and self.evidence_source == "Saved"
            and self.allocation_revision == 0
        ):
            raise ValueError(
                "Saved operational evidence requires its allocation revision."
            )


@dataclass(frozen=True)
class RigOccupancyReference:
    record_kind: str
    record_id: int
    record_date: str
    work_item_id: int | None
    project_id: int | None
    crew_id: int
    claimed_date: str
    revision: int
    legacy_slot: str | None
    source: str

    @property
    def key(self):
        return self.record_kind, self.record_id, self.record_date


@dataclass(frozen=True)
class RigCollision:
    rig_id: int
    local_date: str
    visits: tuple[RigOccupancyReference, ...]


@dataclass(frozen=True)
class RigVisitCheck:
    observation: RigVisit
    availability_state: CheckState
    occupancy_state: CheckState
    state: CheckState
    blocked_period_ids: tuple[int, ...]
    default_rig_ids: tuple[int, ...]
    reasons: tuple[str, ...]
    driver_category_state: Literal["Pending"] = field(default="Pending", init=False)


@dataclass(frozen=True)
class DailyRigValidation:
    checks: tuple[RigVisitCheck, ...]
    conflicts: tuple[RigCollision, ...]
    state: CheckState
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_daily_rigs(
    visits, rigs, conditions, *, start_date, end_date, scope_complete
):
    _range(start_date, end_date)
    if type(scope_complete) is not bool:
        raise ValueError("Declare complete Rig evidence scope explicitly.")
    for rows, cls in (
        (visits, RigVisit),
        (rigs, DailyRigMaster),
        (conditions, RigCondition),
    ):
        if (
            type(rows) is not tuple
            or len(rows) > 100000
            or any(not isinstance(r, cls) for r in rows)
        ):
            raise ValueError("Supply bounded immutable Rig observations.")
    if sum(map(len, (visits, rigs, conditions))) > 100000:
        raise ValueError("Rig evidence workload bound exceeded.")
    masters = {r.rig_id: r for r in rigs}
    if (
        len(masters) != len(rigs)
        or len({v.visit.key for v in visits}) != len(visits)
        or len({p.period_id for p in conditions}) != len(conditions)
    ):
        raise ValueError("Duplicate current Rig observations require resolution.")
    saved = [
        (v.visit.record_kind, v.visit.record_id)
        for v in visits
        if v.visit.record_kind != "Proposal"
    ]
    if len(set(saved)) != len(saved):
        raise ValueError("Duplicate saved identities require resolution.")
    defaults = {}
    for r in rigs:
        if r.default_crew_id is not None:
            defaults.setdefault(r.default_crew_id, []).append(r.rig_id)
    blocked = {}
    work = 0
    for p in conditions:
        if p.status != "Active":
            continue
        first, last = max(start_date, p.start_date), min(end_date, p.end_date)
        if first > last:
            continue
        dates = range_dates(first, last)
        work += len(dates)
        if work > 100000:
            raise ValueError("Condition projection workload exceeded.")
        for day in dates:
            blocked.setdefault((p.rig_id, day), []).append(p.period_id)
    blocked = {key: tuple(sorted(ids)) for key, ids in blocked.items()}
    groups = {}
    unknown = {}
    active = sorted(
        (v for v in visits if v.visit.status == "Draft"), key=lambda o: o.visit.key
    )
    for o in active:
        v = o.visit
        claims = {(v.crew_id, v.local_date): "Current"}
        if o.recorded_date is not None:
            claims.setdefault((o.recorded_crew_id, o.recorded_date), "Recorded")
        if not any(start_date <= day <= end_date for _, day in claims):
            raise ValueError("Rig visit has no context in this horizon.")
        for (crew, day), source in sorted(claims.items()):
            if not start_date <= day <= end_date:
                continue
            work += 1
            if work > 100000:
                raise ValueError("Rig occupancy workload exceeded.")
            if o.actual_rig_id is None:
                unknown.setdefault(day, set()).add(crew)
            else:
                groups.setdefault((o.actual_rig_id, day), []).append(
                    RigOccupancyReference(
                        v.record_kind,
                        v.record_id,
                        v.local_date,
                        v.work_item_id
                        if source == "Current"
                        else o.recorded_work_item_id,
                        v.project_id if source == "Current" else o.recorded_project_id,
                        crew,
                        day,
                        v.revision,
                        v.legacy_slot,
                        source,
                    )
                )
    collisions = []
    conflicted = set()
    for (rig, day), refs in sorted(groups.items()):
        if len({r.crew_id for r in refs}) > 1 and len({r.key for r in refs}) > 1:
            collisions.append(RigCollision(rig, day, tuple(refs)))
            conflicted.update(r.key for r in refs)
    checks = []
    for o in active:
        v = o.visit
        master = masters.get(o.actual_rig_id)
        reasons = []
        dates = tuple(
            sorted(
                {
                    d
                    for d in (v.local_date, o.recorded_date)
                    if d is not None and start_date <= d <= end_date
                }
            )
        )
        period_ids = tuple(
            sorted(
                {p for day in dates for p in blocked.get((o.actual_rig_id, day), ())}
            )
        )
        work += len(period_ids)
        if work > 100000:
            raise ValueError("Rig assessment workload exceeded.")
        if master and not master.active:
            reasons.append("RIG_INACTIVE")
        if period_ids:
            reasons.append("RIG_CONDITION_BLOCKED")
        availability = "Blocked" if reasons else "Pending"
        if not reasons:
            if o.actual_rig_id is None:
                reasons.append("ACTUAL_RIG_NOT_RECORDED")
            elif master is None:
                reasons.append("RIG_CONTEXT_MISSING")
            elif o.context_stale or o.condition_revision != master.condition_revision:
                reasons.append("RIG_OPERATIONAL_EVIDENCE_STALE")
            elif not o.operational_confirmed or not o.full_day_confirmed:
                reasons.append("FULL_DAY_OPERATIONAL_CONFIRMATION_MISSING")
            elif not scope_complete:
                reasons.append("RIG_SCOPE_INCOMPLETE")
            else:
                availability = "Satisfied"
        possible_unknown = any(
            unknown.get(day)
            and (len(unknown[day]) > 1 or v.crew_id not in unknown[day])
            for day in dates
        )
        occupancy = (
            "Blocked"
            if v.key in conflicted
            else "Pending"
            if o.actual_rig_id is None
            or o.context_stale
            or possible_unknown
            or not scope_complete
            else "Satisfied"
        )
        if occupancy == "Blocked":
            reasons.append("RIG_DOUBLE_BOOKED_DAY")
        elif occupancy == "Pending":
            reasons.append("RIG_OCCUPANCY_REQUIRES_REVIEW")
        reasons.append("RIG_DRIVER_CATEGORY_VALIDATION_PENDING")
        if o.evidence_source == "Proposed":
            reasons.append("PROPOSED_OPERATIONAL_ASSERTION_REQUIRES_REVALIDATION")
        checks.append(
            RigVisitCheck(
                o,
                availability,
                occupancy,
                _aggregate([availability, occupancy]),
                period_ids,
                tuple(sorted(defaults.get(v.crew_id, ()))),
                tuple(reasons),
            )
        )
    return DailyRigValidation(
        tuple(checks), tuple(collisions), _aggregate([c.state for c in checks])
    )


def snapshot_rig_inputs(snapshot):
    """Detached conversion, retaining stale outside-horizon recorded occupancy."""
    import json
    from .day_recommendation_adapter import day_staffed_visits

    raw = json.loads(snapshot.rig_source_json)
    visits = {v.key: v for v in day_staffed_visits(snapshot)}
    allocations = {}
    for a in raw["allocations"]:
        c = a["context"]
        key = (c["record_kind"], c["record_id"], c["local_date"])
        if key not in visits:
            visits[key] = DailyStaffedVisit(
                c["record_kind"],
                c["record_id"],
                c["work_item_id"],
                c["project_id"],
                c["crew_id"],
                c["local_date"],
                c["assignment_revision"],
                c["status"],
                False,
                (),
                c["legacy_slot"],
            )
        allocations[key] = a
    observations = []
    for key, v in sorted(visits.items()):
        a = allocations.get(key, {})
        observations.append(
            RigVisit(
                v,
                a.get("original_rig_id"),
                a.get("actual_rig_id"),
                bool(a.get("operational_confirmed", False)),
                bool(a.get("full_day_confirmed", False)),
                a.get("condition_revision", 0),
                a.get("revision", 0),
                a.get("context_stale", False),
                a.get("recorded_date"),
                a.get("recorded_crew_id"),
                recorded_work_item_id=a.get("recorded_work_item_id"),
                recorded_project_id=a.get("recorded_project_id"),
            )
        )
    rigs = tuple(
        DailyRigMaster(
            r["metadata"][0],
            bool(r["metadata"][5]),
            r["metadata"][4],
            r["condition_revision"],
        )
        for r in raw["rigs"]
    )
    periods = tuple(
        RigCondition(
            p["period_id"],
            p["rig_id"],
            p["kind"],
            p["start_date"],
            p["end_date"],
            p["status"],
            p["revision"],
        )
        for p in raw["conditions"]
    )
    return tuple(observations), rigs, periods


def validate_day_snapshot_rigs(snapshot):
    return validate_daily_rigs(
        *snapshot_rig_inputs(snapshot),
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=True,
    )
