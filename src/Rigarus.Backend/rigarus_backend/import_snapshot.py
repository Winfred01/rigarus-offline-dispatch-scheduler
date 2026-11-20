import sqlite3
from contextlib import closing
from pathlib import Path

from .import_preview import ExistingProject, job_key


def project_snapshot(connection: sqlite3.Connection) -> dict[str, ExistingProject]:
    items: dict[int, list[tuple[str, int, int]]] = {}
    for project, kind, crews, days in connection.execute(
        "SELECT ProjectId, Type, RequiredCrewCount, EstimatedHalfDays FROM WorkItems ORDER BY Id"
    ):
        items.setdefault(project, []).append((kind, crews, days))
    return {
        job_key(job): ExistingProject(id, site_id, name, tuple(items.get(id, [])))
        for id, job, site_id, name in connection.execute(
            "SELECT Id, JobNumber, SiteId, SiteName FROM Projects"
        )
    }


def read_existing_projects(database: Path) -> dict[str, ExistingProject]:
    # Read-only previews must not create or write a database.
    with closing(
        sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    ) as connection:
        connection.execute("BEGIN")
        return project_snapshot(connection)
