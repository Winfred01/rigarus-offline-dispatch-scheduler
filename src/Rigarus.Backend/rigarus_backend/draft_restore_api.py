"""No desktop bridge; separately gated, exact synthetic-root dry run and writes."""

import sqlite3
from pathlib import Path
from uuid import UUID
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from .assignment_api import SafeId
from .roster_api import RosterId
from . import draft_restore as restore
from .draft_apply import read_status
from .daily_calendar_store import DailySourceError, DailyNotFound
from .recommendation_adapter import (
    SnapshotReadError,
    SnapshotNotFound,
    SnapshotContextError,
)
from .storage import UnsupportedDatabaseError

WarningId = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class PrepareRestore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: UUID
    source_record_kind: Literal["DraftVersion"] = "DraftVersion"
    source_version_id: SafeId


class ConfirmRestore(PrepareRestore):
    request_id: UUID
    plan_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed: StrictBool
    acknowledged_warning_ids: list[WarningId] = Field(max_length=20000)

    @field_validator("acknowledged_warning_ids")
    @classmethod
    def unique(cls, ids):
        if len(ids) != len(set(ids)):
            raise ValueError("Acknowledge each exact warning once.")
        return ids


def draft_restore_router(path, *, enable_test_writes=False, test_root=None):
    enabled = enable_test_writes is True
    if enabled and (
        test_root is None
        or Path(path).resolve() != (Path(test_root) / "data" / "rigarus.db").resolve()
    ):
        raise ValueError(
            "Synthetic restore requires its exact dedicated smoke-root database."
        )
    router = APIRouter(prefix="/draft-restores")

    def gate():
        if not enabled:
            raise HTTPException(409, "RESTORE_PRODUCTION_WRITES_CLOSED")

    def execute(operation):
        try:
            return operation()
        except restore.RestoreRejected as error:
            raise HTTPException(409, str(error)) from None
        except (
            sqlite3.Error,
            OSError,
            ValueError,
            KeyError,
            TypeError,
            SnapshotReadError,
            SnapshotNotFound,
            SnapshotContextError,
            DailySourceError,
            DailyNotFound,
            UnsupportedDatabaseError,
        ):
            raise HTTPException(
                503,
                "Restore result is UNKNOWN. Keep and reconcile the original request; do not replace its key.",
            ) from None

    @router.get("/status")
    def status():
        return execute(lambda: read_status(path, enabled))

    @router.post("/prepare")
    def prepare(request: PrepareRestore):
        gate()
        return execute(lambda: restore.prepare(path, request))

    @router.post("/submit")
    def submit(request: ConfirmRestore):
        gate()
        return execute(lambda: restore.submit(path, request))

    @router.get("/receipt/{profile_id}/{request_id}")
    def receipt(profile_id: UUID, request_id: UUID):
        return execute(
            lambda: restore.read_result(path, profile_id, request_id=request_id)
        )

    @router.get("/version/{profile_id}/{identity}")
    def version(profile_id: UUID, identity: RosterId):
        return execute(
            lambda: restore.read_result(path, profile_id, version_id=identity)
        )

    return router
