"""Synthetic-only inverse transaction, migration and mixed-kind preservation."""

import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

import test_draft_apply as fixtures
from migration_fixture import remove_draft_restore_schema
from rigarus_backend import storage, draft_restore
from rigarus_backend.api import create_app
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.draft_restore_api import ConfirmRestore
from rigarus_backend.recommendation_adapter import SnapshotReadError


class RestoreTests(unittest.TestCase):
    calendar = fixtures.TransactionTests.calendar
    visit = fixtures.TransactionTests.visit
    employee = fixtures.TransactionTests.employee
    daily = fixtures.TransactionTests.daily
    approve = fixtures.TransactionTests.approve
    save_policy = fixtures.TransactionTests.save_policy
    rig = fixtures.TransactionTests.rig
    allocate = fixtures.TransactionTests.allocate
    prepare = fixtures.TransactionTests.prepare
    request = fixtures.TransactionTests.request
    post = fixtures.TransactionTests.post
    digest = fixtures.TransactionTests.digest

    def setUp(self):
        fixtures.TransactionTests.setUp(self)
        self.root = self.database.parent / "isolated-restore"
        target = self.root / "data" / "rigarus.db"
        target.parent.mkdir(parents=True)
        with (
            closing(storage.connect(self.database)) as source,
            closing(sqlite3.connect(target)) as dest,
        ):
            source.backup(dest)
        self.database = target
        self.client = TestClient(create_app(target))
        self.writer = TestClient(
            create_app(
                target,
                enable_draft_transaction_test_writes=True,
                enable_draft_restore_test_writes=True,
                draft_restore_test_root=self.root,
            )
        )

    def source(self, days=8):
        self.plan["query"]["remaining_days"] = days
        r = self.post(self.request())
        self.assertEqual(r.status_code, 200, r.text)
        self.original = r.json()
        self.input = dict(
            profile_id=self.original["database_identity"],
            source_version_id=self.original["version_id"],
        )
        return self.original

    def rprepare(self):
        r = self.writer.post("/draft-restores/prepare", json=self.input)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def rrequest(self, proof=None):
        proof = self.rprepare() if proof is None else proof
        return self.input | dict(
            request_id=str(uuid4()),
            plan_fingerprint=proof["plan_fingerprint"],
            confirmed=True,
            acknowledged_warning_ids=[w["warning_id"] for w in proof["warnings"]],
        )

    def rpost(self, body):
        return self.writer.post("/draft-restores/submit", json=body)

    def counts(self):
        with closing(storage.connect(self.database, read_only=True)) as c:
            return [
                c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                for t in (
                    "DayDraftChanges",
                    "DraftRestoreVersions",
                    "DraftRestoreReceipts",
                )
            ]

    def test_extension_inverse_preserves_ids_and_cancels_only_additions(self):
        source = self.source()
        before = self.digest()
        proof = self.rprepare()
        self.assertEqual(before, self.digest())
        r = self.rpost(self.rrequest(proof))
        self.assertEqual(r.status_code, 200, r.text)
        result = r.json()
        self.assertEqual(result["outcome"], "Committed", result)
        self.assertEqual(result["source_version_id"], source["version_id"])
        self.assertEqual(result["record_kind"], "DraftRestoreVersion")
        self.assertEqual(sum(x["status"] == "Cancelled" for x in result["after"]), 3)
        for old, new in zip(source["after"], result["after"]):
            self.assertEqual(old["id"], new["id"])
            self.assertEqual(old["revision"] + 1, new["revision"])
        self.assertEqual(self.counts()[1:], [1, 1])
        self.assertFalse(result["applyable"] or result["publishable"])
        self.assertEqual(result["validation_status"], "Pending")
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                json.loads(
                    c.execute("SELECT ResultJson FROM DraftVersions").fetchone()[0]
                ),
                source,
            )
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_shortening_inverse_reactivates_cancelled_stable_ids(self):
        source = self.source(2)
        result = self.rpost(self.rrequest()).json()
        self.assertEqual(result["outcome"], "Committed", result)
        self.assertTrue(all(r["status"] == "Draft" for r in result["after"]))
        self.assertEqual(
            {r["id"] for r in result["after"]}, {d["id"] for d in self.days}
        )
        for row in source["after"]:
            history = DayDraftStore(self.database).history(row["id"])
            self.assertEqual(history[0]["revision"], row["revision"] + 1)
            self.assertEqual(history[-1]["revision"], 1)

    def staff_original(self):
        employee = self.employee()
        self.daily("Employee", employee.id, state="Available")
        store = DayDraftStore(self.database)
        a = self.days[0]
        self.days[0] = store.save(
            DayDraft(
                a["work_item_id"],
                a["crew_id"],
                a["local_date"],
                "Synthetic original employee note",
                (employee.id,),
            ),
            a["id"],
            a["revision"],
        )
        self.plan["query"]["replacements"][0]["expected_revision"] = self.days[0][
            "revision"
        ]
        return employee

    def test_original_staff_notes_and_historical_members_restored(self):
        worker = self.staff_original()
        self.source(2)
        result = self.rpost(self.rrequest()).json()
        self.assertEqual(result["outcome"], "Committed", result)
        row = next(x for x in result["after"] if x["id"] == self.days[0]["id"])
        self.assertEqual(row["employee_ids"], [worker.id])
        self.assertEqual(row["notes"], "Synthetic original employee note")
        self.assertEqual(len(DayDraftStore(self.database).history(row["id"])), 4)

    def test_equal_integer_ids_legacy_and_other_project_never_modified(self):
        from rigarus_backend.project_store import ProjectStore
        from rigarus_backend.projects import ProjectDraft, WorkItemDraft, WorkType

        other = ProjectStore(self.database).save(
            ProjectDraft(
                "SYN-RESTORE-OTHER",
                "19",
                "Synthetic unrelated",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 2)],
            )
        )
        work = other.work_items[0]
        untouched = DayDraftStore(self.database).save(
            DayDraft(work.id, self.c2.id, "2026-12-03", "Synthetic untouched")
        )
        legacy = self.visit(
            crew=self.c2.id, day="2026-11-23", half="PM", work_item=work.id
        )
        self.assertEqual(legacy.id, self.days[0]["id"])
        with closing(storage.connect(self.database)) as c:
            before = c.execute("SELECT * FROM DraftAssignments").fetchall()
        self.source()
        self.assertEqual(self.rpost(self.rrequest()).json()["outcome"], "Committed")
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute("SELECT * FROM DraftAssignments").fetchall(), before
            )
        self.assertEqual(DayDraftStore(self.database).read(untouched["id"]), untouched)
        for kind, identity in (
            ("LegacyHalfDay", legacy.id),
            ("FullDayDraft", self.days[0]["id"]),
        ):
            r = self.client.get(f"/schedule-workbench/locate/{kind}/{identity}")
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()["target"]["record_kind"], kind)
            record = next(
                x
                for x in r.json()["records"]
                if x["record_kind"] == kind and x["id"] == identity
            )
            self.assertEqual(record["slot"], "PM" if kind == "LegacyHalfDay" else None)
            self.assertEqual(
                record["project_id"],
                other.id if kind == "LegacyHalfDay" else self.project.id,
            )
            self.assertEqual(
                record["notes"],
                "Synthetic preserved visit"
                if kind == "LegacyHalfDay"
                else self.days[0]["notes"],
            )

    def test_legacy_half_occupancy_blocks_reactivation(self):
        self.source(2)
        legacy = self.visit(crew=self.c1.id, day=self.days[2]["local_date"], half="AM")
        before = self.counts()
        proof = self.rprepare()
        self.assertEqual(proof["status"], "Blocked")
        result = self.rpost(self.rrequest(proof)).json()
        self.assertEqual(result["code"], "Blocked")
        self.assertEqual(self.counts()[:2], before[:2])
        self.assertEqual(
            self.client.get(
                f"/schedule-workbench/locate/LegacyHalfDay/{legacy.id}"
            ).status_code,
            200,
        )

    def test_changed_touched_note_status_or_revision_is_stale(self):
        self.source()
        body = self.rrequest()
        row = DayDraftStore(self.database).read(self.days[0]["id"])
        DayDraftStore(self.database).save(
            DayDraft(
                row["work_item_id"],
                row["crew_id"],
                row["local_date"],
                "Synthetic later edit",
            ),
            row["id"],
            row["revision"],
        )
        counts = self.counts()
        self.assertEqual(self.rpost(body).json()["code"], "Stale")
        self.assertEqual(self.counts()[:2], counts[:2])

    def test_each_pending_ack_missing_extra_duplicate_and_false(self):
        self.source()
        proof = self.rprepare()
        body = self.rrequest(proof)
        self.assertGreater(len(body["acknowledged_warning_ids"]), 4)
        for changes in (
            dict(acknowledged_warning_ids=[]),
            dict(acknowledged_warning_ids=body["acknowledged_warning_ids"][:-1]),
            dict(confirmed=False),
            dict(
                acknowledged_warning_ids=body["acknowledged_warning_ids"] + ["f" * 64]
            ),
        ):
            result = self.rpost(body | changes | dict(request_id=str(uuid4()))).json()
            self.assertEqual(
                result["code"], "EACH_PENDING_ITEM_REQUIRES_CONFIRMATION", result
            )
        self.assertEqual(
            self.rpost(
                body
                | dict(acknowledged_warning_ids=body["acknowledged_warning_ids"] * 2)
            ).status_code,
            422,
        )
        self.assertEqual(self.rpost(body).json()["outcome"], "Committed")
        self.assertEqual(self.counts()[1:], [1, 5])

    def test_same_key_replay_and_changed_payload_rejected_even_after_later_edit(self):
        self.source()
        body = self.rrequest()
        saved = self.rpost(body).json()
        before = self.digest()
        self.assertEqual(self.rpost(body).json(), saved)
        self.assertEqual(before, self.digest())
        row = next(x for x in saved["after"] if x["status"] == "Draft")
        DayDraftStore(self.database).save(
            DayDraft(
                row["work_item_id"],
                row["crew_id"],
                row["local_date"],
                "Synthetic edit after restore",
            ),
            row["id"],
            row["revision"],
        )
        before = self.digest()
        self.assertEqual(self.rpost(body).json(), saved)
        self.assertEqual(before, self.digest())
        self.assertEqual(self.rpost(body | dict(confirmed=False)).status_code, 409)
        self.assertEqual(before, self.digest())

    def test_rejected_receipt_replays_without_reinterpreting_changed_resources(self):
        self.source()
        body = self.rrequest() | dict(acknowledged_warning_ids=[])
        rejected = self.rpost(body).json()
        before = self.digest()
        self.assertEqual(rejected["outcome"], "Rejected")
        self.assertEqual(self.rpost(body).json(), rejected)
        self.assertEqual(before, self.digest())

    def test_reopen_receipt_version_default_closed_and_unknown(self):
        self.source()
        body = self.rrequest()
        saved = self.rpost(body).json()
        with TestClient(create_app(self.database)) as restart:
            self.assertEqual(
                restart.get(
                    f"/draft-restores/receipt/{body['profile_id']}/{body['request_id']}"
                ).json(),
                saved,
            )
            self.assertEqual(
                restart.get(
                    f"/draft-restores/version/{body['profile_id']}/{saved['version_id']}"
                ).json(),
                saved,
            )
            self.assertEqual(
                restart.post("/draft-restores/submit", json=body).status_code, 409
            )
            self.assertEqual(
                restart.post("/draft-restores/prepare", json=self.input).status_code,
                409,
            )
            self.assertEqual(
                restart.get(
                    f"/draft-restores/receipt/{body['profile_id']}/{uuid4()}"
                ).json()["outcome"],
                "NotFound",
            )

    def test_sql_mid_batch_and_audit_or_receipt_failure_roll_back_all(self):
        self.source()
        body = self.rrequest()
        before = self.digest()
        append = draft_restore.append_change
        calls = 0

        def fail_mid(c, *args):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise sqlite3.OperationalError("Synthetic mid-batch failure")
            return append(c, *args)

        with patch.object(draft_restore, "append_change", side_effect=fail_mid):
            self.assertEqual(self.rpost(body).status_code, 503)
        self.assertEqual(before, self.digest())
        for table in ("DraftRestoreVersions", "DraftRestoreReceipts"):
            with closing(storage.connect(self.database)) as c, c:
                c.execute(
                    f"CREATE TRIGGER SyntheticRestoreFault BEFORE INSERT ON {table} BEGIN SELECT RAISE(ABORT,'synthetic'); END"
                )
            snapshot = self.digest()
            self.assertEqual(self.rpost(body).status_code, 503)
            self.assertEqual(snapshot, self.digest())
            with closing(storage.connect(self.database)) as c, c:
                c.execute("DROP TRIGGER SyntheticRestoreFault")
        self.assertEqual(self.rpost(body).json()["outcome"], "Committed")

    def test_resource_read_failure_is_unknown_not_pending_or_rejected(self):
        self.source()
        body = self.rrequest()
        before = self.digest()
        with patch.object(
            draft_restore, "_week", side_effect=SnapshotReadError("synthetic")
        ):
            self.assertEqual(self.rpost(body).status_code, 503)
        self.assertEqual(before, self.digest())

    def test_driver_hard_negative_rejects(self):
        worker = self.staff_original()
        self.source(2)
        self.approve(worker, state="Suspended")
        proof = self.rprepare()
        self.assertEqual(proof["status"], "Blocked")
        self.assertTrue(any(x["check"] == "ApprovedDriver" for x in proof["blockers"]))
        self.assertEqual(self.rpost(self.rrequest(proof)).json()["code"], "Blocked")

    def assert_blocked(self, check):
        proof = self.rprepare()
        self.assertEqual(proof["status"], "Blocked", proof)
        self.assertTrue(
            any(x["check"].startswith(check) for x in proof["blockers"]),
            proof["blockers"],
        )
        before = self.counts()
        self.assertEqual(self.rpost(self.rrequest(proof)).json()["code"], "Blocked")
        self.assertEqual(self.counts()[:2], before[:2])

    def test_unavailable_employee_hard_negative_rejects(self):
        worker = self.staff_original()
        self.source(2)
        self.daily("Employee", worker.id, state="Unavailable")
        self.assert_blocked("ApprovedDriver")

    def test_personnel_conflict_with_other_crew_rejects(self):
        worker = self.staff_original()
        self.source(2)
        DayDraftStore(self.database).save(
            DayDraft(
                self.work.id,
                self.c2.id,
                self.days[0]["local_date"],
                "Synthetic other Crew",
                (worker.id,),
            )
        )
        self.assert_blocked("PersonnelConflicts")

    def test_project_and_crew_not_working_reject(self):
        self.source(2)
        self.daily("Project", self.project.id, "2026-11-23", "2026-12-04", "NotWorking")
        self.assert_blocked("DailyCalendars")

    def test_minimum_level_and_qualification_checks_reject(self):
        from rigarus_backend.capability_validation import CapabilityRequirements

        self.staff_original()
        self.source(2)
        self.save_policy(
            "WorkItem",
            self.work.id,
            CapabilityRequirements(2, (1, 0, 0), "Exact", (("SYN-RESTORE-Q", 1),)),
        )
        self.assert_blocked("MinimumStaffing")
        proof = self.rprepare()
        self.assertTrue(any(x["check"].startswith("Skills") for x in proof["blockers"]))
        self.assertTrue(
            any(
                x["check"].startswith("Qualification")
                for row in proof["observations"]
                for x in row["checks"]
            )
        )

    def test_explicit_not_verified_qualification_is_blocked(self):
        from rigarus_backend.capability_validation import CapabilityRequirements

        worker = self.staff_original()
        self.source(2)
        self.save_policy(
            "WorkItem",
            self.work.id,
            CapabilityRequirements(1, (0, 0, 0), "AtLeast", (("SYN-RESTORE-Q", 1),)),
        )
        self.save_policy("Employee", worker.id, "NotVerified", "SYN-RESTORE-Q")
        self.assert_blocked("Qualification")

    def test_actual_rig_maintenance_hard_negative_rejects(self):
        from rigarus_backend.daily_rig_store import DailyRigStore, RigPeriodInput

        self.source()
        rig = self.rig()
        self.allocate(DayDraftStore(self.database).read(self.days[0]["id"]), rig)
        DailyRigStore(self.database).save_period(
            rig.id,
            "Maintenance",
            RigPeriodInput(
                "2026-11-23",
                "2026-11-23",
                "Active",
                True,
                "Synthetic restore maintenance",
            ),
        )
        self.assert_blocked("ActualRig")

    def test_saved_rig_readiness_not_recertified_by_restore(self):
        self.source()
        rig = self.rig()
        self.allocate(DayDraftStore(self.database).read(self.days[0]["id"]), rig)
        result = self.rpost(self.rrequest()).json()
        self.assertEqual(result["outcome"], "Committed", result)
        observed = next(
            r for r in result["observations"] if r["id"] == self.days[0]["id"]
        )
        self.assertTrue(observed["rig_context_stale"])
        self.assertTrue(
            any(
                c["check"] == "ActualRig" and c["state"] == "Pending"
                for c in observed["checks"]
            )
        )
        with closing(storage.connect(self.database)) as c:
            self.assertEqual(
                c.execute("SELECT count(*) FROM RigAllocationChanges").fetchone()[0], 1
            )

    def test_new_resource_warning_invalidates_prepared_confirmation(self):
        self.staff_original()
        self.source(2)
        body = self.rrequest()
        self.daily("Crew", self.c1.id, "2026-11-23", "2026-12-04", "Unknown")
        result = self.rpost(body).json()
        self.assertEqual(result["outcome"], "Rejected")
        self.assertEqual(result["code"], "STALE_RESTORE_PLAN")

    def test_late_final_blocker_rolls_back_changes(self):
        self.source()
        body = self.rrequest()
        before = self.counts()
        original = draft_restore._observations
        calls = 0

        def late(*args):
            nonlocal calls
            calls += 1
            rows = original(*args)
            if calls == 2:
                rows[0]["checks"].append(
                    dict(
                        check="SyntheticLateConflict",
                        state="Blocked",
                        reasons=["SYNTHETIC"],
                    )
                )
            return rows

        with patch.object(draft_restore, "_observations", side_effect=late):
            result = self.rpost(body).json()
        self.assertEqual(result["code"], "FINAL_RESOURCE_REVALIDATION_FAILED")
        self.assertEqual(self.counts()[:2], before[:2])

    def test_deadline_failure_rolls_back_and_keeps_request_unknown(self):
        self.source()
        body = self.rrequest()
        before = self.digest()
        with patch.object(draft_restore, "SECONDS", 0):
            self.assertEqual(self.rpost(body).status_code, 503)
        self.assertEqual(before, self.digest())

    def test_migration_backup_failure_leaves_schema20_untouched(self):
        self.source()
        with closing(storage.connect(self.database)) as c, c:
            remove_draft_restore_schema(c)
        before = self.digest()
        with patch.object(
            storage,
            "verified_upgrade_backup",
            side_effect=OSError("Synthetic no backup"),
        ):
            with self.assertRaises(OSError):
                storage.initialize_database(self.database)
        self.assertEqual(before, self.digest())

    def test_cross_namespace_request_uuid_does_not_alias_original_receipt(self):
        self.source()
        body = self.rrequest() | dict(request_id=self.original["request_id"])
        restored = self.rpost(body).json()
        self.assertEqual(restored["outcome"], "Committed", restored)
        self.assertEqual(
            self.client.get(
                f"/draft-transactions/receipt/{body['profile_id']}/{body['request_id']}"
            ).json(),
            self.original,
        )

    def weekend_source(self):
        from rigarus_backend.daily_weekend_store import (
            WeekendConsentStore,
            WeekendDecision,
        )

        worker = self.employee()
        self.daily("Employee", worker.id, "2026-11-23", "2026-12-04", "Available")
        row = DayDraftStore(self.database).save(
            DayDraft(
                self.work.id,
                self.c1.id,
                "2026-11-28",
                "Synthetic weekend original",
                (worker.id,),
            )
        )
        WeekendConsentStore(self.database).save_for_day(
            row["id"],
            row["revision"],
            worker.id,
            WeekendDecision(
                "Confirmed", True, True, "Synthetic prior weekend decision"
            ),
            0,
        )
        self.plan["query"].update(
            remaining_days=1,
            earliest_start_date="2026-11-28",
            horizon_end_date="2026-12-04",
            replacements=[
                dict(
                    record_kind="FullDayDraft",
                    record_id=row["id"],
                    expected_revision=row["revision"],
                )
            ],
        )
        self.source(1)
        return worker, row

    def test_weekend_previous_positive_not_recognized_as_fresh_after_restore(self):
        _, row = self.weekend_source()
        result = self.rpost(self.rrequest()).json()
        self.assertEqual(result["outcome"], "Committed", result)
        observation = next(x for x in result["observations"] if x["id"] == row["id"])
        self.assertTrue(
            any(
                c["check"] == "WeekendConsent" and c["state"] == "Pending"
                for c in observation["checks"]
            )
        )

    def test_weekend_explicit_refusal_rejects(self):
        from rigarus_backend.daily_weekend_store import (
            WeekendConsentStore,
            WeekendDecision,
        )
        from rigarus_backend.daily_weekend_consent import WeekendContext

        worker, _ = self.weekend_source()
        WeekendConsentStore(self.database).save_planned(
            WeekendContext(
                self.work.id, self.project.id, self.c1.id, "2026-11-28", (worker.id,)
            ),
            worker.id,
            WeekendDecision("Declined", True, True, "Synthetic current refusal"),
            1,
        )
        self.assert_blocked("WeekendConsent")

    def test_concurrent_same_key_one_version(self):
        self.source()
        body = self.rrequest()
        request = ConfirmRestore(**body)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(
                    lambda _: draft_restore.submit(self.database, request), range(2)
                )
            )
        self.assertEqual(results[0], results[1])
        self.assertEqual(self.counts()[1:], [1, 1])

    def test_root_gate_and_record_kind_input_validation(self):
        with self.assertRaises(ValueError):
            create_app(self.database, enable_draft_restore_test_writes=True)
        with self.assertRaises(ValueError):
            create_app(
                self.database,
                enable_draft_restore_test_writes=True,
                draft_restore_test_root=self.root / "wrong",
            )
        self.source()
        body = self.rrequest()
        for fields in (
            dict(source_record_kind="LegacyHalfDay"),
            dict(source_version_id=True),
            dict(source_version_id=0),
            dict(confirmed="true"),
            dict(untrusted_after=[]),
        ):
            self.assertEqual(self.rpost(body | fields).status_code, 422)
        self.assertEqual(
            self.rpost(body | dict(profile_id=str(uuid4()))).status_code, 409
        )

    def test_restore_audit_and_receipts_immutable(self):
        self.source()
        self.rpost(self.rrequest())
        with closing(storage.connect(self.database)) as c, c:
            for table in ("DraftRestoreVersions", "DraftRestoreReceipts"):
                for sql in (
                    f"DELETE FROM {table}",
                    f"UPDATE {table} SET ResultJson='{{}}'",
                ):
                    with self.assertRaises(sqlite3.IntegrityError):
                        c.execute(sql)

    def test_schema20_migration_backup_reopen_and_failure_retry(self):
        self.source()
        with closing(storage.connect(self.database)) as c, c:
            remove_draft_restore_schema(c)
        original = self.digest()
        for statements in (
            (*storage.CREATE_DRAFT_RESTORE, "SELECT synthetic_missing_restore"),
        ):
            with patch.object(storage, "CREATE_DRAFT_RESTORE", statements):
                with self.assertRaises(sqlite3.OperationalError):
                    storage.initialize_database(self.database)
            self.assertEqual(original, self.digest())
        storage.initialize_database(self.database)
        current = self.digest()
        storage.initialize_database(self.database)
        self.assertEqual(current, self.digest())
        backups = list(self.database.parent.glob("*.before-day-*.bak"))
        self.assertTrue(any(self.backup_digest(p) == original for p in backups))
        self.assertEqual(self.rpost(self.rrequest()).json()["outcome"], "Committed")

    @staticmethod
    def backup_digest(path):
        with closing(sqlite3.connect(path)) as c:
            return logical_digest(c)
