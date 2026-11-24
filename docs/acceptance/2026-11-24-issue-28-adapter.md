# Issue #28 phase three — persisted read-only snapshot evidence

Initial main `244b5ee1089f233b2d727318bd7f4d86cd1f87c8` includes human-merged
PR92/PR91. Delivery base is latest main `58af6c4db6035116c4f2e6df97b819eaf5ebf320`
(PR93 changes English/Chinese README only; required design/product/CI sources unchanged). Isolated branch `codex/issue-28-sqlite-adapter`. The first Design-First commit
preceded product edits; see [source inventory and implementation
plan](../design/2026-11-24-issue-28-adapter-checklist.md). Issue28 remains Open.
PUBLIC repository verified; synthetic source/sanitized engineering records only.

## What is implemented

`build_recommendation_snapshot(Path, RecommendationQuery)` opens the existing
database using `storage.connect(read_only=True)` (mode=ro/query_only/foreign keys,
5-second busy timeout), starts BEGIN and pins one view by reading schema first.
Migration history/current tables, quick_check and FK checks must pass. No
initialization, migration, journal-mode change, checkpoint, immutable/nolock or
business/schema write is performed. All selected sources share this connection;
the detached frozen result contains no live connection or mutable Store response.

| Real source | Retained mapping and revision / use |
| --- | --- |
| WorkItems → Projects | Real ProjectId FK; optional expected parent is checked, never substituted; IDs, JobNumber, type, RequiredCrewCount, estimate (reference only) |
| Crews / ForemanChanges | Stable Crew ID/type/active/name, latest Foreman change ID/employee/timestamp; not attendance or staffing approval |
| WorkingCalendars / Cells / Changes | Separate Crew and inherited Project calendar cells, native revision/calendar ID/latest change ID; missing cells remain Unknown |
| DraftAssignments → WorkItems | All selected-Crew/horizon visits retain ID, real WorkItem/Project, local date/half, status, revision and update timestamp; only Draft occupies; no same-work exclusion |
| AssignmentStaffingChanges / Members | Reuse current-staffing helper on the same connection, retain configured flag/change ID and explicit employee IDs; never expand Home Crew |
| Employees / EmployeeAvailability / Changes | Related Home Crew members, actual observed workers and current Foremen; ID/HomeCrew/skill/eligible/active/Unverified driver and sparse date/half availability/native revision are observations |

Public `ProjectStore`, `AssignmentStore`, `StaffingStore` and other Store reads
were inspected but are not composed: each opens another connection. Reuse is
through connection-level `working_calendar_store.snapshot/owner`,
`availability_store.snapshot` and `staffing_persistence.read_staffing`. Existing
generator/comparator remain the date/sort authority; no duplicate engine model.

`generation_requests(snapshot)` creates existing GenerationRequest values using
real parent, current required count and operator-confirmed remaining input.
Crew IDs are stable option IDs. Full-horizon CrewOccupancySnapshot includes every
active Draft on that Crew, including target WorkItem repeat visits; Cancelled
rows release capacity. There is no replacement or completed-work deduction.
Inactive/mismatched Crew, or unresolved Small/Other type mapping, returns Crew
Needs Review outside ranking; missing Crew/WorkItem is an explicit lookup error.

`generate_from_persisted_snapshot` returns the source snapshot plus existing
GenerationComparison/candidates/explanations and Crew reviews. It calls
generate_and_compare → generate_candidate → ExplicitOption/comparator; default
EarliestFinish, alternate EarliestStart, stable ties and result limits preserved.
Every result stays Pending / applyable=false / publishable=false. No actual
proposed workers/Rig/consent is inferred. Available, Home Crew, Foreman and
Unverified Driver do not satisfy independent safety checks.

## Snapshot identity and staleness

SHA256 canonical logical fields include the format version, source-location scope,
query (IDs, confirmed Remaining/flag, dates, sort, limit), WorkItem/Project fields,
Crew/calendar/Foreman observations, visits/current staffing, related employee
metadata and recorded availability. The source ID is an opaque hash of resolved
local location, not a new database UUID. No clock, page/WAL/SHM bytes, DB file hash
or fabricated global revision is used. Unversioned master records are compared by
content; native calendar/availability revisions and assignment/staffing/Foreman
identities remain available separately.

Scope is deliberately conservative: an observed owner's calendar/availability
revision can invalidate it even for an edit outside the range. Unrelated Projects,
unobserved employees/default Rig and physical checkpoint/VACUUM do not affect it.
This is input-change identification, not proof of trusted origin or Apply approval.
`check_snapshot_freshness` re-reads the same scope: changed/missing/moved records
are Stale, equal inputs Current, read/schema failures propagate. Current can
become stale immediately after release. Future Apply must check under its own
write transaction and independently validate resource evidence/locks/revisions.

Reads have a 30-second SQL progress/end deadline, 5-second busy bound, inherited
100-Crew/annual limits and 100,000 observed Assignment/staffing/employee/availability
row limit. Limits/failures produce no partial snapshot/fingerprint. Native source
records are not silently skipped on errors. Success/failure closes the transaction
and connection. This budget does not promise interruption of every synchronous
OS call; a future exposed worker needs an independent process deadline.

## Reproduce / actual stored-data demonstration

From `src/Rigarus.Backend`, Python3.13 and uv0.10.12:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -p test_recommendation_adapter.py -v
uv run --locked python -m unittest discover -s tests -q
```

The fixture uses initialize_database and real Project/Crew/working-calendar Stores
to create a temporary synthetic schema-ten DB. Estimated Half-days=99 deliberately
differs from explicitly confirmed Remaining=4. The persisted-date test and a
separate executed fixture demonstration produced:

| Crew | Actual generated start / finish | Accumulation |
| --- | --- | --- |
| C1 ID1 | 2026-11-23 AM → 2026-11-27 PM | Mon AM, Wed PM, Thu AM, Fri PM; 4/4 |
| C2 ID2 | 2026-11-24 AM → 2026-11-25 PM | Tue AM/PM, Wed AM/PM; 4/4 |

EarliestFinish=[2,1], EarliestStart=[1,2]. IDs are real generated fixture IDs;
the adapter, not caller-created candidate dates, supplies generator inputs.
No formal schedule or resource reservation is created.

## Actual checks

| Gate / command scope | Actual result |
| --- | --- |
| Python locked restore | PASS, uv0.10.12 / Python3.13.7, lock unchanged |
| Ruff check / format | PASS, 58 Python files |
| Focused adapter integration | PASS, 24 tests in 8.059s |
| Complete backend | PASS, 181 tests in 47.787s, includes existing generator/comparator suites |
| Windows sidecar build / packaged regression | PASS, locked PyInstaller build and 11 auth/loopback/persistence/restart/upgrade tests in 18.906s; adapter is not connected to packaged UI |
| Frontend | PASS, npm ci/Prettier/35 tests/TypeScript-Vite build; initial restricted mkdir EPERM resolved by authorized local rerun, no code/lock workaround |
| Rust | PASS, 1.95.0 locked fetch/fmt, Windows Release compilation and 8 tests |
| Historical .NET | PASS, 10.0.100 locked restore/format/Release build (0 warnings/errors), 35 tests: 16 Domain/2 Application/17 Infrastructure |
| Acceptance-tool harness | PASS, Windows PowerShell5.1 synthetic deadline/error/UIA/consistent-SQLite controls; not a native app run |
| Staged privacy / whitespace / docs | PASS, 255 indexed paths, intended source/sanitized docs only, links/fences/whitespace checked |
| Feature-head Windows CI | Pending before push/PR; final PR/Issue report records exact head/run/jobs/artifact result |
| Native GUI / disconnected install / upgrade / reboot | NOT RUN; no new HTTP/Tauri/UI workflow, prior package results not borrowed |
| Customer Demo E / UAT | NOT RUN; owner development scope is not customer acceptance |
| Production | NOT APPROVED |

Executed on connected Windows11 developer host build26200 with developer tools.
No real customer DB was opened. Detailed logs/temp DBs/full originals stay local.

## Required scenario evidence

| Scenario | Actual result |
| --- | --- |
| Real WorkItem/Project/Crew mapping; wrong parent/missing records | PASS; stored FK only; explicit lookup/context errors |
| Inactive/mismatched/unmapped Crew | PASS; Needs Review, excluded from complete ranking |
| Single/multi-Crew and absent/unconfirmed remaining work | PASS; existing G1/G2 semantics, no estimate/visit fallback |
| Working/NotWorking/Unknown/conflict and gaps/exhaustion | PASS; skips/reasons/counters retained; incomplete work has no finish |
| Existing Crew occupancy, cancellations, other Crew/AM-PM, repeat visits | PASS; all active visits occupy, Cancelled frees capacity, stable IDs retained, no replacement exclusion |
| Actual borrowed worker vs Home Crew/Availability/Foreman | PASS; explicit staffing/current change ID, foreign Home Crew and Unavailable observation retained; no assumed attendance/driver/Rig/qualification |
| Weekend consent absent despite Working/Available | PASS; no shortened dates, only weekday capacity counted |
| Both sorts / canonical replay / source fingerprint | PASS; stored C1/C2 different orders, reversed Crew input identical snapshot |
| Source changes and freshness | PASS; master content, calendar revision, occupancy, staffing, availability, Foreman/employee fields and query changes detected; missing/moved source/different DB scope Stale |
| Concurrent WAL write | PASS; writer atomically changes WorkItem/Crew/calendar/Draft while reader paused; reader equals complete old fingerprint, next read sees complete changes; checkpoint succeeds after release |
| Read-only/logical equality | PASS; one connection/BEGIN, SQL trace contains only reads/PRAGMAs/transaction control; complete synthetic iterdump unchanged and full FK/quick_check valid |
| Database-enforced read-only | PASS; UPDATE denied; separate synthetic proof disables query_only and mode=ro still returns SQLITE_READONLY |
| Cross-year/leap/spring/autumn DST/annual boundary | PASS; persisted dates equal across three TZ settings, 732-slot bound/no false finish |
| Missing/corrupt/locked/read faults/old/new schema | PASS; distinct typed errors, no initialization/partial result; unknown source message sanitized; read/context handles closed |
| Deadlines/read limits/input errors | PASS; explicit deadline/limit failures and strict query validation |
| Physical changes/unrelated scope | PASS; checkpoint/VACUUM and unrelated Project insertion do not change scoped fingerprint |

## Remaining / next integration

#15 personnel/actual Rig collisions, #23 actual approved driver and borrowing
impact, #25 type/minimum staffing/skills/verified qualifications/Foreman, #24 dated
actual Rig/repair/swaps, #27 actual-worker weekend consent/history/invalidation
remain incomplete. Read employee observations are not proposed membership or
those validators. Small/Other mapping is recorded Open, not inferred.

#18/#29 can consume this detached snapshot/fingerprint for preview, but require
current independent validators, lock-aware changes, source revalidation inside
transaction Apply, rollback/audit and immutable Published history. This service
adds no HTTP/Tauri/UI, save, assignment replacement, staff/Rig selection, Apply,
Publish, automatic messaging, dependency or migration. No real-data migration.

One Draft PR for human review; no auto-merge, Issue closure or Release. Original
planning/UI/Excel/PDF/DB/log files stay local; PUBLIC upload is synthetic/sanitized.

Delivery review extracted shared comparison settings validation, eliminating
placeholder context during query validation. Full backend rerun: 181/181 PASS
in 47.787s; no date/resource rule or contract change.
