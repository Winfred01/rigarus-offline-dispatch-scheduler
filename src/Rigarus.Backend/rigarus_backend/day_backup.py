"""Verified consistent pre-upgrade backup; never an in-place downgrade."""

import hashlib
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path


def logical_digest(connection, *, deadline=None):
    digest = hashlib.sha256()
    count = 0
    byte_count = 0
    schema = connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"
    ).fetchall()
    digest.update(repr(schema).encode())
    for (name,) in connection.execute(
        "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"
    ):
        digest.update(name.encode())
        quoted = '"' + name.replace('"', '""') + '"'
        # Sorting by values retains duplicate rows and storage types.
        rows = []
        for row in connection.execute(f"SELECT * FROM {quoted}"):
            count += 1
            encoded = repr(row)
            byte_count += len(encoded.encode())
            if count > 1_000_000 or byte_count > 128 * 1024 * 1024:
                raise sqlite3.OperationalError(
                    "Backup verification workload limit exceeded."
                )
            if deadline is not None and time.monotonic() > deadline:
                raise sqlite3.OperationalError("Backup verification deadline exceeded.")
            rows.append(encoded)
        for row in sorted(rows):
            digest.update((str(len(row)) + ":" + row).encode())
    return digest.hexdigest()


def verified_upgrade_backup(path: Path):
    """Caller holds BEGIN IMMEDIATE, before any DDL on the source."""
    backup = path.with_name(path.name + ".before-day-" + uuid.uuid4().hex + ".bak")
    deadline = time.monotonic() + 30

    def progress(_status, _remaining, _total):
        if time.monotonic() > deadline:
            raise sqlite3.OperationalError("Pre-upgrade backup deadline exceeded.")

    # Exclusive creation: never overwrite a previous recovery point.
    with backup.open("xb"):
        pass
    try:
        with (
            closing(
                sqlite3.connect(
                    path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5
                )
            ) as source,
            closing(sqlite3.connect(backup)) as target,
        ):
            source.execute("PRAGMA query_only=ON")
            source.execute("BEGIN")
            original = logical_digest(
                source, deadline=deadline
            )  # Pins the source before copying WAL pages.
            source.backup(target, pages=256, progress=progress, sleep=0.01)
            if (
                target.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
                or target.execute("PRAGMA foreign_key_check").fetchone() is not None
            ):
                raise sqlite3.DatabaseError(
                    "The pre-upgrade backup failed integrity verification."
                )
            if logical_digest(target, deadline=deadline) != original:
                raise sqlite3.DatabaseError(
                    "The pre-upgrade backup differs from its source."
                )
        return backup
    except BaseException:
        backup.unlink(missing_ok=True)  # Only this exclusively created incomplete file.
        raise
