"""Synthetic operator-confirmed transaction, audit and inverse-preview evidence."""

import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

import test_impact_preview as fixtures
from migration_fixture import remove_draft_version_schema
from rigarus_backend import storage, draft_apply
from rigarus_backend.api import create_app
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.draft_apply_api import ConfirmDraft
from rigarus_backend.recommendation_adapter import SnapshotReadError


class TransactionTests(unittest.TestCase):
    calendar = fixtures.ImpactTests.calendar
    visit = fixtures.ImpactTests.visit
    employee = fixtures.ImpactTests.employee
    daily = fixtures.ImpactTests.daily
    approve = fixtures.ImpactTests.approve
    save_policy = fixtures.ImpactTests.save_policy
    rig = fixtures.ImpactTests.rig
    allocate = fixtures.ImpactTests.allocate

    def setUp(self):
        fixtures.ImpactTests.setUp(self)
        self.writer = TestClient(
            create_app(self.database, enable_draft_transaction_test_writes=True)
        )
        self.plan = dict(
            query=self.body | dict(replacements=self.scope), selected_crew_id=self.c1.id
        )

    def prepare(self, **changes):
        r = self.client.post("/draft-transactions/prepare", json=self.plan | changes)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def request(self, plan=None):
        proof = self.prepare() if plan is None else plan
        return dict(
            plan=self.plan,
            profile_id=proof["database_identity"],
            request_id=str(uuid4()),
            plan_fingerprint=proof["plan_fingerprint"],
            confirmed=True,
            pending_acknowledged=True,
        )

    def post(self, body):
        return self.writer.post("/draft-transactions/submit", json=body)

    def digest(self):
        with closing(storage.connect(self.database, read_only=True)) as c:
            return logical_digest(c)

    def test_prepare_default_gate_cancel_no_writes(self):
        original = self.digest()
        proof = self.prepare()
        self.assertEqual(len(proof["proposed"]), 8)
        self.assertTrue(proof["warnings"]["checks"])
        self.assertIn("Unsupported", proof["warnings"]["locks"])
        request = self.request(proof)
        self.assertEqual(
            self.client.post("/draft-transactions/submit", json=request).status_code,
            409,
        )
        self.assertEqual(original, self.digest())

    def test_extension_retains_ids_notes_histories_and_reopens(self):
        body = self.request()
        r = self.post(body)
        self.assertEqual(r.status_code, 200, r.text)
        result = r.json()
        self.assertEqual(len(result["after"]), 8)
        for i, old in enumerate(self.days):
            self.assertEqual(result["after"][i]["id"], old["id"])
            self.assertEqual(result["after"][i]["revision"], 1)
            self.assertEqual(result["after"][i]["notes"], old["notes"])
        self.assertEqual(result["validation_status"], "Pending")
        self.assertFalse(result["applyable"] or result["publishable"])
        with TestClient(create_app(self.database)) as restarted:
            reread = restarted.get(
                f"/draft-transactions/receipt/{body['profile_id']}/{body['request_id']}"
            )
            self.assertEqual(reread.json(), result)
            self.assertEqual(
                restarted.get(
                    f"/draft-transactions/version/{body['profile_id']}/1"
                ).json(),
                result,
            )
        self.assertEqual(
            len(DayDraftStore(self.database).list("2026-11-23", "2026-12-04")), 8
        )

    def test_early_finish_cancels_without_deleting_and_inverse_is_readonly(self):
        self.plan["query"]["remaining_days"] = 2
        body = self.request()
        r = self.post(body)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(sum(x["status"] == "Cancelled" for x in r.json()["after"]), 3)
        original = self.digest()
        inverse = self.client.get(
            f"/draft-transactions/recovery-preview/{body['profile_id']}/1"
        ).json()
        self.assertEqual(inverse["status"], "Current")
        self.assertFalse(inverse["restore_enabled"])
        self.assertEqual(
            sum(x["status"] == "Draft" for x in inverse["proposed_restore"]), 5
        )
        self.assertEqual(original, self.digest())
        for a in self.days[2:]:
            history = DayDraftStore(self.database).history(a["id"])
            self.assertEqual([h["revision"] for h in history], [2, 1])

    def test_replay_lost_response_exactly_once_and_mismatch(self):
        body = self.request()
        committed = self.post(body).json()
        original = self.digest()
        self.assertEqual(self.post(body).json(), committed)
        other = json.loads(json.dumps(body))
        other["plan"]["notes"] = "Different synthetic payload"
        self.assertEqual(self.post(other).status_code, 409)
        self.assertEqual(original, self.digest())

    def test_explicit_confirmation_and_acknowledgement_required(self):
        body = self.request()
        original = self.digest()
        for key in ("confirmed", "pending_acknowledged"):
            r = self.post(body | {key: False})
            self.assertEqual(r.status_code, 409)
            self.assertEqual(self.post(body | {key: "true"}).status_code, 422)
        self.assertEqual(original, self.digest())

    def test_wrong_database_and_tampered_proof_no_write(self):
        body = self.request()
        original = self.digest()
        for fields in (
            dict(profile_id=str(uuid4())),
            dict(plan_fingerprint="0" * 64),
            dict(plan=self.plan | dict(notes="Unreviewed edit")),
        ):
            self.assertEqual(self.post(body | fields).status_code, 409)
        self.assertEqual(original, self.digest())

    def test_stale_source_note_and_calendar_changes_reject(self):
        body = self.request()
        old = self.days[0]
        DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, old["local_date"], "Other edit"),
            old["id"],
            1,
        )
        original = self.digest()
        self.assertEqual(self.post(body).status_code, 409)
        self.assertEqual(original, self.digest())

    def test_change_outside_selected_scope_stales(self):
        body = self.request()
        self.visit(crew=self.c2.id, day="2026-11-26", half="AM")
        original = self.digest()
        self.assertEqual(self.post(body).status_code, 409)
        self.assertEqual(original, self.digest())

    def test_legacy_same_integer_id_protected_not_converted(self):
        legacy = self.visit(day="2026-12-01", half="PM")
        body = self.request()
        r = self.post(body)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn("2026-12-01", [x["local_date"] for x in r.json()["after"]])
        with closing(storage.connect(self.database)) as c:
            row = c.execute(
                "SELECT Slot,Revision,Status FROM DraftAssignments WHERE Id=?",
                (legacy.id,),
            ).fetchone()
            self.assertEqual(row, ("PM", 1, "Draft"))

    def test_known_personnel_conflict_refuses_even_with_ack(self):
        worker = self.employee()
        legacy = self.visit(crew=self.c2.id, day="2026-11-23", half="PM")
        from rigarus_backend.staffing_store import StaffingStore

        StaffingStore(self.database).save(legacy.id, (worker.id,), legacy.revision)
        self.plan["query"]["proposed_employee_ids"] = [worker.id]
        original = self.digest()
        r = self.client.post("/draft-transactions/prepare", json=self.plan)
        self.assertEqual(r.status_code, 409, r.text)
        self.assertEqual(original, self.digest())

    def test_actual_rig_nominee_never_written(self):
        self.plan["query"]["proposed_rig_id"] = self.rig().id
        original = self.digest()
        self.assertEqual(
            self.client.post("/draft-transactions/prepare", json=self.plan).status_code,
            409,
        )
        self.assertEqual(original, self.digest())

    def test_source_read_failure_not_false_commit(self):
        body = self.request()
        original = self.digest()
        with patch.object(
            draft_apply, "impact_in", side_effect=SnapshotReadError("SYNTHETIC_FAULT")
        ):
            self.assertEqual(self.post(body).status_code, 503)
        self.assertEqual(original, self.digest())

    def test_mid_write_failure_rolls_back_all_records_and_history(self):
        self.plan["query"]["remaining_days"] = 2
        body = self.request()
        original = self.digest()
        method = DayDraftStore.cancel_in
        calls = 0

        def fail(store, *args):
            nonlocal calls
            result = method(store, *args)
            calls += 1
            if calls == 2:
                raise sqlite3.OperationalError("Synthetic write fault")
            return result

        with patch.object(DayDraftStore, "cancel_in", fail):
            self.assertEqual(self.post(body).status_code, 503)
        self.assertEqual(calls, 2)
        self.assertEqual(original, self.digest())

    def test_audit_failure_rolls_back_even_successful_draft_rows(self):
        with closing(storage.connect(self.database)) as c, c:
            c.execute(
                "CREATE TRIGGER SyntheticAuditFault BEFORE INSERT ON DraftVersions BEGIN SELECT RAISE(ABORT,'Synthetic fault'); END"
            )
        body = self.request()
        original = self.digest()
        self.assertEqual(self.post(body).status_code, 503)
        self.assertEqual(original, self.digest())

    def test_final_resource_read_failure_rolls_back(self):
        body = self.request()
        original = self.digest()
        with patch.object(
            draft_apply, "_week", side_effect=SnapshotReadError("SYNTHETIC_FINAL_FAULT")
        ):
            self.assertEqual(self.post(body).status_code, 503)
        self.assertEqual(original, self.digest())

    def test_two_concurrent_keys_only_one_commits(self):
        body = self.request()
        other = body | dict(request_id=str(uuid4()))
        barrier = threading.Barrier(2)

        def run(b):
            barrier.wait()
            try:
                draft_apply.submit(self.database, ConfirmDraft(**b))
                return "Committed"
            except draft_apply.DraftRejected:
                return "Stale"

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(run, (body, other)))
        self.assertEqual(sorted(outcomes), ["Committed", "Stale"])
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute("SELECT count(*) FROM DraftVersions").fetchone()[0], 1
            )

    def test_same_key_concurrent_replays_exact_result(self):
        body = self.request()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    lambda _: draft_apply.submit(self.database, ConfirmDraft(**body)),
                    range(2),
                )
            )
        self.assertEqual(results[0], results[1])

    def test_recovery_stale_after_subsequent_edit_and_unknown_receipt(self):
        body = self.request()
        result = self.post(body).json()
        row = result["after"][0]
        DayDraftStore(self.database).save(
            DayDraft(
                row["work_item_id"],
                row["crew_id"],
                row["local_date"],
                "Later operator edit",
            ),
            row["id"],
            row["revision"],
        )
        original = self.digest()
        inverse = self.client.get(
            f"/draft-transactions/recovery-preview/{body['profile_id']}/1"
        ).json()
        self.assertEqual(inverse["status"], "Stale")
        unknown = self.client.get(
            f"/draft-transactions/receipt/{body['profile_id']}/{uuid4()}"
        ).json()
        self.assertEqual(unknown["outcome"], "NotFound")
        self.assertIn("not proof", unknown["retry_instruction"])
        self.assertEqual(original, self.digest())

    def test_audit_immutable_integrity_and_foreign_keys(self):
        self.assertEqual(self.post(self.request()).status_code, 200)
        with closing(storage.connect(self.database)) as c:
            for sql in (
                "DELETE FROM DraftVersions",
                "UPDATE DraftVersions SET PlanSha='x'",
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(sql)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_migration_preserves_legacy_and_ids_and_reopens(self):
        self.visit(day="2026-12-01", half="AM")
        with closing(storage.connect(self.database)) as c, c:
            remove_draft_version_schema(c)
            original = logical_digest(c)
            rows = list(c.execute("SELECT * FROM DayDraftAssignments"))
        storage.initialize_database(self.database)
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(list(c.execute("SELECT * FROM DayDraftAssignments")), rows)
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        current = self.digest()
        storage.initialize_database(self.database)
        self.assertEqual(current, self.digest())
        backups = list(self.database.parent.glob("*.before-day-*.bak"))
        self.assertTrue(backups)
        # The backup is a verified19 profile, before adding only the new table.
        with closing(sqlite3.connect(backups[-1])) as c:
            self.assertEqual(logical_digest(c), original)

    def test_migration_failure_whole_rollback_retry(self):
        with closing(storage.connect(self.database)) as c, c:
            remove_draft_version_schema(c)
        original = self.digest()
        with patch.object(
            storage,
            "CREATE_DRAFT_VERSIONS",
            (*storage.CREATE_DRAFT_VERSIONS, "SELECT synthetic_missing"),
        ):
            with self.assertRaises(sqlite3.OperationalError):
                storage.initialize_database(self.database)
        self.assertEqual(original, self.digest())
        storage.initialize_database(self.database)
        self.assertEqual(self.prepare()["status"], "Current")

    def test_invalid_inputs_never_reach_transaction(self):
        original = self.digest()
        for q in (
            dict(remaining_days=0.5),
            dict(remaining_confirmed=False),
            dict(replacements=[self.scope[0], self.scope[0]]),
        ):
            r = self.client.post(
                "/draft-transactions/prepare",
                json=self.plan | dict(query=self.plan["query"] | q),
            )
            self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(original, self.digest())

    def test_explicit_members_and_notes_are_reviewed_exactly(self):
        worker = self.employee()
        self.plan["query"]["remaining_days"] = 1
        self.plan["query"]["proposed_employee_ids"] = [worker.id]
        self.plan["notes"] = "Synthetic reviewed note"
        proof = self.prepare()
        self.assertEqual(proof["proposed"][0]["employee_ids"], [worker.id])
        result = self.post(self.request(proof))
        self.assertEqual(result.status_code, 200, result.text)
        active = next(r for r in result.json()["after"] if r["status"] == "Draft")
        self.assertEqual(active["employee_ids"], [worker.id])
        self.assertEqual(active["notes"], "Synthetic reviewed note")
        self.assertEqual(active["revision"], 2)
        self.assertTrue(result.json()["plan"]["warnings"]["checks"])

    def test_known_driver_negative_refuses_pending_override(self):
        worker = self.employee()
        self.daily("Employee", worker.id, state="Available")
        self.approve(worker, state="Suspended")
        self.plan["query"].update(remaining_days=1, proposed_employee_ids=[worker.id])
        original = self.digest()
        self.assertEqual(
            self.client.post("/draft-transactions/prepare", json=self.plan).status_code,
            409,
        )
        self.assertEqual(original, self.digest())

    def test_known_minimum_and_level_shortage_refuses(self):
        from rigarus_backend.capability_validation import CapabilityRequirements

        worker = self.employee()
        self.daily("Employee", worker.id, state="Available")
        self.save_policy(
            "WorkItem",
            self.work.id,
            CapabilityRequirements(2, (1, 0, 0), "Exact", (("SYN-Q", 1),)),
        )
        self.plan["query"].update(remaining_days=1, proposed_employee_ids=[worker.id])
        original = self.digest()
        self.assertEqual(
            self.client.post("/draft-transactions/prepare", json=self.plan).status_code,
            409,
        )
        self.assertEqual(original, self.digest())

    def test_unavailable_employee_cannot_be_acknowledged_away(self):
        worker = self.employee()
        self.daily("Employee", worker.id, state="Unavailable")
        self.plan["query"].update(remaining_days=1, proposed_employee_ids=[worker.id])
        original = self.digest()
        self.assertEqual(
            self.client.post("/draft-transactions/prepare", json=self.plan).status_code,
            409,
        )
        self.assertEqual(original, self.digest())

    def test_weekend_unknown_cannot_create_capacity(self):
        self.plan["query"].update(
            remaining_days=1,
            replacements=[],
            earliest_start_date="2026-11-28",
            horizon_end_date="2026-11-29",
        )
        original = self.digest()
        self.assertEqual(
            self.client.post("/draft-transactions/prepare", json=self.plan).status_code,
            409,
        )
        self.assertEqual(original, self.digest())

    def test_calendar_edit_stales_exact_confirmation(self):
        body = self.request()
        self.daily("Crew", self.c1.id, "2026-11-23", "2026-12-04", "Unknown")
        original = self.digest()
        self.assertEqual(self.post(body).status_code, 409)
        self.assertEqual(original, self.digest())

    def test_final_known_blocker_rolls_back_not_just_warns(self):
        body = self.request()
        original = self.digest()
        method = draft_apply._week

        def blocked(*args):
            result = method(*args)
            for row in result["records"]:
                row["checks"].append(
                    dict(
                        check="SyntheticKnownBlock",
                        state="Blocked",
                        reasons=["FAULT_INJECTION"],
                    )
                )
            return result

        with patch.object(draft_apply, "_week", blocked):
            response = self.post(body)
            self.assertEqual(response.status_code, 409)
        self.assertEqual(original, self.digest())

    def test_saved_actual_rig_maintenance_blocks_final_transaction(self):
        from rigarus_backend.daily_rig_store import DailyRigStore, RigPeriodInput

        rig = self.rig()
        self.allocate(self.days[0], rig)
        DailyRigStore(self.database).save_period(
            rig.id,
            "Maintenance",
            RigPeriodInput(
                "2026-11-23", "2026-11-23", "Active", True, "Synthetic maintenance"
            ),
        )
        body = self.request()
        original = self.digest()
        response = self.post(body)
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(original, self.digest())

    def test_recovery_new_records_would_cancel_without_rewinding(self):
        body = self.request()
        result = self.post(body).json()
        inverse = self.client.get(
            f"/draft-transactions/recovery-preview/{body['profile_id']}/1"
        ).json()
        self.assertEqual(
            sum(r["status"] == "Cancelled" for r in inverse["proposed_restore"]), 3
        )
        self.assertTrue(
            all(
                "revision" not in r and "expected_current_revision" in r
                for r in inverse["proposed_restore"]
            )
        )
        self.assertEqual(len(result["after"]), 8)

    def test_migration_backup_failure_aborts_before_ddl(self):
        with closing(storage.connect(self.database)) as c, c:
            remove_draft_version_schema(c)
        original = self.digest()
        with patch.object(
            storage,
            "verified_upgrade_backup",
            side_effect=OSError("Synthetic backup failure"),
        ):
            with self.assertRaises(OSError):
                storage.initialize_database(self.database)
        self.assertEqual(original, self.digest())

    def test_schema19_reader_refuses20_and_independent_backup_preserved(self):
        from rigarus_backend.recommendation_adapter import (
            CURRENT_HISTORY,
            CURRENT_TABLES,
            _read_schema,
        )
        import rigarus_backend.recommendation_adapter as adapter
        from rigarus_backend.day_recommendation_adapter import ReadBudget

        with closing(storage.connect(self.database)) as c:
            with (
                patch.object(adapter, "CURRENT_HISTORY", CURRENT_HISTORY[:-1]),
                patch.object(
                    adapter, "CURRENT_TABLES", CURRENT_TABLES - {"DraftVersions"}
                ),
            ):
                with self.assertRaises(storage.UnsupportedDatabaseError):
                    _read_schema(ReadBudget(c))

    def test_expired_deadline_rejects_without_write(self):
        body = self.request()
        original = self.digest()
        with patch.object(draft_apply, "SECONDS", 0):
            self.assertEqual(self.post(body).status_code, 503)
        self.assertEqual(original, self.digest())

    def test_final_shared_read_budget_failure_rolls_back(self):
        body = self.request()
        original = self.digest()
        method = draft_apply._week

        def limited(budget, *args):
            budget.remaining = 1
            return method(budget, *args)

        with patch.object(draft_apply, "_week", limited):
            self.assertEqual(self.post(body).status_code, 503)
        self.assertEqual(original, self.digest())

    def test_prepare_deterministic_and_test_flags_independent(self):
        original = self.digest()
        proof = self.prepare()
        self.assertEqual(proof, self.prepare())
        editor_only = TestClient(
            create_app(self.database, enable_day_editor_test_writes=True)
        )
        self.assertEqual(
            editor_only.post(
                "/draft-transactions/submit", json=self.request(proof)
            ).status_code,
            409,
        )
        self.assertFalse(
            self.writer.get("/day-editor/status").json()["test_writes_enabled"]
        )
        self.assertEqual(original, self.digest())


if __name__ == "__main__":
    unittest.main()
