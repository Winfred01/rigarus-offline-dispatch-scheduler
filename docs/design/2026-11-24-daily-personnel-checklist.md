# Issue105 — Daily personnel conflicts (2C1) Design Compliance Checklist

Read-at2026-11-25T03:42Z onward; owner continuation dated November24 local time.
Latest fetched main `98eacce9a2767b958133a7e6750af2215988ec40`, human merge
PR104 head10b9b9a. Public repository; Open PR array empty; no duplicate active
daily-personnel work. Child105 of15/99, M2 Manual scheduling/weekly view (Demo B),
milestone3 Open. #15/#23/#25/#99 Open. PR104 review array empty; exact-head
CI115 passed; main CI45541369845 in progress at initial inspection. Separate
branch `codex/daily-personnel-conflicts`; unrelated root README/translated README/
local design and all other worktrees preserved. Synthetic data only.

AGENTS.md and DEV-DESIGN-CHECKLIST.md reread (revisiond3b9bea). Required sources'
affected sections reread below; repository-safe summaries have no independent
numbered version. Existing day-based2B acceptance and legacy personnel tests/code
inspected; baseline backend364/packaged13/frontend42/Rust8/.NET35. These do not
prove this new slice. Checkout mtime is recorded, not business authority.

| Source | Last-changing revision | Checkout mtime UTC | Sections reread |
| --- | --- | --- | --- |
|00-PROJECT-PLAN.md|10b9b9a70e3843317cc4e6ff1979042ea0cca9ba|2026-11-25T03:42:39.8894716Z|Current Full Day rule,2B/dependencies/remaining resources|
|09-DELIVERY-PLAYBOOK.md|10b9b9a70e3843317cc4e6ff1979042ea0cca9ba|2026-11-25T03:42:39.8919750Z|2B preview, independent resource slices, engineering/Demo/production gates|
|02-ARCHITECTURE.md|10b9b9a70e3843317cc4e6ff1979042ea0cca9ba|2026-11-25T03:42:39.8894716Z|Daily engine/snapshot, day compatibility, explicit workers and legacy #15|
|03-DATA-MODEL.md|10b9b9a70e3843317cc4e6ff1979042ea0cca9ba|2026-11-25T03:42:39.8904714Z|Current14 incl13 day Drafts, staffing/current history, daily/raw evidence, saved personnel|
|05-DEMO-ACCEPTANCE.md|10b9b9a70e3843317cc4e6ff1979042ea0cca9ba|2026-11-25T03:42:39.8904714Z|Daily2B/2A, legacy personnel/driver/capability/adapter checks|
|10-CLIENT-DECISIONS.md|65f63c1a3e9f347e952c7cffe4bbc729bee5f313|2026-11-25T03:42:39.8929791Z|Full Day supersession,2B/2C priority, no attendance/approval inference|

Latest accessible original UI: authorized local design-planning directory,
Rigarus_UI_Design_Updated_2026-11-24.docx, mtime2026-11-24T23:15:38Z, SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`.
L14 explanatory text at XML paragraphs77–79 and L17–L18 at90–99 reread for
actual-worker/availability boundaries. No original page/image rendered or visually
inspected this session. UI/loading/focus/keyboard/screenshot comparison N/A:
backend-only slice, no UI changes. Original file/raw evidence remains local.

## Requirements / authority and design differences

| Requirement | Authority / existing state | Needed change / acceptance |
| --- | --- | --- |
|Same employee/date across different Crews Blocked|Confirmed latest owner request; old validator groups by AM/PM|Independent whole-date grouping across day/legacy/proposal records, retain raw slots and stable namespaces|
|Legacy halves cannot be ignored|Confirmed;2B includes all-Crew legacy/current membership|Any old half participates in full-date checks, including opposite old halves in different Crews; original records/history and old half-day validator unchanged|
|Missing evidence Pending|Confirmed; new daily subcheck missing|Empty/unconfigured/partial scope Pending; unknown other-Crew staffing on same date prevents a false clear result; known conflicts still Blocked|
|Explicit proposed workers only|Confirmed no Home Crew attendance; generator has no actual members|Read-only candidate membership contract, bind exact generated plan/snapshot; default unstaffed recommendations stay Pending|
|Borrow source rechecks|Confirmed; driver/minimum/qual daily validators absent|Never silently remove source membership. Report source references and mandatory Pending rechecks; #23/#25 remain following slices, no safety certification|
|One coherent snapshot / Stale|Confirmed;2B v1 captures saved actual workers|Optional explicit proposed-employee observations in same transaction, v2 SHA256 and pure proposal fingerprint; changes cannot reuse old recommendation proof|
|Closed gates|Confirmed latest2C scope; currently closed|No migration/UI/HTTP/writes/Apply/Publish; retain full regression and exact-head CI|

Issue15's original "different AM/PM valid" acceptance is historical for its old
half-day contract. The explicitly confirmed Full Day rule and latest daily-person
instruction override that granularity for new daily validation. It is not a
historical data conversion or a claim those old records violated the former rule.
Known daily conflicts block the daily subcheck; old IDs/slots remain traceable.
Company driver/qualification authority, minimums and full transfer semantics stay
Open/Pending; do not guess. No new business default is introduced.

## Implementation Plan (before product code)

1. Register owner2C scope. No schema migration or duration/UI/API/write change.
   Consume current14 from one query-only transaction as in2B; keep production
   daily-input/day-Draft gates closed. Dedicated Issue/PR105 child scope #15 only.
2. Add pure daily_personnel_conflicts.py frozen dated visit/reference/conflict/
   check/report contracts with record-kind namespaces (FullDayDraft, LegacyHalfDay,
   Proposal), stable ID/revision/WorkItem/Project/Crew/date, optional raw legacy
   half and explicit actual employee IDs. Slot is history locator, never capacity
   for new daily records. Require strict IDs/dates/status/configuration/immutable
   unique members and bounded annual range; reject inconsistent duplicates and
   existing Crew occupancy violations, preserve Cancelled identity but ignore load.
3. Index active memberships by (local date, Employee ID); >=2 distinct Crews
   creates EMPLOYEE_DOUBLE_BOOKED_DAY with all affected stable references. No
   pairwise worker loop. Missing/empty/incomplete staffing remains Pending; unknown
   other-Crew membership on the same date prevents a false Satisfied clear check.
   Known conflicts stay Blocked in partial scope. Overall Validation Pending and
   false Apply/Publish even when this single collision subcheck is Satisfied.
   Bounds100,000 visits/memberships; deterministic sorting and linear materialization.
4. Integrate validate_day_snapshot_personnel into existing day adapter and attach
   saved-only report to PersistedDayRecommendations. Do not promote personnel
   evidence into unstaffed generated candidates. Retain all-Crew day/legacy input
   and actual revisions/current staffing, never union historical member snapshots.
5. Extend DayRecommendationQuery with optional immutable proposed_employee_ids
   (technical max1000) only to capture explicit candidate workers' metadata/daily
   availability/old resource observations in the same pinned view, including unused
   borrowed workers. No automatic selection. Missing explicit ID is lookup failure;
   unknown uncaptured proposal context cannot pass. Keep all read/deadline budgets.
   Bump daily snapshot format to v2; re-read same query for Current/Stale; v1 proofs
   must rebuild. No global revision, authentication or Apply authority implied.
6. Add day_personnel_validation.py read-only detached candidate check. Verify exact
   candidate against regeneration from its supplied snapshot; explicit immutable
   per-date members or missing None, reject duplicate/out-of-plan dates. Capture
   candidate/input/proposal fingerprints. Combine one candidate alternative at a
   time with saved actual visits, never combine mutually exclusive alternatives.
   A borrowed worker still saved in another Crew conflicts; source never removed.
   Source actual references require driver/minimum/skills/qualification rechecks
   marked Pending; no Home Crew source inferred without dated membership.
7. Bind per-date PersonnelConflicts subcheck to PR91 true-day comparator for that
   explicit candidate: Blocked excludes before limit; missing membership/context
   Pending; clear collision check is not employee/driver/qualification approval.
   Return saved/all-scope diagnostics separately from candidate-related state,
   so unrelated conflicts are not evidence about unselected workers. Full safety
   and all Apply/Publish remain Pending/false. Reuse snapshot freshness helper.
8. Tests: daily/daily, daily/old AM or PM, old opposite-half cross-Crew under new
   rule, same Crew old halves/no new overlap, equal namespaced IDs,2/3+ Crews,
   multiple workers/projects/dates, cancellation, empty/unknown/partial scope,
   known blockers despite gaps, deterministic/frozen/no I/O/clock and workload
   boundary. Snapshot/proposal tests: real saved staffing/latest revision/borrowing,
   explicit extra employee same-view evidence, no source attendance inference,
   candidate-context mismatch, comparator exclusion/Pending, source recheck markers,
   proposal/input fingerprints, staff/visit/employee/availability updates Stale,
   pinned concurrent reads and complete records, source errors/quota/deadline,
   read-only logical equality and both production gates still closed.
9. Synthetic example; architecture/model/plan/playbook/acceptance updates. Locked
   Python/Ruff/full tests, packaged sidecar, frontend/Rust/Tauri/.NET, synthetic
   PowerShell harness, docs/privacy/exact-head Windows CI. Native day GUI,
   disconnected install/upgrade/reboot/customer Demo/UAT NOT RUN, no implied pass.
10. Draft PR, synchronize105/15/99 (and28 recommendation follow-up), keep Issues
    Open. Human review, no merge/Release/customer DB access. Next #23/#25 whole-day
    eligibility, then actual #24/#27, UI and #18/#29 transactional manual Apply.

All new execution checks NOT RUN at this pre-code commit. Existing schema/history/
Drafts/worker selections unchanged; prior recovery design remains independent
verified backup plus compatible binary. No operational down migration.
