"""Internal full-date company assertions, explicit legacy review, no HTTP writer."""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone

from .availability import range_dates, EmployeeNotFound
from .day_drafts import positive_id
from .driver_eligibility import DRIVER_STATES
from .daily_calendar_store import digest, DailyConflict, DailySourceError
from .storage import connect


@dataclass(frozen=True)
class DailyDriverApprovalDraft:
    start_date: str
    end_date: str
    state: str
    company_confirmed: bool
    full_day_confirmed: bool
    reference: str
    legacy_reviewed: bool = False
    notes: str = ""

    def __post_init__(self):
        range_dates(self.start_date, self.end_date)
        if self.state not in DRIVER_STATES:
            raise ValueError("Supply an explicit daily company driver state.")
        if self.company_confirmed is not True or self.full_day_confirmed is not True:
            raise ValueError(
                "Explicit company and full-day confirmations are required."
            )
        if type(self.legacy_reviewed) is not bool:
            raise ValueError("Declare legacy review explicitly.")
        if (
            not isinstance(self.reference, str)
            or not 1 <= len(self.reference.strip()) <= 200
            or "\x00" in self.reference
        ):
            raise ValueError("Supply a company reference of 1 to 200 characters.")
        if (
            not isinstance(self.notes, str)
            or len(self.notes) > 2000
            or "\x00" in self.notes
        ):
            raise ValueError("Supply notes of at most 2000 characters.")
        object.__setattr__(self, "reference", self.reference.strip())


def _legacy(c, employee_id, start, end):
    revision = c.execute(
        "SELECT coalesce(max(Revision),0) FROM DriverApprovalChanges WHERE EmployeeId=?",
        (employee_id,),
    ).fetchone()[0]
    entries = []
    rows = c.execute(
        """SELECT c.LocalDate,c.Slot,c.State,c.ChangeId,h.StartDate,h.EndDate,h.Slot,h.Revision,h.CompanyConfirmed
        FROM DriverApprovalCells c LEFT JOIN DriverApprovalChanges h
        ON h.Id=c.ChangeId AND h.EmployeeId=c.EmployeeId AND h.State=c.State
        WHERE c.EmployeeId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate,c.Slot""",
        (employee_id, start, end),
    ).fetchmany(733)
    if len(rows) > 732:
        raise DailySourceError("Legacy driver read limit exceeded.")
    for day, half, state, change, first, last, slot, native, confirmed in rows:
        if (
            first is None
            or half not in ("AM", "PM")
            or state not in DRIVER_STATES
            or not first <= day <= last
            or slot not in (half, "FullDay")
            or not 1 <= native <= revision
            or confirmed != 1
        ):
            raise DailySourceError("Legacy driver history/context is invalid.")
        entries.append(dict(local_date=day, slot=half, state=state, change_id=change))
    return dict(
        employee_id=employee_id,
        revision=revision,
        start_date=start,
        end_date=end,
        entries=entries,
    )


def _receipt(legacy, day):
    return digest(
        (
            legacy["employee_id"],
            legacy["revision"],
            day,
            [e for e in legacy["entries"] if e["local_date"] == day],
        )
    )


def snapshot(c, employee_id, start, end):
    """Caller owns pinned transaction/budget; never initialize or write."""
    positive_id(employee_id)
    dates = range_dates(start, end)
    if not c.execute("SELECT 1 FROM Employees WHERE Id=?", (employee_id,)).fetchone():
        raise EmployeeNotFound("This employee no longer exists.")
    revision = c.execute(
        "SELECT coalesce(max(Revision),0) FROM DailyDriverApprovalChanges WHERE EmployeeId=?",
        (employee_id,),
    ).fetchone()[0]
    legacy = _legacy(c, employee_id, start, end)
    rows = c.execute(
        """SELECT c.LocalDate,c.State,c.ChangeId,c.LegacyFingerprint,
        h.StartDate,h.EndDate,h.LegacyRevision,h.LegacyReviewed,h.Reference,h.Notes,h.Revision,h.CompanyConfirmed,h.FullDayConfirmed
        FROM DailyDriverApprovalCells c LEFT JOIN DailyDriverApprovalChanges h
        ON h.Id=c.ChangeId AND h.EmployeeId=c.EmployeeId AND h.State=c.State
        WHERE c.EmployeeId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate""",
        (employee_id, start, end),
    ).fetchmany(367)
    if len(rows) > 366:
        raise DailySourceError("Daily driver read limit exceeded.")
    by_date = {r[0]: r for r in rows}
    entries = []
    for day in dates:
        r = by_date.get(day)
        old = tuple(e for e in legacy["entries"] if e["local_date"] == day)
        if r and (
            r[4] is None
            or not r[4] <= day <= r[5]
            or r[1] not in DRIVER_STATES
            or not 1 <= r[10] <= revision
            or r[11] != 1
            or r[12] != 1
        ):
            raise DailySourceError("Daily driver history/context is invalid.")
        stale = bool(
            r and (r[6] != legacy["revision"] or r[3] != _receipt(legacy, day))
        )
        reviewed = bool(r and (not old or r[7]) and not stale)
        blocked = next(
            (e["state"] for e in old if e["state"] in ("Suspended", "Expired")), None
        )
        # Negative evidence is never silently cleared by a stale/unknown assertion.
        state = (
            r[1]
            if reviewed
            else r[1]
            if r and r[1] in ("Suspended", "Expired")
            else blocked or "Unverified"
        )
        if state == "Unverified" and blocked:
            state = blocked
        entries.append(
            dict(
                local_date=day,
                state=state,
                recorded_state=r[1] if r else None,
                change_id=r[2] if r else None,
                company_confirmed=reviewed,
                full_day_confirmed=reviewed,
                reference=r[8] if r else "",
                notes=r[9] if r else "",
                review_status="Stale"
                if stale
                else "Current"
                if reviewed
                else "NeedsReview"
                if old
                else "NotRecorded",
                legacy_entries=old,
                legacy_needs_review=bool(old),
            )
        )
    return dict(
        employee_id=employee_id,
        start_date=start,
        end_date=end,
        revision=revision,
        legacy_source=legacy,
        entries=entries,
        review_token=digest(
            (
                "rigarus-daily-driver-input-v1",
                employee_id,
                start,
                end,
                revision,
                legacy,
                rows,
            )
        ),
        validation_status="Pending",
        applyable=False,
        publishable=False,
    )


class DailyDriverApprovalStore:
    def __init__(self, path):
        self.path = path

    def read(self, employee_id, start, end):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            return snapshot(c, employee_id, start, end)

    def save(self, employee_id, draft, expected_revision, review_token):
        if not isinstance(draft, DailyDriverApprovalDraft):
            raise ValueError("Supply explicitly confirmed daily driver evidence.")
        if (
            type(expected_revision) is not int
            or expected_revision < 0
            or not isinstance(review_token, str)
        ):
            raise ValueError("Reload daily driver revision and review token.")
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            before = snapshot(c, employee_id, draft.start_date, draft.end_date)
            if (
                before["revision"] != expected_revision
                or before["review_token"] != review_token
            ):
                raise DailyConflict("Driver evidence changed. Reload before saving.")
            if before["legacy_source"]["entries"] and not draft.legacy_reviewed:
                raise DailyConflict(
                    "Review retained legacy driver evidence explicitly."
                )
            if all(
                e["recorded_state"] == draft.state
                and e["reference"] == draft.reference
                and e["notes"] == draft.notes
                and e["review_status"] == "Current"
                for e in before["entries"]
            ):
                return before
            legacy = before["legacy_source"]
            import json

            change = c.execute(
                """INSERT INTO DailyDriverApprovalChanges
                (EmployeeId,Revision,StartDate,EndDate,State,CompanyConfirmed,FullDayConfirmed,LegacyReviewed,LegacyRevision,LegacySnapshot,Reference,Notes,RecordedAt)
                VALUES (?,?,?,?,?,1,1,?,?,?,?,?,?)""",
                (
                    employee_id,
                    expected_revision + 1,
                    draft.start_date,
                    draft.end_date,
                    draft.state,
                    int(draft.legacy_reviewed),
                    legacy["revision"],
                    json.dumps(legacy, sort_keys=True, separators=(",", ":")),
                    draft.reference,
                    draft.notes,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            ).lastrowid
            for day in range_dates(draft.start_date, draft.end_date):
                c.execute(
                    """INSERT INTO DailyDriverApprovalCells VALUES (?,?,?,?,?)
                    ON CONFLICT(EmployeeId,LocalDate) DO UPDATE SET State=excluded.State,ChangeId=excluded.ChangeId,LegacyFingerprint=excluded.LegacyFingerprint""",
                    (employee_id, day, draft.state, change, _receipt(legacy, day)),
                )
            return snapshot(c, employee_id, draft.start_date, draft.end_date)

    def history(self, employee_id):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            snapshot(c, employee_id, "0001-01-01", "0001-01-01")
            return tuple(
                c.execute(
                    "SELECT * FROM DailyDriverApprovalChanges WHERE EmployeeId=? ORDER BY Revision DESC LIMIT 100",
                    (employee_id,),
                )
            )
