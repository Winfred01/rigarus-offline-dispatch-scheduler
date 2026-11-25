import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_day_recommendation_adapter as fixtures
from rigarus_backend.api import create_app
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.assignment_store import AssignmentStore
from rigarus_backend.assignments import AssignmentDraft
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.recommendation_adapter import SnapshotReadError


class WorkbenchTests(unittest.TestCase):
    daily = fixtures.DayAdapterTests.daily
    employee = fixtures.DayAdapterTests.employee
    calendar = fixtures.DayAdapterTests.calendar
    visit = fixtures.DayAdapterTests.visit

    def setUp(self):
        fixtures.DayAdapterTests.setUp(self)
        self.day = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2026-11-23", "Synthetic daily note")
        )
        self.old = AssignmentStore(self.database).save(
            AssignmentDraft(
                self.work.id,
                self.c2.id,
                "2026-11-24",
                "PM",
                "Synthetic retained half note",
            )
        )
        self.client = TestClient(create_app(self.database))

    def read(self):
        return self.client.get(
            "/schedule-workbench/week",
            params=dict(start_date="2026-11-22", end_date="2026-11-28"),
        )

    def locate(self, kind, identity):
        return self.client.get(f"/schedule-workbench/locate/{kind}/{identity}")

    def test_both_kinds_same_numeric_id_notes_slots_and_false_gates(self):
        self.assertEqual(self.day["id"], self.old.id)
        r = self.read()
        self.assertEqual(r.status_code, 200, r.text)
        b = r.json()
        self.assertTrue(b["readonly"])
        self.assertFalse(b["applyable"] or b["publishable"])
        self.assertEqual(b["validation_status"], "Pending")
        rows = {r["record_kind"]: r for r in b["records"]}
        self.assertEqual(rows["FullDayDraft"]["notes"], "Synthetic daily note")
        self.assertIsNone(rows["FullDayDraft"]["slot"])
        self.assertEqual(rows["LegacyHalfDay"]["notes"], self.old.notes)
        self.assertEqual(rows["LegacyHalfDay"]["slot"], "PM")
        self.assertEqual(rows["LegacyHalfDay"]["compatibility_status"], "Needs Review")
        self.assertEqual(len(b["view_fingerprint"]), 64)
        self.assertNotIn(str(self.database), r.text)

    def test_typed_locate_uses_correct_date_and_retains_both_cards(self):
        for kind, day in (
            ("FullDayDraft", "2026-11-23"),
            ("LegacyHalfDay", "2026-11-24"),
        ):
            r = self.locate(kind, self.old.id)
            self.assertEqual(r.status_code, 200, r.text)
            b = r.json()
            target = b["target"]
            self.assertEqual(target["record_kind"], kind)
            row = next(
                v
                for v in b["records"]
                if (v["record_kind"], v["id"]) == (kind, target["id"])
            )
            self.assertEqual(row["local_date"], day)
            self.assertEqual(b["start_date"], "2026-11-22")

    def test_calendar_and_real_cross_kind_personnel_conflicts_visible(self):
        worker = self.employee(home=self.c1.id)
        store = DayDraftStore(self.database)
        store.save(
            DayDraft(
                self.work.id, self.c1.id, "2026-11-24", "Synthetic day", (worker.id,)
            ),
            self.day["id"],
            self.day["revision"],
        )
        StaffingStore(self.database).save(self.old.id, [worker.id], self.old.revision)
        r = self.read()
        self.assertEqual(r.status_code, 200, r.text)
        for row in r.json()["records"]:
            checks = {c["check"]: c for c in row["checks"]}
            self.assertEqual(checks["PersonnelConflicts"]["state"], "Blocked")
            self.assertIsNone(row["actual_rig_id"])
            self.assertFalse(row["publishable"])
        day = next(v for v in r.json()["records"] if v["record_kind"] == "FullDayDraft")
        self.assertEqual(
            next(c for c in day["checks"] if c["check"] == "DailyCalendars")["state"],
            "Blocked",
        )

    def test_cancelled_missing_and_unknown_kind_do_not_fallback_namespace(self):
        DayDraftStore(self.database).cancel(self.day["id"], self.day["revision"])
        self.assertEqual(self.locate("FullDayDraft", self.day["id"]).status_code, 409)
        self.assertEqual(self.locate("LegacyHalfDay", self.old.id).status_code, 200)
        self.assertEqual(self.locate("FullDayDraft", 999999).status_code, 404)
        self.assertEqual(self.locate("LegacyHalfDay", 999999).status_code, 404)
        self.assertEqual(self.locate("Proposal", self.old.id).status_code, 422)

    def test_latest_moved_record_drives_target_week(self):
        DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2027-01-01", "Moved"),
            self.day["id"],
            self.day["revision"],
        )
        b = self.locate("FullDayDraft", self.day["id"]).json()
        self.assertEqual(b["start_date"], "2026-12-27")
        self.assertEqual(b["end_date"], "2027-01-02")
        self.assertEqual(b["target"]["revision"], 2)

    def test_reads_and_locates_keep_all_logical_data_and_closed_writer(self):
        with closing(sqlite3.connect(self.database)) as c:
            before = list(c.iterdump())
        self.assertEqual(self.read().status_code, 200)
        self.assertEqual(self.locate("FullDayDraft", self.day["id"]).status_code, 200)
        self.assertEqual(
            self.client.post(
                "/day-draft-assignments",
                json=dict(
                    work_item_id=self.work.id,
                    crew_id=self.c1.id,
                    local_date="2026-11-27",
                ),
            ).status_code,
            409,
        )
        with closing(sqlite3.connect(self.database)) as c:
            self.assertEqual(list(c.iterdump()), before)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_invalid_range_and_unknown_read_fail_without_partial_board(self):
        for start, end in (
            ("2026-11-28", "2026-11-22"),
            ("2026-02-30", "2026-03-01"),
            ("2026-11-22", "2026-11-29"),
        ):
            self.assertEqual(
                self.client.get(
                    "/schedule-workbench/week",
                    params=dict(start_date=start, end_date=end),
                ).status_code,
                422,
            )
        with patch(
            "rigarus_backend.schedule_workbench._read_day_sources",
            side_effect=SnapshotReadError("private source"),
        ):
            r = self.read()
            self.assertEqual(r.status_code, 503)
            self.assertNotIn("private source", r.text)
            self.assertNotIn("records", r.json())

    def test_budget_limit_fails_instead_of_truncating(self):
        with patch("rigarus_backend.day_recommendation_adapter.MAX_READ_UNITS", 4):
            self.assertEqual(self.read().status_code, 503)

    def test_snapshot_is_query_only_and_pinned_before_sources(self):
        from rigarus_backend import schedule_workbench as module

        original = module._read_day_sources
        observed = []

        def inspect(c, *args):
            observed.append(
                (
                    c.connection.in_transaction,
                    c.connection.execute("PRAGMA query_only").fetchone()[0],
                )
            )
            return original(c, *args)

        with patch.object(module, "_read_day_sources", side_effect=inspect):
            self.assertEqual(self.read().status_code, 200)
        self.assertEqual(observed, [(True, 1)])

    def test_concurrent_atomic_metadata_edit_cannot_mix_week_sources(self):
        from rigarus_backend import schedule_workbench as module

        with closing(sqlite3.connect(self.database)) as c:
            c.execute("PRAGMA journal_mode=WAL")
        original = module._read_day_sources

        def write_after_first_reads(c, *args):
            with closing(sqlite3.connect(self.database)) as writer, writer:
                writer.execute(
                    "UPDATE Crews SET Name='Synthetic after Crew' WHERE Id=?",
                    (self.c1.id,),
                )
                writer.execute(
                    "UPDATE Projects SET SiteName='Synthetic after Site' WHERE Id=?",
                    (self.project.id,),
                )
            return original(c, *args)

        with patch.object(
            module, "_read_day_sources", side_effect=write_after_first_reads
        ):
            r = self.read()
            self.assertEqual(r.status_code, 200, r.text)
        current = self.read().json()
        before = next(
            v for v in r.json()["records"] if v["record_kind"] == "FullDayDraft"
        )
        after = next(
            v for v in current["records"] if v["record_kind"] == "FullDayDraft"
        )
        self.assertNotEqual(before["site_name"], after["site_name"])
        self.assertNotEqual(before["crew_name"], after["crew_name"])
        self.assertEqual(after["crew_name"], "Synthetic after Crew")

    def test_storage_date_edges_have_honest_results(self):
        store = DayDraftStore(self.database)
        for day in ("0001-01-01", "9999-12-31"):
            saved = store.save(DayDraft(self.work.id, self.c1.id, day))
            response = self.locate("FullDayDraft", saved["id"])
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(
                any(v["local_date"] == day for v in response.json()["records"])
            )
