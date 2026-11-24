# SQLite data model

## M0 demo fixture

The initial EF Core migration creates `DemoProjects` with a numeric primary key, a unique job number, a site name and a required note. The SQLite constraint limits the note to 200 characters, and the domain limits .NET strings to 200 UTF-16 code units. The migration inserts exactly one fixture, `DEMO-001`, in the same migration transaction. EF records application in `__EFMigrationsHistory`. Reopening preserves operator edits.

The current user's database lives at `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`. Infrastructure opens SQLite with foreign-key enforcement and a five-second command timeout. Initialization enables WAL. Diagnostics are local to the `logs` directory and rotate between two files.

## Project master data

| Table | Fields and constraints |
| --- | --- |
| `Projects` | Generated integer ID, unique Job #, required Site ID and Site Name |
| `WorkItems` | Generated integer ID, required and indexed Project ID, type, positive integer crew count and estimated half-days |

Job # and Site ID are text and preserve leading zeroes. Project creation trims surrounding whitespace and preserves the entered spelling. The SQLite unique index uses `NOCASE`, so ASCII case variants such as `JOB-001` and `job-001` represent the same job. The Site ID can be shared by several projects. Demo A still needs to confirm the required site fields and accepted Job # format, including any non-ASCII case rules.

A project can enter the backlog before any work items are defined. Each work item carries a type (`Small`, `Civil`, `Tower`, or `Other`) and its own crew requirement and estimate. One half-day is the smallest estimate. A project can have multiple work items of the same or different types. This supports an unsplit job and a combined Civil/Tower job. The generated WorkItem ID gives later scheduling migrations a stable foreign key so several visits or crew assignments can reference the same work item. Assignment dates, crew selection and conflict rules belong to the scheduling milestone.

The `AddProjectsAndWorkItems` migration creates empty tables and indexes and adds a foreign key that prevents deleting a project while it has work items. The M0 migration and `DemoProjects` stay in place. `DEMO-001` remains in the demo table with its saved note, and startup still opens that fixture. The unique Job # index applies to `Projects`. Migration tests use temporary SQLite files, including a file upgraded from the original M0 migration.

Project Master uses the existing schema. Search matches literal substrings in Job #, Site ID and Site Name and follows SQLite's ASCII case handling. The backlog contains all master projects until assignments are introduced. An edit updates the selected project and its work items in one transaction. Existing work items retain their IDs and an omitted item is preserved. A duplicate Job # aborts the save and leaves both projects intact.

## Manual Draft assignments (#14)

Migration `20261122040000_AddDraftAssignments` is additive after Foreman history. `DraftAssignments` stores a stable ID; WorkItem/Crew FKs with RESTRICT deletion; canonical local `YYYY-MM-DD`; provisional `AM`/`PM`; separate assignment notes (up to 2,000 characters, no NUL); `Draft`/`Cancelled` status; positive revision; UTC created/updated timestamps. Existing Projects, WorkItems, demo notes, resources and Foreman history are untouched.

A partial unique index on `(CrewId, LocalDate, Slot) WHERE Status='Draft'` prevents concurrent duplicate occupancy. Date/slot/Crew/ID and WorkItem indexes support week-range reads and repeated visits. This does not assert that estimated duration or a multi-Crew requirement is fulfilled. Inactive Crew references remain readable and marked; master-data status does not invent a new dispatch gate.

| Method / path | Contract |
| --- | --- |
| GET `/draft-assignments` | Optional inclusive `start_date`, `end_date`, `crew_id`; `include_cancelled=false` by default. Deterministic date/slot/Crew/ID order, stable IDs and current Project/WorkItem/Crew labels. |
| GET `/draft-assignments/{id}` | One persisted record, including Cancelled. |
| POST `/draft-assignments` | Strict WorkItem/Crew IDs, local date, AM/PM, optional notes; status/revision/publication flags cannot be supplied. Creates revision 1. |
| PUT `/draft-assignments/{id}` | Same fields plus required `expected_revision`; only a Draft can change. |
| POST `/draft-assignments/{id}/cancel` | Required `expected_revision`; retains IDs/fields/notes, marks Cancelled and increments revision. Already-Cancelled at the current revision is a no-op. |

Writes use `BEGIN IMMEDIATE`. Duplicate occupancy and stale revisions return 409 without overwriting records. Failed inserts/updates/cancellation/migrations roll back. Cancelled rows remain referentially protected but release the slot. Form Cancel before submit makes no write request. Labels are current joins; published snapshots and a full edit-history trail belong to later milestones.

The database allows only Draft/Cancelled. Responses always report `validation_status='Pending'` and `publishable=false`; no publication endpoint exists. AM/PM is owner-approved for this slice, still proposed for final customer use. No hourly boundary or timezone conversion is inferred. Actual-worker, time-off, driver, qualification and Rig compliance remains pending.

Fresh and recognized legacy schemas upgrade inside the existing migration transaction. Tests force a post-DDL failure and verify complete rollback/retry plus existing IDs/notes/values. A real previous-main backend rejects the seventh schema without modifying it; a consistent pre-upgrade backup remains readable by that compatible build. Preserve/verify such a backup before operational upgrades. Never drop tables or edit migration history operationally to downgrade. Application backup/restore and production upgrade remain separate RC gates.

## Explicit Draft workers (#22, first Stage B slice)

Additive migration `20261122200000_AddAssignmentStaffing` follows the seven-schema Draft baseline. `AssignmentStaffingChanges` retains Assignment ID/revision, WorkItem/Crew/local date/AM-PM context, configuration flag and UTC recording time. `AssignmentStaffingMembers` references the change and stable Employee ID, recording employee name and Home Crew ID as saved. Both tables reject UPDATE/DELETE; no existing table/ID/note is rewritten by migration. The latest change determines explicit current membership. No change means unconfigured; a saved empty selection is distinct and never certifies safe staffing. Current member labels/status use live master data; history uses immutable saved snapshots.

`PUT /draft-assignments/{id}/staffing` requires strict `employee_ids` and `expected_revision`. A write reservation covers reference/revision checks, assignment revision/timestamp and complete append. Same selection at current revision is a no-op; duplicates/missing IDs reject without partial changes. Only Draft can change; cancellation preserves history and removes default active occupancy. Changing visit WorkItem/Crew/date/slot appends an unconfigured event in that same edit transaction; note-only edits preserve selections. Failed writes roll back both assignment and history. `GET /draft-assignments/{id}/staffing-history` reads recorded context; `employee_id` on the existing date-range read selects only explicit latest configured associations. It does not expand Home Crew or assume a default actual Rig.

All responses remain Pending / `publishable=false`; no publication path is added. Conflicting, inactive or empty Draft choices are not validated dispatch. Fresh/legacy upgrades and forced post-DDL failure/retry are tested. Previous seven-schema binaries reject migration eight; keep a consistent pre-upgrade SQLite backup (including WAL through the backup API or a verified closed/checkpointed state) with its compatible build. Never edit history/drop tables operationally to downgrade. Application backup/restore and production upgrade remain separate gates.

## Employee recorded availability (#77)

Additive migration `20261123010000_AddEmployeeAvailability` follows schema eight. `EmployeeAvailabilityChanges` records Employee ID, positive per-employee revision, inclusive Start/End dates, FullDay/AM/PM, Available/Unavailable/Unknown and UTC recording time. UPDATE/DELETE triggers preserve history. `EmployeeAvailability` holds sparse current AM/PM cells keyed by Employee/date/slot; a composite FK keeps the cell's change ID and employee consistent. Current cells store only Available/Unavailable; clearing to Not recorded removes the current cell while retaining the Unknown audit event. Original IDs, notes, resources, staffing and assignments are untouched.

GET/PUT `/employees/{id}/availability` read/save a range; PUT requires strict `expected_revision`, dates, slot and state. No-change saves do not increase revision/history. `BEGIN IMMEDIATE` covers revision check, range event and all cell updates/clears. Any failure rolls back all changes. Reads include revision/entries in one snapshot. GET `/employees/{id}/availability/history` returns the latest 100 saved events; older events remain stored. GET `/employee-availability?local_date=...&slot=AM|PM` returns each existing employee's recorded state for the Draft picker; missing cells are Unknown and storage failures are errors, not fabricated unknown/available values.

Dates are local ISO strings, without UTC conversion; event timestamps are separate. Operations are bounded to 366 dates as a technical workload limit. Full day updates both slots; AM-only never overwrites PM. Range Save is explicit replacement, not a merge inferred from Home Crew or jobs. Active/inactive master status and driver approval stay unchanged. Availability is not approved leave or weekend consent; all Drafts remain unpublishable.

Fresh/legacy migration, eight→nine rollback/retry and original-row preservation are tested. Schema-eight builds require their consistent pre-upgrade backup for fallback and reject newer history. Never edit history/drop tables to downgrade an operational database; application backup/restore and production upgrade remain separate gates.

## Shared Project and Crew working calendars (#26)

Additive migration `20261123020000_AddWorkingCalendars` follows schema nine. `WorkingCalendars` identifies exactly one Crew **or** Project, with unique nullable FKs and an XOR CHECK. Owner UPDATE/DELETE triggers preserve identity; WorkItems have no independent calendar owner. `WorkingCalendarChanges` retains a positive per-calendar revision, inclusive dates, FullDay/AM/PM, Working/NotWorking/Unknown and UTC recording time; UPDATE/DELETE is forbidden. `WorkingCalendarCells` stores sparse current Working/NotWorking AM/PM cells. Its composite FK links ChangeId and CalendarId to the same history/owner; Unknown clears current cells but retains the event. Original Projects/WorkItems/resources/availability/staffing/visits/notes remain unchanged.

GET/PUT `/working-calendars/{Crew|Project}/{id}` read/save up to 366 inclusive local dates; PUT requires `expected_revision`. No-change writes append nothing, and `BEGIN IMMEDIATE` covers revision/reference checks, owner creation, range event and every cell change. Failed range writes roll back all changes. GET `.../history` returns latest 100 events while older history remains. GET `/working-calendars/assessment?work_item_id=...&crew_id=...&local_date=...&slot=AM|PM` resolves the real WorkItem.ProjectId in SQLite and reads both snapshots in one transaction. No WorkItem calendar write/override exists. Read failures are errors, never fabricated Unknown.

Current Draft responses include `calendar_assessment`, both calendar revisions and the inherited Project ID. Calendar closure/unknown does not prevent Draft save under the owner's explicit decision; existing Crew/date/slot uniqueness and all IDs/notes/workers remain protected. No calendar edit changes the stored assignment revision. Consumers must reload current feedback; future recommendation/Apply/publication must independently revalidate every hard resource/safety gate and relevant revision. Calendar Matched is not dispatch eligibility.

Migration tests reconstruct synthetic schema nine, retain populated original tables, force a post-DDL history-insert failure, prove complete rollback and retry, and test stale/concurrent/partial-range failures. Schema-nine Python builds reject the newer migration history; operational fallback requires a verified consistent pre-upgrade backup and its compatible binary. Never edit migration history/drop tables to downgrade a customer database. Native installation/upgrade and backup-recovery evidence remain separately recorded in the linked acceptance record.

## Read-only recommendation snapshots (#28 phase three)

No schema/migration is added. `recommendation_adapter.py` reads the existing
schema in one mode=ro/query-only transaction and returns detached frozen inputs.
WorkItems.ProjectId is authoritative; caller Project IDs only check context.
WorkingCalendars.ProjectId supplies the shared calendar for every child WorkItem.
Crews and latest ForemanChanges remain master data. DraftAssignments of all
WorkItems on selected Crews occupy only when Status=Draft; Cancelled rows retain
history but release capacity. There is no replacement/exclusion or progress deduction.

AssignmentStaffingChanges/Members supply current explicit employee IDs, never Home
Crew expansion. Relevant Employees plus sparse EmployeeAvailability and per-employee
revision are observations, not proposed attendance or resource approval. Current
calendar revision/latest change ID, assignment revision and staffing/Foreman IDs
are retained. Projects/WorkItems/Crews have no shared native revision; canonical
logical content supplies scoped change detection without adding a global version.
Fingerprint equality is not dispatch eligibility, a lock, or transaction Apply
permission. See [architecture](02-ARCHITECTURE.md#consistent-persisted-recommendation-inputs-28-phase-three).

Current schema validation is read-only: incompatible versions, bad integrity/FKs,
locked/failed reads, deadline/limits return errors with no snapshot. Never migrate
or initialize a profile while calculating a recommendation. No published/history
rewrite, actual-worker/Rig selection, HTTP/Tauri/UI or save path is introduced.

## Saved-Draft personnel observations (#15)

Snapshot v2 requires an all-Crew/horizon `personnel_assignments` tuple alongside
selected-Crew occupancy. Both use actual DraftAssignments → WorkItems.ProjectId,
native revisions and latest AssignmentStaffingChanges/Members in one read-only
transaction. Saved staffing context must match the visit and refer to an earlier
or current positive assignment revision; malformed sources fail without a
fingerprint. History is not unioned into current workers. Cancelled releases
capacity; still-Draft visits on inactive Crews count.

All actual workers, including other Crews' borrowed workers, enter related
employee observations and the logical fingerprint. Other-Crew changes in the
horizon can make a snapshot Stale. Rebuild v1 inputs; no migration/write/derived
conflict table/history rewrite. The pure report identifies employee/date/half
and affected Assignment/Crew/WorkItem/Project IDs. Empty/unconfigured staffing
is Pending. No attendance, Home Crew change or proposed approval is inferred.

## Crew roster

The first #8 slice adds the Crews table to the local SQLite database. The stable generated ID survives name, type and status edits. Crew type is Civil or Tower. The roster keeps inactive rows visible and has no hard delete. Search uses literal substrings with SQLite's existing ASCII case behavior. Crew names are labels, so multiple rows may share a name. A roster row is master data and does not establish scheduling eligibility. Employee master data and Foreman appointment history are described below.

The Tauri backend applies its AddCrewRoster migration in the same SQLite write transaction as preceding upgrades, including from M0 and Project Master files. Demo notes and existing project and work-item IDs stay in the same tables. The migration has its own entry in the shared history and preserves the original EF Core entries. A Tauri build from before #8 rejects the newer migration history. Before upgrading a live profile, preserve a verified pre-upgrade backup and use a compatible build or the original database copy for fallback. This branch validates synthetic upgrades and retry after rollback.


## Employee roster

Employees have a stable ID, name, required Home Crew ID, skill level 1 through 3, foreman eligibility and active status. Foreign-key enforcement covers the Home Crew link. Deactivating a crew does not change its employee references. The editor lists inactive crews with their status so existing links can still be read and edited. The roster has no hard delete. Foreman eligibility is a master-data field. Foreman appointments, daily assignments and temporary transfers have their own workflows.

The AddEmployeeRoster migration adds Employees and its Home Crew index within the existing migration transaction. Fresh, M0, Project Master and Crew-only databases take the corresponding upgrade path. The new migration leaves existing note, project, work-item and crew IDs intact. Driver status has a database default and constraint of Unverified. The employee write API has no driver approval field. The earlier Tauri preview rejects the newer migration history, so test fallback with a verified pre-upgrade backup and a compatible build.


## Foreman master-data history (#8)

`AddForemanHistory` (`20261122030000`) adds `ForemanChanges` after the Rig schema, without changing existing rows or IDs. Each append records Crew ID, nullable Employee ID (clear), names as recorded and UTC recording time. The highest change ID for a Crew determines its single current Foreman, or Unassigned. A never-appointed Crew has revision zero. The time records when a change was saved; it is not a retrospective scheduling effective date.

Foreign keys retain Crew/Employee references. Database triggers reject history UPDATE and DELETE. Reads show current employee name/active/eligibility alongside immutable change-time snapshots. Later employee or Crew edits do not clear appointments or rewrite history. Home Crew and Driver status are untouched. New appointments require an active, Foreman-eligible employee; cross-Home-Crew appointment is allowed. This is master data, not dispatch or staffing approval. See the owner's bounded decision in the [register](10-CLIENT-DECISIONS.md); Demo D policies remain open.

GET/PUT `/crews/{id}/foreman` read/save the state. PUT requires `employee_id` (integer or null) and `expected_revision` (last change ID or zero). A write reservation covers revision/eligibility checks, append and response snapshot. A stale revision returns 409 without a write; a same-choice save at the current revision adds no history. On an uncertain response, reload before retrying. Failed inserts/migrations roll back. The UI preserves the failed selection until reload and makes discarding it explicit.

Fresh and legacy M0/Project/Crew/Employee/Rig schemas upgrade in the existing transaction. Regression cases retain all note/project/work-item/Crew/Employee/Rig values, force failure after DDL and verify rollback/retry. Earlier previews reject the sixth migration. Preserve a verified consistent pre-upgrade backup; fallback requires that original copy with its compatible build. Do not edit migration history or drop history tables in an operational database. Application backup/restore and production upgrade remain separate RC gates.

## Rig inventory

The AddRigInventory migration adds Rigs, a unique NOCASE Number index and a DefaultCrewId index in the existing SQLite migration transaction. A rig has a stable generated ID, required number and type, optional notes, optional default Crew reference, and active status. Leading zeroes in the number are preserved. An inactive rig retains its number and references. Crew deactivation keeps the optional association intact. The UI offers inactive crews with an explicit label, and operators may clear the association.

The default Crew link is master data for future assignment entry. It carries no date-scoped reservation or eligibility. Future maintenance, inspections and actual vehicle swaps can reference the stable Rig ID. Demo A still needs to confirm number conventions, type labels and default vehicle expectations.

Synthetic regression tests cover upgrades from the Employee schema, existing note/Project/WorkItem/Crew/Employee preservation, a failure after Rigs DDL with transaction rollback and retry, duplicate and concurrent case-variant numbers, and retirement/reactivation on the same ID. Earlier previews reject the newer migration history. Preserve a verified pre-upgrade backup before upgrading a live profile. Recovery requires a compatible build or the pre-upgrade database copy. Packaged upgrade and operator backup/restore acceptance remain part of the RC gate.

## Migration check

The Python backend uses the existing EF Core table and migration identifiers. On a fresh file it creates the demo, Project Master, Crew, Employee, Rig, Foreman history and Draft Assignment schemas. On an M0 file it adds the missing tables and indexes while preserving the note. On a Project Master file it adds the empty resource tables in place and preserves project and work-item IDs and values. The schema update runs in a single SQLite write transaction. Unknown migration histories are rejected.

The Python regression suite uses SQL generated by the checked-in EF migration tooling against the synthetic schema. It verifies fresh startup, note edits and restart, M0 upgrade, Project Master data preservation, constraints, and rollback with retry after a failure inside the schema transaction. It uses temporary databases, including the synthetic copy for the upgrade. Verify application-level backup and clean-PC offline upgrade during packaging before using the Python path with business data.

Check for untracked model changes after restoring the local tool manifest.

```powershell
dotnet tool restore
dotnet ef migrations has-pending-model-changes --project src/Rigarus.Infrastructure --startup-project tests/Rigarus.Infrastructure.Tests
```

Before a future schema upgrade on business data, implement and verify an appropriate consistent backup and rollback path. Keep fixture storage separate when introducing real project data.
