"""Full-day planning persistence; independent ID namespace, no dispatch approval."""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .assignments import AssignmentConflict, AssignmentNotFound
from .day_drafts import DayDraft, positive_id
from .storage import connect


def read_day(connection, assignment_id):
    positive_id(assignment_id)
    row = connection.execute(
        """SELECT a.Id,a.WorkItemId,a.CrewId,a.LocalDate,a.Notes,a.Status,a.Revision,
                  a.CreatedAt,a.UpdatedAt,w.ProjectId,c.Active
           FROM DayDraftAssignments a JOIN WorkItems w ON w.Id=a.WorkItemId
           JOIN Crews c ON c.Id=a.CrewId WHERE a.Id=?""",
        (assignment_id,),
    ).fetchone()
    if not row:
        raise AssignmentNotFound(
            "This Full-Day Draft no longer exists. Reload day drafts."
        )
    result = dict(
        zip(
            (
                "id",
                "work_item_id",
                "crew_id",
                "local_date",
                "notes",
                "status",
                "revision",
                "created_at",
                "updated_at",
                "project_id",
                "crew_active",
            ),
            row,
        )
    )
    change = connection.execute(
        "SELECT Id,StaffingConfigured,WorkItemId,CrewId,LocalDate,Notes,Status FROM DayDraftChanges WHERE AssignmentId=? AND Revision=?",
        (assignment_id, result["revision"]),
    ).fetchone()
    if not change:
        raise ValueError("Full-Day Draft history is incomplete. Needs Review.")
    if change[2:] != (
        result["work_item_id"],
        result["crew_id"],
        result["local_date"],
        result["notes"],
        result["status"],
    ):
        raise ValueError("Full-Day Draft and recorded history disagree. Needs Review.")
    employees = tuple(
        r[0]
        for r in connection.execute(
            "SELECT EmployeeId FROM DayDraftMembers WHERE ChangeId=? ORDER BY EmployeeId",
            (change[0],),
        )
    )
    result.update(
        record_kind="FullDayDraft",
        scheduling_unit="FullDay",
        employee_ids=employees if change[1] else None,
        staffing_configured=bool(change[1]),
        validation_status="Pending",
        applyable=False,
        publishable=False,
        missing_evidence=(
            "DailyCalendars",
            "EmployeeAvailability",
            "PersonnelConflicts",
            "ApprovedDriver",
            "MinimumStaffing",
            "Skills",
            "Qualifications",
            "ActualRigAndMaintenance",
            "ActualWorkerWeekendConsent",
        ),
    )
    return result


def append_change(connection, assignment_id, employee_ids):
    row = connection.execute(
        "SELECT Revision,WorkItemId,CrewId,LocalDate,Notes,Status,UpdatedAt FROM DayDraftAssignments WHERE Id=?",
        (assignment_id,),
    ).fetchone()
    change_id = connection.execute(
        """INSERT INTO DayDraftChanges(AssignmentId,Revision,WorkItemId,CrewId,LocalDate,Notes,Status,StaffingConfigured,RecordedAt)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (assignment_id, *row[:-1], int(employee_ids is not None), row[-1]),
    ).lastrowid
    for employee_id in employee_ids or ():
        worker = connection.execute(
            "SELECT Id,Name,HomeCrewId FROM Employees WHERE Id=?", (employee_id,)
        ).fetchone()
        if not worker:
            raise ValueError(
                "Select existing Employee IDs; Home Crew does not imply attendance."
            )
        connection.execute(
            "INSERT INTO DayDraftMembers VALUES(?,?,?,?)", (change_id, *worker)
        )


class DayDraftStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self, assignment_id):
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN")
            return read_day(c, assignment_id)

    def list(self, start_date, end_date, include_cancelled=False):
        from .availability import range_dates

        range_dates(start_date, end_date)
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN")
            ids = c.execute(
                "SELECT Id FROM DayDraftAssignments WHERE LocalDate BETWEEN ? AND ? AND (? OR Status='Draft') ORDER BY LocalDate,CrewId,Id",
                (start_date, end_date, include_cancelled),
            ).fetchmany(10001)
            if len(ids) > 10000:
                raise ValueError(
                    "Day Draft read limit exceeded; reduce the date range."
                )
            return [read_day(c, i[0]) for i in ids]

    def save(self, draft: DayDraft, assignment_id=None, expected_revision=None):
        if not isinstance(draft, DayDraft):
            raise ValueError("Supply a slotless Full-Day Draft.")
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            old = None
            if assignment_id is not None:
                old = read_day(c, assignment_id)
                self._revision(old, expected_revision)
                if old["status"] != "Draft":
                    raise AssignmentConflict(
                        "This Full-Day Draft is cancelled. Create a new visit."
                    )
            for table, identity in (
                ("WorkItems", draft.work_item_id),
                ("Crews", draft.crew_id),
            ):
                if not c.execute(
                    f"SELECT 1 FROM {table} WHERE Id=?", (identity,)
                ).fetchone():
                    raise ValueError("Select an existing WorkItem and Crew.")
            legacy = c.execute(
                "SELECT Id,Slot FROM DraftAssignments WHERE CrewId=? AND LocalDate=? AND Status='Draft' ORDER BY Id",
                (draft.crew_id, draft.local_date),
            ).fetchall()
            if legacy:
                details = ", ".join(f"Legacy #{i} {slot}" for i, slot in legacy)
                raise AssignmentConflict(
                    f"Crew #{draft.crew_id} is occupied on {draft.local_date}: {details}. Conversion Required; review or explicitly cancel legacy visits. No automatic merge."
                )
            daily = c.execute(
                "SELECT Id FROM DayDraftAssignments WHERE CrewId=? AND LocalDate=? AND Status='Draft' AND (? IS NULL OR Id<>?)",
                (draft.crew_id, draft.local_date, assignment_id, assignment_id),
            ).fetchone()
            if daily:
                raise AssignmentConflict(
                    f"Crew #{draft.crew_id} already has Full-Day Draft #{daily[0]} on {draft.local_date}. Choose another Crew or date."
                )
            if old and (
                old["work_item_id"],
                old["crew_id"],
                old["local_date"],
                old["notes"],
                old["employee_ids"],
            ) == (
                draft.work_item_id,
                draft.crew_id,
                draft.local_date,
                draft.notes,
                draft.employee_ids,
            ):
                return old
            now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            values = (draft.work_item_id, draft.crew_id, draft.local_date, draft.notes)
            if old:
                c.execute(
                    "UPDATE DayDraftAssignments SET WorkItemId=?,CrewId=?,LocalDate=?,Notes=?,Revision=Revision+1,UpdatedAt=? WHERE Id=?",
                    (*values, now, assignment_id),
                )
            else:
                assignment_id = c.execute(
                    "INSERT INTO DayDraftAssignments(WorkItemId,CrewId,LocalDate,Notes,Status,Revision,CreatedAt,UpdatedAt) VALUES(?,?,?,?,'Draft',1,?,?)",
                    (*values, now, now),
                ).lastrowid
            append_change(c, assignment_id, draft.employee_ids)
            return read_day(c, assignment_id)

    def cancel(self, assignment_id, expected_revision):
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            old = read_day(c, assignment_id)
            self._revision(old, expected_revision)
            if old["status"] == "Draft":
                c.execute(
                    "UPDATE DayDraftAssignments SET Status='Cancelled',Revision=Revision+1,UpdatedAt=? WHERE Id=?",
                    (
                        datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                        assignment_id,
                    ),
                )
                append_change(c, assignment_id, old["employee_ids"])
            return read_day(c, assignment_id)

    def history(self, assignment_id):
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN")
            read_day(c, assignment_id)
            rows = c.execute(
                "SELECT Id,Revision,WorkItemId,CrewId,LocalDate,Notes,Status,StaffingConfigured,RecordedAt FROM DayDraftChanges WHERE AssignmentId=? ORDER BY Revision DESC LIMIT 100",
                (assignment_id,),
            ).fetchall()
            return [
                dict(
                    zip(
                        (
                            "change_id",
                            "revision",
                            "work_item_id",
                            "crew_id",
                            "local_date",
                            "notes",
                            "status",
                            "staffing_configured",
                            "recorded_at",
                        ),
                        r,
                    ),
                    workers=c.execute(
                        "SELECT EmployeeId,EmployeeName,HomeCrewId FROM DayDraftMembers WHERE ChangeId=? ORDER BY EmployeeId",
                        (r[0],),
                    ).fetchall(),
                )
                for r in rows
            ]

    @staticmethod
    def _revision(old, expected):
        positive_id(expected)
        if old["revision"] != expected:
            raise AssignmentConflict(
                "This Full-Day Draft changed. Reload before saving."
            )
