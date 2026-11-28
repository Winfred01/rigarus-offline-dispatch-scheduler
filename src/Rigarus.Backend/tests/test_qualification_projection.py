"""Real read-only mixed-board capability proof, never dispatch permission."""

import unittest

import test_schedule_workbench as workbench
import test_daily_capability_snapshot as capabilities
import test_draft_restore as restores
from rigarus_backend.capability_validation import CapabilityRequirements
from rigarus_backend.day_draft_store import DayDraftStore
from rigarus_backend.day_drafts import DayDraft
from rigarus_backend.day_backup import logical_digest
from rigarus_backend.storage import connect
from contextlib import closing


class QualificationProjectionTests(unittest.TestCase):
    setUp = workbench.WorkbenchTests.setUp
    read = workbench.WorkbenchTests.read
    employee = workbench.WorkbenchTests.employee
    daily = workbench.WorkbenchTests.daily
    calendar = workbench.WorkbenchTests.calendar
    visit = workbench.WorkbenchTests.visit
    save = capabilities.DailyCapabilityIntegrationTests.save

    def summary(self):
        with closing(connect(self.database, read_only=True)) as c:
            before = logical_digest(c)
        response = self.read()
        self.assertEqual(response.status_code, 200, response.text)
        rows = response.json()["records"]
        self.assertEqual(
            {r["record_kind"] for r in rows}, {"FullDayDraft", "LegacyHalfDay"}
        )
        self.assertEqual(rows[0]["id"], rows[1]["id"])
        row = next(r for r in rows if r["record_kind"] == "FullDayDraft")
        self.assertEqual(row["validation_status"], "Pending")
        self.assertFalse(row["applyable"] or row["publishable"])
        summaries = [c for c in row["checks"] if c["check"] == "Qualifications"]
        self.assertEqual(len(summaries), 1)
        with closing(connect(self.database, read_only=True)) as c:
            self.assertEqual(logical_digest(c), before)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        return summaries[0], row["checks"]

    def policy(self, codes=()):
        self.save(
            "WorkItem",
            self.work.id,
            CapabilityRequirements(1, (0, 0, 0), "Exact", codes),
        )

    def staffed(self):
        worker = self.employee(home=self.c1.id)
        self.daily("Employee", worker.id, "2026-11-23", "2026-11-23", state="Available")
        DayDraftStore(self.database).save(
            DayDraft(
                self.work.id,
                self.c1.id,
                "2026-11-23",
                "Synthetic qualifications",
                (worker.id,),
            ),
            self.day["id"],
            self.day["revision"],
        )
        return worker

    def test_unknown_policy_remains_one_pending_summary(self):
        self.assertEqual(self.summary()[0]["state"], "Pending")

    def test_explicit_empty_policy_has_satisfied_summary_only_for_this_check(self):
        self.policy()
        summary, checks = self.summary()
        self.assertEqual(summary["state"], "Satisfied")
        self.assertTrue(any(c["state"] == "Pending" for c in checks))

    def test_named_qualification_missing_proof_remains_pending(self):
        self.staffed()
        self.policy((("SYN-Q", 1),))
        summary, checks = self.summary()
        self.assertEqual(summary["state"], "Pending")
        self.assertEqual(
            next(c for c in checks if c["check"] == "Qualification:SYN-Q")["state"],
            "Pending",
        )

    def test_named_qualification_verified_retains_individual_proof(self):
        worker = self.staffed()
        self.policy((("SYN-Q", 1),))
        self.save("Employee", worker.id, "Verified", "SYN-Q")
        summary, checks = self.summary()
        self.assertEqual(summary["state"], "Satisfied")
        self.assertEqual(
            next(c for c in checks if c["check"] == "Qualification:SYN-Q")["state"],
            "Satisfied",
        )

    def test_known_failure_cannot_be_hidden_by_another_satisfied_qualification(self):
        worker = self.staffed()
        self.policy((("SYN-Q", 1), ("SYN-R", 1)))
        self.save("Employee", worker.id, "Verified", "SYN-Q")
        self.save("Employee", worker.id, "NotVerified", "SYN-R")
        summary, checks = self.summary()
        self.assertEqual(summary["state"], "Blocked")
        individual = next(c for c in checks if c["check"] == "Qualification:SYN-R")
        self.assertEqual(individual["state"], "Blocked")
        self.assertTrue(individual["reasons"])

    def test_restore_known_qualification_failure_creates_only_rejected_receipt(self):
        case = restores.RestoreTests()
        case.setUp()
        try:
            worker = case.staff_original()
            case.source(2)
            case.save_policy(
                "WorkItem",
                case.work.id,
                CapabilityRequirements(1, (0, 0, 0), "Exact", (("SYN-Q", 1),)),
            )
            case.save_policy("Employee", worker.id, "NotVerified", "SYN-Q")
            plan = case.rprepare()
            self.assertEqual(plan["status"], "Blocked")
            self.assertTrue(
                any(c["check"] == "Qualification:SYN-Q" for c in plan["blockers"])
            )
            before = case.counts()
            result = case.rpost(case.rrequest(plan)).json()
            self.assertEqual(result["outcome"], "Rejected")
            self.assertEqual(case.counts(), [before[0], before[1], before[2] + 1])
        finally:
            case.tearDown()
            case.doCleanups()
