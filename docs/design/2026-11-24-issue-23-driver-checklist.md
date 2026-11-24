# Issue #23 — dated company-driver evidence and validation

Main baseline 7aec316e1ff2dccf3db8f927d971bdcd3cf96d2e includes human-merged
PR95 (ac0a49e). PUBLIC repository verified; no Open PR. Issue23 Open, milestone5
M4 People/drivers/rigs / Demo D (temporary crews, drivers, time off, rig replacement).
Owner November24 priority plus Continue authorizes this next driver slice.
Root README/Chinese README/local designs untouched; isolated
codex/issue-23-driver-validation worktree. Read source/status at 2026-11-24 UTC.

## Design Compliance Checklist

| Source | Existence/version/read | Last-changing revision | Checkout mtime UTC (not business authority) |
| --- | --- | --- | --- |
| AGENTS.md | Yes, November 2026 baseline | d3b9bea778529c47bb502e59914cbdd0100697a0 | 2026-11-24T22:20:44.312787+00:00 |
| docs/DEV-DESIGN-CHECKLIST.md | Yes, November 2026 baseline | d3b9bea778529c47bb502e59914cbdd0100697a0 | 2026-11-24T22:20:44.319799+00:00 |
| docs/00-PROJECT-PLAN.md | Yes, November 2026 baseline | 2a074876b0d8283578af7464a97ea12837c244d9 | 2026-11-24T22:20:44.314787+00:00 |
| docs/09-DELIVERY-PLAYBOOK.md | Yes, November 2026 baseline | 2a074876b0d8283578af7464a97ea12837c244d9 | 2026-11-24T22:20:44.318291+00:00 |
| docs/02-ARCHITECTURE.md | Yes, November 2026 baseline | ac0a49eadd1eb45bea6db7d7a6810f83063d76ce | 2026-11-24T22:20:44.315787+00:00 |
| docs/03-DATA-MODEL.md | Yes, November 2026 baseline | ac0a49eadd1eb45bea6db7d7a6810f83063d76ce | 2026-11-24T22:20:44.316787+00:00 |
| docs/05-DEMO-ACCEPTANCE.md | Yes, November 2026 baseline | ac0a49eadd1eb45bea6db7d7a6810f83063d76ce | 2026-11-24T22:20:44.316787+00:00 |
| docs/10-CLIENT-DECISIONS.md | Yes, November 2026 baseline | ac0a49eadd1eb45bea6db7d7a6810f83063d76ce | 2026-11-24T22:20:44.318291+00:00 |
| docs/acceptance/2026-11-24-issue-15-personnel.md | Yes, November 2026 baseline | ac0a49eadd1eb45bea6db7d7a6810f83063d76ce | 2026-11-24T22:20:44.329313+00:00 |

Relevant sections: plan Scope/Milestones; playbook Gates; architecture explicit
workers/availability/all-Crew snapshots/collision reports; data Employee roster,
Draft staffing/history/migration compatibility; acceptance saved-Draft and driver
warnings; decisions owner priority and independent checks. Existing roster,
staffing, availability, storage migration, read-only adapter/comparator and tests
inspected. Issue23 R03/R11 and PR95 were checked live. Required checklist is
present in latest main (absent only in stale root checkout).

Local-only November22 UI DOCX SHA256
67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487,
mtime UTC 2026-11-22T08:14:42.434606: XML paragraph152 resource/driver checks.
No rendered page/original figure inspected. UI states/layout/keyboard/focus/ARIA
are not applicable: no UI or HTTP change. Complete originals remain local.
Updated November24 plan/playbook driver sections reviewed: actual dated workers,
source-Crew recheck, unknown never approved; approval responsibility remains a
customer Demo D question. No legal licensing/category rule is inferred.

| Requirement / authority | Existing / needed | Acceptance |
| --- | --- | --- |
| Confirmed owner priority / Issue23 | Actual workers exist; no driver validator | Actual members only, borrowing rechecks source and destination |
| Confirmed Issue23 states | Employee.DriverStatus constrained Unverified | Separate additive evidence tables; preserve original column/invariant |
| Confirmed no missing-evidence success | No real approval records | Missing/Unverified Pending; Active requires explicit company confirmation/reference and exact dated cell |
| Proposed engineering input safeguard | No approval editor | Internal Store requires explicit confirmation for all recorded statuses; bounded local range/AM-PM, revision/history |
| Confirmed independent safety gates | #15 collision and availability snapshots exist | Inactive, unavailable, double-booked worker cannot satisfy; unknown availability Pending |
| Confirmed consistent snapshot | v2 all-Crew staffing | v3 driver cells/revisions read on same connection and fingerprinted |
| Confirmed read-only proposals | No proposed membership/Rig | Saved report only; candidate ApprovedDriver stays Pending, Apply/Publish false |
| Open customer approval responsibility/category rules | No source of authorized roles or actual Rig | No approver role invented; company evidence recorded, not authenticated/certified; category/Rig validation deferred |

## Implementation Plan

1. Add driver_eligibility.py: frozen dated driver cells, explicit range-input
   contract, pure per-visit driver checks; reuse personnel validator for strict
   visit validation/collision context. Missing/empty actual staffing Pending;
   at least one definitely eligible actual worker satisfies only this check;
   all known ineligible Blocked; unresolved possibilities Pending. Same slot
   collision prevents counting the shared driver; no Home Crew inference.
   Active approval plus active employee and Available required; availability
   unknown remains Pending. No weekend/Rig/category/other safety certification.
2. Add schema11 dated DriverApprovalChanges/DriverApprovalCells, no modification
   of Employees.DriverStatus. Necessary because existing CHECK permits only
   Unverified; silently marking it Active would violate existing contract.
   Use existing migration transaction, FK protection, immutable append history,
   per-employee revision, explicit confirmed bounded reference and AM/PM range.
   Internal DriverApprovalStore only: BEGIN IMMEDIATE, expected revision,
   same-change no-op, history/read helpers, rollback. No approval UI/API/role policy.
   Unverified is explicit unknown; no automatic expiry/holiday/attendance inference.
3. Adapter current schema + v3: related employee driver cells/current native
   revision in same pinned view and row budget; detached driver validation/report.
   Old schema rejected by read-only adapter (startup upgrades separately), v2
   snapshots rebuilt. Existing Draft save behavior and comparator unchanged.
4. Tests: states/AM-PM/missing/active/inactive/unknown/unavailable/collision,
   borrowing sole driver and both source/destination, cancellations/permutations,
   year/leap/DST/limits/pure guards; real Store reload/history/stale/no-op/rollback,
   migration10 preservation/failure/retry/FKs/immutable history, same-connection
   concurrent WAL old/new view, fingerprint stale, full logical read immutability.
5. Update decisions/architecture/data/acceptance evidence. Older schema10 builds
   reject schema11; operational fallback needs verified consistent pre-upgrade
   backup and compatible binary, never drop tables/edit history. No customer DB.
6. Locked restores/format/full Python, sidecar packaged, frontend/Rust/.NET,
   synthetic harness/privacy/Windows CI. Native GUI/disconnected install/upgrade
   NOT RUN and customer Demo D NOT RUN; production NOT APPROVED.
7. Draft PR refs23/95/28; keep Issues Open; no merge/Release/Apply/Publish.

## Actual results

NOT RUN at design commit. Execution evidence will record actual outcomes.
