import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_day_recommendation_adapter as fixtures
from rigarus_backend.api import create_app
from rigarus_backend.recommendation_adapter import SnapshotReadError


class DayPreviewApiTests(unittest.TestCase):
    daily = fixtures.DayAdapterTests.daily
    calendar = fixtures.DayAdapterTests.calendar
    visit = fixtures.DayAdapterTests.visit
    employee = fixtures.DayAdapterTests.employee

    def setUp(self):
        fixtures.DayAdapterTests.setUp(self)
        self.client = TestClient(create_app(self.database))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.body = dict(
            work_item_id=self.work.id,
            expected_project_id=self.project.id,
            crew_ids=[self.c1.id, self.c2.id],
            remaining_days=2,
            remaining_confirmed=True,
            earliest_start_date="2026-11-23",
            horizon_end_date="2026-11-27",
        )

    def preview(self, **changes):
        return self.client.post(
            "/day-recommendations/preview", json=self.body | changes
        )

    def test_real_two_sorts_full_day_and_false_gates(self):
        finish = self.preview().json()
        start = self.preview(order="EarliestStart").json()
        self.assertEqual(finish["ranked_crew_ids"], [self.c2.id, self.c1.id])
        self.assertEqual(start["ranked_crew_ids"], [self.c1.id, self.c2.id])
        self.assertEqual(finish["unit"], "FullDay")
        self.assertEqual(finish["confirmed_remaining_days"], 2)
        self.assertEqual(finish["validation_status"], "Pending")
        self.assertFalse(finish["applyable"] or finish["publishable"])
        c1 = next(c for c in finish["candidates"] if c["crew_id"] == self.c1.id)
        self.assertEqual(c1["allocated_working_dates"], ["2026-11-23", "2026-11-27"])
        self.assertTrue(c1["skipped"])
        self.assertIn("ApprovedDriver", [m["check"] for m in c1["missing_evidence"]])
        self.assertEqual(
            sum(m["count"] for m in c1["missing_evidence"]),
            c1["missing_evidence_count"],
        )
        self.assertNotIn(str(self.database), str(finish))
        self.assertNotIn("snapshot", finish)

    def test_missing_confirmation_never_uses_estimate_or_visits(self):
        for changes in (
            dict(remaining_confirmed=False),
            dict(remaining_days=None),
            dict(remaining_days=500),
        ):
            with self.subTest(changes=changes):
                result = self.preview(**changes).json()
                self.assertEqual(result["ranked_crew_ids"], [])
                self.assertTrue(
                    all(c["proposed_finish_date"] is None for c in result["candidates"])
                )
                self.assertFalse(result["applyable"])

    def test_read_only_no_state_changes_and_all_write_gates_closed(self):
        with closing(sqlite3.connect(self.database)) as c:
            before = list(c.iterdump())
        result = self.preview().json()
        request = dict(query=self.body, input_fingerprint=result["input_fingerprint"])
        self.assertEqual(
            self.client.post("/day-recommendations/freshness", json=request).json()[
                "status"
            ],
            "Current",
        )
        self.assertEqual(
            self.client.post(
                "/day-draft-assignments",
                json=dict(
                    work_item_id=self.work.id,
                    crew_id=self.c1.id,
                    local_date="2026-11-23",
                ),
            ).status_code,
            409,
        )
        with closing(sqlite3.connect(self.database)) as c:
            self.assertEqual(list(c.iterdump()), before)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_freshness_tracks_real_input_and_query_change(self):
        result = self.preview().json()
        request = dict(query=self.body, input_fingerprint=result["input_fingerprint"])
        changed = dict(request, query=self.body | dict(order="EarliestStart"))
        self.assertEqual(
            self.client.post("/day-recommendations/freshness", json=changed).json()[
                "status"
            ],
            "Stale",
        )
        self.daily("Crew", self.c1.id, "2026-11-24", "2026-11-24")
        check = self.client.post("/day-recommendations/freshness", json=request).json()
        self.assertEqual(check["status"], "Stale")
        self.assertFalse(check["applyable"] or check["publishable"])

    def test_strict_half_day_safety_flags_unknown_and_malformed_inputs_rejected(self):
        for changes in (
            dict(slot="AM"),
            dict(estimated_half_days=2),
            dict(applyable=True),
            dict(crew_ids=[]),
            dict(crew_ids=[True]),
            dict(crew_ids=[self.c1.id, self.c1.id]),
            dict(remaining_days=True),
            dict(remaining_confirmed=1),
            dict(max_options=True),
            dict(order="Safe"),
            dict(earliest_start_date="2026-11-28"),
            dict(horizon_end_date="2028-01-01"),
        ):
            with self.subTest(changes=changes):
                self.assertEqual(self.preview(**changes).status_code, 422)

    def test_context_and_not_found_have_sanitized_failures(self):
        self.assertEqual(
            self.preview(expected_project_id=self.project.id + 1000).status_code, 409
        )
        self.assertEqual(
            self.preview(work_item_id=self.work.id + 1000).status_code, 404
        )
        self.assertEqual(self.preview(crew_ids=[999999]).status_code, 404)
        with patch(
            "rigarus_backend.day_recommendation_api.build_day_recommendation_snapshot",
            side_effect=SnapshotReadError("private path must never leak"),
        ):
            for route, payload in (
                ("preview", self.body),
                ("freshness", dict(query=self.body, input_fingerprint="a" * 64)),
            ):
                response = self.client.post(
                    "/day-recommendations/" + route, json=payload
                )
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("private path", response.text)

    def test_result_limit_and_needs_review_keep_explanations(self):
        result = self.preview(max_options=1).json()
        self.assertEqual(len(result["ranked_crew_ids"]), 1)
        self.assertEqual(result["omitted_by_limit"], 1)
        result = self.preview(remaining_days=100).json()
        self.assertFalse(result["ranked_crew_ids"])
        self.assertTrue(all(c["unfilled_days"] > 0 for c in result["candidates"]))

    def test_freshness_fingerprint_and_extra_fields_strict(self):
        for fingerprint in ("", "z" * 64, "a" * 65):
            self.assertEqual(
                self.client.post(
                    "/day-recommendations/freshness",
                    json=dict(query=self.body, input_fingerprint=fingerprint),
                ).status_code,
                422,
            )
