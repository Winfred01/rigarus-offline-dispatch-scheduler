"""Pure actual-worker checks against explicit company requirements, not safety approval."""

import re
from dataclasses import asdict, dataclass, field
from typing import Literal

from .assignments import local_date
from .driver_eligibility import DriverWorker
from .personnel_conflicts import StaffedVisit, validate_employee_conflicts
from .recommendation_comparison import CheckState, _positive_id

MAX_EVIDENCE = 100_000
QUALIFICATION_STATES = ("Verified", "NotVerified", "Unknown")


def qualification_code(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.-]{0,49}", value
    ):
        raise ValueError(
            "Supply an exact company qualification code (1 to 50 ASCII characters)."
        )
    return value


def _count(value, *, zero=True):
    if type(value) is not int or not (0 if zero else 1) <= value <= MAX_EVIDENCE:
        raise ValueError("Supply a bounded explicit integer requirement.")


@dataclass(frozen=True)
class CapabilityRequirements:
    minimum_members: int
    level_minimums: tuple[int, int, int]
    level_mode: Literal["Exact", "AtLeast"]
    qualification_minimums: tuple[tuple[str, int], ...]

    def __post_init__(self):
        _count(self.minimum_members, zero=False)
        if type(self.level_minimums) is not tuple or len(self.level_minimums) != 3:
            raise ValueError("Explicitly supply Level 1, 2 and 3 minima.")
        for value in self.level_minimums:
            _count(value)
        if self.level_mode not in ("Exact", "AtLeast"):
            raise ValueError("Explicitly choose Exact or AtLeast level counting.")
        if (
            type(self.qualification_minimums) is not tuple
            or len(self.qualification_minimums) > 32
        ):
            raise ValueError("Explicitly supply at most 32 qualification requirements.")
        codes = set()
        for row in self.qualification_minimums:
            if type(row) is not tuple or len(row) != 2:
                raise ValueError("Supply immutable qualification/count pairs.")
            code, minimum = row
            qualification_code(code)
            _count(minimum, zero=False)
            if code in codes:
                raise ValueError("Duplicate qualification requirements.")
            codes.add(code)
        object.__setattr__(
            self, "qualification_minimums", tuple(sorted(self.qualification_minimums))
        )

    def payload(self):
        return {"version": 1, "requirements": asdict(self)}


def parse_payload(value, *, policy):
    if (
        type(value) is not dict
        or type(value.get("version")) is not int
        or value["version"] != 1
    ):
        raise ValueError("Unsupported capability evidence payload.")
    if not policy:
        if (
            set(value) != {"version", "state"}
            or value["state"] not in QUALIFICATION_STATES
        ):
            raise ValueError("Invalid qualification evidence state.")
        return value["state"]
    if set(value) != {"version", "requirements"}:
        raise ValueError("Invalid requirement payload.")
    data = value["requirements"]
    if (
        type(data) is not dict
        or set(data)
        != {"minimum_members", "level_minimums", "level_mode", "qualification_minimums"}
        or type(data["level_minimums"]) is not list
        or type(data["qualification_minimums"]) is not list
    ):
        raise ValueError("Supply the complete explicit requirements contract.")
    if any(type(row) is not list for row in data["qualification_minimums"]):
        raise ValueError("Invalid qualification/count pairs.")
    return CapabilityRequirements(
        data["minimum_members"],
        tuple(data["level_minimums"]),
        data["level_mode"],
        tuple(tuple(row) for row in data["qualification_minimums"]),
    )


def _cell(subject_id, day, half, change_id, confirmed):
    _positive_id(subject_id)
    _positive_id(change_id)
    local_date(day)
    if half not in ("AM", "PM") or confirmed is not True:
        raise ValueError("Supply an explicitly confirmed dated AM/PM evidence cell.")


@dataclass(frozen=True)
class RequirementCell:
    work_item_id: int
    local_date: str
    slot: str
    requirements: CapabilityRequirements
    change_id: int
    company_confirmed: bool

    def __post_init__(self):
        _cell(
            self.work_item_id,
            self.local_date,
            self.slot,
            self.change_id,
            self.company_confirmed,
        )
        if not isinstance(self.requirements, CapabilityRequirements):
            raise ValueError("Supply explicit validated requirements.")


@dataclass(frozen=True)
class QualificationCell:
    employee_id: int
    code: str
    local_date: str
    slot: str
    state: str
    change_id: int
    company_confirmed: bool

    def __post_init__(self):
        _cell(
            self.employee_id,
            self.local_date,
            self.slot,
            self.change_id,
            self.company_confirmed,
        )
        qualification_code(self.code)
        if self.state not in QUALIFICATION_STATES:
            raise ValueError("Supply explicit qualification evidence state.")


@dataclass(frozen=True)
class CapabilityWorker:
    employee_id: int
    active: bool
    skill_level: int
    availability: tuple[tuple[str, str, str], ...]

    def __post_init__(self):
        validated = DriverWorker(self.employee_id, self.active, self.availability)
        if type(self.skill_level) is not int or not 1 <= self.skill_level <= 3:
            raise ValueError("Supply recorded Level 1, 2 or 3, not a certificate.")
        object.__setattr__(self, "availability", validated.availability)


@dataclass(frozen=True)
class CapabilityCrew:
    crew_id: int
    crew_type: str
    active: bool

    def __post_init__(self):
        _positive_id(self.crew_id)
        if self.crew_type not in ("Civil", "Tower") or type(self.active) is not bool:
            raise ValueError("Invalid Crew capability observation.")


@dataclass(frozen=True)
class CapabilityWorkItem:
    work_item_id: int
    project_id: int
    work_type: str

    def __post_init__(self):
        _positive_id(self.work_item_id)
        _positive_id(self.project_id)
        if self.work_type not in ("Civil", "Tower", "Small", "Other"):
            raise ValueError("Invalid WorkItem type observation.")


@dataclass(frozen=True)
class CapabilitySources:
    crews: tuple[CapabilityCrew, ...]
    work_items: tuple[CapabilityWorkItem, ...]
    requirement_owners: tuple[
        tuple[int, int, int], ...
    ]  # WorkItem / owner / native revision
    requirements: tuple[RequirementCell, ...]
    qualification_owners: tuple[tuple[int, str, int, int], ...]
    qualifications: tuple[QualificationCell, ...]

    def __post_init__(self):
        for rows, size in (
            (self.requirement_owners, 3),
            (self.qualification_owners, 4),
        ):
            if type(rows) is not tuple or len(rows) > MAX_EVIDENCE:
                raise ValueError("Supply immutable bounded evidence owner identities.")
            for row in rows:
                if type(row) is not tuple or len(row) != size:
                    raise ValueError("Invalid evidence owner identity.")
                _positive_id(row[0])
                if size == 4:
                    qualification_code(row[1])
                _positive_id(row[-2])
                if type(row[-1]) is not int or row[-1] < 0:
                    raise ValueError("Supply native evidence revisions.")


@dataclass(frozen=True)
class CapabilityCount:
    check: str
    required: int | None
    confirmed_employee_ids: tuple[int, ...]
    possible_employee_ids: tuple[
        int, ...
    ]  # Includes confirmed; never promised capacity.
    state: CheckState
    reason: str


@dataclass(frozen=True)
class CapabilityVisitCheck:
    visit: StaffedVisit
    crew_state: CheckState
    crew_reason: str
    requirement_change_id: int | None
    counts: tuple[CapabilityCount, ...]
    state: CheckState
    foreman_state: Literal["Pending"] = field(default="Pending", init=False)


@dataclass(frozen=True)
class CapabilityValidation:
    checks: tuple[CapabilityVisitCheck, ...]
    state: CheckState
    scope: Literal["SavedDraftCrewVisitRequirements"] = field(
        default="SavedDraftCrewVisitRequirements", init=False
    )
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def validate_capabilities(
    visits, workers, sources: CapabilitySources, *, start_date, end_date, scope_complete
) -> CapabilityValidation:
    personnel = validate_employee_conflicts(
        visits, start_date=start_date, end_date=end_date, scope_complete=scope_complete
    )
    if not isinstance(sources, CapabilitySources):
        raise ValueError("Supply immutable capability sources.")
    collections = (
        (workers, CapabilityWorker),
        (sources.crews, CapabilityCrew),
        (sources.work_items, CapabilityWorkItem),
        (sources.requirements, RequirementCell),
        (sources.qualifications, QualificationCell),
    )
    if any(
        type(items) is not tuple
        or len(items) > MAX_EVIDENCE
        or any(not isinstance(x, cls) for x in items)
        for items, cls in collections
    ):
        raise ValueError("Supply bounded immutable capability evidence.")
    if (
        sum(len(items) for items, _ in collections)
        + len(sources.requirement_owners)
        + len(sources.qualification_owners)
        + sum(len(w.availability) for w in workers)
        > MAX_EVIDENCE
    ):
        raise ValueError("Capability evidence exceeds workload bound.")
    people = {w.employee_id: w for w in workers}
    crews = {c.crew_id: c for c in sources.crews}
    work = {w.work_item_id: w for w in sources.work_items}
    policies = {(c.work_item_id, c.local_date, c.slot): c for c in sources.requirements}
    qualifications = {
        (c.employee_id, c.code, c.local_date, c.slot): c for c in sources.qualifications
    }
    if tuple(map(len, (people, crews, work, policies, qualifications))) != tuple(
        len(x) for x, _ in collections
    ):
        raise ValueError("Duplicate capability observations require resolution.")
    if any(
        not start_date <= c.local_date <= end_date
        for c in (*sources.requirements, *sources.qualifications)
    ):
        raise ValueError("Evidence lies outside the declared date scope.")
    available = {
        (w.employee_id, d, h): state for w in workers for d, h, state in w.availability
    }
    results = []
    workload = 0
    for pc in personnel.checks:
        v = pc.visit
        item, crew = work.get(v.work_item_id), crews.get(v.crew_id)
        if item and item.project_id != v.project_id:
            raise ValueError("WorkItem parent context does not match the visit.")
        crew_state, crew_reason = (
            ("Blocked", "CREW_INACTIVE")
            if crew and not crew.active
            else ("Pending", "CAPABILITY_CONTEXT_MISSING")
            if not item or not crew
            else ("Pending", "WORK_TYPE_MAPPING_UNCONFIRMED")
            if item.work_type not in ("Civil", "Tower")
            else ("Blocked", "CREW_WORK_TYPE_MISMATCH")
            if item.work_type != crew.crew_type
            else ("Satisfied", "CREW_WORK_TYPE_MATCHED")
        )
        policy = policies.get((v.work_item_id, v.local_date, v.slot))
        workload += (
            4 + (len(policy.requirements.qualification_minimums) if policy else 1)
        ) * (len(v.employee_ids) + 1)
        if workload > MAX_EVIDENCE:
            raise ValueError("Capability evaluation exceeds its workload bound.")
        definite, possible = [], []
        conflicts = set(pc.conflicting_employee_ids)
        for employee_id in v.employee_ids:
            worker = people.get(employee_id)
            state = available.get((employee_id, v.local_date, v.slot), "Unknown")
            if (
                employee_id in conflicts
                or (worker and not worker.active)
                or state == "Unavailable"
            ):
                continue
            possible.append(employee_id)
            if worker and state == "Available" and scope_complete:
                definite.append(employee_id)

        definite_set = set(definite)

        def assess(name, required, known, potential):
            missing = (
                required is None or not v.employee_ids or not v.staffing_configured
            )
            state = (
                "Pending"
                if missing
                else "Blocked"
                if len(potential) < required
                else "Satisfied"
                if scope_complete and len(known) >= required
                else "Pending"
            )
            reason = (
                "REQUIREMENTS_MISSING"
                if required is None
                else "ACTUAL_STAFFING_REQUIRES_REVIEW"
                if missing
                else "CONFIRMED_REQUIREMENT_SHORTFALL"
                if state == "Blocked"
                else "REQUIREMENT_MET"
                if state == "Satisfied"
                else "EVIDENCE_PENDING"
            )
            return CapabilityCount(
                name, required, tuple(known), tuple(potential), state, reason
            )

        req = policy.requirements if policy else None
        counts = [
            assess(
                "MinimumStaffing",
                req.minimum_members if req else None,
                definite,
                possible,
            )
        ]
        for level in (1, 2, 3):

            def matches(employee_id):
                w = people.get(employee_id)
                return w and (
                    w.skill_level == level
                    if req.level_mode == "Exact"
                    else w.skill_level >= level
                )

            known = [e for e in definite if req and matches(e)]
            potential = [e for e in possible if req and (e not in people or matches(e))]
            counts.append(
                assess(
                    f"SkillsLevel{level}",
                    req.level_minimums[level - 1] if req else None,
                    known,
                    potential,
                )
            )
        for code, minimum in req.qualification_minimums if req else ():
            known, potential = [], []
            for e in possible:
                proof = qualifications.get((e, code, v.local_date, v.slot))
                state = proof.state if proof else "Unknown"
                if state != "NotVerified":
                    potential.append(e)
                if state == "Verified" and e in definite_set:
                    known.append(e)
            counts.append(assess("Qualification:" + code, minimum, known, potential))
        if not req:
            counts.append(assess("Qualifications", None, (), ()))
        # Foreman effective-date/presence policy is unresolved; no full pass.
        state = (
            "Blocked"
            if crew_state == "Blocked" or any(c.state == "Blocked" for c in counts)
            else "Pending"
        )
        results.append(
            CapabilityVisitCheck(
                v,
                crew_state,
                crew_reason,
                policy.change_id if policy else None,
                tuple(counts),
                state,
            )
        )
    return CapabilityValidation(
        tuple(results),
        "Blocked" if any(c.state == "Blocked" for c in results) else "Pending",
    )
