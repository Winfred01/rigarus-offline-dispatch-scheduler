from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .assignments import (
    AssignmentConflict,
    AssignmentDraft,
    AssignmentNotFound,
    DraftAssignment,
    local_date,
    check_revision,
)
from .storage import connect
from .staffing_persistence import read_staffing, append_staffing

SELECT_ASSIGNMENTS = """
    SELECT a.Id, a.WorkItemId, a.CrewId, a.LocalDate, a.Slot, a.Notes,
           a.Status, a.Revision, a.CreatedAt, a.UpdatedAt, p.Id, p.JobNumber,
           p.SiteId, p.SiteName, w.Type, w.RequiredCrewCount, w.EstimatedHalfDays,
           c.Name, c.Active
    FROM DraftAssignments a
    JOIN WorkItems w ON w.Id = a.WorkItemId
    JOIN Projects p ON p.Id = w.ProjectId
    JOIN Crews c ON c.Id = a.CrewId
"""


def read_assignment(connection, assignment_id: int) -> DraftAssignment:
    row = connection.execute(
        SELECT_ASSIGNMENTS + " WHERE a.Id = ?", (assignment_id,)
    ).fetchone()
    if row is None:
        raise AssignmentNotFound(
            "This draft assignment no longer exists. Reload assignments."
        )
    return DraftAssignment(
        *row[:-1], bool(row[-1]), staffing=read_staffing(connection, assignment_id)
    )


class AssignmentStore:
    def __init__(self, path: Path):
        self.path = path

    def list(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        crew_id: int | None = None,
        include_cancelled: bool = False,
        employee_id: int | None = None,
    ) -> list[DraftAssignment]:
        for value in (start_date, end_date):
            if value is not None:
                local_date(value)
        if start_date and end_date and start_date > end_date:
            raise ValueError("The end date must be on or after the start date.")
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            rows = connection.execute(
                SELECT_ASSIGNMENTS
                + """
                WHERE (? IS NULL OR a.LocalDate >= ?) AND (? IS NULL OR a.LocalDate <= ?)
                  AND (? IS NULL OR a.CrewId = ?) AND (? OR a.Status = 'Draft')
                  AND (? IS NULL OR EXISTS (
                      SELECT 1 FROM AssignmentStaffingMembers m JOIN AssignmentStaffingChanges s ON s.Id=m.ChangeId
                      WHERE s.AssignmentId=a.Id AND m.EmployeeId=? AND s.Configured=1
                        AND s.Id=(SELECT max(Id) FROM AssignmentStaffingChanges WHERE AssignmentId=a.Id)))
                ORDER BY a.LocalDate, a.Slot, a.CrewId, a.Id
                """,
                (
                    start_date,
                    start_date,
                    end_date,
                    end_date,
                    crew_id,
                    crew_id,
                    include_cancelled,
                    employee_id,
                    employee_id,
                ),
            )
            return [
                DraftAssignment(
                    *row[:-1], bool(row[-1]), staffing=read_staffing(connection, row[0])
                )
                for row in rows
            ]

    def read(self, assignment_id: int) -> DraftAssignment:
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return read_assignment(connection, assignment_id)

    def save(
        self,
        draft: AssignmentDraft,
        assignment_id: int | None = None,
        expected_revision: int | None = None,
    ) -> DraftAssignment:
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if assignment_id is not None:
                record = read_assignment(connection, assignment_id)
                check_revision(record, expected_revision)
                if record.status != "Draft":
                    raise AssignmentConflict(
                        "This assignment is cancelled. Create a new draft visit."
                    )
            for table, record_id, label in (
                ("WorkItems", draft.work_item_id, "work item"),
                ("Crews", draft.crew_id, "Crew"),
            ):
                if (
                    connection.execute(
                        f"SELECT Id FROM {table} WHERE Id = ?", (record_id,)
                    ).fetchone()
                    is None
                ):
                    raise ValueError(f"Select an existing {label}.")
            conflict = connection.execute(
                """SELECT Id FROM DraftAssignments
                WHERE CrewId = ? AND LocalDate = ? AND Slot = ? AND Status = 'Draft'
                  AND (? IS NULL OR Id <> ?)""",
                (
                    draft.crew_id,
                    draft.local_date,
                    draft.slot,
                    assignment_id,
                    assignment_id,
                ),
            ).fetchone()
            if conflict:
                raise AssignmentConflict(
                    f"Crew #{draft.crew_id} already has Draft Assignment #{conflict[0]} on {draft.local_date} {draft.slot}. Choose another Crew or half-day."
                )
            now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            values = (
                draft.work_item_id,
                draft.crew_id,
                draft.local_date,
                draft.slot,
                draft.notes,
            )
            if assignment_id is None:
                assignment_id = connection.execute(
                    """INSERT INTO DraftAssignments
                    (WorkItemId, CrewId, LocalDate, Slot, Notes, Status, Revision, CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, 'Draft', 1, ?, ?)""",
                    (*values, now, now),
                ).lastrowid
            else:
                connection.execute(
                    """UPDATE DraftAssignments SET WorkItemId=?, CrewId=?, LocalDate=?, Slot=?, Notes=?,
                    Revision=Revision+1, UpdatedAt=? WHERE Id=?""",
                    (*values, now, assignment_id),
                )
                if record.staffing.change_id and (
                    record.work_item_id,
                    record.crew_id,
                    record.local_date,
                    record.slot,
                ) != (draft.work_item_id, draft.crew_id, draft.local_date, draft.slot):
                    append_staffing(
                        connection,
                        read_assignment(connection, assignment_id),
                        (),
                        configured=False,
                    )
            return read_assignment(connection, assignment_id)

    def cancel(self, assignment_id: int, expected_revision: int) -> DraftAssignment:
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            record = read_assignment(connection, assignment_id)
            check_revision(record, expected_revision)
            if record.status == "Draft":
                connection.execute(
                    "UPDATE DraftAssignments SET Status='Cancelled', Revision=Revision+1, UpdatedAt=? WHERE Id=?",
                    (
                        datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                        assignment_id,
                    ),
                )
            return read_assignment(connection, assignment_id)
