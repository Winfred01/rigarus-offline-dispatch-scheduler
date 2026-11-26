# PR122 recovery review and dependency gate

## Design Compliance Checklist

Owner November25 request: inspect PR122 first; do not implement dependent impact
preview until122 is human-merged and main builds. Fresh fetched main
9d40765a28703216f636802e7349a84dac3f7e84; main CI45706045706 PASS.
PR122 Open/Draft, head96c311421108c5fa4053710c08124532dff6e272,
CI133/45716246615 previously PASS. No submitted review found. Reuse isolated
codex/issue-120-day-editor worktree/PR; preserve root README/local design changes.
Issues18/19/20/29/99/120 remain Open; M2/M3/M5 are delivery labels, not acceptance.
Repository PUBLIC. No new product PR or dependency-editor copy.

Required sources reread November25 (UTC checkout metadata, not authority):

| Source | Revision | Modified UTC | Sections |
| --- | --- | --- | --- |
| AGENTS / DEV-DESIGN-CHECKLIST |d3b9bea | Existing checkout | Design-First, review, safety and source boundaries |
|00-PROJECT-PLAN |96c3114 |22:33:17.4444596 | Editor prerequisite, human Apply/version priority, offline scope |
|09-DELIVERY-PLAYBOOK |96c3114 |22:33:17.5794744 | Editor recovery/qualified VM and independent gates |
|02-ARCHITECTURE |96c3114 |22:35:09.1879794 | Schema19 transaction/receipts, client journal/deadline, workbench |
|03-DATA-MODEL |96c3114 |22:33:17.3045477 | Immutable workspace/receipts, additive backup/recovery |
|05-DEMO-ACCEPTANCE |7604d2a |21:44:58.3924649 | Daily safety and separate native/offline acceptance |
|10-CLIENT-DECISIONS |96c3114 |22:33:17.7131489 | Explicit Draft versus Apply, closed writes, no inferred policy |
| Issue120 design/acceptance |98f0a34/96c3114 | Current checkout |690 tests, candidate-specific native limits and expired VM |

Original local November24 DOCX SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c
reread XML L11–L14 paragraphs59–78 and L20 paragraphs104–108. Actually viewed
original image64/65/66/72 (batch preview, recommendation, details/locks, staffing).
These are concepts, not current implementation or verified page numbers.
Latest Full Day/no Apply owner rules override prototype halves/Apply/Validated.
This review changes no layout/control; no new UI screenshot comparison claimed.
Future impact design keeps current shell and explains unavailable locks/dependencies.

| Requirement | Review approach / authority |
| --- | --- |
| Confirmed user: unmerged122 prerequisite | Product impact slice BLOCKED; independent contract/design allowed |
| Exact request recovery, no false success | Check committed response matches complete original request; malformed result must preserve recovery evidence |
| Retain another pending operation | Old settlement must not delete a different current journal |
| Transaction/history/SQL guards | Audit write reservation/savepoint/receipt, run synthetic fault/migration/replay tests |
| Default closed writes | Test sidecar opt-in/default status, no gate change |
| Qualified offline installation | Host reports Windows11 Pro Licensed; existing VM evidence is expired Evaluation, not a qualified replacement |

## Implementation Plan — before fixes

1. Commit this review checklist/plan on original122 branch. Add adversarial
   regression cases reproducing incomplete/mismatched Committed receipt acceptance
   and settlement clearing a different pending journal before fixing them.
2. Harden only existing TypeScript recovery state: validate complete typed saved
   fields, exact action/ID/revision/payload/status/member match and false flags.
   Preserve journal on invalid response/read error or a different current request.
   Let the editor acknowledge once after transport returns; avoid clearing before
   its normal accept path. No schema/API/visual/new business constraint.
3. Existing single-window synthetic test scope does not prove atomic WebView
   localStorage coordination across app instances. Document multi-instance
   journal races as an unresolved production rollout gate; do not open writes.
4. Run focused/full frontend and existing backend/packaged/Rust/.NET/locked
   builds/privacy/docs; recheck old binary/backup recovery using fresh synthetic
   files. Native UI/offline VM conditions recorded separately, never borrow CI.
5. Add design-only impact contract: explicit Remaining Days; saved/proposed/
   pending provenance; one query-only view; conservative downstream Unsupported
   Dependency; exact scenario resource validation; scoped freshness; future
   transaction/locks/idempotency/audit/version interface. No endpoint/button/
   impact engine, Apply/Publish or schedule-version restore in this review.
6. Update original Draft PR122/Issue120 and relevant dependencies with findings,
   actual checks and missing acceptance. One existing PR only, no merge/Release/
   Issue closure/customer data. Initial new results NOT RUN.

## Review execution

Confirmed minimal/mismatched success and changed-journal settlement defects with
four pre-fix failing cases; fixed exact acknowledgement and added malformed
rejection/date coverage. No independent editor copy, new migration/API/layout or
impact product implementation. Source-backed API receipt roundtrip also passes.
Local full580 backend/70 frontend/9 Rust/35 .NET =694 distinct PASS, packaged16
repeat PASS; locked builds/format, PowerShell harness and actual packaged18→19/
verified backup/old-binary rejection/restored18 reopening PASS.
Final docs/privacy/CI recorded in the original Draft PR after actual execution.
Local documentation13 files/172 links and staged privacy378/diff PASS.

Native GUI for this review head NOT RUN; earlier candidate evidence is historical.
Configured VM inventory28 classes resolves to the known Evaluation base, no
qualified replacement found. Offline install/upgrade/restart BLOCKED. Host
activation/build checks are not substitutes. Multi-window journal atomicity is
unqualified, not solved by a current-value guard; production daily writes stay closed.
