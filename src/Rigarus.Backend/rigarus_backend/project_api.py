import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .project_store import ProjectStore
from .projects import (
    DuplicateJobNumber,
    ProjectDetail,
    ProjectDraft,
    ProjectNotFound,
    ProjectSummary,
    WorkItemDraft,
    WorkType,
)

PositiveInt = Annotated[int, Field(strict=True, ge=1, le=2_147_483_647)]
ProjectId = Annotated[int, Field(ge=1, le=2_147_483_647)]


class WorkItemInput(BaseModel):
    id: PositiveInt | None = None
    type: WorkType
    required_crew_count: PositiveInt
    estimated_half_days: PositiveInt


class ProjectInput(BaseModel):
    job_number: str
    site_id: str
    site_name: str
    work_items: list[WorkItemInput]


def project_router(database_path: Path) -> APIRouter:
    router = APIRouter(prefix="/projects")
    store = ProjectStore(database_path)

    @router.get("")
    def search_projects(term: str = "") -> list[ProjectSummary]:
        try:
            return store.search(term)
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not load projects. Try Search again."
            ) from error

    @router.get("/{project_id}")
    def read_project(project_id: ProjectId) -> ProjectDetail:
        try:
            return store.read(project_id)
        except ProjectNotFound as error:
            raise HTTPException(404, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not open this project. Refresh the backlog."
            ) from error

    def save(request: ProjectInput, project_id: int | None = None) -> ProjectDetail:
        try:
            draft = ProjectDraft(
                request.job_number,
                request.site_id,
                request.site_name,
                [WorkItemDraft(**item.model_dump()) for item in request.work_items],
            )
            return store.save(draft, project_id)
        except ProjectNotFound as error:
            raise HTTPException(404, str(error)) from error
        except DuplicateJobNumber as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not save the project. Check disk access, then try again."
            ) from error

    @router.post("", status_code=201)
    def create_project(request: ProjectInput) -> ProjectDetail:
        return save(request)

    @router.put("/{project_id}")
    def edit_project(project_id: ProjectId, request: ProjectInput) -> ProjectDetail:
        return save(request, project_id)

    return router
