# SQLite data model

## M0 demo fixture

The initial EF Core migration creates `DemoProjects` with a numeric primary key, a unique job number, a site name and a required note. The SQLite constraint limits the note to 200 characters, and the domain limits .NET strings to 200 UTF-16 code units. The migration inserts exactly one fixture, `DEMO-001`, in the same migration transaction. EF records application in `__EFMigrationsHistory`. Reopening preserves operator edits.

The current user's database lives at `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`. Infrastructure opens SQLite with foreign-key enforcement and a five-second command timeout. Initialization enables WAL. Diagnostics are local to the `logs` directory and rotate between two files.

## Project master data

| Table | Fields and constraints |
| --- | --- |
| `Projects` | Generated integer ID, unique Job #, required Site ID and Site Name |
| `WorkItems` | Generated integer ID, required and indexed Project ID, type, positive integer crew count and estimated half-days |

Job # and Site ID are text and preserve leading zeroes. Project creation trims surrounding whitespace and preserves the entered spelling. The SQLite unique index uses `NOCASE`, so ASCII case variants such as `JOB-001` and `job-001` represent the same job. The Site ID can be shared by several projects. Demo A still needs to confirm the required site fields and accepted Job # format, including any non-ASCII case rules.

A project can enter the backlog before any work items are defined. Each work item carries a type (`Small`, `Civil`, `Tower`, or `Other`) and its own crew requirement and estimate. One half-day is the smallest estimate. A project can have multiple work items of the same or different types. This supports an unsplit job and a combined Civil/Tower job. The generated WorkItem ID gives later scheduling migrations a stable foreign key so several visits or crew assignments can reference the same work item. Assignment dates, crew selection and conflict rules belong to the scheduling milestone.

The `AddProjectsAndWorkItems` migration creates empty tables and indexes and adds a foreign key that prevents deleting a project while it has work items. The M0 migration and `DemoProjects` stay in place. `DEMO-001` remains in the demo table with its saved note, and startup still opens that fixture. The unique Job # index applies to `Projects`. Migration tests use temporary SQLite files, including a file upgraded from the original M0 migration.

Project Master uses the existing schema. Search matches literal substrings in Job #, Site ID and Site Name and follows SQLite's ASCII case handling. The backlog contains all master projects until assignments are introduced. An edit updates the selected project and its work items in one transaction. Existing work items retain their IDs and an omitted item is preserved. A duplicate Job # aborts the save and leaves both projects intact.

## Crew roster

The first #8 slice adds the Crews table to the local SQLite database. The stable generated ID survives name, type and status edits. Crew type is Civil or Tower. The roster keeps inactive rows visible and has no hard delete. Search uses literal substrings with SQLite's existing ASCII case behavior. Crew names are labels, so multiple rows may share a name. A roster row is master data and does not establish scheduling eligibility. Employee master data is described below. Foreman assignment history is subsequent work under #8.

The Tauri backend applies its AddCrewRoster migration in the same SQLite write transaction as preceding upgrades, including from M0 and Project Master files. Demo notes and existing project and work-item IDs stay in the same tables. The migration has its own entry in the shared history and preserves the original EF Core entries. A Tauri build from before #8 rejects the newer migration history. Before upgrading a live profile, preserve a verified pre-upgrade backup and use a compatible build or the original database copy for fallback. This branch validates synthetic upgrades and retry after rollback.


## Employee roster

Employees have a stable ID, name, required Home Crew ID, skill level 1 through 3, foreman eligibility and active status. Foreign-key enforcement covers the Home Crew link. Deactivating a crew does not change its employee references. The editor lists inactive crews with their status so existing links can still be read and edited. The roster has no hard delete. Foreman eligibility is a master-data field. Foreman appointments, daily assignments and temporary transfers have their own workflows.

The AddEmployeeRoster migration adds Employees and its Home Crew index within the existing migration transaction. Fresh, M0, Project Master and Crew-only databases take the corresponding upgrade path. The new migration leaves existing note, project, work-item and crew IDs intact. Driver status has a database default and constraint of Unverified. The employee write API has no driver approval field. The earlier Tauri preview rejects the newer migration history, so test fallback with a verified pre-upgrade backup and a compatible build.


## Migration check

The Python backend uses the existing EF Core table and migration identifiers. On a fresh file it creates the demo, Project Master, Crew and Employee schemas. On an M0 file it adds the missing tables and indexes while preserving the note. On a Project Master file it adds the empty Crew and Employee tables in place and preserves project and work-item IDs and values. The schema update runs in a single SQLite write transaction. Unknown migration histories are rejected.

The Python regression suite uses SQL generated by the checked-in EF migration tooling against the synthetic schema. It verifies fresh startup, note edits and restart, M0 upgrade, Project Master data preservation, constraints, and rollback with retry after a failure inside the schema transaction. It uses temporary databases, including the synthetic copy for the upgrade. Verify application-level backup and clean-PC offline upgrade during packaging before using the Python path with business data.

Check for untracked model changes after restoring the local tool manifest.

```powershell
dotnet tool restore
dotnet ef migrations has-pending-model-changes --project src/Rigarus.Infrastructure --startup-project tests/Rigarus.Infrastructure.Tests
```

Before a future schema upgrade on business data, implement and verify an appropriate consistent backup and rollback path. Keep fixture storage separate when introducing real project data.
