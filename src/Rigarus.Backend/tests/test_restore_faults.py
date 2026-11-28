"""Actual API transactions under a synthetic ASGI fault; no native GUI claim."""

import json
import unittest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import test_draft_restore as fixtures
from rigarus_backend.api import create_app
from rigarus_backend.restore_faults import RestoreFaults, FORMAT, manifest
from rigarus_backend.sidecar import private_api


class FaultTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.RestoreTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.addCleanup(self.case.tearDown)
        self.case.source()
        self.body = self.case.rrequest()
        self.plan = dict(
            format=FORMAT,
            synthetic_only=True,
            profile_id=self.body["profile_id"],
            source_version_id=self.body["source_version_id"],
            transport="none",
            archive="none",
        )

    def wrap(self, mode):
        self.plan["transport"] = mode
        (self.case.root / "data/restore-fault.json").write_text(json.dumps(self.plan))
        self.sleep = AsyncMock()
        self.wrapper = RestoreFaults(
            self.case.writer.app,
            self.case.database,
            self.case.root,
            restore_enabled=True,
            sleep=self.sleep,
        )
        return TestClient(self.wrapper)

    def post(self, client):
        return client.post("/draft-restores/submit", json=self.body)

    def receipt(self):
        return self.case.writer.get(
            f"/draft-restores/receipt/{self.body['profile_id']}/{self.body['request_id']}"
        ).json()

    def test_after_commit_real_transaction_precedes_delay_and_exact_replay_is_once(
        self,
    ):
        client = self.wrap("after_commit_timeout")

        async def during_delay(seconds):
            self.assertEqual(seconds, 65)
            self.assertEqual(self.receipt()["outcome"], "Committed")

        self.sleep.side_effect = during_delay
        self.assertEqual(self.post(client).json()["outcome"], "Committed")
        counts = self.case.counts()
        # Reopening the fault wrapper cannot rearm it.
        reopened = self.wrap("after_commit_timeout")
        self.assertEqual(self.post(reopened).json(), self.receipt())
        self.sleep.assert_not_awaited()
        self.assertEqual(self.case.counts(), counts)

    def test_before_handler_times_out_without_any_sql_then_original_key_replays(self):
        client = self.wrap("before_commit_timeout")
        counts = self.case.counts()
        self.assertEqual(self.post(client).status_code, 503)
        self.sleep.assert_awaited_once_with(65)
        self.assertEqual(self.receipt()["outcome"], "NotFound")
        self.assertEqual(self.case.counts(), counts)
        self.assertEqual(
            self.post(self.wrap("before_commit_timeout")).json()["outcome"], "Committed"
        )
        self.sleep.assert_not_awaited()
        self.assertEqual(self.case.counts()[1:], [1, 1])

    def test_post_commit_read_fails_once_initial_reads_and_receipt_remain_real(self):
        client = self.wrap("refresh_once")
        # Invalid week input would be 422; the injected failure must only begin after commit.
        self.assertNotEqual(client.get("/schedule-workbench/week").status_code, 503)
        self.assertEqual(self.post(client).json()["outcome"], "Committed")
        counts = self.case.counts()
        self.assertEqual(client.get("/schedule-workbench/week").status_code, 503)
        self.assertNotEqual(client.get("/schedule-workbench/week").status_code, 503)
        self.assertEqual(self.receipt()["outcome"], "Committed")
        self.assertEqual(self.case.counts(), counts)

    def test_corrupt_only_outgoing_profile_never_changes_authoritative_receipt(self):
        client = self.wrap("wrong_profile_once")
        result = self.post(client).json()
        self.assertNotEqual(result["database_identity"], self.body["profile_id"])
        self.assertEqual(self.receipt()["database_identity"], self.body["profile_id"])
        self.assertEqual(self.post(client).json(), self.receipt())

    def test_rejected_transaction_is_not_delayed_or_rewritten(self):
        client = self.wrap("after_commit_timeout")
        self.body["acknowledged_warning_ids"] = []
        counts = self.case.counts()
        result = self.post(client).json()
        self.assertEqual(result["outcome"], "Rejected")
        self.sleep.assert_not_awaited()
        self.assertEqual(self.case.counts()[0:2], counts[0:2])
        self.assertEqual(self.receipt(), result)

    def test_manifest_strict_gate_root_profile_modes_and_size(self):
        self.wrap("none")
        for root, enabled in [
            (None, True),
            (self.case.root, False),
            (self.case.root.parent, True),
        ]:
            with self.assertRaises((ValueError, OSError)):
                manifest(self.case.database, root, restore_enabled=enabled)
        for key, value in [
            ("profile_id", "00000000-0000-4000-8000-000000000001"),
            ("source_version_id", True),
            ("transport", "arbitrary"),
            ("archive", "delete"),
            ("synthetic_only", False),
            ("extra", "forbidden"),
        ]:
            path = self.case.root / "data/restore-fault.json"
            path.write_text(json.dumps(self.plan | {key: value}))
            with self.assertRaises((ValueError, TypeError)):
                manifest(self.case.database, self.case.root, restore_enabled=True)
        path.write_text(" " * 4097)
        with self.assertRaises(ValueError):
            manifest(self.case.database, self.case.root, restore_enabled=True)

    def test_claim_corruption_or_replacement_key_never_reaches_handler(self):
        client = self.wrap("before_commit_timeout")
        self.assertEqual(self.post(client).status_code, 503)
        self.body["request_id"] = "00000000-0000-4000-8000-000000000001"
        self.assertEqual(self.post(client).status_code, 503)
        self.assertEqual(self.case.counts()[1:], [0, 0])
        (self.wrapper.folder / "transport.json").write_text("{")
        self.assertEqual(self.post(client).status_code, 503)
        self.assertEqual(self.case.counts()[1:], [0, 0])

    def test_normal_app_ignores_manifest_and_restore_default_stays_closed(self):
        self.wrap("after_commit_timeout")
        closed = TestClient(create_app(self.case.database))
        self.assertEqual(self.post(closed).status_code, 409)
        self.assertFalse(self.wrapper.folder.joinpath("transport.json").exists())

    def test_authentication_precedes_fault_claim_and_lifespan_is_preserved(self):
        self.wrap("before_commit_timeout")
        # Startup/shutdown pass through the pure ASGI wrapper; unauthenticated
        # requests must never claim a fault or reach the real transaction.
        with TestClient(private_api(self.wrapper, b"synthetic-token")) as client:
            result = self.post(client)
            self.assertEqual(result.status_code, 401)
        self.assertFalse((self.wrapper.folder / "transport.json").exists())
        self.assertEqual(self.case.counts()[1:], [0, 0])
