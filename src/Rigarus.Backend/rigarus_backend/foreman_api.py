import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .foreman_store import ForemanStore
from .foremen import ForemanState, StaleForemanChange
from .roster import CrewNotFound
from .roster_api import RosterId

SafeId = Annotated[int, Field(strict=True, ge=1, le=9_007_199_254_740_991)]


class ForemanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: SafeId | None
    expected_revision: Annotated[
        int, Field(strict=True, ge=0, le=9_007_199_254_740_991)
    ]


def foreman_router(database_path: Path) -> APIRouter:
    router = APIRouter(prefix="/crews")
    store = ForemanStore(database_path)

    @router.get("/{crew_id}/foreman")
    def read(crew_id: RosterId) -> ForemanState:
        try:
            return store.read(crew_id)
        except CrewNotFound as error:
            raise HTTPException(404, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not load Foreman. Try Reload Foreman."
            ) from error

    @router.put("/{crew_id}/foreman")
    def save(crew_id: RosterId, request: ForemanInput) -> ForemanState:
        try:
            return store.save(crew_id, request.employee_id, request.expected_revision)
        except CrewNotFound as error:
            raise HTTPException(404, str(error)) from error
        except StaleForemanChange as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503,
                "Could not save Foreman. Check disk access, then reload before retrying.",
            ) from error

    return router
