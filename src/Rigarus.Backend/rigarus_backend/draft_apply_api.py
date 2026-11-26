"""Backend-only unconfirmed Draft preparation and synthetic transaction gate."""

import sqlite3
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from .assignment_api import SafeId
from .roster_api import RosterId
from .assignments import AssignmentConflict, AssignmentNotFound
from .daily_calendar_store import DailySourceError, DailyNotFound
from .draft_apply import prepare, submit, read_version, read_status, DraftRejected
from .impact_preview_api import ImpactQuery
from .recommendation_adapter import (
    SnapshotReadError,
    SnapshotContextError,
    SnapshotNotFound,
)
from .storage import UnsupportedDatabaseError


class PrepareDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: ImpactQuery
    selected_crew_id: SafeId
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("notes")
    @classmethod
    def no_nul(cls, value):
        if value is not None and "\0" in value:
            raise ValueError("Notes cannot contain NUL.")
        return value

    def validated(self):
        self.query.validated()
        if self.selected_crew_id not in self.query.crew_ids:
            raise ValueError("Select an explicit candidate Crew.")


class ConfirmDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan: PrepareDraft
    profile_id: UUID
    request_id: UUID
    plan_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed: StrictBool
    pending_acknowledged: StrictBool


def draft_apply_router(path, *, enable_test_writes=False):
    router = APIRouter(prefix="/draft-transactions")

    def execute(operation):
        try:
            return operation()
        except (SnapshotContextError, SnapshotNotFound, AssignmentNotFound):
            raise HTTPException(409, "STALE_OR_CHANGED_EXACT_PLAN") from None
        except (
            DraftRejected,
            AssignmentConflict,
        ) as e:
            raise HTTPException(409, str(e)) from None
        except (
            sqlite3.Error,
            OSError,
            ValueError,
            KeyError,
            TypeError,
            StopIteration,
            SnapshotReadError,
            DailySourceError,
            DailyNotFound,
            UnsupportedDatabaseError,
        ):
            raise HTTPException(
                503,
                "Draft transaction storage/observations unavailable. Resolve the original request before retrying; success is not certified.",
            ) from None

    def validate(request):
        try:
            request.validated()
        except ValueError:
            raise HTTPException(
                422,
                "Check explicit confirmed days, selected Crew and exact replacement scope.",
            ) from None

    @router.get("/status")
    def status():
        return execute(lambda: read_status(path, enable_test_writes))

    @router.post("/prepare")
    def preview(request: PrepareDraft):
        validate(request)
        return execute(lambda: prepare(path, request))

    @router.post("/submit")
    def write(request: ConfirmDraft):
        if enable_test_writes is not True:
            raise HTTPException(
                409,
                "Production proposal-to-Draft writes remain closed; isolated synthetic opt-in only.",
            )
        validate(request.plan)
        return execute(lambda: submit(path, request))

    @router.get("/receipt/{profile_id}/{request_id}")
    def receipt(profile_id: UUID, request_id: UUID):
        return execute(lambda: read_version(path, profile_id, request_id=request_id))

    @router.get("/version/{profile_id}/{identity}")
    def version(profile_id: UUID, identity: RosterId):
        return execute(lambda: read_version(path, profile_id, version_id=identity))

    @router.get("/recovery-preview/{profile_id}/{identity}")
    def recovery(profile_id: UUID, identity: RosterId):
        return execute(
            lambda: read_version(path, profile_id, version_id=identity, recovery=True)
        )

    return router
