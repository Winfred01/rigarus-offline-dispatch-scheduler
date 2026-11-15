import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .roster import (
    Crew,
    CrewDraft,
    CrewNotFound,
    CrewType,
    Employee,
    EmployeeDraft,
    EmployeeNotFound,
)
from .roster_store import CrewStore, EmployeeStore

RosterId = Annotated[int, Field(ge=1, le=9_007_199_254_740_991)]


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
    def update(crew_id: RosterId, request: CrewInput) -> Crew:
        return save(request, crew_id)

    return router


class EmployeeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    home_crew_id: Annotated[int, Field(strict=True, ge=1, le=9_007_199_254_740_991)]
    skill_level: Annotated[int, Field(strict=True)]
    foreman_eligible: StrictBool = False
    active: StrictBool = True


def employee_router(database_path: Path) -> APIRouter:
    router = APIRouter(prefix="/employees")
    store = EmployeeStore(database_path)

    @router.get("")
    def search(term: str = "") -> list[Employee]:
        try:
            return store.search(term)
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not load employees. Try Search again."
            ) from error

    def save(request: EmployeeInput, employee_id: int | None = None) -> Employee:
        try:
            return store.save(EmployeeDraft(**request.model_dump()), employee_id)
        except EmployeeNotFound as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not save the employee. Check disk access, then try again."
            ) from error

    @router.post("", status_code=201)
    def create(request: EmployeeInput) -> Employee:
        return save(request)

    @router.put("/{employee_id}")
    def update(employee_id: RosterId, request: EmployeeInput) -> Employee:
        return save(request, employee_id)

    return router
