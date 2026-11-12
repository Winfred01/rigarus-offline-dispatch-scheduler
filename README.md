# Rigarus Offline Dispatch Scheduler

Windows 11 x64 first, with one local operator and an English desktop interface. M0 provides a WPF shell and a synthetic SQLite project with an editable note. The application needs no network, account or service during use.

## Build on Windows

Install the .NET 10 SDK. Run from the repository root in PowerShell.

```powershell
dotnet restore Rigarus.sln --locked-mode
dotnet build Rigarus.sln -c Release --no-restore
dotnet test Rigarus.sln -c Release --no-build --no-restore
dotnet run --project src/Rigarus.Desktop -c Release --no-build --no-restore
```

The first restore requires NuGet access. In the app, edit the demo note, select **Save note**, close the window and reopen it. The database is under `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`. Startup and save failures are logged locally by operation and exception type.

See the [M0 acceptance script and manual walkthrough](docs/05-DEMO-ACCEPTANCE.md), [architecture](docs/02-ARCHITECTURE.md) and [local Windows ZIP procedure](docs/08-RELEASE-HANDBOOK.md).

## Development

Read [AGENTS.md](AGENTS.md) and the [project plan](docs/00-PROJECT-PLAN.md) before starting an Issue. M0 uses one fictional fixture. Project CRUD, personnel and fleet management, scheduling, imports, exports, backup and install/upgrade workflows are future milestones.
