import sqlite3
from pathlib import Path
from typing import Annotated, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .assignment_store import AssignmentStore
from .assignments import (
    AssignmentConflict,
    AssignmentDraft,
    AssignmentNotFound,
    DraftAssignment,
    HalfDay,
)
from .roster_api import RosterId
from .staffing_store import StaffingStore

SafeId = Annotated[int, Field(strict=True, ge=1, le=9_007_199_254_740_991)]


class AssignmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_item_id: SafeId
    crew_id: SafeId
    local_date: str
    slot: HalfDay
    notes: str = ""


class AssignmentEdit(AssignmentInput):
    expected_revision: SafeId


class AssignmentCancel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: SafeId


class StaffingInput(AssignmentCancel):
    employee_ids: list[SafeId]


def assignment_router(database_path: Path) -> APIRouter:
    router = APIRouter(prefix="/draft-assignments")
    store = AssignmentStore(database_path)
    staffing = StaffingStore(database_path)

    def execute(operation: Callable):
        try:
            return operation()
        except AssignmentNotFound as error:
            raise HTTPException(404, str(error)) from error
        except AssignmentConflict as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            if (
                isinstance(error, sqlite3.IntegrityError)
                and str(error) == "Rig already occupies this date for another Crew."
            ):
                raise HTTPException(
                    409,
                    "Rig conflict on the target date. Reload actual vehicle allocations before moving this visit.",
                ) from error
            raise HTTPException(
                503,
                "Could not access draft assignments. Check disk access, then reload before retrying.",
            ) from error

    @router.get("")
    def list_assignments(
        start_date: str | None = None,
        end_date: str | None = None,
        crew_id: RosterId | None = None,
        include_cancelled: bool = False,
        employee_id: RosterId | None = None,
    ) -> list[DraftAssignment]:
        return execute(
            lambda: store.list(
                start_date, end_date, crew_id, include_cancelled, employee_id
            )
        )

    @router.get("/{assignment_id}")
    def read(assignment_id: RosterId) -> DraftAssignment:
        return execute(lambda: store.read(assignment_id))

    @router.post("", status_code=201)
    def create(request: AssignmentInput) -> DraftAssignment:
        return execute(lambda: store.save(AssignmentDraft(**request.model_dump())))

    @router.put("/{assignment_id}")
    def update(assignment_id: RosterId, request: AssignmentEdit) -> DraftAssignment:
        return execute(
            lambda: store.save(
                AssignmentDraft(**request.model_dump(exclude={"expected_revision"})),
                assignment_id,
                request.expected_revision,
            )
        )

    @router.post("/{assignment_id}/cancel")
    def cancel(assignment_id: RosterId, request: AssignmentCancel) -> DraftAssignment:
        return execute(lambda: store.cancel(assignment_id, request.expected_revision))

    @router.put("/{assignment_id}/staffing")
    def save_staffing(
        assignment_id: RosterId, request: StaffingInput
    ) -> DraftAssignment:
        return execute(
            lambda: staffing.save(
                assignment_id, request.employee_ids, request.expected_revision
            )
        )

    @router.get("/{assignment_id}/staffing-history")
    def staffing_history(assignment_id: RosterId):
        return execute(lambda: staffing.history(assignment_id))

    return router
