"""Reproducible temporary synthetic SQLite example, never a production profile."""

from pathlib import Path
from tempfile import TemporaryDirectory

from .storage import initialize_database
from .projects import ProjectDraft, WorkItemDraft, WorkType
from .project_store import ProjectStore
from .roster import CrewDraft
from .roster_store import CrewStore
from .daily_calendars import DailyInput
from .daily_calendar_store import DailyCalendarStore
from .day_drafts import ConfirmedRemainingDays
from .day_recommendation_adapter import (
    DayRecommendationQuery,
    build_day_recommendation_snapshot,
    generate_from_day_snapshot,
    check_day_snapshot_freshness,
)


def main():
    with TemporaryDirectory(prefix="rigarus-synthetic-day-") as temporary:
        path = Path(temporary) / "synthetic.db"
        initialize_database(path)  # Seed only; recommendation reads never initialize.
        project = ProjectStore(path).save(
            ProjectDraft(
                "SYN-DAY-28",
                "0028",
                "Synthetic day example",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 99)],
            )
        )
        crews = tuple(
            CrewStore(path).save(CrewDraft(f"Synthetic C{i}", "Civil")) for i in (1, 2)
        )
        store = DailyCalendarStore(path)

        def daily(scope, identity, start, end, state="Working"):
            raw = store.read(scope, identity, start, end)
            store.save(
                scope,
                identity,
                DailyInput(
                    start, end, state, True, False, "Synthetic explicit daily input"
                ),
                raw["revision"],
                raw["review_token"],
            )

        daily("Project", project.id, "2026-11-23", "2026-11-27")
        daily("Crew", crews[0].id, "2026-11-23", "2026-11-27", "NotWorking")
        for d in ("2026-11-23", "2026-11-27"):
            daily("Crew", crews[0].id, d, d)
        daily("Crew", crews[1].id, "2026-11-24", "2026-11-27")
        original = None
        for order in ("EarliestFinish", "EarliestStart"):
            query = DayRecommendationQuery(
                project.work_items[0].id,
                tuple(c.id for c in crews),
                ConfirmedRemainingDays(2, True),
                "2026-11-23",
                "2026-11-27",
                project.id,
                order,
            )
            snapshot = build_day_recommendation_snapshot(path, query)
            if original is None:
                original = snapshot
            result = generate_from_day_snapshot(snapshot)
            print(
                order,
                [o.option.crew_id for o in result.generated.comparison.options],
                result.generated.sort_basis,
            )
            for c in result.generated.candidates:
                print(
                    "Crew",
                    c.crew_id,
                    "start",
                    c.proposed_start_date,
                    "finish",
                    c.proposed_finish_date,
                    "allocated",
                    c.allocated_working_dates,
                    "unfilled",
                    c.unfilled_days,
                )
                print("Skipped", [(d.local_date, d.reasons) for d in c.skipped])
            print(
                "SHA256",
                snapshot.input_fingerprint,
                "freshness",
                check_day_snapshot_freshness(path, snapshot).status,
            )
            print(
                "Validation",
                result.validation_status,
                "Apply",
                result.applyable,
                "Publish",
                result.publishable,
            )
        daily("Crew", crews[0].id, "2026-11-25", "2026-11-26")
        print(
            "Earlier snapshot after calendar edit:",
            check_day_snapshot_freshness(path, original).status,
        )
        query = DayRecommendationQuery(
            project.work_items[0].id,
            (crews[0].id,),
            ConfirmedRemainingDays(4, True),
            "2026-11-23",
            "2026-11-27",
            project.id,
        )
        result = generate_from_day_snapshot(
            build_day_recommendation_snapshot(path, query)
        ).generated.candidates[0]
        print(
            "Confirmed4 days across Tuesday closure:",
            result.allocated_working_dates,
            "finished",
            result.proposed_finish_date,
        )


if __name__ == "__main__":
    main()
