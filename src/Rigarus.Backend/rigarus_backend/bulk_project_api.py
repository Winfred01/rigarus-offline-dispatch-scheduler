import base64
import sqlite3
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .bulk_project_store import BulkProjectStore, StaleBulkPreview
from .bulk_projects import PreviewError, project_template


class BulkInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["text", "xlsx"]
    content: str = Field(max_length=7_000_000)


class BulkConfirmation(BulkInput):
    preview_id: str = Field(pattern=r"^[0-9a-f]{64}$")


def bulk_project_router(database: Path) -> APIRouter:
    router = APIRouter(prefix="/bulk-projects")
    store = BulkProjectStore(database)

    @router.get("/template")
    def template():
        return {"content": base64.b64encode(project_template()).decode("ascii")}

    def perform(request, *, confirm=False):
        try:
            if confirm:
                return store.confirm(request.kind, request.content, request.preview_id)
            return store.preview(request.kind, request.content)
        except StaleBulkPreview as error:
            raise HTTPException(409, str(error)) from error
        except PreviewError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503,
                "Could not complete Bulk Add. No projects from this attempt were saved. Check disk access and preview again.",
            ) from error

    @router.post("/preview")
    def preview(request: BulkInput):
        return perform(request)

    @router.post("/confirm")
    def confirm(request: BulkConfirmation):
        return perform(request, confirm=True)

    return router
