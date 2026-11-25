# Issue103 — Day-based 2B Design Compliance Checklist

Read-at2026-11-25T02:25–02:35Z; owner decision November24 local date.
Public repository verified; latest fetched origin/main
`d281ff78feb52681ad77970a1884a1c036586780`, human merge of PR102 head44b50d0.
PR100/102 merged; no Open PR or duplicate2B Issue found. New child103 of99/28,
M5 Workdays and recommendations (Demo E), milestone6 Open. PR102 review array
empty; prior exact-head CI113 success. Main CI45532690079 in progress at inspection.
Isolated branch `codex/day-recommendation-snapshot`; root README/translated README/
local design changes and previous worktrees retained. No customer DB accessed.

AGENTS.md and DEV-DESIGN-CHECKLIST.md reread (revision
d3b9bea778529c47bb502e59914cbdd0100697a0). Six required sources reread with
affected generator/snapshot/day compatibility/acceptance sections. Repository
summaries have no independent numbered version; November24 Full Day rule wins
over retained historical half-day descriptions. Checkout times are not authority.

| Required source | Last-changing revision | Checkout mtime UTC | Relevant sections |
| --- | --- | --- | --- |
|00-PROJECT-PLAN.md|44b50d0df04eff82f182a46174da9999dc4708f9|2026-11-25T02:25:34.7895880Z|Daily foundation, owner rule, dependencies, historical phase2|
|09-DELIVERY-PLAYBOOK.md|44b50d0df04eff82f182a46174da9999dc4708f9|2026-11-25T02:25:34.7927372Z|2A/2B order, engineering/Demo/production gates|
|02-ARCHITECTURE.md|44b50d0df04eff82f182a46174da9999dc4708f9|2026-11-25T02:25:34.7905884Z|Daily inputs, DayDraft, comparator/generator, consistent snapshots/resources|
|03-DATA-MODEL.md|44b50d0df04eff82f182a46174da9999dc4708f9|2026-11-25T02:25:34.7905884Z|Schemas13/14, legacy staffing/calendars/availability, snapshot/recovery|
|05-DEMO-ACCEPTANCE.md|44b50d0df04eff82f182a46174da9999dc4708f9|2026-11-25T02:25:34.7915874Z|2A/day compatibility, #15/#23/#25, #28 adapter/generator, logical SQLite checks|
|10-CLIENT-DECISIONS.md|a1bbf4b92bf0b84c35b10ecee755619c94dd914d|2026-11-25T02:25:34.7927372Z|Confirmed Full Day/continuation; operator confirmation, no inference/automatic conversion|

Current #28/#99/#101 and merged #100/#102 bodies, actual schema14 source,
day_drafts/day_draft_store/daily_calendar_store, old comparator/generator/adapter
and their synthetic tests inspected. Prior daily input acceptance record reread.
Baseline backend324/packaged13/frontend42/Rust8/.NET35; not proof of this slice.

Latest accessible original UI: local design-planning directory,
Rigarus_UI_Design_Updated_2026-11-24.docx, mtime2026-11-24T23:15:38Z, SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`.
L11–L13 explanatory text read at XML paragraphs60–74: preview does not write,
two sort orders, no-feasible diagnostics. Original images/pages were **not rendered
or visually inspected this session**. No UI work: layout/focus/loading/keyboard/
screenshots are N/A, not PASS. Historical half-day captions superseded; Apply/Undo
in concepts require later #18/#29. Original file/path/raw evidence stays local.

| Requirement | Authority/current state | Change / acceptance |
| --- | --- | --- |
|Explicit positive confirmed days|Confirmed owner current2B request; ConfirmedRemainingDays exists, old pipeline half-day|Reuse independent day object; missing Needs Review; reject bool/float/unconfirmed; no estimate/history fallback|
|Local daily generation across gaps/two sorts|Confirmed; missing daily engine|Scan date ordinals, both calendars Working, occupancy/blocker/weekend checks; no reset; partial deficit/no fictitious finish; stable comparison|
|One coherent14 snapshot incl13 Drafts/legacy|Confirmed; daily helper available, old adapter refuses daily|Dedicated day adapter, one pinned mode=ro/query-only transaction, actual parent and all-Crew visits/staffing; detached frozen observations|
|Fingerprint/freshness|Confirmed; legacy v4 exists|New versioned SHA256 over query/confirmation/source/data/revisions; old daily/legacy calendar and visits/staffing changes Stale; failures never Current|
|Pending/closed production writes|Confirmed; existing gates closed|Always Pending/false flags, no route/UI/migration/Apply/Publish; assert source and packaged gates unchanged|
|Resources|Daily validators missing; later2C scope|Retain related daily availability and old driver/capability evidence as observations only; no half-day safety pass or invented actual proposed membership/Rig/consent|

No material business conflict blocks this backend slice. Company approval policy,
Small/Other Crew mapping, historical conversion/operator reconciliation, actual
Rig/consent and full dispatch safety remain Open/Pending; never guessed.

## Implementation Plan (before product changes)

1. Register owner-approved2B scope. No migration: consume current schema14
   (includes schema13 tables); older13/future/invalid DB rejected read-only, not
   upgraded by recommendation code. No duration write/persistence or UI/HTTP API.
2. Extend existing PR91 comparator with true slotless proposed-date/option/result
   contracts. Share checks/evidence, ranking/limit and stable ties; never encode a
   Full Day as fake AM/PM. Retain legacy interfaces/tests as compatibility only.
3. Add day_recommendation_generator.py: frozen daily calendars/evidence/occupancy,
   DayGenerationRequest using ConfirmedRemainingDays or explicit missing None.
   Match scope/IDs/ranges, reject duplicates/invalid inputs. Reuse annual boundary
   semantics (exclusive anniversary, Feb29 clamp, at most366 dates, year9999 safe).
   Scan each local date once; both explicit Working, no known block/occupied date,
   weekends require context-correct Satisfied evidence. Missing occupancy is
   Pending, never known free; persisted adapter always supplies complete occupancy.
   Preserve per-date states/skips/missing checks, accumulated/unfilled days, start/
   finish (finish absent on incomplete), calendar counters and deterministic sorts.
   Multi-Crew/missing duration returns Needs Review; candidates are alternatives.
4. Add day_recommendation_adapter.py: strict day query; one read-only transaction,
   current schema/integrity/FKs, actual WorkItem parent/Crew master/Foreman metadata.
   Reuse connection-level daily snapshots and existing legacy personnel/resource
   readers, not their public Store methods/old generator. Read every Crew's daily
   and legacy visits/current explicit staffing in horizon with distinct ID kinds;
   any active legacy half blocks whole-date selected-Crew occupancy. Cancelled
   retained but releases capacity. No deduction of work already performed.
5. Include related employees (observed actual workers, selected Home Crew/Foreman
   as observations only), daily availability/raw legacy review and old company-
   driver/capability evidence, owners/revisions in the same view. Freeze into
   immutable dataclasses/canonical JSON strings before pure generation; no borrowed
   attendance or resource approval inferred. Validate source/history contexts.
6. Bounded read wrapper charges materialized SQLite rows and generated daily cells
   against shared100,000 work units; 30-second progress/end deadline and five-second
   busy wait. Exceeding limits/read corruption yields no partial fingerprint. Keep
   independent OS/process watchdog requirement; no hard real-time claim.
7. New format-tagged SHA256 over immutable query (confirmed days/Crew IDs/bounds/
   sort/limit), opaque normalized source location, migrations, logical metadata,
   daily/raw old inputs and all visit/staffing/resource observations. No DB/WAL
   byte hashing. Re-read exact query for Current/Stale; missing/moved source Stale,
   schema/storage errors distinct. Owner revisions may conservatively stale outside
   horizon; unrelated unobserved scope stays Current. Current is not Apply authority.
8. Synthetic pure tests: gaps, two sorts/ties, all closed/Unknown, occupancy/missing
   coverage, weekend no proof, known blockers, multi-Crew/missing duration, no0.5/
   conversion, strict IDs/dates/duplicates/context, cross-year/leap/DST/annual max,
   immutability/determinism/no I/O/system-time dependency and bounded computation.
   SQLite tests: real daily inputs/old evidence and namespaced visits, all-Crew
   staffing/borrowing, logical no-writes, coherent concurrent WAL writes/pinned
   reads, stale on each owner/visit/member/metadata change, stale review receipts,
   unrelated scope/checkpoint, missing/corrupt/locked/old/new schema, quota/deadline/
   closed handles and strict gates. Preserve all existing tests.
9. Reproducible synthetic daily example; architecture/model/acceptance updates.
   Run locked Python/Ruff/full suite, packaged sidecar, frontend/Rust/Tauri/.NET,
   synthetic PowerShell harness, docs/privacy and exact-head Windows CI. Native
   day GUI/disconnected install/upgrade/reboot/customer Demo/UAT NOT RUN.
10. Dedicated Draft PR103 child delivery; synchronize #103/#99/#28, keep Issues
    Open. Human review; no merge/Release/customer data access. Next daily safety
    validators #15/#23/#25 then actual #24/#27, UI and #18/#29 remain separate.

All new execution checks NOT RUN at this design-only commit. Existing14 records
and migration history unchanged; operational recovery remains verified backup
with compatible binary, never deleting history. No UI screenshot pass is claimed.
