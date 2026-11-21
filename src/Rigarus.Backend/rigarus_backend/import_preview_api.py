import base64
import binascii
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .import_preview import (
    ImportPreview,
    PreviewError,
    preview_workbook,
)
from .import_snapshot import read_existing_projects


class WorkbookInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(max_length=7_000_000)


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
