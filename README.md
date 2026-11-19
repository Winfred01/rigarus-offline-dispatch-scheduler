# Rigarus Offline Dispatch Scheduler

English · [简体中文](docs/README.zh-CN.md)

Rigarus is a Windows desktop dispatch tool for one local operator. The current engineering preview targets Windows 11 x64 and has an English interface. It uses Tauri, React and TypeScript, a bundled Python FastAPI sidecar, and local SQLite. Installation and daily use can run offline without an account or external service.

## Install on Windows 11 x64

1. Obtain `Rigarus-Dispatch-x64-setup.exe` through the approved distribution channel. Repository members can get an internal test installer from the [private Windows CI acceptance kit](docs/08-RELEASE-HANDBOOK.md#offline-acceptance-kit).
2. Copy the installer to the target PC, double-click it, and follow the prompts. Setup includes the Python runtime, SQLite, and Microsoft's offline WebView2 installer. It uses the bundled WebView2 installer if Windows has no registered runtime.
3. Select **Run Rigarus Dispatch** at the end of setup or open **Rigarus Dispatch** from the Start menu.

Operators can use the installed app without separately installing Python, Node.js, Rust, .NET, or Visual Studio. Use synthetic data for this engineering preview. Demo A customer sign-off and production approval are pending.

## Current preview

- **Dashboard** opens the synthetic job `DEMO-001`. Edit its demo note, select **Save note**, and reopen the app to verify the saved note.
- **Projects** lets you search by Job #, Site ID, or site name and create or edit projects and work items. Each work item can record a required crew count and an estimate in whole half-days.
- **Crews** lets you create, search, edit, deactivate, and reactivate Civil and Tower crews. Inactive crews remain visible.

- **Employees** lets you maintain names, home crews, skill levels, foreman eligibility and active status. Driver status starts as Unverified.
- **Rigs** lets you maintain unique Rig #s, type, notes, an optional default crew and active status. Inactive rigs keep their identity and number.

The [project plan](docs/00-PROJECT-PLAN.md) covers upcoming foreman assignments, scheduling, import and export, backup and restore, and upgrade verification.

## Local data

The default database path is `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`. Development, demos, and CI use synthetic data. Keep customer databases, original spreadsheets, attachments, backups, and raw diagnostics on authorized local systems. See the [data model and migration notes](docs/03-DATA-MODEL.md) before using an existing database.

## Tauri development and tests

Follow the [Windows source build and packaging instructions](docs/08-RELEASE-HANDBOOK.md#tauri-desktop-preview) to set up Node.js, Rust, the Windows C++ build tools, Python 3.13, and uv 0.10.12. The first dependency restore requires network access.

Run the backend checks from the repository root in PowerShell.

```powershell
Set-Location src/Rigarus.Backend
uv sync --locked
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -v
```

The tests use temporary synthetic databases and loopback HTTP. The [desktop verification walkthrough](docs/05-DEMO-ACCEPTANCE.md#tauri-demo-note-engineering-check) describes the native Windows smoke tests. Read [AGENTS.md](AGENTS.md) and the [architecture](docs/02-ARCHITECTURE.md) before working on an Issue.

## Legacy WPF development build

The .NET/WPF baseline remains available for checking earlier behavior and data compatibility. Install the .NET 10 SDK and run these commands from the repository root in PowerShell.

```powershell
dotnet restore Rigarus.sln --locked-mode
dotnet build Rigarus.sln -c Release --no-restore
dotnet test Rigarus.sln -c Release --no-build --no-restore
dotnet run --project src/Rigarus.Desktop -c Release --no-build --no-restore
```

The first restore requires NuGet access. See the [legacy Windows ZIP procedure](docs/08-RELEASE-HANDBOOK.md#local-m0-engineering-package).
