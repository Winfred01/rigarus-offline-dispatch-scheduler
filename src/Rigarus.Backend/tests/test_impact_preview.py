"""Synthetic exact-scope read-only impact regression."""

import sqlite3
import threading
import unittest
from contextlib import closing
from unittest.mock import patch

from fastapi.testclient import TestClient

import test_day_recommendation_adapter as fixtures
import test_daily_driver_snapshot as drivers
import test_daily_capability_snapshot as capabilities
import test_daily_rig_snapshot as rigs
from rigarus_backend.api import create_app
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend import impact_preview as impact
from rigarus_backend.impact_preview_api import ImpactQuery
from rigarus_backend.recommendation_adapter import SnapshotReadError
from rigarus_backend.project_store import ProjectStore
from rigarus_backend.projects import ProjectDraft, WorkItemDraft, WorkType
from rigarus_backend.capability_validation import CapabilityRequirements
from rigarus_backend.staffing_store import StaffingStore
from rigarus_backend.daily_rig_store import DailyRigStore, RigPeriodInput
from rigarus_backend.daily_weekend_store import WeekendConsentStore, WeekendDecision


class ImpactTests(unittest.TestCase):
    calendar = fixtures.DayAdapterTests.calendar
    visit = fixtures.DayAdapterTests.visit
    employee = fixtures.DayAdapterTests.employee
    daily = fixtures.DayAdapterTests.daily
    approve = drivers.DailyDriverSnapshotTests.approve
    save_policy = capabilities.DailyCapabilityIntegrationTests.save
    rig = rigs.DailyRigIntegrationTests.rig
    allocate = rigs.DailyRigIntegrationTests.allocate

    def setUp(self):
        fixtures.DayAdapterTests.setUp(self)
        self.daily("Crew", self.c1.id, "2026-11-23", "2026-12-04")
        self.daily("Project", self.project.id, "2026-11-23", "2026-12-04")
        self.client = TestClient(create_app(self.database))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.body = dict(
            work_item_id=self.work.id,
            expected_project_id=self.project.id,
            crew_ids=[self.c1.id],
            remaining_days=8,
            remaining_confirmed=True,
            earliest_start_date="2026-11-23",
            horizon_end_date="2026-12-04",
        )
        self.days = [
            DayDraftStore(self.database).save(
                DayDraft(self.work.id, self.c1.id, d, "Synthetic saved A")
            )
            for d in (
                "2026-11-23",
                "2026-11-24",
                "2026-11-25",
                "2026-11-26",
                "2026-11-27",
            )
        ]
        self.scope = [
            dict(
                record_kind="FullDayDraft",
                record_id=a["id"],
                expected_revision=a["revision"],
            )
            for a in self.days
        ]

    def post(self, **changes):
        return self.client.post("/day-impact/preview", json=self.body | changes)

    def fingerprint(self, result, **changes):
        return self.client.post(
            "/day-impact/freshness",
            json=dict(
                query=self.body | changes, input_fingerprint=result["input_fingerprint"]
            ),
        )

    def dump(self):
        with closing(sqlite3.connect(self.database)) as c:
            return list(c.iterdump())

    def test_five_to_eight_and_early_finish_exact_scope_no_writes(self):
        original = self.dump()
        for days, finish in ((8, "2026-12-02"), (2, "2026-11-24")):
            result = self.post(replacements=self.scope, remaining_days=days)
            self.assertEqual(result.status_code, 200, result.text)
            data = result.json()
            self.assertEqual(data["candidates"][0]["proposed_finish_date"], finish)
            self.assertEqual(data["before"]["finish_date"], "2026-11-27")
            self.assertIsNone(data["before"]["remaining_days"])
            self.assertEqual(
                data["downstream_status"], "Needs Review / Unsupported Dependency"
            )
            self.assertFalse(data["applyable"] or data["publishable"])
        self.assertEqual(original, self.dump())

    def test_omitted_scope_never_releases_saved_dates(self):
        data = self.post().json()
        self.assertEqual(data["candidates"][0]["proposed_start_date"], "2026-11-30")
        self.assertEqual(data["replacement_scope"], [])
        self.assertEqual(len(data["protected_records"]), 5)

    def test_invalid_kind_duplicate_foreign_and_stale_scope_reject(self):
        for scope, code in (
            ([self.scope[0], self.scope[0]], 422),
            ([self.scope[0] | dict(record_kind="LegacyHalfDay")], 422),
            ([self.scope[0] | dict(expected_revision=999)], 409),
            ([self.scope[0] | dict(record_id=999)], 409),
        ):
            response = self.post(replacements=scope)
            self.assertEqual(response.status_code, code, response.text)

    def test_confirmation_and_strict_day_inputs(self):
        for fields in (
            dict(remaining_confirmed=False),
            dict(remaining_days=None),
            dict(remaining_days=True),
            dict(remaining_days=0),
            dict(remaining_days=0.5),
            dict(earliest_start_date="2026-02-30"),
            dict(horizon_end_date="2028-01-01"),
            dict(proposed_employee_ids=[1, 1]),
        ):
            self.assertEqual(self.post(**fields).status_code, 422, fields)
        request = ImpactQuery(**self.body).model_dump() | dict(
            remaining_confirmed=False
        )
        with patch.object(
            impact.storage, "connect", side_effect=AssertionError("must not read")
        ):
            with self.assertRaises(ValueError):
                impact.read_impact(self.database, request)

    def test_current_stale_includes_query_and_saved_notes(self):
        data = self.post(replacements=self.scope).json()
        self.assertIn("input_fingerprint", data, data)
        self.assertEqual(
            self.fingerprint(data, replacements=self.scope).json()["status"], "Current"
        )
        self.assertEqual(
            self.fingerprint(data, replacements=self.scope, remaining_days=7).json()[
                "status"
            ],
            "Stale",
        )
        DayDraftStore(self.database).save(
            DayDraft(
                self.work.id,
                self.c1.id,
                self.days[0]["local_date"],
                "Changed synthetic notes",
            ),
            self.days[0]["id"],
            self.days[0]["revision"],
        )
        self.assertEqual(
            self.fingerprint(data, replacements=self.scope).json()["status"], "Stale"
        )
        self.assertEqual(self.post(replacements=self.scope).status_code, 409)
        reload = self.post(replacements=[]).json()
        revised_scope = [
            dict(
                record_kind=r["record_kind"],
                record_id=r["record_id"],
                expected_revision=r["revision"],
            )
            for r in reload["before"]["records"]
            if r["record_kind"] == "FullDayDraft"
        ]
        self.assertEqual(self.post(replacements=revised_scope).status_code, 200)

    def test_read_failure_never_certifies_success_or_leaks_path(self):
        with patch(
            "rigarus_backend.impact_preview_api.read_impact",
            side_effect=SnapshotReadError("secret local path"),
        ):
            for response in (
                self.post(),
                self.fingerprint(dict(input_fingerprint="a" * 64)),
            ):
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("secret local", response.text)

    def test_deterministic_identity_proposed_missing_resources_pending(self):
        a = self.post(replacements=self.scope).json()
        b = self.post(replacements=self.scope).json()
        self.assertEqual(a, b)
        self.assertEqual(a["proposal_id"], a["proposal_fingerprint"])
        self.assertEqual(a["candidates"][0]["resource_state"], "Pending")
        checks = a["candidates"][0]["checks"]
        self.assertIn("ApprovedDriver", {c["check"] for c in checks})
        self.assertIn("ActualRig", {c["check"] for c in checks})

    def test_scope_and_budget_fail_closed(self):
        request = ImpactQuery(**(self.body | dict(replacements=self.scope)))
        with patch.object(impact, "ReadBudget") as budget:
            budget.side_effect = SnapshotReadError("READ_LIMIT_EXCEEDED")
            with self.assertRaises(SnapshotReadError):
                impact.read_impact(self.database, request.model_dump())
        with patch.object(impact, "READ_SECONDS", -1):
            response = self.post()
            self.assertEqual(response.status_code, 503)

    def test_protected_successor_and_legacy_same_integer_identity(self):
        other = ProjectStore(self.database).save(
            ProjectDraft(
                "SYN-B",
                "000B",
                "Synthetic protected successor",
                [WorkItemDraft(None, WorkType.CIVIL, 1, 5)],
            )
        )
        b = DayDraftStore(self.database).save(
            DayDraft(other.work_items[0].id, self.c1.id, "2026-11-30")
        )
        old = self.visit(day="2026-12-01", half="PM")
        data = self.post(replacements=self.scope).json()
        self.assertEqual(data["candidates"][0]["proposed_finish_date"], "2026-12-04")
        self.assertEqual(
            {(r["record_kind"], r["record_id"]) for r in data["protected_records"]},
            {("FullDayDraft", b["id"]), ("LegacyHalfDay", old.id)},
        )
        # New and old namespaces intentionally both start at1.
        self.assertEqual(old.id, self.days[0]["id"])
        self.assertTrue(
            any(
                r["record_kind"] == "LegacyHalfDay" and r["record_id"] == old.id
                for r in data["before"]["records"]
            )
        )
        self.assertIsNone(data["candidates"][0]["proposed_employee_ids"])

    def test_protected_b_alone_finishes_december_third(self):
        b = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2026-11-30")
        )
        data = self.post(replacements=self.scope).json()
        self.assertEqual(data["candidates"][0]["proposed_finish_date"], "2026-12-03")
        self.assertIn(b["id"], [r["record_id"] for r in data["protected_records"]])

    def test_borrowing_collision_rechecks_source_and_target_without_transfer(self):
        p = self.employee()
        source = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c2.id, "2026-11-23", employee_ids=(p.id,))
        )
        original = self.dump()
        data = self.post(
            replacements=self.scope, remaining_days=1, proposed_employee_ids=[p.id]
        ).json()
        self.assertEqual(data["candidates"][0]["resource_state"], "Blocked")
        checks = data["candidates"][0]["checks"]
        self.assertTrue(
            any(
                c["record_kind"] == "FullDayDraft"
                and c["record_id"] == source["id"]
                and c["check"] == "ApprovedDriver"
                for c in checks
            )
        )
        self.assertIn(self.c1.id, data["blocked_crew_ids"])
        self.assertEqual(original, self.dump())

    def test_driver_negative_and_missing_full_day_proof(self):
        p = self.employee()
        self.daily("Employee", p.id, state="Available")
        self.approve(p, state="Suspended")
        data = self.post(
            replacements=self.scope, remaining_days=1, proposed_employee_ids=[p.id]
        ).json()
        self.assertTrue(
            any(
                c["check"] == "ApprovedDriver" and c["state"] == "Blocked"
                for c in data["candidates"][0]["checks"]
            )
        )
        self.approve(p, state="Unverified")
        data = self.post(
            replacements=self.scope, remaining_days=1, proposed_employee_ids=[p.id]
        ).json()
        self.assertTrue(
            any(
                c["check"] == "ApprovedDriver" and c["state"] == "Pending"
                for c in data["candidates"][0]["checks"]
            )
        )

    def test_minimum_level_and_independent_qualification_shortage(self):
        p = self.employee()
        self.daily("Employee", p.id, state="Available")
        self.save_policy(
            "WorkItem",
            self.work.id,
            CapabilityRequirements(2, (1, 0, 0), "Exact", (("SYN-QUAL", 1),)),
        )
        data = self.post(
            replacements=self.scope, remaining_days=1, proposed_employee_ids=[p.id]
        ).json()
        checks = data["candidates"][0]["checks"]
        self.assertTrue(
            any(
                c["check"] == "MinimumStaffing" and c["state"] == "Blocked"
                for c in checks
            )
        )
        self.assertTrue(
            any(
                c["check"] == "SkillsLevel1" and c["state"] == "Blocked" for c in checks
            )
        )
        self.assertTrue(
            any(
                c["check"].startswith("Qualification") and c["state"] == "Pending"
                for c in checks
            )
        )

    def test_rig_maintenance_and_actual_other_crew_occupancy_block(self):
        rig = self.rig()
        row = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c2.id, "2026-11-23")
        )
        self.allocate(row, rig)
        changes = dict(
            replacements=self.scope, remaining_days=1, proposed_rig_id=rig.id
        )
        data = self.post(**changes).json()
        self.assertEqual(data["candidates"][0]["resource_state"], "Blocked")
        DayDraftStore(self.database).cancel(row["id"], row["revision"])
        DailyRigStore(self.database).save_period(
            rig.id,
            "Maintenance",
            RigPeriodInput(
                "2026-11-23", "2026-11-23", "Active", True, "Synthetic service hold"
            ),
        )
        data = self.post(**changes).json()
        self.assertTrue(
            any(
                c["check"] == "ActualRig" and c["state"] == "Blocked"
                for c in data["candidates"][0]["checks"]
            )
        )

    def test_unknown_calendar_and_weekend_cannot_fabricate_finish(self):
        data = self.post(
            replacements=[],
            earliest_start_date="2026-11-28",
            horizon_end_date="2026-11-29",
            remaining_days=1,
        ).json()
        self.assertIsNone(data["candidates"][0]["proposed_finish_date"])
        self.assertEqual(data["candidates"][0]["unfilled_days"], 1)
        self.assertTrue(data["candidates"][0]["skipped"])
        self.daily("Crew", self.c1.id, "2026-11-23", "2026-12-04", "Unknown")
        data = self.post(replacements=self.scope).json()
        self.assertIsNone(data["candidates"][0]["proposed_finish_date"])

    def test_source_changes_outside_horizon_and_legacy_make_stale(self):
        data = self.post(replacements=self.scope).json()
        DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2027-01-04", "Outside shown horizon")
        )
        self.assertEqual(
            self.fingerprint(data, replacements=self.scope).json()["status"], "Stale"
        )
        newer = self.post(replacements=self.scope).json()
        self.assertEqual(newer["outside_horizon_count"], 1)
        self.calendar("Crew", self.c1.id, "2026-11-24", "2026-11-24", "PM", "Working")
        self.assertEqual(
            self.fingerprint(newer, replacements=self.scope).json()["status"], "Stale"
        )

    def test_one_read_transaction_pins_identity_scope_and_resources(self):
        original_read = impact._read_day_sources
        errors = []

        def writer():
            try:
                self.daily("Crew", self.c1.id, "2026-11-23", "2026-12-04", "NotWorking")
            except BaseException as error:
                errors.append(error)

        def read(*args):
            # Identity + target-index reads have pinned the WAL view already.
            t = threading.Thread(target=writer)
            t.start()
            t.join(timeout=10)
            self.assertFalse(t.is_alive())
            return original_read(*args)

        with patch.object(impact, "_read_day_sources", side_effect=read):
            result = self.post(replacements=self.scope).json()
        self.assertFalse(errors)
        self.assertEqual(result["candidates"][0]["proposed_finish_date"], "2026-12-02")
        self.assertEqual(
            self.fingerprint(result, replacements=self.scope).json()["status"], "Stale"
        )

    def test_saved_worker_rig_not_promoted_to_proposed_evidence(self):
        p = self.employee()
        changed = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2026-11-23", employee_ids=(p.id,)),
            self.days[0]["id"],
            self.days[0]["revision"],
        )
        rig = self.rig()
        self.allocate(changed, rig)
        scope = [
            r | dict(expected_revision=changed["revision"])
            if r["record_id"] == changed["id"]
            else r
            for r in self.scope
        ]
        data = self.post(replacements=scope, remaining_days=1).json()
        self.assertIn(p.id, data["before"]["records"][0]["employee_ids"])
        self.assertEqual(data["before"]["records"][0]["actual_rig_id"], rig.id)
        self.assertIsNone(data["candidates"][0]["proposed_employee_ids"])
        self.assertIsNone(data["candidates"][0]["proposed_rig_id"])
        self.assertEqual(data["candidates"][0]["resource_state"], "Pending")

    def test_old_half_day_actual_worker_is_not_ignored(self):
        p = self.employee()
        legacy = self.visit(crew=self.c2.id, day="2026-11-23", half="PM")
        StaffingStore(self.database).save(legacy.id, [p.id], legacy.revision)
        result = self.post(
            replacements=self.scope, remaining_days=1, proposed_employee_ids=[p.id]
        ).json()
        checks = result["candidates"][0]["checks"]
        self.assertTrue(
            any(
                c["record_kind"] == "LegacyHalfDay"
                and c["record_id"] == legacy.id
                and c["state"] == "Blocked"
                for c in checks
            )
        )

    def test_saved_weekend_pending_and_declined_stays_visible_not_capacity(self):
        p = self.employee()
        row = DayDraftStore(self.database).save(
            DayDraft(self.work.id, self.c1.id, "2026-11-28", employee_ids=(p.id,))
        )
        pending = self.post(replacements=self.scope).json()
        saved = next(
            r for r in pending["before"]["records"] if r["record_id"] == row["id"]
        )
        self.assertTrue(
            any(
                c["check"] == "WeekendConsent" and c["state"] == "Pending"
                for c in saved["checks"]
            )
        )
        WeekendConsentStore(self.database).save_for_day(
            row["id"],
            row["revision"],
            p.id,
            WeekendDecision("Declined", True, True, "Synthetic refusal"),
            0,
        )
        declined = self.post(replacements=self.scope).json()
        saved = next(
            r for r in declined["before"]["records"] if r["record_id"] == row["id"]
        )
        self.assertTrue(
            any(
                c["check"] == "WeekendConsent" and c["state"] == "Blocked"
                for c in saved["checks"]
            )
        )
        self.assertNotIn(
            "2026-11-28", declined["candidates"][0]["allocated_working_dates"]
        )
        self.assertEqual(
            self.fingerprint(pending, replacements=self.scope).json()["status"], "Stale"
        )

    def test_dual_sort_is_stable_and_explainably_different(self):
        self.daily("Crew", self.c1.id, state="NotWorking")
        self.daily("Crew", self.c1.id, "2026-11-23", "2026-11-23")
        self.daily("Crew", self.c1.id, "2026-11-27", "2026-11-27")
        body = dict(
            replacements=self.scope,
            remaining_days=2,
            horizon_end_date="2026-11-27",
            crew_ids=[self.c1.id, self.c2.id],
        )
        finish = self.post(**body).json()
        start = self.post(**body, order="EarliestStart").json()
        self.assertEqual(finish["ranked_crew_ids"], [self.c2.id, self.c1.id])
        self.assertEqual(start["ranked_crew_ids"], [self.c1.id, self.c2.id])
        self.assertEqual(finish, self.post(**body).json())

    def test_year_leap_dst_local_dates_and_horizon_deficit(self):
        for start, end in (
            ("2026-12-31", "2027-01-01"),
            ("2028-02-28", "2028-02-29"),
            ("2027-03-15", "2027-03-16"),
            ("2027-11-08", "2027-11-09"),
        ):
            self.daily("Crew", self.c1.id, start, end)
            self.daily("Project", self.project.id, start, end)
            data = self.post(
                remaining_days=2, earliest_start_date=start, horizon_end_date=end
            ).json()
            self.assertEqual(
                data["candidates"][0]["allocated_working_dates"], [start, end]
            )
        incomplete = self.post(replacements=self.scope, remaining_days=10000).json()
        self.assertIsNone(incomplete["candidates"][0]["proposed_finish_date"])
        self.assertGreater(incomplete["candidates"][0]["unfilled_days"], 0)

    def test_detached_projection_has_no_file_sql_network_or_clock_access(self):
        request = ImpactQuery(
            **(self.body | dict(replacements=self.scope))
        ).model_dump()
        original = impact.project_impact

        def verify(*args):
            with (
                patch("builtins.open", side_effect=AssertionError("file I/O")),
                patch("sqlite3.connect", side_effect=AssertionError("SQL")),
                patch("socket.socket", side_effect=AssertionError("network")),
                patch.object(impact, "monotonic", side_effect=AssertionError("clock")),
            ):
                return original(*args)

        with patch.object(impact, "project_impact", side_effect=verify):
            data = impact.read_impact(self.database, request)
        self.assertFalse(data["applyable"] or data["publishable"])

    def test_performance_budget_rejects_oversized_scenario_before_projection(self):
        with patch.object(
            impact, "project_impact", side_effect=AssertionError("must not project")
        ):
            with patch("rigarus_backend.day_recommendation_adapter.MAX_READ_UNITS", 1):
                self.assertEqual(self.post().status_code, 503)

    def test_multi_crew_work_needs_review_and_cancelled_scope_cannot_be_released(self):
        multi = ProjectStore(self.database).save(
            ProjectDraft(
                "SYN-MULTI",
                "MULTI",
                "Synthetic simultaneous crews",
                [WorkItemDraft(None, WorkType.CIVIL, 2, 4)],
            )
        )
        data = self.post(
            work_item_id=multi.work_items[0].id, expected_project_id=multi.id
        ).json()
        self.assertFalse(data["ranked_crew_ids"])
        self.assertIsNone(data["candidates"][0]["proposed_finish_date"])
        DayDraftStore(self.database).cancel(
            self.days[0]["id"], self.days[0]["revision"]
        )
        self.assertEqual(self.post(replacements=self.scope).status_code, 409)

    def test_parent_movement_or_missing_work_invalidates_original_proof(self):
        data = self.post(replacements=self.scope).json()
        self.assertEqual(
            self.post(expected_project_id=self.project.id + 1000).status_code, 409
        )
        self.assertEqual(
            self.fingerprint(data, work_item_id=999999).json()["status"], "Stale"
        )

    def test_large_project_input_and_12_month_horizon_are_bounded(self):
        import time
        from datetime import date, timedelta

        started = time.monotonic()
        data = self.post(
            replacements=self.scope, remaining_days=500, horizon_end_date="2027-11-22"
        ).json()
        self.assertIsNone(data["candidates"][0]["proposed_finish_date"])
        self.assertLess(time.monotonic() - started, 10)
        self.assertGreater(data["candidates"][0]["unfilled_days"], 0)
        self.assertEqual(self.post(horizon_end_date="2027-11-23").status_code, 422)
        for i in range(100):
            project = ProjectStore(self.database).save(
                ProjectDraft(
                    f"SYN-LOAD-{i}",
                    f"LOAD-{i}",
                    "Synthetic load scope",
                    [WorkItemDraft(None, WorkType.CIVIL, 1, 2)],
                )
            )
            DayDraftStore(self.database).save(
                DayDraft(
                    project.work_items[0].id,
                    self.c2.id,
                    (date(2026, 11, 23) + timedelta(days=i)).isoformat(),
                )
            )
        started = time.monotonic()
        loaded = self.post(replacements=self.scope, horizon_end_date="2027-02-28")
        self.assertEqual(loaded.status_code, 200, loaded.text[:300])
        self.assertEqual(
            loaded.json()["candidates"][0]["proposed_finish_date"], "2026-12-02"
        )
        self.assertLess(time.monotonic() - started, 10)


if __name__ == "__main__":
    unittest.main()
