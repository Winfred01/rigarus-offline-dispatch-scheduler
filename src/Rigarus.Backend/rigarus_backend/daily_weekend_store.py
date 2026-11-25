"""Internal recorded decisions, not employee authentication or an approval API."""

import json
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone

from .storage import connect
from .day_draft_store import read_day
from .day_drafts import positive_id
from .daily_calendar_store import DailyConflict
from .daily_weekend_consent import WeekendContext, WeekendConsentFact


@dataclass(frozen=True)
class WeekendDecision:
    state: str
    employee_decision_confirmed: bool
    full_day_confirmed: bool
    reference: str

    def __post_init__(self):
        if (
            self.state not in ("Pending", "Confirmed", "Declined")
            or type(self.employee_decision_confirmed) is not bool
            or self.full_day_confirmed is not True
        ):
            raise ValueError("Record an explicit full-day employee decision.")
        if self.state != "Pending" and not self.employee_decision_confirmed:
            raise ValueError(
                "Confirmed/Declined needs explicit employee-decision evidence."
            )
        if (
            not isinstance(self.reference, str)
            or not 1 <= len(self.reference.strip()) <= 200
            or "\0" in self.reference
        ):
            raise ValueError("Supply a bounded decision reference.")
        object.__setattr__(self, "reference", self.reference.strip())


def _context(c, context):
    if not isinstance(context, WeekendContext):
        raise ValueError("Supply a complete explicit weekend context.")
    if c.execute(
        "SELECT ProjectId FROM WorkItems WHERE Id=?", (context.work_item_id,)
    ).fetchone() != (context.project_id,):
        raise ValueError("WorkItem parent changed; rebuild context.")
    if (
        c.execute("SELECT Id FROM Crews WHERE Id=?", (context.crew_id,)).fetchone()
        is None
    ):
        raise LookupError("Crew not found.")
    for employee in context.employee_ids:
        if (
            c.execute("SELECT Id FROM Employees WHERE Id=?", (employee,)).fetchone()
            is None
        ):
            raise LookupError("Explicit weekend worker not found.")


def _save(
    c,
    context,
    employee_id,
    decision,
    expected_revision,
    source_kind,
    source_id=None,
    source_revision=None,
):
    positive_id(employee_id)
    if (
        type(expected_revision) is not int
        or expected_revision < 0
        or not isinstance(decision, WeekendDecision)
    ):
        raise ValueError("Supply explicit decision and nonnegative expected revision.")
    _context(c, context)
    if employee_id not in context.employee_ids:
        raise ValueError("Employee is not in the explicit weekend roster.")
    key = (*context.key, employee_id)
    row = c.execute(
        "SELECT Id FROM WeekendConsentScopes WHERE WorkItemId=? AND ProjectId=? AND CrewId=? AND LocalDate=? AND EmployeeId=?",
        key,
    ).fetchone()
    revision = (
        c.execute(
            "SELECT coalesce(max(Revision),0) FROM WeekendConsentChanges WHERE ScopeId=?",
            (row[0],),
        ).fetchone()[0]
        if row
        else 0
    )
    if revision != expected_revision:
        raise DailyConflict("Weekend consent changed. Reload before recording.")
    values = (
        decision.state,
        int(decision.employee_decision_confirmed),
        1,
        json.dumps(context.employee_ids, separators=(",", ":")),
        context.roster_fingerprint,
        source_kind,
        source_id,
        source_revision,
        decision.reference,
    )
    if row:
        current = c.execute(
            "SELECT State,EmployeeDecisionConfirmed,FullDayConfirmed,RosterSnapshot,RosterFingerprint,SourceKind,SourceAssignmentId,SourceRevision,Reference FROM WeekendConsentChanges WHERE ScopeId=? AND Revision=?",
            (row[0], revision),
        ).fetchone()
        if current == values:
            return revision
    scope = (
        row[0]
        if row
        else c.execute(
            "INSERT INTO WeekendConsentScopes(WorkItemId,ProjectId,CrewId,LocalDate,EmployeeId) VALUES(?,?,?,?,?)",
            key,
        ).lastrowid
    )
    c.execute(
        "INSERT INTO WeekendConsentChanges(ScopeId,Revision,State,EmployeeDecisionConfirmed,FullDayConfirmed,RosterSnapshot,RosterFingerprint,SourceKind,SourceAssignmentId,SourceRevision,Reference,RecordedAt) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            scope,
            revision + 1,
            *values,
            datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        ),
    )
    return revision + 1


class WeekendConsentStore:
    def __init__(self, path):
        self.path = path

    def save_planned(self, context, employee_id, decision, expected_revision):
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            return _save(
                c, context, employee_id, decision, expected_revision, "Proposed"
            )

    def save_for_day(
        self,
        assignment_id,
        expected_assignment_revision,
        employee_id,
        decision,
        expected_revision,
    ):
        positive_id(assignment_id)
        positive_id(expected_assignment_revision)
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            day = read_day(c, assignment_id)
            if (
                day["revision"] != expected_assignment_revision
                or day["status"] != "Draft"
            ):
                raise DailyConflict(
                    "Weekend assignment changed; reload actual workers."
                )
            if not day["staffing_configured"] or not day["employee_ids"]:
                raise ValueError("Actual full-day workers must be explicitly recorded.")
            context = WeekendContext(
                day["work_item_id"],
                day["project_id"],
                day["crew_id"],
                day["local_date"],
                day["employee_ids"],
            )
            return _save(
                c,
                context,
                employee_id,
                decision,
                expected_revision,
                "FullDayDraft",
                assignment_id,
                expected_assignment_revision,
            )

    def history(self, context, employee_id):
        if not isinstance(context, WeekendContext):
            raise ValueError("Supply an explicit weekend context.")
        positive_id(employee_id)
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            return c.execute(
                """SELECT h.* FROM WeekendConsentChanges h JOIN WeekendConsentScopes s ON s.Id=h.ScopeId
              WHERE s.WorkItemId=? AND s.ProjectId=? AND s.CrewId=? AND s.LocalDate=? AND s.EmployeeId=?
              ORDER BY h.Revision DESC LIMIT 100""",
                (*context.key, employee_id),
            ).fetchall()


def consent_sources(c, work_item_ids, start, end):
    """Connection-level observations in caller's pinned/budgeted transaction."""
    sources = []
    for work in sorted(work_item_ids):
        revision = c.execute(
            "SELECT coalesce(max(h.Id),0) FROM WeekendConsentChanges h JOIN WeekendConsentScopes s ON s.Id=h.ScopeId WHERE s.WorkItemId=?",
            (work,),
        ).fetchone()[0]
        rows = c.execute(
            """SELECT s.WorkItemId,s.ProjectId,s.CrewId,s.LocalDate,s.EmployeeId,
           h.State,h.Revision,h.Id,h.Reference,h.SourceKind,h.SourceAssignmentId,h.SourceRevision,
           h.RosterSnapshot,h.RosterFingerprint,h.EmployeeDecisionConfirmed,h.FullDayConfirmed
           FROM WeekendConsentScopes s JOIN WeekendConsentChanges h ON h.ScopeId=s.Id
           WHERE s.WorkItemId=? AND s.LocalDate BETWEEN ? AND ?
           AND h.Revision=(SELECT max(Revision) FROM WeekendConsentChanges WHERE ScopeId=s.Id)
           ORDER BY s.ProjectId,s.CrewId,s.LocalDate,s.EmployeeId""",
            (work, start, end),
        ).fetchall()
        for r in rows:
            if r[15] != 1 or r[14] not in (0, 1) or (r[5] != "Pending" and r[14] != 1):
                raise ValueError("Invalid full-day consent provenance.")
            context = WeekendContext(*r[:4], tuple(json.loads(r[12])))
            if hasattr(c, "charge"):
                c.charge(len(context.employee_ids))
            if context.roster_fingerprint != r[13]:
                raise ValueError("Consent roster fingerprint disagrees with history.")
            WeekendConsentFact(
                context, r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]
            )
        sources.append((work, revision, tuple(rows)))
    return tuple(sources)


def snapshot_consent_facts(snapshot):
    return tuple(
        WeekendConsentFact(
            WeekendContext(*r[:4], tuple(json.loads(r[12]))),
            r[4],
            r[5],
            r[6],
            r[7],
            r[8],
            r[9],
            r[10],
            r[11],
        )
        for _, _, rows in json.loads(snapshot.weekend_source_json)
        for r in rows
    )
