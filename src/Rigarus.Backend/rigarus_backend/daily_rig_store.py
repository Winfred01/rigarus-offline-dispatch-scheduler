"""Internal explicit dated resource evidence; no production allocation/period API."""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone

from .availability import range_dates
from .assignments import local_date
from .day_drafts import positive_id
from .daily_calendar_store import DailyConflict, DailySourceError
from .storage import connect

KINDS = ("Maintenance", "Inspection", "OutOfService")


def _reference(value):
    if (
        not isinstance(value, str)
        or not 1 <= len(value.strip()) <= 200
        or "\0" in value
    ):
        raise ValueError("Supply an explicit reference of1 to200 characters.")
    return value.strip()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def condition_revision(c, rig_id):
    return c.execute(
        "SELECT coalesce(max(h.Id),0) FROM RigConditionChanges h JOIN RigConditionPeriods p ON p.Id=h.PeriodId WHERE p.RigId=?",
        (rig_id,),
    ).fetchone()[0]


@dataclass(frozen=True)
class RigPeriodInput:
    start_date: str
    end_date: str
    status: str
    company_confirmed: bool
    reference: str

    def __post_init__(self):
        range_dates(self.start_date, self.end_date)
        if (
            self.status not in ("Active", "Cancelled")
            or self.company_confirmed is not True
        ):
            raise ValueError(
                "Supply explicitly confirmed Active/Cancelled condition evidence."
            )
        object.__setattr__(self, "reference", _reference(self.reference))


@dataclass(frozen=True)
class RigAllocationInput:
    original_rig_id: int | None
    actual_rig_id: int | None
    operational_confirmed: bool
    company_confirmed: bool
    full_day_confirmed: bool
    reference: str
    condition_revision: int

    def __post_init__(self):
        if type(self.condition_revision) is not int or self.condition_revision < 0:
            raise ValueError("Supply the explicitly reviewed Rig condition revision.")
        for value in (self.original_rig_id, self.actual_rig_id):
            if value is not None:
                positive_id(value)
        if (
            type(self.operational_confirmed) is not bool
            or type(self.full_day_confirmed) is not bool
            or self.company_confirmed is not True
        ):
            raise ValueError(
                "Declare operational/company/full-date evidence explicitly."
            )
        if self.operational_confirmed and (
            self.actual_rig_id is None or not self.full_day_confirmed
        ):
            raise ValueError(
                "Operational confirmation requires an explicit full-day actual Rig."
            )
        object.__setattr__(self, "reference", _reference(self.reference))


def assignment_context(c, kind, identity):
    if kind not in ("FullDayDraft", "LegacyHalfDay"):
        raise ValueError("Choose a saved namespaced assignment identity.")
    positive_id(identity)
    row = c.execute(
        "SELECT * FROM RigAssignmentContexts WHERE RecordKind=? AND AssignmentId=?",
        (kind, identity),
    ).fetchone()
    if row is None:
        raise LookupError("This saved assignment no longer exists.")
    local_date(row[5])
    return dict(
        zip(
            (
                "record_kind",
                "record_id",
                "work_item_id",
                "project_id",
                "crew_id",
                "local_date",
                "assignment_revision",
                "status",
                "legacy_slot",
            ),
            row,
        )
    )


def allocation_snapshot(c, kind, identity):
    context = assignment_context(c, kind, identity)
    column = "DayAssignmentId" if kind == "FullDayDraft" else "LegacyAssignmentId"
    owner = c.execute(
        f"SELECT Id FROM RigAllocations WHERE {column}=?", (identity,)
    ).fetchone()
    row = c.execute(
        "SELECT h.Id,h.Revision,h.AssignmentRevision,h.WorkItemId,h.ProjectId,h.CrewId,h.LocalDate,h.OriginalRigId,h.ActualRigId,h.OperationalConfirmed,h.ConditionRevision,h.FullDayConfirmed,h.Reference FROM RigAllocationChanges h WHERE h.AllocationId=? ORDER BY h.Revision DESC LIMIT 1",
        (owner[0] if owner else None,),
    ).fetchone()
    if owner and row is None:
        raise DailySourceError("Rig allocation history is missing.")
    if row and (
        row[11] != (kind == "FullDayDraft") or (kind == "LegacyHalfDay" and row[9] != 0)
    ):
        raise DailySourceError(
            "Legacy Rig occupancy cannot establish full-day readiness."
        )
    source = (
        dict(
            zip(
                (
                    "change_id",
                    "revision",
                    "recorded_revision",
                    "recorded_work_item_id",
                    "recorded_project_id",
                    "recorded_crew_id",
                    "recorded_date",
                    "original_rig_id",
                    "actual_rig_id",
                    "operational_confirmed",
                    "condition_revision",
                    "full_day_confirmed",
                    "reference",
                ),
                row,
            )
        )
        if row
        else dict(
            revision=0,
            original_rig_id=None,
            actual_rig_id=None,
            operational_confirmed=False,
            full_day_confirmed=False,
            condition_revision=0,
        )
    )
    stale = bool(
        row
        and tuple(row[2:7])
        != (
            context["assignment_revision"],
            context["work_item_id"],
            context["project_id"],
            context["crew_id"],
            context["local_date"],
        )
    )
    return dict(
        context=context,
        allocation_id=owner[0] if owner else None,
        context_stale=stale,
        **source,
    )


def rig_sources(c, start, end, selected_crews, proposed_rigs):
    """Caller owns one query-only view/budget. Never open a second connection."""
    if (
        c.execute(
            "SELECT 1 FROM RigAllocations o WHERE NOT EXISTS(SELECT 1 FROM RigAllocationChanges h WHERE h.AllocationId=o.Id) LIMIT 1"
        ).fetchone()
        or c.execute(
            "SELECT 1 FROM RigConditionPeriods p WHERE NOT EXISTS(SELECT 1 FROM RigConditionChanges h WHERE h.PeriodId=p.Id) LIMIT 1"
        ).fetchone()
    ):
        raise DailySourceError("Rig identity/history is incomplete.")
    keys = c.execute(
        "SELECT RecordKind,AssignmentId FROM RigCurrentAllocations WHERE LocalDate BETWEEN ? AND ? OR RecordedDate BETWEEN ? AND ? ORDER BY RecordKind,AssignmentId",
        (start, end, start, end),
    ).fetchall()
    allocations = tuple(
        allocation_snapshot(c, kind, identity) for kind, identity in keys
    )
    wanted = set(proposed_rigs)
    wanted.update(
        r
        for a in allocations
        for r in (a["original_rig_id"], a["actual_rig_id"])
        if r is not None
    )
    placeholders = ",".join("?" for _ in selected_crews)
    defaults = c.execute(
        f"""SELECT Id FROM Rigs WHERE DefaultCrewId IN ({placeholders})
      OR DefaultCrewId IN (SELECT CrewId FROM RigAssignmentContexts WHERE LocalDate BETWEEN ? AND ?)
      OR DefaultCrewId IN (SELECT CrewId FROM RigCurrentAllocations WHERE RecordedDate BETWEEN ? AND ?)
      OR DefaultCrewId IN (SELECT RecordedCrewId FROM RigCurrentAllocations WHERE RecordedDate BETWEEN ? AND ?)
      ORDER BY Id""",
        (*selected_crews, start, end, start, end, start, end),
    ).fetchall()
    wanted.update(r[0] for r in defaults)
    rigs = []
    conditions = []
    for identity in sorted(wanted):
        row = c.execute(
            "SELECT Id,Number,Type,Notes,DefaultCrewId,Active FROM Rigs WHERE Id=?",
            (identity,),
        ).fetchone()
        if row is None:
            raise LookupError("A proposed/observed Rig no longer exists.")
        native = condition_revision(c, identity)
        rigs.append(dict(metadata=row, condition_revision=native))
        for r in c.execute(
            "SELECT Id,RigId,Kind,ChangeId,Revision,StartDate,EndDate,Status,Reference FROM RigCurrentConditions WHERE RigId=? AND StartDate<=? AND EndDate>=? ORDER BY Id",
            (identity, end, start),
        ):
            range_dates(r[5], r[6])
            conditions.append(
                dict(
                    zip(
                        (
                            "period_id",
                            "rig_id",
                            "kind",
                            "change_id",
                            "revision",
                            "start_date",
                            "end_date",
                            "status",
                            "reference",
                        ),
                        r,
                    )
                )
            )
    return dict(allocations=allocations, rigs=rigs, conditions=conditions)


class DailyRigStore:
    def __init__(self, path):
        self.path = path

    def read_allocation(self, kind, identity):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            return allocation_snapshot(c, kind, identity)

    def read_conditions(self, rig_id, start, end):
        positive_id(rig_id)
        range_dates(start, end)
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            master = c.execute(
                "SELECT Id,Number,Type,Notes,DefaultCrewId,Active FROM Rigs WHERE Id=?",
                (rig_id,),
            ).fetchone()
            if master is None:
                raise LookupError("This Rig no longer exists.")
            native = condition_revision(c, rig_id)
            periods = c.execute(
                "SELECT * FROM RigCurrentConditions WHERE RigId=? AND StartDate<=? AND EndDate>=? ORDER BY Id",
                (rig_id, end, start),
            ).fetchmany(100001)
            if len(periods) > 100000:
                raise DailySourceError("Rig condition read limit exceeded.")
            for p in periods:
                range_dates(p[5], p[6])
            return dict(metadata=master, condition_revision=native, periods=periods)

    def save_allocation(
        self, kind, identity, draft, expected_assignment_revision, expected_revision
    ):
        if not isinstance(draft, RigAllocationInput):
            raise ValueError("Supply explicit actual Rig evidence.")
        positive_id(expected_assignment_revision)
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("Reload allocation revision.")
        if draft.full_day_confirmed != (kind == "FullDayDraft"):
            raise ValueError(
                "Legacy occupancy is explicitly partial, never full-day proof."
            )
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            before = allocation_snapshot(c, kind, identity)
            v = before["context"]
            if (
                v["status"] != "Draft"
                or v["assignment_revision"] != expected_assignment_revision
                or before["revision"] != expected_revision
            ):
                raise DailyConflict(
                    "Assignment/allocation changed. Reload before recording."
                )
            for value in (draft.original_rig_id, draft.actual_rig_id):
                if (
                    value is not None
                    and not c.execute(
                        "SELECT 1 FROM Rigs WHERE Id=?", (value,)
                    ).fetchone()
                ):
                    raise LookupError("This Rig no longer exists.")
            native = condition_revision(c, draft.actual_rig_id)
            if native != draft.condition_revision:
                raise DailyConflict(
                    "Rig conditions changed. Reload before confirming operational status."
                )
            if draft.operational_confirmed and (
                not c.execute(
                    "SELECT 1 FROM Rigs WHERE Id=? AND Active=1", (draft.actual_rig_id,)
                ).fetchone()
                or c.execute(
                    "SELECT 1 FROM RigCurrentConditions WHERE RigId=? AND Status='Active' AND ? BETWEEN StartDate AND EndDate LIMIT 1",
                    (draft.actual_rig_id, v["local_date"]),
                ).fetchone()
            ):
                raise DailyConflict(
                    "Inactive/maintenance/inspection/out-of-service evidence blocks operational confirmation."
                )
            if (
                not before["context_stale"]
                and before["revision"]
                and all(
                    (before[key] == getattr(draft, key))
                    for key in (
                        "original_rig_id",
                        "actual_rig_id",
                        "operational_confirmed",
                        "full_day_confirmed",
                        "reference",
                    )
                )
                and before["condition_revision"] == native
            ):
                return before
            owner = before["allocation_id"]
            if owner is None:
                column = (
                    "DayAssignmentId"
                    if kind == "FullDayDraft"
                    else "LegacyAssignmentId"
                )
                owner = c.execute(
                    f"INSERT INTO RigAllocations({column}) VALUES(?)", (identity,)
                ).lastrowid
            c.execute(
                """INSERT INTO RigAllocationChanges
                (AllocationId,Revision,AssignmentRevision,WorkItemId,ProjectId,CrewId,LocalDate,OriginalRigId,ActualRigId,OperationalConfirmed,ConditionRevision,CompanyConfirmed,FullDayConfirmed,Reference,RecordedAt)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                (
                    owner,
                    expected_revision + 1,
                    expected_assignment_revision,
                    v["work_item_id"],
                    v["project_id"],
                    v["crew_id"],
                    v["local_date"],
                    draft.original_rig_id,
                    draft.actual_rig_id,
                    int(draft.operational_confirmed),
                    native,
                    int(draft.full_day_confirmed),
                    draft.reference,
                    _now(),
                ),
            )
            return allocation_snapshot(c, kind, identity)

    def save_period(self, rig_id, kind, draft, period_id=None, expected_revision=0):
        positive_id(rig_id)
        if (
            kind not in KINDS
            or not isinstance(draft, RigPeriodInput)
            or type(expected_revision) is not int
            or expected_revision < 0
        ):
            raise ValueError("Supply explicit condition kind/input/revision.")
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            if not c.execute("SELECT 1 FROM Rigs WHERE Id=?", (rig_id,)).fetchone():
                raise LookupError("This Rig no longer exists.")
            if period_id is None:
                if expected_revision != 0:
                    raise DailyConflict("Reload the condition identity.")
                period_id = c.execute(
                    "INSERT INTO RigConditionPeriods(RigId,Kind) VALUES(?,?)",
                    (rig_id, kind),
                ).lastrowid
                revision = 0
            else:
                positive_id(period_id)
                owner = c.execute(
                    "SELECT RigId,Kind FROM RigConditionPeriods WHERE Id=?",
                    (period_id,),
                ).fetchone()
                if owner != (rig_id, kind):
                    raise ValueError("Condition identity does not match this Rig/kind.")
                current = c.execute(
                    "SELECT Revision,StartDate,EndDate,Status,Reference FROM RigConditionChanges WHERE PeriodId=? ORDER BY Revision DESC LIMIT 1",
                    (period_id,),
                ).fetchone()
                if current is None:
                    raise DailySourceError("Condition history is missing.")
                revision = current[0]
                if revision != expected_revision:
                    raise DailyConflict("Condition changed. Reload before recording.")
                if current[1:] == (
                    draft.start_date,
                    draft.end_date,
                    draft.status,
                    draft.reference,
                ):
                    return dict(period_id=period_id, revision=revision)
            c.execute(
                "INSERT INTO RigConditionChanges(PeriodId,Revision,StartDate,EndDate,Status,CompanyConfirmed,Reference,RecordedAt) VALUES(?,?,?,?,?,1,?,?)",
                (
                    period_id,
                    revision + 1,
                    draft.start_date,
                    draft.end_date,
                    draft.status,
                    draft.reference,
                    _now(),
                ),
            )
            return dict(period_id=period_id, revision=revision + 1)

    def allocation_history(self, kind, identity):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            source = allocation_snapshot(c, kind, identity)
            return tuple(
                c.execute(
                    "SELECT * FROM RigAllocationChanges WHERE AllocationId=? ORDER BY Revision DESC LIMIT 100",
                    (source["allocation_id"],),
                )
            )

    def period_history(self, period_id):
        positive_id(period_id)
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            return tuple(
                c.execute(
                    "SELECT * FROM RigConditionChanges WHERE PeriodId=? ORDER BY Revision DESC LIMIT 100",
                    (period_id,),
                )
            )
