"""Internal explicit evidence recorder; not an approval authority or HTTP route."""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .availability import EmployeeNotFound, range_dates
from .driver_eligibility import DriverApprovalDraft
from .recommendation_comparison import _positive_id
from .storage import connect


class DriverApprovalConflict(ValueError):
    pass


def snapshot(connection, employee_id, start, end):
    _positive_id(employee_id)
    range_dates(start, end)
    if (
        connection.execute(
            "SELECT 1 FROM Employees WHERE Id=?", (employee_id,)
        ).fetchone()
        is None
    ):
        raise EmployeeNotFound("This employee no longer exists.")
    revision = connection.execute(
        "SELECT coalesce(max(Revision),0) FROM DriverApprovalChanges WHERE EmployeeId=?",
        (employee_id,),
    ).fetchone()[0]
    entries = []
    for row in connection.execute(
        """SELECT c.LocalDate,c.Slot,c.State,c.ChangeId,h.StartDate,h.EndDate,h.Slot,h.CompanyConfirmed
        FROM DriverApprovalCells c JOIN DriverApprovalChanges h ON h.Id=c.ChangeId
        WHERE c.EmployeeId=? AND c.LocalDate BETWEEN ? AND ?
        ORDER BY c.LocalDate,c.Slot""",
        (employee_id, start, end),
    ):
        if not row[4] <= row[0] <= row[5] or row[6] not in (row[1], "FullDay"):
            raise ValueError("Invalid dated driver evidence context.")
        entry = dict(zip(("local_date", "slot", "state", "change_id"), row[:4]))
        entry["company_confirmed"] = row[7] == 1
        entries.append(entry)
    return dict(
        employee_id=employee_id,
        revision=revision,
        start_date=start,
        end_date=end,
        entries=entries,
    )


class DriverApprovalStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self, employee_id, start, end):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return snapshot(connection, employee_id, start, end)

    def save(self, employee_id, draft: DriverApprovalDraft, expected_revision):
        if not isinstance(draft, DriverApprovalDraft):
            raise ValueError("Supply explicitly confirmed driver evidence.")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("Reload the driver evidence revision.")
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            current = snapshot(
                connection, employee_id, draft.start_date, draft.end_date
            )
            if current["revision"] != expected_revision:
                raise DriverApprovalConflict(
                    "Driver evidence changed. Reload before saving."
                )
            existing = {
                (row[0], row[1]): (row[2], row[3])
                for row in connection.execute(
                    """SELECT c.LocalDate,c.Slot,c.State,h.Reference FROM DriverApprovalCells c
                    JOIN DriverApprovalChanges h ON h.Id=c.ChangeId
                    WHERE c.EmployeeId=? AND c.LocalDate BETWEEN ? AND ?""",
                    (employee_id, draft.start_date, draft.end_date),
                )
            }
            if all(
                existing.get(cell) == (draft.state, draft.reference)
                for cell in draft.cells()
            ):
                return current
            change_id = connection.execute(
                """INSERT INTO DriverApprovalChanges
                (EmployeeId,Revision,StartDate,EndDate,Slot,State,CompanyConfirmed,Reference,RecordedAt)
                VALUES (?,?,?,?,?,?,1,?,?)""",
                (
                    employee_id,
                    current["revision"] + 1,
                    draft.start_date,
                    draft.end_date,
                    draft.slot,
                    draft.state,
                    draft.reference,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            ).lastrowid
            for day, half in draft.cells():
                connection.execute(
                    """INSERT INTO DriverApprovalCells VALUES (?,?,?,?,?)
                    ON CONFLICT(EmployeeId,LocalDate,Slot) DO UPDATE
                    SET State=excluded.State,ChangeId=excluded.ChangeId""",
                    (employee_id, day, half, draft.state, change_id),
                )
            return snapshot(connection, employee_id, draft.start_date, draft.end_date)

    def history(self, employee_id):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            snapshot(connection, employee_id, "0001-01-01", "0001-01-01")
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
                            "company_confirmed",
                            "reference",
                            "recorded_at",
                        ),
                        row,
                    )
                )
                for row in connection.execute(
                    """SELECT Id,Revision,StartDate,EndDate,Slot,State,CompanyConfirmed,Reference,RecordedAt
                    FROM DriverApprovalChanges WHERE EmployeeId=? ORDER BY Revision DESC LIMIT 100""",
                    (employee_id,),
                )
            ]
