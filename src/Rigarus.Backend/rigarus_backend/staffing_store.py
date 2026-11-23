from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .assignment_store import read_assignment
from .assignments import AssignmentConflict, check_revision
from .staffing import worker_ids
from .staffing_persistence import append_staffing
from .storage import connect


class StaffingStore:
    def __init__(self, path: Path):
        self.path = path

    def save(self, assignment_id: int, employee_ids: list[int], expected_revision: int):
        ids = worker_ids(employee_ids)
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            record = read_assignment(connection, assignment_id)
            check_revision(record, expected_revision)
            if record.status != "Draft":
                raise AssignmentConflict(
                    "This assignment is cancelled. Reload assignments."
                )
            for employee_id in ids:
                if (
                    connection.execute(
                        "SELECT Id FROM Employees WHERE Id=?", (employee_id,)
                    ).fetchone()
                    is None
                ):
                    raise ValueError("Select an existing employee. Reload the roster.")
            if (
                record.staffing.configured
                and tuple(w.employee_id for w in record.staffing.workers) == ids
            ):
                return record
            connection.execute(
                "UPDATE DraftAssignments SET Revision=Revision+1, UpdatedAt=? WHERE Id=?",
                (
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                    assignment_id,
                ),
            )
            append_staffing(connection, read_assignment(connection, assignment_id), ids)
            return read_assignment(connection, assignment_id)

    def history(self, assignment_id: int):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            read_assignment(connection, assignment_id)
            changes = connection.execute(
                """SELECT Id, AssignmentRevision, WorkItemId, CrewId, LocalDate, Slot, Configured, RecordedAt
                FROM AssignmentStaffingChanges WHERE AssignmentId=? ORDER BY Id DESC""",
                (assignment_id,),
            ).fetchall()
            return [
                dict(
                    zip(
                        (
                            "id",
                            "assignment_revision",
                            "work_item_id",
                            "crew_id",
                            "local_date",
                            "slot",
                            "configured",
                            "recorded_at",
                        ),
                        row,
                    ),
                    configured=bool(row[6]),
                    members=[
                        dict(
                            zip(
                                (
                                    "employee_id",
                                    "recorded_name",
                                    "recorded_home_crew_id",
                                ),
                                member,
                            )
                        )
                        for member in connection.execute(
                            "SELECT EmployeeId, EmployeeName, HomeCrewId FROM AssignmentStaffingMembers WHERE ChangeId=? ORDER BY EmployeeId",
                            (row[0],),
                        )
                    ],
                )
                for row in changes
            ]
