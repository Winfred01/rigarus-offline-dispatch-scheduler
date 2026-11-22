from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .foremen import ForemanChange, ForemanState, StaleForemanChange
from .roster import CrewNotFound
from .storage import connect


def read_state(connection, crew_id: int) -> ForemanState:
    if (
        connection.execute("SELECT Id FROM Crews WHERE Id = ?", (crew_id,)).fetchone()
        is None
    ):
        raise CrewNotFound("This crew no longer exists. Refresh the roster.")
    history = [
        ForemanChange(*row)
        for row in connection.execute(
            """
            SELECT Id, CrewId, EmployeeId, CrewName, EmployeeName, RecordedAt
            FROM ForemanChanges WHERE CrewId = ? ORDER BY Id DESC
            """,
            (crew_id,),
        )
    ]
    latest = history[0] if history else None
    employee_id = latest.employee_id if latest else None
    employee = connection.execute(
        "SELECT Name, Active, ForemanEligible FROM Employees WHERE Id = ?",
        (employee_id,),
    ).fetchone()
    return ForemanState(
        crew_id,
        latest.id if latest else 0,
        employee_id,
        employee[0] if employee else None,
        bool(employee[1]) if employee else None,
        bool(employee[2]) if employee else None,
        history,
    )


class ForemanStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self, crew_id: int) -> ForemanState:
        with closing(connect(self.path)) as connection, connection:
            # A consistent snapshot includes both the current employee and history.
            connection.execute("BEGIN")
            return read_state(connection, crew_id)

    def save(
        self, crew_id: int, employee_id: int | None, expected_revision: int
    ) -> ForemanState:
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            state = read_state(connection, crew_id)
            if state.revision != expected_revision:
                raise StaleForemanChange(
                    "The Foreman record changed. Reload Foreman before saving again."
                )
            # Saving the same current choice is not a new appointment or history event.
            if state.employee_id == employee_id:
                return state
            employee_name = None
            if employee_id is not None:
                employee = connection.execute(
                    "SELECT Name, Active, ForemanEligible FROM Employees WHERE Id = ?",
                    (employee_id,),
                ).fetchone()
                if employee is None or not employee[1] or not employee[2]:
                    raise ValueError(
                        "Select an active employee marked Foreman eligible."
                    )
                employee_name = employee[0]
            crew_name = connection.execute(
                "SELECT Name FROM Crews WHERE Id = ?", (crew_id,)
            ).fetchone()[0]
            connection.execute(
                """
                INSERT INTO ForemanChanges (CrewId, EmployeeId, CrewName, EmployeeName, RecordedAt)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    crew_id,
                    employee_id,
                    crew_name,
                    employee_name,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            )
            return read_state(connection, crew_id)
