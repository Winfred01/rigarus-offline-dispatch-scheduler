from contextlib import closing
from pathlib import Path

from .roster import (
    Crew,
    CrewDraft,
    CrewNotFound,
    Employee,
    EmployeeDraft,
    EmployeeNotFound,
)
from .storage import connect


class CrewStore:
    def __init__(self, path: Path):
        self.path = path

    def search(self, term: str) -> list[Crew]:
        with closing(connect(self.path)) as connection:
            rows = connection.execute(
                """
                SELECT Id, Name, Type, Active FROM Crews
                WHERE instr(lower(Name), lower(?)) > 0 OR ? = ''
                ORDER BY Active DESC, Name COLLATE NOCASE, Id
                """,
                (term.strip(), term.strip()),
            )
            return [
                Crew(id, name, kind, bool(active)) for id, name, kind, active in rows
            ]

    def save(self, draft: CrewDraft, crew_id: int | None = None) -> Crew:
        values = (draft.name, draft.type, draft.active)
        with closing(connect(self.path)) as connection, connection:
            if crew_id is None:
                cursor = connection.execute(
                    "INSERT INTO Crews (Name, Type, Active) VALUES (?, ?, ?)", values
                )
                crew_id = cursor.lastrowid
            else:
                result = connection.execute(
                    "UPDATE Crews SET Name = ?, Type = ?, Active = ? WHERE Id = ?",
                    (*values, crew_id),
                )
                if result.rowcount != 1:
                    raise CrewNotFound(
                        "This crew no longer exists. Refresh the roster."
                    )
        return Crew(crew_id, *values)


def read_employee(row) -> Employee:
    employee_id, name, crew_id, level, eligible, active, driver = row
    return Employee(
        employee_id, name, crew_id, level, bool(eligible), bool(active), driver
    )


class EmployeeStore:
    def __init__(self, path: Path):
        self.path = path

    def search(self, term: str) -> list[Employee]:
        term = term.strip()
        with closing(connect(self.path)) as connection:
            rows = connection.execute(
                """
                SELECT Id, Name, HomeCrewId, SkillLevel, ForemanEligible, Active, DriverStatus
                FROM Employees
                WHERE instr(lower(Name), lower(?)) > 0 OR ? = ''
                ORDER BY Active DESC, Name COLLATE NOCASE, Id
                """,
                (term, term),
            )
            return [read_employee(row) for row in rows]

    def save(self, draft: EmployeeDraft, employee_id: int | None = None) -> Employee:
        values = (
            draft.name,
            draft.home_crew_id,
            draft.skill_level,
            draft.foreman_eligible,
            draft.active,
        )
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if (
                connection.execute(
                    "SELECT Id FROM Crews WHERE Id = ?", (draft.home_crew_id,)
                ).fetchone()
                is None
            ):
                raise ValueError("Select an existing home crew.")
            if employee_id is None:
                row = connection.execute(
                    """
                    INSERT INTO Employees (Name, HomeCrewId, SkillLevel, ForemanEligible, Active)
                    VALUES (?, ?, ?, ?, ?)
                    RETURNING Id, Name, HomeCrewId, SkillLevel, ForemanEligible, Active, DriverStatus
                    """,
                    values,
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    UPDATE Employees SET Name = ?, HomeCrewId = ?, SkillLevel = ?, ForemanEligible = ?, Active = ?
                    WHERE Id = ?
                    RETURNING Id, Name, HomeCrewId, SkillLevel, ForemanEligible, Active, DriverStatus
                    """,
                    (*values, employee_id),
                ).fetchone()
            if row is None:
                raise EmployeeNotFound(
                    "This employee no longer exists. Refresh the roster."
                )
        return read_employee(row)
