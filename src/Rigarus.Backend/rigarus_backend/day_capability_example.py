"""Reproducible temporary daily capacity preview using fictional company inputs."""

from pathlib import Path
from tempfile import TemporaryDirectory

from .storage import initialize_database
from .projects import ProjectDraft, WorkItemDraft, WorkType
from .project_store import ProjectStore
from .roster import CrewDraft, EmployeeDraft
from .roster_store import CrewStore, EmployeeStore
from .daily_calendar_store import DailyCalendarStore
from .daily_calendars import DailyInput
from .daily_driver_store import DailyDriverApprovalStore, DailyDriverApprovalDraft
from .daily_capability_store import DailyCapabilityStore, DailyCapabilityInput
from .capability_validation import CapabilityRequirements
from .day_drafts import DayDraft, ConfirmedRemainingDays
from .day_draft_store import DayDraftStore
from .day_recommendation_adapter import (
    DayRecommendationQuery,
    build_day_recommendation_snapshot,
    generate_from_day_snapshot,
)
from .day_personnel_validation import ProposedDayMembers
from .day_driver_proposal import SourceDayMembers
from .day_capability_proposal import (
    validate_day_capability_proposal,
    check_day_capability_proposal_freshness,
)


def main():
    day = "2026-11-23"
    with TemporaryDirectory(prefix="rigarus-synthetic-daily-capability-") as temporary:
        path = Path(temporary) / "synthetic.db"
        initialize_database(path)
        project = ProjectStore(path).save(
            ProjectDraft(
                "SYN-DAY-CAP",
                "0109",
                "Synthetic capability site",
                [
                    WorkItemDraft(None, WorkType.CIVIL, 1, 99),
                    WorkItemDraft(None, WorkType.CIVIL, 1, 99),
                ],
            )
        )
        target, source = tuple(
            CrewStore(path).save(CrewDraft(f"Synthetic C{i}", "Civil")) for i in (1, 2)
        )
        people = tuple(
            EmployeeStore(path).save(
                EmployeeDraft(f"Synthetic worker{i}", source.id, 2, False)
            )
            for i in (1, 2, 3)
        )
        cal = DailyCalendarStore(path)
        for scope, identity, state in (
            ("Project", project.id, "Working"),
            ("Crew", target.id, "Working"),
            *(("Employee", p.id, "Available") for p in people),
        ):
            before = cal.read(scope, identity, day, day)
            cal.save(
                scope,
                identity,
                DailyInput(day, day, state, True),
                before["revision"],
                before["review_token"],
            )
        drivers = DailyDriverApprovalStore(path)
        capability = DailyCapabilityStore(path)

        def record(scope, identity, code, value):
            before = capability.read(scope, identity, code, day, day)
            capability.save(
                scope,
                identity,
                code,
                value,
                DailyCapabilityInput(
                    day, day, True, True, "Synthetic explicit daily company input"
                ),
                before["revision"],
                before["review_token"],
            )

        for p in people:
            before = drivers.read(p.id, day, day)
            drivers.save(
                p.id,
                DailyDriverApprovalDraft(
                    day, day, "Active", True, True, "Synthetic company driver proof"
                ),
                before["revision"],
                before["review_token"],
            )
            record("Employee", p.id, "SYN-Q", "Verified")
        for item, minimum in zip(project.work_items, (1, 2)):
            record(
                "WorkItem",
                item.id,
                "",
                CapabilityRequirements(
                    minimum, (0, minimum, 0), "Exact", (("SYN-Q", 1),)
                ),
            )
        saved = DayDraftStore(path).save(
            DayDraft(
                project.work_items[1].id,
                source.id,
                day,
                "Synthetic source actual workers",
                tuple(p.id for p in people[:2]),
            )
        )
        query = DayRecommendationQuery(
            project.work_items[0].id,
            (target.id,),
            ConfirmedRemainingDays(1, True),
            day,
            day,
            project.id,
            proposed_employee_ids=tuple(p.id for p in people),
        )
        snapshot = build_day_recommendation_snapshot(path, query)
        candidate = generate_from_day_snapshot(snapshot).generated.candidates[0]
        members = (ProposedDayMembers(day, (people[0].id,)),)
        result = None
        for label, ids in (
            ("Source short after borrowing", (people[1].id,)),
            ("Explicit qualified replacement", (people[1].id, people[2].id)),
        ):
            override = SourceDayMembers(
                "FullDayDraft", saved["id"], saved["revision"], ids
            )
            result = validate_day_capability_proposal(
                snapshot, candidate, members, (override,)
            )
            print(
                label,
                "driver",
                result.driver.state,
                "capability",
                result.state,
                "ranked",
                len(result.comparison.options),
            )
            print(
                "Source counts",
                [
                    (c.check, c.required, c.state)
                    for c in result.source_checks[0].counts
                ],
            )
            print(
                "Validation",
                result.validation_status,
                "Apply",
                result.applyable,
                "Publish",
                result.publishable,
                "remaining",
                result.pending_validators,
            )
        print(
            "Before source edit",
            check_day_capability_proposal_freshness(path, result).status,
        )
        record("Employee", people[1].id, "SYN-Q", "NotVerified")
        print(
            "After source edit",
            check_day_capability_proposal_freshness(path, result).status,
        )


if __name__ == "__main__":
    main()
