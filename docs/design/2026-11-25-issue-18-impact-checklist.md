# Issue18 — read-only full-day impact preview

## Design Compliance Checklist (before product edits)

Owner November25 continuation: read-only Before/After, then separately safe human
Apply, recoverable versions, downstream replanning and formal exports. One slice,
one Draft PR; no merge, Release, Issue closure or production writer opening.

Fetched main8f6e547d62c772d56d277d3e4a645a9aca272910 includes human-merged122
(head675d090). Public repository, no Open PR observed. Main Windows CI45757807364
was in progress at discovery; product edits wait for successful main build.
Original checkout README/untracked guide/design sources are preserved. Isolated
codex/issue-18-impact-preview worktree. Issues18/19/20/29/99/120 read again, all
Open. M3 milestone4 covers impact/timeline; labels are not customer acceptance.

All required sources exist/readable in the isolated checkout. Checkout modification
times November26 04:53:24 UTC (November25 Toronto), not business authority:

| Source | Last-changing revision | Sections read / authority |
| --- | --- | --- |
| AGENTS and DEV-DESIGN-CHECKLIST | d3b9bea | Mandatory Design-First, offline/privacy/human gates |
| 00-PROJECT-PLAN | 96c3114 | Scope, current owner priority, milestones, day rule |
| 09-DELIVERY-PLAYBOOK | 96c3114 | Current delivery, engineering/demo/production gates |
| 02-ARCHITECTURE | 675d090 | Editor19, weekly workbench, recommendation v6, resource proposals |
| 03-DATA-MODEL | 96c3114 | Schemas13–19, current/legacy history and receipts |
| 05-DEMO-ACCEPTANCE | 7604d2a | Daily resources/calendars/generation and no-write checks |
| 10-CLIENT-DECISIONS | 675d090 | Confirmed owner read-only dependency/day rules, Open policies |
| Previous impact contract / editor review and acceptance | 675d090 | Exact scope, future transaction contract, VM/recovery limits |

Local November24 UI DOCX SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c
was rechecked. L11–L14 paragraphs60–79, L20 paragraphs105–109 read; original
images64/65/66/72 viewed (concepts, not current screenshots; no verified page
numbers). L13 dual sort/diagnostics, L14 detail/locks, L20 explicit people inform
the added component. New Full Day/read-only owner rules override old halves,
Apply/Validated captions. No original/real data will enter the public repository.

| Requirement | Existing / change | Acceptance |
| --- | --- | --- |
| Confirmed positive days, dual sort, calendar gaps | Reuse daily query/generator/PR91 comparison | 5→8,5→2, gaps, strict input |
| Exact replacement scope | Missing; typed FullDayDraft IDs+expected revisions, explicit checkboxes | No implicit release, wrong kind/id/revision rejects |
| Read-only Before/After | Missing; one pinned query-only source plus detached scenario | Full logical dump equality, concurrent coherent read |
| Existing resource rules | Reuse saved and candidate people/driver/capability/Rig/consent checks | Missing Pending, known blockers Blocked, both-Crew observations |
| Freshness | Extend source fingerprint with UUID, exact scope and complete target index | Notes/legacy/calendar/UUID/query/revision changes Stale |
| Locks/dependencies | No persisted authoritative model | Not recorded / Unsupported Dependency, never no-impact |
| UI | Existing recommendation Dialog/form/style | Loading/Empty/Invalid/Blocked/Pending/Stale/Error, Cancel/Escape/focus |
| Future Apply | Existing design only | Reserved identity/revision/audit contract; no write route/button |

Confirmed: day unit, explicit duration, no default workers/Rig, Pending/false gates,
no automatic conversion/progress deduction. Open: customer lock/dependency policy,
approval authority/Foreman/category/legal meaning/historical reconciliation.
Before Remaining Days is Not recorded: no persisted confirmed-day field exists.
Scope is explicitly bounded to chosen horizon; count/display target records outside
it, never imply whole-history or downstream coverage. Different saved Crews remain
visible. Releasing chosen saved visits in memory never transfers their workers or
dated Rig/consent approvals into the proposed plan.

## Implementation Plan

1. Commit this checklist before product edits. Verify merged-main CI passes.
2. Add independent day_impact_preview domain/read service and strict API routes.
   Reuse connection-level snapshot sources inside one mode=ro/query-only transaction,
   schema19 lineage UUID, 100k-unit/64MiB/30second budgets. Read target index and exact
   scope/revisions in that transaction; incompatible/missing data fail explicitly.
3. Detached scenario removes only explicit day records and corresponding saved Rig
   claims; never remove legacy/unselected visits. Run existing generation and complete
   candidate-resource chain. Proposed people/Rig absent stays Pending; no inheritance.
   Return whitelisted Saved facts/resource reasons, Proposed alternatives/skip reasons,
   protected related records, missing dependency/lock coverage, exact revision vector,
   deterministic source/proposal SHA256. Current is an observation, not reservation.
4. Extend fixed authenticated Rust recommendation command with only two impact paths.
   Add Preview Impact within existing WorkItem Auto-Recommend form; explicit scope
   checkboxes, Before/After comparison, affected IDs and detailed validation. Preserve
   existing dates-only mode/weekly Locate. Reuse Dialog keyboard/Escape/focus return;
   response epochs and sticky Stale prevent old/late results reappearing. No new deps.
5. No schema/migration, SQLite write, confirmation persistence, locks, Apply, Publish,
   B/C shifting or schedule restore. Reserve future Apply contract in existing design.
6. Add synthetic API/scenario/freshness/concurrency/failure/limit/no-write regressions
   and UI state tests. Run locked full backend/sidecar/frontend/Rust/.NET, Windows
   builds, format/privacy/docs and exact-head Windows CI. Inspect rendered UI with
   synthetic data; report native and browser checks separately.
7. Update architecture/model/acceptance/decisions and guide entry, one Draft PR linked
   Issue18/29; synchronize actual results. Qualified offline VM unavailable per owner:
   installation/upgrade/reboot BLOCKED, never substituted by CI/activated host.

## Actual acceptance (initial)

All new product checks NOT RUN until executed. Main CI pending at plan creation.
Native/offline/customer acceptance separate; production daily writes remain closed.

## Execution update — November26

Main CI45757807364 completed success/all3 jobs before the first product edit.
No design-policy deviation: no new schema, writer, automatic transfer or chain.
The new bounded scenario uses the complete existing resource-validation chain.
Root results stay Pending even if some independent subchecks are Satisfied.

Native connected-host comparison inspected against L13/image65: existing Dialog,
blue/neutral controls, inherited borders/fonts and table vocabulary retained.
Full Day, exact typed replacement scope, explicit Pending resources and unsupported
locks/dependencies intentionally replace prototype half-days/Validated/Apply.
Original drawings remain local. Actual native5→8/protected B, Escape/focus/reopen
and SQLite equality were executed; narrower sizes/native faults/offline VM were
not. See [execution evidence](../acceptance/2026-11-26-issue-18-impact.md).
