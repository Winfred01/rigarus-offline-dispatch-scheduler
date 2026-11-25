"""Pure full-date explicit staffing, Level and independent qualification counts."""

from dataclasses import dataclass, field
from typing import Literal

from .assignments import local_date
from .day_drafts import positive_id
from .capability_validation import (
    CapabilityRequirements,
    CapabilityCrew,
    CapabilityWorkItem,
    CapabilityCount,
    qualification_code,
    QUALIFICATION_STATES,
    parse_payload,
)
from .daily_personnel_conflicts import (
    DailyStaffedVisit,
    DailyPersonnelValidation,
    validate_daily_employee_conflicts,
)
from .recommendation_comparison import CheckState


@dataclass(frozen=True)
class DailyRequirement:
    work_item_id: int
    local_date: str
    requirements: CapabilityRequirements
    change_id: int

    def __post_init__(self):
        positive_id(self.work_item_id)
        positive_id(self.change_id)
        local_date(self.local_date)
        if not isinstance(self.requirements, CapabilityRequirements):
            raise ValueError(
                "Supply explicit independently confirmed daily requirements."
            )


@dataclass(frozen=True)
class DailyQualification:
    employee_id: int
    code: str
    local_date: str
    state: str
    change_id: int | None
    full_day_confirmed: bool

    def __post_init__(self):
        positive_id(self.employee_id)
        qualification_code(self.code)
        local_date(self.local_date)
        if (
            self.state not in QUALIFICATION_STATES
            or type(self.full_day_confirmed) is not bool
        ):
            raise ValueError(
                "Supply explicit qualification state and full-date confirmation."
            )
        if self.change_id is not None:
            positive_id(self.change_id)
        if self.state == "Verified" and (
            not self.full_day_confirmed or self.change_id is None
        ):
            raise ValueError(
                "Verified requires independent complete-day evidence identity."
            )


@dataclass(frozen=True)
class DailyCapabilityWorker:
    employee_id: int
    active: bool
    skill_level: int
    availability: tuple[tuple[str, str], ...]

    def __post_init__(self):
        positive_id(self.employee_id)
        if (
            type(self.active) is not bool
            or type(self.skill_level) is not int
            or not 1 <= self.skill_level <= 3
        ):
            raise ValueError(
                "Supply active status and recorded Level1/2/3, not a certificate."
            )
        if type(self.availability) is not tuple or len(self.availability) > 366:
            raise ValueError("Supply bounded immutable daily availability.")
        for row in self.availability:
            if (
                type(row) is not tuple
                or len(row) != 2
                or row[1] not in ("Available", "Unavailable", "Unknown")
            ):
                raise ValueError("Supply exact daily availability states.")
            local_date(row[0])
        if len({r[0] for r in self.availability}) != len(self.availability):
            raise ValueError("Duplicate daily availability requires resolution.")


@dataclass(frozen=True)
class DailyCapabilitySources:
    crews: tuple[CapabilityCrew, ...]
    work_items: tuple[CapabilityWorkItem, ...]
    requirements: tuple[DailyRequirement, ...]
    qualifications: tuple[DailyQualification, ...]


@dataclass(frozen=True)
class DailyCapabilityCheck:
    visit: DailyStaffedVisit
    crew_state: CheckState
    crew_reason: str
    requirement_change_id: int | None
    counts: tuple[CapabilityCount, ...]
    state: CheckState
    foreman_state: Literal["Pending"] = field(default="Pending", init=False)


@dataclass(frozen=True)
class DailyCapabilityValidation:
    personnel: DailyPersonnelValidation
    checks: tuple[DailyCapabilityCheck, ...]
    state: CheckState
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_daily_capabilities(
    visits, workers, sources, *, start_date, end_date, scope_complete
):
    personnel = validate_daily_employee_conflicts(
        visits, start_date=start_date, end_date=end_date, scope_complete=scope_complete
    )
    if not isinstance(sources, DailyCapabilitySources):
        raise ValueError("Supply independent immutable daily capability sources.")
    collections = (
        (workers, DailyCapabilityWorker),
        (sources.crews, CapabilityCrew),
        (sources.work_items, CapabilityWorkItem),
        (sources.requirements, DailyRequirement),
        (sources.qualifications, DailyQualification),
    )
    if any(
        type(rows) is not tuple
        or len(rows) > 100000
        or any(not isinstance(r, cls) for r in rows)
        for rows, cls in collections
    ):
        raise ValueError("Supply bounded immutable daily capability evidence.")
    if (
        sum(len(r) for r, _ in collections) + sum(len(w.availability) for w in workers)
        > 100000
    ):
        raise ValueError("Capability evidence workload bound exceeded.")
    people = {w.employee_id: w for w in workers}
    crews = {c.crew_id: c for c in sources.crews}
    work = {w.work_item_id: w for w in sources.work_items}
    policies = {(r.work_item_id, r.local_date): r for r in sources.requirements}
    proofs = {(q.employee_id, q.code, q.local_date): q for q in sources.qualifications}
    if tuple(map(len, (people, crews, work, policies, proofs))) != tuple(
        len(rows) for rows, _ in collections
    ):
        raise ValueError("Duplicate daily capability observations require resolution.")
    if any(
        not start_date <= day <= end_date
        for day in [
            *(r.local_date for r in sources.requirements),
            *(q.local_date for q in sources.qualifications),
            *(d for w in workers for d, _ in w.availability),
        ]
    ):
        raise ValueError("Evidence outside declared local-date horizon.")
    available = {
        (w.employee_id, d): state for w in workers for d, state in w.availability
    }
    checks = []
    workload = 0
    for p in personnel.checks:
        v = p.visit
        crew, item = crews.get(v.crew_id), work.get(v.work_item_id)
        if item and item.project_id != v.project_id:
            raise ValueError("WorkItem parent does not match actual visit.")
        crew_state, reason = (
            ("Blocked", "CREW_INACTIVE")
            if crew and not crew.active
            else ("Pending", "CAPABILITY_CONTEXT_MISSING")
            if not crew or not item
            else ("Pending", "WORK_TYPE_MAPPING_UNCONFIRMED")
            if item.work_type not in ("Civil", "Tower")
            else ("Blocked", "CREW_WORK_TYPE_MISMATCH")
            if crew.crew_type != item.work_type
            else ("Satisfied", "CREW_WORK_TYPE_MATCHED")
        )
        policy = policies.get((v.work_item_id, v.local_date))
        req = policy.requirements if policy else None
        workload += (4 + len(req.qualification_minimums) if req else 5) * (
            len(v.employee_ids) + 1
        )
        if workload > 100000:
            raise ValueError("Daily capability evaluation workload exceeded.")
        definite = []
        possible = []
        conflicting = set(p.conflicting_employee_ids)
        for e in v.employee_ids:
            w = people.get(e)
            state = available.get((e, v.local_date), "Unknown")
            if e in conflicting or (w and not w.active) or state == "Unavailable":
                continue
            possible.append(e)
            if (
                w
                and state == "Available"
                and p.state == "Satisfied"
                and v.record_kind != "LegacyHalfDay"
            ):
                definite.append(e)
        definite_set = set(definite)

        def count(name, minimum, known, potential):
            unknown = (
                minimum is None
                or not v.staffing_configured
                or v.record_kind == "LegacyHalfDay"
            )
            state = (
                "Pending"
                if unknown
                else "Blocked"
                if len(potential) < minimum
                else "Satisfied"
                if len(known) >= minimum and scope_complete
                else "Pending"
            )
            why = (
                "REQUIREMENTS_MISSING"
                if minimum is None
                else "FULL_DAY_STAFFING_REVIEW_REQUIRED"
                if unknown
                else "CONFIRMED_REQUIREMENT_SHORTFALL"
                if state == "Blocked"
                else "REQUIREMENT_MET"
                if state == "Satisfied"
                else "EVIDENCE_PENDING"
            )
            return CapabilityCount(
                name, minimum, tuple(known), tuple(potential), state, why
            )

        counts = [
            count(
                "MinimumStaffing",
                req.minimum_members if req else None,
                definite,
                possible,
            )
        ]
        for level in (1, 2, 3):

            def matches(e):
                w = people.get(e)
                return w and (
                    w.skill_level == level
                    if req.level_mode == "Exact"
                    else w.skill_level >= level
                )

            counts.append(
                count(
                    f"SkillsLevel{level}",
                    req.level_minimums[level - 1] if req else None,
                    [e for e in definite if req and matches(e)],
                    [e for e in possible if req and (e not in people or matches(e))],
                )
            )
        for code, minimum in req.qualification_minimums if req else ():
            known = []
            potential = []
            for e in possible:
                proof = proofs.get((e, code, v.local_date))
                state = proof.state if proof else "Unknown"
                if state != "NotVerified":
                    potential.append(e)
                if state == "Verified" and e in definite_set:
                    known.append(e)
            counts.append(count("Qualification:" + code, minimum, known, potential))
        if not req:
            counts.append(count("Qualifications", None, (), ()))
        checks.append(
            DailyCapabilityCheck(
                v,
                crew_state,
                reason,
                policy.change_id if policy else None,
                tuple(counts),
                "Blocked"
                if crew_state == "Blocked" or any(c.state == "Blocked" for c in counts)
                else "Pending",
            )
        )
    return DailyCapabilityValidation(
        personnel,
        tuple(checks),
        "Blocked" if any(c.state == "Blocked" for c in checks) else "Pending",
    )


def snapshot_capability_inputs(snapshot):
    """Detached conversion; positive legacy proof is never used."""
    import json

    availability = {
        s.entity_id: json.loads(s.payload_json)
        for s in snapshot.daily_inputs
        if s.scope == "Employee"
    }
    workers = tuple(
        DailyCapabilityWorker(
            e.employee_id,
            bool(e.metadata[5]),
            e.metadata[3],
            tuple(
                (r["local_date"], r["state"])
                for r in availability[e.employee_id]["entries"]
            ),
        )
        for e in snapshot.employees
    )
    policies = []
    proofs = []
    for source in snapshot.daily_capability_sources:
        raw = json.loads(source.payload_json)
        for e in raw["entries"]:
            value = (
                parse_payload(
                    json.loads(e["payload"]), policy=source.scope == "WorkItem"
                )
                if e["payload"] not in (None, "null")
                else None
            )
            if source.scope == "WorkItem" and value is not None:
                policies.append(
                    DailyRequirement(
                        source.subject_id, e["local_date"], value, e["change_id"]
                    )
                )
            elif source.scope == "Employee" and value is not None:
                proofs.append(
                    DailyQualification(
                        source.subject_id,
                        source.code,
                        e["local_date"],
                        value,
                        e["change_id"],
                        e["review_status"] == "Current",
                    )
                )
    old = snapshot.legacy_capability_sources
    return workers, DailyCapabilitySources(
        old.crews, old.work_items, tuple(policies), tuple(proofs)
    )


def validate_day_snapshot_capabilities(snapshot):
    from .day_recommendation_adapter import day_staffed_visits

    workers, sources = snapshot_capability_inputs(snapshot)
    return validate_daily_capabilities(
        day_staffed_visits(snapshot),
        workers,
        sources,
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=True,
    )
