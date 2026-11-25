# Issue107 — Daily company-approved drivers (2C2 / #23)

Baseline main `a179b916baa683e743180b80f4f57e28acae2ab5`, human merge PR106.
Branch `codex/daily-driver-validation`; pre-code design commit `5f3f218`.
[Source inventory/plan](../design/2026-11-24-daily-drivers-checklist.md),
[decision register](../10-CLIENT-DECISIONS.md),
[synthetic reproduction](../../samples/synthetic-only/daily-drivers.md).
Executed November25 UTC on Windows developer host (10.0.26200.0), networking
active. PUBLIC repository, synthetic temporary profiles only; originals, raw
diagnostics, backups, profiles and binaries stay local/ignored.

## Delivered scope

- Independent slotless DailyDriverApprovalDraft requires company and full-day
  confirmation, exact bounded dates and a reference. Revision/range-token-protected
  internal recorder preserves immutable history, Unverified tombstones, raw old
  approval observations and per-date legacy receipts. No HTTP/UI writer.
- Neither old AM/PM Active nor an old FullDay event proves a new complete date.
  Unreviewed/stale old Suspended/Expired blocks. Fresh explicitly reviewed daily
  Active may supersede it for new use; old values/history remain untouched.
  Legacy edits, even out-of-range native revision changes, invalidate positives.
- Pure actual-member driver check requires current full-date company Active,
  active Employee, full-date Available and complete collision-free context.
  Missing/Unverified/stale/half-day evidence Pending; known ineligible cannot
  count. One eligible member satisfies driver only; all known ineligible Blocked.
  Missing roster Pending, explicit zero roster known driverless/Blocked. Old
  attendance remains partial/Pending even with new daily approval. No inference
  from Home Crew/Foreman/Rig/available status, and Cancelled releases capacity.
- Coherent schema15 daily snapshot v3 includes new/raw old approval sources,
  revisions, history IDs, references and receipts in the same pinned query-only
  transaction/read budget. SHA256/Current-Stale bind consumed sources and explicit
  observed employees. Source errors never fabricate Current or a safe empty view.
- Saved driver report remains distinct from unstaffed proposals. Detached driver
  preview binds an exact generated plan and normalized proposed/date members.
  Explicit SourceDayMembers matches stable namespaced saved ID/revision/date and
  borrowed-worker context. It replaces only detached staffing, never saved data.
  Before/after, target and source checks remain visible. No override means source
  still occupied/Blocked. Sole-driver removal blocks the source; verified source
  replacement can satisfy these subchecks. A replacement's third-Crew personnel
  conflict still blocks the option even with another eligible source driver.
- PR91 daily comparison receives source-and-target PersonnelConflicts and
  ApprovedDriver states, excludes known blockers and preserves stable date sorts.
  Unknown source/target proof Pending; proposal SHA binds input/options/members/
  overrides. Entire-roster availability, minimum/skills/qualifications, Foreman,
  actual Rig, consent and operator review remain independent Pending.
- Every root report is Validation Pending / Apply=false / Publish=false. Both
  production daily write gates remain closed. No UI, HTTP/transfer/Apply/Publish/
  export path, automatic staffing selection, customer DB or existing API change.

## Actual engineering checks

Locked Python3.13.7/uv0.10.12 bundle27 installed packages, Node22, Rust1.95.0,
.NET10. No dependency/lockfile change. Commands use the repository scripts and
locked environments; packaged checks use the actual generated sidecar executable.

| Check | Status and evidence |
| --- | --- |
| Python locked restore / Ruff check and format | PASS;99 Python files |
| Full backend | PASS **438**, no skips (394 baseline +44 new) |
| Focused daily-driver suite | PASS **44**:16 pure +24 integration +3 migration +1 legacy guard |
| PyInstaller sidecar build and actual packaged regressions | PASS **13** repeated source-sidecar checks |
| Frontend locked npm ci / Prettier / tests / TypeScript/Vite | PASS **42** |
| Locked Rustfmt/fetch / Tauri Windows no-bundle build / release tests | PASS **8** |
| Historical .NET locked restore / whitespace / Windows build / tests | PASS **35** (16+2+17), build0 warnings/errors |
| Synthetic console example | PASS; no-removal and sole-driver removal Blocked, explicit replacement subchecks Satisfied/full Pending, Current→Stale after driver edit |
| Windows PowerShell5 synthetic acceptance harness | PASS; mock controls/timeouts and logical SQLite checks, not native/offline GUI acceptance |
| Actual packaged14→15 upgrade / old-binary rejection / independent backup recovery | PASS, detailed below |
| Staged privacy, diff and affected Markdown UTF-8/fences/relative links | PASS;320 indexed paths and9 affected Markdown sources |
| Exact-head Windows CI / installer and offline-kit build/upload | NOT RUN before push; final Draft PR records actual head/run/jobs/artifact result |
| Production daily writes | BLOCKED intentionally; unchanged default-closed gates and no driver HTTP writer |
| Native daily GUI/Locate, disconnected installation/upgrade/restart/clean-device, customer Demo D/E/UAT and production approval | NOT RUN; no GUI/installation/UAT performed, developer host networking active |

Distinct executed regression inventory **523** =438+42+8+35. Packaged13 repeat
existing source-sidecar tests, not extra distinct coverage. Examples/harness and
prior-binary recovery are extra engineering checks, not unit counts.

Focused pure16 cover actual single/multiple workers; all approval states, missing
dated proof, company/full-day/current receipt requirements, daily availability,
inactive/missing master, old attendance and opposite halves/day collisions,
alternative eligible driver versus personnel failure, unknown alternative versus
all known ineligible, configured zero/unconfigured/no active, cancellation and
partial/unknown scope, strict malformed/duplicate/bounded input, cross-year/leap/
DST/final local date, frozen deterministic no-file/socket/SQL calls,1000 independent
Crews and1000 colliding employees. Per-visit conflicts use set lookup; grouping is
bounded/indexed rather than employee-pair scanning.

Integration24 cover persisted/no-op/reference/history/reopen, raw old half and
old FullDay never promotion, legacy negative/review/Unknown/stale, conservative
outside-range revision, half availability, states/range/tombstone, revision/token
concurrent writers and source edits, SQL history/context guards and full range
rollback, invalid contracts/missing employee, old attendance, cancellation, explicit
source/destination/third-Crew checks, no implicit transfer, sole-driver loss,
replacement/unknown/legacy attendance, strict source identity/revision/plan,
missing/empty target, fingerprints/freshness, pinned old view during concurrent
approval/availability edits, detached purity/logical no-writes and read limits.
Three migration cases cover preservation/verified backup/idempotence, injected
DDL/history and backup failure rollback/retry, and read-only14 rejection without
migration. Legacy guard rejects even daily Unverified and expires old proofs.

Initial full regression found9 obsolete schema-count/latest-migration/v2-format
expectations; updated to15/v3, preserving original data assertions. First new
test run found fixture ID/schema-exception/query-scope assumptions and an overly
optimistic target expectation when source is explicitly empty. Corrected tests
to existing conservative2C1 semantics. Review added source replacement personnel
collision protection and indexed conflict lookup; final gates above passed.

## Real packaged migration and recovery (synthetic only)

The actual previous schema14 sidecar from PR106 created a temporary fictional
profile. Seeded AM and PM visits with independent WorkItems/stable IDs/notes,
mixed legacy calendar, partial employee availability, old PM Suspended driver
evidence, daily availability and a separate day Draft/current actual members.
The actual new packaged startup upgraded to15. Every original table row/type,
ID, relationship, note, revision/history/sequence was compared exactly; only
migration history appends/new tables differ. FK and integrity checks passed.
Daily input/day-Draft production writes still return409; mixed/partial evidence
remains conservative, compatibility converted_records=0.

Verified pre-DDL backup logically equals the entire14 database. Actual14 binary
refused15 without logical mutation. Restored a separate database through SQLite
backup from that recovery point; actual14 sidecar reopened it and all visits
matched, with exact logical equality. Live15 was never downgraded or history
deleted. Unit fault injection separately verifies transactional rollback/retry.

- Prior sidecar SHA256: `b44659269b039892431ea023740f9f84b55595cff0877aada167dafdf8a5ca68`.
- New sidecar SHA256: `e2d5d1aae179b6f0202dbcf403ad675d96442db5729a7f64b9b00547f605fc66`.

This is packaged sidecar/SQLite recovery on a connected developer host, not an
installer, native GUI, physical reboot or disconnected customer upgrade pass.

## Remaining scope and decisions

#25 daily actual minimum members, explicit Level policy and independent verified
qualifications must recheck both source and target. Then actual #24 Rig dated
occupancy/maintenance/inspection and #27 actual-worker consent; no default Rig or
weekend approval. Later visible daily UI/Locate and #18/#29 Preview/locks/
transactional revalidation/manual Apply/audit. Company approval authority,
category/legal/expiry policy and historical reconciliation remain customer/owner
decisions, not defaults inferred by this slice. Human review only; keep107/23/99
and dependencies Open, no automatic merge/Release. Demo acceptance and production
approval remain separate and pending.
