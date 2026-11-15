from contextlib import closing
from pathlib import Path

from .roster import Crew, CrewDraft, CrewNotFound
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
