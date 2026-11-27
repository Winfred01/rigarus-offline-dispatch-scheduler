# Issue20 — single historical Draft Restore backend

## Design Compliance Checklist

Fresh main99c9741297ae6158aec849fa3f6ce3337bd24513, public repository, human-merged
PR128, no competing open PR. Branch codex/issue-20-draft-restore, isolated worktree;
preserve root README/language/local-design changes. Current #20/#99/#124/#126,
confirmation comment7227116880 and existing code checked. Owner's exact scope
confirmation is engineering-only, not proof of legal/customer authority. New
confirmed decision precedes product code; historical Proposed text is preserved.

Sources freshly checked for existence/revision/UTCmtime (full SHA inventory stays
local): AGENTS d3b9bea; DEV-DESIGN-CHECKLIST d3b9bea; planning00/playbook09,
architecture02/model03/acceptance05 at80e6eb8; decisions at8f63b1c before this edit.
Plan/playbook reread, current affected architecture/model/acceptance/decision
sections reread; not every historical subsection is claimed read. Schema20,
DraftVersions, draft_apply/API, day_draft_store, storage/backup, weekly resource
projection, migration/transaction tests, desktop confirmation and native journal
reviewed. Exact source revisions/checkout times are retained locally.

Latest local UI original November24: SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c,
mtime2026-11-24T23:15:38.711423Z. Fresh original L10 paragraphs54–58/image62 and
L12 paragraphs64–68/image64 inspected; L13 text69–73 and original image65 relevant
to existing candidate adoption. Paragraphs are not page numbers. Published History
and batch Undo are concepts, not authorization for Published/full-database restore.
No UI change in this backend slice; originals stay local.

| Requirement | Existing / planned change / acceptance |
| --- | --- |
| Exact single DraftVersion | Existing immutable original JSON; reject other kind, malformed/missing source or any current After/revision mismatch |
| Append only | Reuse read_day/append_change and all SQL guards; add new revisions even for retained touched values; additions cancel, cancelled originals reactivate under current constraints |
| Per-item Pending | Reuse current weekly saved-resource chain; canonical warning IDs for each missing reason plus unsupported locks/dependencies; exact full acknowledgement set required |
| Known hard conflicts | SQL daily/legacy/Rig occupancy and current Crew/people/driver/capability/calendar/Rig/consent checks reject; no old certification copied |
| Atomic / uncertain result | BEGIN IMMEDIATE includes revalidation, exact proof, changes, immutable recovery version/audit and independently namespaced receipt; same request replay and changed-payload refusal |
| Mixed FullDay/Legacy | Keep typed IDs, old AM/PM labels/notes/staff/Rig/history; regression existing weekly projection/Locate and occupancy; no new half-day editor or calendar |
| Minimal migration | Schema20 original DraftVersions lacks source-version FK / recovery namespace; schema21 adds only immutable DraftRestoreVersions + DraftRestoreReceipts, verified pre-DDL backup |
| Closed gates | Explicit new synthetic flag plus exact smoke-root database; no Rust command/desktop Restore/production runtime switch/Publish |

Baseline main CI46060107526: Python/.NET succeeded; Tauri failed in existing
draft_journal archive-failure fixture when Journal::open unexpectedly found its
recovery storage unavailable/occupied. Temporary fixture names currently depend
only on process+wall-clock nanos and create_dir_all can reuse a collided path.
Investigate/reproduce this test isolation risk; if confirmed, make test fixtures
exclusive/unique without weakening journal locking or assertions. No product
journal-policy change belongs to this slice. Record failure and final rerun.

## Implementation Plan — committed before product code

1. Add draft_restore_migration.py (schema21 source-linked immutable recovery
   versions and separate committed/rejected idempotent receipts); extend exact
   storage/read-schema inventories and synthetic older-schema fixture removal.
   Back up recognized20 before DDL. Preserve all original JSON/data/history.
2. Add draft_restore.py and strict draft_restore_api.py: status, gated synthetic
   prepare/submit, read-only receipt/version lookup. Separate UUID request namespace,
   database identity, bounded payload/rows/output, shared30s deadline/read budget.
3. Preparation is a **synthetic-only reserved dry run**, not query-only SQL:
   BEGIN IMMEDIATE + SAVEPOINT executes exact inverse using existing SQL guards,
   appended revisions and current saved-resource validators, then always rolls
   back/release before returning. No persistent records/audit/receipt on prepare.
   Blocked remains visible; source/read faults fail explicitly. This avoids a
   duplicated resource engine or a partial in-memory approximation of SQL guards.
4. Source Before/After are immutable server values, never client-provided targets.
   Typed FullDayDraft IDs only, maximum366 touched rows. Compare exact current
   values including status/revision/staff. Use new revision/history for each row;
   do cancellations first. Do not copy old Rig/driver/consent evidence. Recheck
   current saved observations after new revisions, including stale approvals.
5. Bind preparation fingerprint and every individual Pending warning ID. Submit
   recomputes under the same write reservation, checks exact acknowledgements,
   repeats inverse and final validation, appends source-linked immutable audit/
   version and receipt atomically. Known rejection rolls back its savepoint and
   retains an immutable rejection receipt; storage/SQL/audit failure rolls back
   everything and remains Unknown. No automatic retries or replacement keys.
6. HTTP default closed; sidecar adds a separate manual test flag requiring exact
   RIGARUS_SMOKE_DATA_ROOT/data/rigarus.db. Existing desktop does not pass this
   flag. No UI state/interaction/API bridge change; native Restore UI N/A.
7. Test all twenty requested scenarios:5→8/5→2, stable IDs/notes/staff/history,
   unrelated records/old halves/equal integer IDs, legacy and resource blockers,
   stale/per-item Pending/false safety flags, replay/payload mismatch/concurrent
   calls, SQL/audit failure rollback, reopen, migration/backup/retry/prior-binary
   refusal/independent schema20 recovery, default gate. Regress mixed weekly
   projection/Locate and frontend labels rather than duplicate UI.
8. Locked restore, Ruff/Prettier/rustfmt, full Python/frontend/Rust/historical.NET,
   Windows sidecar/desktop build, packaged tests, CI/privacy and sanitized evidence.
   Qualified VM install/upgrade/OS reboot BLOCKED, no host-as-offline claim.

Limits: original DraftVersion only, not restore-of-restore/general undo/Published
revision; no downstream/locks/category/Foreman policy inventions. Customer UAT,
dispatch, production and Release are separate unapproved gates. No auto merge,
Issue closure or original-source/customer-data upload.
