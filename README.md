# Rigarus Offline Dispatch Scheduler

Windows 11 x64 first, with one local operator and an English desktop interface. The application needs no network, account or service during use.

## Build on Windows

Install the .NET 10 SDK. Run from the repository root in PowerShell.

```powershell
dotnet restore Rigarus.sln --locked-mode
dotnet build Rigarus.sln -c Release --no-restore
dotnet test Rigarus.sln -c Release --no-build --no-restore
dotnet run --project src/Rigarus.Desktop -c Release --no-build --no-restore
```

The first restore requires NuGet access. In the app, edit the demo note, select **Save note**, close the window and reopen it. The database is under `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`. Startup and save failures are logged locally by operation and exception type.

Open **Projects** to browse the unscheduled backlog, search by Job #, Site ID or site name, and create or edit projects. Work items are optional. Each one records a type, required crew count and estimated whole half-days.

See the [desktop verification walkthrough](docs/05-DEMO-ACCEPTANCE.md), [architecture](docs/02-ARCHITECTURE.md) and [local Windows ZIP procedure](docs/08-RELEASE-HANDBOOK.md).

## Development

Read [AGENTS.md](AGENTS.md) and the [project plan](docs/00-PROJECT-PLAN.md) before starting an Issue. Use synthetic data for development and tests. Personnel and fleet management, scheduling, imports, exports, backup and install/upgrade workflows are future milestones.
