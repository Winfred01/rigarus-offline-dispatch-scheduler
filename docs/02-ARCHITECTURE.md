# Architecture

## Tauri migration

The planned shell uses Tauri with a React/TypeScript UI and a bundled Python FastAPI sidecar. `Rigarus.Backend` separates the ASGI routes, note validation, and SQLite storage. Its app factory receives the database path from the caller so tests can use isolated files. Startup must complete schema initialization before serving requests.

The sidecar still needs launch and shutdown supervision, a local-only transport, startup error reporting, and packaging with the Python runtime. The new UI needs to port the current demo and Project Master workflows before replacing the legacy desktop. The existing Project Master remains available in WPF.

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
