import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StrictBool

from .roster import Crew, CrewDraft, CrewNotFound, CrewType
from .roster_store import CrewStore

CrewId = Annotated[int, Field(ge=1, le=9_007_199_254_740_991)]


class CrewInput(BaseModel):
    name: str
    type: CrewType
    active: StrictBool = True


def crew_router(database_path: Path) -> APIRouter:
    router = APIRouter(prefix="/crews")
    store = CrewStore(database_path)

    @router.get("")
    def search(term: str = "") -> list[Crew]:
        try:
            return store.search(term)
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not load crews. Try Search again."
            ) from error

    def save(request: CrewInput, crew_id: int | None = None) -> Crew:
        try:
            return store.save(CrewDraft(**request.model_dump()), crew_id)
        except CrewNotFound as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not save the crew. Check disk access, then try again."
            ) from error

    @router.post("", status_code=201)
    def create(request: CrewInput) -> Crew:
        return save(request)

    @router.put("/{crew_id}")
    def update(crew_id: CrewId, request: CrewInput) -> Crew:
        return save(request, crew_id)

    return router
