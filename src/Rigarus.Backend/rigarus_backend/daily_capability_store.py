"""Internal explicit full-date company policy/proof recorder, no HTTP/UI writer."""

import json
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone

from .availability import range_dates
from .capability_validation import CapabilityRequirements, parse_payload
from .capability_store import identity, _decode
from .daily_calendar_store import digest, DailyConflict, DailySourceError
from .storage import connect


def decode_value(scope, payload):
    if payload == "null" and scope == "WorkItem":
        return None
    return parse_payload(_decode(payload), policy=scope == "WorkItem")


def encode_value(scope, value):
    if scope == "WorkItem":
        if value is not None and not isinstance(value, CapabilityRequirements):
            raise ValueError(
                "Supply complete explicit daily requirements or explicit None."
            )
        raw = value.payload() if value else None
    elif scope == "Employee":
        raw = {"version": 1, "state": value}
    else:
        raise ValueError("Choose WorkItem policy or Employee qualification.")
    encoded = json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded) > 20000:
        raise ValueError("Daily capability payload exceeds workload bound.")
    decode_value(scope, encoded)
    return encoded


@dataclass(frozen=True)
class DailyCapabilityInput:
    start_date: str
    end_date: str
    company_confirmed: bool
    full_day_confirmed: bool
    reference: str
    legacy_reviewed: bool = False

    def __post_init__(self):
        range_dates(self.start_date, self.end_date)
        if (
            self.company_confirmed is not True
            or self.full_day_confirmed is not True
            or type(self.legacy_reviewed) is not bool
        ):
            raise ValueError(
                "Explicit company/full-day confirmation and boolean legacy review required."
            )
        if (
            not isinstance(self.reference, str)
            or not 1 <= len(self.reference.strip()) <= 200
            or "\0" in self.reference
        ):
            raise ValueError("Supply a company reference of1 to200 characters.")
        object.__setattr__(self, "reference", self.reference.strip())


def _legacy(c, owner, scope, start, end):
    revision = c.execute(
        "SELECT coalesce(max(Revision),0) FROM CapabilityEvidenceChanges WHERE OwnerId=?",
        (owner,),
    ).fetchone()[0]
    rows = c.execute(
        """SELECT c.LocalDate,c.Slot,c.ChangeId,h.Payload,h.StartDate,h.EndDate,h.Slot,h.Revision,h.CompanyConfirmed
        FROM CapabilityEvidenceCells c LEFT JOIN CapabilityEvidenceChanges h ON h.Id=c.ChangeId AND h.OwnerId=c.OwnerId
        WHERE c.OwnerId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate,c.Slot""",
        (owner, start, end),
    ).fetchmany(733)
    if len(rows) > 732:
        raise DailySourceError("Legacy capability read limit exceeded.")
    entries = []
    for day, half, change, payload, first, last, slot, native, confirmed in rows:
        if (
            first is None
            or half not in ("AM", "PM")
            or not first <= day <= last
            or slot not in (half, "FullDay")
            or not 1 <= native <= revision
            or confirmed != 1
        ):
            raise DailySourceError("Legacy capability history/context invalid.")
        parse_payload(_decode(payload), policy=scope == "WorkItem")
        entries.append(
            dict(local_date=day, slot=half, change_id=change, payload=payload)
        )
    source = dict(owner_id=owner, revision=revision, entries=entries)
    if len(json.dumps(source, sort_keys=True, separators=(",", ":"))) > 250000:
        raise DailySourceError(
            "Retained legacy capability source exceeds workload bound."
        )
    return source


def _receipt(legacy, day):
    return digest(
        (
            legacy["owner_id"],
            legacy["revision"],
            day,
            [e for e in legacy["entries"] if e["local_date"] == day],
        )
    )


def snapshot(c, scope, subject_id, code, start, end):
    dates = range_dates(start, end)
    owner = identity(c, scope, subject_id, code)
    revision = c.execute(
        "SELECT coalesce(max(Revision),0) FROM DailyCapabilityChanges WHERE OwnerId=?",
        (owner,),
    ).fetchone()[0]
    legacy = _legacy(c, owner, scope, start, end)
    rows = c.execute(
        """SELECT c.LocalDate,c.ChangeId,c.LegacyFingerprint,h.StartDate,h.EndDate,h.Payload,h.LegacyRevision,h.LegacyReviewed,h.Reference,h.Revision,h.CompanyConfirmed,h.FullDayConfirmed
        FROM DailyCapabilityCells c LEFT JOIN DailyCapabilityChanges h ON h.Id=c.ChangeId AND h.OwnerId=c.OwnerId
        WHERE c.OwnerId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate""",
        (owner, start, end),
    ).fetchmany(367)
    if len(rows) > 366:
        raise DailySourceError("Daily capability read limit exceeded.")
    by_date = {r[0]: r for r in rows}
    entries = []
    for day in dates:
        r = by_date.get(day)
        old = tuple(e for e in legacy["entries"] if e["local_date"] == day)
        if r and (
            r[3] is None
            or not r[3] <= day <= r[4]
            or not 1 <= r[9] <= revision
            or r[10] != 1
            or r[11] != 1
        ):
            raise DailySourceError("Daily capability history/context invalid.")
        value = decode_value(scope, r[5]) if r else None
        stale = bool(
            r and (r[6] != legacy["revision"] or r[2] != _receipt(legacy, day))
        )
        current = bool(r and not stale and (not old or r[7]))
        negative = scope == "Employee" and any(
            decode_value(scope, e["payload"]) == "NotVerified" for e in old
        )
        payload = r[5] if current else None
        if scope == "Employee" and (
            value == "NotVerified"
            or (negative and (not current or value != "Verified"))
        ):
            payload = encode_value(scope, "NotVerified")
        entries.append(
            dict(
                local_date=day,
                payload=payload,
                recorded_payload=r[5] if r else None,
                change_id=r[1] if r else None,
                reference=r[8] if r else "",
                review_status="Stale"
                if stale
                else "Current"
                if current
                else "NeedsReview"
                if old
                else "NotRecorded",
                legacy_entries=old,
            )
        )
    return dict(
        scope=scope,
        subject_id=subject_id,
        code=code,
        owner_id=owner,
        revision=revision,
        start_date=start,
        end_date=end,
        legacy_source=legacy,
        entries=entries,
        review_token=digest(
            (
                "rigarus-daily-capability-v1",
                scope,
                subject_id,
                code,
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


class DailyCapabilityStore:
    def __init__(self, path):
        self.path = path

    def read(self, scope, subject_id, code, start, end):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            return snapshot(c, scope, subject_id, code, start, end)

    def save(
        self, scope, subject_id, code, value, draft, expected_revision, review_token
    ):
        if (
            not isinstance(draft, DailyCapabilityInput)
            or type(expected_revision) is not int
            or expected_revision < 0
            or not isinstance(review_token, str)
        ):
            raise ValueError(
                "Supply explicit daily evidence and reload its revision/token."
            )
        payload = encode_value(scope, value)
        with closing(connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            before = snapshot(
                c, scope, subject_id, code, draft.start_date, draft.end_date
            )
            if (
                before["revision"] != expected_revision
                or before["review_token"] != review_token
            ):
                raise DailyConflict(
                    "Capability evidence changed. Reload before saving."
                )
            if before["legacy_source"]["entries"] and not draft.legacy_reviewed:
                raise DailyConflict("Review retained half-day evidence explicitly.")
            if all(
                e["recorded_payload"] == payload
                and e["reference"] == draft.reference
                and e["review_status"] == "Current"
                for e in before["entries"]
            ):
                return before
            owner = identity(c, scope, subject_id, code, create=True)
            legacy = before["legacy_source"]
            # A newly created shared identity has no old evidence; receipt must
            # bind its actual stable ID, rather than the pre-creation None.
            legacy["owner_id"] = owner
            change = c.execute(
                """INSERT INTO DailyCapabilityChanges
                (OwnerId,Revision,StartDate,EndDate,Payload,CompanyConfirmed,FullDayConfirmed,LegacyReviewed,LegacyRevision,LegacySnapshot,Reference,RecordedAt)
                VALUES (?,?,?,?,?,1,1,?,?,?,?,?)""",
                (
                    owner,
                    expected_revision + 1,
                    draft.start_date,
                    draft.end_date,
                    payload,
                    int(draft.legacy_reviewed),
                    legacy["revision"],
                    json.dumps(legacy, sort_keys=True, separators=(",", ":")),
                    draft.reference,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            ).lastrowid
            for day in range_dates(draft.start_date, draft.end_date):
                c.execute(
                    """INSERT INTO DailyCapabilityCells VALUES (?,?,?,?) ON CONFLICT(OwnerId,LocalDate) DO UPDATE SET ChangeId=excluded.ChangeId,LegacyFingerprint=excluded.LegacyFingerprint""",
                    (owner, day, change, _receipt(legacy, day)),
                )
            return snapshot(
                c, scope, subject_id, code, draft.start_date, draft.end_date
            )

    def history(self, scope, subject_id, code):
        with closing(connect(self.path, read_only=True)) as c, c:
            c.execute("BEGIN")
            owner = identity(c, scope, subject_id, code)
            return tuple(
                c.execute(
                    "SELECT * FROM DailyCapabilityChanges WHERE OwnerId=? ORDER BY Revision DESC LIMIT 100",
                    (owner,),
                )
            )
