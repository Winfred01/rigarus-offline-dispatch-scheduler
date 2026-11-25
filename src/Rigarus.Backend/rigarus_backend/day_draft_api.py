"""Separate slotless API. Default write gate stays closed until desktop cutover."""

import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .assignment_api import SafeId, AssignmentCancel
from .assignments import AssignmentConflict, AssignmentNotFound
from .day_drafts import DayDraft
from .day_draft_store import DayDraftStore
from .day_compatibility import compatibility_report
from .roster_api import RosterId


class DayInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_item_id: SafeId
    crew_id: SafeId
    local_date: str
    notes: str = ""
    employee_ids: list[SafeId] | None = Field(default=None, max_length=1000)

    def draft(self):
        return DayDraft(
            self.work_item_id,
            self.crew_id,
            self.local_date,
            self.notes,
            None if self.employee_ids is None else tuple(self.employee_ids),
        )


class DayEdit(DayInput):
    expected_revision: SafeId


def day_draft_router(path, *, enable_writes=False):
    router = APIRouter(prefix="/day-draft-assignments")
    store = DayDraftStore(path)

    def execute(operation, write=False):
        if write and enable_writes is not True:
            raise HTTPException(
                409,
                "Full-Day writes are not enabled in this desktop rollout. Calendar/resource/snapshot and visible day UI integration required; no automatic conversion.",
            )
        try:
            return operation()
        except AssignmentNotFound as e:
            raise HTTPException(404, str(e)) from e
        except AssignmentConflict as e:
            raise HTTPException(409, str(e)) from e
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        except sqlite3.IntegrityError as e:
            raise HTTPException(
                409,
                "Full-Day conflict or invalid reference. Reload and review daily and legacy visits.",
            ) from e
        except sqlite3.Error as e:
            raise HTTPException(
                503,
                "Cannot access Full-Day Drafts. Check storage and reload before retrying.",
            ) from e

    @router.get("")
    def listing(start_date: str, end_date: str, include_cancelled: bool = False):
        return execute(lambda: store.list(start_date, end_date, include_cancelled))

    @router.get("/legacy-compatibility")
    def compatibility(start_date: str, end_date: str):
        return execute(lambda: compatibility_report(path, start_date, end_date))

    @router.get("/{assignment_id}")
    def read(assignment_id: RosterId):
        return execute(lambda: store.read(assignment_id))

    @router.get("/{assignment_id}/history")
    def history(assignment_id: RosterId):
        return execute(lambda: store.history(assignment_id))

    @router.post("", status_code=201)
    def create(request: DayInput):
        return execute(lambda: store.save(request.draft()), True)

    @router.put("/{assignment_id}")
    def edit(assignment_id: RosterId, request: DayEdit):
        return execute(
            lambda: store.save(
                request.draft(), assignment_id, request.expected_revision
            ),
            True,
        )

    @router.post("/{assignment_id}/cancel")
    def cancel(assignment_id: RosterId, request: AssignmentCancel):
        return execute(
            lambda: store.cancel(assignment_id, request.expected_revision), True
        )

    return router
