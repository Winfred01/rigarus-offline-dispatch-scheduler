# Architecture

## Tauri migration

The preview shell uses Tauri with a React/TypeScript UI and a bundled Python FastAPI sidecar. `Rigarus.Backend` separates the ASGI routes, note validation, and SQLite storage. Its app factory receives the database path from the caller so tests can use isolated files. Startup must complete schema initialization before serving requests.

The Python sidecar binds IPv4 loopback on a port assigned by Windows. Its parent starts it with the database path and supplies a fresh 32-byte token as 64 lowercase hex digits followed by a newline over stdin. After SQLite initialization and HTTP startup, the sidecar writes a JSON readiness line with `event` set to `ready` and the assigned `port` on stdout. Requests require the token in the Authorization header and the expected loopback Host. The sidecar exits when the parent closes the input pipe. If initialization fails, it exits with an actionable stderr message.

Rust owns the sidecar process, token, and port. React invokes the Rust commands to read the demo project and save a note. Rust resolves the sidecar from bundled resources and opens the existing `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db` path. The desktop shows database startup errors with a retry action. At exit it closes the input pipe and waits for process exit, terminating the child if the grace period expires. The Project Master UI remains available in WPF during the migration. Close one desktop before launching the other.

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
