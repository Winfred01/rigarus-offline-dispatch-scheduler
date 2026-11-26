# Full-day Before/After impact preview — design only

Status: **BLOCKED for product implementation while PR122 is unmerged**.
Owner request November25; dependencies18/19/20/29/99/120. This document implements
no endpoint, button, allocator, lock, Apply or schedule-version restoration.
PR122 remains the only product PR in this review. Recheck human merge/current
main build before the next independently reviewed slice.

## Current implementation and gaps

Merged118 supplies WorkItem Auto-Recommend, whole-day accumulation/dual sort,
read-only coherent snapshot and scoped freshness. Merged121 supplies daily/legacy
weekly boards, actual saved resource reasons and typed Locate. Unmerged122 adds
manual Draft editing, database-lineage UUID and immutable exact-request receipts.
Keep those contracts; do not copy/refactor the unmerged editor into a new feature.

Schema19 has no persisted Confirmed Remaining Days, schedule-wide revision,
lock state, dependency graph, proposal audit or immutable Published schedule
version model. WorkItems.EstimatedHalfDays remains unconfirmed legacy metadata.
Receipt/history data is not a recoverable schedule version or Apply authority.
Absent sources must be Pending/Unsupported, not invented None/Unlocked/Passed.

## Proposed read-only slice

Input (strict, bounded, no estimate conversion):

- WorkItem and expected parent Project; explicit positive Confirmed Remaining Days
  plus operator confirmation; candidate Crew IDs, earliest local start, horizon
  ending within existing12-month boundary, EarliestFinish/EarliestStart.
- Exact replacement scope: typed FullDayDraft IDs and expected revisions, explicitly
  selected by operator. Omitted scope means new-work alternative, never implicit
  deletion of every saved visit for that WorkItem. Retain raw LegacyHalfDay
  occupancy; no conversion/merging or automatic old-record replacement.
- Explicit proposed per-date people/Rig evidence and source-Crew roster overrides
  only where existing validators support them. Missing proposal roster/resources
  stays Pending. Do not infer people, original/actual vehicle or approvals.
- Supported real lock/dependency observations only. Currently unavailable: show
  Not recorded/Unsupported Dependency and keep full validation Pending.

One bounded mode=ro/query-only SQLite transaction pins schema, workspace UUID,
WorkItem/parent/master data, exact saved scope, all relevant day/legacy visits,
current workers, calendars, availability, resource evidence and native revisions.
Use connection-level existing helpers and shared100k units/64MiB/30second budget;
no public Store composition with independent transactions. Snapshot readers
never initialize/migrate, write receipts, create proposals or save confirmation.
Failures/timeouts return error, never an empty Current/safe result.

Build a detached typed scenario. Release only explicitly selected replacement
visits in that scenario, retain every unrelated active visit/legacy occupation;
no live cancellation or employee transfer. Run the existing generator against
scenario capacity, then reuse exact proposed people/driver/capability/Rig/consent
checks, source and target after borrowing, plus full-date employee availability
and Crew/parent-Project calendars. Calendar/one subcheck Satisfied never makes the
overall proposal safe. Unknown contexts/partial legacy positives remain Pending;
known negative resources remain Blocked. No safety algorithm duplication.

Before/After DTO:

| Field | Before provenance | After provenance |
| --- | --- | --- |
| WorkItem / Project / Crew | Exact saved typed records and revisions; multiple Crews shown separately | Proposed IDs; unresolved multi-Crew scope Needs Review |
| Start / Finish | Min/max of observed active saved dates, labelled saved planned span, not actual progress | Allocated dates and gap reasons; no finish if incomplete |
| Remaining Days | Not recorded unless a real persisted confirmation exists; optional operator baseline clearly labelled session input | Explicit newly confirmed query value, Proposed, not saved |
| Employees / Rig | Explicit saved members and actual dated allocation, retaining stale/legacy provenance | Explicit proposed values or Pending; never HomeCrew/default Rig |
| Resource conflicts | Existing saved checks with exact resource/date/source | Proposed/scenario checks plus both-Crew effects and skipped/protected conflicts |
| Downstream impact | Related saved work with observed dates | Known affected/protected records; Unsupported Dependency where chain cannot be computed |
| Locks | Real supported source or Not recorded/Unsupported | Preserve real locks; unsupported lock coverage cannot claim a pass |

State axes remain independent: Saved/Proposed provenance, Blocked/Pending subcheck
state, Current/Stale freshness, and overall Validation Pending. Display IDs/date/
source/reasons, not only red icons. Do not label Saved as safe or Current as Applyable.
If details are bounded/paged show totals/coverage explicitly; never silently omit
conflicts and imply completeness.

There is no authoritative dependency graph. Same-Crew date order is not proof of
a dependency or of no dependency. List known affected occupancy, retain B/C,
and show Needs Review / Unsupported Dependency for complete downstream coverage.
Do not automatically move a fixed successor, release its resources or return
"no downstream impact" from absent dependency data.

## Concrete proposed examples (not executed feature evidence)

Synthetic A has five saved full-day visits November23–27,2026. The operator
explicitly confirms baseline5 and proposed8 days and selects only A's five typed
records as the replacement scope. Before Remaining5 is labelled session-confirmed,
not fabricated database state. Crew/Project explicitly Working on weekdays.

- Without another saved occupation,8 dates span November23–December2, skipping
  unapproved November28–29; saved A remains unchanged.
- If B occupies November30 on the same Crew, retain B. Existing generator skips
  that protected date, so A's8 dates finish December3. Explain B's saved identity/
  skip reason; downstream chain remains Unsupported. A manual alternative that
  explicitly overlaps B is Blocked, not silently shifted.
- Proposed2 days spans November23–24; remaining A dates are only proposed releases.
  B/C do not move automatically. Actual completed work is not inferred.
- Missing calendars/resources/remaining confirmation keeps Pending/Needs Review.
  No scenario creates a trusted completion date from old half-day estimates.

## UI and cancellation contract

Future entry: Preview Impact from the actual WorkItem/Auto-Recommend flow, retaining
existing visual variables/buttons/borders. No new navigation system or fake Apply.
Original L12/L13 comparison and L14/L20 detail/actual-workers concepts inform the
layout; latest Full Day/read-only gates override prototype halves/Apply/Validated.
Use a Before/After table, affected Crew/WorkItem list, allocation/skipped dates,
per-resource reasons, coverage and explicit Pending/Saved/Proposed labels.

Loading clears old identity data; Empty distinguishes no plan from read error;
Invalid retains input; Blocked/Pending explains exact missing or conflicting
date/person/Rig; Stale visibly retires the old result, requiring recompute; Error
cannot show Current. Separate response epochs prevent late preview/freshness from
overwriting a newer selection. Switching options is read-only; Cancel/Escape
invalidate pending responses and close without SQLite changes, then restore focus
to the trigger. Keep typed Locate/week/focus/two-second/reduced-motion behavior.

Detect edits through explicit source-freshness recheck on relevant reload/focus/
interaction; this is not instantaneous protection after a read transaction ends.
Keep the old proposal Stale until recomputation, even if input fields revert.
Apply/Publish remain false; unavailable actions have explanatory text.

## Reserved future Apply contract (not exposed in this slice)

| Field | Reuse / unresolved requirement |
| --- | --- |
| Proposal ID / fingerprint | Deterministic SHA256 of versioned exact before/scenario/after/coverage/sort; not an authorization token |
| Base database identity | Reuse schema19 workspace UUID as lineage identity plus existing source scope; clones/restores need explicit recovery policy |
| Base revision | Exact typed per-record revision vector + native evidence revisions/source fingerprint; no invented global counter |
| Exact before/after | Canonical typed records/status/membership/actual Rig; no ambiguous same integer ID or implicit visit set |
| Affected scope | WorkItem/Project/Crew/resource IDs and complete/unsupported coverage |
| Lock state | Real persisted revisions/semantics; absence cannot be a guessed unlocked flag |
| Resource summary | Existing independent checks + input/source provenance, known blockers, missing evidence and complete coverage |
| Freshness | Same-query/scenario proof; transaction must reread and revalidate all needed sources |
| Operator intent | Explicit reviewed exact proposal confirmation, never inferred from opening/selecting it |
| Idempotency | Reuse exact-payload/key/immutable-receipt pattern, separately namespaced for future Apply |
| Audit/version | New transaction audit reference and recoverable schedule-version design required; Draft receipt is not this audit |

Future Apply to Draft reserves one SQLite write transaction, verifies schema/
lineage/revisions/locks/exact scope and complete current resource evidence, then
mutates exactly the reviewed records with audit/version links and idempotent
receipt atomically. Any conflict/stale/incomplete evidence or storage/audit failure
rejects/rolls back everything. No override bypasses hard rules. Publish remains a
separate validated immutable-snapshot/operator gate. Restoring a prior schedule
version requires an independent approved conflict/revalidation policy; never
delete history or restore an old database file as "schedule undo".

## Next slice acceptance plan (NOT RUN while dependency is unmerged)

Pure/integration/UI cases:5→8/5→2 explicit baseline versus missing Before value;
Crew conflict; old half/full-day overlap and equal integer namespaces; driver,
member/qualification shortage; Rig maintenance/collision; weekend Pending/Declined;
both-Crew borrowing; unsupported dependencies/locks; Current→Stale/reverted input;
open/switch/Cancel/Escape/reopen with full SQLite logical equality; read failures/
late responses; bounded large inputs/timeouts; no fake finish or Apply/Publish.
Run full locked Python/packaged/frontend/Rust/.NET/Windows build/privacy/CI and
qualified native/VM acceptance. No legal Windows VM means offline install/upgrade/
restart remains BLOCKED; connected-host or CI checks are not substitutes.
