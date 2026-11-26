# Architecture

## Independent Full Day Draft editor (#120, schema19)

Strict `day_editor_api.py` contracts call `day_editor_store.py` transaction
service, reusing connection-level DayDraftStore and saved-resource validators.
One BEGIN IMMEDIATE covers database/request identity and payload hash, current
revision/Project, explicit staffing, existing day/legacy/Rig SQL guards, saved
row/history, complete observations and immutable result receipt. Source/storage
failure rolls back. Same request replays its original JSON; changed payload
cannot reuse it. Resource reasons remain Blocked/Pending with root false flags.
No default safety policy, worker/source transfer or actual Rig is inferred.

PR122 recovery review additionally validates the complete Committed record against
the original action/typed ID/revision/WorkItem/Project/Crew/date/notes/members and
false safety flags before clearing recovery evidence. Unknown/malformed rejection
is uncertain; another current journal is never intentionally cleared. Transport
returns without acknowledgement; the editor's normal accept path settles once.
This is not atomic cross-window localStorage coordination: concurrent app-instance
journals remain an unqualified production rollout gate. See
[review](design/2026-11-25-issue-120-recovery-review.md).
Before/After remains [design only](design/2026-11-25-impact-preview-contract.md)
until this prerequisite PR is human-merged and main builds.

React journals the unchanged request in local WebView storage before dispatch,
scoped by database UUID, bounded and treated as untrusted. Invalid/unwritable
journal blocks dispatch. Resolve reads the exact receipt; NotFound is not proof
of rejection. Only explicit unchanged same-key replay is permitted after unknown
outcomes, never blind create retry. Stale rejection retains form fields until
deliberately loading saved values. Committed save survives failed weekly refresh;
retry refresh is read-only. Unclear journal clearing leaves recoverable evidence.
UUID is database-lineage identity, not authentication or future freshness proof.
Desktop editor calls have a150second outer deadline; timeout does not cancel or
disprove a commit. Preserve the journal and ignore a late reply until explicit
reconciliation. Rust HTTP60second and SQL30second checks remain independent.

Boards reload actual rows; active identities use typed Locate, cancellation
leaves active grids but remains readable by Full Day ID/history. Context edits
require explicit worker reconfirmation; note-only edits preserve members. Raw
legacy records, original IDs/notes/history and independent evidence are retained.

Schema19 is additive with verified backup/atomic migration. Older binaries
reject19 and need an independent compatible pre-upgrade backup; restoring it
does not retain later edits. No operational downgrade or customer DB restore.
Readers now recognize19; schema18 workbench below is merged119's baseline.

Production daily writes stay closed. Packaged sidecar test flag
`--synthetic-day-editor` requires the dedicated
`RIGARUS_SMOKE_DATA_ROOT/data/rigarus.db`; desktop adds it only with explicit
`RIGARUS_DAY_EDITOR_TEST=1` and matching root. This synthetic engineering opt-in
does not authorize customer rollout. Raw day/calendar writer gates remain
independently closed; Apply/Publish are not exposed by this editor.
See [design](design/2026-11-25-issue-120-day-editor-checklist.md) and
[evidence](acceptance/2026-11-25-issue-120-day-editor.md).

## Full-day weekly workbench (#119)

`schedule_workbench.py` reads schema18 through one pinned mode=ro/query-only
transaction. Weekly metadata and both saved ID namespaces share the existing
100k-unit/64MiB/30second read budget. Reuse daily snapshot sources and existing
saved personnel/driver/capability/Rig/consent validators, plus exact daily calendar
assessment; no duplicated safety algorithms or inferred members/vehicles. Weekly
ranges are at most7 local dates, technical Crew scope at most100; exceeded bounds
and source failures fail explicitly without a partial board. The result digest
describes the visible loaded view, not a complete source freshness/Apply proof.

Fixed authenticated GET week/typed Locate paths return whitelisted saved facts.
Locate reads kind+ID/current status and target week in the same transaction;
cancelled/missing records do not fall back to another namespace. Legacy raw slots,
notes and IDs remain Needs Review. Unknown subchecks stay Pending and every root
Apply/Publish false. No migration, production writer or safety-policy change.

Job Schedule/Crew Board default to the shared read-only daily workbench. Detail/
review/typed Locator reveal exact cards across week/filter boundaries, center and
focus internally with the existing2second/reduced-motion cue. Request epochs
prevent stale week/Locate results; navigation cancels pending cues. Existing
legacy editing remains distinctly labeled compatibility functionality, including
the unchanged Project Assign handoff; it is not new Full Day entry. Current global
Schedule search still indexes legacy rows and explicitly passes LegacyHalfDay;
daily records use the typed Locator. Employee Week/calendar editing remain legacy.

Merged118 Auto-Recommend is reused from WorkItems/details, with no saved overlay
or automatic reservation. Independent daily editor120 and human Apply/versions/
exports remain later slices. See [design](design/2026-11-25-issue-119-workbench-checklist.md)
and [actual checks](acceptance/2026-11-25-issue-119-workbench.md).

## Read-only full-day WorkItem preview (#117/#28)

`day_recommendation_api.py` exposes strict POST `/day-recommendations/preview`
and `/day-recommendations/freshness` projections over the existing query-only v6
snapshot/generator. No writer gate, migration, membership or resource inference
is added. Explicit safe IDs, confirmed Remaining Days, inclusive local dates,
100 Crew/366 date/1–10 result limits retain adapter bounds. Missing confirmation
remains Needs Review. Whitelisted results include coherent WorkItem titles,
ranked alternatives, skipped dates/reasons and grouped missing-check counts;
never full snapshots, database paths or raw personnel evidence. Read failures
return sanitized errors, never Current. Context edits make freshness Stale.

The authenticated Rust sidecar command accepts only `preview`/`freshness`, bounded
payloads and fixed read-only paths. Project WorkItem Auto-Recommend uses the
existing Dialog, independent preview/freshness epochs, input invalidation,
manual/window-focus rechecks and close/unmount guards. No late reply restores
old output. Current means observed at read time, not a reservation. Every result
remains FullDay / Validation Pending / Apply=false / Publish=false; actions are
disabled. Daily boards/evidence editors and human Apply remain separate work.
See [design](design/2026-11-25-issue-117-day-preview-checklist.md) and
[actual verification](acceptance/2026-11-25-issue-117-day-preview.md).

## Actual full-day weekend consent (#113/#27)

`daily_weekend_consent.py` is pure and bounded: explicit dated actual/proposed
rosters plus latest full-day employee decisions. Identity is WorkItem/Project/
Crew/local Saturday-or-Sunday/Employee, never HomeCrew/global availability.
Confirmed requires exact nonempty roster fingerprint; saved evidence additionally
matches stable day Assignment ID/revision. Even removing then returning the same
workers cannot resurrect saved approval. Pending/missing/stale/legacy attendance
requires review; applicable Declined blocks despite other missing evidence.
Cancelled visits release capacity; weekday consent is not applicable.

`daily_weekend_store.py` internally records explicit employee-decision/full-day/
reference assertions, append-only revisions and proposed versus saved provenance.
BEGIN IMMEDIATE protects expected consent revision, saved assignment revision and
current roster. Planned consent never proves saved attendance; the saved helper
records actual current workers independently. No HTTP/UI consent writer, employee
communication, authenticated approval authority or production gate opening exists.

Daily snapshot v6 observes relevant target/source WorkItems' latest consent rows
and native max event IDs in the same pinned query-only transaction as calendars,
availability, people, drivers, capabilities and Rigs. Optional immutable
WeekendCrewDay(Crew,date,Employee IDs) declares weekend alternative rosters, and
captures those employee observations. No membership is inferred. Query/observations
enter SHA256; any relevant decision edit, including conservative outside-horizon
edit, invalidates old proofs. Existing100k units/64MiB/30second bounds include
decoded consent memberships. Errors fail without Current/partial fingerprints;
readers never migrate17. Rebuild v5; legacy generation refuses new consent.

Only fully confirmed exact planned workers can supply WeekendConsent Satisfied
to existing daily accumulation/PR91 comparison. Working calendars and free Crew
date remain independent; Pending/Declined is skipped with reasons and per-member
planned checks retained even for skipped dates. Different Crew plans are
alternatives, never simultaneous reservations. All other resource evidence remains
independent; consent is not employee availability or safe dispatch certification.

All proposed weekend members must match the query roster even at the lower-level
personnel entry point; changing workers requires a new query/candidate. The
`day_weekend_proposal.py` wrapper reuses personnel/driver/capability/Rig checks,
then checks effective target and every borrowed source roster before/after.
Source refusal excludes with WeekendConsent Blocked; changed positive source
roster Pending. No implicit source removal, approval transfer or saved mutation.
Input/proposal SHA and same-query freshness are observations, never future locks.
Every root result remains Validation Pending/Apply=false/Publish=false.

Next independent slice prioritizes daily desktop weekly visibility and visible
recommendation/consent reasons; native/offline interaction acceptance remains
required. #18/#29 must later implement locks, Before/After, transaction revalidation,
explicit human Apply/audit/recoverable versions before validated file delivery.

## Actual daily Rig evidence and proposal-only replacement (#111/#24)

`daily_rig_store.py` records explicit actual vehicle facts per stable saved day or
legacy visit, distinct original/actual Rig IDs and immutable assignment context/
revision/reference. No default Rig is inferred. Legacy allocation is partial
occupancy, never full-day operational proof. New day operational assertions require
explicit company/full-date confirmation and a caller-reviewed native condition
revision under BEGIN IMMEDIATE. No-op preserves history; original known Rig ID
is retained. This is internal recording, no resource HTTP/UI writer or authority
authentication. Master active/default/type/notes remain unchanged inventory data.

Independent condition identities/events represent Maintenance, Inspection and
OutOfService inclusive local-date periods. Overlapping records remain independent;
cancelling one cannot clear another. Active conditions/master inactive always
block even with an operational assertion. Later condition changes invalidate
prior positive readiness, conservatively even outside horizon; after cancelling
all blocks the old assertion stays Pending until explicitly reconfirmed. No legal
inspection due-date/category/license equivalence is invented.

SQL current views plus triggers protect cross-Crew Rig/date occupancy on allocation
append and saved day/legacy move or restoration. Old AM/PM consumes the whole date
for daily safety; same-Crew old halves may retain the same vehicle. Cancelled
visits release capacity without history deletion. Changed assignment context
keeps both recorded/current date/Crew claims conservatively until reviewed and
cannot supply readiness. Recorded WorkItem/Project IDs remain distinct from current
IDs in diagnostics; even a recorded in-horizon claim whose visit moved outside
the horizon is read. Existing Crew/date/legacy overlap guards remain intact.
Known Rig collision on an existing legacy HTTP move returns409 with reload/review
feedback instead of a storage503; no route or production-gate shape changes.

`daily_rig_validation.py` is pure: indexed whole-date claims and bounded condition
projection. Known duplicate actual Rig/different Crew Blocked; missing actual or
unknown other-Crew allocation Pending. Active alone/default association/original
Rig never supply actual capacity. Operational positive needs full-date explicit
proof, complete context/scope and matching condition revision; missing/stale/legacy
proof Pending. Reasons retain periods, identities, original/actual/default IDs,
context and driver-category Pending. Input/condition projection/assessment bounds
100,000 prevent quadratic/unbounded work; grouping uses indexes and sets, not
pairwise Crew comparisons. Every root result Validation Pending/false flags.

Daily snapshot v5 includes explicit Rig nominees, all relevant saved allocation
and stale recorded context, referenced/nominee/default masters, condition periods
and native revisions in the same pinned query-only transaction with existing
row/byte/deadline limits. SHA256/Current-Stale binds those observations and existing
actual personnel/driver/capability/calendar data. Nomination is observation only;
missing explicit Rig lookup fails. Rebuild v4 proofs. Source errors never mean
Current/safe empty scope; Current remains logical equality, not a future lock.
Legacy adapter recognizes17 but refuses in-range Rig evidence with a specific
stale/context reason. Recommendation reads never initialize/migrate a profile.

`day_rig_proposal.py` reuses the exact capability/driver/personnel plan and explicit
source worker overrides. Per-date Rig choices require explicit operational planning
evidence/reference, never a default fallback. Rig states from target and affected
borrowed sources enter PR91 RigAvailability/RigConflicts; an unsafe source blocks
even when the target Rig/people pass. Known blockers exclude before limiting,
stable date sorting preserved. Missing dates/uncaptured Rig context remain Pending.
Saved-visit replacement previews bind exact assignment/allocation revisions and
keep before/after/original vehicle; stale or partial legacy sources require review.
Saved versus Proposed evidence is explicit, so projected actual R2 never claims
that SQLite actual R1 changed. Proof SHA binds input, normalized choices/reference
and prior staffing proof; freshness re-reads exactly the original query.

No automatic allocation, source Rig transfer, Apply/Publish/export, new UI or
production write-gate opening. Vehicle-category driver eligibility remains Pending
independently of generic approved-driver status; no Rig.Type inference. Saved Rig
checks never certify unstaffed/unselected generated dates. Actual-worker weekend
consent #27, day UI/visible previews and #18/#29 transactional human Apply/audit
follow. See [design](design/2026-11-25-daily-rigs-checklist.md) and
[evidence](acceptance/2026-11-25-daily-rigs.md); historical slice sections follow.

## Daily explicit capability validation (#109,2C3)

`daily_capability_store.py` records slotless WorkItem requirements or exact-code
Employee qualifications using shared immutable capability owner identities and
new daily-only history/cells. Explicit company/full-day confirmation/reference,
expected revision/range review token and old-evidence acknowledgement are required.
No threshold, Level hierarchy, certificate or company policy is seeded. Reuse
CapabilityRequirements: positive member minimum, all three Level minima, explicit
Exact/AtLeast and explicit qualification-code/count list. Counts may overlap
independently; no disjoint-role allocation/legal equivalence is inferred. Explicit
empty qualification list differs from missing policy; None/Unknown tombstones
never resurrect old positives. This internal recorder adds no HTTP/UI writer.

Old positive policies/qualifications, including both halves or a legacy FullDay
event, never supply daily confirmation. Old NotVerified is conservative negative;
only fresh reviewed daily Verified can supersede it without rewriting history.
Legacy native revisions/per-date receipts expire positives after later edits,
even out-of-range edits. Stale/missing daily policy returns no effective policy;
known daily qualification negatives remain negative even if stale.

`daily_capability_validation.py` is pure and indexes whole local dates. Actual
explicit workers only: active, daily Available and complete collision-clear
context supplies confirmed counts. Unknown metadata/availability/proofs supplies
possible capacity only; inactive/Unavailable/colliding workers cannot count.
For every member/Level/code minimum, a known possible upper bound below the
requirement is Blocked, enough confirmed capacity satisfies that subcheck,
otherwise Pending. Unconfigured roster has no known upper bound; configured
empty roster is known zero. Legacy half-day attendance cannot prove a complete
daily roster and its counts stay Pending. Level never proves qualification and
qualification never changes Level. Known Crew inactivity/type mismatch blocks;
Small/Other mapping remains Pending. Foreman policy remains separately Pending.

Snapshot v4 captures every related source/target WorkItem policy, actual/proposed
employee qualification owner/code/revision/current cells/raw legacy/receipts in
the existing single pinned query-only transaction. Earlier half-day observations
remain separate. Same-query SHA256/Current-Stale binds all consumed sources;
new/old policy/proof, actual members, metadata and availability changes invalidate
prior input. Existing100,000 units/deadline plus shared64MiB SQL/projected-text
budget and per-owner250,000-character retained legacy source prevent payload
amplification. Exceeded bounds fail without a partial fingerprint. Rebuild v3.

`day_capability_proposal.py` calls PR108's exact-plan/explicit source override
checker and uses precisely those detached before/after rosters. It adds saved,
target and borrowed source capability counts, keeps stable record/WorkItem/
Project IDs/revisions, and propagates CrewType/MinimumStaffing/Skills/Qualifications
from both source and target to PR91 day comparison. Driver pass cannot mask a
source shortfall. Unrelated saved failures remain visible separately from the
candidate-related state. Missing evidence Pending; known blocker excludes before
limit; date sorting remains stable. Proposal SHA binds the driver's normalized
input/member/override proof and a new capability contract identity. Freshness is
source equality then, not a lock/Apply authorization.

Root results always Validation Pending / Apply=false / Publish=false. Entire
roster availability, Foreman, actual Rig, weekend consent and operator review
remain separate; no inferred attendance, source removal, staffing write, legal
certification, production write-gate opening or UI/API/export change. Technical
evidence/evaluation bounds100,000 and at most32 qualification codes keep indexed
counting bounded; no employee-pair comparisons. See [design](design/2026-11-25-daily-capabilities-checklist.md)
and [checks](acceptance/2026-11-25-daily-capabilities.md). Older sections below
retain their historical slice contracts, superseded for new daily scheduling.

## Full-date company-approved drivers (#107,2C2)

`daily_driver_store.py` records independent slotless, explicitly company/full-day
confirmed assertions with exact bounded dates/reference, expected revision and
range review token. Old DriverApprovalCells, including two Active halves or one
old FullDay history event, are retained observations and never positive daily
proof. Legacy Suspended/Expired is known blocking until a fresh explicitly
reviewed positive daily assertion. Unverified never resurrects old positives or
clears known old negatives. Native legacy revision plus per-date receipt expires
daily positives after later old edits, even conservative out-of-range edits.
The internal recorder has no HTTP/UI/authentication/production rollout path.

`daily_driver_validation.py` is pure. Only explicitly configured actual members
can count. An eligible full-date company driver needs current Active daily proof,
both confirmations, active Employee, daily Available and collision-clear complete
personnel scope. Missing/Unverified/stale/partial-day facts remain Pending;
Suspended/Expired/inactive/Unavailable/double-booked members cannot count. One
eligible member satisfies only ApprovedDriver; all known ineligible is Blocked,
an unknown alternative keeps Pending. Missing roster is Pending; explicitly
configured zero workers is known zero drivers/Blocked. Old half-day attendance
still needs review even with new daily approval; it is never silently merged.
Cancelled releases capacity. No Home Crew, Foreman, Rig or attendance inference.

The same pinned query-only daily transaction now captures independent daily/raw
legacy driver sources/revisions/receipts for every observed worker. Shared SQL/
projection/deadline limits apply. Snapshot SHA256 format v3 replaces v2; rebuild
older proofs. Same-query Current/Stale covers daily and old approval, availability,
actual memberships and all other consumed sources. Current is not Apply authority.
`PersistedDayRecommendations.driver_validation` explains saved visits only;
unstaffed generated candidates still have ApprovedDriver Pending.

`day_driver_proposal.py` checks one exact generated alternative and explicit
ProposedDayMembers. Optional SourceDayMembers is a full replacement roster for a
namespaced active saved source with matching revision/date and actual borrowed
member context. It changes detached data only. Without it, source members remain
and collisions block. Reports retain before/after, target and every known borrowed
source check. Source driver failure **or source personnel collision** blocks the
candidate, including a replacement's collision with a third Crew. Missing source
evidence stays Pending; no automatic replacement/driver selection. An explicit
empty source also conservatively leaves target personnel scope Pending under2C1,
while its known driverless source makes the candidate Blocked.

Daily PersonnelConflicts and ApprovedDriver evidence enters the existing PR91 day
comparator; known blockers exclude before limiting, stable date sorting remains.
Proposal SHA256 binds input, exact option, normalized date members/source overrides.
All-scope failures remain visible separately from candidate-related state. Other
resources, source minimum/skills/qualifications, actual Rig/category, weekend
consent and review remain independent Pending. Root reports are always Pending /
Apply=false / Publish=false. No API/UI, transfer Apply or write-gate opening.

Grouping/indexing is O(V+M+E), deterministic sorting O((V+M+E) log(V+M+E));
bounded100,000 visits/memberships/facts and source replacement memberships, at
most366 dates. Conflict member lookup uses sets, source checks group by date,
avoiding worker-pair/source-date rescans. See [design](design/2026-11-24-daily-drivers-checklist.md)
and [evidence](acceptance/2026-11-24-daily-drivers.md). Historical sections below
describe earlier slices and are superseded by the current daily contract here.

## Daily personnel safety foundation (#105,2C1)

`daily_personnel_conflicts.py` checks explicit Employee IDs by whole local date.
Frozen DailyStaffedVisit preserves record kind (FullDayDraft/LegacyHalfDay/Proposal),
ID/revision/WorkItem/Project/Crew/date, actual configuration/members and raw legacy
AM/PM locator. Day/proposal identity never uses a half. Distinct namespaces allow
equal old/day/proposal integer IDs without collision. Current saved identities
must be unique; existing Crew day/legacy-slot occupancy invariants remain checked.
Cancelled identities remain in diagnostics while releasing capacity.

Index active membership by (date,employee); two distinct Crews produce
EMPLOYEE_DOUBLE_BOOKED_DAY with all affected references. Legacy AM or PM both
participate; opposite old halves in different Crews are also conflicts under the
new daily rule. No historical record is converted or rewritten, and the old
half-day validator retains its historical semantics. Missing/empty staffing,
partial scope or unknown other-Crew membership on that date is Pending; known
conflicts stay Blocked. No active records means Pending. Satisfied concerns only
this collision subcheck, never availability, approved driver or full dispatch.
Every root report stays Validation Pending / Apply=false / Publish=false.

At most100,000 visits/memberships; deterministic sorting takes
O((visits+memberships) log(visits+memberships)), materialization is linear.
Unknown-Crew lookups use set size/membership without copying a large set per
visit. Compact references are reused instead of copying complete rosters.
Pure validation makes no file/network/SQL/system-time calls.

The daily snapshot adapter now exposes day_staffed_visits and
validate_day_snapshot_personnel; PersistedDayRecommendations.personnel_validation
reports saved day/old visits' current actual membership from the existing pinned
view. Latest member revision replaces history; no historical member union or
Home Crew/Foreman/Available attendance inference. Unstaffed generated candidates
still have PersonnelConflicts Pending; saved reports never certify new workers.

DayRecommendationQuery.proposed_employee_ids is an optional sorted unique tuple
(technical max1000). It captures explicitly nominated candidate employees, even
from unselected Home Crews, in the same read-only transaction: metadata, daily/raw
availability and old resource sources/revisions. It records observation only,
not attendance or membership. Missing explicit employee fails lookup. Existing
read/projection/deadline budgets apply. Format is now
`rigarus-day-recommendation-input-v2`; rebuild v1 proofs. Added observation IDs and
data enter SHA256; staff/visit/employee/availability/resource changes make prior
snapshots Stale. Source failure never means Current or an empty safe scope.

`day_personnel_validation.py` accepts one actual generated complete candidate and
explicit ProposedDayMembers for its dates. It regenerates that candidate from the
supplied snapshot to check exact date/context values; duplicate/out-of-plan dates
reject. Missing membership or uncaptured employee context remains Pending. One
alternative is combined with all saved visits; alternatives are not simultaneous
reservations. Per-date PersonnelConflicts evidence enters PR91 day comparison:
Blocked excludes before limit, clear subcheck Satisfied still leaves all other
resources Pending. The all-saved-scope report stays visible separately from
candidate-related state/conflicts; an unrelated employee's conflict is not proof
that the candidate's workers conflict.

Borrowing never silently removes source members. If still saved in another Crew,
the employee conflicts; known source references carry mandatory Pending driver,
minimum, skills, qualifications and availability rechecks. These markers cover
known current overlaps, not an exhaustive transfer/approval workflow. After any
real membership change, #23/#25 must re-evaluate all affected source/destination
actual Crews; #18/#29 must retain before/after transfer context and revalidate in
the write transaction. No source revision or employee Home Crew is changed here.

Candidate report binds snapshot/input SHA256 and a separate deterministic
`rigarus-day-personnel-proposal-v1` SHA256 of that input, exact option and normalized
date/member choices. Changing choices produces a new proof. Freshness re-reads
the original query; Current means source equality then, not a lock/authentication
or Apply permission. Missing/changed sources Stale; read/schema errors propagate.
No migration/UI/Rust/HTTP/writes or production-gate change. Daily #23/#25 eligibility,
actual #24 Rig/#27 consent and full manual review remain later slices. See
[design](design/2026-11-24-daily-personnel-checklist.md) and
[evidence](acceptance/2026-11-24-daily-personnel.md).

## Daily recommendation engine and coherent inputs (#103, slice2B)

This records the merged2B baseline; personnel-aware v2 query/snapshot additions
are documented above. Earlier v1 proofs must rebuild.

New planning uses independent `ConfirmedRemainingDays(days, confirmed_by_operator)`
from `day_drafts.py`; positive integer only, strict explicit confirmation. Missing
duration is Needs Review. Old EstimatedHalfDays stays a reference observation;
neither estimates nor saved visits/history are converted or deducted. Legacy
half-day generator/adapter contracts remain compatibility code, never the new day path.

`day_recommendation_generator.py` accepts immutable DayGenerationRequest with
WorkItem/parent/Crew IDs, required Crew count, confirmed days, earliest/horizon
local dates, separate DayCalendars and DayOccupancy, plus explicitly scoped
independent per-date evidence. It indexes inputs and scans each local ordinal
date once. Both calendars must be current Working; Unknown/closure/conflict/
unreviewed/stale positive evidence, occupied date or known resource blocker is
skipped with reasons. Missing/partial occupancy coverage is also skipped as
Unknown, never inferred free. Weekends require exact full-date Satisfied consent;
persisted planning has no such approval source yet, so it skips weekends.
Other missing resources remain Pending; gaps do not reset accumulated work.
One earliest cumulative option per Crew scenario, not exhaustive optimization.

Outputs retain actual allocated dates, confirmed/accumulated/unfilled days,
proposed start/finish, scanned/skipped states/reasons, calendar counters and missing
checks. Insufficient capacity retains partial dates/deficit but no finish or ranked
complete option. Multi-Crew/missing confirmed work returns Needs Review without
scanning. Annual bound is before next anniversary (Feb29 clamps to Feb28), at
most366 inclusive dates, with year9999 safe. Up to100 alternative scenarios.

PR91 `recommendation_comparison.py` now also has genuine ProposedDay/
ExplicitDayOption/DayOptionComparison contracts. Shared constraint definitions,
evidence policy and `_rank_evaluated` retain hard-filter-before-limit, default
EarliestFinish, alternate EarliestStart, then Crew/option-ID stable ties and1–10
limit. No day is represented by fake AM/PM. Pure scan/index work is linear in
bounded input/horizon; comparison sorting O(H log H). No I/O, SQL or system clock
in generation/comparison. All proposals/comparisons stay Pending/false flags.

`day_recommendation_adapter.py` exposes internal build_day_recommendation_snapshot,
day_generation_requests, generate_from_day_snapshot and check_day_snapshot_freshness.
DayRecommendationQuery has a confirmed-day object or explicit missing None; no
half-day field or fallback. One mode=ro/query-only `BEGIN` transaction pins current
schema14/integrity/FKs and all reads: actual parent/Crew/Foreman metadata, schema13
day Drafts/current immutable staffing, all Crews' old visits/current staffing,
daily Crew/Project/related-employee inputs and raw legacy evidence/receipts, old
company-driver and capability/qualification observations. Existing connection-level
read helpers share this view; public Store reads are never composed. Older13,
future/unknown or broken schema is rejected without initialization/migration.

Both ID namespaces remain distinct. Any active old AM or PM blocks the whole
date for that Crew, including same WorkItem; day Drafts also occupy the whole
date. Cancelled records remain observations but release capacity. Related actual
workers, selected Home Crew/Foreman employees are **observations only**, never
attendance or proposed membership. Old driver/qualification evidence is not daily
approval; daily resource validators #15/#23/#25 and actual #24/#27 remain missing.

Snapshots are detached frozen dataclasses with canonical immutable JSON source
payloads. A shared ReadBudget/BudgetCursor charges materialized SQL rows and daily
projection cells against100,000 units, including nested legacy helpers. A30-second
SQL progress/end deadline and existing5-second busy timeout fail without a partial
snapshot/fingerprint. Synchronous OS work still needs an independent caller budget.

Fingerprint format `rigarus-day-recommendation-input-v1` hashes canonical logical
query/confirmed days/sort/limit, opaque normalized source-location scope, migrations,
metadata, current daily/raw legacy cells/receipts/native revisions, all horizon
visits/current staffing and related old resource observations. No DB/WAL byte
hash or global version. Observed-owner revisions can conservatively stale changes
outside the horizon; unrelated unobserved owners stay outside scope. Re-reading
the exact query returns Current on equality, Stale on changed/missing/moved inputs.
Storage/schema/limit/deadline errors propagate as failures, never false Current.
Current is observation equality then, not a lock, authenticity or Apply authority.

No database migration, HTTP recommendation route, Tauri/UI, selected workers/Rig,
Apply/Publish/export or opening daily write gates. Production daily-input/day-Draft
writes remain default closed. Packaged-sidecar tests verify compatibility/gates;
the new internal algorithm is exercised by locked Python tests and the synthetic
SQLite console example, not a new packaged GUI/API workflow. See
[design](design/2026-11-24-day-recommendations-checklist.md) and
[evidence](acceptance/2026-11-24-day-recommendations.md).

## Daily inputs (#101, day-based slice2A)

`daily_calendars.py` resolves slotless Crew/Project Working/NotWorking/Unknown
and Employee Available/Unavailable/Unknown (labelled Not recorded). No weekday,
holiday, attendance, eligibility or weekend approval is inferred. WorkItems use
their persisted ProjectId without overrides. Calendar Matched is only a calendar
observation: resource validation Pending, Apply/Publish false.

`daily_calendar_store.py` reads at most366 inclusive local dates in one
mode=ro/query-only transaction, with connection-level snapshot/assessment helpers
for a future daily adapter. Reads never initialize, migrate or write. Even two
positive legacy halves remain Unknown until an explicit new daily assertion.
Unreviewed/stale legacy negatives block; mixed/partial raw states and change IDs
remain visible as Needs Review. Save requires explicit operator confirmation,
daily revision/range review token and legacy acknowledgement when old cells exist.
A reviewed new assertion may explicitly supersede old negative evidence for the
daily workflow, while original values/history stay unchanged and conversion-required.

BEGIN IMMEDIATE covers receipt comparison, immutable event append and range
upserts. Concurrent writes cannot both use one expected revision. No-op requires
matching state/notes/current receipt. Explicit Unknown is stored, never a fallback
to legacy positives. Per-cell receipt hashes scope/owner/date/raw legacy states,
change IDs and native legacy owner revision. Any subsequent legacy revision,
including out-of-range changes conservatively, makes the receipt Stale: positives
become Unknown until re-review, known negatives remain blocking. Tokens record
observations for concurrency/review; they are not authentication or Apply locks.

Schema14 is additive. Strict `/daily-calendars/{Crew|Project|Employee}/{id}`
GET/PUT/history and `/daily-calendars/assessment` GET have no slot. Production
writes remain **default closed**, independently of the closed day-Draft gate.
Only app-factory test opt-in enables writes. No Tauri command/React control is added.
The half-day recommendation adapter recognizes14 and refuses **any** in-horizon
daily cell (even Unknown/unrelated owners conservatively), returning
DAILY_CALENDAR_ADAPTER_REQUIRED. Prior snapshots become Stale; the guard shares
the pinned read. Out-of-horizon daily data does not alter the old query scope.

DayDraft payloads stay unchanged; dedicated bounded reads avoid introducing large
per-worker lookups or partially visible feedback before coherent daily snapshot/UI
integration. Day allocator, confirmed-day duration persistence, full daily snapshot,
personnel/driver/qualification/Rig/consent validators and UI follow separately.
See [design](design/2026-11-24-daily-calendars-checklist.md) and
[evidence](acceptance/2026-11-24-daily-calendars.md).

## Day-based Draft compatibility (#99 slice1)

New `DayDraft` is slotless: WorkItem/Crew/local date, notes and explicit nullable
Employee IDs. `ConfirmedRemainingDays` accepts only an operator-confirmed positive
integer; no half-day estimate is converted or deducted. `DayDraftStore` uses a
write reservation, daily Crew/date uniqueness, cross-model overlap guards and
append-only dated revision/member snapshots. Every result stays Pending with
missing calendar/resource evidence and false Apply/Publish. Explicit staffing is
not attendance, company-driver or eligibility certification.

Additive schema13 preserves all old tables/IDs/Slot/history/revisions/FKs. Daily
and legacy IDs are separate **record-kind namespaces**, with separate HTTP routes;
future UI/Locate must retain the kind and never route a daily ID to old assignment
commands. `day_draft_api.py` offers strict local read/list/history/legacy-report
contracts, but daily HTTP writes are **default disabled**. Only explicit app-factory
opt-in (synthetic tests) enables create/edit/cancel. The production sidecar does not
opt in. React/Rust stay on protected legacy paths until the independent day UI slice.
This intentional staging exception does not authorize new AM/PM business contracts.

`day_compatibility.py` reads one bounded mode=ro transaction. It preserves original
half values/change IDs and owner context; reports same/different/single legacy
visits and complete/partial/mixed evidence with Needs Review, never conversion.
Known calendar closure/unavailability or suspended/expired driver evidence is
retained as blocking evidence. Driver/capability coverage alone never satisfies a
new daily resource check. Blank dates remain Unknown. No Project calendar override,
Home Crew attendance, actual Rig or weekend consent is inferred.

Legacy recommendation snapshots now recognize schema14 (schema13 at slice1) and refuse any daily record
in their requested horizon, including Cancelled history conservatively. The guard
shares the existing pinned read transaction. Prior inputs become Stale on that
context change; no half-day allocator ignores a daily occupancy row. Out-of-range
daily data does not alter that legacy query scope. Detached legacy algorithms
remain legacy-only, not a daily recommendation API. Daily generation/validation
and full UI integration remain slices2/3. Earlier AM/PM sections below describe
historical code behavior, superseded as new business requirements.

## Exact saved-visit Locate (#16)

The existing Publish review lists dated observations from saved visits' calendar
assessments and actual staffing, including visits hidden by board filters. It is
not a new resource validator. Review and draft details share Locate with the
existing global saved-record search. Locate re-reads the persistent assignment
ID and current workspace before navigating to its current local Sunday–Saturday
week in Job Schedule / 1 Week. Only incompatible Crew/Project filters are cleared.
Each AM/PM button keeps its assignment ID, including visits inside multiday strips.

`schedule-locate.ts` isolates record guards, filter revelation, sticky-grid scroll
geometry and an injected-clock cue controller. Rendering closes the source dialog,
centers the exact card within the internal grid and focuses it without scrolling
the document. Temporary amber highlighting is independent of detail selection;
it expires after 2000ms, cancels on repeat/navigation/unmount and is static with
reduced motion. Request tokens reject stale asynchronous responses. Unavailable,
cancelled or invalid records produce recovery feedback before date/filter changes.
An active draft editor is never silently discarded. No IPC/API, persistence,
dependency, schema or publication contract changes. See [design](design/2026-11-24-issue-16-locate-checklist.md)
and [verification](acceptance/2026-11-24-issue-16-locate.md).

## Explicit Crew capability requirements (#25 first slice)

`capability_validation.py` checks actual saved Draft members against dated,
explicitly confirmed WorkItem requirements. There are no default minimums:
minimum members, all three Level minima, Exact/AtLeast mode and the separate
qualification-code/count list are required inputs. Counts are independent
overlapping minima, not disjoint role allocations. Company-defined codes are
exact technical identifiers; no case, code or legal equivalence is inferred.
Explicitly empty qualification requirements differ from a missing policy.

Active/Available workers without #15 collisions supply confirmed capacity.
Unknown metadata/availability remains only possible capacity; inactive,
Unavailable or double-booked members are excluded. Per requirement, a known
possible upper bound below the confirmed minimum is Blocked; enough definite
workers satisfies that subcheck; other cases stay Pending. Empty/unconfigured
membership and missing policy stay Pending. Reports retain required values,
confirmed and possible Employee IDs and reasons. Level never creates a Verified
qualification; qualification evidence never substitutes for a Level requirement.
Civil/Tower mismatch and inactive Crew block capability; Small/Other mapping or
missing context stays Pending. Actual Project/WorkItem IDs are preserved.

Foreman appointment is master data, not dated attendance. Its effective-date,
promotion and merger rules remain unresolved: Foreman stays Pending and every
otherwise clear visit/report stays Pending. This per-Crew visit scope does not
certify multi-Crew synchronization, all project roles or full dispatch.
No existing visits/worker selections/master/history are modified by validation.

`capability_store.py` records explicit company assertions through an internal
service, with expected revision, immutable owner/history, exact dated cells,
no-op handling and atomic rollback. It is not an approval UI/API or authenticated
certification authority. Necessary additive schema12 stores WorkItem policy and
employee/code qualification owners, versioned bounded evidence and cells.
Existing employee levels/driver constraints/Foreman and assignment invariants
remain unchanged. Actual company thresholds/codes are not seeded by this slice.

Snapshot v4 adds all related WorkItems' parent/type/requirement owners/revisions/
cells and all horizon Crews' type/active observations plus related employees'
qualification owner revisions/cells in the same pinned read-only view and
100,000-row budget. Missing records are unknown; malformed payload/context
fails before a fingerprint. Other-Crew policy/qualification/master changes can
mark old inputs Stale. Rebuild v3 snapshots; initialization/upgrades remain
separate from calculation. `validate_snapshot_capabilities` converts detached
inputs and `PersistedRecommendations.capability_validation` exposes the report.

Pure evaluation has no SQL/file/network/clock calls. Indexed evidence and
deterministic sorting avoid pairwise worker comparisons. Qualification requirements
are bounded to32; aggregate evidence and assessment work are each bounded to
100,000 units, rejecting excess without a partial report.
Generated options still have no proposed actual workers and retain Pending
MinimumStaffing/Skills/Qualifications/Foreman checks in PR91. Apply/Publish stay
false. See [design](design/2026-11-24-issue-25-capability-checklist.md) and
[evidence](acceptance/2026-11-24-issue-25-capability.md).

## Company-driver evidence and checks (#23 first slice)

`driver_eligibility.py` separates frozen dated company-approval evidence and
pure validation from SQLite. Explicit actual members are checked per local
date/AM-PM; at least one Active approval with explicit company confirmation,
active Employee, recorded Available and no #15 double-booking satisfies this
company-driver check only. Missing/Unverified approval, missing worker/availability
or incomplete scope is Pending. Suspended/Expired, inactive, Unavailable or
double-booked workers are Blocked; if every actual member is known ineligible
the visit is Blocked. Missing/empty staffing or no active visits stays Pending.
Cancelled releases capacity. No Home Crew/Foreman/default Rig inference.
Re-evaluating all visits after a proposed membership change also checks the
source Crew; validation never performs that change.

`driver_store.py` is an internal evidence service with explicit confirmed
range/status/reference input, revision-protected BEGIN IMMEDIATE, append-only
history, sparse exact-date cells and transactional rollback. Same state/reference
is a no-op. It is not an authorization system, legal license checker or HTTP/UI
workflow. Company approval authority and vehicle/category policy are unresolved;
recording a statement does not authenticate its author or certify an actual Rig.
Legacy Employee.DriverStatus and its Unverified CHECK/API remain unchanged.

Necessary additive schema11 stores DriverApprovalChanges/DriverApprovalCells.
Startup migrates separately; the read-only adapter never upgrades a database.
Snapshot v3 includes related employees' dated approval cells/change IDs/explicit
confirmation and native driver revisions in the existing pinned all-Crew view,
row/deadline budgets and fingerprint. Rebuild v2 snapshots. Other-Crew driver
changes and conservative out-of-range revision changes can mark snapshots Stale.
`validate_snapshot_drivers` operates on detached data;
`PersistedRecommendations.driver_validation` carries saved-Draft explanations.
Indexing/grouping is bounded by visits, memberships and supplied evidence with
deterministic sorting; no pairwise worker comparison or clock/SQL/I/O in core.

No proposed membership is selected: generated ApprovedDriver remains Pending in
PR91, regardless of saved-Draft results. Every result stays Validation pending /
Apply=false / Publish=false. Actual Rig/category, weekend consent, skills,
minimum staffing, qualifications and #18/#29 approval/locks/transaction/audit
remain independent. No UI/API/Apply/Publish path is added. See
[design](design/2026-11-24-issue-23-driver-checklist.md) and
[engineering evidence](acceptance/2026-11-24-issue-23-drivers.md).

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

The comparator itself has no allocator. The read-only adapter below supplies
stored inputs; full safety validators, HTTP/Tauri/UI integration and SQLite
writes remain absent. Supplied Satisfied evidence
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
the persisted parent and correct/current context. The adapter below supplies
consistent stored sources and scoped freshness checks; it does not certify
actual proposed workers/Rig or resource approval.
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

## Consistent persisted recommendation inputs (#28 phase three)

`recommendation_adapter.py` is an internal service, not an HTTP/Tauri/UI route.
`build_recommendation_snapshot(path, RecommendationQuery(...))` uses
`storage.connect(read_only=True)` with URI `mode=ro`, query-only, foreign keys
and the existing five-second busy timeout. `BEGIN` plus the first schema read
pins one SQLite transaction view. Current migration IDs/table set, quick_check
and foreign_key_check must pass. Older/newer/unknown schemas reject without
initialization or migration. No journal-mode change, checkpoint, immutable/nolock,
file copy or SQL business/schema write occurs. SQLite manages normal WAL/SHM.

The adapter resolves WorkItems.ProjectId through Projects, validates an optional
expected parent, and reads JobNumber/type/required count/estimate (reference only).
Connection-level calendar and availability snapshot helpers and current staffing
helper share that same connection. Public Store reads are not composed because
they open independent views. Crews retain type/active/current Foreman change;
inactive, Civil/Tower mismatch or unresolved Small/Other mappings return Crew
Needs Review outside ranking. This conservative planning filter is not #25
dispatch certification. Missing WorkItem/Crew is an explicit lookup failure.

All selected-Crew visits in the requested horizon retain stable IDs, parent and
WorkItem IDs, date/slot, status, revision, timestamp and latest staffing change.
Only Draft occupies; Cancelled remains observational history. Same-WorkItem
visits are never excluded or deducted: this service proposes new work, not a
replacement. Relevant employee observations include selected Home Crew members,
observed actual workers (including borrowing) and current Foremen. Sparse
availability includes native revision; absence is Unknown. Home Crew, Foreman,
Available and Unverified Driver never produce staffing/driver/qualification/
Rig/consent Satisfied evidence. The #15 saved-Draft collision report below now
includes other Crews; proposed workers remain unvalidated.

Frozen observations are detached before `generation_requests` constructs existing
`GenerationRequest`/`CrewOccupancySnapshot` values. `generate_from_persisted_snapshot`
reuses `generate_and_compare` → `generate_candidate` → PR91 `ExplicitOption`
comparison, with stable Crew IDs as option IDs. The wrapper retains snapshot,
existing generation/comparison results, excluded Crew review reasons and pending
validator names. Every result remains Pending / applyable=false / publishable=false.

`input_fingerprint` is SHA256 of canonical logical observations, format identifier,
query (confirmation/remaining/Crew IDs/bounds/order/limit) and an opaque hash of
the resolved local source location. It is not a DB UUID, global revision, DB/WAL
byte digest, authenticity signature or Apply authorization. Calendars/availability
retain native revisions; assignments retain revisions; staffing/Foreman retain
change IDs. Unversioned master fields are compared by content. The scope includes
extra observations and owner revisions, so an out-of-range calendar/availability
change for an observed owner may conservatively mark Stale. Unrelated Projects,
unobserved employees, default Rig, names not consumed by this contract and page
layout/checkpoints are outside the fingerprint.

`check_snapshot_freshness` re-reads exactly that query in another consistent view:
Current means scoped equality then; Stale means changed/missing/moved sources.
Storage/schema failures propagate, not false Current/Unknown. No global version
is invented. The source can change immediately after either transaction closes.
Future #18/#29 Apply must obtain current input/evidence, honor locks, revalidate
under its write transaction and roll back/audit failures; this service cannot Apply.

Reads use a 30-second progress deadline (SQL callback and end check), five-second
busy waits, at most 100 Crews and inherited annual bounds; observed Assignment/
staffing/employee/availability materialization is bounded to 100,000 rows. Limits
fail without a partial snapshot/fingerprint. Read errors are sanitized/distinct
(busy, unavailable, invalid, failed, deadline/limit); success and all failures
release the transaction/connection. Synchronous OS calls are not a hard real-time
guarantee and require the caller's independent process budget when exposed later.

See [design](design/2026-11-24-issue-28-adapter-checklist.md) and
[engineering evidence](acceptance/2026-11-24-issue-28-adapter.md).

## Explicit employee collisions (#15 first resource slice)

`personnel_conflicts.validate_employee_conflicts(tuple[StaffedVisit, ...],
start_date=..., end_date=..., scope_complete=...)` is pure and deterministic.
Inputs require explicit dated AM/PM Assignment/WorkItem/Project/Crew IDs, status,
staffing configuration and unique actual Employee IDs. The validator checks
annual scope and visit/membership limits, preserves unique active Crew/date/half
occupancy, ignores Cancelled visits, and indexes active membership by local
date/half/employee. Two or more distinct Crews produce EMPLOYEE_DOUBLE_BOOKED
with every affected Assignment/Crew/WorkItem/Project. Compact references avoid
repeating whole rosters for each shared worker. Space is O(visits + memberships);
deterministic sorting takes O((visits + memberships) log(visits + memberships)).

Per-visit checks are Blocked on collision, Pending on missing/explicit-empty
staffing or incomplete scope, otherwise Satisfied for this collision check only.
Known conflicts stay Blocked in partial views; no active visits means Pending.
Every report retains Validation pending / applyable=false / publishable=false.
No worker is inferred/reassigned and other resource gates remain independent.

Snapshot contract `rigarus-recommendation-input-v2` requires
`personnel_assignments`: all Crews' visits in the requested horizon, including
inactive Crews' still-Draft visits and other WorkItems/Projects. Latest explicit
staffing and related employees share the pinned read-only connection. Staffing
context/revision is checked; the expanded scope participates in the fingerprint.
Selected-Crew `assignments` still drives occupancy. Other-Crew staffing/visit
changes now invalidate snapshots; rebuild v1 inputs. No database migration.

`validate_snapshot_personnel(snapshot)` converts detached sources;
`PersistedRecommendations.personnel_validation` carries saved-Draft results.
It supplies no Satisfied PersonnelConflicts evidence to the PR91 comparator:
generated dates have no explicit proposed workers. They retain Pending resource
checks and false Apply/Publish flags. Draft save behavior, HTTP/UI and publication
are unchanged. Future #18/#29 must obtain proposed membership and complete safety
evidence, honor locks, and revalidate within Apply's transaction with rollback/audit.
See [design](design/2026-11-24-issue-15-personnel-checklist.md) and
[evidence](acceptance/2026-11-24-issue-15-personnel.md).

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
