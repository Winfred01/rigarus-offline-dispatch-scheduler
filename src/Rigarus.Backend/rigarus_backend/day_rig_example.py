"""Temporary synthetic Rig snapshot and swap preview; never a real profile."""

from pathlib import Path
from tempfile import TemporaryDirectory

from .storage import initialize_database
from .projects import ProjectDraft, WorkItemDraft, WorkType
from .project_store import ProjectStore
from .roster import CrewDraft
from .roster_store import CrewStore
from .rigs import RigDraft
from .rig_store import RigStore
from .daily_calendar_store import DailyCalendarStore
from .daily_calendars import DailyInput
from .daily_rig_store import DailyRigStore, RigAllocationInput, RigPeriodInput
from .day_draft_store import DayDraftStore
from .day_drafts import DayDraft, ConfirmedRemainingDays
from .day_recommendation_adapter import (
    DayRecommendationQuery,
    build_day_recommendation_snapshot,
    generate_from_day_snapshot,
)
from .day_rig_proposal import (
    ProposedDayRig,
    validate_saved_rig_change,
    validate_day_rig_proposal,
    check_rig_proposal_freshness,
)


def main():
    day = "2026-11-23"
    with TemporaryDirectory(prefix="rigarus-synthetic-rigs-") as temporary:
        path = Path(temporary) / "synthetic.db"
        initialize_database(path)
        project = ProjectStore(path).save(
            ProjectDraft(
                "SYN-RIG-24",
                "0024",
                "Synthetic Rig site",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 99)],
            )
        )
        crews = tuple(
            CrewStore(path).save(CrewDraft(f"Synthetic C{i}", "Civil")) for i in (1, 2)
        )
        r1 = RigStore(path).save(
            RigDraft("SYN-R1", "Synthetic vehicle", default_crew_id=crews[0].id)
        )
        r2 = RigStore(path).save(RigDraft("SYN-R2", "Synthetic vehicle"))
        calendars = DailyCalendarStore(path)
        for scope, identity in (("Project", project.id), ("Crew", crews[0].id)):
            before = calendars.read(scope, identity, day, "2026-11-27")
            calendars.save(
                scope,
                identity,
                DailyInput(day, "2026-11-27", "Working", True),
                before["revision"],
                before["review_token"],
            )
        visits = DayDraftStore(path)
        one = visits.save(
            DayDraft(
                project.work_items[0].id, crews[0].id, day, "Synthetic original visit"
            )
        )
        two = visits.save(
            DayDraft(
                project.work_items[0].id,
                crews[1].id,
                day,
                "Synthetic competing vehicle visit",
            )
        )
        rigs = DailyRigStore(path)
        for row, vehicle in ((one, r1), (two, r2)):
            rigs.save_allocation(
                "FullDayDraft",
                row["id"],
                RigAllocationInput(
                    vehicle.id,
                    vehicle.id,
                    True,
                    True,
                    True,
                    "Synthetic recorded actual Rig",
                    0,
                ),
                row["revision"],
                0,
            )
        rigs.save_period(
            r1.id,
            "Maintenance",
            RigPeriodInput(
                day, "2026-11-25", "Active", True, "Synthetic independent repair"
            ),
        )
        query = DayRecommendationQuery(
            project.work_items[0].id,
            (crews[0].id,),
            ConfirmedRemainingDays(1, True),
            day,
            "2026-11-27",
            project.id,
            proposed_rig_ids=(r2.id,),
        )
        snapshot = build_day_recommendation_snapshot(path, query)
        choice = ProposedDayRig(
            day, r2.id, True, "Synthetic proposed replacement readiness"
        )
        blocked = validate_saved_rig_change(
            snapshot, "FullDayDraft", one["id"], one["revision"], 1, choice
        )
        print(
            "Occupied replacement",
            blocked.state,
            "conflicts",
            len(blocked.after.conflicts),
            "Validation",
            blocked.validation_status,
            "Apply",
            blocked.applyable,
            "Publish",
            blocked.publishable,
        )
        visits.cancel(two["id"], two["revision"])
        snapshot = build_day_recommendation_snapshot(path, query)
        proposal = validate_saved_rig_change(
            snapshot, "FullDayDraft", one["id"], one["revision"], 1, choice
        )
        after = next(
            c
            for c in proposal.after.checks
            if c.observation.visit.record_id == one["id"]
        ).observation
        print(
            "Replacement after cancellation",
            proposal.state,
            "original",
            after.original_rig_id,
            "projected actual",
            after.actual_rig_id,
            "evidence",
            after.evidence_source,
        )
        print(
            "Database actual unchanged",
            rigs.read_allocation("FullDayDraft", one["id"])["actual_rig_id"],
            "Validation",
            proposal.validation_status,
            "Apply",
            proposal.applyable,
            "Publish",
            proposal.publishable,
        )
        candidate = generate_from_day_snapshot(snapshot).generated.candidates[0]
        choices = tuple(
            ProposedDayRig(d, r2.id, True, "Synthetic dated candidate readiness")
            for d in candidate.allocated_working_dates
        )
        future = validate_day_rig_proposal(snapshot, candidate, choices=choices)
        print(
            "Generated dates",
            candidate.allocated_working_dates,
            "unstaffed overall",
            future.state,
            "Validation",
            future.validation_status,
            "Apply",
            future.applyable,
            "Publish",
            future.publishable,
        )
        print(
            "Before condition change",
            check_rig_proposal_freshness(path, proposal).status,
        )
        rigs.save_period(
            r2.id,
            "Inspection",
            RigPeriodInput(
                day, day, "Active", True, "Synthetic independent inspection"
            ),
        )
        print(
            "After condition change",
            check_rig_proposal_freshness(path, proposal).status,
        )


if __name__ == "__main__":
    main()
