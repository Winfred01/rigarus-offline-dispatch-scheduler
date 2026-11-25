# Issue107 / #23 — Day-based2C2 approved drivers

## Design Compliance Checklist (before product changes)

Inspected November25,2026 04:44–04:50 UTC. PUBLIC repository
Winfred01/rigarus-offline-dispatch-scheduler; fetched main
`a179b916baa683e743180b80f4f57e28acae2ab5` (human merge PR106).
Isolated branch `codex/daily-driver-validation`. No Open PRs at inspection;
root README/local design changes preserved outside this worktree. PR106 merged,
its exact-head engineering checks passed; main CI45548330939 was in progress.
Issue107 is the single child implementation slice of Open23/99, milestone5
M4 People, drivers and rigs (Open; temporary crew changes, driver checks,
time off and rig replacement). #25 follows, then #24/#27; none are closed here.

| Re-read source | Declared identity / last-changing revision | Checkout modified UTC | Affected sections |
| --- | --- | --- | --- |
| AGENTS.md / DEV-DESIGN-CHECKLIST.md | Mandatory Design-First /d3b9bea | November25 checkout | All instructions/template |
| 00-PROJECT-PLAN.md | November2026 repository summary /1787a8d | 04:44:08 | Current daily rule, priority2, M4, Option C |
| 09-DELIVERY-PLAYBOOK.md | November2026 repository summary /1787a8d | 04:44:08 |2C1/2B previews, engineering/Demo/production gates |
| 02-ARCHITECTURE.md | Current architecture /1787a8d | 04:44:08 | Daily personnel, coherent inputs, company-driver foundation |
| 03-DATA-MODEL.md | Current SQLite /1787a8d | 04:44:08 | Daily observations/schema14/13, driver schema11, recovery |
| 05-DEMO-ACCEPTANCE.md | Living acceptance /1787a8d | 04:44:08 | Daily personnel, daily recommendation, driver follow-up |
| 10-CLIENT-DECISIONS.md | Decision register /2437a81 | 04:44:08 | Day rule,2C priority, driver/qualification authority |
| acceptance/2026-11-24-daily-personnel.md |2C1 engineering /1787a8d | Current checkout | Delivered behavior,479 distinct regressions, limitations |
| acceptance/2026-11-24-issue-23-drivers.md | Legacy #23 engineering /a9967a6 | Current checkout | Internal evidence, dated actual workers, Pending boundaries |
| Local Rigarus_UI_Design_Updated_2026-11-24.docx | SHA256 d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c | November24 23:15:38.7114232 | L14, L17–L20, Demo D–E text extracted |

All sources exist/readable; metadata is observation, not decision authority.
Local original remains in authorized design directory; no original upload.
DOCX XML text inspected, **no page/image rendering or screenshot comparison**.
No UI layout/control/keyboard change; original figures are N/A for backend-only
slice. Its half-day text is historical under the explicit owner daily decision.

| Requirement / authority | Existing implementation | Needed change / acceptance |
| --- | --- | --- |
| Owner2C2 November24 / #23 R03,R11: actual full-date company driver | Legacy half-day validator/schema11 only | Independent daily evidence, actual members, full availability and collisions; never promote two old halves |
| Owner: missing Pending, known ineligible Blocked | Daily personnel snapshot v2 | Driver subchecks with explicit reasons; at least one eligible member, overall Pending/false flags |
| Owner: sole-driver borrowing rechecks both Crews |2C1 never removes source; markers Pending | Explicit revision-bound detached roster overrides, before/after source and target reports, no write |
| Preserve history / current schema14 | Verified pre-DDL backup, additive13/14 | Necessary schema15 separate slotless approval history/cells; rollback/idempotence/prior-binary recovery |
| Consistency/Stale/closed writes | One pinned budgeted query-only snapshot | Include daily approval/raw legacy revisions in same view and SHA256 v3; old adapter refuses daily evidence |
| Open customer policy | No authorization/legal/category/Rig certification | Do not invent authority, automatic expiration, vehicle class or legal qualification |

No numeric staffing/skill rules, actual Rig or weekend consent added. Confirmed
owner development scope is separate from customer Demo D/E acceptance.

## Implementation Plan

1. Record current owner2C2 scope, commit this checklist/plan before product code.
2. Add daily_driver_migration and internal daily_driver_store: additive schema15,
   exact local dates, explicit company/full-day confirmation/reference, expected
   revision plus range review token, immutable history and legacy receipts.
   Keep all old values/IDs/Slot/history/revisions/FKs unchanged. Unknown evidence
   is retained, no positive fallback. Legacy edits invalidate daily positives;
   known unreviewed/stale negatives remain blocking. A fresh explicitly reviewed
   daily assertion can supersede an old negative without changing it.
3. Extend startup backup prefix through14 and migration transaction; rollback on
   failure, idempotent reopen. Independent verified14 backup and compatible prior
   binary is recovery, never delete migration history. No production write route.
4. New pure daily_driver_validation checks actual slotless workers and daily
   employee availability; old attendance remains partial/Pending. Missing staffing
   Pending; explicitly configured empty roster is known zero drivers/Blocked.
   Known worker disqualification cannot count; unknown alternative keeps Pending
   if no eligible worker. One eligible driver satisfies only this subcheck.
5. Extend daily snapshot v3 and saved-driver report; charge new SQL rows and date
   projection to existing read budget. Legacy snapshot reader recognizes15 but
   refuses in-range daily-driver cells. All fingerprints bind raw/new evidence.
6. Detached candidate driver preview reuses2C1 exact-plan/member validation;
   optional immutable source overrides require saved identity/revision/date and
   actual borrowed-member context. Validate all saved/proposed effective members,
   source/destination driver checks, retain before/after. Source known failure
   blocks option; unknown stays Pending. PR91 gets daily Personnel/ApprovedDriver
   evidence. Proposal hash binds normalized overrides and input; no source edit.
7. Synthetic tests: states, old half evidence, full-date availability/collisions,
   source sole-driver loss/replacement, malformed input, strict scope, immutable
   no-I/O core, migration preservation/fault/locks, pinned concurrent view/Stale,
   budgets and unchanged closed gates. Add console example and sanitized docs.
8. Locked Python/Ruff/full suite, packaged sidecar, frontend, Rust/Tauri, legacy
   .NET, synthetic harness, staged privacy/docs, exact-head Windows CI. Record
   actual PASS/FAIL/BLOCKED/NOT RUN; no native GUI/offline/UAT claim without execution.

No desktop/API shape, dependency lock, daily write gate, Apply/Publish/export or
actual transfer changes. Loading/focus/keyboard states N/A, no UI. Main risk is
false promotion/stale approval; independent daily assertions and conservative
legacy receipts address it. Approval authority/category/expiry policy remains
Open; tests establish engineering evidence only. Initial tests **NOT RUN**.
One Draft PR for107, link23/99 and prior106, human review; no merge/Release/closure.

## Implemented evidence

No scope expansion beyond this plan. Source replacement personnel conflicts are
also propagated to the candidate; a driver's presence cannot mask another unsafe
source member. All-roster EmployeeAvailability remains independently Pending.
Main CI45548330939 subsequently completed success. Actual commands/results,
44 focused cases, migration recovery/limitations and523 distinct regressions are
recorded in [acceptance](../acceptance/2026-11-24-daily-drivers.md). Exact-head CI
is reported after push in the final Draft PR; no native/offline/UAT pass inferred.
