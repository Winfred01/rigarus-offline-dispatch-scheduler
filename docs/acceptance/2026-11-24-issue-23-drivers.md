# Issue #23 — dated company-driver evidence and checks

Main baseline `7aec316e1ff2dccf3db8f927d971bdcd3cf96d2e` includes human-merged
PR95. Isolated branch codex/issue-23-driver-validation. Design-first commit
96c22ba preceded product code; [inventory/plan](../design/2026-11-24-issue-23-driver-checklist.md).
PUBLIC repository, synthetic sources/evidence only. Issue23 remains Open/partial.

## Implemented contract

DriverApprovalDraft requires explicit company confirmation/reference, local
inclusive range (at most366 dates), AM/PM/FullDay and Issue23 driver state.
DriverApprovalStore saves dated evidence under an expected per-employee revision,
retains immutable history and updates current exact-date cells atomically.
No-op retains revision; changed reference appends evidence; stale writes fail.
This internal service has no HTTP/UI entry, approver-role authentication or
legal/category/automatic-expiry policy. Employee roster DriverStatus stays
Unverified. Original business tables and actual assignments are not rewritten.

Necessary schema11 migration adds evidence/history without altering existing
constraints. Synthetic schema10 upgrade tests preserve every original table,
force history-insert failure after DDL, verify complete rollback, then retry and
idempotent reopen. Historical legacy migration fixtures now remove this latest
schema only in generated tests; production downgrade is never performed.
Older schema10 binaries reject the newer history. Real rollback needs a
consistent pre-upgrade backup and compatible binary, not table/history removal.
Native installer upgrade/recovery has NOT RUN; no customer database was opened.

Pure validate_drivers checks each actual active Draft's members with exact dated
approval and employee/availability/collision evidence. Active + explicit company
confirmation + active employee + recorded Available + no double-booking satisfies
this company-driver check. Missing/Unverified/unknown scope remains Pending.
Known disqualifications cannot count. All known ineligible means Blocked;
empty/unconfigured staffing stays Pending. Cancelled is ignored. Borrowing is
validated by evaluating all projected source/destination memberships, without
mutating saved data. Actual Rig/category/weekend/other safety gates stay separate.

Snapshot v3 reads driver cells/change IDs/confirmation and native revisions on the
same existing all-Crew read-only transaction, within current limits. Changed
other-Crew evidence invalidates the fingerprint; WAL controls prove complete
old/new views. validate_snapshot_drivers returns detached saved-Draft results;
PersistedRecommendations.driver_validation exposes them beside personnel checks.
Generated proposals lack actual proposed workers and keep ApprovedDriver Pending
in PR91. Every result is Validation pending / Apply=false / Publish=false.

## Reproduce

From src/Rigarus.Backend, locked Python3.13 / uv0.10.12:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -p "test_driver*.py" -v
uv run --locked python -m unittest discover -s tests -q
```

The borrowing test creates actual source members (Employee1 active approved,
Employee2 suspended) and destination Employee3 suspended. Before borrowing,
source=Satisfied, destination=Blocked; after moving Employee1 in the immutable
projection, source=Blocked, destination=Satisfied; publication remains false.
The Store-backed fixture records actual dated company evidence, reloads SQLite
and demonstrates Pending→Satisfied→Blocked→Pending on missing, Active, Suspended
and Unverified respectively. The existing Employee flag remains Unverified.

## Actual validation

Connected Windows11 developer host build26200, developer tools present, temporary
synthetic DBs. No native GUI or physical disconnected installation exercised.

| Gate/scenario | Result |
| --- | --- |
| New driver tests | PASS, 27 (14 pure + 13 Store/snapshot), includes 4,000 shared-worker assessments |
| Full backend | PASS, final 235 tests in 56.031s including explicit company-confirmation cells |
| Locked Python/Ruff | PASS, uv0.10.12 / Python3.13.7, lock unchanged; 66 files |
| Packaged sidecar | PASS, PyInstaller build + 11 persistence/restart/upgrade tests, 18.441s; internal validator unconnected to UI |
| Frontend | PASS, npm ci/Prettier/35 tests/TypeScript-Vite; initial npm PowerShell wrapper failed, npm.cmd rerun passed without lock change |
| Rust | PASS, 1.95.0 fmt/locked fetch/Windows Release and 8 tests |
| Historical .NET | PASS, locked restore/format/Release build and 35 tests (16/2/17) |
| Synthetic acceptance harness | PASS; not a native app run |
| Borrowing/collision/cancel/local AM-PM/year/leap/DST | PASS; source and destination checked, no date carry or UTC conversion |
| Missing/Unverified/unknown/inactive/unavailable | PASS; no missing-evidence success or roster inference |
| Stale/no-op/reference/history/FK/concurrent writers/partial rollback | PASS |
| Schema10 preservation/failure/retry/idempotence | PASS, integrity/FKs retained; legacy rollback regressions preserved |
| Consistent WAL/staleness/detached purity/logical no-write validation | PASS |
| Staged privacy/docs/whitespace | PASS, 267 indexed paths; staged whitespace and changed-document links/fences checked |
| Final-head Windows CI | Pending push/PR; final PR/Issue records SHA/run/jobs/artifact |
| Native GUI/disconnected install/upgrade/reboot | NOT RUN |
| Customer Demo D/E/UAT | NOT RUN |
| Production | NOT APPROVED |

Initial regression failures exposed test-only schema reconstruction leaving
newer tables/history and two hard-coded migration counts. Updated those fixtures
to reflect schema11 while retaining original data/rollback assertions. No
production safeguard was bypassed to make tests pass.

## Remaining

Company approval authority, actual legal/category requirements and approval
management UI require confirmed design/policy. No actual Rig/category evidence
is inferred; Satisfied is scoped to company-driver evidence only. Complete
proposed membership, #25 staffing/skills/qualifications, #24 actual Rig/maintenance,
#27 actual-worker weekend consent; #18/#29 Preview/locks/transaction revalidation/
human Apply/rollback/audit and final publication gates remain. No merge, Release
or Issue closure; human review and customer acceptance are separate.
