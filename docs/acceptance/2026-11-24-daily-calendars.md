# Issue101 — Daily calendar/availability input foundation

Baseline main `947da5f6a6fd326592f09f34be26370bfcea47b7` (merged PR100).
Branch `codex/daily-calendars-availability`; pre-code design commit `a1bbf4b`.
See [source inventory/plan](../design/2026-11-24-daily-calendars-checklist.md),
[owner decision](../10-CLIENT-DECISIONS.md) and
[reproducible example](../../samples/synthetic-only/daily-inputs.md).
This delivers **slice2A backend inputs**, not the whole second slice or day UI.

## Delivered behavior

- Slotless explicit Crew/Project daily Working/NotWorking/Unknown and Employee
  Available/Unavailable/Unknown (Not recorded). WorkItems inherit persisted Project.
- Independent additive schema14: immutable owners/revision events/current cells.
  No old row, ID, Slot, revision, note, relation, history or sequence is rewritten.
- One pinned read-only range, bounded to366 dates. No defaults or positive legacy
  promotion. Raw mixed/partial evidence and known negatives remain Needs Review.
- Explicit new daily assertion requires operator confirmation and matching exact
  range revision/review token, plus acknowledgement when raw legacy cells exist.
  It may deliberately supersede old negative evidence for daily use after review;
  original values stay visible and unchanged. Token is not approval authentication.
- Per-date review receipt binds raw legacy evidence/change IDs and native owner
  revision. Later legacy edits (even out of range conservatively) invalidate prior
  daily positives; negatives remain blockers. Re-review appends history. Explicit
  Unknown stays stored, never resurrecting old positive halves.
- BEGIN IMMEDIATE protects current revision/receipt, event append and entire
  range. Concurrent writers produce one success/one conflict; no-op keeps revision.
- Separate strict daily read/save/history/assessment API; no new slot input.
  **Production daily-input and day-Draft writes default closed**. Only explicit
  app-factory synthetic test opt-in enables daily input writes; no Rust/UI wiring.
- Legacy half-day recommendation reader recognizes14 but refuses any in-horizon
  daily cell, including Unknown. Previous inputs report Stale with
  DAILY_CALENDAR_ADAPTER_REQUIRED; guard shares pinned read. Out-of-horizon daily
  cells do not alter legacy scope. No day generator is claimed.
- Calendar Matched remains resource Validation Pending / Apply=false / Publish=false.
  Actual staffing, employee eligibility, driver, Rig and weekend consent are not inferred.

## Actual automated checks

Windows developer host, networking active, synthetic temporary profiles only.
Python3.13.7/locked uv bundle environment, Node22, Rust1.95.0, .NET10.
Raw diagnostics and databases/backups remain in ignored local storage.

| Check | Result | Evidence/coverage |
| --- | --- | --- |
| Locked Python bundle restore; Ruff check/format | PASS |27 locked packages;83 Python files formatted |
| Full backend suite | PASS |324 tests (295 baseline +28 daily tests +1 sidecar test); no skips |
| Packaged Windows sidecar | PASS |13 authenticated loopback tests, restart and default write gates; same tests also included in backend total |
| Frontend locked npm ci/Prettier/tests/TypeScript/Vite | PASS |42 tests; unchanged UI/source, zero npm audit findings at execution |
| Rustfmt/locked fetch/Windows Tauri no-bundle release build/Rust tests | PASS |8 readiness/error/path tests; matching packaged sidecar |
| Historical .NET locked restore/format/Windows build/tests | PASS |35 tests:16 Domain +2 Application +17 Infrastructure |
| Schema13→14 backup, rollback, retry, idempotence | PASS |All logical rows including old AM/PM different WorkItems, single-half availability, daily Draft and history/sequence preserved; integrity/FKs clean |
| Actual packaged13→14 and independent backup reopening | PASS |Detailed recovery below; not an installer or disconnected upgrade |
| Synthetic PowerShell acceptance harness | PASS on isolated rerun |First run failed an unchanged one-second Project protocol timing case during concurrent builds; no harness code changed; does not represent actual native GUI/offline acceptance |
| Staged privacy and diff/document checks | PASS |295 indexed paths scanned; staged diff clean;9 affected Markdown sources UTF-8/fences/local links checked; no originals/DBs/logs/binaries staged |
| Exact-head Windows CI, three jobs and artifact upload | NOT RUN at evidence commit |Final Draft PR records actual run URL/head/outcomes; no CI success inferred from local checks |
| Native day GUI/control removal/Locate interaction | NOT RUN |No day UI in this slice |
| Disconnected installer/upgrade/reboot/clean-device acceptance | NOT RUN |Networking remained active; no installation or NIC isolation performed |
| Customer Demo D/E/UAT/production approval | NOT RUN |Engineering checks are not customer acceptance |

Distinct automated unit/integration tests:409 (=324+42+8+35); packaged13 repeats
source-sidecar coverage and is not added as new distinct tests. Synthetic harness
and packaged recovery probes are additional checks, not counted as unit tests.

The initial full backend run had one failure in an existing aggregate evidence
budget test: schema14 has more than its artificial25-table limit, so metadata
stopped the test before qualification rows. The test now isolates schema metadata
to preserve its intended aggregate qualification-budget assertion. Targeted16 and
final full324 passed. No runtime evidence limit was increased. An initial local
recovery probe used an incorrect employee field (`level`); corrected to the
existing `skill_level` contract and rerun on fresh synthetic files. No product
API relaxation was introduced.

## Daily acceptance cases (28 focused tests)

Missing inputs stay Unknown without writes; positive pair/single-half legacy does
not become daily Working; mixed negative blocks; raw values retained; explicit
review required; old edits invalidate receipts; re-review retains both snapshots;
Unknown tombstone stays Unknown; daily negative remains blocking; employee mixed/
partial/clear states remain separate from Crew/Home Crew; Civil/Tower IDs inherit
the same parent; weekends keep consent Pending; Crew/Project closure blocks.

Scope/ID/range/revision/legacy-token mismatches conflict. Strict API rejects slot,
coerced booleans, unconfirmed assertion, wrong scoped state and bad dates. Range
failure rolls back event/cells/owner; ownership/history immutable; composite FK,
scope and event-date constraints hold. Invalid legacy source context fails closed.
Reopen/no-op/history/read logical equality pass. Concurrent writers cannot both
commit; pinned daily and inherited assessments never mix later daily/old edits.
Legacy recommendation snapshots similarly retain complete pinned inputs then
report the specific Stale reason after close. Pure resolution/contract does no
file/network/SQL I/O; local cross-year, leap/DST,366-date limit and invalid values
are tested. Existing full regressions cover preserved daily occupancy safeguards.

## Actual packaged recovery

An actual previous schema13 packaged sidecar created synthetic Projects/Crew,
two different AM/PM WorkItems, mixed Working/NotWorking and AM-only Available.
After shutdown, new packaged startup upgraded to14. Every original table's logical
rows (history prefix except its new migration row) and sqlite_sequence matched.
No legacy conversion occurred; daily reads reported negative Needs Review and
partial availability Unknown; both production write gates remained closed.

Pre-upgrade backup's complete schema/rows/types/history/sequence digest equalled
the original source. The actual schema13 binary refused14 without changing its
logical digest. SQLite backup into an independent synthetic path reopened with
the schema13 binary and matched all original visits and logical digest.

- Previous sidecar SHA256: `6c6f62641fd636a3032b821ff7dc983c911d30918cc5108f9e697f4ac9ac9bb5`
- New sidecar SHA256: `5c3bcdd84950e860a60523af04f3eabe7a10f8682a7daa87f6997343eeafd0ae`

No operational downgrade/history deletion is offered. Transaction rollback and
backup/disk failure/retry use synthetic fault injection. Real customer database
conversion still requires separate reviewed operator workflow and local recovery.

## Remaining dependency order

1. Daily confirmed Remaining Days + pure day allocation/comparison, full consistent
   daily snapshot/fingerprint/Stale checks; no half-day estimate rounding/deduction.
2. Daily actual-member #15 collisions, whole-day #23 driver evidence and #25
   minimum/skills/separate qualifications. Existing half-day safety proofs do not
   certify daily eligibility. Missing evidence Pending; known blockers Blocked.
3. Actual Rig occupancy/maintenance/inspection #24 and actual workers' weekend
   consent #27, without inferred Rig/driver/Home Crew attendance.
4. Daily Working Calendar/Availability and Schedule/Crew Board/Employee Week UI,
   visible review and accurate Locate; native/offline upgrade acceptance. Only
   then consider opening protected daily writes with complete integration.
5. #18/#29 Preview/locks/transactional revalidation/manual Apply/audit. No automatic
   Apply/Publish/export/distribution, Release or customer acceptance in this PR.

Keep101/99/22/26/28 and other dependencies Open; Draft PR/human review only.
