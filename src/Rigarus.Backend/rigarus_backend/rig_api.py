import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .rig_store import RigStore
from .rigs import DuplicateRigNumber, Rig, RigDraft, RigNotFound
from .roster_api import RosterId


class RigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: str
    type: str
    notes: str = ""
    default_crew_id: (
        Annotated[int, Field(strict=True, ge=1, le=9_007_199_254_740_991)] | None
    ) = None
    active: StrictBool = True


def rig_router(database_path: Path) -> APIRouter:
    router = APIRouter(prefix="/rigs")
    store = RigStore(database_path)

    @router.get("")
    def search(term: str = "") -> list[Rig]:
        try:
            return store.search(term)
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not load rigs. Try Search again."
            ) from error

    def save(request: RigInput, rig_id: int | None = None) -> Rig:
        try:
            return store.save(RigDraft(**request.model_dump()), rig_id)
        except RigNotFound as error:
            raise HTTPException(404, str(error)) from error
        except DuplicateRigNumber as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except sqlite3.Error as error:
            raise HTTPException(
                503, "Could not save the rig. Check disk access, then try again."
            ) from error

    @router.post("", status_code=201)
    def create(request: RigInput) -> Rig:
        return save(request)

    @router.put("/{rig_id}")
    def update(rig_id: RosterId, request: RigInput) -> Rig:
        return save(request, rig_id)

    return router
