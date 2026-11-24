"""Internal recording of company assertions; not authenticated safety certification."""

import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .availability import range_dates
from .capability_validation import (
    CapabilityRequirements,
    parse_payload,
    qualification_code,
)
from .recommendation_comparison import _positive_id
from .storage import connect


class CapabilityEvidenceConflict(ValueError):
    pass


def _decode(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate capability payload keys.")
            result[key] = value
        return result

    return json.loads(payload, object_pairs_hook=unique)


def identity(connection, scope, subject_id, code, *, create=False):
    _positive_id(subject_id)
    if scope not in ("WorkItem", "Employee"):
        raise ValueError(
            "Choose WorkItem requirements or Employee qualification evidence."
        )
    if scope == "Employee":
        qualification_code(code)
    elif code != "":
        raise ValueError("WorkItem policy has no qualification identity.")
    column, table = (
        ("WorkItemId", "WorkItems")
        if scope == "WorkItem"
        else ("EmployeeId", "Employees")
    )
    if (
        connection.execute(
            f"SELECT 1 FROM {table} WHERE Id=?", (subject_id,)
        ).fetchone()
        is None
    ):
        raise LookupError("The evidence subject no longer exists.")
    row = connection.execute(
        f"SELECT Id FROM CapabilityEvidenceOwners WHERE {column}=? AND Code=?",
        (subject_id, code),
    ).fetchone()
    if row:
        return row[0]
    if not create:
        return None
    return connection.execute(
        f"INSERT INTO CapabilityEvidenceOwners ({column},Code) VALUES (?,?)",
        (subject_id, code),
    ).lastrowid


def snapshot(connection, scope, subject_id, code, start, end):
    range_dates(start, end)
    owner_id = identity(connection, scope, subject_id, code)
    if owner_id is None:
        return dict(owner_id=None, revision=0, entries=[])
    revision = connection.execute(
        "SELECT coalesce(max(Revision),0) FROM CapabilityEvidenceChanges WHERE OwnerId=?",
        (owner_id,),
    ).fetchone()[0]
    entries, parsed = [], {}
    for row in connection.execute(
        """SELECT c.LocalDate,c.Slot,c.ChangeId,h.Payload,h.CompanyConfirmed,h.StartDate,h.EndDate,h.Slot,h.Reference
        FROM CapabilityEvidenceCells c JOIN CapabilityEvidenceChanges h ON h.Id=c.ChangeId
        WHERE c.OwnerId=? AND c.LocalDate BETWEEN ? AND ? ORDER BY c.LocalDate,c.Slot""",
        (owner_id, start, end),
    ):
        if (
            not row[5] <= row[0] <= row[6]
            or row[7] not in (row[1], "FullDay")
            or row[4] != 1
        ):
            raise ValueError("Malformed capability evidence context.")
        if row[2] not in parsed:
            parsed[row[2]] = parse_payload(_decode(row[3]), policy=scope == "WorkItem")
        entries.append(
            dict(
                local_date=row[0],
                slot=row[1],
                change_id=row[2],
                value=parsed[row[2]],
                company_confirmed=True,
                reference=row[8],
            )
        )
    return dict(owner_id=owner_id, revision=revision, entries=entries)


def qualification_snapshots(connection, employee_id, start, end):
    _positive_id(employee_id)
    codes = [
        r[0]
        for r in connection.execute(
            "SELECT Code FROM CapabilityEvidenceOwners WHERE EmployeeId=? ORDER BY Code",
            (employee_id,),
        ).fetchmany(100_001)
    ]
    if len(codes) > 100_000:
        raise ValueError("Qualification owner workload exceeded.")
    # Stream one owner at a time so the caller's aggregate read budget can stop
    # before materializing the next owner's cells.
    for code in codes:
        yield code, snapshot(connection, "Employee", employee_id, code, start, end)


class CapabilityEvidenceStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self, scope, subject_id, code, start, end):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            return snapshot(connection, scope, subject_id, code, start, end)

    def save(
        self,
        scope,
        subject_id,
        code,
        value,
        *,
        start_date,
        end_date,
        slot,
        company_confirmed,
        reference,
        expected_revision,
    ):
        days = range_dates(start_date, end_date)
        if slot not in ("AM", "PM", "FullDay") or company_confirmed is not True:
            raise ValueError("Explicitly confirm company evidence and AM/PM scope.")
        if (
            not isinstance(reference, str)
            or not 1 <= len(reference.strip()) <= 200
            or "\x00" in reference
        ):
            raise ValueError("Supply a bounded company evidence reference.")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("Reload the capability evidence revision.")
        if scope == "WorkItem":
            if not isinstance(value, CapabilityRequirements):
                raise ValueError(
                    "Supply explicit WorkItem requirements without defaults."
                )
            payload = value.payload()
        elif scope == "Employee":
            payload = {"version": 1, "state": value}
        else:
            raise ValueError("Invalid evidence scope.")
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        if len(encoded) > 20_000:
            raise ValueError("Capability payload exceeds workload limit.")
        # Validate exactly what will be persisted, without trusting arbitrary JSON.
        parse_payload(json.loads(encoded), policy=scope == "WorkItem")
        reference = reference.strip()
        cells = tuple(
            (day, half)
            for day in days
            for half in ("AM", "PM")
            if slot in (half, "FullDay")
        )
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            current = snapshot(
                connection, scope, subject_id, code, start_date, end_date
            )
            if current["revision"] != expected_revision:
                raise CapabilityEvidenceConflict(
                    "Capability evidence changed. Reload before saving."
                )
            target = parse_payload(json.loads(encoded), policy=scope == "WorkItem")
            existing = {
                (e["local_date"], e["slot"]): (e["value"], e["reference"])
                for e in current["entries"]
            }
            if all(existing.get(cell) == (target, reference) for cell in cells):
                return current
            owner_id = identity(connection, scope, subject_id, code, create=True)
            change_id = connection.execute(
                """INSERT INTO CapabilityEvidenceChanges
                (OwnerId,Revision,StartDate,EndDate,Slot,Payload,CompanyConfirmed,Reference,RecordedAt)
                VALUES (?,?,?,?,?,?,1,?,?)""",
                (
                    owner_id,
                    current["revision"] + 1,
                    start_date,
                    end_date,
                    slot,
                    encoded,
                    reference,
                    datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                ),
            ).lastrowid
            for day, half in cells:
                connection.execute(
                    """INSERT INTO CapabilityEvidenceCells VALUES (?,?,?,?)
                    ON CONFLICT(OwnerId,LocalDate,Slot) DO UPDATE SET ChangeId=excluded.ChangeId""",
                    (owner_id, day, half, change_id),
                )
            return snapshot(connection, scope, subject_id, code, start_date, end_date)

    def history(self, scope, subject_id, code):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN")
            owner_id = identity(connection, scope, subject_id, code)
            return [
                dict(
                    zip(
                        (
                            "id",
                            "revision",
                            "start_date",
                            "end_date",
                            "slot",
                            "payload",
                            "company_confirmed",
                            "reference",
                            "recorded_at",
                        ),
                        row,
                    )
                )
                for row in connection.execute(
                    """SELECT Id,Revision,StartDate,EndDate,Slot,Payload,CompanyConfirmed,Reference,RecordedAt
                        FROM CapabilityEvidenceChanges WHERE OwnerId=? ORDER BY Revision DESC LIMIT 100""",
                    (owner_id,),
                )
            ]
