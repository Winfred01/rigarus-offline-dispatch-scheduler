from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .availability import (
    AvailabilityConflict,
    AvailabilityDraft,
    EmployeeNotFound,
    range_dates,
)
from .assignments import local_date
from .storage import connect


def employee_revision(connection, employee_id):
    if (
        connection.execute(
            "SELECT Id FROM Employees WHERE Id=?", (employee_id,)
        ).fetchone()
        is None
    ):
        raise EmployeeNotFound("This employee no longer exists. Reload employees.")
    return connection.execute(
        "SELECT coalesce(max(Revision),0) FROM EmployeeAvailabilityChanges WHERE EmployeeId=?",
        (employee_id,),
    ).fetchone()[0]


def snapshot(connection, employee_id, start, end):
    revision = employee_revision(connection, employee_id)
    return {
        "employee_id": employee_id,
        "revision": revision,
        "start_date": start,
        "end_date": end,
        "entries": [
            dict(zip(("local_date", "slot", "state"), row))
            for row in connection.execute(
                "SELECT LocalDate, Slot, State FROM EmployeeAvailability WHERE EmployeeId=? AND LocalDate BETWEEN ? AND ? ORDER BY LocalDate,Slot",
                (employee_id, start, end),
            )
        ],
    }


class AvailabilityStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self, employee_id: int, start: str, end: str):
        range_dates(start, end)
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return snapshot(connection, employee_id, start, end)

    def save(self, employee_id: int, draft: AvailabilityDraft, expected_revision: int):
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("Reload the employee availability revision.")
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            current = snapshot(
                connection, employee_id, draft.start_date, draft.end_date
            )
            if current["revision"] != expected_revision:
                raise AvailabilityConflict(
                    "Availability changed. Reload before saving again."
                )
            states = {
                (e["local_date"], e["slot"]): e["state"] for e in current["entries"]
            }
            cells = draft.cells()
            if all(states.get(cell, "Unknown") == draft.state for cell in cells):
                return current
            revision = current["revision"] + 1
            change_id = connection.execute(
                """INSERT INTO EmployeeAvailabilityChanges
                (EmployeeId,Revision,StartDate,EndDate,Slot,State,RecordedAt)
                VALUES (?,?,?,?,?,?,?)""",
                (
                    employee_id,
                    revision,
                    draft.start_date,
                    draft.end_date,
                    draft.slot,
                    draft.state,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            ).lastrowid
            for day, slot in cells:
                if draft.state == "Unknown":
                    connection.execute(
                        "DELETE FROM EmployeeAvailability WHERE EmployeeId=? AND LocalDate=? AND Slot=?",
                        (employee_id, day, slot),
                    )
                else:
                    connection.execute(
                        """INSERT INTO EmployeeAvailability(EmployeeId,LocalDate,Slot,State,ChangeId)
                        VALUES (?,?,?,?,?) ON CONFLICT(EmployeeId,LocalDate,Slot)
                        DO UPDATE SET State=excluded.State,ChangeId=excluded.ChangeId""",
                        (employee_id, day, slot, draft.state, change_id),
                    )
            return snapshot(connection, employee_id, draft.start_date, draft.end_date)

    def on_slot(self, day: str, slot: str):
        local_date(day)
        if slot not in ("AM", "PM"):
            raise ValueError("Choose AM or PM.")
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return {
                "local_date": day,
                "slot": slot,
                "employees": [
                    dict(zip(("employee_id", "state"), row))
                    for row in connection.execute(
                        """SELECT e.Id, coalesce(a.State,'Unknown') FROM Employees e
                LEFT JOIN EmployeeAvailability a ON a.EmployeeId=e.Id AND a.LocalDate=? AND a.Slot=? ORDER BY e.Id""",
                        (day, slot),
                    )
                ],
            }

    def history(self, employee_id: int):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            employee_revision(connection, employee_id)
            return [
                dict(
                    zip(
                        (
                            "id",
                            "revision",
                            "start_date",
                            "end_date",
                            "slot",
                            "state",
                            "recorded_at",
                        ),
                        row,
                    )
                )
                for row in connection.execute(
                    "SELECT Id,Revision,StartDate,EndDate,Slot,State,RecordedAt FROM EmployeeAvailabilityChanges WHERE EmployeeId=? ORDER BY Revision DESC LIMIT 100",
                    (employee_id,),
                )
            ]
