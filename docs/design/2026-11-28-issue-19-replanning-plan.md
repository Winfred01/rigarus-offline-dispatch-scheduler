# Issue19 — downstream replanning Design Compliance Checklist and Implementation Plan

**Design only. No product implementation or new business-rule approval.**
Owner's November28 continuation starts planning while bounded130 qualification
continues. Do not repeat normal Restore or treat all native fault checks as passed.

## Baseline, sources and authority

- Fresh fetched main `739bfecdc67f0142305f45454392d5f6d629500f`, human-merged137.
  PR137 final-head CI46111158850 passed3/3. Merge-main CI46112092717 was still
  running at inspection; its result must be reported separately, not assumed green.
- Independent branch `codex/issue-19-replanning-design`; preserve unrelated root
  README/language/original files and all earlier smoke roots. Repository PUBLIC:
  only sanitized Markdown, no original DOCX/images/logs/SQLite/journals/backups.
- Fresh open Issues19/18/20/21/28/29/130 inspected. No open PR was returned by the
  fresh repository open-PR search;137 is closed/merged, not reopened or extended.
  Issue bodies retain historical Planned/unmerged/half-day statements. Code and
  current owner decisions supersede stale implementation descriptions.
- Reread AGENTS/template and six source documents' current scope, delivery,
  impact/transaction/schema/acceptance/authorization/decision sections. Architecture,
  data-model and acceptance history is not a claim that every old module was reread.
  Source inventory records exact Git revision, SHA256, checkout UTCmtime and read
  time locally. UTCmtime reflects checkout, not rule authority.

| Source | Last-changing Git revision | Relevant sections actually inspected |
| --- | --- | --- |
| AGENTS.md | `880c79b64f058d3f68dd164c84a337e22113392f` | Design-First, staged privacy, A/B/C and no-repeat refusal rules |
| DEV-DESIGN-CHECKLIST.md | `d3b9bea778529c47bb502e59914cbdd0100697a0` | Source identity, authority, UI mapping, plan and actual acceptance |
| 00-PROJECT-PLAN.md | `1bf8341e267969e88fe272e601cc0a5d8777d87c` | Full local days, Option C, dependency order,19/20/29 before exports |
| 09-DELIVERY-PLAYBOOK.md | `1bf8341e267969e88fe272e601cc0a5d8777d87c` | Impact/Apply/Restore boundaries, native/offline separation and delivery gates |
| 02-ARCHITECTURE.md | `1bf8341e267969e88fe272e601cc0a5d8777d87c` | Read-only Before/After impact; schema20 transaction; schema21/native recovery |
| 03-DATA-MODEL.md | `1bf8341e267969e88fe272e601cc0a5d8777d87c` | Read-only impact; immutable DraftVersions/RestoreVersions/receipts; typed identities |
| 05-DEMO-ACCEPTANCE.md | `1bf8341e267969e88fe272e601cc0a5d8777d87c` | Read-only full-day impact and separate124/126/130 engineering checks |
| 10-CLIENT-DECISIONS.md | `880c79b64f058d3f68dd164c84a337e22113392f` | Full Day, exact reviewed Draft, pending/blocked, early-completion Proposed and present planning-only direction |

UI original: accessible local-only `Rigarus_UI_Design_Updated_2026-11-24.docx`,
SHA256 `d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`,
mtime2026-11-24T23:15:38.711423Z; re-extracted/read November28 UTC.
Viewed original image57/L05(paragraphs29–33), image60/L08(44–48),
image64/L12(64–68), image65/L13(69–73). These are paragraph/figure locators,
not verified page numbers. Figures are concepts, not implemented product evidence.
L11 text was read, but its image63 was not viewed or used as a layout claim.

L05 informs long-window visibility; L08 links delay/leave/maintenance impacts to
review; L12 informs comparison/partial coverage; L13 supplies explicit candidate
choice and earliest-finish/start sorting. Prototype half-day counts, published
controls, batch Apply and automatic dependency labels do not authorize present
half-day editing, publication or unconfirmed rules. No original is uploaded.

## Current implementation audit

| Requirement | Authority / present implementation | Preserve or missing work |
| --- | --- | --- |
| Operator-controlled explainable proposals | Confirmed planning direction;19/29 and00 Option C | Never silently move B/C; operator can choose none |
| Whole local days with old halves intact | Confirmed99; existing day generator/mixed workbench | Use record_kind+id; old AM/PM occupancy remains protected, no merge/conversion |
| Saved/proposed exact scope | Existing `impact_preview.py:project_impact`; `impact-preview.tsx` | Only selected FullDay records of one exact WorkItem are released in memory; protected records stay |
| Remaining work | Existing independent positive ConfirmedRemainingDays; saved Before Not recorded | No estimate/history deduction; completion/zero is a separate unresolved contract |
| Downstream scope | Missing authoritative graph; current downstream_complete=false | Same Crew/date order/shared Project is not dependency or proof of no impact |
| Locks | Existing lock_status=Not recorded/Unsupported | Need approved semantics and explicit source/revisions; absence is not Unlocked |
| Personnel/driver/capability/Rig/consent | Existing daily snapshot and independent validator chain | Recheck all affected source/target Crews/dates; Available never certifies dispatch |
| Exact atomic unconfirmed Draft | Existing `draft_apply.py:prepare_in/submit`; schema20 | Current request is one WorkItem; cannot make a chain atomic by repeatedly calling it |
| Version/recovery | Existing schema21 Restore and native operation journals | Reuse patterns, not new multi-WorkItem writer permission or old receipt reinterpretation |
| Native qualification |137 new variant/mixed evidence;130 residual composite gaps | Retain exact artifact scopes, refused D10 pending and qualified-VM BLOCKED |

The [earlier impact contract](2026-11-25-impact-preview-contract.md) includes
historical schema19/missing-Apply statements. Current schema21 already supplies
Draft audit/restore; do not rebuild them. It still lacks an approved dependency/
lock/confirmed-progress model and a chain-wide transaction contract. Existing
resource-generated dates can avoid protected B; that is not propagation of B.

## Implementation Plan — proposed independently reviewed slices

### 1. Explicit chain/lock/progress contract before affected code

Obtain decisions for WorkItem versus Project trigger scope, operator-specified
same-Crew order, cross-Crew edge types/lag and cycles, fixed successor semantics,
each lock and manual exception, and early-finish/zero/completion provenance.
Do not infer Civil→Tower edges from type or shared Project. Project-level change
must enumerate affected WorkItems instead of silently changing every sibling.
Keep missing evidence Unknown/Unsupported and old early-start suggestion Proposed.

After confirmed semantics, specify a pure versioned input DTO with explicit typed
nodes, relations, lock observations, confirmed remaining values and independent
calendar/resource snapshot. First isolated model/tests can use explicitly supplied
synthetic facts; they do not establish a persisted customer policy. No production
defaults, weekend approval, resource eligibility or estimate conversion is seeded.
Suggested future files: `replanning.py`, `tests/test_replanning.py`; names and
policy are proposals, not current implementation.

### 2. Read-only bounded downstream candidate calculation

Reuse generator/dual comparator/resource validation rather than a second safety
engine. Given explicit approved order/edges, compute the reachable affected set;
detect cycles, missing references, incomplete closure and horizon overflow.
Return no complete chain claim or partial Current fingerprint on source failure.
Keep read/deadline/unit/response bounds explicit; do not silently grow existing
single-WorkItem limits to accommodate a chain.

Candidate releases exactly reviewed FullDay IDs/revisions in a detached scenario.
Everything else, including old halves, fixed successors and stale Rig claims,
remains protected. Re-evaluate all affected employees, driver/skills/qualifications,
Rig occupancy/conditions and real weekend consent; no historical positive evidence
is copied to new dates. Unknown capacity cannot supply a finish date. Preserve
effort across calendar gaps and interrupt/resume; pause/completion state writes
remain separate21 scope.

Show a small deterministic set ordered by the existing earliest-finish/start
policy; don't add a new priority, continuity score, tie rule or packing heuristic
without review. Both A5→8 shifting an explicitly movable B/C and A5→2 offering
earlier B/C must explain exact edge/resource causes. A fixed B is protected; if
it cannot be met, explain the conflict instead of moving it or pretending success.
An optional earlier-start suggestion never automatically changes B.

Suggested extension points: `impact_preview.py` and a separate chain adapter/API
module/tests after review. Use one coherent query-only SQLite view, schema/lineage,
all typed revisions and edge/lock/evidence fingerprints. New source storage needs
a separately reviewed minimal additive migration with verified SQLite backup,
failure rollback/retry/reopen/old-binary recovery evidence. Do not assign a future
schema number or create tables in this planning PR.

### 3. Explicit comparison and selection in the existing desktop workflow

Extend existing impact/state and fixed Tauri/FastAPI routes after their contracts
are reviewed. UI names/files are planned: `impact-preview.tsx`, `impact-state.ts`,
existing recommendation command and weekly typed Locate. No large new calendar.
Review original L08/L12/L13 again before layout work.

Show original/current/proposed per WorkItem and Crew, dates, notes, staff/Rig
provenance, moved/cancelled/protected records, dependencies/locks, reasons and
coverage totals. Distinguish truly unscheduled from read failure, unknown remaining,
incomplete horizon and no feasible option. Loading clears stale identity; input/
scope/order changes invalidate reviews, late responses cannot revive them.
Stale requires recomputation; Blocked cannot be overridden. Cancel/X/Escape before
dispatch preserves all SQL/history/receipts and returns focus; narrow lists scroll
internally with full labels, keyboard focus and Narrator status verification.
Selecting a candidate stays read-only; no Apply/Publish becomes available just
because a preview is Current.

### 4. Separately approved chain-wide unconfirmed Draft transaction

Only after the reviewed model/preview: reserve one BEGIN IMMEDIATE, reread all
lineage/revisions/graph/locks/resources, recompute exactly the reviewed plan and
atomically append every selected WorkItem's changes/history, one batch audit/
version and reliable idempotent receipt. Never loop current one-WorkItem submits
and call partial commits atomic. Preserve matching IDs, cancel by appended history
and never rewrite old versions/legacy records. Review multi-WorkItem version and
Restore compatibility explicitly; single-version Restore must not gain implicit
new scope merely because an audit format is extended.

If an approved unconfirmed-Draft path permits Pending, list and acknowledge each
exact warning; never change it to Passed. Known hard conflicts reject the entire
batch. Separate operation namespace/guard, durable pre-dispatch request, exact
receipt verification/archive and Unknown/original-key resolution are required;
do not copy another operation's pending or change keys after uncertain writes.
Committed plus failed display refresh retries reads only. Production writers and
Publish remain closed pending a separate explicit authorization and qualification.

## Proposed acceptance matrix — execution NOT RUN

These are future19 cases, not borrowed130 Restore passes or a customer Demo.

| Case | Synthetic scenario / expected result | Actual |
| --- | --- | --- |
| C01 | Confirmed A5→8 plus explicit movable B→C; exact before/after/reasons, conserved work | NOT RUN |
| C02 | A5→2 offers earlier B/C; choose none leaves all saved dates unchanged | NOT RUN |
| C03 | Fixed B or each independent lock honored; incompatible chain explains conflict | NOT RUN |
| C04 | Same Crew/date order without an authoritative relation remains Unsupported | NOT RUN |
| C05 | Confirmed cross-Crew edge; cycle/missing edge/wrong parent and multi-Crew ambiguity fail closed | NOT RUN |
| C06 | Gaps/closures/unknown/weekend consent and leap/cross-year horizon; no invented finish | NOT RUN |
| C07 | Missing confirmed remaining/estimate/zero-completion distinction; preserve long remaining work | NOT RUN |
| C08 | Crew, employee, driver, qualification, Rig/maintenance and legacy-half conflicts; source+target rechecks | NOT RUN |
| C09 | Same integer FullDay/Legacy IDs, original notes/staff/Rig/history and unrelated projects preserved | NOT RUN |
| C10 | Repeated same inputs/sort deterministic; scope/order/graph/lock/resource edits make Stale | NOT RUN |
| C11 | Cancel/X/Escape/late response and comparison selection: coherent all-table no-write equality | NOT RUN |
| C12 | Missing/malformed/timeout/oversized sources; no partial safe/Current result or unbounded work | NOT RUN |
| C13 | Future exact human batch confirm, Pending acknowledgements, blocker/stale refusal | NOT RUN |
| C14 | Future mid-batch SQL/audit failure rolls everything back; one original key/receipt across reopen | NOT RUN |
| C15 | Future same-key changed payload refusal, concurrent writer and commit/refresh read-only retry | NOT RUN |
| C16 | Narrow window/full keyboard/Narrator, mixed boards/Locate; no unseen confirmation | NOT RUN |
| C17 | Applicable locked full regression, Windows build/CI, migration compatibility/privacy | NOT RUN for product |
| C18 | Qualified licensed disconnected install/upgrade/WebView2/OS restart, customer sign-off separately | BLOCKED: VM absent; no customer/production approval |

This delivery changes only planning Markdown, no API/schema/UI/runtime/test code
or database. Product builds/native cases are not applicable to validating these
text edits, and no historical858 tests are presented as19 implementation evidence.
Run strict UTF8/fences/relative links, diff whitespace and staged privacy locally;
report documentation-head CI truthfully in its Draft PR. No merge/Issue closure/
Release, customer file upload or production access.

## Independent130 qualification backlog

1. Bounded native malformed/mismatched receipts, process contention and journal
   isolation; archive/flush faults, sealed Rejected and failed-refresh composite
   subcases, each on identified synthetic artifacts with coherent SQL comparison.
2. Narrow window, full keyboard and Narrator. Licensed offline VM tests only when
   a valid environment exists; no host/CI/NSIS substitute or licensing bypass.
3. Preserve specifically blocked D10 wire request/pending/receipt/archive as-is;
   no repeated approval loop or alternate API/channel. A/B authorization remains
   subordinate to actual platform gates. This planning session performs no native
   Restore, Resolve, Replay, Archive or fault operation and claims no new130 pass.

Engineering review of this plan does not accept Demo C, UAT or software delivery.
Next product slice requires confirmed affected business semantics and a fresh
healthy-main/source audit; formal company/Crew/employee PDF/Excel remains a later
independent mixed-type and immutable-publication contract.
