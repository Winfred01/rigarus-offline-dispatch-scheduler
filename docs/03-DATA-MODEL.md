# M0 data model

The initial EF Core migration creates `DemoProjects` with a numeric primary key, a unique job number, a site name and a required note. The SQLite constraint limits the note to 200 characters, and the domain limits .NET strings to 200 UTF-16 code units. The migration inserts exactly one fixture, `DEMO-001`, in the same migration transaction. EF records application in `__EFMigrationsHistory`. Reopening preserves operator edits.

The current user's database lives at `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`. Infrastructure opens SQLite with foreign-key enforcement and a five-second command timeout. Initialization enables WAL. Diagnostics are local to the `logs` directory and rotate between two files.

Check for untracked model changes after restoring the local tool manifest.

```powershell
dotnet tool restore
dotnet ef migrations has-pending-model-changes --project src/Rigarus.Infrastructure --startup-project tests/Rigarus.Infrastructure.Tests
```

Before a future schema upgrade on business data, implement and verify an appropriate consistent backup and rollback path. Keep fixture storage separate when introducing real project data.
