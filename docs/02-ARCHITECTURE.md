# Architecture

| Project | Responsibility | Dependencies |
| --- | --- | --- |
| Rigarus.Domain | Project master data, work item requirements, and demo note validation | .NET |
| Rigarus.Application | Open the fixture and save a validated note | Domain |
| Rigarus.Infrastructure | Local paths, EF Core migrations and mappings, SQLite storage, local diagnostics | Application, Domain, EF Core SQLite |
| Rigarus.Desktop | WPF window, bindings and startup composition | Application, Infrastructure, Domain |
| Rigarus.Reporting | Library reserved for later report adapters | .NET |

Desktop startup composes a storage path, SQLite store and application workspace. It applies migrations, reads the fixture, and loads the view model. The window passes save requests to the view model. Infrastructure updates only the note in a SQLite transaction. Each operation disposes its context and connection. Local errors display a recovery hint. Diagnostic entries contain timestamp, operation and exception type.

Project and WorkItem are plain C# domain types. A project owns its work items and validates them when they are added. EF Core stores the two types in separate tables. The desktop continues to open the demo workspace while the project management screens are planned for a separate slice. See the [data model](03-DATA-MODEL.md).

Domain, Application and Infrastructure have xUnit suites. Reporting tests begin with the first report behavior. The EF CLI uses the Infrastructure test project as its startup project so design tooling stays out of the desktop distribution.

Windows development requires the .NET 10 SDK and Windows Desktop reference pack. The framework-dependent app requires the .NET 10 Windows Desktop runtime. The local self-contained Windows x64 package includes its runtime.
