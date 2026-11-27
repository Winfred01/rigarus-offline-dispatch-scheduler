# Issue130 implementation — refreshed Design-First checklist

## Design Compliance Checklist

Fresh main d4f97ad8d2dc87b71d42bf812666b4a39ff72a2c, human-merged131;
public repository, no competing open PR. User explicitly requests a NEW short
product branch from this baseline: codex/issue-130-desktop-restore-ui, isolated
worktree; previous design PR stays merged. Preserve root unrelated changes.
Design PR CI149/run46067419996 all3 passed; this is not new desktop evidence.

Fresh source inventory (full SHA/checkout UTCmtime local): AGENTS/checklist
d3b9bea; plan00/playbook09/decisions10 and Issue130 design f3a68da; affected
architecture02/model03/acceptance05 at0323f9e. Current sections reread, not all
historical subsections claimed. Original UI November24 DOCX SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c,
mtime2026-11-24T23:15:38.711423Z; freshly inspected L10 paragraphs54–58/image62,
L12 paragraphs64–68/image64, L13 paragraphs69–73/image65. Paragraphs are not
pages. Published History/batch Undo are concepts, not permission for Published
or whole-week recovery. Originals remain local. Current original-version backend,
strict API/schema21, desktop Apply state/bridge/journal/Dialog and mixed weekly
entry points checked; no database migration needed.

| Requirement | Existing source / needed change / acceptance |
| --- | --- |
| Exact original/current/inverse | Backend21 and L10/L12 inspect flow; new independent Restore Dialog; D01/D03 |
| Every Pending / Blocked / Stale | Backend warning IDs; independent unchecked controls; exact-plan change invalidates; D02/D03 |
| Cancel and Unknown | Existing Dialog/native journal foundation; preserve dispatch uncertainty/original key; D04–D08 |
| Operation isolation | Apply envelope is incompatible; separate typed pending/archive under same profile guard, mutually block unresolved writes; D09–D11 |
| Committed versus refresh | Never resubmit to fix a read failure; D12 |
| Mixed FullDay/Legacy | Existing boards and typed Locate, retain all raw facts/occupancy; D13 |
| Accessibility / limits | Existing app shell/type/colours; complete scrollable evidence, keyboard/focus/status; D14 |
| Gates and environment | Independent synthetic flag/exact root, real backend status; D15–D18 |

## Implementation Plan — before product code

1. Backend adds read-only Restore status/profile, no new SQLite schema or resource
   rules. Reuse original version/prepare/submit/receipt/version. No production gate.
2. Native fixed Restore actions and bounded authenticated response/request reads;
   independent startup test flag/exact root. Reuse shared profile OS guard,
   operation-specific pending/archive names. Block new writes across Apply/Restore
   while either unresolved; never reinterpret old Apply envelopes.
3. Add strict native and TypeScript envelope/plan/receipt validation: exact source,
   profile/UUID, plan/warning set, typed rows/revisions/staff, observations and
   Pending/false flags. Verified immutable Rejected receipt differs from Apply's
   synthesized rejection. Archive flush precedes exact journal retirement.
4. React Restore Dialog independent of recommendation success: enter explicit
   original DraftVersion ID; four complete row views (original Before/After,
   current/inverse), independent Pending checks, plan confirmation. Closed/loading/
   empty/invalid/blocked/stale/error/prepared/submitting/Unknown/reopened/Committed/
   Rejected/refresh-error states. Cancel/X/Escape before dispatch leaves no durable
   writes; after send preserve exact journal; explicit resolve/replay only.
5. Screen question: which exact records change, and what actually committed?
   Signature: typed per-date identity/revision differences beside explicit warnings.
   Keep existing Rigarus shell/palette/type/Dialog; no unrelated visual redesign.
   L10/L12/L13 flow adaptation is deliberate; complete evidence over decorative
   totals. Long data scrolls; native keyboard/focus and narrow width checked.
6. New frontend/native/backend fault/namespace tests and fresh18-case evidence;
   new native synthetic GUI/reopen/DB integrity checks. Locked restores, formats,
   Windows builds, full Python/frontend/Rust/historical.NET, privacy and CI.
   Host native engineering is NOT disconnected VM acceptance. D18 remains BLOCKED.

Risks: matching complete receipts and source proofs, bounds, lost response,
archive/flush/process-exit/cross-operation interaction. Existing manual-editor
localStorage coordination remains separate; no claim that it is fixed. No old
half conversion, new half editor, downstream propagation, legal/resource-policy
invention, customer DB, Publish, auto merge/Issue closure/Release/deployment.
All new execution outcomes remain NOT RUN until actual evidence is recorded.
