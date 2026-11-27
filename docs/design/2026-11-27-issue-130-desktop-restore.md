# Issue130 — desktop Draft Restore confirmation and request recovery

## Baseline and delivery status

Design-only handoff for [Issue130](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/130),
parent20, compatibility99, reuse126. Fresh public repository main
`a1ea436b86074876800247c3f4e742c33217b899`; PR129 human-merged November27.
Existing backend implementation0323f9e is reused, not reimplemented. No competing
open PR or duplicate desktop Restore Issue found at inspection. Isolated branch
codex/issue-130-desktop-restore; preserve root README/language/local originals.
Reuse this Issue branch and Draft PR for its later implementation.

This delivery changes documentation only. New desktop behavior and tests below
are **NOT RUN / not implemented**. Prior backend tests are historical evidence,
not desktop success. No control, Tauri command, startup flag or writer is enabled.

## Design Compliance Checklist

Sources freshly checked November27,2026 for existence, revision and checkout UTC
mtime; full inventory is local. Read current affected sections again, including
the architecture's Restore/desktop recovery/workbench, model21/20/19 and
acceptance's Restore/confirmation/gates. Do not claim all historical subsections
were reread. All checkout times below are metadata, not business authority.

| Source | Last-changing revision / version | Checkout modified UTC | Relevant sections |
| --- | --- | --- | --- |
| AGENTS / DEV-DESIGN-CHECKLIST | d3b9bea | 2026-11-27T20:54:37Z | Mandatory workflow; source identity; UI; delivery/reporting |
| docs/00-PROJECT-PLAN | 0323f9e | 2026-11-27T20:54:37Z | Current Restore priority; Scope; dependency order |
| docs/09-DELIVERY-PLAYBOOK | 0323f9e | 2026-11-27T20:54:37Z | Restore/confirmation; Engineering/Demo/Production gates |
| docs/02-ARCHITECTURE | 0323f9e | 2026-11-27T20:54:37Z | Synthetic Restore; desktop exact recording/recovery; weekly workbench |
| docs/03-DATA-MODEL | 0323f9e | 2026-11-27T20:54:37Z | Source-linked Restore21; DraftVersions20; recovery19 |
| docs/05-DEMO-ACCEPTANCE | 0323f9e | 2026-11-27T20:54:37Z | Single-version Restore; desktop confirmation |
| docs/10-CLIENT-DECISIONS | d4052a3 before this edit | 2026-11-27T20:54:37Z | Confirmed five conditions; mixed display; historical Proposed entry |
| Local original UI DOCX | November24, SHA below | 2026-11-24T23:15:38.711423Z | L10/L12/L13 text and original figures |

Local source Rigarus_UI_Design_Updated_2026-11-24.docx SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`.
Freshly extracted/viewed L10 paragraphs54–58/image62, L12 paragraphs64–68/image64,
L13 paragraphs69–73/image65. Paragraphs are not verified page numbers. Originals
remain local. L10 shows empty Published History, not a Draft Restore editor.
L12 mentions Undo Last Batch in explanatory text; the figure depicts batch Apply.
L13 shows candidate adoption. These are concepts, not implemented/native evidence
or authority for Published/full-week restore. Use their inspect/compare/confirm
flow with existing Rigarus Dialog/row styling; the detailed Restore states below
are a proposed adaptation. Prototype half-day counts do not override confirmed
new full-day scheduling or authorize new half-day entry.

Current #20/#99/#124/#126, merged129, the31-test Restore inventory/acceptance
matrix and relevant current code reviewed. Actual implementation: draft_restore/API provides gated prepare/submit,
read-only receipt/version; no Restore status route/desktop bridge. Existing
draft-confirmation.tsx, draft-confirmation-state.ts and Rust sidecar/draft_journal implement Apply
confirmation/recovery with a different envelope/acknowledgement contract.
Do not route Restore through Apply's whitelist or bulk warning checkbox.

| Requirement | Authority / implementation | Required change and acceptance |
| --- | --- | --- |
| One exact original version | Confirmed backend20; existing21 | Explicit typed source/profile; display original versus inverse; no latest-version inference |
| Specific warning confirmation | Confirmed backend20; Missing desktop | Per-warning unchecked control bound to exact plan; missing/stale/blocked rejects |
| Cancel versus uncertain close | Requested next priority; Missing desktop | No pre-submit persistent writes; post-dispatch close retains request, not a transaction cancel |
| Original-key recovery | Existing backend receipts; Partial native foundation | Operation-tagged exact journal; verify/archive before release; no NotFound/new-key assumption |
| Mixed day/half visibility | Reconfirmed; Existing boards/Locate | Preserve raw labels/notes/members/Rig/history and independent ID namespaces |
| Future Employee/search/exports | Confirmed compatibility; Partial/Missing coverage | Explicit later typed-data/display audit; do not claim those modules upgraded here |
| Offline and production | BLOCKED / unapproved | Qualified target VM evidence separately; no runtime writer opening or customer pass |

## Implementation Plan — future product slice, no product edit here

1. Recheck main, owner decisions, this contract, source figures and existing PR
   feedback before implementation. Keep Tauri/Rust + React/TypeScript + FastAPI +
   SQLite, Windows-only/single-operator/offline; no login/cloud. Reuse schema21.
2. Proposed files: draft-restore-state.ts (strict validators/pure state),
   draft-restore.tsx (independent confirmation/recovery Dialog), associated frontend
   tests; extend existing Schedule recovery entry, main.rs fixed command,
   sidecar.rs bounded authenticated calls, draft_journal.rs operation-aware storage
   and Rust tests; small draft_restore_api.py status projection plus API/sidecar
   tests. Do not replace the weekly calendar or duplicate resource validators.
3. API: reuse POST /draft-restores/prepare and /submit; GET receipt/{profile}/{key}
   and version/{profile}/{id}. Add a read-only actual gate/profile/status projection;
   never infer enabled state from renderer configuration. Reuse original version
   lookup, explicitly labeled DraftVersion, distinct from DraftRestoreVersion and
   PublishedSnapshot. No general URL/SQL/file-path forwarding from the renderer.
4. Proposed engineering opt-in: separate exact synthetic-root environment flag
   before Rust passes --synthetic-draft-restores; independent of Apply opt-in.
   Both prepare and submit require the real closed-by-default backend gate.
   Preparation is BEGIN IMMEDIATE + rolled-back SAVEPOINT, not query-only SQL.
   Read-only views must not silently fall back to production prepare. No live UI
   preference, production toggle, Publish or true-customer database operation.
5. Show source identity, original Before/After and separate current/proposed
   inverse. For each typed touched ID show revisions/status/local date,
   Project/WorkItem/Crew, notes and exact actual staff; label IDs when names are
   not independently available. Mark cancel/reactivate/retained rows. Show only
   recorded Rig facts; historical readiness/consent is not new proof. Paginate or
   scroll complete data without truncating the proof or permitting unseen warnings.
6. Warning controls: each canonical warning ID has its own initially unchecked
   checkbox with full reason/record context. No select-all substitute. Require
   separate exact-plan confirmation; selection/plan/fingerprint change clears
   all acknowledgements. Blocked/Stale disables submit; Pending never Passed.
7. Journal format: explicit operation=DraftRestore and versioned envelope;
   retain exact profile/source/request/plan SHA, complete warning acknowledgements
   and reviewed plan before dispatch. Restore pending/archive names must not
   collide with existing Apply journals, even for the same UUID. Reuse one
   profile-level exclusive guard; under it inspect both operation namespaces
   and block another mutating workflow while either is unresolved. Existing
   untagged Apply journals retain their original interpretation. Manual-editor
   localStorage coordination remains an independent known limitation, not fixed
   by this proposal. Do not migrate/delete unknown recovery files automatically.
8. Bound all work: preserve SQL30s, HTTP60s and desktop150s deadlines. Target
   backend limits2MB request/4MB plan/8MB result/366 rows; native journal8MB.
   Explicitly reject unsupported oversized wire/envelope combinations, never
   truncate. Use bounded HTTP reads, not unbounded JSON followed by a size check.
   Timeout does not cancel commit; ignore late UI replies until deliberate resolve.
9. Receipt validation must match operation/profile/key/complete request, exact
   source kind/ID and root Pending/false flags. Committed additionally requires
   the reviewed plan and all touched before/after IDs/business values/statuses/
   revisions. A successful commit appends
   revisions/history/version; it does not activate old Rig/driver/weekend proofs.
   Rejected receipts differ: backend21 persists known rejection outcomes. Fetch
   and verify that sealed receipt; do not reuse Apply's synthesized409 retirement.
   Bare409, read failure, malformed/mismatched response and NotFound stay uncertain.
10. Archive the authenticated verified receipt with flush/exclusive guard before
    removing only its exact pending file. Acknowledgement accepts identity/digest,
    rereads authoritative data in Rust, and does not trust renderer After values.
    Archive/write/flush failure retains recovery. No automatic replays/new keys;
    only explicit identical original-request replay after reconciliation.
11. No SQLite migration anticipated: schema21 already stores immutable source-
    linked recovery version/audit and independent receipts. Any newly demonstrated
    schema need requires a separately documented minimal plan before affected
    code; never rewrite old JSON/history, alter AM/PM or downgrade a live DB.

## UI states and cancellation contract

| State | Required behavior |
| --- | --- |
| Closed/default gate | Explain closed engineering gate; no enabled Restore write or automatic dry run |
| Loading/empty/invalid | Show bounded progress, no source selected, invalid typed ID or unavailable original; no guessed selection |
| Prepared Current | Complete immutable current/inverse difference and individually unchecked warnings |
| Blocked/Stale/read error | Explicit reasons; no submit; deliberate prepare again invalidates old confirmations |
| Cancel before dispatch | Cancel/X/Escape closes; no persistent business/audit/receipt write; restore opener focus |
| Submitting | Freeze version/acknowledgements and double-submit; announce progress; Close cannot imply transaction cancellation |
| Unknown/reopened | Retain/display original operation/key; resolve first, explicit same-body replay only; close keeps journal |
| Committed | Show recovery version and durable receipt; remain unconfirmed Draft; refresh boards using reads only |
| Committed + refresh failure | Preserve success and recovery evidence; retry reads, never Restore again |
| Rejected | Show verified original rejection; explicit durable acknowledgement before retiring that request |
| Journal/receipt/storage conflict | Fail closed; do not reset/delete files or silently switch profile/key |

Use existing Dialog semantics, labeled controls, visible keyboard focus, live
status/error announcements and focus return. Escape follows the state-specific
close contract; confirmation never moves behind an overlay. Long notes/warnings,
scroll and narrow windows must retain context and reachable Cancel/Resolve.

## Compatibility and future coverage

Job Schedule/Crew Board keep FullDayDraft versus LegacyHalfDay labels, separate
Project/WorkItem/Crew/date facts and recorded notes/actual people/Rig. Use
record_kind+id, including FullDayDraft1 versus LegacyHalfDay1. Cancellation leaves
active boards but stays in history; active Locate must not fall back to another
kind. No old-half conversion/merge/edit or occupancy release by Restore.
Current search and Employee Week still have legacy coverage limitations; later
work must add typed daily support rather than hide/convert old rows. Future
company/Crew/employee PDF/Excel must verify both types against a coherent source,
not infer that this design supplies publication or exports.

## Acceptance cases — future desktop execution NOT RUN

| ID | Synthetic case / expected result | Current result |
| --- | --- | --- |
| D01 | Select original version; inspect all original/current/inverse facts,5→8 and5→2 | NOT RUN |
| D02 | Missing/extra/changed acknowledgements; every exact item required | NOT RUN |
| D03 | Known blocker, later edit or wrong profile/source type; no write | NOT RUN |
| D04 | Cancel/X/Escape before dispatch; logical business/audit/receipt equality | NOT RUN |
| D05 | Double click/close during send; no second key or claimed rollback | NOT RUN |
| D06 | Commit then lost response; restart/resolve returns same version/history once | NOT RUN |
| D07 | NotFound/timeout/service error; unchanged journal, explicit original replay | NOT RUN |
| D08 | Wrong operation/profile/body/source/plan/After/flags; no journal release | NOT RUN |
| D09 | Same UUID Apply/Restore; namespace and unresolved-operation interlock | NOT RUN |
| D10 | Malformed/oversize journal, competing process, archive/flush failure | NOT RUN |
| D11 | Verified Committed versus Rejected, exact archive then matching retirement | NOT RUN |
| D12 | Committed + failed refresh; read retry updates both boards/Locate only | NOT RUN |
| D13 | FullDay/legacy same integer ID, distinct projects/AM/PM/notes/staff/Rig/history | NOT RUN |
| D14 | Keyboard/focus/screen-reader, long data, narrow window, no unseen warning confirmation | NOT RUN |
| D15 | Default gates, wrong smoke root, runtime flag absent; no dry run/write | NOT RUN |
| D16 | Full locked backend/frontend/Rust/historical.NET, build/privacy/Windows CI | NOT RUN for product |
| D17 | Exact-package native synthetic GUI/reopen and DB integrity/history | NOT RUN |
| D18 | Qualified disconnected VM install/upgrade/OS reboot/data retention | BLOCKED |

Current documentation checks and CI are reported in the Draft PR; no product
tests are claimed executed by this documentation-only change. No product UI,
SQLite/API migration or new executable is produced. Qualified licensed VM is
still missing; never bypass Evaluation expiry or substitute the development host.
Customer Demo/UAT, deployment/production Restore and Publish remain unapproved.

Remaining design risks: native cross-operation serialization/durability, complete
receipt validation and size bounds need actual fault tests; prototype has no
exact Restore layout; manual-editor coordination is separately scoped. Recheck
design/current code before implementation; preserve all existing hard constraints.
No automatic merge, Issue closure, Release or raw-source/customer-data upload.
