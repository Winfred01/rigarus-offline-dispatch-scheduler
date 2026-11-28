"""Coherent, bounded, query-only weekly UI projection. Never write authorization."""

import json
import sqlite3
from contextlib import closing
from datetime import date
from time import monotonic
from typing import Literal

from fastapi import APIRouter, HTTPException

from .roster_api import RosterId
from .assignments import local_date
from .storage import connect
from .recommendation_adapter import _read_schema, _digest, SnapshotReadError
from .day_recommendation_adapter import (
    ReadBudget,
    DayRecommendationQuery,
    _read_day_sources,
    validate_day_snapshot_personnel,
    validate_day_snapshot_weekend,
)
from .daily_driver_validation import validate_day_snapshot_drivers
from .daily_capability_validation import validate_day_snapshot_capabilities
from .day_capability_proposal import _groups as capability_groups
from .daily_rig_validation import validate_day_snapshot_rigs
from .daily_calendar_store import daily_assessment, DailySourceError

KINDS = ("FullDayDraft", "LegacyHalfDay")


def check_range(start, end):
    local_date(start)
    local_date(end)
    if not 0 <= (date.fromisoformat(end) - date.fromisoformat(start)).days <= 6:
        raise ValueError("Choose an ordered range of at most seven local dates.")


def _week(c, start, end, migrations):
    crews = [
        dict(zip(("id", "name", "type", "active"), r))
        for r in c.execute("SELECT Id,Name,Type,Active FROM Crews ORDER BY Id")
    ]
    if len(crews) > 100:
        raise SnapshotReadError("CREW_SCOPE_LIMIT")
    works = [
        dict(zip(("id", "project_id", "job_number", "site_id", "site_name", "type"), r))
        for r in c.execute(
            "SELECT w.Id,w.ProjectId,p.JobNumber,p.SiteId,p.SiteName,w.Type FROM WorkItems w JOIN Projects p ON p.Id=w.ProjectId ORDER BY w.Id"
        )
    ]
    records, people = [], []
    if crews and works:
        q = DayRecommendationQuery(
            works[0]["id"], tuple(x["id"] for x in crews), None, start, end
        )
        snap = _read_day_sources(c, q, "weekly-ui", migrations)
        people = [
            dict(
                id=e.employee_id,
                name=e.metadata[1],
                home_crew_id=e.metadata[2],
                active=bool(e.metadata[5]),
            )
            for e in snap.employees
        ]
        names = {p["id"]: p for p in people}
        work = {w["id"]: w for w in works}
        crew = {x["id"]: x for x in crews}
        personnel = {
            x.visit.key: x for x in validate_day_snapshot_personnel(snap).checks
        }
        drivers = {x.visit.key: x for x in validate_day_snapshot_drivers(snap).checks}
        capabilities = {
            x.visit.key: x for x in validate_day_snapshot_capabilities(snap).checks
        }
        rigs = {
            x.observation.visit.key: x for x in validate_day_snapshot_rigs(snap).checks
        }
        consents = {x.visit.key: x for x in validate_day_snapshot_weekend(snap).checks}
        legacy_notes = dict(
            c.execute(
                "SELECT Id,Notes FROM DraftAssignments WHERE LocalDate BETWEEN ? AND ?",
                (start, end),
            )
        )
        for kind, rows in (
            ("FullDayDraft", snap.day_assignments),
            ("LegacyHalfDay", snap.legacy_assignments),
        ):
            for a in rows:
                if a.status != "Draft":
                    continue
                key = kind, a.assignment_id, a.local_date
                try:
                    p, d, cap, r, consent = (
                        m[key]
                        for m in (personnel, drivers, capabilities, rigs, consents)
                    )
                except KeyError:
                    raise SnapshotReadError("INCOMPLETE_VALIDATION_SCOPE") from None
                calendar = daily_assessment(c, a.work_item_id, a.crew_id, a.local_date)
                c.charge_bytes(len(json.dumps(calendar).encode("utf-8")))
                notes = (
                    json.loads(a.payload_json)["current"]["notes"]
                    if kind == "FullDayDraft"
                    else legacy_notes[a.assignment_id]
                )
                checks = [
                    dict(
                        check="DailyCalendars",
                        state=calendar["status"],
                        reasons=[
                            "CREW_" + calendar["crew"]["state"],
                            "PROJECT_" + calendar["project"]["state"],
                        ],
                    ),
                    dict(check="PersonnelConflicts", state=p.state, reasons=p.reasons),
                    dict(
                        check="ApprovedDriver",
                        state=d.state,
                        reasons=tuple(d.reasons)
                        + tuple(
                            reason for member in d.members for reason in member.reasons
                        ),
                    ),
                    dict(
                        check="CrewType",
                        state=cap.crew_state,
                        reasons=[cap.crew_reason],
                    ),
                    *[
                        dict(check=n.check, state=n.state, reasons=[n.reason])
                        for n in cap.counts
                    ],
                    *(
                        []
                        if any(n.check == "Qualifications" for n in cap.counts)
                        else [
                            dict(
                                check="Qualifications",
                                state=capability_groups(cap)["Qualifications"],
                                reasons=[
                                    n.check + ":" + n.reason
                                    for n in cap.counts
                                    if n.check.startswith("Qualification:")
                                ]
                                or ["EXPLICIT_EMPTY_QUALIFICATION_REQUIREMENTS"],
                            )
                        ]
                    ),
                    dict(
                        check="Foreman",
                        state="Pending",
                        reasons=["FOREMAN_POLICY_PENDING"],
                    ),
                    dict(check="ActualRig", state=r.state, reasons=r.reasons),
                    dict(
                        check="VehicleCategory",
                        state="Pending",
                        reasons=["CATEGORY_POLICY_PENDING"],
                    ),
                    dict(
                        check="WeekendConsent",
                        state=consent.state,
                        reasons=tuple(consent.reasons)
                        + tuple(m.reason for m in consent.members),
                    ),
                ]
                row = dict(
                    record_kind=kind,
                    id=a.assignment_id,
                    revision=a.revision,
                    work_item_id=a.work_item_id,
                    project_id=a.project_id,
                    crew_id=a.crew_id,
                    crew_name=crew[a.crew_id]["name"],
                    local_date=a.local_date,
                    slot=a.slot if kind == "LegacyHalfDay" else None,
                    job_number=work[a.work_item_id]["job_number"],
                    site_id=work[a.work_item_id]["site_id"],
                    site_name=work[a.work_item_id]["site_name"],
                    work_type=work[a.work_item_id]["type"],
                    notes=notes,
                    staffing_configured=p.visit.staffing_configured,
                    workers=[names[e] for e in p.visit.employee_ids],
                    actual_rig_id=r.observation.actual_rig_id,
                    rig_context_stale=r.observation.context_stale,
                    validation_status="Pending",
                    applyable=False,
                    publishable=False,
                    compatibility_status="Needs Review"
                    if kind == "LegacyHalfDay"
                    else "Full Day Draft",
                    checks=checks,
                )
                c.charge(
                    len(checks)
                    + len(row["workers"])
                    + sum(len(x["reasons"]) for x in checks)
                )
                c.charge_bytes(len(json.dumps(row, ensure_ascii=False).encode("utf-8")))
                records.append(row)
    result = dict(
        start_date=start,
        end_date=end,
        crews=crews,
        work_items=works,
        people=people,
        records=records,
        validation_status="Pending",
        applyable=False,
        publishable=False,
        readonly=True,
    )
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False)
    c.charge_bytes(len(encoded.encode("utf-8")))
    result["view_fingerprint"] = _digest(("weekly-workbench-v1", encoded))
    return result


def read_workbench(path, start=None, end=None, *, kind=None, identity=None):
    if kind is None:
        check_range(start, end)
    elif (
        kind not in KINDS or type(identity) is not int or not 0 < identity <= 2**53 - 1
    ):
        raise ValueError("Choose an explicit saved record kind and positive ID.")
    deadline = monotonic() + 30
    try:
        with closing(connect(path, read_only=True)) as conn, conn:
            conn.set_progress_handler(lambda: int(monotonic() >= deadline), 1000)
            conn.execute("BEGIN")
            c = ReadBudget(conn)
            migrations = _read_schema(c)
            target = None
            if kind is not None:
                table = (
                    "DayDraftAssignments"
                    if kind == "FullDayDraft"
                    else "DraftAssignments"
                )
                row = c.execute(
                    f"SELECT LocalDate,Status,Revision FROM {table} WHERE Id=?",
                    (identity,),
                ).fetchone()
                if row is None:
                    raise HTTPException(
                        404, "Saved record not found. Check its kind and ID."
                    )
                if row[1] != "Draft":
                    raise HTTPException(
                        409,
                        "This record is cancelled; the active board was not changed.",
                    )
                day = date.fromisoformat(row[0])
                first = max(
                    date.min.toordinal(), day.toordinal() - (day.weekday() + 1) % 7
                )
                start, end = (
                    date.fromordinal(first).isoformat(),
                    date.fromordinal(min(date.max.toordinal(), first + 6)).isoformat(),
                )
                target = dict(record_kind=kind, id=identity, revision=row[2])
            result = _week(c, start, end, migrations)
            if monotonic() >= deadline:
                raise SnapshotReadError("READ_DEADLINE_EXCEEDED")
            if target is not None:
                if not any(
                    r["record_kind"] == kind and r["id"] == identity
                    for r in result["records"]
                ):
                    raise SnapshotReadError("TARGET_NOT_PROJECTED")
                result["target"] = target
            return result
    except (
        SnapshotReadError,
        DailySourceError,
        sqlite3.Error,
        OSError,
        KeyError,
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            503,
            "Unable to read a complete weekly snapshot. Reload; no record or check is certified.",
        ) from None


def workbench_router(path):
    router = APIRouter(prefix="/schedule-workbench")

    @router.get("/week")
    def week(start_date: str, end_date: str):
        try:
            check_range(start_date, end_date)
        except ValueError:
            raise HTTPException(
                422, "Choose an ordered range of at most seven valid local dates."
            ) from None
        return read_workbench(path, start_date, end_date)

    @router.get("/locate/{kind}/{identity}")
    def locate(kind: Literal["FullDayDraft", "LegacyHalfDay"], identity: RosterId):
        return read_workbench(path, kind=kind, identity=identity)

    return router
