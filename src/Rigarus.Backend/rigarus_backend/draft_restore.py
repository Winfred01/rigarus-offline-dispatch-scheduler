"""Single original DraftVersion inverse. Isolated synthetic backend only."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from time import monotonic

from . import storage
from .assignments import AssignmentNotFound
from .day_draft_store import read_day, append_change
from .day_editor_store import profile
from .draft_apply import flags, values, FORMAT as APPLY_FORMAT
from .day_recommendation_adapter import ReadBudget, canonical
from .recommendation_adapter import _read_schema, _digest, SnapshotReadError
from .schedule_workbench import _week

FORMAT = "rigarus-draft-restore-v1"
SECONDS = 30


class RestoreRejected(ValueError):
    pass


def _deadline(end):
    if monotonic() >= end:
        raise SnapshotReadError("RESTORE_DEADLINE")


def _source(c, identity, lineage):
    size = c.execute(
        "SELECT length(CAST(ResultJson AS BLOB)) FROM DraftVersions WHERE Id=?",
        (identity,),
    ).fetchone()
    if size and size[0] > 4_000_000:
        raise SnapshotReadError("SOURCE_VERSION_SIZE_LIMIT")
    row = c.execute(
        "SELECT ProfileId,ResultJson FROM DraftVersions WHERE Id=?", (identity,)
    ).fetchone()
    if not row:
        raise RestoreRejected("SOURCE_NOT_FOUND")
    data = json.loads(row[1])
    if (
        row[0] != lineage
        or data["database_identity"] != lineage
        or data["version_id"] != identity
        or data["outcome"] != "Committed"
        or data["plan"]["format"] != APPLY_FORMAT
        or data["applyable"] is not False
        or data["publishable"] is not False
    ):
        raise SnapshotReadError("INVALID_ORIGINAL_DRAFT_VERSION")
    after, before = data["after"], data["plan"]["before"]
    if not 1 <= len(after) <= 366 or len(before) > 366:
        raise SnapshotReadError("RESTORE_SCOPE_LIMIT")
    for rows in (before, after):
        if len({r["id"] for r in rows}) != len(rows) or any(
            r["record_kind"] != "FullDayDraft"
            or type(r["id"]) is not int
            or r["id"] <= 0
            or type(r["revision"]) is not int
            or r["revision"] <= 0
            or r["status"] not in ("Draft", "Cancelled")
            for r in rows
        ):
            raise SnapshotReadError("INVALID_RESTORE_IDENTITIES")
    if not {r["id"] for r in before} <= {r["id"] for r in after}:
        raise SnapshotReadError("INCOMPLETE_ORIGINAL_SCOPE")
    return data


def _inverse(c, source):
    current, desired = [], []
    before = {r["id"]: r for r in source["plan"]["before"]}
    for saved in source["after"]:
        try:
            actual = values(read_day(c, saved["id"]))
        except AssignmentNotFound:
            raise RestoreRejected("Stale") from None
        if canonical(actual) != canonical(saved):
            raise RestoreRejected("Stale")
        current.append(actual)
        target = dict(before.get(saved["id"], saved | dict(status="Cancelled")))
        target["revision"] = actual["revision"] + 1
        desired.append(target)
    return current, desired


def _apply(c, desired):
    """Existing SQL occupancy/Rig/history guards stay active; no legacy SQL writes."""
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    for row in sorted(desired, key=lambda r: (r["status"] != "Cancelled", r["id"])):
        c.execute(
            """UPDATE DayDraftAssignments SET WorkItemId=?,CrewId=?,LocalDate=?,Notes=?,Status=?,
            Revision=Revision+1,UpdatedAt=? WHERE Id=? AND Revision=?""",
            (
                row["work_item_id"],
                row["crew_id"],
                row["local_date"],
                row["notes"],
                row["status"],
                now,
                row["id"],
                row["revision"] - 1,
            ),
        )
        if c.execute("SELECT changes()").fetchone()[0] != 1:
            raise RestoreRejected("Stale")
        append_change(c, row["id"], row["employee_ids"])
    return [values(read_day(c, r["id"])) for r in desired]


def _observations(c, budget, desired, migrations, end):
    active = {r["id"] for r in desired if r["status"] == "Draft"}
    observations = []
    for day in sorted({r["local_date"] for r in desired if r["status"] == "Draft"}):
        _deadline(end)
        board = _week(budget, day, day, migrations)
        observations.extend(
            r
            for r in board["records"]
            if r["record_kind"] == "FullDayDraft" and r["id"] in active
        )
    if len(observations) != len(active):
        raise SnapshotReadError("INCOMPLETE_RESTORE_OBSERVATIONS")
    return observations


def _warnings(observations):
    items, blockers = {}, []
    for row in observations:
        for check in row["checks"]:
            state = check["state"]
            if state not in ("Blocked", "Pending", "Satisfied") and not (
                check["check"] == "DailyCalendars" and state == "Matched"
            ):
                raise SnapshotReadError("UNKNOWN_RESTORE_CHECK_STATE")
            if state == "Blocked":
                blockers.append(dict(record_kind="FullDayDraft", id=row["id"], **check))
            elif state not in ("Matched", "Satisfied"):
                for reason in check["reasons"] or ["MISSING_EVIDENCE"]:
                    item = dict(
                        record_kind="FullDayDraft",
                        record_id=row["id"],
                        local_date=row["local_date"],
                        check=check["check"],
                        state=state,
                        reason=reason,
                    )
                    items[_digest(item)] = item
    for name in (
        "LOCK_POLICY_UNSUPPORTED",
        "DEPENDENCY_POLICY_UNSUPPORTED",
        "UNCONFIRMED_DRAFT_ONLY_NO_DISPATCH",
        "NO_HISTORICAL_RESOURCE_APPROVAL_INHERITANCE",
    ):
        item = dict(
            record_kind="DraftRestore", check=name, state="Pending", reason=name
        )
        items[_digest(item)] = item
    return [dict(warning_id=k, **v) for k, v in sorted(items.items())], blockers


def prepare_in(c, request, end):
    budget = ReadBudget(c)
    migrations = _read_schema(budget)
    lineage = profile(c)
    if lineage != str(request.profile_id):
        raise RestoreRejected("WRONG_DATABASE_IDENTITY")
    source = _source(c, request.source_version_id, lineage)
    current, desired = _inverse(c, source)
    observations, blockers = [], []
    c.execute("SAVEPOINT restore_preview")
    try:
        _apply(c, desired)
        observations = _observations(c, budget, desired, migrations, end)
    except sqlite3.IntegrityError:
        blockers = [
            dict(
                check="SQLGuard",
                state="Blocked",
                reasons=["CURRENT_OCCUPANCY_OR_REFERENCE_CONFLICT"],
            )
        ]
    finally:
        c.execute("ROLLBACK TO restore_preview")
        c.execute("RELEASE restore_preview")
    warnings, resource_blockers = _warnings(observations)
    result = dict(
        format=FORMAT,
        **flags(),
        database_identity=lineage,
        source_record_kind="DraftVersion",
        source_version_id=request.source_version_id,
        source_fingerprint=_digest(source),
        before_restore=current,
        proposed_restore=desired,
        observations=observations,
        warnings=warnings,
        blockers=blockers + resource_blockers,
        status="Blocked" if blockers or resource_blockers else "Current",
        production_writes_enabled=False,
    )
    result["plan_fingerprint"] = _digest(result)
    if len(canonical(result).encode()) > 4_000_000:
        raise SnapshotReadError("RESTORE_PLAN_SIZE_LIMIT")
    _deadline(end)
    return result


def prepare(path, request):
    end = monotonic() + SECONDS
    with closing(storage.connect(path)) as c, c:
        c.set_progress_handler(lambda: int(monotonic() >= end), 1000)
        c.execute("BEGIN IMMEDIATE")
        return prepare_in(c, request, end)


def submit(path, request):
    payload = canonical(request.model_dump(mode="json"))
    if len(payload.encode()) > 2_000_000:
        raise RestoreRejected("REQUEST_SIZE_LIMIT")
    sha, end = _digest((FORMAT, payload)), monotonic() + SECONDS
    with closing(storage.connect(path)) as c, c:
        c.set_progress_handler(lambda: int(monotonic() >= end), 1000)
        c.execute("BEGIN IMMEDIATE")
        _read_schema(ReadBudget(c))
        lineage = profile(c)
        if lineage != str(request.profile_id):
            raise RestoreRejected("WRONG_DATABASE_IDENTITY")
        old = c.execute(
            "SELECT PayloadSha,ResultJson FROM DraftRestoreReceipts WHERE RequestId=?",
            (str(request.request_id),),
        ).fetchone()
        if old:
            if old[0] != sha:
                raise RestoreRejected("IDEMPOTENCY_PAYLOAD_MISMATCH")
            return json.loads(old[1])
        c.execute("SAVEPOINT restore_change")
        try:
            plan = prepare_in(c, request, end)
            if plan["status"] == "Blocked":
                raise RestoreRejected("Blocked")
            if plan["plan_fingerprint"] != request.plan_fingerprint:
                raise RestoreRejected("STALE_RESTORE_PLAN")
            ids = [x["warning_id"] for x in plan["warnings"]]
            if request.confirmed is not True or sorted(
                request.acknowledged_warning_ids
            ) != sorted(ids):
                raise RestoreRejected("EACH_PENDING_ITEM_REQUIRES_CONFIRMATION")
            after = _apply(c, plan["proposed_restore"])
            observations = _observations(
                c, ReadBudget(c), after, _read_schema(ReadBudget(c)), end
            )
            warnings, blocked = _warnings(observations)
            if blocked or warnings != plan["warnings"]:
                raise RestoreRejected("FINAL_RESOURCE_REVALIDATION_FAILED")
            version_id = c.execute(
                "SELECT coalesce(max(Id),0)+1 FROM DraftRestoreVersions"
            ).fetchone()[0]
            result = dict(
                outcome="Committed",
                **flags(),
                record_kind="DraftRestoreVersion",
                version_id=version_id,
                database_identity=lineage,
                request_id=str(request.request_id),
                source_record_kind="DraftVersion",
                source_version_id=request.source_version_id,
                plan=plan,
                after=after,
                observations=observations,
                confirmation=request.model_dump(mode="json"),
                recorded_at=datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
            )
            encoded = canonical(result)
            if len(encoded.encode()) > 8_000_000:
                raise SnapshotReadError("RESTORE_RESULT_SIZE_LIMIT")
            c.execute(
                "INSERT INTO DraftRestoreVersions VALUES(?,?,?,?,?,?,?)",
                (
                    version_id,
                    request.source_version_id,
                    lineage,
                    str(request.request_id),
                    plan["plan_fingerprint"],
                    encoded,
                    result["recorded_at"],
                ),
            )
        except RestoreRejected as error:
            c.execute("ROLLBACK TO restore_change")
            result = dict(
                outcome="Rejected",
                **flags(),
                code=str(error),
                database_identity=lineage,
                request_id=str(request.request_id),
                source_record_kind="DraftVersion",
                source_version_id=request.source_version_id,
                confirmation=request.model_dump(mode="json"),
                recorded_at=datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
            )
            version_id = None
        c.execute("RELEASE restore_change")
        source_exists = c.execute(
            "SELECT Id FROM DraftVersions WHERE Id=?", (request.source_version_id,)
        ).fetchone()
        c.execute(
            "INSERT INTO DraftRestoreReceipts VALUES(?,?,?,?,?,?,?)",
            (
                str(request.request_id),
                sha,
                lineage,
                request.source_version_id if source_exists else None,
                version_id,
                canonical(result),
                result["recorded_at"],
            ),
        )
        _deadline(end)
        return json.loads(canonical(result))


def read_result(path, lineage, *, request_id=None, version_id=None):
    end = monotonic() + SECONDS
    with closing(storage.connect(path, read_only=True)) as c, c:
        c.set_progress_handler(lambda: int(monotonic() >= end), 1000)
        c.execute("BEGIN")
        _read_schema(ReadBudget(c))
        if profile(c) != str(lineage):
            raise RestoreRejected("WRONG_DATABASE_IDENTITY")
        table, field, identity = (
            ("DraftRestoreReceipts", "RequestId", str(request_id))
            if request_id is not None
            else ("DraftRestoreVersions", "Id", version_id)
        )
        row = c.execute(
            f"SELECT ResultJson FROM {table} WHERE {field}=?", (identity,)
        ).fetchone()
        if row and len(row[0].encode()) > 8_000_000:
            raise SnapshotReadError("RESTORE_RECEIPT_SIZE_LIMIT")
        _deadline(end)
        return (
            json.loads(row[0])
            if row
            else dict(
                outcome="NotFound",
                **flags(),
                retry_instruction="Unknown: reconcile or replay only the original unchanged key; do not replace it.",
            )
        )
