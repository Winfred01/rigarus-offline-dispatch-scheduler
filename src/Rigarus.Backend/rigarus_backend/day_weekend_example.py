"""Synthetic T06 console preview; local temporary profile, never employee contact."""

from pathlib import Path
from tempfile import TemporaryDirectory

from .storage import initialize_database
from .projects import ProjectDraft, WorkItemDraft, WorkType
from .project_store import ProjectStore
from .roster import CrewDraft, EmployeeDraft
from .roster_store import CrewStore, EmployeeStore
from .daily_calendar_store import DailyCalendarStore
from .daily_calendars import DailyInput
from .day_drafts import ConfirmedRemainingDays
from .daily_weekend_consent import WeekendContext, WeekendCrewDay
from .daily_weekend_store import WeekendConsentStore, WeekendDecision
from .day_recommendation_adapter import (
    DayRecommendationQuery,
    build_day_recommendation_snapshot,
    generate_from_day_snapshot,
    check_day_snapshot_freshness,
)


def main():
    with TemporaryDirectory(prefix="rigarus-synthetic-consent-") as temporary:
        path = Path(temporary) / "synthetic.db"
        initialize_database(path)
        project = ProjectStore(path).save(
            ProjectDraft(
                "SYN-CONSENT-27",
                "0027",
                "Synthetic consent site",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 99)],
            )
        )
        crew = CrewStore(path).save(CrewDraft("Synthetic weekend Crew", "Civil"))
        workers = tuple(
            EmployeeStore(path)
            .save(EmployeeDraft(f"Synthetic worker {i}", crew.id, 2, False))
            .id
            for i in (1, 2)
        )
        start, end, saturday = "2026-11-27", "2026-11-30", "2026-11-28"
        calendars = DailyCalendarStore(path)
        for scope, identity in (("Crew", crew.id), ("Project", project.id)):
            old = calendars.read(scope, identity, start, end)
            calendars.save(
                scope,
                identity,
                DailyInput(start, end, "Working", True),
                old["revision"],
                old["review_token"],
            )
        query = DayRecommendationQuery(
            project.work_items[0].id,
            (crew.id,),
            ConfirmedRemainingDays(2, True),
            start,
            end,
            weekend_members=(WeekendCrewDay(crew.id, saturday, workers),),
        )
        context = WeekendContext(
            project.work_items[0].id, project.id, crew.id, saturday, workers
        )
        store = WeekendConsentStore(path)
        first = build_day_recommendation_snapshot(path, query)
        for label, person, state, revision in (
            ("Pending", None, None, 0),
            ("Partial", workers[0], "Confirmed", 0),
            ("Declined", workers[1], "Declined", 0),
            ("All confirmed", workers[1], "Confirmed", 1),
        ):
            if person is not None:
                store.save_planned(
                    context,
                    person,
                    WeekendDecision(state, True, True, "Synthetic employee decision"),
                    revision,
                )
            snapshot = build_day_recommendation_snapshot(path, query)
            result = generate_from_day_snapshot(snapshot)
            candidate = result.generated.candidates[0]
            print(
                label,
                "consent:",
                result.planned_weekend_validation.state,
                "dates:",
                candidate.allocated_working_dates,
                "finish:",
                candidate.proposed_finish_date,
                "validation:",
                result.validation_status,
                "Apply:",
                result.applyable,
                "Publish:",
                result.publishable,
            )
            print("Skipped:", [(d.local_date, d.reasons) for d in candidate.skipped])
        print("Original input:", check_day_snapshot_freshness(path, first).status)
        print(
            "Consent is not staffing, resource approval, employee authentication or Apply."
        )


if __name__ == "__main__":
    main()
