# Architecture

| Project | M0 responsibility | Dependencies |
| --- | --- | --- |
| Rigarus.Domain | Demo project and note invariant | .NET |
| Rigarus.Application | Open the fixture and save a validated note | Domain |
| Rigarus.Infrastructure | Local paths, EF Core migration, SQLite store, minimal local diagnostics | Application, Domain, EF Core SQLite |
| Rigarus.Desktop | WPF window, bindings and startup composition | Application, Infrastructure, Domain |
| Rigarus.Reporting | Library reserved for later report adapters | .NET |

Desktop startup composes a storage path, SQLite store and application workspace. It applies migrations, reads the fixture, and loads the view model. The window passes save requests to the view model. Infrastructure updates only the note in a SQLite transaction. Each operation disposes its context and connection. Local errors display a recovery hint. Diagnostic entries contain timestamp, operation and exception type.

Domain, Application and Infrastructure have xUnit suites. Reporting tests begin with the first report behavior. The EF CLI uses the Infrastructure test project as its startup project so design tooling stays out of the desktop distribution.

Windows development requires the .NET 10 SDK and Windows Desktop reference pack. The framework-dependent app requires the .NET 10 Windows Desktop runtime. The local self-contained Windows x64 package includes its runtime.
