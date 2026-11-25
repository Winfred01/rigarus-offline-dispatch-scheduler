# Project plan for repository use

Owner November25 next-stage priority: full-day weekly workbench and namespaced
Locate (#119), then independent safe daily Draft editing (#120), then human
Apply/locks/transaction revalidation/audit and recoverable schedule versions
(#18/#29/#20), then formal company/Crew/employee PDF/Excel (#17/#71/#32).
Human-merged118 already supplies read-only WorkItem recommendations. This branch
adds read-only weekly visibility, not the daily editor or a completed dispatch
loop. No write/publication gate opens from green read-only checks.

Daily actual-worker consent (#113/#27) adds independent full-day decisions and
roster-bound weekend planning in coherent snapshot v6. Pending/partial/refusal
cannot shorten dates through weekend capacity; all relevant workers confirmed
permits re-proposal only. Membership changes and borrowing recheck both Crews.
See [design](design/2026-11-25-daily-weekend-checklist.md) and
[checks](acceptance/2026-11-25-daily-weekend.md). Overall validation remains
Pending/false flags; production daily writes closed. Next priority is real daily
desktop visibility and visible recommendation previews, followed by #18/#29
transactional human Apply/recoverable versions, then validated PDF/Excel.

Daily Rig safety (#111/#24) adds explicit dated original/actual vehicle evidence,
independent maintenance/inspection/out-of-service periods, whole-date SQL guards
and coherent snapshot v5. Defaults are suggestions, not actual occupancy. Swaps
and date-candidate vehicle choices remain detached proposals with false Apply/
Publish flags. See [design](design/2026-11-25-daily-rigs-checklist.md) and
[checks](acceptance/2026-11-25-daily-rigs.md). Next #27 actual-worker consent,
then day desktop UI/visible recommendation preview/manual Apply, version history
and PDF/Excel export. Category/legal policy and customer acceptance remain open.

Daily2C3 (#109/#25), following human-merged PR108, adds explicit daily
minimum members/Level policy/separate qualifications and both-Crew borrowing
rechecks. Independent schema16 evidence and snapshot v4 never promote legacy
half-day proof. See [design](design/2026-11-25-daily-capabilities-checklist.md)
and [evidence](acceptance/2026-11-25-daily-capabilities.md). All overall results
Pending/false flags, production daily writes closed. Actual #24 Rig/#27 consent,
then visible daily UI/manual Apply remain next; no customer acceptance implied.

Daily2C2 (#107/#23) adds independent full-date company-driver assertions and
actual-worker checks, coherent schema15/v3 snapshots, and explicit read-only
borrowing previews that recheck source and destination. Old half-day approval
never certifies a day. See [design](design/2026-11-24-daily-drivers-checklist.md)
and [checks](acceptance/2026-11-24-daily-drivers.md). #25 staffing/skills/separate
qualifications follows, then actual #24 Rig/#27 consent. All root results remain
Pending / Apply=false / Publish=false; production daily writes stay closed.

Resource slice2C1 (#105/#15) adds whole-date actual-member conflicts and explicit
read-only candidate checks on the daily snapshot. No automatic attendance/source
removal; missing context Pending, known daily conflict Blocked; full dispatch
remains Pending/false flags. See [design](design/2026-11-24-daily-personnel-checklist.md)
and [evidence](acceptance/2026-11-24-daily-personnel.md). Whole-day #23/#25, then
actual #24/#27, day UI and #18/#29 follow; production daily writes stay closed.

Slice2B (#103) connects explicitly confirmed Remaining Days to pure full-date
allocation and coherent schema14 recommendation snapshots. Legacy half-day
contracts remain compatibility-only; new generation uses independent day inputs.
See [design](design/2026-11-24-day-recommendations-checklist.md) and
[evidence](acceptance/2026-11-24-day-recommendations.md). Resource validators and
visible daily UI remain later slices; production daily writes stay closed.

Daily input backend slice2A (#101) follows merged #100: additive schema14,
explicit daily Crew/Project/Employee assertions, legacy review and stale receipts.
See [design](design/2026-11-24-daily-calendars-checklist.md) and
[evidence](acceptance/2026-11-24-daily-calendars.md). Production daily writes remain
closed; day generator/full snapshot/resources and UI are later independent PRs.

## Current owner rule: full local days (November24,2026)

The explicit owner day-based decision supersedes AM/PM and half-day duration
conventions below for **new scheduling contracts**. See [decision](10-CLIENT-DECISIONS.md)
and [Issue99 audit/rollout](design/2026-11-24-day-based-checklist.md).
Preserve legacy half-day records and events without rounding, merging or implicit
conversion. Slice1 supplies additive compatibility/storage and daily Crew safety;
daily calendars/recommendations/resource checks and then day UI follow separately.
Until that cutover, legacy desktop functionality remains a protected compatibility
path and new daily HTTP writes are disabled by default. This is not a completed
day UI upgrade or customer Demo B/E acceptance. Older half-day sections remain
historical implementation context, not authority to undo this decision.

Repository-safe summary of the November 2026 project plan. The source planning documents remain in local development storage.

## Scope

A native Windows 11 x64-first desktop scheduler for one operator. The owner selected Tauri, React/TypeScript and Python FastAPI for the desktop migration in [Issue #42](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/42). Use local SQLite, local attachments and an independent scheduling domain. The WPF/.NET and EF Core baseline provides existing behavior and database compatibility requirements. Validate any supported Windows 10 edition on the target device. The UI is English. The product supports a full-year view and a rolling 3–5 month planning window. Development can use online dependencies and CI. Operation, reporting, data storage and recovery stay local.

Option C gives the operator explainable proposals to preview and approve. Preserve operator locks, explicit publication, recorded approvals, resource constraints and history. Scheduling proposals must leave the database unchanged until explicitly applied in a transaction. The scheduling model and business rules belong to later milestones.

## Milestones

Milestone numbers describe delivery and customer-demo gates, not mandatory coding order. The owner confirmed this dependency-driven sequence on November 23, 2026:

| Priority | Issues | Next required outcome |
| --- | --- | --- |
| 1 | #26 | Persist and edit Crew/Project work calendars; all WorkItems inherit their Project; connect date/AM-PM assessments to Draft planning |
| 2 | #15, #23, #25 | Actual personnel conflicts, approved drivers, staffing, skills and verified qualifications |
| 3 | #24, #27 | Actual Rig occupancy/unavailability and consent from actual weekend workers |
| 4 | #18, #28 | Pure explainable candidates and earliest-start/earliest-finish comparison, using independently validated constraints |
| 5 | #19, #20, #29 | Delay propagation, locks, before/after options and explicit transaction Apply with revalidation |
| 6 | #17, #71, #32 | Validated immutable Published schedules and consistent personal/company PDF/XLSX output |
| 7 | #30–#40 | Complete remaining historical migration, performance, backup/restore, UAT and delivery gates |

Cross-cutting privacy, migration recovery, offline reliability and tests remain required for every affected slice; step 7 consolidates their final acceptance rather than deferring safeguards. #32 also belongs to the final range and is implemented at its earlier export dependency. Existing Issue-specific dependencies still apply: for example Rig collision validation needs actual dated Rig records from #24. The calendar foundation may precede the complete #18 engine; calendar persistence does not depend on first delivering automatic proposals. Do not infer that a milestone or Issue is complete from a scaffold, green CI or its position in this sequence.

PR #83 began with a pure calendar calculation foundation. Full #26 additionally requires storage, editing, inherited Project dates, Draft feedback and matching engineering evidence. Employee availability is one input only; it never replaces personnel, driver, qualification, actual Rig or weekend-consent checks. Calendar-matched Drafts remain unpublishable until all independent hard gates and operator approval exist.

| Milestone | Outcome |
| --- | --- |
| M0 | Private repository, native WPF shell, SQLite migration and synthetic fixture, Windows CI and a restart persistence check |
| M1 / Demo A | Project and work-item CRUD, search, crew and employee roster, rigs and import preview |
| M2 / Demo B | Manual scheduling, explicit half-day assumptions, conflict checks and weekly output |
| M3 / Demo C | Chain impact preview, locks, pause/resume, revisions and timeline |
| M4 / Demo D | Actual crews, drivers and qualifications, borrowing and rig availability |
| M5 / Demo E | Flexible working days, weekend approval and explainable recommendations |
| M6 / Demo F | Reviewed historical import mapping and production-layout reports |
| M7 / RC | Offline install and upgrade, backup and restore, performance and reliability |
| M8 / v1.0 | Customer UAT, approved package, training and handover |

Use an issue and a reviewed PR per slice after the initial repository commit. Publish releases only with explicit approval. Keep all examples fictional.

## #28 phase-two owner scope (2026-11-24)

The owner approved G1 single-Crew WorkItem generation, G2 explicit confirmed
Remaining Half-days, and G3 accumulation across calendar gaps; see the
[decision register](10-CLIENT-DECISIONS.md). Multi-Crew or missing confirmed
duration returns Needs Review. Civil/Tower inherit their shared Project calendar
with separate IDs. No Draft/history deduction is inferred.

The internal Python generator computes proposed local AM/PM dates from supplied
Crew/Project snapshots and sends complete plans to merged PR91's comparator.
Unknown/closed/known-blocked slots and unapproved weekends never count. All
results remain Pending / cannot Apply/Publish. This bounded foundation may
precede full resource validators; it does not fulfil their gates or complete
#28. No UI/API/schema change. See the
[engineering scope](acceptance/2026-11-24-issue-28-generator.md).
Customer Demo E, RC/UAT and production approval remain pending.
