"""Synthetic transaction, receipt and compatibility recovery contracts."""

import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

import test_schedule_workbench as fixtures
from migration_fixture import remove_day_editor_schema
from rigarus_backend.api import create_app
from rigarus_backend import storage
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_editor_api import EditorSave
from rigarus_backend.day_editor_store import submit
from rigarus_backend.recommendation_adapter import SnapshotReadError


class EditorTests(unittest.TestCase):
    daily = fixtures.WorkbenchTests.daily
    employee = fixtures.WorkbenchTests.employee
    calendar = fixtures.WorkbenchTests.calendar
    visit = fixtures.WorkbenchTests.visit

    def setUp(self):
        fixtures.WorkbenchTests.setUp(self)
        self.editor = TestClient(
            create_app(self.database, enable_day_editor_test_writes=True)
        )
        self.profile = self.editor.get("/day-editor/status").json()["profile_id"]

    def request_body(self, **changes):
        body = dict(
            profile_id=self.profile,
            request_id=str(uuid4()),
            action="Create",
            work_item_id=self.work.id,
            expected_project_id=self.project.id,
            crew_id=self.c1.id,
            local_date="2026-11-25",
            notes="Synthetic editor note",
            employee_ids=None,
            staffing_confirmed=False,
        )
        body.update(changes)
        return body

    def post(self, body):
        return self.editor.post("/day-editor/submit", json=body)

    def digest(self):
        with closing(storage.connect(self.database, read_only=True)) as c:
            return logical_digest(c)

    def test_closed_default_gate_and_read_only_status(self):
        before = self.digest()
        r = self.client.post("/day-editor/submit", json=self.request_body())
        self.assertEqual(r.status_code, 409)
        self.assertFalse(
            self.client.get("/day-editor/status").json()["test_writes_enabled"]
        )
        self.assertEqual(before, self.digest())

    def test_create_edit_cancel_notes_workers_history_and_reopen(self):
        worker = self.employee(home=self.c2.id)
        body = self.request_body(employee_ids=[worker.id], staffing_confirmed=True)
        r = self.post(body)
        self.assertEqual(r.status_code, 200, r.text)
        result = r.json()
        self.assertEqual(result["outcome"], "Committed")
        saved = result["record"]
        self.assertFalse(result["applyable"] or result["publishable"])
        self.assertEqual(saved["employee_ids"], [worker.id])
        edited = self.post(
            self.request_body(
                action="Edit",
                id=saved["id"],
                expected_revision=1,
                notes="Synthetic edited note",
                employee_ids=[worker.id],
                staffing_confirmed=True,
            )
        ).json()
        self.assertEqual(edited["record"]["id"], saved["id"])
        self.assertEqual(edited["record"]["revision"], 2)
        self.assertEqual(edited["record"]["employee_ids"], [worker.id])
        cancel = dict(
            profile_id=self.profile,
            request_id=str(uuid4()),
            action="Cancel",
            id=saved["id"],
            expected_revision=2,
        )
        cancelled = self.post(cancel).json()
        self.assertEqual(cancelled["record"]["status"], "Cancelled")
        self.assertEqual(
            DayDraftStore(self.database).read(saved["id"])["employee_ids"], (worker.id,)
        )
        history = self.editor.get(f"/day-editor/history/{saved['id']}").json()
        self.assertEqual([h["revision"] for h in history], [3, 2, 1])
        self.assertEqual([h["workers"][0][0] for h in history], [worker.id] * 3)
        receipt = self.editor.get(
            f"/day-editor/receipt/{self.profile}/{body['request_id']}"
        ).json()
        self.assertEqual(receipt, result)

    def test_unknown_lost_reply_replays_same_committed_row_once(self):
        body = self.request_body()
        first = self.post(body).json()  # Pretend caller lost this response.
        before = self.digest()
        self.assertEqual(self.post(body).json(), first)
        self.assertEqual(before, self.digest())
        changed = {**body, "notes": "Synthetic changed after unknown"}
        self.assertEqual(self.post(changed).json()["code"], "REQUEST_REUSED")
        self.assertEqual(before, self.digest())

    def test_concurrent_duplicate_request_commits_one_record_and_receipt(self):
        request = EditorSave(**self.request_body())
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: submit(self.database, request), range(2)))
        self.assertEqual(results[0], results[1])
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute("SELECT count(*) FROM DayEditorReceipts").fetchone()[0], 1
            )
            self.assertEqual(
                c.execute(
                    "SELECT count(*) FROM DayDraftAssignments WHERE LocalDate='2026-11-25'"
                ).fetchone()[0],
                1,
            )
        identity = results[0]["record"]["id"]
        edits = [
            EditorSave(
                **self.request_body(
                    action="Edit",
                    id=identity,
                    expected_revision=1,
                    notes="Synthetic concurrent " + suffix,
                )
            )
            for suffix in ("left", "right")
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda r: submit(self.database, r), edits))
        self.assertEqual({r["outcome"] for r in outcomes}, {"Committed", "Rejected"})
        self.assertEqual(DayDraftStore(self.database).read(identity)["revision"], 2)

    def test_receipt_storage_failure_rolls_back_then_same_request_recovers(self):
        body = self.request_body()
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticReceiptFailure BEFORE INSERT ON DayEditorReceipts BEGIN SELECT RAISE(ABORT,'Synthetic receipt storage error'); END"
            )
        before = self.digest()
        self.assertEqual(self.post(body).status_code, 503)
        self.assertEqual(self.digest(), before)
        with closing(storage.connect(self.database)) as c, c:
            c.execute("DROP TRIGGER SyntheticReceiptFailure")
        self.assertEqual(
            self.editor.get(
                f"/day-editor/receipt/{self.profile}/{body['request_id']}"
            ).json()["outcome"],
            "NotFound",
        )
        self.assertEqual(self.post(body).json()["outcome"], "Committed")

    def test_stale_revision_does_not_overwrite_and_retains_rejection_receipt(self):
        saved = self.post(self.request_body()).json()["record"]
        stale = self.request_body(
            action="Edit", id=saved["id"], expected_revision=9, notes="Synthetic stale"
        )
        result = self.post(stale).json()
        self.assertEqual(result["code"], "STALE_REVISION")
        self.assertEqual(self.post(stale).json(), result)
        self.assertEqual(
            DayDraftStore(self.database).read(saved["id"])["notes"],
            "Synthetic editor note",
        )

    def test_legacy_half_or_daily_occupancy_rejects_without_conversion(self):
        for crew, day in ((self.c2.id, "2026-11-24"), (self.c1.id, "2026-11-23")):
            r = self.post(self.request_body(crew_id=crew, local_date=day)).json()
            self.assertEqual(r["outcome"], "Rejected")
        old = self.client.get(f"/draft-assignments/{self.old.id}").json()
        self.assertEqual(old["notes"], self.old.notes)
        self.assertEqual(old["slot"], "PM")

    def test_feedback_failure_rolls_back_assignment_history_and_receipt(self):
        before = self.digest()
        body = self.request_body()
        with patch(
            "rigarus_backend.day_editor_store._week",
            side_effect=SnapshotReadError("private synthetic source"),
        ):
            r = self.post(body)
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("private synthetic source", r.text)
        self.assertEqual(before, self.digest())
        receipt = self.editor.get(
            f"/day-editor/receipt/{self.profile}/{body['request_id']}"
        ).json()
        self.assertEqual(receipt["outcome"], "NotFound")
        self.assertEqual(self.post(body).json()["outcome"], "Committed")

    def test_context_reconfirmation_and_explicit_empty_not_inferred(self):
        r = self.post(
            self.request_body(employee_ids=[], staffing_confirmed=False)
        ).json()
        self.assertEqual(r["code"], "STAFFING_RECONFIRM")
        r = self.post(
            self.request_body(employee_ids=[], staffing_confirmed=True)
        ).json()
        self.assertEqual(r["record"]["employee_ids"], [])
        self.assertEqual(r["observation"]["validation_status"], "Pending")
        self.assertTrue(
            any(c["state"] == "Pending" for c in r["observation"]["checks"])
        )

    def test_wrong_profile_rejects_and_unknown_receipt_never_claims_rejection(self):
        before = self.digest()
        r = self.post(self.request_body(profile_id=str(uuid4()))).json()
        self.assertEqual(r["code"], "WRONG_PROFILE")
        self.assertEqual(before, self.digest())
        r = self.editor.get(f"/day-editor/receipt/{self.profile}/{uuid4()}").json()
        self.assertEqual(r["outcome"], "NotFound")

    def test_receipt_and_identity_are_immutable(self):
        self.post(self.request_body())
        for sql in (
            "DELETE FROM DayEditorReceipts",
            "UPDATE DayEditorWorkspace SET ProfileId='x'",
        ):
            with closing(storage.connect(self.database)) as c, c:
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)

    def test_recorded_employee_conflict_remains_explicitly_blocked_draft(self):
        from rigarus_backend.day_drafts import DayDraft

        worker = self.employee(home=self.c1.id)
        DayDraftStore(self.database).save(
            DayDraft(
                self.work.id, self.c1.id, "2026-11-23", "Synthetic source", (worker.id,)
            ),
            self.day["id"],
            1,
        )
        r = self.post(
            self.request_body(
                crew_id=self.c2.id,
                local_date="2026-11-23",
                employee_ids=[worker.id],
                staffing_confirmed=True,
            )
        ).json()
        self.assertEqual(r["outcome"], "Committed")
        checks = {c["check"]: c for c in r["observation"]["checks"]}
        self.assertEqual(checks["PersonnelConflicts"]["state"], "Blocked")
        self.assertFalse(r["publishable"] or r["applyable"])

    def test_migration18_preserves_rows_verified_backup_and_failure_retry(self):
        with closing(storage.connect(self.database)) as c, c:
            remove_day_editor_schema(c)
            tables = [
                r[0]
                for r in c.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT GLOB 'sqlite_*' AND name<>'__EFMigrationsHistory'"
                )
            ]
            originals = {
                t: c.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables
            }
        before = self.digest()
        with patch.object(
            storage, "CREATE_DAY_EDITOR", ("SELECT invalid_synthetic_column",)
        ):
            with self.assertRaises(sqlite3.Error):
                storage.initialize_database(self.database)
        self.assertEqual(before, self.digest())
        backups = list(self.database.parent.glob("*.before-day-*.bak"))
        self.assertEqual(len(backups), 1)
        with closing(storage.connect(backups[0], read_only=True)) as c:
            self.assertEqual(logical_digest(c), before)
        storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c:
            for table, rows in originals.items():
                self.assertEqual(
                    c.execute(f'SELECT * FROM "{table}"').fetchall(), rows, table
                )
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(
            self.client.get(f"/draft-assignments/{self.old.id}").json()["notes"],
            self.old.notes,
        )
        self.assertEqual(
            DayDraftStore(self.database).read(self.day["id"])["notes"],
            "Synthetic daily note",
        )
        after = self.digest()
        storage.initialize_database(self.database)
        self.assertEqual(after, self.digest())
