# Project plan for repository use

Repository-safe summary of the November 2026 project plan. The source planning documents remain in local development storage.

## Scope

A native Windows 11 x64-first desktop scheduler for one operator. Use WPF with .NET 10 LTS, EF Core SQLite, local attachments and an independent C# scheduling core. Validate any supported Windows 10 edition on the target device. The UI is English. The product supports a full-year view and a rolling 3–5 month planning window. Development may use GitHub and NuGet. Operation, reporting, data storage and recovery stay local.

Option C gives the operator explainable proposals to preview and approve. Preserve operator locks, explicit publication, recorded approvals, resource constraints and history. Scheduling proposals must leave the database unchanged until explicitly applied in a transaction. The scheduling model and business rules belong to later milestones.

## Milestones

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
