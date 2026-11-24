"""Consistent persisted inputs for planning, never dispatch or Apply approval.

All SQLite reads share one mode=ro/query-only transaction. Frozen observations
are detached before the pure generator runs. No Store public read method,
initialization, migration, checkpoint, write or resource-approval inference.
"""

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import monotonic
from typing import Literal

from . import storage
from .availability_store import snapshot as availability_snapshot
from .recommendation_comparison import CHECKS, SortOrder, compare_explicit_options
from .recommendation_generator import (
    CrewOccupancySnapshot,
    DateSlot,
    GenerationComparison,
    GenerationRequest,
    _positive,
    _range,
    generate_and_compare,
)
from .staffing_persistence import read_staffing
from .working_calendar_store import owner, snapshot as calendar_snapshot
from .work_calendars import WorkCalendar, WorkCalendarCell

FORMAT = "rigarus-recommendation-input-v1"
MAX_OBSERVED_ROWS = 100_000  # Technical workload bound, not staffing policy.
READ_SECONDS = 30
PENDING_VALIDATORS = tuple(
    x
    for x in CHECKS
    if x
    not in (
        "CrewCalendar",
        "ProjectCalendar",
        "CrewOccupancy",
    )
)
CURRENT_HISTORY = (
    *storage.CREW_HISTORY,
    storage.EMPLOYEE_ROSTER,
    storage.RIG_INVENTORY,
    storage.FOREMAN_HISTORY,
    storage.DRAFT_ASSIGNMENTS,
    storage.ASSIGNMENT_STAFFING,
    storage.EMPLOYEE_AVAILABILITY,
    storage.WORKING_CALENDARS,
)
CURRENT_TABLES = storage.CREW_TABLES | {
    "Employees",
    "Rigs",
    "ForemanChanges",
    "DraftAssignments",
    "AssignmentStaffingChanges",
    "AssignmentStaffingMembers",
    "EmployeeAvailabilityChanges",
    "EmployeeAvailability",
    *storage.CALENDAR_TABLES,
}


class SnapshotNotFound(LookupError):
    """A referenced source row is missing, distinct from a failed read."""


class SnapshotContextError(ValueError):
    pass


class SnapshotReadError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Recommendation snapshot unavailable ({code}).")


@dataclass(frozen=True)
class RecommendationQuery:
    work_item_id: int
    crew_ids: tuple[int, ...]
    confirmed_remaining_half_days: int | None
    remaining_confirmed_by_operator: bool
    earliest_start_date: str
    horizon_end_date: str
    expected_project_id: int | None = None
    order: SortOrder = "EarliestFinish"
    max_options: int = 3

    def __post_init__(self):
        _positive(self.work_item_id, "WorkItem ID")
        if self.expected_project_id is not None:
            _positive(self.expected_project_id, "Expected Project ID")
        if type(self.crew_ids) is not tuple or not 1 <= len(self.crew_ids) <= 100:
            raise ValueError("Select 1 to 100 immutable Crew IDs.")
        for crew_id in self.crew_ids:
            _positive(crew_id, "Crew ID")
        if len(set(self.crew_ids)) != len(self.crew_ids):
            raise ValueError("Duplicate Crew IDs require resolution.")
        object.__setattr__(self, "crew_ids", tuple(sorted(self.crew_ids)))
        if self.confirmed_remaining_half_days is not None:
            _positive(self.confirmed_remaining_half_days, "Remaining Half-days")
        if type(self.remaining_confirmed_by_operator) is not bool:
            raise ValueError("Operator confirmation must be explicitly boolean.")
        _range(self.earliest_start_date, self.horizon_end_date)
        compare_explicit_options(
            self.work_item_id, 1, (), max_options=self.max_options, order=self.order
        )


@dataclass(frozen=True)
class WorkItemSource:
    work_item_id: int
    project_id: int
    job_number: str
    work_type: str
    required_crew_count: int
    estimated_half_days: int  # Reference only; never used as Remaining.


@dataclass(frozen=True)
class CalendarSource:
    calendar: WorkCalendar
    calendar_id: int | None
    revision: int
    latest_change_id: int | None


@dataclass(frozen=True)
class ForemanSource:
    change_id: int
    employee_id: int | None
    recorded_at: str


@dataclass(frozen=True)
class CrewSource:
    crew_id: int
    name: str
    crew_type: str
    active: bool
    foreman: ForemanSource | None
    calendar: CalendarSource
    review_reasons: tuple[str, ...]


@dataclass(frozen=True)
class AssignmentSource:
    assignment_id: int
    work_item_id: int
    project_id: int
    crew_id: int
    local_date: str
    slot: str
    status: str
    revision: int
    updated_at: str
    staffing_change_id: int
    staffing_configured: bool
    actual_employee_ids: tuple[int, ...]


@dataclass(frozen=True)
class AvailabilityCell:
    local_date: str
    slot: str
    state: str


@dataclass(frozen=True)
class EmployeeSource:
    employee_id: int
    home_crew_id: int
    skill_level: int
    foreman_eligible: bool
    active: bool
    driver_status: str
    availability_revision: int
    availability: tuple[AvailabilityCell, ...]  # Sparse; absent = Unknown.


def _digest(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class RecommendationSnapshot:
    source_id: str  # Opaque location scope, not a database UUID/global version.
    query: RecommendationQuery
    migrations: tuple[str, ...]
    work_item: WorkItemSource
    project_calendar: CalendarSource
    crews: tuple[CrewSource, ...]
    assignments: tuple[AssignmentSource, ...]
    employees: tuple[EmployeeSource, ...]
    input_fingerprint: str = field(default="", init=False)

    def __post_init__(self):
        payload = asdict(self)
        payload.pop("input_fingerprint")
        object.__setattr__(self, "input_fingerprint", _digest((FORMAT, payload)))


def _rows(connection, sql, params=()):
    rows = connection.execute(sql, params).fetchmany(MAX_OBSERVED_ROWS + 1)
    if len(rows) > MAX_OBSERVED_ROWS:
        raise SnapshotReadError("READ_LIMIT_EXCEEDED")
    return rows


def _read_schema(connection):
    tables = {
        r[0]
        for r in _rows(
            connection,
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT GLOB 'sqlite_*'",
        )
    }
    if tables != CURRENT_TABLES:
        raise storage.UnsupportedDatabaseError(
            "Recommendation snapshot requires the current supported Rigarus schema."
        )
    history = tuple(
        r[0]
        for r in _rows(
            connection,
            "SELECT MigrationId FROM __EFMigrationsHistory ORDER BY MigrationId",
        )
    )
    if history != CURRENT_HISTORY:
        raise storage.UnsupportedDatabaseError(
            "Recommendation snapshot requires the current supported Rigarus migrations."
        )
    if (
        connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]
        or connection.execute("PRAGMA foreign_key_check").fetchone() is not None
    ):
        raise SnapshotReadError("DATABASE_INVALID")
    return history


def _calendar_source(connection, scope, entity_id, query):
    current = calendar_snapshot(
        connection, scope, entity_id, query.earliest_start_date, query.horizon_end_date
    )
    calendar_id, _ = owner(connection, scope, entity_id)
    change = connection.execute(
        "SELECT max(Id) FROM WorkingCalendarChanges WHERE CalendarId=?", (calendar_id,)
    ).fetchone()[0]
    return CalendarSource(
        WorkCalendar(
            scope, entity_id, tuple(WorkCalendarCell(**x) for x in current["entries"])
        ),
        calendar_id,
        current["revision"],
        change,
    )


def _read_sources(connection, query, source_id, migrations):
    row = connection.execute(
        """SELECT w.Id,w.ProjectId,p.JobNumber,w.Type,w.RequiredCrewCount,w.EstimatedHalfDays
        FROM WorkItems w JOIN Projects p ON p.Id=w.ProjectId WHERE w.Id=?""",
        (query.work_item_id,),
    ).fetchone()
    if row is None:
        raise SnapshotNotFound("WorkItem or its parent Project was not found.")
    work_item = WorkItemSource(*row)
    if (
        query.expected_project_id is not None
        and work_item.project_id != query.expected_project_id
    ):
        raise SnapshotContextError(
            "WorkItem does not belong to the expected parent Project."
        )
    project_calendar = _calendar_source(
        connection, "Project", work_item.project_id, query
    )
    crews = []
    for crew_id in query.crew_ids:
        row = connection.execute(
            "SELECT Id,Name,Type,Active FROM Crews WHERE Id=?", (crew_id,)
        ).fetchone()
        if row is None:
            raise SnapshotNotFound("A selected Crew was not found.")
        foreman = connection.execute(
            "SELECT Id,EmployeeId,RecordedAt FROM ForemanChanges WHERE CrewId=? ORDER BY Id DESC LIMIT 1",
            (crew_id,),
        ).fetchone()
        reasons = []
        if not row[3]:
            reasons.append("CREW_INACTIVE")
        if work_item.work_type not in ("Civil", "Tower"):
            reasons.append("WORK_TYPE_MAPPING_PENDING")
        elif row[2] != work_item.work_type:
            reasons.append("CREW_TYPE_MISMATCH")
        crews.append(
            CrewSource(
                *row[:3],
                bool(row[3]),
                ForemanSource(*foreman) if foreman else None,
                _calendar_source(connection, "Crew", crew_id, query),
                tuple(reasons),
            )
        )
    placeholders = ",".join("?" for _ in query.crew_ids)
    assignments = []
    observed_count = 0
    for row in _rows(
        connection,
        f"""SELECT a.Id,a.WorkItemId,w.ProjectId,a.CrewId,a.LocalDate,a.Slot,a.Status,a.Revision,a.UpdatedAt
        FROM DraftAssignments a JOIN WorkItems w ON w.Id=a.WorkItemId
        WHERE a.CrewId IN ({placeholders}) AND a.LocalDate BETWEEN ? AND ?
        ORDER BY a.CrewId,a.LocalDate,a.Slot,a.Id""",
        (*query.crew_ids, query.earliest_start_date, query.horizon_end_date),
    ):
        staffing = read_staffing(connection, row[0])
        observed_count += 1 + len(staffing.workers)
        if observed_count > MAX_OBSERVED_ROWS:
            raise SnapshotReadError("READ_LIMIT_EXCEEDED")
        assignments.append(
            AssignmentSource(
                *row,
                staffing.change_id,
                staffing.configured,
                tuple(w.employee_id for w in staffing.workers),
            )
        )
    employee_ids = {
        r[0]
        for r in _rows(
            connection,
            f"SELECT Id FROM Employees WHERE HomeCrewId IN ({placeholders})",
            query.crew_ids,
        )
    }
    employee_ids.update(e for a in assignments for e in a.actual_employee_ids)
    employee_ids.update(
        c.foreman.employee_id
        for c in crews
        if c.foreman and c.foreman.employee_id is not None
    )
    employees = []
    for employee_id in sorted(employee_ids):
        row = connection.execute(
            "SELECT Id,HomeCrewId,SkillLevel,ForemanEligible,Active,DriverStatus FROM Employees WHERE Id=?",
            (employee_id,),
        ).fetchone()
        if row is None:
            raise SnapshotReadError("DATABASE_INVALID")
        available = availability_snapshot(
            connection, employee_id, query.earliest_start_date, query.horizon_end_date
        )
        observed_count += 1 + len(available["entries"])
        if observed_count > MAX_OBSERVED_ROWS:
            raise SnapshotReadError("READ_LIMIT_EXCEEDED")
        employees.append(
            EmployeeSource(
                *row[:3],
                bool(row[3]),
                bool(row[4]),
                row[5],
                available["revision"],
                tuple(AvailabilityCell(**x) for x in available["entries"]),
            )
        )
    return RecommendationSnapshot(
        source_id,
        query,
        migrations,
        work_item,
        project_calendar,
        tuple(crews),
        tuple(assignments),
        tuple(employees),
    )


def build_recommendation_snapshot(
    path: Path, query: RecommendationQuery
) -> RecommendationSnapshot:
    """Read current-schema local SQLite in one bounded, read-only transaction.

    No automatic upgrade. WAL/SHM coordination remains SQLite's responsibility.
    Missing source rows, wrong parent and unsupported schema remain distinct
    exceptions; storage failures yield no snapshot or fabricated Unknown cells.
    """
    if not isinstance(path, Path) or not isinstance(query, RecommendationQuery):
        raise ValueError("Supply a local database Path and RecommendationQuery.")
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
            migrations = _read_schema(connection)  # First read pins the view.
            result = _read_sources(connection, query, source_id, migrations)
            if progress():
                raise SnapshotReadError("READ_DEADLINE_EXCEEDED")
            return result
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


@dataclass(frozen=True)
class CrewReview:
    crew_id: int
    reasons: tuple[str, ...]
    status: Literal["Needs Review"] = field(default="Needs Review", init=False)
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


@dataclass(frozen=True)
class PersistedRecommendations:
    snapshot: RecommendationSnapshot
    generated: GenerationComparison
    crew_reviews: tuple[CrewReview, ...]
    pending_validators: tuple[str, ...] = field(default=PENDING_VALIDATORS, init=False)
    validation_status: Literal["Pending"] = field(default="Pending", init=False)
    applyable: Literal[False] = field(default=False, init=False)
    publishable: Literal[False] = field(default=False, init=False)


def generation_requests(
    snapshot: RecommendationSnapshot,
) -> tuple[GenerationRequest, ...]:
    """Pure conversion; occupancy never excludes the target WorkItem's visits."""
    if not isinstance(snapshot, RecommendationSnapshot):
        raise ValueError("Supply a RecommendationSnapshot.")
    q, work = snapshot.query, snapshot.work_item
    return tuple(
        GenerationRequest(
            option_id=c.crew_id,
            work_item_id=work.work_item_id,
            project_id=work.project_id,
            crew_id=c.crew_id,
            required_crew_count=work.required_crew_count,
            confirmed_remaining_half_days=q.confirmed_remaining_half_days,
            remaining_confirmed_by_operator=q.remaining_confirmed_by_operator,
            earliest_start_date=q.earliest_start_date,
            horizon_end_date=q.horizon_end_date,
            crew_calendar=c.calendar.calendar,
            project_calendar=snapshot.project_calendar.calendar,
            occupancy=CrewOccupancySnapshot(
                c.crew_id,
                q.earliest_start_date,
                q.horizon_end_date,
                tuple(
                    DateSlot(a.local_date, a.slot)
                    for a in snapshot.assignments
                    if a.crew_id == c.crew_id and a.status == "Draft"
                ),
            ),
            # No actual proposed workers/Rig/consent or safety passes inferred.
        )
        for c in snapshot.crews
        if not c.review_reasons
    )


def generate_from_persisted_snapshot(
    snapshot: RecommendationSnapshot,
) -> PersistedRecommendations:
    requests = generation_requests(snapshot)
    q = snapshot.query
    return PersistedRecommendations(
        snapshot,
        generate_and_compare(
            snapshot.work_item.work_item_id,
            snapshot.work_item.project_id,
            requests,
            max_options=q.max_options,
            order=q.order,
        ),
        tuple(
            CrewReview(c.crew_id, c.review_reasons)
            for c in snapshot.crews
            if c.review_reasons
        ),
    )


@dataclass(frozen=True)
class SnapshotFreshness:
    status: Literal["Current", "Stale"]
    expected_fingerprint: str
    current_fingerprint: str | None
    reason: str


def check_snapshot_freshness(
    path: Path, snapshot: RecommendationSnapshot
) -> SnapshotFreshness:
    """Scoped change detection, not a global revision, lock or Apply authority.

    Read failures propagate. Missing/moved source rows are Stale, not an empty
    successful plan. Even Current can change immediately after this read closes.
    """
    if not isinstance(snapshot, RecommendationSnapshot):
        raise ValueError("Supply a RecommendationSnapshot.")
    try:
        current = build_recommendation_snapshot(path, snapshot.query)
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
