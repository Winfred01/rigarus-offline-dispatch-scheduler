from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .assignments import AssignmentDraft
from .availability import range_dates
from .storage import connect
from .work_calendars import WorkCalendar, WorkCalendarCell, assess_project_calendar


class CalendarNotFound(ValueError):
    pass


class CalendarConflict(ValueError):
    pass


def owner(connection, scope, entity_id):
    if (
        scope not in ("Crew", "Project")
        or type(entity_id) is not int
        or not 1 <= entity_id <= 2**53 - 1
    ):
        raise ValueError("Select an existing Crew or Project calendar.")
    table, column = (
        ("Crews", "CrewId") if scope == "Crew" else ("Projects", "ProjectId")
    )
    if not connection.execute(
        f"SELECT Id FROM {table} WHERE Id=?", (entity_id,)
    ).fetchone():
        raise CalendarNotFound(
            "This Crew or Project no longer exists. Reload calendars."
        )
    row = connection.execute(
        f"SELECT Id FROM WorkingCalendars WHERE {column}=?", (entity_id,)
    ).fetchone()
    return (row[0] if row else None), column


def snapshot(connection, scope, entity_id, start, end):
    calendar_id, _ = owner(connection, scope, entity_id)
    revision = connection.execute(
        "SELECT coalesce(max(Revision),0) FROM WorkingCalendarChanges WHERE CalendarId=?",
        (calendar_id,),
    ).fetchone()[0]
    return {
        "scope": scope,
        "entity_id": entity_id,
        "revision": revision,
        "start_date": start,
        "end_date": end,
        "entries": [
            dict(zip(("local_date", "slot", "state"), row))
            for row in connection.execute(
                "SELECT LocalDate,Slot,State FROM WorkingCalendarCells WHERE CalendarId=? AND LocalDate BETWEEN ? AND ? ORDER BY LocalDate,Slot",
                (calendar_id, start, end),
            )
        ],
    }


def assessment(connection, draft):
    row = connection.execute(
        "SELECT ProjectId FROM WorkItems WHERE Id=?", (draft.work_item_id,)
    ).fetchone()
    if not row:
        raise CalendarNotFound("This WorkItem no longer exists. Reload projects.")
    project_id = row[0]
    crew = snapshot(
        connection, "Crew", draft.crew_id, draft.local_date, draft.local_date
    )
    project = snapshot(
        connection, "Project", project_id, draft.local_date, draft.local_date
    )
    result = asdict(
        assess_project_calendar(
            draft,
            WorkCalendar(
                "Crew",
                draft.crew_id,
                tuple(WorkCalendarCell(**e) for e in crew["entries"]),
            ),
            WorkCalendar(
                "Project",
                project_id,
                tuple(WorkCalendarCell(**e) for e in project["entries"]),
            ),
        )
    )
    return {
        **result,
        "crew_revision": crew["revision"],
        "project_revision": project["revision"],
    }


class WorkingCalendarStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self, scope, entity_id, start, end):
        range_dates(start, end)
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return snapshot(connection, scope, entity_id, start, end)

    def save(
        self, scope, entity_id, start_date, end_date, slot, state, expected_revision
    ):
        start, end = start_date, end_date
        dates = range_dates(start, end)
        if slot not in ("FullDay", "AM", "PM") or state not in (
            "Working",
            "NotWorking",
            "Unknown",
        ):
            raise ValueError(
                "Choose Full day/AM/PM and a recorded working-calendar state."
            )
        if (
            type(expected_revision) is not int
            or not 0 <= expected_revision <= 2**53 - 1
        ):
            raise ValueError("Reload the working calendar revision.")
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            current = snapshot(connection, scope, entity_id, start, end)
            if current["revision"] != expected_revision:
                raise CalendarConflict(
                    "Working calendar changed. Reload before saving again."
                )
            cells = tuple(
                (d, s)
                for d in dates
                for s in (("AM", "PM") if slot == "FullDay" else (slot,))
            )
            states = {
                (e["local_date"], e["slot"]): e["state"] for e in current["entries"]
            }
            if all(states.get(cell, "Unknown") == state for cell in cells):
                return current
            calendar_id, column = owner(connection, scope, entity_id)
            if calendar_id is None:
                calendar_id = connection.execute(
                    f"INSERT INTO WorkingCalendars({column}) VALUES (?)", (entity_id,)
                ).lastrowid
            change_id = connection.execute(
                """INSERT INTO WorkingCalendarChanges
                (CalendarId,Revision,StartDate,EndDate,Slot,State,RecordedAt) VALUES (?,?,?,?,?,?,?)""",
                (
                    calendar_id,
                    current["revision"] + 1,
                    start,
                    end,
                    slot,
                    state,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            ).lastrowid
            for day, half in cells:
                if state == "Unknown":
                    connection.execute(
                        "DELETE FROM WorkingCalendarCells WHERE CalendarId=? AND LocalDate=? AND Slot=?",
                        (calendar_id, day, half),
                    )
                else:
                    connection.execute(
                        """INSERT INTO WorkingCalendarCells(CalendarId,LocalDate,Slot,State,ChangeId)
                        VALUES (?,?,?,?,?) ON CONFLICT(CalendarId,LocalDate,Slot)
                        DO UPDATE SET State=excluded.State,ChangeId=excluded.ChangeId""",
                        (calendar_id, day, half, state, change_id),
                    )
            return snapshot(connection, scope, entity_id, start, end)

    def history(self, scope, entity_id):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            calendar_id, _ = owner(connection, scope, entity_id)
            return [
                dict(
                    zip(
                        (
                            "id",
                            "revision",
                            "start_date",
                            "end_date",
                            "slot",
                            "state",
                            "recorded_at",
                        ),
                        row,
                    )
                )
                for row in connection.execute(
                    "SELECT Id,Revision,StartDate,EndDate,Slot,State,RecordedAt FROM WorkingCalendarChanges WHERE CalendarId=? ORDER BY Revision DESC LIMIT 100",
                    (calendar_id,),
                )
            ]

    def assess(self, work_item_id, crew_id, day, slot):
        draft = AssignmentDraft(work_item_id, crew_id, day, slot)
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return assessment(connection, draft)
