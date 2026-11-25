# Issue111 — Actual daily Rig safety and read-only swaps (#24)

Baseline main `afcb504a80eb77962d1f221316893d991b3c76d8`, human merge110;
main CI45558589366 succeeded. Branch codex/daily-rig-validation, pre-code plan
commit152eae5. [Source inventory/design](../design/2026-11-25-daily-rigs-checklist.md),
[owner scope](../10-CLIENT-DECISIONS.md),
[synthetic example](../../samples/synthetic-only/daily-rigs.md).
PUBLIC repository, Windows developer host10.0.26200.0, networking active; only
synthetic temporary profiles. Original designs, raw logs/profiles/backups/binaries
remain local/ignored. No real customer database was opened.

## Delivered behavior

- Explicit original/actual Rig per stable day/legacy visit; default link never
  actual capacity. Saved operational evidence requires company/full-date/reference,
  assignment/allocation revisions and caller-reviewed native condition revision.
  Legacy observation is partial occupancy, never full-date readiness.
- Independent Maintenance/Inspection/OutOfService periods and immutable events;
  cancelling one cannot clear another. Inactive master/active conditions override
  positive assertions. Condition changes invalidate readiness even outside horizon;
  clearing all blocks still requires explicit reconfirmation.
- Additive schema17 four tables/four views, immutable ownership/history, context/
  original/readiness/collision guards and indexes. Concurrent same-Rig/date across
  Crews rejects; saved visit move/restore cannot bypass SQL. Old halves reserve
  a whole date for new daily safety, same-Crew old halves retained; Cancelled frees
  capacity. Existing Crew/day/legacy guards remain intact.
- Stale allocation reserves recorded/current dates/Crews until review, including
  a current visit moved outside horizon. Recorded WorkItem/Project IDs stay distinct
  from current identities in conflict diagnostics. No historical record is rewritten.
- Pure indexed checks: known condition/master/occupancy blocker Blocked; missing
  actual/full-date/scope/context or stale evidence Pending. Unknown other-Crew
  allocation cannot yield a clear check. Projection/occupancy/assessment capped
 100,000, no employee/Crew pairwise comparison or file/network/SQL/clock in core.
- One pinned query-only snapshot v5 includes nominees, saved/stale allocation
  context, original/actual/default/nominee masters, periods/native revisions and
  existing personnel/driver/capability/calendar data, within row/byte/deadline
  limits. SHA256/Current-Stale covers consumed observations; rebuild v4. Legacy
  reader refuses relevant Rig evidence. Reads never initialize/migrate16. Current
  is scoped logical equality, not a lock or Apply authority; errors never mean safe.
- Candidate Rig choices reuse exact prior worker/borrowed-source checks. Both
  source and target Rig states enter PR91 RigAvailability/RigConflicts; source
  hardware blocker excludes even when target passes. Missing/uncaptured/date gaps
  Pending, stable sort retained. Saved swap preview checks exact source revisions,
  keeps before/after/original identity, labels Proposed evidence and never writes.
  Planning operational assertions/reference bind choice/input SHA, not saved approval.
- Generic approved driver or free-text Rig.Type never proves selected vehicle
  category eligibility. Category/legal/inspection due-date/authority policy remains
  unresolved; no legal certification inferred. All root Validation Pending /
  Apply=false / Publish=false. No new Rig HTTP/UI writer, staffing edit, published
  history change, production gate opening, Apply/Publish/export or actual transfer.
  Existing legacy Draft move reports known Rig collision409 instead of storage503.

## Actual engineering verification

Python3.13.7/uv0.10.12 locked bundle27 packages, Node22, Rust1.95.0 and .NET10.
No dependency/lockfile change. Developer Windows host connected to networking.

| Check | Actual outcome |
| --- | --- |
| Locked Python restore / Ruff check/format | PASS;113 Python files |
| Full backend | PASS **512**, no skips (473 baseline +39 new); earlier507/511 runs passed before final added cases |
| Focused Rig suite | PASS **39** (14 pure,21 integration,3 migration,1 legacy guard) |
| PyInstaller / actual packaged sidecar | PASS **13** repeated source-sidecar tests |
| Frontend locked npm ci / Prettier / tests / TypeScript/Vite | PASS **42** |
| Locked Rustfmt/fetch / native Tauri no-bundle build / release tests | PASS **8** |
| Historical .NET locked restore/format/Windows build/tests | PASS **35** (16+2+17),0 warnings/errors |
| Synthetic console example | PASS; busy replacement Blocked, released replacement only Rig subchecks Satisfied/Proposed, SQLite actual unchanged, generated unstaffed dates Pending, condition edit Stale |
| Windows PowerShell5 synthetic harness | PASS; mock controls/timeouts/SQLite, not native/offline product acceptance |
| Actual prior16→17 packaged sidecar upgrade/rejection/independent backup recovery | PASS, below |
| Staged privacy/diff / nine UTF-8 Markdown/fence/link checks | PASS;340 indexed paths, clean diff and nine source/link/fence checks |
| Exact-head Windows CI / installer/offline-kit build/upload | NOT RUN before push; final Draft PR records actual run/head/jobs/artifact |
| Production daily writes/Rig HTTP writer/manual Apply | BLOCKED intentionally; gates default closed, no new writer/Apply path |
| Native daily GUI/Locate, disconnected install/upgrade/reboot/clean-device, customer Demo D/E/UAT/production approval | NOT RUN; no product GUI/install/customer acceptance, networking active |

Distinct inventory **597** =512+42+8+35. Packaged13 repeat coverage, not additional
distinct tests; examples/harness/recovery are extra checks. This internal evidence/
calculation/snapshot slice does not claim a new Rig validation HTTP/GUI workflow.

Pure14 groups: explicit actual/subcheck-only pass, default/original not actual,
cross-Crew dated conflict/all refs, different resources/cancellation/no active,
legacy/same-Crew halves, independent conditions/partial cancellation, inactive
actual versus inactive original replacement, missing/scope/unknown-other-Crew/
known-block precedence, stale native/context/outside-horizon recorded claim,
invalid/duplicate/bounded inputs, local year/leap/DST/final date/frozen deterministic
no-I/O/time, projection bound and1000-resource/shared-Rig indexed grouping.

Integration21 groups: default ambiguity, explicit original/actual/no-op/history/
reopen, cross-Crew/different Rig/cancel/restore, old halves, condition independence/
reconfirmation, inactive/out-of-service, reviewed-native race, concurrent writers/
identity rollback, legacy API409, stale move/reservations/review/outside horizon,
original/current WorkItem/parent provenance, immutable revisions/fault rollback,
period identity/no-op/contracts, candidate missing/explicit/blocked Rig, borrowed
source hardware blocker, invalid query/choices, source swap/no-write, busy/uncaptured/
stale swap, coherent pinned conditions/SHA/Stale/limits/detached immutability.
Migration3: full16 preservation/verified backup/idempotence, injected DDL/history/
backup failure rollback/retry, query-only16 rejection without initialization.
Legacy guard refuses condition facts and expires old half-day proof.

Two first-run pure fixtures constructed positive readiness before replacing absent
actual Rig; fixed fixtures, retaining strict rejection. Review added explicit Saved/
Proposed provenance and recorded project-context regression. Existing assertions
updated to17/v5 while preserving old data checks; no safety rule was weakened.

## Actual packaged migration and recovery (synthetic)

Actual previous16 sidecar from PR110 created old AM/PM visits with different work
items/notes, mixed old calendars, partial availability, old driver evidence, daily
availability/day members, daily driver and daily/old policy/qualification history.
Rig inventory included leading-zero0007/0008, notes/default Crew, active/inactive.
Actual new17 startup upgraded it; every original table row/type/ID/relation/note/
revision/history/sequence was compared. Only additive schema/history differs.
FK/integrity passed; daily input/day Draft writes stayed409, conversion count0.

Verified pre-DDL backup logically equals the complete16 source. Actual16 binary
refused17 without logical mutation. Restored a separate file through SQLite backup,
opened with actual16 sidecar, and verified exact original visits/logical equality.
Live17 retained; no downgrade/history deletion. Recovery point excludes later17
edits, requiring separate retention/reconciliation. Unit fault injection separately
checks rollback/retry and backup failure. This is connected-host packaged sidecar/
SQLite recovery, not native installer/offline/reboot/customer acceptance.

- Previous sidecar SHA256: `ff9890d4559c344de58db7f780bc9cb027650be97f0d634763d3ee80db603c9c`.
- New sidecar SHA256: `2fbdf4a7420632ca72c74642d45edc94cc1babedbef693de673e055a4d979efd`.

## Remaining scope

Next #27 consent from actual weekend workers, rechecking source/destination after
borrowing; Available/Home Crew never means consent. Then daily desktop UI/visible
recommendation preview/safe human Apply, version history and PDF/Excel. #18/#29
must bind Preview/locks, transaction revalidation and audit. Category/driver,
legal/inspection/approval policy, Foreman and historical reconciliation remain
explicit follow-up, never defaults from examples. Published actual-Rig display/full
Issue24 Demo D remain unimplemented/unaccepted. Keep111/24/99/dependencies Open,
human review only, no automatic merge/Release or customer-data upload.
