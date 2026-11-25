# Issue101 daily input foundation — Design Compliance Checklist

Read-at2026-11-25T01:29–01:39Z; owner day-based decision November24 local date.
Public repository verified; origin/main `947da5f6a6fd326592f09f34be26370bfcea47b7`
is human-merged PR100, head9864a6c. main CI45524825467 successful; PR100 exact-head
CI45522726761 successful. Actual open-PR REST array empty. Parent99/26/22/28
Open, current calendar milestone6. Isolated branch
`codex/daily-calendars-availability`; root README/translated README/local design
changes and all other worktrees preserved. Dedicated child101 avoids a second
unreviewable parent-PR expansion. No production/customer database is accessed.

AGENTS.md and DEV-DESIGN-CHECKLIST.md re-read. The six required documents and
affected acceptance sections were re-read; earlier AM/PM descriptions are
historical, subordinate to the owner Full Day decision.

| Source | Last-changing revision | Checkout modification UTC | Sections inspected |
| --- | --- | --- | --- |
|00-PROJECT-PLAN.md|681bb6f07c879cad6f697768d8b74b78f9bb87fc|2026-11-25T01:29:26Z|Current full-day rule, scope/dependencies|
|09-DELIVERY-PLAYBOOK.md|681bb6f07c879cad6f697768d8b74b78f9bb87fc|2026-11-25T01:29:26Z|Day upgrade and engineering/Demo/production gates|
|02-ARCHITECTURE.md|681bb6f07c879cad6f697768d8b74b78f9bb87fc|2026-11-25T01:29:26Z|Daily Draft, recorded availability, working calendars, snapshots|
|03-DATA-MODEL.md|681bb6f07c879cad6f697768d8b74b78f9bb87fc|2026-11-25T01:29:26Z|Actual schema13, immutable old evidence, backup/recovery|
|05-DEMO-ACCEPTANCE.md|681bb6f07c879cad6f697768d8b74b78f9bb87fc|2026-11-25T01:29:26Z|Day compatibility, calendar/availability, native limitations|
|10-CLIENT-DECISIONS.md|1aa07c1447806925672362cde79710e4f479e1fc|2026-11-25T01:29:26Z|Confirmed day rule, legacy/history and Pending safety gates|

`acceptance/2026-11-24-day-based.md` and PR100 checks were inspected. Existing
baseline tests295/packaged12/frontend42/Rust8/.NET35; native day UI/offline
acceptance remains NOT RUN, not inherited from prior engineering success.

Latest accessible local original `Rigarus_UI_Design_Updated_2026-11-24.docx`:
SHA256 d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c,
modified2026-11-24T23:15:38Z. Metadata/text L17–L18 (XML paragraphs89–98) re-read.
Its half-day controls are superseded by the explicit owner rule. **No original
figure or Word pagination is claimed inspected this session:** this slice changes
no frontend/Tauri control/layout; native UI/visual comparison is not applicable
until the separate day UI slice. Actual working-calendar/availability Store/API,
schema, UI selectors and current projection boundaries were inspected.

## Requirements / impact and authority

| Requirement | Authority | Baseline | This slice / acceptance |
| --- | --- | --- | --- |
|Daily Crew/parent Project Working/NotWorking/Unknown; employee Available/Unavailable/Unknown (Not recorded)|Confirmed owner Nov24 and current continuation|Missing slotless evidence store|Independent daily owners/changes/cells, no Slot; blank Unknown; scope-specific states|
|WorkItem inherits Project|Confirmed #26|Existing half-day FK resolution|Daily assessment resolves persisted parent, never WorkItem override|
|Legacy mixed/partial raw evidence Needs Review|Confirmed owner #99|Read-only compatibility report, all old tables retained|Never automatically promote legacy positives; raw halves/change IDs/revision retained alongside daily observations|
|Operator explicit daily assertion, legacy acknowledgement and optimistic read token|Proposed engineering contract implementing owner review boundary|No daily evidence writes|Gate remains default closed; snapshots/revisions bind the reviewed range and source, not authentication or customer approval|
|No stale positive capacity after old edits|Confirmed safety invariant|Old calendar APIs still compatibility paths|Store per-date legacy review receipt plus native legacy revision; later change makes daily positive Unknown/Stale, retain known blockers|
|Clearing cannot revive old half-day availability|Confirmed conservative input rule|Old Unknown deletes cells|Persist an explicit daily Unknown tombstone; never fall back to a positive legacy half/pair|
|No actual-worker/driver/Rig/weekend inference|Confirmed owner|Safety validators partly legacy, full gates missing|Calendar match only; all results Pending and false Apply/Publish|
|Atomic migration/backup/history/concurrency|Confirmed #99/AGENTS|Schema13 verified backup infrastructure|Schema14 additive; reuse consistent backup, broaden recognized previous prefix to13; preserve every old row/ID/event|
|Daily recommendation prerequisites|Confirmed dependency sequence|Legacy generator/snapshot cannot consume daily inputs|Connection-level coherent daily reads; legacy adapter refuses in-horizon daily cells and returns specific Stale reason; daily generator/full snapshots follow separately|

## Implementation Plan — one reviewable input slice

1. Commit this checklist and implementation plan before product edits. Record
   continuation scope and explicit receipt/clear engineering semantics in decisions.
2. Add schema14 DailyCalendarOwners/Changes/Cells, exact one Crew/Project/Employee
   FK per immutable owner. Changes retain native revision, canonical inclusive dates,
   scope-valid state, explicit operator confirmation, legacy acknowledgement,
   original reviewed legacy snapshot/revision, optional notes and UTC event time.
   Cells key owner/local date, no Slot; composite FK/date/context guards; immutable
   owner/history. Unknown is retained, not deleted. No old table/index/event rewrite.
3. Pure daily_calendars.py validates strict IDs/local ranges/states/flags and
   resolves effective states. A missing daily assertion is Unknown even when
   legacy positives cover both halves; legacy closure/unavailability remains
   visible known blocking evidence. Explicit current reviewed daily choices are
   independent new assertions, not automatic conversion. Old raw evidence always
   retains its compatibility Needs Review label. Stale positives become Unknown;
   explicit negative evidence cannot become positive from staleness/absence.
4. DailyCalendarStore exposes bounded same-connection snapshot helpers and public
   read/save/history/WorkItem assessment. BEGIN IMMEDIATE covers owner creation,
   current daily revision + range fingerprint compare, explicit legacy-review
   guard, append event and all current cells. Fingerprints bind scope/ID/range,
   current daily/legacy rows and native revisions, not authority. Per-day receipt
   includes raw old state/change IDs and legacy owner revision; an out-of-range
   old-owner revision change may conservatively require re-review. No-op only
   if state/notes/receipt match; re-review after source change appends an event.
5. Strict separate `/daily-calendars/{Crew|Project|Employee}/{id}` read/save/history
   and inherited assessment endpoints; no slot parameter. Canonical employee
   Unknown is labelled Not recorded. Explicit app-factory test opt-in for daily
   input writes; production default gate closed. Keep day-Draft write gate closed.
   Map missing/stale/invalid/storage to404/409/422/503 without raw diagnostics.
6. Prepare daily DayDraft read feedback (current parent/Crew daily assessment and
   explicit workers' daily availability) if safely bounded without inferring
   membership or approval. Do not implement generator/resource validator/UI.
7. Extend schema whitelist/old half-day snapshot guard to daily cells. In-horizon
   daily input must refuse legacy computation, including explicit Unknown, rather
   than be ignored. Preserve same pinned read and specific Stale reasons. Update
   synthetic older-schema fixture builders/counts only; no operational downgrade.
8. Test pure dates/states/missing/mixed/negative/review/stale/clear; real SQLite
   save/reopen/history/no-op/stale/range rollback/immutable FKs and source context;
   employee/Crew/Project independence and Civil/Tower parent inheritance; both
   old-then-new and new-then-old edits; simultaneous writers, complete concurrent
   WAL reads, fingerprints and logical no-write equality. Schema13→14 full row,
   history/sequence preservation, forced failure/backup/rollback/retry and actual
   packaged prior13 rejection + independent backup reopening. Locked Python/Ruff,
   sidecar, frontend/Rust/Tauri/.NET, synthetic harness, privacy/docs and Windows CI.

No new confirmed-day duration persistence, day allocator/comparator, complete
daily snapshot/validators, #24/#27, UI cutover or Apply/Publish/export. Next
independent PRs follow those dependencies, then native day UI/offline acceptance.
All engineering checks NOT RUN at this pre-code commit; customer Demo D/E and
production approval pending. Keep101/99/22/26/28 Open; Draft PR/human review,
no merge/Release/customer database modification.
