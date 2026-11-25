# Issue109 / #25 — Daily capability2C3

## Design Compliance Checklist

November25,2026 inspection; PUBLIC Winfred01/rigarus-offline-dispatch-scheduler.
Fetched main `a179b916baa683e743180b80f4f57e28acae2ab5`, CI success. Only Open
PR108 covers prerequisite drivers, not this slice; it remains Draft/unmerged at
`0634276a168b75c76aee11f87721643ab25f1349`, CI119 three jobs success. Branch
codex/daily-capability-validation is stacked on that exact head in an isolated
worktree; new Draft PR targets its branch until human merge/rebase. No automatic
merge/rewrite of108. Root README/local design changes preserved. Issue25 and
child109/milestone5 M4 People, drivers and rigs remain Open. #8 master Foreman
context and #106 actual members are reused, not reimplemented.

All required sources reread at current checkout November25 05:22–05:27 UTC.
Modification times are checkout observations, not business decision authority.

| Readable source | Declared version / last-changing revision | Modified UTC | Sections read |
| --- | --- | --- | --- |
| AGENTS.md, DEV-DESIGN-CHECKLIST.md | Mandatory Design-First /d3b9bea |05:22:30 checkout | Instructions/template |
|00-PROJECT-PLAN.md | November2026 repository summary /0634276 |05:22:30 | Daily2C2, scope/milestones/priority2 |
|09-DELIVERY-PLAYBOOK.md | November2026 repository summary /0634276 |05:22:30 |2C previews, engineering/Demo/production gates |
|02-ARCHITECTURE.md | Living architecture /0634276 |05:22:30 | Driver/personnel snapshots, explicit Crew capability requirements |
|03-DATA-MODEL.md | Living SQLite /0634276 |05:22:30 | Schema15/12, owner/history, payloads and recovery |
|05-DEMO-ACCEPTANCE.md | Living acceptance /0634276 |05:22:30 | Daily resource checks and Pending boundaries |
|10-CLIENT-DECISIONS.md | Register /5f3f218 |05:22:30 | Daily scope, explicit Level/count policies, open Foreman/authority |
|acceptance/2026-11-24-daily-drivers.md |2C2 /0634276 |05:22:30 | Source/target,523 regressions and limitations |
|acceptance/2026-11-24-issue-25-capability.md | Legacy #25 engineering /27c7c1c |05:22:30 | Explicit requirements, definite/possible counts, immutable company evidence |
| Local Rigarus_UI_Design_Updated_2026-11-24.docx | SHA256 d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c | November24 23:15:38.7114232 | L14,L17,L19,L20, qualification/borrowing/review text |

Original DOCX stays local in authorized design directory. XML text inspected;
no rendered page/image/screenshot claim. No UI changes, so visual/focus/keyboard
states N/A. Its half-day captions are historical under the owner daily decision.

| Requirement / authority | Existing code | Change / acceptance |
| --- | --- | --- |
| Confirmed owner2C3 November25 / #25 R04/R05/R06 | Legacy capability_validation/store, daily actual personnel/driver checks | Pure daily minimum, Level1/2/3 and independent qualifications; no driver-to-Crew certification |
| Confirmed full-date evidence/no silent promotion | Schema12 half-day policy/proof only | Independent schema16 daily evidence; old positives Pending, known qualification negatives conservative |
| Confirmed actual-member borrowing rechecks both sides | PR108 explicit source overrides and before/after drivers | Reuse same detached effective roster, add source/target capability evidence and blocking to PR91 |
| Confirmed coherent sources/Stale/closed gates | Read-only schema15 snapshot v3 | Same transaction/budget captures all affected WorkItem policies/employee qualifications, v4 SHA and stale regressions |
| Open numeric/legal/Foreman policy | No numeric defaults, Exact/AtLeast explicit, Foreman Pending | Preserve independent overlapping counts, exact codes, unresolved Foreman/authority remain Pending |

## Implementation Plan (before product code)

1. Commit this design and owner scope register first. New daily capability
   contracts reuse CapabilityRequirements and company-defined qualification codes;
   explicit policy has no defaults, explicit empty qualification list is distinct
   from missing policy. Level is not a certificate; Exact/AtLeast is never inferred.
2. Necessary additive schema16: reuse immutable CapabilityEvidenceOwners identity,
   add DailyCapabilityChanges/Cells without Slot. Explicit company/full-date
   confirmation/reference, native daily revision/range token and retained legacy
   snapshots/receipts; immutable history/context guards, atomic range save/no-op.
   Old tables/IDs/half-day values unchanged. Positive legacy qualifications cannot
   count; unreviewed/stale NotVerified remains negative. Fresh reviewed daily
   assertions may supersede old evidence without altering it. Missing/stale daily
   policy Pending; explicit Unknown/None tombstones never resurrect old policy.
3. Extend verified pre-DDL backup prefix through15, migration rollback/retry and
   idempotence; recovery is independent15 backup with compatible prior binary,
   never delete live migration history. Internal recorder only, no API/UI writer.
4. Pure daily validator uses actual members, active/availability/collision context
   and current daily policy/proofs. Confirmed versus possible counts per minimum,
   each Level and code; possible upper bound below explicit minimum Blocked,
   unknown evidence Pending. Unconfigured staffing has no known upper bound.
   Configured empty roster has known zero. Legacy half-day attendance never
   supplies confirmed daily capacity. Crew type/inactive checks reuse existing
   contexts; Foreman/merger/effective-date rules stay Pending. Bounded indexing.
5. Extend daily snapshot v4 in the same pinned transaction/read/projection limits;
   include policies for target and all saved source WorkItems plus all related
   employee qualification owners/codes/receipts. Native old revisions invalidate
   positives and old/new edits expire snapshots. Legacy adapter refuses new cells.
6. Reuse PR108 driver proposal/overrides to construct exactly the same effective
   rosters; add detached before/after capabilities and source/target states to
   day comparator (MinimumStaffing/Skills/Qualifications/CrewType). Source shortage
   blocks even when target driver passes. All root results Pending/false flags.
   No Home Crew inference, transfer/actual write, Apply or publish/export route.
7. Synthetic pure, SQL/store/migration, concurrent snapshot/Stale, source/target,
   malformed/duplicate/boundary/budget/no-I/O/no-write tests; reproducible example.
   Full locked Python/Ruff, sidecar, frontend, Rust/Tauri, legacy .NET, synthetic
   harness/privacy/docs and exact-head Windows CI. Initial outcomes NOT RUN.

No UI/API/dependency/gate change. #24 Rig/#27 consent and daily UI/manual Apply
remain later slices. Customer Demo D/E, authority/legal policy and production
approval are separate and pending. One Draft PR for109, human review, no merge,
Release, Issue closure, real data upload or customer database modification.

Pre-verification refinement: bounded JSON payloads can still amplify total memory.
Add a shared64MiB SQL/projected-text byte budget alongside existing100,000 read
units and deadline; bound retained legacy capability JSON to250,000 characters.
This technical workload bound is not a company rule; errors return no fingerprint.

## Delivery baseline refresh

PR108 was subsequently human-merged to main
`15879cd72832e9a90047220f184684fb819c822e`, main CI45553296541 success; no review
submissions were present. Its product/document tree equals the previously inspected
0634276 dependency tree. Rebased this isolated branch onto that latest main with
all pending work preserved; original pre-code plan07e8303 is now c9f9801. New PR
therefore targets main directly, and contains only2C3. No dependency/source/scope
change or repeated implementation was needed. Full results are recorded in
[acceptance](../acceptance/2026-11-25-daily-capabilities.md). Human review remains
required, production gates stay closed, native/offline/customer acceptance pending.
