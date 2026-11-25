"""Temporary synthetic company-driver preview; no operational profile or Apply."""

from pathlib import Path
from tempfile import TemporaryDirectory

from .storage import initialize_database
from .projects import ProjectDraft, WorkItemDraft, WorkType
from .project_store import ProjectStore
from .roster import CrewDraft, EmployeeDraft
from .roster_store import CrewStore, EmployeeStore
from .daily_calendars import DailyInput
from .daily_calendar_store import DailyCalendarStore
from .daily_driver_store import DailyDriverApprovalDraft, DailyDriverApprovalStore
from .day_drafts import ConfirmedRemainingDays, DayDraft
from .day_draft_store import DayDraftStore
from .day_recommendation_adapter import (
    DayRecommendationQuery,
    build_day_recommendation_snapshot,
    generate_from_day_snapshot,
)
from .day_personnel_validation import ProposedDayMembers
from .day_driver_proposal import (
    SourceDayMembers,
    validate_day_driver_proposal,
    check_day_driver_proposal_freshness,
)


def main():
    day = "2026-11-23"
    with TemporaryDirectory(prefix="rigarus-synthetic-daily-drivers-") as temporary:
        path = Path(temporary) / "synthetic.db"
        initialize_database(
            path
        )  # Explicit synthetic seed; never in recommendation reads.
        project = ProjectStore(path).save(
            ProjectDraft(
                "SYN-DRIVER-DAY",
                "0023",
                "Synthetic driver site",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 99)],
            )
        )
        target, source = tuple(
            CrewStore(path).save(CrewDraft(f"Synthetic C{i}", "Civil")) for i in (1, 2)
        )
        driver, replacement = tuple(
            EmployeeStore(path).save(
                EmployeeDraft(f"Synthetic driver {i}", source.id, 2, False)
            )
            for i in (1, 2)
        )
        calendar = DailyCalendarStore(path)
        for scope, identity, state in (
            ("Project", project.id, "Working"),
            ("Crew", target.id, "Working"),
            ("Employee", driver.id, "Available"),
            ("Employee", replacement.id, "Available"),
        ):
            old = calendar.read(scope, identity, day, day)
            calendar.save(
                scope,
                identity,
                DailyInput(day, day, state, True),
                old["revision"],
                old["review_token"],
            )
        approvals = DailyDriverApprovalStore(path)

        def approve(person, state="Active"):
            old = approvals.read(person.id, day, day)
            approvals.save(
                person.id,
                DailyDriverApprovalDraft(
                    day,
                    day,
                    state,
                    True,
                    True,
                    "Synthetic explicit whole-day company confirmation",
                ),
                old["revision"],
                old["review_token"],
            )

        for person in (driver, replacement):
            approve(person)
        saved = DayDraftStore(path).save(
            DayDraft(
                project.work_items[0].id,
                source.id,
                day,
                "Synthetic source visit",
                (driver.id,),
            )
        )
        query = DayRecommendationQuery(
            project.work_items[0].id,
            (target.id,),
            ConfirmedRemainingDays(1, True),
            day,
            day,
            project.id,
            proposed_employee_ids=(driver.id, replacement.id),
        )
        snapshot = build_day_recommendation_snapshot(path, query)
        candidate = generate_from_day_snapshot(snapshot).generated.candidates[0]
        members = (ProposedDayMembers(day, (driver.id,)),)
        proof = None
        for label, overrides in (
            ("No implicit source removal", ()),
            (
                "Sole driver removed",
                (SourceDayMembers("FullDayDraft", saved["id"], saved["revision"], ()),),
            ),
            (
                "Explicit eligible replacement",
                (
                    SourceDayMembers(
                        "FullDayDraft",
                        saved["id"],
                        saved["revision"],
                        (replacement.id,),
                    ),
                ),
            ),
        ):
            proof = validate_day_driver_proposal(
                snapshot, candidate, members, overrides
            )
            print(
                label,
                proof.state,
                "target",
                [c.state for c in proof.target_checks],
                "source",
                [c.state for c in proof.source_checks],
                "ranked",
                len(proof.comparison.options),
            )
            print(
                "Validation",
                proof.validation_status,
                "Apply",
                proof.applyable,
                "Publish",
                proof.publishable,
                "remaining",
                proof.pending_validators,
            )
        print("Before edit", check_day_driver_proposal_freshness(path, proof).status)
        approve(replacement, "Suspended")
        print(
            "After driver edit", check_day_driver_proposal_freshness(path, proof).status
        )


if __name__ == "__main__":
    main()
