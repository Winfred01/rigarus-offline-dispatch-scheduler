"""Slotless daily evidence API; production writes remain gated during cutover."""

import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .daily_calendars import DailyInput
from .daily_calendar_store import (
    DailyCalendarStore,
    DailyNotFound,
    DailyConflict,
    DailySourceError,
)
from .roster_api import RosterId

Scope = Literal["Crew", "Project", "Employee"]


class DailyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: str
    end_date: str
    state: Literal["Working", "NotWorking", "Available", "Unavailable", "Unknown"]
    confirmed_by_operator: StrictBool
    legacy_reviewed: StrictBool = False
    notes: str = Field(default="", max_length=2000)
    expected_revision: Annotated[
        int, Field(strict=True, ge=0, le=9_007_199_254_740_991)
    ]
    expected_review_token: str = Field(pattern="^[0-9a-f]{64}$")


def daily_calendar_router(path, *, enable_writes=False):
    router = APIRouter(prefix="/daily-calendars")
    store = DailyCalendarStore(path)

    def execute(operation, write=False):
        if write and enable_writes is not True:
            raise HTTPException(
                409,
                "Daily input writes are not enabled in this desktop rollout. Visible daily review and snapshot/resource integration required; legacy records remain unchanged.",
            )
        try:
            return operation()
        except DailyNotFound as error:
            raise HTTPException(404, str(error)) from error
        except DailyConflict as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except DailySourceError as error:
            raise HTTPException(
                503,
                "Daily evidence history is inconsistent. Needs Review; do not infer capacity.",
            ) from error
        except sqlite3.IntegrityError as error:
            raise HTTPException(
                409,
                "Daily input conflict or invalid context. Reload the range before retrying.",
            ) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503,
                "Cannot access daily evidence. Check storage and reload before retrying.",
            ) from error

    @router.get("/assessment")
    def assessment(work_item_id: RosterId, crew_id: RosterId, local_date: str):
        return execute(lambda: store.assess(work_item_id, crew_id, local_date))

    @router.get("/{scope}/{entity_id}")
    def read(scope: Scope, entity_id: RosterId, start_date: str, end_date: str):
        return execute(lambda: store.read(scope, entity_id, start_date, end_date))

    @router.get("/{scope}/{entity_id}/history")
    def history(scope: Scope, entity_id: RosterId):
        return execute(lambda: store.history(scope, entity_id))

    @router.put("/{scope}/{entity_id}")
    def save(scope: Scope, entity_id: RosterId, request: DailyRequest):
        return execute(
            lambda: store.save(
                scope,
                entity_id,
                DailyInput(
                    **request.model_dump(
                        exclude={"expected_revision", "expected_review_token"}
                    )
                ),
                request.expected_revision,
                request.expected_review_token,
            ),
            True,
        )

    return router
