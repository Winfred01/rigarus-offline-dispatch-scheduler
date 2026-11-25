# Issue99 Day-Based Scheduling — Design Compliance Checklist

## Baseline and authority

Read-at2026-11-25T00:25–00:34Z (owner decision November24 local date).
Latest fetched origin/main `f6af09f4f63060fec5f8097a4e80e4a9a65d341d`;
branch `codex/day-based-draft-compat`, isolated worktree. Root README changes,
untracked translated README/design originals and other worktrees preserved.
Public visibility verified through GitHub API. No open PRs (actual REST array
empty; PowerShell wrapping an empty array misleadingly reported count1).
main Windows CI45516482368 successful; PR98 CI45514117801 all3 successful.
Dedicated [Issue99](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/99)
created after title search found no existing day-based upgrade.

AGENTS.md and DEV-DESIGN-CHECKLIST.md re-read before implementation.
Required sources re-read, relevant acceptance/code/test sections inspected:

| Source | Revision | Checkout modified UTC | Relevant sections |
| --- | --- | --- | --- |
| docs/00-PROJECT-PLAN.md |2a074876b0d8283578af7464a97ea12837c244d9|2026-11-25T00:25:54Z|Scope, dependencies, M2–M5, G1–G3|
| docs/09-DELIVERY-PLAYBOOK.md |2a074876b0d8283578af7464a97ea12837c244d9|2026-11-25T00:25:54Z|Engineering/Demo/production gates, generator preview|
| docs/02-ARCHITECTURE.md |b89e35e9bc7bf82bf30b8989c7803f2373b926c0|2026-11-25T00:25:54Z|Draft/staffing/availability/calendars/Locate/snapshots/validators|
| docs/03-DATA-MODEL.md |27c7c1c6a6dfdc4bc2d6f17da4cd2706304a2ec7|2026-11-25T00:25:54Z|Schema12, immutable history, legacy EF, backup/fallback|
| docs/05-DEMO-ACCEPTANCE.md |b89e35e9bc7bf82bf30b8989c7803f2373b926c0|2026-11-25T00:25:54Z|Draft/worker/calendar/adapter/Locate checks, native/offline conditions|
| docs/10-CLIENT-DECISIONS.md |b89e35e9bc7bf82bf30b8989c7803f2373b926c0|2026-11-25T00:25:54Z|Earlier AM/PM and G2 decisions superseded for new contracts; other safety gates retained|

Latest accessible original `Rigarus_UI_Design_Updated_2026-11-24.docx` in the
authorized local design directory: SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`,
modified2026-11-24T23:15:38Z. XML paragraphs/original embedded images inspected;
Word pagination not verified. L01(image53), L02(image54), L03(image55, prior
Locate inspection), L06(image58), L14(image66, prior Locate inspection),
L17–L18(image69–70), L20(image72), historical Crew Board figure(image8).
They are prototype references, not implemented day-based product screenshots.
No newer daily design or dedicated Working Calendars original figure was found;
its actual working-calendar.tsx controls/state and existing acceptance were
inspected. Keep layout vocabulary; explicit owner's day-based instruction
supersedes half-day captions. No visual change belongs to this first slice.

Issues14/15/16/22/23/24/25/26/27/28/71 re-fetched: Open, M2/M4/M5 dependencies.
PR91/92/94/95/96/97/98 re-fetched: merged; comparator, allocator, snapshot,
personnel, drivers, capability and Locate respectively. Current schema12 was
verified from storage.py and migration modules, not inferred from old docs.
Acceptance records for those slices remain engineering evidence only.

## AM/PM impact matrix (audited current sources)

| Surface | Storage / wire / rule dependency | This slice / later requirement |
| --- | --- | --- |
| assignments.py, assignment_store.py, assignment_api.py |DraftAssignments Slot CHECK AM/PM, partial Crew/date/slot uniqueness; strict request/response; date/revision/staffing context|Keep historical table/IDs unchanged; add slotless daily contract/table; cross-model SQL protection and actionable old-Store conflict|
| storage.py, staffing.py, staffing_persistence.py, staffing_store.py |AssignmentStaffingChanges date/Slot/revision, immutable members; FK to old assignment|Never repoint/rewrite history; new daily revision history with explicit Employee IDs and distinct unconfigured/empty selection|
| projects.py/project_api/store, bulk/import and WorkItems |EstimatedHalfDays positive integer stored and editable; no confirmed Remaining Days source|Legacy master/import unchanged in slice1; new confirmed-days domain contract never derives from estimates or divides/rounds half-days; project UI later|
| work_calendars.py, working_calendar_store/api.py, calendar_migration.py |Crew/Project owner, exact date/half cells; FullDay history expands to two cells|Read conservative compatibility observations only; daily read/write/version contract in slice2; preserve Project inheritance|
| availability.py, availability_store/api.py |Employee date/half cells and FullDay/AM/PM change history|Only both Available constitutes complete legacy coverage; missing/mixed remains review, unavailable is known blocker; no automatic conversion|
| recommendation_generator/comparison/example.py |DateSlot/ProposedSlot, confirmed half-day counts, AM-before-PM sorting and gaps|Leave legacy foundation/tests; new daily generator/comparator in slice2, no silent input coercion|
| recommendation_adapter.py |schema/table whitelist, same read transaction, v4 fingerprint/revisions, all-Crew half-day sources|Recognize additive schema; refuse legacy snapshot generation when any daily visit exists in horizon; freshness returns Stale on that context change; daily snapshot in slice2|
| personnel_conflicts.py, driver_eligibility/store/migration.py, capability_validation/store/migration.py |Employee/date/half grouping, exact approval/requirement/qualification evidence and immutable context|Compatibility preserves both values; no half-day resource evidence certifies a daily visit; daily validators in slice2|
| rig_store/rigs; future #24/#27 |Master/default Rig is not actual occupancy; maintenance/inspection/actual-worker consent missing|No fabricated actual Rig, driver or consent; all daily drafts Pending, Apply/Publish false; daily hard gates later|
| schedule.tsx, assignment-fields.ts, schedule-locate.ts, system-tools.tsx |AM/PM editor, card/Review labels, target ID/date/focus/timer|Unchanged legacy UI in slice1; default daily HTTP write gate closed until visible day UI; future Locate uses record kind + stable ID/date, never half as identity|
| week.ts/week-cells.ts, desktop.css, employee-week-data/employee-week.tsx |Local Sun–Sat dates; combine complete AM+PM pairs into strips; worker availability per half|Keep date helpers; daily strip/projection and legacy review cards in slice3|
| working-calendar.tsx/fields, availability.tsx/fields, staffing.tsx, projects.tsx/work-item-validation.ts |New-write FullDay/AM/PM selectors, actual-worker context, half-day estimates|Daily controls and requirements in later independent UI slice; do not claim controls removed now|
| Rust main.rs/sidecar.rs, packaged sidecar, Python/frontend/native harness and .NET regressions |Forward slot-bearing old routes; exact schema counts/legacy fixtures; raw saved IDs|No new Rust/UI commands; old paths stay protected; update only synthetic migration fixtures/count expectations and add daily/backend tests|
| Historical versions/publication/export |No current immutable Published or Apply workflow; snapshot fingerprints detached|Do not alter any saved events or infer historical completion; no export/distribution/Apply/Publish enabled|

## Confirmed requirements and planned implementation

All new daily contracts: local YYYY-MM-DD, FullDay unit, stable WorkItem/Crew IDs,
Draft/Cancelled/revision, explicit staffing, positive integer confirmed days,
Pending and false Apply/Publish. No AM/PM parameter, 0.5-day, inferred workers,
duration deduction, default weekdays/holidays/weekend consent or rounding.
Old IDs/Slot/notes/revisions/relationships/evidence/events remain unchanged.

### Implementation Plan — slice1 only

1. Register **Confirmed (owner development scope): Day-based scheduling,
   November24,2026**; label old granularity decisions historical/superseded.
   Add this audit and architecture/data/acceptance scope; commit design before code.
2. Add schema13 `AddDayDraftCompatibility`: independent DayDraftAssignments,
   DayDraftChanges and DayDraftMembers. No destructive table rebuild or global
   Crew/date index on legacy rows. Daily partial unique Crew/date index plus
   symmetric INSERT/UPDATE overlap triggers protect old/new paths, including
   direct SQL and concurrent writers; Cancelled releases occupancy. Old AM and
   PM may coexist unchanged. Daily and legacy integer IDs have separate explicit
   record-kind namespaces/routes; never pass a daily ID to old Locate/read/edit.
3. Before DDL on an existing recognized older profile, hold BEGIN IMMEDIATE and
   use another pinned read connection + SQLite backup API into a new exclusive
   local backup. Verify logical schema/rows/sequence/history, integrity and FKs.
   Failure aborts upgrade. Retain backup; rollback failed DDL transaction; retry
   is safe. Operational fallback uses a verified independent backup and matching
   old binary, never DELETE migration history or destructive downgrade in place.
4. Pure day_drafts.py validates slotless input and explicit positive confirmed
   days (separate from legacy WorkItems estimates). DayDraftStore provides
   transactionally protected create/edit/cancel/read/list/history, explicit
   membership and append-only snapshots; stale revisions/no-op/context changes
   tested. Internal Store remains testable independently of UI.
5. Add distinct day-draft HTTP read/write/history/compatibility routes with strict
   extra-forbidden models, sanitized 404/422/409/503. **Daily HTTP writes default
   disabled** until UI/snapshot/resource integration; tests explicitly opt in.
   Existing half-day UI/APIs remain unchanged compatibility functionality under
   owner's staged-rollout allowance, with new cross-model conflict guard. No
   production day switch, automatic conversion or two unprotected occupancy rules.
6. Read-only bounded compatibility report: legacy visits grouped by Crew/date,
   same WorkItem halves/different work/single half retained with IDs/Slot/status;
   calendars/availability/driver/qualification/requirements retain each original
   value/change context, complete versus partial/mixed coverage and known blockers.
   Reports say Legacy Half-Day Record / Needs Review / Conversion Required;
   they do not create daily cells, assignments or complete resource approvals.
7. Update legacy adapter schema whitelist and reject daily records within its
   horizon before producing half-day snapshots; retain consistent read boundary,
   staleness/error distinction and existing tests. No new daily allocator or
   resource validator is claimed. Daily Draft save is planning storage only;
   calendar/resource approval remains Pending and cannot Apply/Publish.
8. Synthetic tests: schema12→13 full logical preservation, same/different/single
   halves and mixed evidence, backup W​AL recovery, post-DDL failure/rollback/retry,
   indexes/triggers/direct SQL/FKs/history, concurrent same/day and legacy/day
   writers, daily CRUD/restart/cancel/revision/staffing, strict inputs/date
   boundaries, snapshot refusal/Stale/consistent concurrent reads and no-write
   compatibility reports. Keep all existing tests. Run locked Python/Ruff,
   packaged sidecar, frontend, Rust/Tauri and historical .NET; privacy + Windows CI.

## Deferred independent PRs / unresolved business questions

Slice2: daily calendar/availability writes, explicitly confirmed Remaining Days,
daily generator/comparator and full snapshot/freshness, daily #15/#23/#25 checks,
then actual Rig/maintenance/inspection #24 and actual-worker weekend consent #27.
Slice3: day WorkItem estimates/new Draft editors, board/Employee Week/legacy badges,
record-kind-aware Locate/continuous day strips; native Windows/offline upgrade.
No settled rule is reopened. Owner/customer must decide historical conversion
membership/work attribution, partial/mixed evidence reconciliation, odd half-day
estimates and explicit daily remaining work; nothing is silently converted.

All engineering checks NOT RUN at this pre-code design commit. GUI/offline
installation/upgrade/reboot/customer Demo B/E/UAT NOT RUN; production not approved.
One Draft PR refs99, keep related Issues Open; no merge/Release/customer DB access.
