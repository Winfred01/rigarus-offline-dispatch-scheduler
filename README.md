# Rigarus Offline Dispatch Scheduler

English · [简体中文](docs/README.zh-CN.md)

Windows 11 x64 first, with one local operator and an English desktop interface. The application needs no network, account or service during use.

## Install on Windows 11 x64

1. Copy `Rigarus-Dispatch-x64-setup.exe` to the computer where you want to use Rigarus.
2. Double-click the installer and follow the prompts.
3. Select **Run Rigarus Dispatch** at the end of setup or open it later from the Start menu.

The installer includes the Python runtime, SQLite, and Microsoft's WebView2 offline installer. Setup uses the included WebView2 installer if Windows has no registered runtime. Operators do not need to install Python, Node.js, Rust, .NET, or Visual Studio. Internet access is unnecessary during setup and use.

On first launch, **Dashboard** shows a synthetic project. Use **Projects** to create and edit projects and work items. Rigarus saves the database to `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`.

For internal testing, use the installer from the [private Windows CI acceptance kit](docs/08-RELEASE-HANDBOOK.md#offline-acceptance-kit).

## Legacy WPF development build

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

## Tauri development and tests

The Tauri desktop preview uses React/TypeScript and a bundled Python FastAPI sidecar. It supports demo note save and reopen, and the Project Master backlog, search, detail, creation and editing on the existing SQLite schema.

Use Python 3.13 and uv 0.10.12 on Windows to verify the backend from the repository root.

```powershell
Set-Location src/Rigarus.Backend
uv sync --locked
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -v
```

The tests use temporary synthetic SQLite files, an in-process ASGI client, and child-process loopback HTTP. See the [Windows build and installer procedure](docs/08-RELEASE-HANDBOOK.md#tauri-desktop-preview) and [desktop verification walkthrough](docs/05-DEMO-ACCEPTANCE.md#tauri-demo-note-engineering-check).
