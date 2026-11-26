"""Pinned impact observations and detached scenarios. Never saves a proposal."""

import json
import os
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import asdict, replace
from pathlib import Path
from time import monotonic
from uuid import UUID

from . import storage
from .daily_calendar_store import DailySourceError, DailyNotFound
from .daily_calendars import assess_daily
from .day_drafts import ConfirmedRemainingDays
from .day_personnel_validation import ProposedDayMembers
from .day_recommendation_adapter import (
    DayRecommendationQuery,
    ReadBudget,
    _read_day_sources,
    canonical,
    generate_from_day_snapshot,
)
from .day_rig_proposal import ProposedDayRig
from .day_weekend_proposal import validate_day_weekend_proposal
from .recommendation_adapter import (
    _digest,
    _read_schema,
    SnapshotReadError,
    SnapshotNotFound,
    SnapshotContextError,
)
from .recommendation_comparison import compare_day_options

FORMAT = "rigarus-read-only-impact-v1"
READ_SECONDS = 30


def _flags():
    return dict(
        unit="FullDay",
        validation_status="Pending",
        applyable=False,
        publishable=False,
        readonly=True,
    )


def _query(request, crews=None):
    return DayRecommendationQuery(
        request["work_item_id"],
        tuple(crews or request["crew_ids"]),
        ConfirmedRemainingDays(
            request["remaining_days"], request["remaining_confirmed"]
        ),
        request["earliest_start_date"],
        request["horizon_end_date"],
        request["expected_project_id"],
        request["order"],
        request["max_options"],
        tuple(request["proposed_employee_ids"] or ()),
        (request["proposed_rig_id"],) if request["proposed_rig_id"] else (),
    )


def _check(name, state, reasons, day=None, kind=None, identity=None):
    return dict(
        check=name,
        state=state,
        reasons=tuple(reasons),
        local_date=day,
        record_kind=kind,
        record_id=identity,
    )


def _resource_rows(personnel, drivers, capabilities, rigs, weekend):
    """Whitelisted explanations, retaining every relevant saved/proposed identity."""
    rows = []
    for name, checks in (
        ("PersonnelConflicts", personnel.checks),
        ("ApprovedDriver", drivers.checks),
        ("WeekendConsent", weekend.checks),
    ):
        for c in checks:
            reasons = list(c.reasons)
            for member in getattr(c, "members", ()):
                reasons.extend(getattr(member, "reasons", ()))
                if hasattr(member, "reason"):
                    reasons.append(member.reason)
            v = c.visit
            rows.append(
                _check(name, c.state, reasons, v.local_date, v.record_kind, v.record_id)
            )
    for c in capabilities.checks:
        v = c.visit
        rows.append(
            _check(
                "CrewType",
                c.crew_state,
                (c.crew_reason,),
                v.local_date,
                v.record_kind,
                v.record_id,
            )
        )
        for n in c.counts:
            rows.append(
                _check(
                    n.check,
                    n.state,
                    (n.reason,),
                    v.local_date,
                    v.record_kind,
                    v.record_id,
                )
            )
    for c in rigs.checks:
        v = c.observation.visit
        rows.append(
            _check(
                "ActualRig",
                c.state,
                c.reasons,
                v.local_date,
                v.record_kind,
                v.record_id,
            )
        )
    return rows


def _saved_rows(snapshot, result):
    checks = _resource_rows(
        result.personnel_validation,
        result.driver_validation,
        result.capability_validation,
        result.rig_validation,
        result.weekend_validation,
    )
    grouped = {}
    for c in checks:
        grouped.setdefault((c["record_kind"], c["record_id"]), []).append(c)
    rigs = {
        c.observation.visit.key: c.observation for c in result.rig_validation.checks
    }
    inputs = {
        (s.scope, s.entity_id): {
            e["local_date"]: e for e in json.loads(s.payload_json)["entries"]
        }
        for s in snapshot.daily_inputs
    }
    records = []
    for kind, visits in (
        ("FullDayDraft", snapshot.day_assignments),
        ("LegacyHalfDay", snapshot.legacy_assignments),
    ):
        for a in visits:
            if a.status != "Draft":
                continue
            key = kind, a.assignment_id
            current = (
                json.loads(a.payload_json)["current"]
                if kind == "FullDayDraft"
                else None
            )
            row_checks = list(grouped.get(key, ()))
            if a.work_item_id == snapshot.work_item.work_item_id:
                crew = inputs.get(("Crew", a.crew_id), {}).get(a.local_date)
                project = inputs["Project", a.project_id][a.local_date]
                if crew:
                    calendar = assess_daily(a.local_date, crew, project)
                    row_checks.append(
                        _check(
                            "DailyCalendars",
                            calendar["status"],
                            ("CREW_" + crew["state"], "PROJECT_" + project["state"]),
                            a.local_date,
                            kind,
                            a.assignment_id,
                        )
                    )
            observation = rigs.get((*key, a.local_date))
            records.append(
                dict(
                    record_kind=kind,
                    record_id=a.assignment_id,
                    revision=a.revision,
                    work_item_id=a.work_item_id,
                    project_id=a.project_id,
                    crew_id=a.crew_id,
                    local_date=a.local_date,
                    slot=getattr(a, "slot", None),
                    staffing_configured=current["staffing_configured"]
                    if current
                    else a.staffing_configured,
                    employee_ids=a.actual_employee_ids,
                    actual_rig_id=observation.actual_rig_id if observation else None,
                    notes=current["notes"] if current else None,
                    checks=row_checks,
                    provenance="Saved",
                    compatibility_status="Needs Review"
                    if kind == "LegacyHalfDay"
                    else "Full Day Draft",
                )
            )
    return records


def project_impact(snapshot, request, base, target_index):
    """Pure scenario projection; all I/O is complete before entering this function."""
    replacements = {
        r["record_id"]: r["expected_revision"] for r in request["replacements"]
    }
    saved_by_id = {a.assignment_id: a for a in snapshot.day_assignments}
    for identity, revision in replacements.items():
        a = saved_by_id.get(identity)
        if (
            a is None
            or a.revision != revision
            or a.status != "Draft"
            or a.work_item_id != request["work_item_id"]
            or a.project_id != request["expected_project_id"]
        ):
            raise SnapshotContextError("Exact full-day replacement scope changed.")
    before_result = generate_from_day_snapshot(snapshot)
    saved = _saved_rows(snapshot, before_result)
    before = [r for r in saved if r["work_item_id"] == request["work_item_id"]]
    # Release reviewed actual capacity only in memory. Stale Rig claims remain
    # conservative: releasing today's visit cannot erase its unreviewed old claims.
    rig = json.loads(snapshot.rig_source_json)
    rig["allocations"] = [
        a
        for a in rig["allocations"]
        if not (
            a["context"]["record_kind"] == "FullDayDraft"
            and a["context"]["record_id"] in replacements
            and not a.get("context_stale", False)
        )
    ]
    scenario = replace(
        snapshot,
        crews=tuple(c for c in snapshot.crews if c.crew_id in request["crew_ids"]),
        day_assignments=tuple(
            a for a in snapshot.day_assignments if a.assignment_id not in replacements
        ),
        rig_source_json=canonical(rig),
    )
    generated = generate_from_day_snapshot(scenario)
    candidates, options = [], []
    related_keys, related_crews, related_works = set(), set(), set()
    crew_names = {c.crew_id: c.name for c in snapshot.crews}
    for c in generated.generated.candidates:
        checks, state = [], "Pending"
        if c.option is not None:
            members = tuple(
                ProposedDayMembers(
                    day,
                    tuple(request["proposed_employee_ids"])
                    if request["proposed_employee_ids"] is not None
                    else None,
                )
                for day in c.allocated_working_dates
            )
            choices = tuple(
                ProposedDayRig(
                    day,
                    request["proposed_rig_id"],
                    False,
                    "Explicit impact-preview nominee; operational proof not supplied",
                )
                for day in c.allocated_working_dates
            )
            proof = validate_day_weekend_proposal(scenario, c, members, (), choices)
            capability, driver = proof.rig.capability, proof.rig.capability.driver
            checks = _resource_rows(
                driver.after.personnel,
                driver.after,
                capability.after,
                proof.rig.after,
                proof.after,
            )
            # Include exact proposed dates and both-Crew borrowing observations.
            source_keys = {x.visit.key for x in driver.source_checks}
            for check in driver.source_checks:
                related_crews.add(check.visit.crew_id)
                related_works.add(check.visit.work_item_id)
            for collision in proof.rig.after.conflicts:
                if not any(v.record_kind == "Proposal" for v in collision.visits):
                    continue
                for ref in collision.visits:
                    if ref.record_kind != "Proposal":
                        source_keys.add(ref.key)
                        related_crews.add(ref.crew_id)
                        if ref.work_item_id is not None:
                            related_works.add(ref.work_item_id)
            related_keys.update(source_keys)
            # A stale Rig can retain a recorded claim inside this horizon while
            # its current visit/WorkItem has moved outside. Expose both identities.
            for check in proof.rig.after.checks:
                visit = check.observation.visit
                if visit.key in source_keys:
                    related_crews.add(visit.crew_id)
                    related_works.add(visit.work_item_id)
            checks = [
                r
                for r in checks
                if r["record_kind"] == "Proposal"
                or (r["record_kind"], r["record_id"], r["local_date"]) in source_keys
            ]
            state = proof.state
            options.append(
                (*proof.comparison.options, *proof.comparison.excluded)[0].option
            )
        missing = Counter((e.check, e.source) for e in c.missing_evidence)
        candidates.append(
            dict(
                crew_id=c.crew_id,
                crew_name=crew_names[c.crew_id],
                status=c.status,
                resource_state=state,
                proposed_start_date=c.proposed_start_date,
                proposed_finish_date=c.proposed_finish_date,
                allocated_working_dates=c.allocated_working_dates,
                accumulated_days=c.accumulated_days,
                unfilled_days=c.unfilled_days,
                review_reasons=c.review_reasons,
                skipped=[asdict(d) for d in c.skipped],
                checks=checks,
                proposed_employee_ids=request["proposed_employee_ids"],
                proposed_rig_id=request["proposed_rig_id"],
                missing_evidence=[
                    dict(check=k, source=s, count=n)
                    for (k, s), n in sorted(missing.items())
                ],
                missing_evidence_count=len(c.missing_evidence),
                provenance="Proposed",
            )
        )
    comparison = compare_day_options(
        request["work_item_id"],
        request["expected_project_id"],
        tuple(options),
        max_options=request["max_options"],
        order=request["order"],
    )
    selected_dates = [
        a.local_date
        for a in snapshot.day_assignments
        if a.assignment_id in replacements
    ]
    protected = [
        r
        for r in saved
        if (
            r["crew_id"] in request["crew_ids"]
            or r["work_item_id"] == request["work_item_id"]
            or (r["record_kind"], r["record_id"], r["local_date"]) in related_keys
        )
        and not (r["record_kind"] == "FullDayDraft" and r["record_id"] in replacements)
    ]
    result = dict(
        **_flags(),
        work_item_id=request["work_item_id"],
        project_id=snapshot.work_item.project_id,
        job_number=snapshot.work_item.job_number,
        work_type=snapshot.work_item.work_type,
        order=request["order"],
        input_fingerprint=base["input_fingerprint"],
        database_identity=base["database_identity"],
        before=dict(
            provenance="Saved",
            records=before,
            start_date=min((r["local_date"] for r in before), default=None),
            finish_date=max((r["local_date"] for r in before), default=None),
            remaining_days=None,
            remaining_status="Not recorded",
            selected_start_date=min(selected_dates, default=None),
            selected_finish_date=max(selected_dates, default=None),
        ),
        confirmed_remaining_days=request["remaining_days"],
        candidates=candidates,
        protected_records=protected,
        ranked_crew_ids=[o.option.crew_id for o in comparison.options],
        blocked_crew_ids=[o.option.crew_id for o in comparison.excluded],
        omitted_by_limit=comparison.omitted_by_limit,
        crew_reviews=[
            dict(crew_id=c.crew_id, crew_name=c.name, reasons=c.review_reasons)
            for c in scenario.crews
            if c.review_reasons
        ],
        replacement_scope=request["replacements"],
        outside_horizon_count=sum(
            not request["earliest_start_date"] <= r[2] <= request["horizon_end_date"]
            for r in target_index
        ),
        affected_crew_ids=sorted(
            set(request["crew_ids"])
            | related_crews
            | {r["crew_id"] for r in protected}
            | {
                a.crew_id
                for a in saved_by_id.values()
                if a.assignment_id in replacements
            }
        ),
        affected_work_item_ids=sorted(
            {request["work_item_id"]}
            | related_works
            | {r["work_item_id"] for r in protected}
        ),
        lock_status="Not recorded / Unsupported",
        downstream_status="Needs Review / Unsupported Dependency",
        status="Current",
        coverage=dict(
            start_date=request["earliest_start_date"],
            end_date=request["horizon_end_date"],
            downstream_complete=False,
            source_revision_vector=[
                dict(record_kind=r[0], record_id=r[1], local_date=r[2], revision=r[3])
                for r in target_index
            ],
        ),
    )
    result["proposal_fingerprint"] = _digest((FORMAT, result))
    result["proposal_id"] = result["proposal_fingerprint"]
    return result


def read_impact(path: Path, request, fingerprint=None):
    """One query-only transaction includes source identity, scope and resources."""
    deadline = monotonic() + READ_SECONDS

    def expired():
        return int(monotonic() >= deadline)

    query = _query(request)
    try:
        with closing(storage.connect(path, read_only=True)) as connection, connection:
            connection.set_progress_handler(expired, 1000)
            connection.execute("BEGIN")
            c = ReadBudget(connection)
            migrations = _read_schema(c)
            profile = c.execute(
                "SELECT ProfileId FROM DayEditorWorkspace WHERE Id=1"
            ).fetchone()
            if profile is None or str(UUID(profile[0])) != profile[0]:
                raise SnapshotReadError("DATABASE_IDENTITY_INVALID")
            target_index = tuple(
                c.execute(
                    "SELECT 'FullDayDraft',Id,LocalDate,Revision,CrewId,Notes FROM DayDraftAssignments WHERE WorkItemId=? AND Status='Draft' "
                    "UNION ALL SELECT 'LegacyHalfDay',Id,LocalDate,Revision,CrewId,Notes FROM DraftAssignments WHERE WorkItemId=? AND Status='Draft' ORDER BY 1,2",
                    (query.work_item_id, query.work_item_id),
                ).fetchall()
            )
            crews = sorted(
                set(query.crew_ids)
                | {
                    r[4]
                    for r in target_index
                    if query.earliest_start_date <= r[2] <= query.horizon_end_date
                }
            )
            snapshot = _read_day_sources(
                c,
                _query(request, crews),
                _digest(os.path.normcase(str(path.resolve()))),
                migrations,
            )
            base = dict(
                database_identity=profile[0],
                input_fingerprint=_digest(
                    (
                        FORMAT,
                        profile[0],
                        snapshot.input_fingerprint,
                        request,
                        target_index,
                    )
                ),
            )
            # Bound repeated detached validation before materializing alternatives.
            # SQL/bytes already share the reader budget; computation is charged too.
            if fingerprint is None:
                c.charge(
                    (len(snapshot.day_assignments) + len(snapshot.legacy_assignments))
                    * (len(query.crew_ids) + 2)
                    * 8
                    + min(request["remaining_days"], 366)
                    * len(query.crew_ids)
                    * max(1, len(request["proposed_employee_ids"] or ()))
                    * 8
                )
            if fingerprint is not None:
                result = dict(
                    **_flags(),
                    status="Current"
                    if fingerprint == base["input_fingerprint"]
                    else "Stale",
                    reason="UNCHANGED_AT_READ"
                    if fingerprint == base["input_fingerprint"]
                    else "INPUTS_CHANGED",
                )
            else:
                result = project_impact(snapshot, request, base, target_index)
            c.charge_bytes(len(canonical(result).encode("utf-8")))
            c.charge(
                sum(len(x.get("checks", ())) for x in result.get("candidates", ()))
            )
            if expired():
                raise SnapshotReadError("READ_DEADLINE_EXCEEDED")
            return result
    except (SnapshotContextError, SnapshotNotFound, SnapshotReadError):
        raise
    except (
        sqlite3.Error,
        OSError,
        DailySourceError,
        DailyNotFound,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        OverflowError,
    ):
        raise SnapshotReadError("IMPACT_SOURCE_READ_FAILED") from None
