# Issue126 — exact desktop Draft confirmation and reconciliation

## Design Compliance Checklist

Fresh public repository/main0f128221b496e38a49267b0625e860b4d055f694,
externally human-merged PR125. Current main Windows CI45839749613 must pass
before product edits. Root README/language/local design changes preserved;
independent codex/issue-126-draft-confirmation. Issue124 backend-only scope and
merged125 implementation/evidence read; no competing open PR/review feedback.

Fresh source inventory records SHA256, last-changing Git revision and checkout
UTC mtime locally: AGENTS d3b9bea; plan/playbook/architecture/model/acceptance
b6eb695; decisions1858259. Relevant current sections, historical compatibility
and owner authority were re-read, not inferred from an older chat. UI original
November24 DOCX remains local: SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c,
mtime2026-11-24T23:15:38.711423Z. Fresh extracted original L10 paragraphs54–58/
image62, L12 paragraphs64–68/image64, L13 paragraphs69–73/image65 viewed.
Paragraph locators are not page numbers. No original design/images uploaded.

| Requirement | Existing / implementation / acceptance |
| --- | --- |
| L13 explicit candidate adoption | Existing single-WorkItem impact; exact prepare for one selected Crew, no selection inference |
| L12 inspect before committing | Existing prepare contains exact before/proposed/cancel sets and warnings; separate plan/warning confirmations |
| L10 version identity | Read exact immutable schema20 version and Current/Stale inverse; not Published snapshot or full-database undo |
| Owner Pending recording decision | May record exactly acknowledged Pending as unconfirmed Draft, known blockers reject; no safety certification |
| Stable data and rules | Reuse merged transaction, ID/history/legacy/resource guards; no scheduling duplication or migration |
| Unknown save and restart | Durable native database-scoped original request, exclusive per-profile operations, original-key reconciliation/replay; no blind new key |
| Receipt acknowledgement | Validate exact confirmation, plan, typed before/after IDs/values/revisions and false flags; no malformed response retires recovery |
| Committed plus refresh failure | Keep exact receipt/version visible; refresh reads only, never repeat Save |
| Production/offline gates | Synthetic flag + exact smoke-root only; production closed. Expired Evaluation/no qualified replacement remains BLOCKED |

Deliberate differences: Full Day replaces prototype halves. No batch Apply/Undo,
inferred workers/actual Rig, lock/dependency defaults, actual restore, dispatch
approval or Published history. Missing data is Pending, not Satisfied. Native
cross-instance/process durability must be tested and limitations stated before
any rollout; existing manual editor localStorage limitation is not silently
declared fixed by this separate workflow.

## Implementation Plan — before product code

1. Fixed authenticated status/prepare/submit/receipt/version/recovery actions,
   bounded payloads/IDs/UUIDs, SQL30s/HTTP60s/desktop150s. Minimal status projection
   exposes actual separate test gate/profile; no production switch.
2. Rust pre-dispatch recovery file under the same isolated database directory,
   bounded exact JSON, create-new/flush and per-profile native serialization.
   No replacement while unresolved, malformed/unreadable journal fails closed.
   Acknowledge only exact verified result; NotFound/storage/network errors remain
   uncertain. No automatic retries. Rejections versus unknown remain explicit.
3. React confirmation within existing recommendation workflow. Inspect immutable
   prepared before/proposed/cancellations, employee IDs/notes, all warnings, two
   separate confirmations. Changed context requires new preparation. Cancel before
   dispatch writes nothing. Busy closes disabled; unknown can close retaining
   recovery. Committed receipt persists through failed week refresh/reopen.
4. Recovery entry independent of successful preview, plus exact version ID lookup
   and read-only inverse with Current/Stale and Restore unavailable. Escape/focus,
   empty/loading/invalid/blocked/stale/rejected/unknown/committed/read-error states.
5. Meaningful malformed/mismatched receipt, late reply, journal failure, conflicting
   pending key, double action, restart/replay/default-gate and read-only inverse
   tests; native synthetic visible workflow and DB invariants; full locked
   backend/frontend/Rust/.NET build/format/privacy/Windows CI. Installer/offline
   upgrade/reboot requires qualified VM and cannot be borrowed from CI.

Existing Rigarus shell/palette/type retained. Screen question: exactly what will
this choice record, and what actually committed? Signature is typed saved/proposed
date rows, explicit warning acknowledgement and immutable version receipt; no
charts, fake totals, rebranding or web assets. Style app sheet keeps palette/type;
table scrolls within its frame; important identity/status stays legible.
