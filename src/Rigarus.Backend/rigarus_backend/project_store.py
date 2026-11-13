import sqlite3
from contextlib import closing
from pathlib import Path

from .projects import (
    DuplicateJobNumber,
    ProjectDetail,
    ProjectDraft,
    ProjectNotFound,
    ProjectSummary,
    WorkItemDraft,
    WorkType,
)
from .storage import connect


class ProjectStore:
    def __init__(self, path: Path):
        self.path = path

    def search(self, term: str) -> list[ProjectSummary]:
        literal = (
            term.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        pattern = f"%{literal}%"
        with closing(connect(self.path)) as connection:
            return [
                ProjectSummary(*row)
                for row in connection.execute(
                    r"""
                    SELECT p.Id, p.JobNumber, p.SiteId, p.SiteName,
                           (SELECT count(*) FROM WorkItems w WHERE w.ProjectId = p.Id)
                    FROM Projects p
                    WHERE p.JobNumber LIKE ? ESCAPE '\' OR p.SiteId LIKE ? ESCAPE '\'
                          OR p.SiteName LIKE ? ESCAPE '\'
                    ORDER BY p.JobNumber
                    """,
                    (pattern, pattern, pattern),
                )
            ]

    def read(self, project_id: int) -> ProjectDetail:
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return read_project(connection, project_id)

    def save(self, draft: ProjectDraft, project_id: int | None = None) -> ProjectDetail:
        details = (draft.job_number, draft.site_id, draft.site_name)
        try:
            with closing(connect(self.path)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                if project_id is None:
                    project_id = connection.execute(
                        "INSERT INTO Projects (JobNumber, SiteId, SiteName) VALUES (?, ?, ?)",
                        details,
                    ).lastrowid
                elif not connection.execute(
                    "UPDATE Projects SET JobNumber = ?, SiteId = ?, SiteName = ? WHERE Id = ?",
                    (*details, project_id),
                ).rowcount:
                    raise ProjectNotFound(
                        "This project could not be found. Refresh the backlog."
                    )

                existing = {
                    row[0]
                    for row in connection.execute(
                        "SELECT Id FROM WorkItems WHERE ProjectId = ?", (project_id,)
                    )
                }
                for item in draft.work_items:
                    requirements = (
                        item.type,
                        item.required_crew_count,
                        item.estimated_half_days,
                    )
                    if item.id is None:
                        connection.execute(
                            """
                            INSERT INTO WorkItems (ProjectId, Type, RequiredCrewCount, EstimatedHalfDays)
                            VALUES (?, ?, ?, ?)
                            """,
                            (project_id, *requirements),
                        )
                    elif item.id in existing:
                        existing.remove(item.id)
                        connection.execute(
                            """
                            UPDATE WorkItems SET Type = ?, RequiredCrewCount = ?, EstimatedHalfDays = ?
                            WHERE Id = ? AND ProjectId = ?
                            """,
                            (*requirements, item.id, project_id),
                        )
                    else:
                        raise ValueError(
                            "A work item is repeated or does not belong to this project."
                        )
                return read_project(connection, project_id)
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                raise DuplicateJobNumber(
                    "That Job # already belongs to another project."
                ) from error
            raise


def read_project(connection: sqlite3.Connection, project_id: int) -> ProjectDetail:
    details = connection.execute(
        "SELECT Id, JobNumber, SiteId, SiteName FROM Projects WHERE Id = ?",
        (project_id,),
    ).fetchone()
    if details is None:
        raise ProjectNotFound("This project could not be found. Refresh the backlog.")
    work_items = [
        WorkItemDraft(item_id, WorkType(kind), crews, half_days)
        for item_id, kind, crews, half_days in connection.execute(
            """
            SELECT Id, Type, RequiredCrewCount, EstimatedHalfDays
            FROM WorkItems WHERE ProjectId = ? ORDER BY Id
            """,
            (project_id,),
        )
    ]
    return ProjectDetail(*details, work_items)
