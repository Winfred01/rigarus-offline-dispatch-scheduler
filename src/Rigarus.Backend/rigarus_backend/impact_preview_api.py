"""Strict read-only impact requests; no Apply, publication or save endpoint."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .assignment_api import SafeId
from .day_recommendation_api import PreviewQuery, _flags
from .impact_preview import read_impact
from .recommendation_adapter import (
    SnapshotContextError,
    SnapshotNotFound,
    SnapshotReadError,
)


class Replacement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_kind: Literal["FullDayDraft"]
    record_id: SafeId
    expected_revision: SafeId


class ImpactQuery(PreviewQuery):
    replacements: list[Replacement] = Field(default_factory=list, max_length=366)
    proposed_employee_ids: list[SafeId] | None = Field(default=None, max_length=100)
    proposed_rig_id: SafeId | None = None

    def validated(self):
        query = self.query()
        if query.remaining is None:
            raise ValueError("Explicit confirmed Remaining Days required.")
        if len({r.record_id for r in self.replacements}) != len(self.replacements):
            raise ValueError("Duplicate replacement identity.")
        if self.proposed_employee_ids is not None and len(
            set(self.proposed_employee_ids)
        ) != len(self.proposed_employee_ids):
            raise ValueError("Duplicate proposed worker.")
        return query


class ImpactFreshness(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: ImpactQuery
    input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


def impact_router(path):
    router = APIRouter(prefix="/day-impact")

    def execute(request, fingerprint=None):
        request.validated()  # Bad user input is distinguished from corrupt sources.
        try:
            return read_impact(path, request.model_dump(), fingerprint)
        except (SnapshotNotFound, SnapshotContextError):
            if fingerprint is not None:
                return dict(**_flags(), status="Stale", reason="SOURCE_CONTEXT_CHANGED")
            raise HTTPException(
                409, "Saved scope changed or was not found. Reload before previewing."
            ) from None
        except SnapshotReadError:
            raise HTTPException(
                503, "Unable to read impact sources. No preview or safety is certified."
            ) from None

    @router.post("/preview")
    def preview(request: ImpactQuery):
        try:
            return execute(request)
        except ValueError:
            raise HTTPException(
                422, "Check confirmed days, IDs and local dates."
            ) from None

    @router.post("/freshness")
    def freshness(request: ImpactFreshness):
        try:
            return execute(request.query, request.input_fingerprint)
        except ValueError:
            raise HTTPException(422, "Check the original impact query.") from None

    return router
