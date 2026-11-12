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

## Migration check

Check for untracked model changes after restoring the local tool manifest.

```powershell
dotnet tool restore
dotnet ef migrations has-pending-model-changes --project src/Rigarus.Infrastructure --startup-project tests/Rigarus.Infrastructure.Tests
```

Before a future schema upgrade on business data, implement and verify an appropriate consistent backup and rollback path. Keep fixture storage separate when introducing real project data.
