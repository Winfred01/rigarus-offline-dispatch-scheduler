"""Transactional manual Draft recording and durable recovery, independent of HTTP."""

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from time import monotonic
from uuid import UUID
from .assignments import AssignmentConflict, AssignmentNotFound
from .day_draft_store import DayDraftStore, read_day
from .recommendation_adapter import _read_schema, SnapshotReadError
from .day_recommendation_adapter import ReadBudget
from .schedule_workbench import _week
from .storage import connect


def profile(c):
    row = c.execute("SELECT ProfileId FROM DayEditorWorkspace WHERE Id=1").fetchone()
    if row is None or str(UUID(row[0])) != row[0]:
        raise ValueError("The editor workspace identity needs review.")
    return row[0]


def receipt_in(c, request_id):
    return c.execute(
        "SELECT PayloadSha,ResultJson FROM DayEditorReceipts WHERE RequestId=?",
        (str(request_id),),
    ).fetchone()


def rejected(request, code, message):
    return dict(
        outcome="Rejected",
        request_id=str(request.request_id),
        code=code,
        message=message,
        validation_status="Pending",
        applyable=False,
        publishable=False,
    )


def apply_request(c, path, request):
    store = DayDraftStore(path)
    if request.action == "Create":
        if request.id is not None or request.expected_revision is not None:
            raise ValueError("New Drafts cannot supply an existing ID or revision.")
    else:
        if request.id is None or request.expected_revision is None:
            raise ValueError("Reload the saved Draft and its revision before editing.")
        old = read_day(c, request.id)
        if old["revision"] != request.expected_revision:
            return rejected(
                request,
                "STALE_REVISION",
                "The Draft changed. Reload its current revision; your unsaved fields were retained.",
            )
    if request.action == "Cancel":
        return store.cancel_in(c, request.id, request.expected_revision)
    draft = request.draft()
    parent = c.execute(
        "SELECT ProjectId FROM WorkItems WHERE Id=?", (draft.work_item_id,)
    ).fetchone()
    if not parent or parent[0] != request.expected_project_id:
        return rejected(
            request,
            "STALE_PROJECT",
            "The WorkItem no longer belongs to this Project. Reload before saving.",
        )
    if draft.employee_ids is not None and not request.staffing_confirmed:
        return rejected(
            request,
            "STAFFING_RECONFIRM",
            "Explicitly confirm the actual employee list for this WorkItem, Crew and date.",
        )
    return store.save_in(c, draft, request.id, request.expected_revision)


def submit(path, request):
    encoded = json.dumps(
        request.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    if len(encoded.encode("utf-8")) > 64000:
        raise ValueError("Draft request exceeds the bounded editor size.")
    sha = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    deadline = monotonic() + 30
    with closing(connect(path)) as c, c:
        c.set_progress_handler(lambda: int(monotonic() >= deadline), 1000)
        c.execute("BEGIN IMMEDIATE")
        if profile(c) != str(request.profile_id):
            return rejected(
                request,
                "WRONG_PROFILE",
                "This recovery request belongs to a different database. No write was made.",
            )
        existing = receipt_in(c, request.request_id)
        if existing:
            if existing[0] != sha:
                return rejected(
                    request,
                    "REQUEST_REUSED",
                    "This request ID already has a different payload. Resolve the original request; do not replace it.",
                )
            return json.loads(existing[1])
        migrations = _read_schema(ReadBudget(c))
        c.execute("SAVEPOINT editor_change")
        try:
            row = apply_request(c, path, request)
            if row.get("outcome") == "Rejected":
                result = row
            else:
                checks = None
                if row["status"] == "Draft":
                    week = _week(
                        ReadBudget(c), row["local_date"], row["local_date"], migrations
                    )
                    checks = next(
                        r
                        for r in week["records"]
                        if r["record_kind"] == "FullDayDraft" and r["id"] == row["id"]
                    )
                result = dict(
                    outcome="Committed",
                    request_id=str(request.request_id),
                    record=row,
                    observation=checks,
                    validation_status="Pending",
                    applyable=False,
                    publishable=False,
                )
        except AssignmentNotFound:
            result = rejected(
                request,
                "NOT_FOUND",
                "This Full Day Draft no longer exists. Reload; no replacement was created.",
            )
        except AssignmentConflict as e:
            result = rejected(request, "OCCUPANCY_OR_REVISION", str(e))
        except ValueError as e:
            result = rejected(request, "INVALID_DRAFT", str(e))
        except sqlite3.IntegrityError:
            result = rejected(
                request,
                "SQL_GUARD",
                "Crew/date, legacy occupancy, Rig or reference conflict. Reload and review; existing records were retained.",
            )
        if result["outcome"] == "Rejected":
            c.execute("ROLLBACK TO editor_change")
        c.execute("RELEASE editor_change")
        if monotonic() >= deadline:
            raise SnapshotReadError("EDITOR_DEADLINE")
        result = json.loads(json.dumps(result))
        c.execute(
            "INSERT INTO DayEditorReceipts VALUES(?,?,?,?)",
            (
                str(request.request_id),
                sha,
                json.dumps(result),
                datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            ),
        )
        return result
