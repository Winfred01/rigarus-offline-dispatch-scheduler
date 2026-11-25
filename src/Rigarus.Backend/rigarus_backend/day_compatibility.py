"""Read-only, bounded legacy observations. Never a conversion or safety approval."""

from contextlib import closing
from collections import defaultdict

from .availability import range_dates
from .day_drafts import legacy_day_observation
from .storage import connect


def compatibility_report(path, start_date, end_date):
    range_dates(start_date, end_date)
    budget = 10000
    with closing(connect(path, read_only=True)) as c, c:
        c.execute("BEGIN")

        def rows(sql):
            nonlocal budget
            result = c.execute(sql, (start_date, end_date)).fetchmany(budget + 1)
            budget -= len(result)
            if budget < 0:
                raise ValueError(
                    "Compatibility report row limit exceeded; reduce the range."
                )
            return result

        visits = rows(
            "SELECT Id,WorkItemId,CrewId,LocalDate,Slot,Status,Revision,Notes FROM DraftAssignments WHERE LocalDate BETWEEN ? AND ? ORDER BY LocalDate,CrewId,Slot,Id"
        )
        groups = defaultdict(list)
        for r in visits:
            groups[(r[2], r[3])].append(
                dict(
                    zip(
                        (
                            "id",
                            "work_item_id",
                            "crew_id",
                            "local_date",
                            "slot",
                            "status",
                            "revision",
                            "notes",
                        ),
                        r,
                    )
                )
            )
        reports = []
        for (crew, day), original in groups.items():
            active = [r for r in original if r["status"] == "Draft"]
            shape = (
                "Single legacy half"
                if len(original) == 1
                else "Different WorkItems; do not merge"
                if len({r["work_item_id"] for r in original}) > 1
                else "Same WorkItem halves; operator confirmation required"
            )
            reports.append(
                dict(
                    crew_id=crew,
                    local_date=day,
                    label="Legacy Half-Day Record",
                    compatibility_status="Needs Review",
                    conversion_required=True,
                    blocks_full_day=bool(active),
                    reason=shape,
                    original_records=original,
                )
            )
        evidence = []
        for kind, sql in (
            (
                "Calendar",
                "SELECT CalendarId,LocalDate,Slot,State,ChangeId FROM WorkingCalendarCells WHERE LocalDate BETWEEN ? AND ? ORDER BY CalendarId,LocalDate,Slot",
            ),
            (
                "Availability",
                "SELECT EmployeeId,LocalDate,Slot,State,ChangeId FROM EmployeeAvailability WHERE LocalDate BETWEEN ? AND ? ORDER BY EmployeeId,LocalDate,Slot",
            ),
            (
                "Driver",
                "SELECT EmployeeId,LocalDate,Slot,State,ChangeId FROM DriverApprovalCells WHERE LocalDate BETWEEN ? AND ? ORDER BY EmployeeId,LocalDate,Slot",
            ),
            (
                "Capability",
                "SELECT c.OwnerId,c.LocalDate,c.Slot,h.Payload,c.ChangeId FROM CapabilityEvidenceCells c JOIN CapabilityEvidenceChanges h ON h.Id=c.ChangeId WHERE c.LocalDate BETWEEN ? AND ? ORDER BY c.OwnerId,c.LocalDate,c.Slot",
            ),
        ):
            cells = defaultdict(list)
            for owner, day, slot, state, change in rows(sql):
                cells[(owner, day)].append(
                    dict(slot=slot, state=state, change_id=change)
                )
            for (owner, day), halves in cells.items():
                if kind == "Calendar":
                    context = c.execute(
                        "SELECT CrewId,ProjectId FROM WorkingCalendars WHERE Id=?",
                        (owner,),
                    ).fetchone()
                    source_context = dict(crew_id=context[0], project_id=context[1])
                elif kind == "Capability":
                    context = c.execute(
                        "SELECT WorkItemId,EmployeeId,Code FROM CapabilityEvidenceOwners WHERE Id=?",
                        (owner,),
                    ).fetchone()
                    source_context = dict(
                        work_item_id=context[0], employee_id=context[1], code=context[2]
                    )
                else:
                    source_context = dict(employee_id=owner)
                observation = (
                    legacy_day_observation(kind, halves)
                    if kind in ("Calendar", "Availability")
                    else dict(
                        compatibility_status="Needs Review",
                        conversion_required=True,
                        complete_legacy_coverage={r["slot"] for r in halves}
                        == {"AM", "PM"},
                        original_halves=halves,
                        resource_validation="Blocked"
                        if kind == "Driver"
                        and any(r["state"] in ("Suspended", "Expired") for r in halves)
                        else "Pending",
                        reason="Legacy evidence is not full-day actual-worker approval.",
                    )
                )
                evidence.append(
                    dict(
                        kind=kind,
                        owner_id=owner,
                        local_date=day,
                        source_context=source_context,
                        **observation,
                    )
                )
        return dict(
            start_date=start_date,
            end_date=end_date,
            status="Needs Review",
            visits=reports,
            evidence=evidence,
            missing_dates="Unknown / Not recorded; sparse absence is never available capacity.",
            converted_records=0,
            applyable=False,
            publishable=False,
        )
