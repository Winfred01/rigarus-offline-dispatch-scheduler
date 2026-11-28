# Issue19 — consolidated rule confirmation gate

**Decision delivery only. A/B/C/D below are proposals, not approved defaults.**
The current owner request explicitly requires confirmation before affected
product coding. Four questions were presented together once; no response has
been received at this record's creation. Silence, elapsed time, a sample schedule
or merging design PR138 does not approve these business rules.

## Design Compliance Checklist

Fresh fetched main `dbfa40b76198b3b8ae43bfd7920b74bab1c22328`; PR138 is human-
merged/closed. Issue19 remains Open. Its only current comment records planning,
not rule confirmation. No open product PR returned by the fresh search.
Reuse the clean isolated `codex/issue-19-decision-gate` worktree/branch; preserve
unrelated root README/language/original files. Repository PUBLIC; upload only
sanitized Markdown. Never inspect, rewrite, replay or archive130's refused D10
request/pending/receipt as part of this task.

Refreshed AGENTS/template,00/09/02/03/05/10 and
[merged19 plan](2026-11-28-issue-19-replanning-plan.md), with focus on current
scope, impact, day generation, schema20 transaction/schema21 recovery, acceptance
and confirmed-versus-proposed rules. Full source Git revision/hash/UTCmtime/read
inventory stays local; checkout modification times are not business authority.
00/10/19 plan last changed at `2d6b80a`;09/02/03/05 at `1bf8341`;
AGENTS at `880c79b`, template at `d3b9bea`. These are source revisions before
this proposed documentation edit, not assertions of new implementation.

This session changes no UI. The earlier plan's November24 L05/L08/L12/L13 image
review remains a separately dated reference; it is not claimed as a fresh image
inspection here. Reopen the corresponding originals before future UI work.

| Code/test inspected | Current fact / reuse boundary |
| --- | --- |
| `impact_preview.py:project_impact/read_impact` | Exact one-WorkItem replacement, detached scenario, downstream_complete=false and Unsupported locks/dependencies; no chain movement |
| `day_recommendation_generator.py` | Immutable whole-date requests/calendars/occupancy, positive confirmed remaining, existing bounded cumulative allocation |
| `recommendation_comparison.py:_rank_evaluated/compare_day_options` | Hard-filter known Blocked; existing stable finish/start, Crew ID and option ID ordering; supplied evidence never certifies dispatch |
| `draft_apply.py:prepare_in/submit` | One reserved exact-plan transaction/version/receipt for current single-WorkItem request; no chain-level atomicity by repeated calls |
| `draft_restore.py` and schema21 model | Exact original version, typed inverse, immutable audit/recovery receipts; unchanged and outside this slice |
| Existing impact/generator/comparison/Apply/Restore tests | Baseline test definitions reviewed, not new19 tests executed or proof of propagation |

## Four proposed decisions — one owner response, per-group status

Existing confirmations reused without another vote: new scheduling uses full
local days, preserves typed FullDay/Legacy identities and raw old occupancy;
Remaining Days must be explicit, not inferred from estimates/history; previews
stay read-only/Pending with no automatic publication; use the existing dual
sorts without new scoring weights. The new semantics below still need confirmation.

| Group | Concrete proposed first-engine scope | Status / affected work |
| --- | --- | --- |
| A Dependency | WorkItem nodes, explicit same/cross-Crew and cross-Project edges within one database; no adjacency/shared-Project/type inference. Only Finish-to-Start; nonnegative **calendar-day** lag: successor earliest local date = upstream final allocated work date +1+lag, then its own calendar/constraints. Reject cycles/missing references. Future single local operator explicitly maintains edges with change history; current core receives explicit facts only. Project changes enumerate selected WorkItems with individually confirmed remaining values, no automatic total-duration split. | Awaiting owner confirmation; dependency dates/propagation BLOCKED |
| B Locks | Start lock fixes the explicitly confirmed start date; Crew lock fixes the explicitly confirmed Crew; full lock fixes the whole reviewed date set/Crew/staff/Rig/notes/status with no add/cancel/edit. Locks combine, full lock most restrictive. Missing evidence/baseline is Needs Review, not Unlocked. No override/automatic unlock in this core; future explicit lock edits need reason/confirmation/append audit and separate implementation. | Awaiting owner confirmation; lock behavior BLOCKED |
| C Delay / earlier suggestion | Positive remaining5→8 or5→2 may propose dependent dates, including earlier successors only within explicit earliest-start floors, confirmed relations/locks and resource/calendar constraints. Missing evidence stays Pending/Needs Review, not verified feasible. Operator may choose none. No saved movement;5→2 is changed remaining work, not inferred actual completion. Existing earliest-finish/start order retained. | Awaiting owner confirmation of earlier-candidate conditions; changed-duration propagation BLOCKED |
| D Zero / completion | Recommended boundary: exclude zero/completion management this round; current positive ConfirmedRemainingDays remains unchanged. Zero requires a separate completion workflow, does not free saved capacity; Paused is not Completed. Completion authority, actual completion date/evidence, release and second confirmation stay Open for that later contract. | Awaiting owner confirmation of exclusion; no completion capability authorized |

Owner may change or reject any group. Working-day lag requires an explicit
calendar choice and counting convention; it is not silently substituted for
calendar-day lag. Start-lock without a confirmed baseline and a multi-Crew
WorkItem without supported scope cannot be treated as ordinary unlocked input.
No proposal here authorizes dependency editing, lock editing, completion writes,
chain Apply, production Restore/Apply/Publish or legal/customer sign-off.

## Implementation Plan — permitted independent work and future core boundary

Until sufficient decisions arrive: inspect existing contracts, record exact
choices/questions, update Issue19/matrix, verify document links/privacy and report
CI honestly. **Do not create `replanning.py` or business-rule tests that implement
an unanswered proposal.** No SQLite migration, initialization, test database or
runtime flag change is needed for this decision delivery.

Once necessary answers are explicit, first commit the actual decision source,
scope and updated Design-First plan, preserving older Proposed history. Then one
small pure-core PR can propose immutable versioned inputs: WorkItem/Project/crew
identity, saved typed dates/revisions, explicit confirmed positive remaining,
complete/unknown dependency coverage and edges, explicit lock evidence/baselines,
earliest start/horizon and detached independent calendar/resource evidence.
Do not replace complete context-bound validator observations with arbitrary
Passed booleans. Existing sources include actual workers/availability, drivers,
levels/separate qualifications, Rig conditions/occupancy and actual-worker weekend
consent; retained legacy halves remain occupied. Reuse generation/comparison and
resource validators, not a second eligibility algorithm.

Future proposed output: affected typed WorkItems, exact Before/Proposed dates,
edge/lag/lock reasons, per-resource warnings, skipped dates, incomplete coverage,
input/proposal fingerprints and false Apply/Publish flags. A pure function can
bind supplied input/revision fingerprints; it cannot claim a live SQLite Current
check without an independently re-observed source comparison. No I/O, wall-clock
dependency, SQL writes, new HTTP/Tauri commands or desktop UI in that first core.
Review graph-wide date/resource collision handling and bounded node/edge/work/
response budgets before implementation; reaching a bound never means complete.

Keep chain-wide transaction/audit/idempotency/recovery, dependency persistence,
desktop comparison/selection, pause/completion management and export in later
separately reviewed slices. Never invoke single-WorkItem Apply repeatedly and
describe the result as atomic. Production gates and all historical data remain
unchanged. No original DOCX/images/DBs/backups/raw diagnostics uploaded.

## Illustrative expectations, not execution results

After A/B/C decisions, synthetic A→B→C with explicit working dates/resources can
demonstrate positive5→8 later candidates or5→2 earlier candidates. A locked B
must obey the selected lock semantics and expose incompatibility. Date-adjacent
A/B without complete explicit dependency evidence cannot create an edge.
No concrete new candidate dates, eligibility passes or lock passes are claimed
before the model is approved and actually run. Existing single-WorkItem5→8/5→2
tests explicitly return Unsupported Dependency and are not chain acceptance.

Product C01–C10 are BLOCKED by the unresolved new-rule gate. Future UI/write/
accessibility C11–C16 remain NOT RUN. C17 new product regression/build acceptance
is NOT RUN because no product was implemented; document-only checks and current
CI are reported separately. C18 remains BLOCKED by missing qualified disconnected
VM evidence; customer UAT/production approval remains absent. No old test count
or CI success is borrowed to mark these cases passed.

## Delivery validation

Required for these text edits: strict UTF8/fences/relative links, diff whitespace
and staged privacy. Product unit/integration/native/Release/NSIS execution is not
applicable to validating a decision-only Markdown delivery. Run state, exact
commit and documentation-head CI link belong in the Draft PR; a running job is
not PASS. Issue19 remains Open, Draft PR waits for human review, no automatic
merge, Issue closure, Release, deployment or production operation.
