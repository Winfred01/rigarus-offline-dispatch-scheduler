"""One coherent read-only daily planning view; never dispatch or Apply authority."""

import json
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field, asdict
from pathlib import Path
from time import monotonic
from typing import Literal

from . import storage
from .daily_calendar_store import (
    snapshot as daily_snapshot,
    DailySourceError,
    DailyNotFound,
)
from .day_draft_store import read_day
from .day_drafts import ConfirmedRemainingDays, positive_id
from .driver_store import snapshot as driver_snapshot
from .recommendation_generator import _range
from .recommendation_comparison import SortOrder, validate_comparison_settings
from .recommendation_adapter import (
    WorkItemSource,
    AssignmentSource,
    SnapshotReadError,
    SnapshotNotFound,
    SnapshotContextError,
    SnapshotFreshness,
    CrewReview,
    PENDING_VALIDATORS,
    _digest,
    _read_schema,
    _personnel_sources,
    _capability_sources,
)
from .capability_validation import CapabilitySources
from .daily_personnel_conflicts import (
    DailyStaffedVisit,
    DailyPersonnelValidation,
    validate_daily_employee_conflicts,
)
from .day_recommendation_generator import (
    DayCalendar,
    DayCalendarCell,
    DayOccupancy,
    DayGenerationRequest,
    DayGenerationComparison,
    generate_days_and_compare,
)

FORMAT = "rigarus-day-recommendation-input-v2"
MAX_READ_UNITS = 100_000
READ_SECONDS = 30


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class DayRecommendationQuery:
    work_item_id: int
    crew_ids: tuple[int, ...]
    remaining: ConfirmedRemainingDays | None
    earliest_start_date: str
    horizon_end_date: str
    expected_project_id: int | None = None
    order: SortOrder = "EarliestFinish"
    max_options: int = 3
    proposed_employee_ids: tuple[int, ...] = ()

    def __post_init__(self):
        positive_id(self.work_item_id)
        if self.expected_project_id is not None:
            positive_id(self.expected_project_id)
        if type(self.crew_ids) is not tuple or not 1 <= len(self.crew_ids) <= 100:
            raise ValueError("Select 1 to 100 immutable Crew IDs.")
        for identity in self.crew_ids:
            positive_id(identity)
        if len(set(self.crew_ids)) != len(self.crew_ids):
            raise ValueError("Duplicate Crew IDs require resolution.")
        object.__setattr__(self, "crew_ids", tuple(sorted(self.crew_ids)))
        if (
            type(self.proposed_employee_ids) is not tuple
            or len(self.proposed_employee_ids) > 1000
        ):
            raise ValueError(
                "Supply at most 1000 immutable proposed Employee IDs for observation only."
            )
        for identity in self.proposed_employee_ids:
            positive_id(identity)
        if len(set(self.proposed_employee_ids)) != len(self.proposed_employee_ids):
            raise ValueError("Duplicate proposed Employee IDs require resolution.")
        object.__setattr__(
            self, "proposed_employee_ids", tuple(sorted(self.proposed_employee_ids))
        )
        if (
            self.remaining is not None
            and type(self.remaining) is not ConfirmedRemainingDays
        ):
            raise ValueError(
                "Supply independent explicitly ConfirmedRemainingDays; no half-day fallback."
            )
        _range(self.earliest_start_date, self.horizon_end_date)
        validate_comparison_settings(max_options=self.max_options, order=self.order)


class ReadBudget:
    """Shared materialization/projection budget, independent of SQL progress time."""

    def __init__(self, connection):
        self.connection = connection
        self.remaining = MAX_READ_UNITS

    def charge(self, amount):
        self.remaining -= amount
        if self.remaining < 0:
            raise SnapshotReadError("READ_LIMIT_EXCEEDED")

    def execute(self, sql, parameters=()):
        return BudgetCursor(self.connection.execute(sql, parameters), self)


class BudgetCursor:
    def __init__(self, cursor, budget):
        self.cursor, self.budget = cursor, budget

    def fetchone(self):
        row = self.cursor.fetchone()
        self.budget.charge(int(row is not None))
        return row

    def fetchmany(self, size):
        rows = self.cursor.fetchmany(min(size, self.budget.remaining + 1))
        self.budget.charge(len(rows))
        return rows

    def fetchall(self):
        return self.fetchmany(self.budget.remaining + 1)

    def __iter__(self):
        while (row := self.fetchone()) is not None:
            yield row


@dataclass(frozen=True)
class DailySource:
    scope: str
    entity_id: int
    payload_json: str  # Canonical detached raw/effective cells, revisions and receipts.

    def calendar(self):
        raw = json.loads(self.payload_json)
        return DayCalendar(
            self.scope,
            self.entity_id,
            tuple(
                DayCalendarCell(e["local_date"], e["state"], e["review_status"])
                for e in raw["entries"]
            ),
        )


@dataclass(frozen=True)
class DayCrewSource:
    crew_id: int
    name: str
    crew_type: str
    active: bool
    foreman: tuple | None
    review_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DayAssignmentSource:
    assignment_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    local_date: str
    status: str
    revision: int
    actual_employee_ids: tuple[int, ...]
    payload_json: str  # Namespaced current visit, immutable current change/members.


@dataclass(frozen=True)
class DayEmployeeSource:
    employee_id: int
    metadata: tuple
    legacy_driver_json: str  # Observation only, never whole-day approval.


@dataclass(frozen=True)
class DayRecommendationSnapshot:
    source_id: str
    query: DayRecommendationQuery
    migrations: tuple[str, ...]
    work_item: WorkItemSource  # Old EstimatedHalfDays retained as reference only.
    crews: tuple[DayCrewSource, ...]
    daily_inputs: tuple[DailySource, ...]
    day_assignments: tuple[DayAssignmentSource, ...]
    legacy_assignments: tuple[AssignmentSource, ...]
    employees: tuple[DayEmployeeSource, ...]
    legacy_capability_sources: CapabilitySources
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)
    input_fingerprint: str = field(default="", init=False)

    def __post_init__(self):
        payload = asdict(self)
        payload.pop("input_fingerprint")
        object.__setattr__(self, "input_fingerprint", _digest((FORMAT, payload)))


def _read_day_sources(c, query, source_id, migrations):
    row = c.execute(
        "SELECT w.Id,w.ProjectId,p.JobNumber,w.Type,w.RequiredCrewCount,w.EstimatedHalfDays FROM WorkItems w JOIN Projects p ON p.Id=w.ProjectId WHERE w.Id=?",
        (query.work_item_id,),
    ).fetchone()
    if row is None:
        raise SnapshotNotFound("WorkItem or parent Project was not found.")
    work = WorkItemSource(*row)
    if (
        query.expected_project_id is not None
        and query.expected_project_id != work.project_id
    ):
        raise SnapshotContextError("WorkItem moved from the expected parent Project.")
    crews = []
    for identity in query.crew_ids:
        row = c.execute(
            "SELECT Id,Name,Type,Active FROM Crews WHERE Id=?", (identity,)
        ).fetchone()
        if row is None:
            raise SnapshotNotFound("A selected Crew was not found.")
        foreman = c.execute(
            "SELECT Id,EmployeeId,RecordedAt FROM ForemanChanges WHERE CrewId=? ORDER BY Id DESC LIMIT 1",
            (identity,),
        ).fetchone()
        reasons = []
        if not row[3]:
            reasons.append("CREW_INACTIVE")
        if work.work_type not in ("Civil", "Tower"):
            reasons.append("WORK_TYPE_MAPPING_PENDING")
        elif row[2] != work.work_type:
            reasons.append("CREW_TYPE_MISMATCH")
        crews.append(DayCrewSource(*row[:3], bool(row[3]), foreman, tuple(reasons)))
    legacy, _ = _personnel_sources(c, query)
    days = []
    identities = c.execute(
        "SELECT Id FROM DayDraftAssignments WHERE LocalDate BETWEEN ? AND ? ORDER BY CrewId,LocalDate,Id",
        (query.earliest_start_date, query.horizon_end_date),
    ).fetchall()
    for (identity,) in identities:
        raw = read_day(c, identity)
        change = c.execute(
            "SELECT Id FROM DayDraftChanges WHERE AssignmentId=? AND Revision=?",
            (identity, raw["revision"]),
        ).fetchone()[0]
        members = c.execute(
            "SELECT EmployeeId,EmployeeName,HomeCrewId FROM DayDraftMembers WHERE ChangeId=? ORDER BY EmployeeId",
            (change,),
        ).fetchall()
        if len(members) > 1000 or (not raw["staffing_configured"] and members):
            raise SnapshotReadError("DATABASE_INVALID")
        payload = dict(current=raw, change_id=change, members=members)
        days.append(
            DayAssignmentSource(
                identity,
                raw["work_item_id"],
                raw["project_id"],
                raw["crew_id"],
                raw["local_date"],
                raw["status"],
                raw["revision"],
                tuple(m[0] for m in members),
                canonical(payload),
            )
        )
    placeholders = ",".join("?" for _ in query.crew_ids)
    employee_ids = {
        r[0]
        for r in c.execute(
            f"SELECT Id FROM Employees WHERE HomeCrewId IN ({placeholders})",
            query.crew_ids,
        )
    }
    employee_ids.update(e for a in (*legacy, *days) for e in a.actual_employee_ids)
    employee_ids.update(query.proposed_employee_ids)
    employee_ids.update(
        crew.foreman[1]
        for crew in crews
        if crew.foreman and crew.foreman[1] is not None
    )
    daily = []

    def read_daily(scope, identity):
        raw = daily_snapshot(
            c, scope, identity, query.earliest_start_date, query.horizon_end_date
        )
        c.charge(len(raw["entries"]))
        daily.append(DailySource(scope, identity, canonical(raw)))

    read_daily("Project", work.project_id)
    for identity in query.crew_ids:
        read_daily("Crew", identity)
    employees = []
    for identity in sorted(employee_ids):
        metadata = c.execute(
            "SELECT Id,Name,HomeCrewId,SkillLevel,ForemanEligible,Active,DriverStatus FROM Employees WHERE Id=?",
            (identity,),
        ).fetchone()
        if metadata is None:
            if identity in query.proposed_employee_ids:
                raise SnapshotNotFound("An explicitly proposed Employee was not found.")
            raise SnapshotReadError("DATABASE_INVALID")
        read_daily("Employee", identity)
        driver = driver_snapshot(
            c, identity, query.earliest_start_date, query.horizon_end_date
        )
        employees.append(DayEmployeeSource(identity, metadata, canonical(driver)))
    capability = _capability_sources(c, query, (*legacy, *days), employee_ids, 0)
    return DayRecommendationSnapshot(
        source_id,
        query,
        migrations,
        work,
        tuple(crews),
        tuple(daily),
        tuple(days),
        legacy,
        tuple(employees),
        capability,
    )


def build_day_recommendation_snapshot(path: Path, query: DayRecommendationQuery):
    if not isinstance(path, Path) or not isinstance(query, DayRecommendationQuery):
        raise ValueError("Supply a local Path and independent DayRecommendationQuery.")
    expired = False
    deadline = monotonic() + READ_SECONDS

    def progress():
        nonlocal expired
        expired = monotonic() >= deadline
        return int(expired)

    try:
        source_id = _digest(os.path.normcase(str(path.resolve())))
        with closing(storage.connect(path, read_only=True)) as connection, connection:
            connection.set_progress_handler(progress, 1000)
            connection.execute("BEGIN")
            budget = ReadBudget(connection)
            migrations = _read_schema(
                budget
            )  # First read pins one view for every source.
            result = _read_day_sources(budget, query, source_id, migrations)
            if progress():
                raise SnapshotReadError("READ_DEADLINE_EXCEEDED")
            return result
    except (SnapshotContextError, SnapshotNotFound):
        raise
    except (DailySourceError, DailyNotFound, ValueError, TypeError, OverflowError):
        raise SnapshotReadError("DATABASE_INVALID") from None
    except sqlite3.Error as error:
        code = getattr(error, "sqlite_errorcode", 0) & 0xFF
        label = (
            "READ_DEADLINE_EXCEEDED"
            if expired
            else "DATABASE_BUSY"
            if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
            else "DATABASE_INVALID"
            if code in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB)
            else "DATABASE_UNAVAILABLE"
            if code == sqlite3.SQLITE_CANTOPEN
            else "DATABASE_READ_FAILED"
        )
        raise SnapshotReadError(label) from None
    except OSError:
        raise SnapshotReadError("DATABASE_UNAVAILABLE") from None


def day_generation_requests(snapshot: DayRecommendationSnapshot):
    if not isinstance(snapshot, DayRecommendationSnapshot):
        raise ValueError("Supply an immutable daily snapshot.")
    q, work = snapshot.query, snapshot.work_item
    inputs = {(s.scope, s.entity_id): s for s in snapshot.daily_inputs}
    visits = (*snapshot.day_assignments, *snapshot.legacy_assignments)
    return tuple(
        DayGenerationRequest(
            crew.crew_id,
            work.work_item_id,
            work.project_id,
            crew.crew_id,
            work.required_crew_count,
            q.remaining,
            q.earliest_start_date,
            q.horizon_end_date,
            inputs["Crew", crew.crew_id].calendar(),
            inputs["Project", work.project_id].calendar(),
            DayOccupancy(
                crew.crew_id,
                q.earliest_start_date,
                q.horizon_end_date,
                tuple(
                    sorted(
                        {
                            a.local_date
                            for a in visits
                            if a.crew_id == crew.crew_id and a.status == "Draft"
                        }
                    )
                ),
            ),
        )
        for crew in snapshot.crews
        if not crew.review_reasons
    )


@dataclass(frozen=True)
class PersistedDayRecommendations:
    snapshot: DayRecommendationSnapshot
    generated: DayGenerationComparison
    crew_reviews: tuple[CrewReview, ...]
    personnel_validation: DailyPersonnelValidation
    pending_validators: tuple[str, ...] = field(default=PENDING_VALIDATORS, init=False)
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def generate_from_day_snapshot(snapshot: DayRecommendationSnapshot):
    requests = day_generation_requests(snapshot)
    q = snapshot.query
    generated = generate_days_and_compare(
        q.work_item_id,
        snapshot.work_item.project_id,
        requests,
        max_options=q.max_options,
        order=q.order,
    )
    return PersistedDayRecommendations(
        snapshot,
        generated,
        tuple(
            CrewReview(c.crew_id, c.review_reasons)
            for c in snapshot.crews
            if c.review_reasons
        ),
        validate_day_snapshot_personnel(snapshot),
    )


def day_staffed_visits(snapshot: DayRecommendationSnapshot):
    """Detached current members only, never Home Crew attendance/history union."""
    if not isinstance(snapshot, DayRecommendationSnapshot):
        raise ValueError("Supply a daily recommendation snapshot.")
    days = tuple(
        DailyStaffedVisit(
            "FullDayDraft",
            a.assignment_id,
            a.work_item_id,
            a.project_id,
            a.crew_id,
            a.local_date,
            a.revision,
            a.status,
            json.loads(a.payload_json)["current"]["staffing_configured"],
            a.actual_employee_ids,
        )
        for a in snapshot.day_assignments
    )
    legacy = tuple(
        DailyStaffedVisit(
            "LegacyHalfDay",
            a.assignment_id,
            a.work_item_id,
            a.project_id,
            a.crew_id,
            a.local_date,
            a.revision,
            a.status,
            a.staffing_configured,
            a.actual_employee_ids,
            a.slot,
        )
        for a in snapshot.legacy_assignments
    )
    return (*days, *legacy)


def validate_day_snapshot_personnel(snapshot: DayRecommendationSnapshot):
    return validate_daily_employee_conflicts(
        day_staffed_visits(snapshot),
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=True,
    )


def check_day_snapshot_freshness(path: Path, snapshot: DayRecommendationSnapshot):
    if not isinstance(snapshot, DayRecommendationSnapshot):
        raise ValueError("Supply an immutable daily snapshot.")
    try:
        current = build_day_recommendation_snapshot(path, snapshot.query)
    except (SnapshotNotFound, SnapshotContextError):
        return SnapshotFreshness(
            "Stale", snapshot.input_fingerprint, None, "SOURCE_RECORD_MISSING_OR_MOVED"
        )
    same = current.input_fingerprint == snapshot.input_fingerprint
    return SnapshotFreshness(
        "Current" if same else "Stale",
        snapshot.input_fingerprint,
        current.input_fingerprint,
        "INPUTS_UNCHANGED" if same else "INPUTS_CHANGED",
    )
