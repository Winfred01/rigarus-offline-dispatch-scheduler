# SQLite data model

## Source-linked Draft Restore (schema twenty-one, #20)

`20261127010000_AddDraftRestoreVersions` adds exactly two tables and immutable
UPDATE/DELETE guards; no original table/version JSON/history is rewritten.

| Table | Contract |
| --- | --- |
| DraftRestoreVersions | Independent positive recovery-version ID, original DraftVersion FK, lineage FK, unique request UUID, exact plan SHA, immutable before/proposed/after/resource/acknowledgement audit JSON and UTC time |
| DraftRestoreReceipts | Separate UUID namespace/payload SHA, lineage FK, optional existing original-version FK, optional committed recovery-version FK, immutable Committed/Rejected JSON and UTC time |

One transaction commits new DayDraft revisions/history/members, recovery audit/
version and receipt. Original source versions remain immutable. New records from
the old batch cancel rather than delete. Previously cancelled originals keep
their IDs when reactivated, with higher revisions. The only inverse targets are
`FullDayDraft+id`; `LegacyHalfDay+id` never aliases it. No past resource evidence is
recreated. Recovery versions are not original DraftVersions or Published snapshots.

Recognized20 receives an independently consistent, integrity/FK/digest-verified
backup before DDL under the existing reservation. DDL/history/backup failures
abort safely; retry/reopen is idempotent. Actual prior20 sidecar must reject21
without changing it and reopen an independently restored verified20 backup.
Never remove live migration history or overwrite21 to downgrade. Later writes
must be reconciled separately if a prior backup is used. Current schema is21;
older sections below are dated historical slice descriptions. See
[migration/recovery evidence](acceptance/2026-11-27-issue-20-draft-restore.md).

Issue126 desktop integration adds no SQLite migration: schema20 is unchanged.
Native exact-request journals/acknowledged receipt archives are local recovery
files, separate from immutable DraftVersions. Preserve unresolved recovery files
with their matching database/profile during diagnosis; a NotFound receipt is not
proof of rejection. This is not database-file undo, a Published version store or
permission to discard later edits. Existing IDs/notes/people/history/legacy rows
and all previous schema compatibility guards remain in force.

## Confirmed Draft changeset versions (schema twenty, #124)

`20261126010000_AddDraftVersions` adds only immutable DraftVersions: monotonic
version ID, unique namespaced request UUID/payload SHA, retained lineage UUID FK,
exact plan SHA, result JSON (review proof, before/after, confirmation, observations)
and UTC time. It is both atomic batch audit/version and committed request receipt;
the independent manual editor namespace is unchanged. Old IDs/Slot/notes/members/
history/FKs are not converted. Existing rows retain matching Crew/date IDs;
removed dates cancel with new history; new dates receive new IDs. Schema19 gets
verified consistent pre-DDL backup; DDL/history failures roll back and retry/reopen
is safe. Older binaries reject20; no in-place downgrade or history removal.
Versions cover exact touched Draft records, not entire database recovery or
publication. Inverse preview never rewinds revisions or writes. See
[evidence](acceptance/2026-11-26-issue-124-draft-transactions.md).

## Read-only impact proposals (#18, no migration)

Schema19 remains unchanged. One pinned query-only read combines its lineage UUID,
active target index/notes, exact FullDayDraft IDs/revisions and existing coherent
daily/legacy/resource sources. A detached scenario releases only selected day
capacity; it never cancels saved records or writes receipts, confirmation, locks,
members, Rig choices or proposal/audit/version rows. Canonical source/proposal
SHA256 and exact typed revision vectors are read observations, not a global
database version or authorization. Saved Remaining Days is Not recorded because
no confirmed-day field exists. Original slots/IDs/history remain untouched.
Future Apply/audit/recoverable-version persistence needs a separate reviewed
contract/migration; the current editor receipt is not schedule undo. See
[impact evidence](acceptance/2026-11-26-issue-18-impact.md).

## Manual Draft recovery (schema nineteen, #120)

`20261125040000_AddDayEditorReceipts` is additive after18; original tables,
IDs, estimates, slots, notes, personnel, relations and history are unchanged.

| Added table | Contract |
| --- | --- |
| DayEditorWorkspace | One immutable database-lineage UUID at Id1; scope recovery to the database rather than an assignment integer |
| DayEditorReceipts | Immutable canonical request UUID, exact payload SHA256, serialized Committed/Rejected result and UTC time; unique key committed atomically with saved Draft/history |

UPDATE/DELETE triggers protect identity/receipts. Identical replay returns the
same JSON; changed payload never replaces the original receipt. A receipt can
refer to an older revision after later edits: reload current state before another
edit. Unknown read errors are distinct from absent receipts. NotFound is uncertain,
not permission for a new create key. Existing occupancy/history/Rig guards stay.

Verified backup precedes DDL, failure rolls back, retry preserves recovery data,
19 startup is idempotent. Actual old18 binary rejects19 and reopens an independent
restored18 backup unchanged. No in-place downgrade/customer restore was performed;
old backup recovery loses later edits and requires operator reconciliation.
Production writes stay closed; all Draft safety/Apply/Publish gates remain pending.

## Actual-worker full-day consent (schema eighteen, #113)

Additive `20261125030000_AddDailyWeekendConsent` follows17. No existing row,
stable ID/Slot/note/relation/revision/history/sequence is converted or rewritten.

| Table | Contract |
| --- | --- |
| WeekendConsentScopes | Immutable WorkItem/Project/Crew/local weekend date/Employee FKs and unique scope; parent/date validated |
| WeekendConsentChanges | Immutable sequential per-scope revision; Pending/Confirmed/Declined; explicit employee-decision/full-day assertion; exact roster JSON/SHA256; Proposed or FullDayDraft source with saved ID/revision; reference/UTC timestamp |

Indexes support dated lookup. SQL enforces valid explicit nonempty unique existing
employee roster, decision scope membership, full-day confirmation, exact current
saved context/roster, sequential append and immutable identities/history. Store
write reservation and expected revisions protect concurrent callers; failure
rolls back scope creation/sequence and history together. Identical current decision/
reference/context is a no-op; latest Pending cannot resurrect older Confirmed.
There is no old half-day consent table to convert. Legacy attendance remains
Needs Review even with separately recorded full-day employee evidence.

Recognized17 startup takes an independently verified pre-DDL backup under the
existing reservation. DDL/history faults roll back; backup failure aborts before
DDL;18 reopens idempotently. Recovery uses independent verified17 backup and its
compatible prior binary, retains live18 separately for later edits/reconciliation,
and never deletes migration history. See [actual evidence](acceptance/2026-11-25-daily-weekend.md).
Recommendation reads use query-only current18 and never initialize/migrate17.
Snapshot v6 SHA includes raw decisions, exact planned rosters and native revision.
Earlier schema identities below are historical descriptions.

## Dated Rig allocation and independent conditions (schema seventeen, #111)

Necessary additive `20261125020000_AddDailyRigs` follows16. No previous table values,
IDs, Slot, notes, employee/vehicle/default links, revisions/history or FKs change.

| Table | Purpose |
| --- | --- |
| RigAllocations | Immutable identity, exactly one unique DayAssignmentId or LegacyAssignmentId with RESTRICT FKs |
| RigAllocationChanges | Append-only positive owner revision, assignment revision/current-time WorkItem/Project/Crew/local date, original/actual Rig FKs, explicit company/full-day/operational flags, reviewed native condition revision, bounded reference and separate UTC event time |
| RigConditionPeriods | Immutable Rig/kind identity; independent Maintenance/Inspection/OutOfService records can overlap |
| RigConditionChanges | Append-only positive period revision, canonical inclusive dates, Active/Cancelled, explicit confirmation/reference and UTC event time |

Four views expose current conditions, saved visit context, current allocation and
conservative daily occupancy. Indexes support Rig condition/current allocation
lookups. SQL context/original-identity/readiness/collision triggers protect event
appends; Rig move triggers extend existing saved day/legacy updates/restores.
Full-day readiness cannot be attached to a legacy half; positive assertions cannot
override inactive/active-condition blocks or a changed native condition revision.
Same Rig/date across Crews rejects under concurrent writes; same-Crew old halves
can retain a vehicle. Cancelled releases capacity. Stale recorded/current claims
retain both dates/Crews until explicit review; original/current WorkItem/Project
context and all events stay visible. History/identity UPDATE/DELETE rejects.

Internal stores use BEGIN IMMEDIATE, expected assignment/allocation/condition
revisions, explicit original/actual/operational input and reference; event/identity
creation rolls back together. Period cancellation is per identity, never a blanket
clear of overlapping records. No-op is not a fresh readiness approval. Master
Active/default link does not grant readiness/attendance/category qualification.
No new allocation/condition HTTP writer or desktop write gate is enabled.

Recognized16 startup receives an independent verified pre-DDL backup under the
write reservation. DDL/views/triggers/history all roll back on failure, backup
failure aborts before DDL, current17 reopens idempotently. Recovery uses verified16
backup plus compatible prior binary; retain live17 separately for reconciliation
of later edits. Never delete migration history or overwrite the newer profile
to downgrade. [Evidence](acceptance/2026-11-25-daily-rigs.md) covers actual16→17
sidecar upgrade, prior-binary rejection and independent backup reopening.

Daily snapshot format v5 adds canonical Rig observations/nominees/native revisions
to existing logical SHA256 in one query-only transaction; rebuild v4 proofs.
Legacy reader refuses relevant new Rig observations. Snapshot reads never migrate16.
Current schema is17; earlier sections retain historical slice identities.

## Daily policy and qualification provenance (schema sixteen, #109)

Necessary additive `20261125010000_AddDailyCapabilities` follows15. Existing
CapabilityEvidenceOwners remains immutable WorkItem or Employee+exact-code
identity. New DailyCapabilityChanges stores positive per-owner native revision,
canonical inclusive local dates, bounded strict versioned payload, company/full-day
confirmation, reference, legacy review/native revision/raw snapshot and UTC event
time. New DailyCapabilityCells has unique owner/date without Slot, immutable-event
FK/context triggers and per-date legacy SHA256 receipt. Old capability/driver/
calendar/assignment/master/history/notes/IDs/revisions/FKs/sequences stay untouched.

Policy payload reuses explicit CapabilityRequirements; null is an explicit
unknown-policy tombstone. Employee payload has Verified/NotVerified/Unknown,
independent of Employee.SkillLevel or driver status. The daily table plus explicit
full-day confirmation establishes new provenance; shared owner identity alone
never promotes old AM/PM evidence. Duplicate JSON keys/types/context reject.
Save reserves BEGIN IMMEDIATE before revision/range-token comparison; event/cells
commit together or roll back. Same current payload/reference no-op; legacy change
requires re-review. No daily evidence HTTP/UI writer or authenticated authority.

Recognized15 startup now receives the same independent verified pre-DDL backup
under the write reservation. Migration DDL/history rolls back on failure, backup
failure aborts before DDL, current16 reopening is idempotent. Recovery requires
independent15 backup plus compatible prior binary, never remove live migration
history. [Actual evidence](acceptance/2026-11-25-daily-capabilities.md) includes
synthetic actual15→16 sidecar upgrade/rejection/backup reopening and fault tests.

Daily snapshot SHA256 format v4 includes raw/effective daily policy/qualification
source, current event IDs/reference, native revisions/legacy receipts and existing
actual-worker context in one budgeted read-only view. Legacy reader recognizes16
but refuses any in-range daily capability cell, even Unknown/null, with
DAILY_CAPABILITY_ADAPTER_REQUIRED; old proofs become Stale. Recommendation reads
never initialize or migrate15. Production daily writes remain closed. Current
schema is16; earlier schema sections remain historical compatibility references.

## Independent daily company-driver assertions (schema fifteen, #107)

Necessary additive `20261124050000_AddDailyDriverApprovals` follows14. Reusing old
Slot evidence would incorrectly promote half-day approval; separate storage gives
explicit full-date provenance while preserving all original values/IDs/history/
revisions/notes/relations/sequence. No old table or migration is rewritten.

| New table | Contract |
| --- | --- |
| DailyDriverApprovalChanges | Immutable Employee FK/positive per-employee revision, canonical local inclusive dates, Unverified/Active/Suspended/Expired, CompanyConfirmed=1 and FullDayConfirmed=1, explicit reference/notes, legacy acknowledgement/native revision/raw snapshot and separate UTC RecordedAt |
| DailyDriverApprovalCells | Unique Employee/local date, no Slot; explicit Unverified retained; composite employee/state/history FK and dated-context triggers; per-date legacy receipt SHA256 |

The internal store reserves BEGIN IMMEDIATE before comparing revision/range token;
history/cells commit atomically. Same current state/reference/notes is a no-op;
changed legacy source requires new review. History UPDATE/DELETE and invalid
cell/date/context fail. Raw old negatives survive unknown/stale daily assertions;
fresh explicitly reviewed daily Active may supersede a negative for new daily
planning while preserving the raw evidence. This is recorded company assertion,
not authenticated authority, legal license/category or actual-Rig certification.

Existing recognized14 startup now takes verified pre-DDL backup under the same
write reservation and independent pinned backup connection. All DDL/history roll
back on failure; backup failure prevents migration; current15 reopen is idempotent.
Recovery uses the independent verified14 backup with its compatible prior binary,
never migration-history deletion or unsafe downgrade of live15. Actual packaged
14→15/rejection/independent recovery is covered in [evidence](acceptance/2026-11-24-daily-drivers.md).

Daily recommendation source format v3 includes raw/effective daily-driver entries,
change IDs/references/native revisions/legacy receipts in the same query-only
transaction and logical SHA256. Older snapshot proofs must rebuild. Legacy
recommendation reads recognize15 but reject any in-horizon daily-driver cell,
even Unverified, with DAILY_DRIVER_ADAPTER_REQUIRED; freshness reports Stale.
Schema14 itself is not silently upgraded by recommendation reads. Daily production
HTTP writes remain closed, and no driver-evidence HTTP writer is added. Historical
sections below retain their original slice identities; current schema is15.

## Daily actual/proposed personnel observations (#105, no migration)

Schema14 stays unchanged. One pinned daily recommendation transaction already
contains all Crews' day/legacy visits, current actual members/revisions and related
evidence. The new saved-personnel report converts these detached observations;
no conflict table/history/worker edit is persisted. Raw old slots remain locators,
while new daily collision capacity groups whole local dates and keeps ID namespaces.
Cancelled releases capacity; latest staff replaces history. Existing Crew/date
and cross-model SQL guards are unchanged.

Optional query proposed_employee_ids extends related observations without adding
attendance. Their metadata/daily availability/raw old resources share the same
transaction and read budget. Daily snapshot SHA256 format becomes v2; rebuild v1.
An explicit candidate-membership proof also hashes normalized member choices and
the exact input/option. Current/Stale is scoped source equality; no global version,
DB/WAL byte hash or Apply authority. Unknown membership/context Pending; known
cross-Crew daily conflict Blocked. Legacy evidence is never full-day eligibility.

No schema migration, operational conversion, source-worker removal or saved-Draft
mutation. Actual transfer/audit and original-Crew resource revalidation remain
#23/#25/#18/#29 work. Backup/recovery design remains unchanged; run all existing
migration/preservation tests. See [acceptance](acceptance/2026-11-24-daily-personnel.md).

## Daily recommendation observations (#103, no migration)

The following is the merged2B baseline; current v2 personnel observations extend it above.

Slice2B reads current schema14, including schema13 DayDraft tables, using one
pinned query-only transaction. It adds no table, column, revision counter or
duration write contract. Remaining Days is an explicitly confirmed query input;
WorkItems.EstimatedHalfDays and historical visits are never converted/deducted.
Older13 alone is unsupported by this read path; startup migration remains separate.

Day and legacy visits retain separate ID namespaces, parent/date/status/revision
and current staffing. Any active legacy half or day visit occupies the full Crew
date; Cancelled releases it without deletion. All-Crew horizon visits preserve
other-Crew borrowing/resource context. Daily calendar/availability observations
include effective/raw state, native daily/legacy revisions, current cell/change
identity and legacy review receipts. No silent positive legacy projection.
Related old driver/capability/qualification data stays compatibility evidence,
not full-day certification. Employee Home Crew remains master data, not attendance.

Frozen snapshot format `rigarus-day-recommendation-input-v1` uses canonical logical
SHA256, query confirmation/days/bounds/Crews/order/limit, opaque source scope and
all consumed observations. Same-query re-read detects changed daily/old calendars,
visits, members, metadata and related evidence; unobserved scope/checkpoints are
not mutations. Current is not future Apply authority. Errors produce no partial
fingerprint. No DB/WAL copy/hash, checkpoint, initialization or business/schema
write in recommendation reads. Existing backup/recovery remains unchanged;
full migration regression tests are still required. See
[actual checks](acceptance/2026-11-24-day-recommendations.md).

## Daily assertions (schema fourteen, #101)

`20261124040000_AddDailyCalendars` follows13 additively. No old Assignment,
staffing, calendar/availability, driver/capability or history row/ID/Slot/note/
revision/sequence/relation is converted, rounded, merged or removed.

| Table | Contract |
| --- | --- |
| DailyCalendarOwners | Immutable identity: exactly one unique CrewId, ProjectId or EmployeeId; RESTRICT FKs; no WorkItem override |
| DailyCalendarChanges | Append-only owner revision, local date range, scoped state, OperatorConfirmed, LegacyReviewed, native LegacyRevision, retained LegacySnapshot JSON, notes, UTC event timestamp |
| DailyCalendarCells | Unique owner/date, no Slot; explicit Unknown retained; composite owner/state/change FK, event-range trigger, per-date legacy receipt SHA256 |

SQL enforces owner XOR, scope/state, canonical dates, positive integer revision
and immutable owners/history. Store ranges are bounded to366 dates. A write
reservation protects expected revision/review token and all range upserts; failure
rolls back the whole event/range. Identical current assertions are no-ops; source
change requires a new review event. Receipts bind raw old states/change IDs and
native legacy owner revision, so later legacy edits invalidate positive capacity.
They are concurrency observations, not authentication or signed approval.

Explicit Unknown retains a current tombstone/history. Unreviewed legacy positives
never supply daily capacity; known negatives block. Reviewed daily assertions may
supersede old values for new daily use while keeping raw legacy evidence visible.
Production daily writes stay closed. Old recommendation readers reject daily cells.

Existing recognized schema13 startup now takes the same verified pre-DDL backup
described below. DDL/history append roll back together; backup failure aborts
before DDL; already14 is idempotent. Recovery means independent verified backup
plus its compatible previous binary, never deleting migration history. Synthetic
fixture helpers that construct old schemas are test-only. Actual13 packaged
rejection of14 and independent backup reopening are tested; see
[recovery evidence](acceptance/2026-11-24-daily-calendars.md).

## Full-day Draft compatibility (schema thirteen)

This section records the PR100 schema13 baseline; current schema14 extends it above.

`20261124030000_AddDayDraftCompatibility` is additive after schema12. Original
DraftAssignments, WorkItems.EstimatedHalfDays, staffing, availability/calendars,
driver/capability evidence and histories keep their exact values and stable IDs.
The original Crew/date/Slot unique index is retained; no failing global Crew/date
index is applied to historical AM+PM rows. No data is rounded, merged or converted.

| New table | Contract |
| --- | --- |
| DayDraftAssignments | Independent stable integer ID namespace, WorkItem/Crew RESTRICT FKs, canonical local date, notes, Draft/Cancelled, positive revision, separate UTC timestamps; **no Slot column** |
| DayDraftChanges | Immutable assignment/revision/WorkItem/Crew/date/notes/status/staffing-configured snapshots; one per revision |
| DayDraftMembers | Immutable explicit Employee ID, saved name/Home Crew snapshot per change; Employee/Crew FKs; never automatically expands a Home Crew |

Daily partial unique `(CrewId,LocalDate) WHERE Status='Draft'` handles two daily
writers. Symmetric INSERT/UPDATE triggers on daily and legacy assignments reject
overlap with the other model's active Crew/date, regardless of AM versus PM.
Cancelled releases occupancy; reactivation cannot bypass those guards. Store
preflight returns actionable 409 conflict details under BEGIN IMMEDIATE; SQL is
the final cross-model guard. Saved cancellation retains identity/history.
Daily full PUT explicitly replaces membership: null is unconfigured, [] explicitly
empty; callers retain the current IDs for note edits or explicitly reconfirm them
for a new context. No old staffing history is repointed to the new namespace.

Separate `/day-draft-assignments` read/list/history/legacy-compatibility routes
identify `record_kind=FullDayDraft`; old `/draft-assignments` returns old IDs plus
LegacyHalfDay/Needs Review/conversion-required metadata. Default sidecar daily
write gate is closed until visible daily UI and safety integration. No new Tauri
command or frontend record can accidentally invoke the new write path. A daily
record must never be joined to an old assignment merely because integer IDs match.

Before DDL on an existing recognized pre13 profile, initialization holds a write
reservation and uses a separate pinned read connection/SQLite backup API. It
creates an exclusive `*.before-day-<random-id>.bak` alongside the source; previous
backups are never overwritten. Verification compares complete logical schema,
rows, types, duplicate rows, sqlite_sequence and migration history plus integrity
and FK checks. Technical verification bounds:1million rows/128MiB counted encoding,
30-second best-effort deadline and normal five-second SQLite busy wait. Exceeding
them or failing backup/storage verification aborts the upgrade; no partial success.
Fresh profiles need no pre-upgrade backup. Already13 startup is idempotent.

DDL/history insertion share the existing transaction and roll back on failure.
Fallback is **a verified independent backup with its compatible previous binary**,
never table/history deletion or an in-place down migration. Schema12 binaries
reject13; actual packaged rejection and restored12 reopening were tested using
synthetic data. Preserve the upgraded file separately; restoring a pre-upgrade
copy does not preserve later daily edits and requires operator reconciliation.
No automatic restore or customer profile modification was performed by this task.

Earlier half-day sections below are retained historical schema/API references;
the owner's new Full Day rule takes precedence for new scheduling.

## Explicit capability evidence (#25, schema twelve)

Necessary additive `20261124020000_AddCapabilityEvidence` follows schema11
inside the existing startup transaction. No original table/ID/level/driver flag,
Home Crew, visit, staffing, Foreman, calendar or prior history is rewritten.
There was no authoritative persisted source for requirements or separate verified
qualifications; these records enable real SQLite-backed checks without inventing
defaults or overloading Employee.SkillLevel.

CapabilityEvidenceOwners identifies exactly one WorkItem policy or one
Employee+case-sensitive technical qualification code through an XOR CHECK,
unique identities and protected FKs. Ownership is immutable.
CapabilityEvidenceChanges stores native per-owner Revision, inclusive local
dates/AM-PM/FullDay, bounded version1 JSON, CompanyConfirmed=1, evidence Reference
and separate UTC recording time. History UPDATE/DELETE is forbidden.
CapabilityEvidenceCells links current owner/date/half to its history through a
composite FK. Readers validate history date/half context and strictly decode
payload keys/version/types; duplicate JSON keys are rejected.

WorkItem payloads explicitly specify positive minimum members, three nonnegative
Level minima, Exact/AtLeast mode and qualification-code/count pairs. Qualification
payloads record Verified/NotVerified/Unknown separately from levels and driver
approval. No unrecorded date inherits a policy/certificate; there is no automatic
expiry, certificate equivalence, approver-role authentication or company standard.
An explicitly empty qualification list is an assertion, not the missing-policy
default. Actual threshold values and legal meaning remain customer decisions.

Internal Store saves require confirmation/reference and expected revision under
BEGIN IMMEDIATE; history and all current cells commit or roll back together.
Identical evidence/reference is a no-op; corrected reference appends history.
The latest100 history events are returned while older records remain stored.
No HTTP/UI editor or actual staffing Apply is added.

Read-only snapshot v4 fingerprints related owner IDs/native revisions/current
cells and all related WorkItem/Crew context in one transaction. Rebuild v3 input
objects. Schema11 binaries reject schema12; operational fallback needs a verified
consistent schema11 backup and compatible binary, never manual table/history
removal. Synthetic upgrade preservation/rollback/retry is tested; no real customer
database was opened/migrated, and native upgrade/recovery remains a separate gate.

## Dated company-driver evidence (#23, schema eleven)

Additive `20261124010000_AddDriverApprovals` follows schema ten in the existing
startup migration transaction. Original employee fields, IDs, Home Crew, staffing,
visits, calendars and prior history remain unchanged. The legacy DriverStatus
CHECK still permits only Unverified; existing roster writes cannot grant approval.

DriverApprovalChanges retains EmployeeId, positive per-employee Revision,
StartDate/EndDate, AM/PM/FullDay, Unverified/Active/Suspended/Expired, explicit
CompanyConfirmed=1, bounded evidence Reference and separate UTC RecordedAt.
UPDATE/DELETE history triggers and FK protection apply. DriverApprovalCells
stores current exact local date/AM-PM/state/change ID. Composite FK links the
same employee/state to its immutable history; reads verify dated context.
Explicit Unverified is retained as evidence, never approval. No date outside a
recorded cell inherits Active and no legal expiration rule is invented.

The internal Store requires expected revision under BEGIN IMMEDIATE; recording
and cells commit together or roll back. Changed evidence references append a
new event; identical state/reference is a no-op. History reads return latest100,
older history stays stored. This adds no HTTP/UI approval editor or actual
staffing mutation. Company confirmation is a recorded operator assertion,
not authenticated company authorization or actual-Rig/category certification.

Read-only snapshot v3 includes related actual workers' driver revisions/cells
from the same transaction and fingerprints them. Earlier read-only adapters and
schema10 binaries reject schema11. Operational fallback requires a verified
consistent schema10 backup and its compatible binary: never delete tables/history
to downgrade a live profile. Synthetic migration rollback/retry and preservation
are tested; native installation/upgrade/recovery and customer acceptance remain
separate. No customer database is migrated by this development task.

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
