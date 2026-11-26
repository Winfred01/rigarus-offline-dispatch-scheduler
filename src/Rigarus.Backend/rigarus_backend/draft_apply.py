"""Exact human-confirmed Draft changesets. Never dispatches, publishes or restores."""

import json
from contextlib import closing
from datetime import datetime, timezone
from time import monotonic

from . import storage
from .day_drafts import DayDraft
from .day_draft_store import DayDraftStore, read_day
from .day_editor_store import profile
from .impact_preview import impact_in
from .recommendation_adapter import _digest, _read_schema, SnapshotReadError
from .day_recommendation_adapter import ReadBudget, canonical
from .schedule_workbench import _week

FORMAT = "rigarus-unconfirmed-draft-v1"
SECONDS = 30


class DraftRejected(ValueError):
    pass


def flags():
    return dict(validation_status="Pending", applyable=False, publishable=False)


def values(row):
    """Restorable business values; never rewind revisions or timestamps."""
    return {
        k: row[k]
        for k in (
            "record_kind",
            "id",
            "revision",
            "work_item_id",
            "project_id",
            "crew_id",
            "local_date",
            "notes",
            "status",
            "employee_ids",
        )
    }


def prepare_in(c, path, request, deadline):
    request.validated()
    q = request.query.model_dump()
    impact = impact_in(c, path, q, deadline=deadline)
    candidate = next(
        (r for r in impact["candidates"] if r["crew_id"] == request.selected_crew_id),
        None,
    )
    if (
        candidate is None
        or not candidate["proposed_finish_date"]
        or request.selected_crew_id not in impact["ranked_crew_ids"]
        or candidate["unfilled_days"]
        or candidate["resource_state"] == "Blocked"
        or any(x["state"] == "Blocked" for x in candidate["checks"])
    ):
        raise DraftRejected("BLOCKED_OR_INCOMPLETE_PLAN")
    # A vehicle nominee is neither actual allocation nor operational confirmation.
    # This slice deliberately refuses to imply that it will assign a vehicle.
    if q["proposed_rig_id"] is not None:
        raise DraftRejected("ACTUAL_RIG_WRITE_UNSUPPORTED")
    before = [values(read_day(c, r["record_id"])) for r in q["replacements"]]
    by_date = {(r["crew_id"], r["local_date"]): r for r in before}
    desired = []
    for day in candidate["allocated_working_dates"]:
        old = by_date.get((request.selected_crew_id, day))
        desired.append(
            dict(
                record_kind="FullDayDraft",
                id=old["id"] if old else None,
                work_item_id=q["work_item_id"],
                project_id=q["expected_project_id"],
                crew_id=request.selected_crew_id,
                local_date=day,
                status="Draft",
                notes=request.notes
                if request.notes is not None
                else old["notes"]
                if old
                else "",
                employee_ids=q["proposed_employee_ids"],
            )
        )
    kept = {r["id"] for r in desired if r["id"] is not None}
    warnings = dict(
        checks=[r for r in candidate["checks"] if r["state"] != "Satisfied"],
        missing_evidence=candidate["missing_evidence"],
        locks=impact["lock_status"],
        downstream=impact["downstream_status"],
        notes=[
            "UNCONFIRMED_DRAFT_ONLY",
            "NO_ACTUAL_RIG_ALLOCATION",
            "SAVED_RESOURCE_EVIDENCE_REQUIRES_RECONFIRMATION_AFTER_REVISION_CHANGE",
            "NO_IMPLICIT_STAFF_INHERITANCE_OR_SOURCE_TRANSFER",
        ],
    )
    result = dict(
        format=FORMAT,
        **flags(),
        status="Current",
        database_identity=impact["database_identity"],
        input_fingerprint=impact["input_fingerprint"],
        proposal_fingerprint=impact["proposal_fingerprint"],
        before=before,
        proposed=desired,
        cancel_ids=sorted(r["id"] for r in before if r["id"] not in kept),
        warnings=warnings,
        affected_crew_ids=impact["affected_crew_ids"],
        affected_work_item_ids=impact["affected_work_item_ids"],
        confirmed_remaining_days=q["remaining_days"],
    )
    result["plan_fingerprint"] = _digest(
        (FORMAT, request.model_dump(mode="json"), result)
    )
    if monotonic() >= deadline:
        raise SnapshotReadError("DRAFT_PREPARATION_DEADLINE")
    return result


def prepare(path, request):
    deadline = monotonic() + SECONDS
    with closing(storage.connect(path, read_only=True)) as c, c:
        c.set_progress_handler(lambda: int(monotonic() >= deadline), 1000)
        c.execute("BEGIN")
        return prepare_in(c, path, request, deadline)


def read_status(path, test_writes=False):
    with closing(storage.connect(path, read_only=True)) as c, c:
        c.execute("BEGIN")
        _read_schema(ReadBudget(c))
        return dict(
            database_identity=profile(c),
            test_writes_enabled=test_writes is True,
            production_writes_enabled=False,
            **flags(),
        )


def receipt_in(c, request_id):
    return c.execute(
        "SELECT PayloadSha,ResultJson FROM DraftVersions WHERE RequestId=?",
        (str(request_id),),
    ).fetchone()


def submit(path, request):
    """One reserved transaction includes proof, mutations, history and version receipt."""
    if request.confirmed is not True or request.pending_acknowledged is not True:
        raise DraftRejected("EXPLICIT_PLAN_AND_PENDING_CONFIRMATION_REQUIRED")
    sha = _digest((FORMAT, request.model_dump(mode="json")))
    deadline = monotonic() + SECONDS
    with closing(storage.connect(path)) as c, c:
        c.set_progress_handler(lambda: int(monotonic() >= deadline), 1000)
        c.execute("BEGIN IMMEDIATE")
        _read_schema(ReadBudget(c))
        if profile(c) != str(request.profile_id):
            raise DraftRejected("WRONG_DATABASE_IDENTITY")
        existing = receipt_in(c, request.request_id)
        if existing:
            if existing[0] != sha:
                raise DraftRejected("IDEMPOTENCY_PAYLOAD_MISMATCH")
            return json.loads(existing[1])
        plan = prepare_in(c, path, request.plan, deadline)
        if plan["plan_fingerprint"] != request.plan_fingerprint:
            raise DraftRejected("STALE_OR_CHANGED_EXACT_PLAN")
        store = DayDraftStore(path)
        before = {r["id"]: r for r in plan["before"]}
        changed = []
        for identity in plan["cancel_ids"]:
            changed.append(
                values(store.cancel_in(c, identity, before[identity]["revision"]))
            )
        for proposed in plan["proposed"]:
            identity = proposed["id"]
            changed.append(
                values(
                    store.save_in(
                        c,
                        DayDraft(
                            proposed["work_item_id"],
                            proposed["crew_id"],
                            proposed["local_date"],
                            proposed["notes"],
                            tuple(proposed["employee_ids"])
                            if proposed["employee_ids"] is not None
                            else None,
                        ),
                        identity,
                        before[identity]["revision"] if identity is not None else None,
                    )
                )
            )
        # Validate actual final saved revisions, including stale saved approvals/Rig.
        # Share one read budget across all dates and every Crew's resource context.
        budget = ReadBudget(c)
        migrations = _read_schema(budget)
        observations = []
        active = {r["id"] for r in changed if r["status"] == "Draft"}
        for day in sorted({r["local_date"] for r in changed if r["status"] == "Draft"}):
            board = _week(budget, day, day, migrations)
            for row in board["records"]:
                if row["record_kind"] == "FullDayDraft" and row["id"] in active:
                    if any(x["state"] == "Blocked" for x in row["checks"]):
                        raise DraftRejected("FINAL_SAVED_RESOURCE_BLOCKED")
                    observations.append(row)
        if len(observations) != len(active):
            raise SnapshotReadError("INCOMPLETE_FINAL_OBSERVATIONS")
        version_id = c.execute(
            "SELECT coalesce(max(Id),0)+1 FROM DraftVersions"
        ).fetchone()[0]
        result = dict(
            outcome="Committed",
            request_id=str(request.request_id),
            version_id=version_id,
            database_identity=str(request.profile_id),
            **flags(),
            plan=plan,
            after=changed,
            observations=observations,
            confirmation=request.model_dump(mode="json"),
            recorded_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        )
        encoded = canonical(result)
        if len(encoded.encode("utf-8")) > 4_000_000:
            raise SnapshotReadError("VERSION_SIZE_LIMIT")
        c.execute(
            "INSERT INTO DraftVersions VALUES(?,?,?,?,?,?,?)",
            (
                version_id,
                str(request.request_id),
                sha,
                str(request.profile_id),
                request.plan_fingerprint,
                encoded,
                result["recorded_at"],
            ),
        )
        if monotonic() >= deadline:
            raise SnapshotReadError("DRAFT_TRANSACTION_DEADLINE")
        return json.loads(encoded)


def read_version(path, profile_id, *, version_id=None, request_id=None, recovery=False):
    """Read reconciliation/inverse only. Never interpret NotFound as rejection."""
    deadline = monotonic() + SECONDS
    with closing(storage.connect(path, read_only=True)) as c, c:
        c.set_progress_handler(lambda: int(monotonic() >= deadline), 1000)
        c.execute("BEGIN")
        _read_schema(ReadBudget(c))
        if profile(c) != str(profile_id):
            raise DraftRejected("WRONG_DATABASE_IDENTITY")
        if version_id is not None:
            row = c.execute(
                "SELECT ResultJson FROM DraftVersions WHERE Id=?", (version_id,)
            ).fetchone()
        else:
            found = receipt_in(c, request_id)
            row = (found[1],) if found else None
        if not row:
            return dict(
                outcome="NotFound",
                **flags(),
                retry_instruction="Resolve/replay the original unchanged request key; absence is not proof of rejection.",
            )
        result = json.loads(row[0])
        if not recovery:
            return result
        current = [values(read_day(c, r["id"])) for r in result["after"]]
        stale = canonical(current) != canonical(result["after"])
        original = {r["id"]: r for r in result["plan"]["before"]}
        proposed = []
        for row in result["after"]:
            target = dict(original.get(row["id"], row | dict(status="Cancelled")))
            target.pop("revision")
            target["expected_current_revision"] = next(
                r["revision"] for r in current if r["id"] == row["id"]
            )
            proposed.append(target)
        if monotonic() >= deadline:
            raise SnapshotReadError("RECOVERY_READ_DEADLINE")
        return dict(
            **flags(),
            readonly=True,
            status="Stale" if stale else "Current",
            version_id=result["version_id"],
            before_restore=current,
            proposed_restore=proposed,
            restore_enabled=False,
            warnings=[
                "INVERSE_PREVIEW_ONLY",
                "RESOURCE_LOCK_DEPENDENCY_REVALIDATION_REQUIRED",
                "RESTORE_WOULD_APPEND_NEW_REVISIONS_NEVER_REWIND_OR_DELETE_HISTORY",
            ],
        )
