"""Read-only operator projection; never a daily writer or Apply authorization."""

from dataclasses import asdict
from collections import Counter
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .assignment_api import SafeId
from .day_drafts import ConfirmedRemainingDays
from .day_recommendation_adapter import (
    DayRecommendationQuery,
    build_day_recommendation_snapshot,
    generate_from_day_snapshot,
)
from .recommendation_adapter import (
    SnapshotContextError,
    SnapshotNotFound,
    SnapshotReadError,
)


class PreviewQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_item_id: SafeId
    expected_project_id: SafeId
    crew_ids: list[SafeId] = Field(min_length=1, max_length=100)
    remaining_days: SafeId | None = None
    remaining_confirmed: StrictBool = False
    earliest_start_date: str = Field(min_length=10, max_length=10)
    horizon_end_date: str = Field(min_length=10, max_length=10)
    order: Literal["EarliestFinish", "EarliestStart"] = "EarliestFinish"
    max_options: int = Field(default=3, strict=True, ge=1, le=10)

    def query(self):
        return DayRecommendationQuery(
            self.work_item_id,
            tuple(self.crew_ids),
            ConfirmedRemainingDays(self.remaining_days, True)
            if self.remaining_confirmed and self.remaining_days is not None
            else None,
            self.earliest_start_date,
            self.horizon_end_date,
            self.expected_project_id,
            self.order,
            self.max_options,
        )


class FreshnessQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: PreviewQuery
    input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


def _flags():
    return dict(
        unit="FullDay", validation_status="Pending", applyable=False, publishable=False
    )


def _preview(path, query):
    snapshot = build_day_recommendation_snapshot(path, query)
    result = generate_from_day_snapshot(snapshot)
    if (
        result.validation_status != "Pending"
        or result.applyable is not False
        or result.publishable is not False
    ):
        raise SnapshotReadError("UNEXPECTED_PREVIEW_AUTHORIZATION")
    crew_names = {c.crew_id: c.name for c in snapshot.crews}
    candidates = []
    for c in result.generated.candidates:
        missing = Counter((e.check, e.source) for e in c.missing_evidence)
        candidates.append(
            dict(
                crew_id=c.crew_id,
                crew_name=crew_names[c.crew_id],
                status=c.status,
                proposed_start_date=c.proposed_start_date,
                proposed_finish_date=c.proposed_finish_date,
                allocated_working_dates=c.allocated_working_dates,
                accumulated_days=c.accumulated_days,
                unfilled_days=c.unfilled_days,
                review_reasons=c.review_reasons,
                skipped=[asdict(d) for d in c.skipped],
                missing_evidence=[
                    dict(check=check, source=source, count=count)
                    for (check, source), count in sorted(missing.items())
                ],
                missing_evidence_count=len(c.missing_evidence),
            )
        )
    return dict(
        **_flags(),
        work_item_id=query.work_item_id,
        project_id=snapshot.work_item.project_id,
        job_number=snapshot.work_item.job_number,
        work_type=snapshot.work_item.work_type,
        input_fingerprint=snapshot.input_fingerprint,
        order=query.order,
        confirmed_remaining_days=query.remaining.days
        if query.remaining is not None
        else None,
        ranked_crew_ids=[o.option.crew_id for o in result.generated.comparison.options],
        omitted_by_limit=result.generated.comparison.omitted_by_limit,
        candidates=candidates,
        crew_reviews=[
            dict(crew_id=c.crew_id, crew_name=c.name, reasons=c.review_reasons)
            for c in snapshot.crews
            if c.review_reasons
        ],
    )


def day_recommendation_router(path):
    router = APIRouter(prefix="/day-recommendations")

    def execute(operation):
        try:
            return operation()
        except SnapshotNotFound:
            raise HTTPException(
                404, "Selected WorkItem or Crew was not found. Reload project data."
            ) from None
        except SnapshotContextError:
            raise HTTPException(
                409,
                "The WorkItem context changed. Reload the project before previewing.",
            ) from None
        except ValueError:
            raise HTTPException(
                422,
                "Check the selected IDs, explicit days and ordered date range (at most 366 dates).",
            ) from None
        except SnapshotReadError:
            raise HTTPException(
                503,
                "Unable to read current planning data. Check local storage and retry; no preview is certified.",
            ) from None

    @router.post("/preview")
    def preview(request: PreviewQuery):
        return execute(lambda: _preview(path, request.query()))

    @router.post("/freshness")
    def freshness(request: FreshnessQuery):
        def read():
            query = request.query.query()
            try:
                current = build_day_recommendation_snapshot(path, query)
            except (SnapshotNotFound, SnapshotContextError):
                return dict(**_flags(), status="Stale", reason="SOURCE_CONTEXT_CHANGED")
            same = current.input_fingerprint == request.input_fingerprint
            return dict(
                **_flags(),
                status="Current" if same else "Stale",
                reason="UNCHANGED_AT_READ" if same else "INPUTS_CHANGED",
            )

        return execute(read)

    return router
