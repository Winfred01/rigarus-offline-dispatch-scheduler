"""Transactional daily assertions and conservative, pinned legacy review receipts."""

import hashlib
import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .assignments import local_date
from .availability import range_dates
from .daily_calendars import DailyInput, states_for, resolve_daily, assess_daily
from .day_drafts import positive_id
from .storage import connect


class DailyNotFound(ValueError):
    pass


class DailyConflict(ValueError):
    pass


class DailySourceError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def owner(connection, scope, entity_id):
    states_for(scope)
    positive_id(entity_id)
    table, column = {
        "Crew": ("Crews", "CrewId"),
        "Project": ("Projects", "ProjectId"),
        "Employee": ("Employees", "EmployeeId"),
    }[scope]
    if not connection.execute(
        f"SELECT 1 FROM {table} WHERE Id=?", (entity_id,)
    ).fetchone():
        raise DailyNotFound(
            "This daily calendar owner no longer exists. Reload calendars."
        )
    row = connection.execute(
        f"SELECT Id FROM DailyCalendarOwners WHERE {column}=?", (entity_id,)
    ).fetchone()
    return row[0] if row else None, column


def legacy_source(connection, scope, entity_id, start, end):
    if scope == "Employee":
        identity = entity_id
        revision = connection.execute(
            "SELECT coalesce(max(Revision),0) FROM EmployeeAvailabilityChanges WHERE EmployeeId=?",
            (identity,),
        ).fetchone()[0]
        sql = """SELECT c.LocalDate,c.Slot,c.State,c.ChangeId,h.StartDate,h.EndDate,h.Slot,h.State,h.Revision
               FROM EmployeeAvailability c LEFT JOIN EmployeeAvailabilityChanges h ON h.Id=c.ChangeId AND h.EmployeeId=c.EmployeeId
               WHERE c.EmployeeId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate,c.Slot"""
    else:
        column = "CrewId" if scope == "Crew" else "ProjectId"
        row = connection.execute(
            f"SELECT Id FROM WorkingCalendars WHERE {column}=?", (entity_id,)
        ).fetchone()
        identity = row[0] if row else None
        revision = connection.execute(
            "SELECT coalesce(max(Revision),0) FROM WorkingCalendarChanges WHERE CalendarId=?",
            (identity,),
        ).fetchone()[0]
        sql = """SELECT c.LocalDate,c.Slot,c.State,c.ChangeId,h.StartDate,h.EndDate,h.Slot,h.State,h.Revision
               FROM WorkingCalendarCells c LEFT JOIN WorkingCalendarChanges h ON h.Id=c.ChangeId AND h.CalendarId=c.CalendarId
               WHERE c.CalendarId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate,c.Slot"""
    entries = []
    for row in connection.execute(sql, (identity, start, end)).fetchmany(733):
        day, half, state, change, first, last, range_half, history_state, native = row
        if (
            first is None
            or half not in ("AM", "PM")
            or state not in states_for(scope)[:2]
            or not first <= day <= last
            or range_half not in (half, "FullDay")
            or history_state != state
            or not 1 <= native <= revision
        ):
            raise DailySourceError(
                "Legacy evidence history/context is invalid. Needs Review."
            )
        entries.append(dict(local_date=day, slot=half, state=state, change_id=change))
    if len(entries) > 732:
        raise DailySourceError("Daily legacy input read limit exceeded.")
    return dict(
        scope=scope,
        entity_id=entity_id,
        revision=revision,
        start_date=start,
        end_date=end,
        entries=entries,
    )


def legacy_day_fingerprint(legacy, day):
    return digest(
        (
            legacy["scope"],
            legacy["entity_id"],
            legacy["revision"],
            day,
            [r for r in legacy["entries"] if r["local_date"] == day],
        )
    )


def snapshot(connection, scope, entity_id, start, end):
    """Connection-level read: caller owns one pinned transaction, never initializes."""
    dates = range_dates(start, end)
    owner_id, _ = owner(connection, scope, entity_id)
    revision = connection.execute(
        "SELECT coalesce(max(Revision),0) FROM DailyCalendarChanges WHERE OwnerId=?",
        (owner_id,),
    ).fetchone()[0]
    legacy = legacy_source(connection, scope, entity_id, start, end)
    rows = connection.execute(
        """SELECT c.LocalDate,c.State,c.ChangeId,c.LegacyFingerprint,
                  h.StartDate,h.EndDate,h.LegacyRevision,h.LegacyReviewed,h.Notes,h.Revision,h.OperatorConfirmed
             FROM DailyCalendarCells c LEFT JOIN DailyCalendarChanges h ON h.Id=c.ChangeId AND h.OwnerId=c.OwnerId AND h.State=c.State
             WHERE c.OwnerId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate""",
        (owner_id, start, end),
    ).fetchmany(367)
    if len(rows) > 366:
        raise DailySourceError("Daily input read limit exceeded.")
    by_day = {r[0]: r for r in rows}
    entries = []
    for day in dates:
        r = by_day.get(day)
        halves = [x for x in legacy["entries"] if x["local_date"] == day]
        if r and (
            r[4] is None
            or not r[4] <= day <= r[5]
            or r[1] not in states_for(scope)
            or not 1 <= r[9] <= revision
            or r[10] != 1
        ):
            raise DailySourceError(
                "Daily cell history/context is invalid. Needs Review."
            )
        stale = bool(
            r
            and (
                r[6] != legacy["revision"]
                or r[3] != legacy_day_fingerprint(legacy, day)
            )
        )
        entry = resolve_daily(
            scope,
            r[1] if r else None,
            halves,
            stale=stale,
            legacy_reviewed=bool(r and r[7]),
        )
        entries.append(
            dict(
                local_date=day,
                change_id=r[2] if r else None,
                notes=r[8] if r else "",
                **entry,
            )
        )
    token = digest(
        (
            "rigarus-daily-calendar-input-v1",
            scope,
            entity_id,
            start,
            end,
            revision,
            legacy,
            rows,
        )
    )
    return dict(
        scope=scope,
        entity_id=entity_id,
        start_date=start,
        end_date=end,
        revision=revision,
        legacy_revision=legacy["revision"],
        legacy_source=legacy,
        entries=entries,
        review_token=token,
        validation_status="Pending",
        applyable=False,
        publishable=False,
    )


def daily_assessment(connection, work_item_id, crew_id, day):
    positive_id(work_item_id)
    local_date(day)
    row = connection.execute(
        "SELECT ProjectId FROM WorkItems WHERE Id=?", (work_item_id,)
    ).fetchone()
    if not row:
        raise DailyNotFound("This WorkItem no longer exists. Reload projects.")
    crew = snapshot(connection, "Crew", crew_id, day, day)
    project = snapshot(connection, "Project", row[0], day, day)
    return dict(
        work_item_id=work_item_id,
        project_id=row[0],
        crew_id=crew_id,
        crew_revision=crew["revision"],
        project_revision=project["revision"],
        input_fingerprint=digest(
            (crew["review_token"], project["review_token"], work_item_id)
        ),
        **assess_daily(day, crew["entries"][0], project["entries"][0]),
    )


class DailyCalendarStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self, scope, entity_id, start, end):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            return snapshot(c, scope, entity_id, start, end)

    def assess(self, work_item_id, crew_id, day):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            return daily_assessment(c, work_item_id, crew_id, day)

    def save(
        self,
        scope,
        entity_id,
        draft: DailyInput,
        expected_revision: int,
        expected_review_token: str,
    ):
        if not isinstance(draft, DailyInput):
            raise ValueError("Supply an explicit slotless daily assertion.")
        if draft.state not in states_for(scope):
            raise ValueError("Daily state does not match its owner scope.")
        if (
            type(expected_revision) is not int
            or not 0 <= expected_revision <= 2**53 - 1
            or not isinstance(expected_review_token, str)
            or len(expected_review_token) != 64
        ):
            raise ValueError(
                "Reload the daily range revision and review token before saving."
            )
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            current = snapshot(c, scope, entity_id, draft.start_date, draft.end_date)
            if (
                current["revision"] != expected_revision
                or current["review_token"] != expected_review_token
            ):
                raise DailyConflict(
                    "Daily or legacy evidence changed. Reload and review this exact range before saving."
                )
            if current["legacy_source"]["entries"] and not draft.legacy_reviewed:
                raise DailyConflict(
                    "Legacy half-day evidence needs explicit review; no automatic daily conversion."
                )
            dates = range_dates(draft.start_date, draft.end_date)
            if all(
                e["recorded_state"] == draft.state
                and e["review_status"] == "Current"
                and e["notes"] == draft.notes
                and e["legacy_reviewed"] == draft.legacy_reviewed
                for e in current["entries"]
            ):
                return current
            owner_id, column = owner(c, scope, entity_id)
            if owner_id is None:
                owner_id = c.execute(
                    f"INSERT INTO DailyCalendarOwners({column}) VALUES(?)", (entity_id,)
                ).lastrowid
            encoded = json.dumps(
                current["legacy_source"], sort_keys=True, separators=(",", ":")
            )
            if len(encoded) > 250000:
                raise ValueError(
                    "Reviewed legacy snapshot exceeds the daily input limit."
                )
            change_id = c.execute(
                """INSERT INTO DailyCalendarChanges(OwnerId,Revision,StartDate,EndDate,State,OperatorConfirmed,
                    LegacyReviewed,LegacyRevision,LegacySnapshot,Notes,RecordedAt) VALUES(?,?,?,?,?,1,?,?,?,?,?)""",
                (
                    owner_id,
                    expected_revision + 1,
                    draft.start_date,
                    draft.end_date,
                    draft.state,
                    int(draft.legacy_reviewed),
                    current["legacy_revision"],
                    encoded,
                    draft.notes,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            ).lastrowid
            for day in dates:
                c.execute(
                    """INSERT INTO DailyCalendarCells(OwnerId,LocalDate,State,ChangeId,LegacyFingerprint) VALUES(?,?,?,?,?)
                    ON CONFLICT(OwnerId,LocalDate) DO UPDATE SET State=excluded.State,ChangeId=excluded.ChangeId,LegacyFingerprint=excluded.LegacyFingerprint""",
                    (
                        owner_id,
                        day,
                        draft.state,
                        change_id,
                        legacy_day_fingerprint(current["legacy_source"], day),
                    ),
                )
            return snapshot(c, scope, entity_id, draft.start_date, draft.end_date)

    def history(self, scope, entity_id):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            owner_id, _ = owner(c, scope, entity_id)
            rows = c.execute(
                "SELECT Id,Revision,StartDate,EndDate,State,LegacyReviewed,LegacyRevision,LegacySnapshot,Notes,RecordedAt FROM DailyCalendarChanges WHERE OwnerId=? ORDER BY Revision DESC LIMIT 100",
                (owner_id,),
            ).fetchall()
            result = []
            for r in rows:
                try:
                    reviewed = json.loads(r[7])
                except (ValueError, TypeError) as e:
                    raise DailySourceError(
                        "Recorded legacy review is invalid. Needs Review."
                    ) from e
                result.append(
                    dict(
                        zip(
                            (
                                "id",
                                "revision",
                                "start_date",
                                "end_date",
                                "state",
                                "legacy_reviewed",
                                "legacy_revision",
                                "legacy_snapshot",
                                "notes",
                                "recorded_at",
                            ),
                            (*r[:7], reviewed, *r[8:]),
                        )
                    )
                )
            return result
