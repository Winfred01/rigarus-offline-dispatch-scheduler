# Project plan for repository use

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
