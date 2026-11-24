"""Synthetic, reproducible internal example: python -m rigarus_backend.recommendation_example.

This console example is not wired into the desktop/sidecar. No real records,
database, current clock, employee attendance or resource approval are used.
"""

from dataclasses import replace

from .recommendation_generator import GenerationRequest, generate_and_compare
from .work_calendars import WorkCalendar, WorkCalendarCell


def synthetic_requests() -> tuple[GenerationRequest, ...]:
    c1 = (
        ("2026-11-23", "AM"),
        ("2026-11-25", "PM"),
        ("2026-11-26", "AM"),
        ("2026-11-27", "PM"),
    )
    c2 = (
        ("2026-11-24", "AM"),
        ("2026-11-24", "PM"),
        ("2026-11-25", "AM"),
        ("2026-11-25", "PM"),
    )
    project = WorkCalendar(
        "Project",
        6,
        tuple(
            WorkCalendarCell(day, half, "Working") for day, half in sorted(set(c1 + c2))
        ),
    )
    first = GenerationRequest(
        option_id=1,
        work_item_id=14,
        project_id=6,
        crew_id=1,
        required_crew_count=1,
        confirmed_remaining_half_days=4,
        remaining_confirmed_by_operator=True,
        earliest_start_date="2026-11-23",
        horizon_end_date="2026-11-27",
        crew_calendar=WorkCalendar(
            "Crew", 1, tuple(WorkCalendarCell(day, half, "Working") for day, half in c1)
        ),
        project_calendar=project,
    )
    return first, replace(
        first,
        option_id=2,
        crew_id=2,
        crew_calendar=WorkCalendar(
            "Crew", 2, tuple(WorkCalendarCell(day, half, "Working") for day, half in c2)
        ),
    )


def main():
    for order in ("EarliestFinish", "EarliestStart"):
        result = generate_and_compare(
            14, 6, synthetic_requests(), max_options=3, order=order
        )
        print(order, [f"C{x.option.crew_id}" for x in result.comparison.options])
        print("Sort:", " -> ".join(result.sort_basis))
        for evaluated in result.comparison.options:
            candidate = next(
                x
                for x in result.candidates
                if x.option_id == evaluated.option.option_id
            )
            print(
                f"C{candidate.crew_id}: {candidate.proposed_start} -> {candidate.proposed_finish}; {candidate.generated_half_days}/{candidate.confirmed_remaining_half_days}; {candidate.status}; applyable={candidate.applyable}; publishable={candidate.publishable}"
            )
            print("Accumulated:", [(x.local_date, x.slot) for x in candidate.slots])
            print(
                "Skipped:",
                [
                    (x.calendar.local_date, x.calendar.slot, x.reasons)
                    for x in candidate.skipped
                ],
            )
            print(
                "Pending checks:", sorted({x.check for x in candidate.missing_evidence})
            )


if __name__ == "__main__":
    main()
