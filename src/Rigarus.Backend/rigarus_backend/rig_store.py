import sqlite3
from contextlib import closing
from pathlib import Path

from .rigs import DuplicateRigNumber, Rig, RigDraft, RigNotFound
from .storage import connect


def read_rig(row) -> Rig:
    rig_id, number, kind, notes, crew_id, active = row
    return Rig(rig_id, number, kind, notes, crew_id, bool(active))


class RigStore:
    def __init__(self, path: Path):
        self.path = path

    def search(self, term: str) -> list[Rig]:
        term = term.strip()
        with closing(connect(self.path)) as connection:
            rows = connection.execute(
                """
                SELECT Id, Number, Type, Notes, DefaultCrewId, Active FROM Rigs
                WHERE instr(lower(Number), lower(?)) > 0
                   OR instr(lower(Type), lower(?)) > 0
                   OR instr(lower(Notes), lower(?)) > 0
                ORDER BY Active DESC, Number COLLATE NOCASE, Id
                """,
                (term, term, term),
            )
            return [read_rig(row) for row in rows]

    def save(self, draft: RigDraft, rig_id: int | None = None) -> Rig:
        values = (
            draft.number,
            draft.type,
            draft.notes,
            draft.default_crew_id,
            draft.active,
        )
        try:
            with closing(connect(self.path)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                if draft.default_crew_id is not None:
                    if (
                        connection.execute(
                            "SELECT Id FROM Crews WHERE Id = ?",
                            (draft.default_crew_id,),
                        ).fetchone()
                        is None
                    ):
                        raise ValueError("Select an existing default crew.")
                if rig_id is None:
                    row = connection.execute(
                        """
                        INSERT INTO Rigs (Number, Type, Notes, DefaultCrewId, Active)
                        VALUES (?, ?, ?, ?, ?)
                        RETURNING Id, Number, Type, Notes, DefaultCrewId, Active
                        """,
                        values,
                    ).fetchone()
                else:
                    row = connection.execute(
                        """
                        UPDATE Rigs SET Number = ?, Type = ?, Notes = ?, DefaultCrewId = ?, Active = ?
                        WHERE Id = ?
                        RETURNING Id, Number, Type, Notes, DefaultCrewId, Active
                        """,
                        (*values, rig_id),
                    ).fetchone()
                if row is None:
                    raise RigNotFound(
                        "This rig no longer exists. Refresh the inventory."
                    )
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
                raise DuplicateRigNumber(
                    "That Rig # already belongs to another rig, including inactive rigs."
                ) from error
            raise
        return read_rig(row)
