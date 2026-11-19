import base64
import binascii
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .import_preview import (
    ExistingProject,
    ImportPreview,
    PreviewError,
    job_key,
    preview_workbook,
)


class WorkbookInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(max_length=7_000_000)


def read_existing_projects(database: Path) -> dict[str, ExistingProject]:
    # Opening SQLite read-only also prevents accidentally creating a missing DB.
    with closing(
        sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    ) as connection:
        connection.execute("BEGIN")
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


def import_preview_router(database: Path) -> APIRouter:
    router = APIRouter(prefix="/import-preview")

    @router.post("")
    def preview(request: WorkbookInput) -> ImportPreview:
        try:
            content = base64.b64decode(request.content, validate=True)
        except (ValueError, binascii.Error) as error:
            raise HTTPException(
                422, "Workbook content could not be decoded."
            ) from error
        try:
            existing = read_existing_projects(database)
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not compare existing projects. Reopen the preview."
            ) from error
        try:
            return preview_workbook(content, existing)
        except PreviewError as error:
            raise HTTPException(422, str(error)) from error
        except Exception as error:
            # Workbook libraries may raise XML-specific errors. Keep source data
            # and workbook paths out of the error response.
            raise HTTPException(
                422, "Could not read this .xlsx workbook. Check the file and try again."
            ) from error

    return router
