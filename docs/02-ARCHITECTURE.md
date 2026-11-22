# Architecture

## Tauri migration

The preview shell uses Tauri with a React/TypeScript UI and a bundled Python FastAPI sidecar. `Rigarus.Backend` separates the ASGI routes, note validation, and SQLite storage. Its app factory receives the database path from the caller so tests can use isolated files. Startup must complete schema initialization before serving requests.

The Python sidecar binds IPv4 loopback on a port assigned by Windows. Its parent starts it with the database path and supplies a fresh 32-byte token as 64 lowercase hex digits followed by a newline over stdin. After SQLite initialization and HTTP startup, the sidecar writes a JSON readiness line with `event` set to `ready` and the assigned `port` on stdout. Requests require the token in the Authorization header and the expected loopback Host. The sidecar exits when the parent closes the input pipe. If initialization fails, it exits with an actionable stderr message.

Rust owns the sidecar process, token, and port. React invokes Rust commands for the demo note and Project Master. Rust resolves the sidecar from bundled resources and opens the existing `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db` path. The desktop shows database startup errors with a retry action. At exit it closes the input pipe and waits for process exit, terminating the child if the grace period expires. Close one desktop before launching the other.

FastAPI routes validate Project Master inputs and pass drafts to the SQLite store. A project and its work-item changes commit in one transaction. Both desktops use the same existing schema and retain the IDs of previously saved rows.

## Manual Draft assignments (#14)

`assignments.py` holds the local-calendar/AM-PM draft model and revision rule independently of HTTP, UI and SQLite. `assignment_store.py` checks stable references and Crew-slot occupancy under a write reservation. `assignment_api.py` validates strict inputs and maps missing, invalid, conflicting and storage-failure outcomes to 404/422/409/503 without exposing database diagnostics.

React's Schedule form and per-WorkItem Assign action invoke `list_assignments`, `read_assignment`, `save_assignment` and `cancel_assignment` through the existing authenticated Rust/sidecar bridge. Range reads supply persistent data for the later #16 seven-day grid. Work dates remain local ISO strings; UTC edit timestamps never convert the work date.

Every response is Draft/Cancelled with `validation_status: Pending` and `publishable: false`. There is no publish command or endpoint. Actual personnel (#22), driver/time-off/qualification/Rig checks, published versions and a full weekly board (#16) are separate slices. A definite Crew-slot collision permits correction; version conflicts or uncertain responses require reload. Committed writes followed by failed reads report that outcome and clear the stale list. Form Cancel makes no write; explicit saved cancellation retains the record/ID and releases its slot.

## Desktop framework and weekly projection (#16)

The desktop opens Schedule / Job Schedule without an account. The dark module rail retains the existing Project, Crew/Employee/Foreman, Rig, import-preview and demo-note workflows under their new modules. Local search reads existing authenticated commands, indexes supported types with stable IDs and routes to the stored record or assignment week. No external search or calendar service is used. Device appearance preferences use validated, versioned WebView local storage; preview is reversible and only explicit Save persists it.

`workspace-data.ts` bounds concurrent Project-detail and Foreman reads. Job Schedule, Crew Board, the unscheduled queue and Overview derive from the same active Draft Assignment rows. The job grid shows projects with visits (retained across empty weeks); unscheduled work remains in its queue. Calendar arithmetic uses an integer UTC day counter without converting a local work date into an instant. One table owns vertical/horizontal scrolling, sticky dates and roster. Selection scrolls within that table. Assign/edit/cancel reuse #14 commands and revisions; uncertain writes require reload and failed refresh after commit clears stale board data.

Home Crew members/current Foreman are master data. Cross-Home-Crew appointments remain labelled; default Rig is reference data, not actual dated equipment. Dated membership/leave is not fabricated: show Actual staffing not assigned and Time off not configured. Publish review and formal reports explain missing checks/snapshots and have no publishing path. No SQLite migration, domain-rule relaxation or dependency change is introduced.

## WPF baseline

| Project | Responsibility | Dependencies |
| --- | --- | --- |
| Rigarus.Domain | Project master data, work item requirements, and demo note validation | .NET |
| Rigarus.Application | Demo note and Project Master use cases | Domain |
| Rigarus.Infrastructure | Local paths, EF Core migrations and mappings, SQLite storage, local diagnostics | Application, Domain, EF Core SQLite |
| Rigarus.Desktop | WPF window, bindings and startup composition | Application, Infrastructure, Domain |
| Rigarus.Reporting | Library reserved for later report adapters | .NET |

Desktop startup composes the local demo store and project repository. It applies migrations, reads the demo fixture, and loads the view model. The Projects view uses application use cases to search the backlog, load details, and save edits from a modal editor. Local errors display a recovery hint. Diagnostic entries contain timestamp, operation and exception type.

Project and WorkItem are plain C# domain types. A project owns its work items and validates their requirements. EF Core stores the two types in separate tables and commits project and work item changes with one save. Each repository operation disposes its context and connection. See the [data model](03-DATA-MODEL.md).

Domain, Application and Infrastructure have xUnit suites. Reporting tests begin with the first report behavior. The EF CLI uses the Infrastructure test project as its startup project so design tooling stays out of the desktop distribution.

Windows development requires the .NET 10 SDK and Windows Desktop reference pack. The framework-dependent app requires the .NET 10 Windows Desktop runtime. The local self-contained Windows x64 package includes its runtime.
