# Issue113 / #27 — Actual-worker full-day weekend consent

## Design Compliance Checklist

Inspected November25,2026 08:00–08:20 UTC. PUBLIC repository
Winfred01/rigarus-offline-dispatch-scheduler; latest fetched main
3d87b27e306b9a3617fe7fcbc433ef333807ba89 (human merge112), main Windows
CI45572428803 passed. No Open PR or112 review submission. Branch
codex/daily-weekend-consent, isolated worktree; unrelated root README/local
design changes preserved. Issue27 and child113, milestone6 M5 Workdays and
recommendations (Demo E), remain Open. Reuse human-merged91/92/94/98/100/102/
104/106/108/110/112 foundations, especially actual-worker borrowing and Rig checks.

Required sources exist/readable and were reread for this slice. Repository
documents are living November2026 summaries, not new customer approvals.

| Source | Revision / identity | Checkout modified UTC | Relevant sections |
| --- | --- | --- | --- |
| AGENTS.md / DEV-DESIGN-CHECKLIST | Mandatory Design-First /d3b9bea | November25 08:03:47 | Workflow/invariants/template |
|00-PROJECT-PLAN.md |7867419 |08:03:47.8641166 | Daily Rig/priority3, Option C, scope/M5 |
|09-DELIVERY-PLAYBOOK.md |7867419 |08:03:47.8681168 | Rig preview, engineering/Demo/production gates |
|02-ARCHITECTURE.md |7867419 |08:03:47.8651178 | Actual members/borrowing, v5 pinned view, daily generator weekend gate |
|03-DATA-MODEL.md |7867419 |08:03:47.8661169 | Schema13–17, immutable history and backup/recovery |
|05-DEMO-ACCEPTANCE.md |7867419 |08:03:47.8671168 | Daily resource/recommendation checks and Demo E limitations |
|10-CLIENT-DECISIONS.md |152eae5 |08:03:47.8681168 | Full Day, actual workers, Open approval/recording authority |
|acceptance/2026-11-25-daily-rigs.md |7867419 |08:03:47 checkout |512 backend tests, source/target rechecks, false flags |
| Local UI Updated2026-11-24.docx | SHA256 d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c | November24 23:15:38.7114232 | L09 consent, L14 details, L20 actual workers |

Original DOCX XML explanatory text inspected, not original images or verified
pagination. L09 says Pending/Approved/Declined; Issue27/latest owner uses
Pending/Confirmed/Declined, adopted for backend contract. Old half-day captions
are historical under confirmed Full Day decision. No UI layout/input/focus change
in this slice; original image comparison N/A, not a GUI pass. Original remains
local. Metadata identifies sources; checkout time does not establish authority.

| Requirement / authority | Current status | Planned change and acceptance |
| --- | --- | --- |
| Confirmed owner November25 / Issue27 T06 | Missing consent source; adapter always skips weekends | Per-worker full-day decision, only all confirmed exact roster permits weekend planning |
| Confirmed actual workers / reassignment recheck | Existing explicit roster/borrowing preview | Bind WorkItem/Project/Crew/date/roster; change invalidates positive consent, recheck both Crews |
| Confirmed missing Pending / refusal Blocked | Existing comparator contract | Reasons per actual employee; never infer consent from HomeCrew/Available/calendar |
| Confirmed immutable history / consistent read | Schema17/v5 | Additive18 with verified17 backup; same pinned view, v6 SHA/Current-Stale |
| Open approval and recorder authority | No authenticated approval role | Explicit internal recorded decision/reference only; no legal authority inference or production writer |
| Confirmed next operator-facing priority | Legacy desktop lacks daily workflow | Next independent slice daily UI/visible preview, then transactional Apply/versions and PDF/XLSX |

## Implementation Plan (before product code)

1. Commit this plan and owner decision before product edits. Add schema18
   immutable consent scope (WorkItem/Project/Crew/weekend date/Employee FKs) and
   append-only Pending/Confirmed/Declined events, revision, exact full-date
   roster fingerprint/snapshot, explicit employee-decision confirmation/reference
   and UTC recording time. No old records/IDs/Slot/history/revisions change.
2. Internal recorder only, BEGIN IMMEDIATE and expected consent revision;
   current saved-day helper checks assignment revision and explicit actual roster
   in that transaction. Planned-roster recording is visibly proposed, never saved
   attendance or employee authentication. No consent HTTP/UI writer or messages.
   Full-day evidence cannot originate from a legacy half. Positive consent needs
   an exact nonempty roster match; latest Pending never resurrects old consent.
   An applicable current Declined remains blocking across roster changes until
   explicitly revised; removed employees are not actual required workers.
3. Pure bounded per-employee assessment uses actual DailyStaffedVisit rosters,
   ignores Cancelled capacity and reports partial legacy attendance Needs Review.
   Weekday consent is not applicable. Missing/unconfigured/empty/stale evidence
   Pending; explicit refusal Blocked even when other evidence is missing.
   Consent satisfaction alone never certifies availability/resources/dispatch.
4. Query may explicitly nominate per-Crew/weekend-date planned workers; no
   HomeCrew inference and alternative Crew plans are not simultaneous visits.
   Observe their employee metadata and consent scope/events/native revisions in
   the existing query-only transaction/budgets. v6 SHA binds query/roster/raw
   consent and revisions, including conservative out-of-range source edits.
   Legacy adapter refuses relevant new consent rather than ignoring it.
5. Daily generator derives WeekendConsent from exact planned roster + snapshot,
   skipping Pending/Declined, permitting fully confirmed weekend calendar capacity
   for planning only. Retain gaps/order/stability and all root false flags.
   Final detached proposal rechecks exact weekend roster and source/destination
   after borrowing through the existing personnel/driver/capability/Rig chain.
   Changed target roster requires a rebuilt query/candidate; source roster change
   cannot inherit an old approval. No write/reservation/Apply/Publish.
6. Extend verified pre-DDL backup prefix through17, atomic DDL/history rollback,
   retry/idempotence/record preservation, actual prior17 binary rejection of18
   and independently restored17 backup. Never delete live migration history.
7. Synthetic tests: pending/partial/all-confirmed/refusal and rescored dates,
   roster/context changes/borrowing/old halves, no inferred workers, known-block
   precedence, strict invalid/bounded inputs, coherent concurrent reads/Stale/
   no-I/O/no-writes, SQL revisions/history/FKs/fault/recovery and closed gates.
   Reproducible console example plus full locked Python/sidecar/frontend/Rust/
   historical .NET, Windows CI/harness/privacy/docs. Initial results NOT RUN.

No desktop/API approval workflow, authenticated recorder role, customer acceptance,
production daily writes, manual Apply/audit/version/export in this backend slice.
Next slice must deliver real daily desktop visibility and visible recommendations,
not another isolated resource algorithm. #18/#29 follows with locks/transactional
revalidation/human Apply/audit/recoverable versions, then validated exports.
Keep113/27/99 Open; one Draft PR, human review, no merge/Release/customer data.

## Implementation refinements and actual checks

Saved confirmations bind the exact saved revision as well as the entire roster,
conservatively including note-only changes; planned positives require separate
saved actual-context review. Per-member planned checks are retained even when a
date is skipped. SQL additionally checks exact saved roster and sequential events;
the lower-level personnel entry also rejects changed target weekend rosters.
These safeguards do not authenticate an approver or introduce a production writer.

Executed:545 backend/33 focused,13 repeated packaged,42 frontend,8 Rust,35 .NET,
locked builds/format, synthetic example/harness and actual17→18 preservation/
verified backup/prior-binary rejection/independent recovery PASS. Staged privacy/
docs PASS (350 indexed paths/nine Markdown sources); exact-head CI recorded in Draft PR after push.
Native day GUI/offline install/reboot/customer Demo/UAT NOT RUN.
See [actual checks and remaining UI deliverable](../acceptance/2026-11-25-daily-weekend.md).
