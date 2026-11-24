# Rigarus Offline Dispatch Scheduler

**English** · [简体中文](docs/README.zh-CN.md)

Rigarus is a **Windows-first, fully offline dispatch-planning desktop application** for a single local operator. It opens without a user account or sign-in. The application uses **Tauri/Rust + React/TypeScript**, a bundled **Python FastAPI** sidecar, and **local SQLite**. No Google Calendar account, cloud sync, or hosted scheduling service is required.

> **Engineering preview — 24 November 2026.** Code merged into `main` is not the same as a customer-approved release. Demo A–F sign-off, full dispatch-safety validation, production distribution, and UAT remain pending. Use fictional data for demonstrations and CI; do not treat a Draft as a confirmed crew dispatch.

## What's implemented

| Area | Available engineering-preview behavior |
| --- | --- |
| **Schedule → Job Schedule / Crew Board** | Shared Sunday–Saturday boards built from saved Draft visits; local date and provisional AM/PM slots; assign, edit, explicitly cancel and reopen visits. Existing Crew/slot collisions are rejected. Consecutive visits can appear as multi-day spans. Search and week navigation are local. |
| **Project Management** | Create, edit, search and sort Projects and their Small/Civil/Tower/Other WorkItems. Bulk Add accepts pasted CSV, Excel-style TAB-separated text, or local `.xlsx`, with read-only preview, duplicate/error diagnostics and explicit transactional confirmation. |
| **People → Employees / Crews** | Employee and Civil/Tower Crew rosters; Home Crew, skill level, current Foreman assignment and retained appointment history. Explicitly select workers for a dated Draft visit; a temporary assignment to another Crew does **not** change Home Crew. |
| **People → Availability** | Record an employee as Available, Unavailable or Not recorded, for a full day, AM or PM, over inclusive dates; review the calendar and change history. These statuses are advisory, not dispatch clearance. |
| **Schedule → Employee Week** | Read-only weekly view of **explicitly assigned** visits for one employee, including borrowed-Crew labels and recorded availability. Its planning preview is **DRAFT – NOT CONFIRMED**. Home Crew membership alone does not imply attendance. |
| **Schedule → Working calendars** | Explicit working / nonworking / unknown AM/PM dates for each Crew and Project; WorkItems inherit their parent Project calendar. Calendar conflicts and missing information are shown as Draft feedback. No default Monday–Friday or weekend permission is inferred. |
| **Items / Data / device tools** | Rig inventory and optional default Crew (not actual dated vehicle allocation); read-only Excel import preview; separate demo-note fixture; local workspace search (`Ctrl+K`), appearance settings and Help. |

### Automatic scheduling: internal calculation only

Merged [#28 phase-one comparison](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/pull/91) and [phase-two date generator](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/pull/92) are **pure Python engineering modules**, **not a desktop “Auto Schedule” workflow**. They can:

- Calculate dates for **one Crew per WorkItem** from **operator-confirmed remaining half-days** and explicitly supplied Crew/parent-Project calendar and occupancy snapshots.
- Accumulate AM/PM work across gaps, retain skipped-slot explanations, and return **Needs Review** instead of a made-up finish date when duration or capacity is insufficient.
- Compare supplied/generated alternatives by **earliest finish** (default) or **earliest start**, excluding supplied known hard blocks and keeping missing safety evidence pending.

The generator is **not yet connected to trusted persisted scheduling snapshots, an API, or the UI**. It does not certify worker/driver qualifications, staffing minimums, actual Rig availability or weekend consent. Every result remains **Validation pending; Apply = false; Publish = false**. See the [engineering acceptance record](docs/acceptance/2026-11-24-issue-28-generator.md).

## Not yet available for operational dispatch

- Full employee/Rig overlap checks, approved-driver and skills/qualification gates, actual Rig swaps/maintenance and worker-specific weekend approvals ([#15](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/15), [#23–#27](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues)).
- Trusted recommendation input adapters, safe multi-option review/Apply, delay and early-finish propagation, locks, and immutable **Published** schedule revisions ([#18–#29](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues)).
- Company, Crew or employee **PDF/XLSX dispatch exports**. `Reports → Weekly Export` shows the unmet checks; export actions remain disabled. The Employee Week preview is not a sendable confirmed schedule.
- Complete historical workbook reconciliation, cross-machine application-level backup/restore, different-version upgrade and enterprise-policy distribution acceptance. A successful Windows CI build or isolated offline VM test is **not** customer UAT or production authorization.

## Install or try an engineering build (Windows 11 x64)

1. Obtain a **verified engineering test installer** from an authorized maintainer. A matching-commit [Windows Actions acceptance kit](docs/08-RELEASE-HANDBOOK.md#offline-acceptance-kit) may be available to authorized repository contributors; artifacts can expire and are **not** official customer releases. Do not choose an arbitrary CI artifact as a production installer.
2. Check its `build.json` and expected SHA-256 against the approved test record before running it. The current `0.1.0` NSIS engineering build is typically named `Rigarus Dispatch_0.1.0_x64-setup.exe`; verify the actual filename and hash rather than assuming they are fixed.
3. Follow the approved installation instructions. The package bundles the local Python sidecar/runtime and supports installation of the bundled WebView2 runtime when needed. Start **Rigarus Dispatch** from the Windows Start menu—**no software account is required**.

Installed operator machines do not need a separate Python, Node.js, Rust, or .NET development environment. Clean-image, no-network installation and same-version build replacement have passed **specific** Windows 11 VM checks, but signed distribution, managed-device policies, different semantic-version upgrades, and customer acceptance remain separate gates. See [release/acceptance instructions](docs/08-RELEASE-HANDBOOK.md).

### Short synthetic walkthrough

1. In **Project Management**, create a fictional Project and Civil/Tower WorkItem (or use **Bulk Add Projects**).
2. In **People**, create a Crew and employee; optionally appoint a Foreman and record the employee's availability.
3. In **Schedule → Working calendars**, explicitly set Crew and Project AM/PM work dates.
4. In **Schedule → Job Schedule**, select **Assign Work Item**, choose a Crew/date/slot and save a **Draft**. Inspect the matching **Crew Board**. Edit or explicitly cancel it; reopen to verify persistence.
5. Optionally select actual Draft workers and open **Employee Week**. It will show only explicitly assigned visits, labeled **DRAFT – NOT CONFIRMED**. **Do not distribute it as a validated schedule.**

See the [desktop walkthrough](docs/05-DEMO-ACCEPTANCE.md) and the [bulk-input mapping](docs/11-IMPORT-MAPPING.md).

## Offline data and privacy

The default application database is:

`%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`

All normal app data and processing remain on the operator's Windows computer; development dependency restore and GitHub CI may use the network. Keep real customer employee names, project addresses, original Excel/PDF files, SQLite databases, backups, credentials and raw diagnostics in authorized local storage—not in GitHub Issues, commits, screenshots or Actions artifacts.

**This repository is currently public.** Do not interpret its visibility as permission to publish customer data. Read the [data model](docs/03-DATA-MODEL.md) and [security/development rules](AGENTS.md) before testing existing databases.

## Develop and test (Windows)

Follow the [current Tauri build instructions](docs/08-RELEASE-HANDBOOK.md#tauri-desktop-preview) for pinned Node.js, Rust/MSVC, Python 3.13, uv and Windows build tools. The first locked dependency restore requires network access. Run the applicable checks with **synthetic** data:

```powershell
# From repository root
./scripts/Build-RigarusSidecar.ps1

Push-Location src/Rigarus.Backend
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -v
Pop-Location

Push-Location src/Rigarus.Tauri
npm ci
npm run format
npm test
npm run build
npm run tauri -- build -- --locked
Pop-Location
```

The historical **.NET/WPF** solution is retained for regression and SQLite compatibility only; it is **not** the architecture for new features. From the repository root:

```powershell
dotnet restore Rigarus.sln --locked-mode
dotnet build Rigarus.sln -c Release --no-restore
dotnet test Rigarus.sln -c Release --no-build --no-restore
```

Documentation: [project plan](docs/00-PROJECT-PLAN.md) · [delivery gates](docs/09-DELIVERY-PLAYBOOK.md) · [architecture](docs/02-ARCHITECTURE.md) · [decision register](docs/10-CLIENT-DECISIONS.md) · [Design-First requirements](AGENTS.md).

**Development flow:** one scoped Issue → Design-First review → isolated branch → automated/Windows checks → **Draft PR for human review**. Never auto-merge, publish a release, close an Issue or treat engineering evidence as customer sign-off.
