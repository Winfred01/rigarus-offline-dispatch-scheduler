# Architecture

## Tauri migration

The preview shell uses Tauri with a React/TypeScript UI and a bundled Python FastAPI sidecar. `Rigarus.Backend` separates the ASGI routes, note validation, and SQLite storage. Its app factory receives the database path from the caller so tests can use isolated files. Startup must complete schema initialization before serving requests.

The Python sidecar binds IPv4 loopback on a port assigned by Windows. Its parent starts it with the database path and supplies a fresh 32-byte token as 64 lowercase hex digits followed by a newline over stdin. After SQLite initialization and HTTP startup, the sidecar writes a JSON readiness line with `event` set to `ready` and the assigned `port` on stdout. Requests require the token in the Authorization header and the expected loopback Host. The sidecar exits when the parent closes the input pipe. If initialization fails, it exits with an actionable stderr message.

Rust owns the sidecar process, token, and port. React invokes Rust commands for the demo note and Project Master. Rust resolves the sidecar from bundled resources and opens the existing `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db` path. The desktop shows database startup errors with a retry action. At exit it closes the input pipe and waits for process exit, terminating the child if the grace period expires. Close one desktop before launching the other.

FastAPI routes validate Project Master inputs and pass drafts to the SQLite store. A project and its work-item changes commit in one transaction. Both desktops use the same existing schema and retain the IDs of previously saved rows.

## Manual Draft assignments (#14)

`assignments.py` holds the local-calendar/AM-PM draft model and revision rule independently of HTTP, UI and SQLite. `assignment_store.py` checks stable references and Crew-slot occupancy under a write reservation. `assignment_api.py` validates strict inputs and maps missing, invalid, conflicting and storage-failure outcomes to 404/422/409/503 without exposing database diagnostics.

React's Schedule form and per-WorkItem Assign action invoke `list_assignments`, `read_assignment`, `save_assignment` and `cancel_assignment` through the existing authenticated Rust/sidecar bridge. The same assignment reads supply the #16 weekly projection described below. Work dates remain local ISO strings; UTC edit timestamps never convert the work date.

Every response is Draft/Cancelled with `validation_status: Pending` and `publishable: false`. There is no publish command or endpoint. Actual personnel (#22), driver/time-off/qualification/Rig checks and published versions remain separate slices; the #16 weekly projection is described below. A definite Crew-slot collision permits correction; version conflicts or uncertain responses require reload. Committed writes followed by failed reads report that outcome and clear the stale list. Form Cancel makes no write; explicit saved cancellation retains the record/ID and releases its slot.

## Desktop framework and weekly projection (#16)

The desktop opens Schedule / Job Schedule without an account. The dark module rail retains the existing Project, Crew/Employee/Foreman, Rig, import-preview and demo-note workflows under their new modules. Local search reads existing authenticated commands, indexes supported types with stable IDs and routes to the stored record or assignment week. No external search or calendar service is used. Device appearance preferences use validated, versioned WebView local storage; preview is reversible and only explicit Save persists it.

`workspace-data.ts` bounds concurrent Project-detail and Foreman reads. Job Schedule, Crew Board, the unscheduled queue and Overview derive from the same active Draft Assignment rows. The job grid shows projects with visits (retained across empty weeks); unscheduled work remains in its queue. Calendar arithmetic uses an integer UTC day counter without converting a local work date into an instant. One table owns vertical/horizontal scrolling, sticky dates and roster. Selection scrolls within that table. Assign/edit/cancel reuse #14 commands and revisions; uncertain writes require reload and failed refresh after commit clears stale board data.

Home Crew members/current Foreman are master data. Cross-Home-Crew appointments remain labelled; default Rig is reference data, not actual dated equipment. Dated membership is explicit only: show Actual staffing not assigned until workers are saved for that visit. Leave is not fabricated: show Time off not configured. Publish review and formal reports explain missing checks/snapshots and have no publishing path. No SQLite migration, domain-rule relaxation or dependency change is introduced.

## Explicit Draft workers (#22)

The first persisted-membership slice separates pure staffing types/ID validation (`staffing.py`), SQLite snapshot helpers (`staffing_persistence.py`), transactional writes/history (`staffing_store.py`) and the existing assignment HTTP router. Assignment reads include explicit staffing under the same read transaction; `employee_id` range filtering follows only the latest configured selection. Saves share the visit revision and never update Home Crew. Date/slot/Crew/WorkItem edits require staffing reconfirmation; note edits retain it. Audit/context and selection commit together.

Rust adds authenticated `save_staffing` and `read_staffing_history` commands; the existing assignment query bridge allows the employee filter. React's detail dialog embeds an explicit Draft workers editor; both weekly projections consume the same saved workers, including individual multi-day source buttons. History preserves saved names/Home Crew snapshots while current labels reflect live master data. No inferred attendance, leave, qualification, actual Rig, publish or export capability is added. Uncertain writes require reload; post-commit refresh clears stale data and reports failure distinctly.

## Recorded availability (#77)

`availability.py` defines three recorded states and bounded inclusive local-date ranges, independently of HTTP/UI/SQLite. `availability_store.py` owns snapshot reads, per-employee revision-protected range saves and retained history; `availability_api.py` maps validation/missing/stale/storage outcomes without database diagnostics. Startup adds schema nine in the existing migration transaction. An empty current cell is Not recorded, never presumed available.

The People Availability page first provides independent management and a selected employee's Sun–Sat AM/PM calendar. Its clear action removes current cells but preserves change history. Save explicitly replaces selected slots only; Cancel does not write. Query identity and effect cancellation prevent an older employee/week from supplying new cells. A failed read is shown separately from unknown; uncertain saves require reload and a failed post-commit refresh does not show stale cells.

Rust bridges read/save/history plus one bulk employee-status read for a local date/slot. Draft worker selection consumes that same recorded status as advisory information, with loading/error/retry distinct from Not recorded. It never edits Home Crew, workers or visits and never grants leave/weekend/driver/dispatch approval. No new external service or dependency is used.

## Employee Week planning projection (#71 first slice)

Employee Week reads existing `list_assignments` with employee_id and inclusive local dates, plus independent recorded availability. Only latest explicit configured staffing associations supply cards; Home Crew never expands into attendance. A defensive pure projection excludes other workers, cancelled and out-of-week visits. Stable ID/detail/revision, actual dated Crew and borrowed marker stay separate from Home Crew/default Rig. No schema, HTTP/Rust contract or dependency changes.

The app retains the selected Schedule date and employee in memory across directory/search handoffs. Loading/read errors clear the old identity's cards; delayed responses are cancelled and keyed by employee/week. Availability errors are not Unknown. A parent-roster failure can be retried from the same employee-week control. Read-only details and the copied employee/week/revision preview display DRAFT – NOT CONFIRMED. PDF/XLSX remain disabled until validated immutable Published snapshots and safety checks exist; no file/write/publication path is added.

## Explicit working-calendar calculation (#26 foundation)

`work_calendars.py` is an independent, read-only domain foundation. Explicit local-date AM/PM Working, NotWorking or Unknown cells are evaluated without timezone conversion, holiday feed or inferred Mon–Fri. Absence remains Unknown; duplicate cells reject instead of silently overriding. The original WorkItem calculation snapshot is now an inherited in-memory projection of its parent Project. The Project adapter records the Project ID and Project-scoped reasons. There is no WorkItem calendar write or override.

Only two Working cells produce Matched. A known NotWorking yields Blocked, and otherwise an unknown yields Pending; explicit opposite states retain a conflict reason. Matched does not mean a feasible or safe dispatch: every assessment stays Validation pending / unpublishable, and weekend cells separately explain pending weekend approval. Employee availability, personnel collisions, driver/qualification, actual Rig checks and operator approval must be evaluated independently in later integration.

The owner subsequently approved Crew/Project storage/editing and advisory Draft integration. `working_calendar_store.py` resolves each WorkItem's Project through its persisted FK, reads independent Crew/shared Project snapshots, saves revision-protected explicit ranges and retains history in schema ten. Draft reads/list/save responses include that same current assessment within their transaction. Calendar edits never rewrite a visit's ID, date, notes, revision or workers. Calendar closure/unknown remains permitted in Draft; the existing definite Crew-slot collision rejection is unchanged.

`working_calendar_api.py` provides strict bounded read/save/history and assessment routes with sanitized 404/422/409/503 errors. Four Rust commands retain the existing authenticated loopback lifecycle and allow only Crew/Project calendar owner paths. Schedule / Working calendars uses the same local Sun–Sat/date/dialog conventions as recorded availability. Cancel does not write; stale/uncertain saves require reload, and committed-save/failed-refresh clears old cells. Draft forms, cards and details display advisory conflict/pending/matched states. No recommendation, weekend-consent approval, safety certification, Apply/publication or export is introduced.

## Explicit-option comparison (#28 foundation)

`recommendation_comparison.py` independently compares immutable, explicitly
supplied dated AM/PM options for one WorkItem/parent Project. It excludes any
known Blocked option before limiting results, explains each slot/check/source,
and deterministically orders earliest finish (default) or earliest start, with
stable Crew/option-ID ties. Missing independent evidence remains Pending.

The comparator itself has no allocator. There is no production snapshot
adapter, safety validator, HTTP/Tauri/UI connection or SQLite write. Supplied Satisfied evidence
is not certified current safety: every option/comparison is Validation pending,
unapplyable and unpublishable, even if all supplied checks are satisfied. Home
Crew, default Rig and employee Available never supply other missing checks.
The raw internal gap count introduces no continuity weight or remaining-work
deduction. Future #15/#23/#24/#25/#27 validators, approved generation semantics,
and #18/#29 revision/lock/Apply gates remain necessary. No schema change.

## Single-Crew date generation (#28 phase two)

`recommendation_generator.py` generates actual proposed dates from immutable
`GenerationRequest` snapshots: option/WorkItem/parent Project/Crew IDs, required
Crew count, explicit Remaining Half-days and strict operator-confirmation bool,
earliest local date, inclusive horizon, Crew/Project `WorkCalendar`s, optional
`CrewOccupancySnapshot` and per-slot independent evidence. The caller resolves
the persisted parent and correct/current context. No production adapter verifies
source revisions, actual workers/Rig or resource approval in this slice.
No WorkItem override, estimate fallback or Draft-work deduction exists.

Index cells once, scan local ordinal dates AM before PM, reuse
`assess_project_calendar` with constant-size indexed cells. Only both Working
can count. Closure/unknown/conflict, known occupancy and supplied Blocked
resource checks skip the slot. Weekends additionally need exact-slot Satisfied
consent; missing/Pending consent cannot shorten dates. Other missing safety
evidence remains Pending and never certifies dispatch. Gaps do not reset work.

One earliest cumulative plan is generated per Crew/earliest-date scenario,
rather than exhaustive start-date or multi-Crew optimization. Scans stop on the
confirmed count or horizon. Multi-Crew and absent/unconfirmed remaining work
return Needs Review without scanning. Exhaustion retains partial slots/unfilled
count but no finish or complete comparator option. Every scanned/skipped slot
retains date/half, source states, assessment and reasons. Calendar counters cover
only scanned slots and may overlap (one closure with the other source unknown).

Complete plans become PR91 `ExplicitOption`s. `generate_and_compare` validates
same WorkItem/parent/remaining requirement, rejects conflicting shared Project
snapshots on overlapping dates, and calls `compare_explicit_options` for canonical
explanations, earliest-finish default/earliest-start alternate, Crew/option-ID ties
and the 1–10 limit. Incomplete diagnostics remain outside ranking. Candidates
are alternatives, not simultaneous reservations. Occupancy None is missing;
empty means explicitly free within its snapshot range. Partial coverage stays
Pending outside that range, never inferred free.

The inclusive horizon ends before the next annual anniversary (Feb29 clamps to
Feb28), also bounded to 366 dates / 732 slots. Dates near year 9999 never overflow.
At most 100 requests; scan/index work is linear, comparator canonicalization
O(H log H). No UTC instant, clock, file, SQL, network, dependency, migration,
API, Tauri/UI, save/Apply or publication path is introduced. All outputs remain
Validation pending or Needs Review, `validation_status=Pending`,
`applyable=false`, `publishable=false`, even with every supplied check Satisfied.

See the [design record](design/2026-11-24-issue-28-generator-checklist.md) and
[engineering evidence](acceptance/2026-11-24-issue-28-generator.md). Trusted
resource validators, revision adapters, operator preview/locks/Apply and customer
Demo E remain separate requirements.

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
