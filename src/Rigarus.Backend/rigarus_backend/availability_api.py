import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .availability import (
    AvailabilityConflict,
    AvailabilityDraft,
    AvailabilitySlot,
    AvailabilityState,
    EmployeeNotFound,
)
from .availability_store import AvailabilityStore
from .roster_api import RosterId


class AvailabilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: str
    end_date: str
    slot: AvailabilitySlot
    state: AvailabilityState
    expected_revision: Annotated[
        int, Field(strict=True, ge=0, le=9_007_199_254_740_991)
    ]


def availability_router(path: Path):
    router = APIRouter()
    store = AvailabilityStore(path)

    def execute(operation):
        try:
            return operation()
        except EmployeeNotFound as error:
            raise HTTPException(404, str(error)) from error
        except AvailabilityConflict as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503,
                "Could not access recorded availability. Check disk access, then reload before retrying.",
            ) from error

    @router.get("/employees/{employee_id}/availability")
    def read(employee_id: RosterId, start_date: str, end_date: str):
        return execute(lambda: store.read(employee_id, start_date, end_date))

    @router.put("/employees/{employee_id}/availability")
    def save(employee_id: RosterId, request: AvailabilityInput):
        return execute(
            lambda: store.save(
                employee_id,
                AvailabilityDraft(**request.model_dump(exclude={"expected_revision"})),
                request.expected_revision,
            )
        )

    @router.get("/employees/{employee_id}/availability/history")
    def history(employee_id: RosterId):
        return execute(lambda: store.history(employee_id))

    @router.get("/employee-availability")
    def on_slot(local_date: str, slot: str):
        return execute(lambda: store.on_slot(local_date, slot))

    return router
