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

from .driver_store import snapshot as driver_snapshot
from .driver_eligibility import (
    DriverCell,
    DriverWorker,
    DriverValidation,
    validate_drivers,
)
from .capability_store import snapshot as capability_snapshot, qualification_snapshots
from .capability_validation import (
    CapabilityCrew,
    CapabilityWorkItem,
    CapabilitySources,
    RequirementCell,
    QualificationCell,
    CapabilityWorker,
    CapabilityValidation,
    validate_capabilities,
)
from . import storage
from .availability_store import snapshot as availability_snapshot
from .personnel_conflicts import (
    StaffedVisit,
    PersonnelValidation,
    validate_employee_conflicts,
)
from .recommendation_comparison import CHECKS, SortOrder, validate_comparison_settings
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

FORMAT = "rigarus-recommendation-input-v4"
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
    storage.DRIVER_APPROVALS,
    storage.CAPABILITY_EVIDENCE,
    storage.DAY_DRAFTS,
    storage.DAILY_CALENDARS,
    storage.DAILY_DRIVERS,
    storage.DAILY_CAPABILITIES,
    storage.DAILY_RIGS,
    storage.DAILY_WEEKEND,
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
    *storage.DRIVER_TABLES,
    *storage.CAPABILITY_TABLES,
    *storage.DAY_TABLES,
    *storage.DAILY_TABLES,
    *storage.DAILY_DRIVER_TABLES,
    *storage.DAILY_CAPABILITY_TABLES,
    *storage.DAILY_RIG_TABLES,
    *storage.DAILY_WEEKEND_TABLES,
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
        validate_comparison_settings(max_options=self.max_options, order=self.order)


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
    driver_revision: int
    driver_approvals: tuple[DriverCell, ...]


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
    personnel_assignments: tuple[AssignmentSource, ...]
    capability_sources: CapabilitySources
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


def _personnel_sources(connection, query):
    """Every Crew in this horizon, read once in the caller's pinned view."""
    assignments = []
    observed_count = 0
    for row in _rows(
        connection,
        """SELECT a.Id,a.WorkItemId,w.ProjectId,a.CrewId,a.LocalDate,a.Slot,a.Status,a.Revision,a.UpdatedAt
        FROM DraftAssignments a JOIN WorkItems w ON w.Id=a.WorkItemId
        WHERE a.LocalDate BETWEEN ? AND ? ORDER BY a.CrewId,a.LocalDate,a.Slot,a.Id""",
        (query.earliest_start_date, query.horizon_end_date),
    ):
        staffing = read_staffing(connection, row[0])
        if not staffing.configured and staffing.workers:
            raise SnapshotReadError("DATABASE_INVALID")
        if staffing.change_id:
            context = connection.execute(
                "SELECT WorkItemId,CrewId,LocalDate,Slot,AssignmentRevision FROM AssignmentStaffingChanges WHERE Id=?",
                (staffing.change_id,),
            ).fetchone()
            if (
                context is None
                or tuple(context[:4]) != (row[1], row[3], row[4], row[5])
                or not 1 <= context[4] <= row[7]
            ):
                raise SnapshotReadError("DATABASE_INVALID")
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
    return tuple(assignments), observed_count


def _capability_sources(connection, query, assignments, employee_ids, observed_count):
    crews, items, policy_owners, policies, qualification_owners, qualifications = (
        [],
        [],
        [],
        [],
        [],
        [],
    )

    def count(amount):
        nonlocal observed_count
        observed_count += amount
        if observed_count > MAX_OBSERVED_ROWS:
            raise SnapshotReadError("READ_LIMIT_EXCEEDED")

    for crew_id in sorted(set(query.crew_ids) | {a.crew_id for a in assignments}):
        row = connection.execute(
            "SELECT Id,Type,Active FROM Crews WHERE Id=?", (crew_id,)
        ).fetchone()
        if row is None:
            raise SnapshotReadError("DATABASE_INVALID")
        count(1)
        crews.append(CapabilityCrew(row[0], row[1], bool(row[2])))
    for item_id in sorted({query.work_item_id} | {a.work_item_id for a in assignments}):
        row = connection.execute(
            "SELECT Id,ProjectId,Type FROM WorkItems WHERE Id=?", (item_id,)
        ).fetchone()
        if row is None:
            raise SnapshotReadError("DATABASE_INVALID")
        items.append(CapabilityWorkItem(*row))
        source = capability_snapshot(
            connection,
            "WorkItem",
            item_id,
            "",
            query.earliest_start_date,
            query.horizon_end_date,
        )
        count(1 + bool(source["owner_id"]) + len(source["entries"]))
        if source["owner_id"] is not None:
            policy_owners.append((item_id, source["owner_id"], source["revision"]))
        policies.extend(
            RequirementCell(
                item_id,
                e["local_date"],
                e["slot"],
                e["value"],
                e["change_id"],
                e["company_confirmed"],
            )
            for e in source["entries"]
        )
    for employee_id in sorted(employee_ids):
        for code, source in qualification_snapshots(
            connection, employee_id, query.earliest_start_date, query.horizon_end_date
        ):
            count(1 + len(source["entries"]))
            qualification_owners.append(
                (employee_id, code, source["owner_id"], source["revision"])
            )
            qualifications.extend(
                QualificationCell(
                    employee_id,
                    code,
                    e["local_date"],
                    e["slot"],
                    e["value"],
                    e["change_id"],
                    e["company_confirmed"],
                )
                for e in source["entries"]
            )
    return CapabilitySources(
        tuple(crews),
        tuple(items),
        tuple(policy_owners),
        tuple(policies),
        tuple(qualification_owners),
        tuple(qualifications),
    )


def _read_sources(connection, query, source_id, migrations):
    if connection.execute(
        "SELECT 1 FROM WeekendConsentScopes WHERE LocalDate BETWEEN ? AND ? LIMIT 1",
        (query.earliest_start_date, query.horizon_end_date),
    ).fetchone():
        raise SnapshotContextError(
            "DAILY_WEEKEND_ADAPTER_REQUIRED: full-day actual-worker decisions cannot be ignored."
        )
    if (
        connection.execute(
            "SELECT 1 FROM RigCurrentAllocations WHERE LocalDate BETWEEN ? AND ? OR RecordedDate BETWEEN ? AND ? LIMIT 1",
            (
                query.earliest_start_date,
                query.horizon_end_date,
                query.earliest_start_date,
                query.horizon_end_date,
            ),
        ).fetchone()
        or connection.execute(
            "SELECT 1 FROM RigCurrentConditions WHERE StartDate<=? AND EndDate>=? LIMIT 1",
            (query.horizon_end_date, query.earliest_start_date),
        ).fetchone()
    ):
        raise SnapshotContextError(
            "DAILY_RIG_ADAPTER_REQUIRED: actual daily Rig data cannot be ignored by the half-day generator."
        )
    if connection.execute(
        "SELECT 1 FROM DailyCapabilityCells WHERE LocalDate BETWEEN ? AND ? LIMIT 1",
        (query.earliest_start_date, query.horizon_end_date),
    ).fetchone():
        raise SnapshotContextError(
            "DAILY_CAPABILITY_ADAPTER_REQUIRED: full-date evidence cannot enter the half-day generator."
        )
    if connection.execute(
        "SELECT 1 FROM DailyDriverApprovalCells WHERE LocalDate BETWEEN ? AND ? LIMIT 1",
        (query.earliest_start_date, query.horizon_end_date),
    ).fetchone():
        raise SnapshotContextError(
            "DAILY_DRIVER_ADAPTER_REQUIRED: daily company evidence cannot enter the legacy half-day generator."
        )
    if connection.execute(
        "SELECT 1 FROM DailyCalendarCells WHERE LocalDate BETWEEN ? AND ? LIMIT 1",
        (query.earliest_start_date, query.horizon_end_date),
    ).fetchone():
        raise SnapshotContextError(
            "DAILY_CALENDAR_ADAPTER_REQUIRED: daily evidence cannot be ignored by the legacy half-day generator."
        )
    if connection.execute(
        "SELECT 1 FROM DayDraftAssignments WHERE LocalDate BETWEEN ? AND ? LIMIT 1",
        (query.earliest_start_date, query.horizon_end_date),
    ).fetchone():
        raise SnapshotContextError(
            "DAY_BASED_ADAPTER_REQUIRED: full-day records cannot enter the legacy half-day generator."
        )
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
    personnel_assignments, observed_count = _personnel_sources(connection, query)
    selected = set(query.crew_ids)
    assignments = tuple(a for a in personnel_assignments if a.crew_id in selected)
    employee_ids = {
        r[0]
        for r in _rows(
            connection,
            f"SELECT Id FROM Employees WHERE HomeCrewId IN ({placeholders})",
            query.crew_ids,
        )
    }
    employee_ids.update(e for a in personnel_assignments for e in a.actual_employee_ids)
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
        try:
            driver = driver_snapshot(
                connection,
                employee_id,
                query.earliest_start_date,
                query.horizon_end_date,
            )
        except ValueError:
            raise SnapshotReadError("DATABASE_INVALID") from None
        observed_count += 1 + len(available["entries"]) + len(driver["entries"])
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
                driver["revision"],
                tuple(
                    DriverCell(employee_id=employee_id, **x) for x in driver["entries"]
                ),
            )
        )
    try:
        capability = _capability_sources(
            connection, query, personnel_assignments, employee_ids, observed_count
        )
    except (ValueError, LookupError):
        raise SnapshotReadError("DATABASE_INVALID") from None
    return RecommendationSnapshot(
        source_id,
        query,
        migrations,
        work_item,
        project_calendar,
        tuple(crews),
        tuple(assignments),
        tuple(employees),
        personnel_assignments,
        capability,
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
    personnel_validation: PersonnelValidation
    driver_validation: DriverValidation
    capability_validation: CapabilityValidation
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


def validate_snapshot_personnel(
    snapshot: RecommendationSnapshot,
) -> PersonnelValidation:
    """Saved Drafts only; a clear check is not evidence for unstaffed proposals."""
    if not isinstance(snapshot, RecommendationSnapshot):
        raise ValueError("Supply a RecommendationSnapshot.")
    return validate_employee_conflicts(
        tuple(
            StaffedVisit(
                a.assignment_id,
                a.work_item_id,
                a.project_id,
                a.crew_id,
                a.local_date,
                a.slot,
                a.status,
                a.staffing_configured,
                a.actual_employee_ids,
            )
            for a in snapshot.personnel_assignments
        ),
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=True,
    )


def validate_snapshot_drivers(snapshot: RecommendationSnapshot) -> DriverValidation:
    if not isinstance(snapshot, RecommendationSnapshot):
        raise ValueError("Supply a RecommendationSnapshot.")
    personnel = validate_snapshot_personnel(snapshot)
    return validate_drivers(
        tuple(c.visit for c in personnel.checks),
        tuple(
            DriverWorker(
                e.employee_id,
                e.active,
                tuple((c.local_date, c.slot, c.state) for c in e.availability),
            )
            for e in snapshot.employees
        ),
        tuple(c for e in snapshot.employees for c in e.driver_approvals),
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=True,
    )


def validate_snapshot_capabilities(
    snapshot: RecommendationSnapshot,
) -> CapabilityValidation:
    if not isinstance(snapshot, RecommendationSnapshot):
        raise ValueError("Supply a RecommendationSnapshot.")
    personnel = validate_snapshot_personnel(snapshot)
    return validate_capabilities(
        tuple(c.visit for c in personnel.checks),
        tuple(
            CapabilityWorker(
                e.employee_id,
                e.active,
                e.skill_level,
                tuple((c.local_date, c.slot, c.state) for c in e.availability),
            )
            for e in snapshot.employees
        ),
        snapshot.capability_sources,
        start_date=snapshot.query.earliest_start_date,
        end_date=snapshot.query.horizon_end_date,
        scope_complete=True,
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
        validate_snapshot_personnel(snapshot),
        validate_snapshot_drivers(snapshot),
        validate_snapshot_capabilities(snapshot),
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
    except (SnapshotNotFound, SnapshotContextError) as error:
        return SnapshotFreshness(
            "Stale",
            snapshot.input_fingerprint,
            None,
            "DAILY_WEEKEND_ADAPTER_REQUIRED"
            if str(error).startswith("DAILY_WEEKEND_ADAPTER_REQUIRED:")
            else "DAILY_RIG_ADAPTER_REQUIRED"
            if str(error).startswith("DAILY_RIG_ADAPTER_REQUIRED:")
            else "DAILY_CAPABILITY_ADAPTER_REQUIRED"
            if str(error).startswith("DAILY_CAPABILITY_ADAPTER_REQUIRED:")
            else "DAILY_DRIVER_ADAPTER_REQUIRED"
            if str(error).startswith("DAILY_DRIVER_ADAPTER_REQUIRED:")
            else "DAY_BASED_ADAPTER_REQUIRED"
            if str(error).startswith("DAY_BASED_ADAPTER_REQUIRED:")
            else "DAILY_CALENDAR_ADAPTER_REQUIRED"
            if str(error).startswith("DAILY_CALENDAR_ADAPTER_REQUIRED:")
            else "SOURCE_RECORD_MISSING_OR_MOVED",
        )
    same = current.input_fingerprint == snapshot.input_fingerprint
    return SnapshotFreshness(
        "Current" if same else "Stale",
        snapshot.input_fingerprint,
        current.input_fingerprint,
        "INPUTS_UNCHANGED" if same else "INPUTS_CHANGED",
    )
