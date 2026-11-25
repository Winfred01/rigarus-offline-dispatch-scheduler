"""Pure exact-roster full-day consent; no attendance or dispatch authority."""

import hashlib
import json
from datetime import date
from dataclasses import dataclass, field
from typing import Literal

from .assignments import local_date
from .day_drafts import positive_id
from .daily_personnel_conflicts import DailyStaffedVisit

LIMIT = 100_000


def roster_ids(values):
    if type(values) is not tuple or not 1 <= len(values) <= 1000:
        raise ValueError("Supply 1–1000 explicit actual/planned workers.")
    for value in values:
        positive_id(value)
    if len(set(values)) != len(values):
        raise ValueError("Duplicate actual workers require review.")
    return tuple(sorted(values))


@dataclass(frozen=True)
class WeekendContext:
    work_item_id: int
    project_id: int
    crew_id: int
    local_date: str
    employee_ids: tuple[int, ...]

    def __post_init__(self):
        for identity in (self.work_item_id, self.project_id, self.crew_id):
            positive_id(identity)
        if date.fromisoformat(local_date(self.local_date)).weekday() < 5:
            raise ValueError("Consent scope must be a local Saturday or Sunday.")
        object.__setattr__(self, "employee_ids", roster_ids(self.employee_ids))

    @property
    def roster_fingerprint(self):
        raw = (
            "rigarus-full-day-consent-roster-v1",
            self.work_item_id,
            self.project_id,
            self.crew_id,
            self.local_date,
            self.employee_ids,
        )
        return hashlib.sha256(
            json.dumps(raw, separators=(",", ":")).encode()
        ).hexdigest()

    @property
    def key(self):
        return (self.work_item_id, self.project_id, self.crew_id, self.local_date)


@dataclass(frozen=True)
class WeekendCrewDay:
    crew_id: int
    local_date: str
    employee_ids: tuple[int, ...]

    def __post_init__(self):
        positive_id(self.crew_id)
        if date.fromisoformat(local_date(self.local_date)).weekday() < 5:
            raise ValueError("Nominate an explicit weekend date.")
        object.__setattr__(self, "employee_ids", roster_ids(self.employee_ids))


@dataclass(frozen=True)
class WeekendConsentFact:
    context: WeekendContext
    employee_id: int
    state: str
    revision: int
    change_id: int
    reference: str
    source_kind: str
    source_id: int | None = None
    source_revision: int | None = None

    def __post_init__(self):
        if not isinstance(self.context, WeekendContext):
            raise ValueError("Supply an explicit full-day context.")
        for identity in (self.employee_id, self.revision, self.change_id):
            positive_id(identity)
        if self.employee_id not in self.context.employee_ids:
            raise ValueError("Consent employee must belong to the explicit roster.")
        if self.state not in ("Pending", "Confirmed", "Declined"):
            raise ValueError("Record Pending, Confirmed or Declined.")
        if (
            not isinstance(self.reference, str)
            or not 1 <= len(self.reference.strip()) <= 200
            or "\0" in self.reference
        ):
            raise ValueError("Supply a bounded explicit decision reference.")
        if self.source_kind == "FullDayDraft":
            positive_id(self.source_id)
            positive_id(self.source_revision)
        elif (
            self.source_kind != "Proposed"
            or self.source_id is not None
            or self.source_revision is not None
        ):
            raise ValueError(
                "Consent must identify explicit proposed or saved full-day provenance."
            )


@dataclass(frozen=True)
class WeekendMemberCheck:
    employee_id: int
    state: str
    reason: str
    fact: WeekendConsentFact | None


@dataclass(frozen=True)
class WeekendVisitCheck:
    visit: DailyStaffedVisit
    state: str
    members: tuple[WeekendMemberCheck, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class WeekendValidation:
    checks: tuple[WeekendVisitCheck, ...]
    state: str
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def aggregate(states):
    return (
        "Blocked"
        if "Blocked" in states
        else "Pending"
        if not states or "Pending" in states
        else "Satisfied"
    )


def validate_weekend_consent(visits, facts, *, scope_complete=True):
    if (
        type(visits) is not tuple
        or type(facts) is not tuple
        or type(scope_complete) is not bool
    ):
        raise ValueError("Supply immutable explicit consent observations.")
    if len(visits) + len(facts) > LIMIT:
        raise ValueError("Consent observation limit exceeded.")
    if any(not isinstance(v, DailyStaffedVisit) for v in visits) or any(
        not isinstance(f, WeekendConsentFact) for f in facts
    ):
        raise ValueError("Supply typed dated visits and full-day facts.")
    if (
        sum(len(v.employee_ids) for v in visits)
        + sum(len(f.context.employee_ids) for f in facts)
        > LIMIT
    ):
        raise ValueError("Consent membership limit exceeded.")
    if len({v.key for v in visits}) != len(visits):
        raise ValueError("Duplicate consent visit identity.")
    index = {}
    for fact in facts:
        key = (*fact.context.key, fact.employee_id)
        if key in index:
            raise ValueError("Supply only one latest decision per employee/scope.")
        index[key] = fact
    checks = []
    for visit in sorted(visits, key=lambda v: v.key):
        if visit.status == "Cancelled":
            continue
        if date.fromisoformat(local_date(visit.local_date)).weekday() < 5:
            checks.append(
                WeekendVisitCheck(
                    visit, "Satisfied", (), ("WEEKDAY_CONSENT_NOT_APPLICABLE",)
                )
            )
            continue
        context = (
            WeekendContext(
                visit.work_item_id,
                visit.project_id,
                visit.crew_id,
                visit.local_date,
                visit.employee_ids,
            )
            if visit.employee_ids
            else None
        )
        reasons = []
        if not visit.staffing_configured or not context:
            reasons.append("ACTUAL_WEEKEND_WORKERS_NOT_RECORDED")
        if visit.record_kind == "LegacyHalfDay":
            reasons.append("LEGACY_HALF_DAY_NEEDS_REVIEW")
        if not scope_complete:
            reasons.append("WEEKEND_CONSENT_SCOPE_INCOMPLETE")
        members = []
        for employee in visit.employee_ids:
            fact = index.get((*context.key, employee))
            state, reason = "Pending", "WEEKEND_DECISION_NOT_RECORDED"
            if fact:
                if fact.state == "Declined":
                    state, reason = "Blocked", "ACTUAL_WORKER_DECLINED"
                elif fact.state == "Pending":
                    reason = "ACTUAL_WORKER_PENDING"
                elif fact.context.roster_fingerprint != context.roster_fingerprint:
                    reason = "WEEKEND_ROSTER_CHANGED_RECONFIRM"
                elif fact.source_kind == "FullDayDraft" and (
                    visit.record_kind != "FullDayDraft"
                    or fact.source_id != visit.record_id
                    or fact.source_revision != visit.revision
                ):
                    reason = "SAVED_WEEKEND_CONTEXT_CHANGED_RECONFIRM"
                elif fact.source_kind == "Proposed" and visit.record_kind != "Proposal":
                    reason = "PLANNED_CONSENT_NEEDS_SAVED_REVIEW"
                elif visit.record_kind != "LegacyHalfDay" and scope_complete:
                    state, reason = "Satisfied", "FULL_DAY_ACTUAL_WORKER_CONFIRMED"
            members.append(WeekendMemberCheck(employee, state, reason, fact))
        states = [m.state for m in members] + (["Pending"] if reasons else [])
        checks.append(
            WeekendVisitCheck(visit, aggregate(states), tuple(members), tuple(reasons))
        )
    return WeekendValidation(tuple(checks), aggregate([c.state for c in checks]))
