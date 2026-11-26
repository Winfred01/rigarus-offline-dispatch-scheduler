# Issue124 — confirmed unconfirmed-Draft transaction evidence

Baseline main75dc07862a97ecd5522c0e617b7d81e2c4085083 (human-merged123),
Windows CI45773860962 all3 jobs PASS before product edits. Pre-code plan/owner
decision commit1858259. Public repo, isolated codex/safe-manual-apply; synthetic
data only. See [design](../design/2026-11-26-issue-124-draft-apply.md) and
[reproduction/API](../../samples/synthetic-only/draft-transactions.md).

Owner November26 explicitly permits reviewed Pending plans to be saved as
unconfirmed Draft with exact warnings acknowledged; known hard blockers reject.
This supersedes only the former incomplete-evidence Draft refusal. No production
writer, dispatch certification, Publish, actual restore or customer acceptance.

## Implemented

- Query-only prepare binds exact source/proposal/plan SHA256, lineage UUID,
  candidate, before/after/cancel set, confirmation and Pending/unsupported reasons.
- One reserved SQLite transaction recomputes current plan and independent checks,
  saves reviewed dates/cancellations/history, validates final saved observations,
  then writes immutable version/audit/receipt. Any failure rolls back everything.
- Matching Crew/date IDs and notes survive; legacy AM/PM remains separate and
  occupied. No actual Rig, automatic workers/source transfer or dependency shift.
- Same key/payload replays original committed result after restart; key mismatch
  rejects. Receipt absence is uncertain. A separate synthetic CLI opt-in requires
  matching smoke-root database; default API/desktop production writers stay closed.
- Read-only inverse compares exact committed After with current touched records;
  subsequent edits Stale. This is not full resource freshness or enabled restore.
  Future restore must append new revisions, not rewind history or copy old DBs.
- Schema20 additive immutable DraftVersions, FK to retained schema19 lineage;
  verified pre-DDL backup, transactional migration/fault rollback/retry/reopen.

## Actual verification

| Check | Outcome |
| --- | --- |
| New synthetic transaction cases36 | PASS within final full suite; focused34 also passed before two added regressions |
| Frontend locked restore / formatting /74 tests / TypeScript/Vite | PASS |
| Historical .NET locked restore/format/Release /35 tests | PASS |
| Full backend | PASS644, 235.248seconds |
| Actual packaged sidecar | PASS17 repeated subset, 34.509seconds |
| Rust / Windows Release / NSIS | PASS11 / PASS / PASS; installer built, not installed |
| PS5 acceptance-harness regression | PASS; expected synthetic timeout/failure paths are not native GUI acceptance |
| Actual prior19 binary | PASS: rejects20; independently restored verified19 backup reopens logically unchanged |
| Staged privacy / documentation / whitespace / Ruff | PASS394 indexed paths /9 Markdown files,165 local links / PASS / PASS135 files |
| Exact-head Windows CI | Draft PR records run/head and final job results after push |
| New native desktop confirmation/recovery UI | NOT RUN; no UI/bridge implemented in this backend-only slice |
| Disconnected install/upgrade/reboot | BLOCKED: owner confirmed no qualified replacement for expired Evaluation VM |
| Customer Demo C/E/UAT / production approval | NOT RUN / pending human acceptance |

Focused tests cover extension5→8 and early finish5→2, exact stable IDs/notes/
explicit workers, Pending acknowledgement, source/plan/UUID tamper and Stale,
legacy same integer namespaces, personnel collision, driver suspension, member/
Level shortage, employee Unavailable, unknown weekend capacity, actual saved Rig
maintenance, final known-block refusal, same/different-key concurrency, same-key
replay/restart, storage/final-source/audit/mid-write/deadline failures with logical
rollback, immutable audit, integrity/FKs, migration backup/preservation/fault/retry,
schema19 reader refusal, inverse/no-write/Subsequent-edit Stale.

Initial local tests caught path integer coercion and synthetic fixture signature
mistakes; corrected before delivery. The first complete642 run exposed two unchanged last-migration-name assertions;
updated only their current schema expectation to20 and reran644 successfully.
A discovery-time full607 run overlapped
schema edits and failed its old sidecar migration-count assertion (19 versus20);
it is not a clean baseline claim. Merged-main CI is the verified baseline; final
full suite must pass on finished sources. Initial local build invoked PowerShell5
and treated normal PyInstaller stderr progress as terminating; rerun under
PowerShell7. These are recorded failures, not customer data operations.

## Remaining independent slices

Desktop exact confirmation/durable request recovery and version comparison;
native/offline acceptance and controlled writer rollout; actual restore as a new
conflict-checked audited transaction; granular locks/dependencies/delay propagation;
later formal immutable Published PDF/Excel. Open Foreman/category/authority policies
remain Open. This backend foundation does not complete Issues18/20/29/99/120.

Local Windows11 Pro10.0.26200 x64, connected development host. New installer
SHA256 e889f68a9f3fedf9a6b552bfa6712cc8e60166cc9230508d16f0d41a494d37a8;
not executed/installed. Actual prior19 sidecar SHA256
591a70c5141afd3d1ece0d10f85d5d767d7c96713169cff84ff733b30a78048a.
644 backend +74 frontend +11 Rust +35 .NET =764 distinct tests; packaged17
are repeats, not additional unique tests. No dependency locks, React or Rust
product files changed. No real customer profile, release or merge operation.
