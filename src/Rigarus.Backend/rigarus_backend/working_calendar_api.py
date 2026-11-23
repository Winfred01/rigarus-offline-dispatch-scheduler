import sqlite3
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .roster_api import RosterId
from .working_calendar_store import (
    CalendarConflict,
    CalendarNotFound,
    WorkingCalendarStore,
)

Scope = Literal["Crew", "Project"]


class CalendarInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: str
    end_date: str
    slot: Literal["FullDay", "AM", "PM"]
    state: Literal["Working", "NotWorking", "Unknown"]
    expected_revision: Annotated[
        int, Field(strict=True, ge=0, le=9_007_199_254_740_991)
    ]


def working_calendar_router(path: Path):
    router = APIRouter()
    store = WorkingCalendarStore(path)

    def execute(operation):
        try:
            return operation()
        except CalendarNotFound as error:
            raise HTTPException(404, str(error)) from error
        except CalendarConflict as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503,
                "Could not access working calendars. Check disk access, then reload before retrying.",
            ) from error

    @router.get("/working-calendars/assessment")
    def assess(work_item_id: RosterId, crew_id: RosterId, local_date: str, slot: str):
        return execute(lambda: store.assess(work_item_id, crew_id, local_date, slot))

    @router.get("/working-calendars/{scope}/{entity_id}")
    def read(scope: Scope, entity_id: RosterId, start_date: str, end_date: str):
        return execute(lambda: store.read(scope, entity_id, start_date, end_date))

    @router.put("/working-calendars/{scope}/{entity_id}")
    def save(scope: Scope, entity_id: RosterId, request: CalendarInput):
        return execute(lambda: store.save(scope, entity_id, **request.model_dump()))

    @router.get("/working-calendars/{scope}/{entity_id}/history")
    def history(scope: Scope, entity_id: RosterId):
        return execute(lambda: store.history(scope, entity_id))

    return router
