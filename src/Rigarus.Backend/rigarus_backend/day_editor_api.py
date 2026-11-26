"""Recoverable manual Draft requests. Production write gate remains closed."""

import sqlite3
from contextlib import closing
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .assignment_api import SafeId
from .assignments import AssignmentNotFound
from .day_draft_api import DayInput
from .day_draft_store import DayDraftStore
from .recommendation_adapter import SnapshotReadError
from .daily_calendar_store import DailySourceError
from .storage import connect
from .roster_api import RosterId
from .day_editor_store import profile, receipt_in, submit
import json


class RequestIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: UUID
    request_id: UUID


class EditorSave(DayInput, RequestIdentity):
    action: Literal["Create", "Edit"]
    id: SafeId | None = None
    expected_revision: SafeId | None = None
    expected_project_id: SafeId
    staffing_confirmed: StrictBool = False


class EditorCancel(RequestIdentity):
    action: Literal["Cancel"]
    id: SafeId
    expected_revision: SafeId


Operation = Annotated[EditorSave | EditorCancel, Field(discriminator="action")]


def day_editor_router(path, *, enable_test_writes=False):
    router = APIRouter(prefix="/day-editor")

    def execute(operation):
        try:
            return operation()
        except AssignmentNotFound:
            raise HTTPException(
                404, "Full Day Draft not found; reload its typed identity."
            ) from None
        except (
            sqlite3.Error,
            OSError,
            ValueError,
            KeyError,
            StopIteration,
            SnapshotReadError,
            DailySourceError,
        ):
            raise HTTPException(
                503,
                "Editor storage or complete safety observations are unavailable. If a request was sent, resolve that exact request before another save.",
            ) from None

    @router.get("/status")
    def status():
        def read():
            with closing(connect(path, read_only=True)) as c, c:
                c.execute("BEGIN")
                return dict(
                    profile_id=profile(c),
                    test_writes_enabled=enable_test_writes is True,
                    production_writes_enabled=False,
                )

        return execute(read)

    @router.get("/record/{identity}")
    def record(identity: RosterId):
        return execute(lambda: DayDraftStore(path).read(identity))

    @router.get("/history/{identity}")
    def history(identity: RosterId):
        return execute(lambda: DayDraftStore(path).history(identity))

    @router.get("/receipt/{profile_id}/{request_id}")
    def receipt(profile_id: UUID, request_id: UUID):
        def read():
            with closing(connect(path, read_only=True)) as c, c:
                c.execute("BEGIN")
                if profile(c) != str(profile_id):
                    raise HTTPException(
                        409, "Recovery belongs to another database; no write was made."
                    )
                row = receipt_in(c, request_id)
                return (
                    json.loads(row[1])
                    if row
                    else dict(outcome="NotFound", request_id=str(request_id))
                )

        return execute(read)

    @router.post("/submit")
    def write(request: Operation):
        if enable_test_writes is not True:
            raise HTTPException(
                409,
                "Production Full Day Draft writes remain closed. This editor is available only in an explicit isolated synthetic test profile pending rollout review.",
            )
        return execute(lambda: submit(path, request))

    return router
