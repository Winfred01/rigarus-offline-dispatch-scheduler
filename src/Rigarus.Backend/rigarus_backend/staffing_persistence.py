from .staffing import AssignedWorker, StaffingState


def read_staffing(connection, assignment_id: int) -> StaffingState:
    change = connection.execute(
        "SELECT Id, Configured FROM AssignmentStaffingChanges WHERE AssignmentId=? ORDER BY Id DESC LIMIT 1",
        (assignment_id,),
    ).fetchone()
    if not change:
        return StaffingState()
    rows = connection.execute(
        """SELECT e.Id, e.Name, e.HomeCrewId, e.Active, e.DriverStatus
        FROM AssignmentStaffingMembers m JOIN Employees e ON e.Id=m.EmployeeId
        WHERE m.ChangeId=? ORDER BY e.Id""",
        (change[0],),
    )
    return StaffingState(
        bool(change[1]),
        change[0],
        [AssignedWorker(*r[:3], bool(r[3]), r[4]) for r in rows],
    )


def append_staffing(
    connection, record, ids: tuple[int, ...], *, configured: bool = True
):
    change_id = connection.execute(
        """INSERT INTO AssignmentStaffingChanges
        (AssignmentId, AssignmentRevision, WorkItemId, CrewId, LocalDate, Slot, Configured, RecordedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            record.id,
            record.revision,
            record.work_item_id,
            record.crew_id,
            record.local_date,
            record.slot,
            configured,
            record.updated_at,
        ),
    ).lastrowid
    for employee_id in ids:
        connection.execute(
            """INSERT INTO AssignmentStaffingMembers (ChangeId, EmployeeId, EmployeeName, HomeCrewId)
            SELECT ?, Id, Name, HomeCrewId FROM Employees WHERE Id=?""",
            (change_id, employee_id),
        )
