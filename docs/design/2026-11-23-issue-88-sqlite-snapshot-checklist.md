# Issue #88 — active SQLite read-only verification

November 23, 2026, America/Toronto. Latest fetched main `e6cb19db8a4ac9f1e0bdeb504dcb82ffe4e96111` contains the owner's human merge of PR #87. Issue #88 is open. The repository remains PUBLIC. Work uses independent `codex/issue-88-sqlite-readonly-snapshot`; unrelated root README/Chinese README/original-design changes are preserved.

## Sources read again

Existence, SHA-256, content revision and filesystem last-write UTC are recorded locally; checkout timestamps are not approval dates.

| Source | Revision | Relevant sections |
| --- | --- | --- |
| AGENTS.md | `d3b9bea` | Design-First, synthetic evidence, one slice, human review |
| docs/00-PROJECT-PLAN.md | `d43fa6d` | Offline scope and actual dependency order; #28 integration gates |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326df` | Engineering / customer acceptance / production separation |
| docs/02-ARCHITECTURE.md | `d43fa6d` | Sidecar lifetime, explicit staffing, availability, read-only Employee Week |
| docs/03-DATA-MODEL.md | `d43fa6d` | Stable IDs/history, WAL, read transactions and schema ten |
| docs/05-DEMO-ACCEPTANCE.md | `dd12c43` | Cancel/read-only guards, Employee Week and calendar reopen, #86 snapshots |
| docs/10-CLIENT-DECISIONS.md | `d43fa6d` | Draft versus safety/publication; no new business defaults |
| #86 checklist, #35 supervisor record, #88 body/comments and #87 result matrix | `dd12c43` / live GitHub | Actual Normal digest mismatch, Hidden WAL sharing failure; closed full-table equality; original Project timeout still unconfirmed |

No product UI is changed, so original UI figures are not applicable. No fresh original-DOCX read is claimed; the complete design stays local. This is acceptance tooling, not a change to the Tauri/React/FastAPI/SQLite product architecture or a return to WPF development.

## Design Compliance Checklist

| Requirement / authority | Existing behavior and planned change | Acceptance case |
| --- | --- | --- |
| Confirmed: ordinary WAL behavior must not imply a business change | `Get-FileHash` reads active DB/WAL separately; last-connection checkpoint changes physical bytes | Same logical fingerprint across active WAL, checkpoint, cleanup and physical layout changes |
| Confirmed: detect real record changes | Replace physical hash with canonical typed records, schema/version metadata and ID sequences from one read transaction | Insert/update/delete, notes/IDs/types, NULL versus empty, Unicode/NUL, BLOB, duplicates, schema and sequence changes |
| Confirmed: never silently ignore unknown reads | Missing, corrupt, locked, integrity/FK, native-library and resource errors must throw without a fingerprint | Actual failing files, lock timeout, invalid FK; no constant digest or byte-hash fallback |
| Consistent active reads | Use system SQLite READONLY + PRIVATECACHE, query-only, explicit read transaction; keep normal locks/change detection | Concurrent atomic two-table writer; 100 reads must match a complete committed state |
| Bounded work and privacy | Existing GUI deadline, SQLite busy/progress limits, explicit size/row/table limits; independent outer watchdog | Persistent lock times out; no partial/truncated fingerprint; log only phase/time/count/version, never rows |
| Preserve native gate and package | Same Save/Cancel/selection/value/exit assertions and frozen installed payload | Original full Employee Week/Availability/staffing/calendar/reopen command under Normal and Hidden supervision |
| Evidence and human approval | CI is not native acceptance; preserve failures | Actual statuses, closed SQLite/data/file/process audit; Draft PR, no merge/Issue closure/Release |

## Implementation Plan

1. Recheck current Issue/PR/main, actual helper call sites and prior Normal/Hidden exception chains. Keep the raw synthetic reproductions local.
2. Add acceptance-only `TauriSqliteSnapshot.ps1`. Use the Windows system `winsqlite3.dll` through a small C# interop helper, without installing a runtime/SDK or changing the application. Probe actual Windows compatibility; missing/incompatible library is a failed check, never a skipped guard.
3. Read schema, explicit stored column values and `sqlite_sequence` in one read-only transaction. Encode SQLite storage type, lengths and raw values; sort encoded row multisets to preserve duplicates without relying on physical order. Include schema definitions, user/application versions; exclude physical page/WAL/SHM bytes and housekeeping statistics. Check integrity/FKs. Compare net committed logical states, not an audit of every transient SQL statement.
4. Fail at the existing GUI deadline (Default 30 / SlowVm 150 s, existing overrides), with busy waits at most 5 s and a progress callback. Technical safety limits are 256 tables, one million encoded schema/data rows and 128 MiB counted read/encoding work. Exceeding a limit fails, never truncates. The independent process watchdog remains required for synchronous OS/provider calls.
5. Replace only the implementation of `Get-SyntheticAssignmentDigest`; keep all its callers and their before/after equality assertions. Add snapshot START/PASS/FAIL/TIMEOUT events. Include the matching module in the offline acceptance kit. Keep all product/API/schema/package files unchanged.
6. Add real SQLite synthetic regressions and wrapper/kit checks to the existing PowerShell 5.1 CI harness. Exercise mutation and error controls as well as normal WAL and concurrent snapshots; do not equate arbitrary WAL bytes with a committed row.
7. Run matching native full scenarios under Normal/Hidden supervision in fresh no-NIC VM overlays, with independent deadlines. If successful, additionally exercise Employee Week → Availability → actual staffing → Project navigation using retained synthetic data. Verify close/reopen, all logical records, SQLite integrity/FKs, frozen payload and residual processes from a closed guest. Record any unexecuted/failed gate honestly.
8. Run parser/docs/whitespace/privacy and current-head Windows CI; push one branch and open/update one Draft PR. Publish only sanitized findings. Customer acceptance and production remain separate.

## Conflicts, differences and open items

No new business rule or migration. This deliberately changes the *measurement* of the existing no-business-change invariant; it does not remove that invariant. SQLite may manage normal WAL/SHM locks/files while reading. A stable final logical snapshot cannot prove that no intermediate write was later reverted; a SQL write audit is outside this check. Unsupported schema/runtime/read errors must remain visible. The original intermittent #86 Project timeout is not declared fixed by this reader or by a successful reduced probe. #26 complete GUI acceptance remains pending until its matching full flow actually passes; #28 design can proceed independently.

Primary references: [SQLite isolation](https://sqlite.org/isolation.html), [read-only open flags](https://sqlite.org/c3ref/open.html), [read-only WAL conditions](https://sqlite.org/wal.html#read_only_databases). Never use `immutable`/`nolock` on the active test database or copy only its live main file.
