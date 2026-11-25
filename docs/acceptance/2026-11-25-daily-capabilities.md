# Issue109 — Daily staffing, Level and separate qualifications (2C3)

Delivery baseline main `15879cd72832e9a90047220f184684fb819c822e`, human merge
PR108, main CI45553296541 success. Branch codex/daily-capability-validation.
Original pre-code Design-First commit07e8303, rebased unchanged plan c9f9801.
Initial main was a179b91 with108 unmerged at0634276; human merge occurred during
implementation. Baseline product tree is identical; PR targets main directly.
[Source inventory/plan](../design/2026-11-25-daily-capabilities-checklist.md),
[owner scope](../10-CLIENT-DECISIONS.md),
[synthetic example](../../samples/synthetic-only/daily-capabilities.md).
PUBLIC repository, Windows developer host10.0.26200.0, networking active,
synthetic temporary profiles only. Raw diagnostics/databases/backups/binaries and
local original DOCX remain ignored/local. No real customer database opened.

## Delivered behavior and limits

- Independent full-date WorkItem requirements and Employee exact-code qualification
  assertions, additive schema16. Reuse immutable capability owner identities;
  separate daily history/cells have no Slot. Explicit company/full-day confirmation,
  reference, revision/range token and retained legacy review receipts. Strict
  payload/context parsing, immutable history, atomic save/no-op/rollback.
- Requirements reuse explicit positive minimum, all Level1/2/3 minima, explicit
  Exact/AtLeast and explicit qualification-code/count list. No company threshold,
  certificate/Level equivalence, disjoint-role allocation or legal default. An
  explicit empty code list differs from missing policy; null/Unknown tombstones
  never resurrect old positives.
- Old half-day/full-day legacy positive policy/proof never certifies a day.
  Unreviewed/stale NotVerified remains negative; only fresh explicitly reviewed
  daily Verified supersedes it without rewriting old history. Native old revision
  and per-date receipt expire positives after later edits, including outside range.
  Missing/stale policy stays Pending, never silently inherits an old policy.
- Pure daily actual-worker validation indexes confirmed/possible capacity per
  minimum, Level and exact qualification. Active/daily Available/collision-clear
  complete context gives confirmed capacity; unknown evidence only possible;
  inactive/Unavailable/colliding people do not count. Known possible upper bound
  below the explicit requirement is Blocked, enough definite satisfies only that
  subcheck, otherwise Pending. Configured zero is known zero; unconfigured/legacy
  half-day roster has no proven whole-date upper bound and remains Pending.
- Same pinned query-only snapshot now captures all related target/source WorkItem
  policies, employee code owners/revisions/proofs/legacy receipts and existing
  member/driver/availability data. Format v4/SHA256, rebuild v3 proofs. Same-query
  Current/Stale detects consumed changes; errors never fabricate Current. Shared
 100,000 read/evaluation units/deadline,64MiB SQL/projected-text and250,000-character
  retained legacy source limits prevent unbounded payload amplification.
- Detached proposal uses exactly PR108 before/after rosters and source override
  ID/kind/revision/date context. Reports preserve target/source Project/WorkItem/
  Crew/record identities and counts. Source member, Level or qualification loss
  blocks even with drivers valid on both sides. No implicit source removal.
  Qualified explicit replacement satisfies these subchecks only. PR91 receives
  both-Crew CrewType/MinimumStaffing/Skills/Qualifications states, preserves prior
  personnel/driver blockers and stable date sorting. Unrelated saved failures stay
  visible separately from candidate state. Proposal SHA binds normalized existing
  driver/member/source proof plus the daily capability contract.
- Root validation always Pending / Apply=false / Publish=false. Whole-roster
  availability, Foreman effective-date/promotion/merger policy, actual Rig,
  actual-worker weekend consent and operator review remain independent Pending.
  No Home Crew inference, saved transfer/staffing edit, API/UI/dependency change,
  authenticated/legal approval claim, Apply/Publish/export or production gate opening.

## Actual engineering verification

Python3.13.7 / uv0.10.12 locked bundle27 installed packages; Node22, Rust1.95.0,
.NET10. Reproduction uses repository build scripts and locked environments.

| Check | Actual outcome |
| --- | --- |
| Python locked restore / Ruff check/format | PASS;106 Python files |
| Full backend | PASS **473**, no skips (438 baseline +35 new); first full472 before final availability case also passed |
| Focused daily capability | PASS **35** (14 pure,17 integration,3 migration,1 legacy guard) |
| Packaged sidecar build/actual exe regression | PASS **13** repeated source-sidecar tests |
| Frontend locked npm ci / Prettier / tests / TypeScript/Vite | PASS **42** |
| Locked Rustfmt/fetch / Windows Tauri no-bundle build / release tests | PASS **8** |
| Historical .NET locked restore/whitespace/Windows build/tests | PASS **35** (16+2+17), build0 warnings/errors |
| Synthetic console example | PASS; source member/Level shortage blocks despite driver pass; replacement subchecks clear but full Pending; proof Current→Stale after certificate edit |
| Windows PowerShell5 synthetic harness | PASS; mock controls/timeouts, consistent SQLite checks; not native/offline GUI acceptance |
| Actual prior15→16 packaged sidecar migration/backup/rejection/recovery | PASS, below |
| Staged privacy/diff and nine affected UTF-8 Markdown/link/fence checks | PASS;330 indexed paths, clean diff and nine source/link/fence checks |
| Exact-head Windows CI/installer/offline-kit build/upload | NOT RUN before push; final Draft PR records actual run/head/jobs/artifact |
| Production daily writes | BLOCKED intentionally; same default-closed gates, no daily capability HTTP/UI writer |
| Native daily GUI/Locate, disconnected installation/upgrade/reboot/clean-device, customer Demo D/E/UAT/production approval | NOT RUN; networking active, no GUI/install/customer acceptance performed |

Distinct regression inventory **558** =473+42+8+35. Packaged13 repeat coverage,
not additional distinct tests; synthetic example/harness/recovery are extra checks.
First focused run corrected one test indexing Level1 minimum0 instead of Level2
minimum1; the product correctly satisfied the explicitly configured zero minimum.
No rule/constraint was weakened. Existing schema assertions updated to16/v4,
preserving all original data assertions. Review added payload byte budgets.

Pure14 groups cover explicit/missing policy, member shortages, all three Exact
levels and explicit AtLeast, qualification independence/states/exact codes,
overlapping independent requirements, unknown/Unavailable/inactive/master context,
configured zero/unconfigured/no active, legacy partial attendance/scope gaps,
daily personnel/cancellation, Crew/parent context, strict duplicate/invalid/bounded
inputs, deterministic frozen no-file/socket/SQL/time calls and cross-year/leap/
DST/final local date. Core indexes evidence then checks bounded member/code counts;
no employee-pair comparisons. Evaluation workload capped100,000.

Integration17 groups cover persisted policy/certification/no-op/reference/history/
reopen, both old halves never promotion, negative/review/Unknown/reinstatement,
legacy outside/inside-range expiration, explicit null policy, half availability,
SQL history/context/range rollback, revision/token/concurrent writers/source edit,
strict owner/confirmation/date inputs, source minimum loss, independent source
Level loss, source unique qualification loss despite driver pass, missing versus
verified source proof, legacy borrowing/revision checks, proposal/input SHA/Stale,
coherent pinned old view during policy/proof changes, detached logical immutability
and row/byte budget failure. Migration3 cover full preservation/verified backup/
reopen, injected DDL/history/backup failure rollback/retry, and read-only15 rejection
without initialization. Legacy guard rejects daily Unknown and expires prior proof.

## Actual packaged migration and independent recovery

Actual previous schema15 sidecar (PR108) created a temporary fictional profile.
Seeded independent AM/PM visits/WorkItems/notes, mixed old calendar, partial old
availability, old Suspended driver proof, explicit daily availability, day Draft
with actual members, independent daily company-driver assertion and old FullDay
policy/qualification proofs. Actual new sidecar startup upgraded to16. Every
original table row/type/ID/relationship/note/revision/history/sequence was compared;
only additive tables and appended migration history differ. Integrity/FKs passed.
Production daily input/day Draft writes remained409; compatibility converted0.

Verified pre-DDL backup logically equals the complete15 database. Actual15 binary
refused16 without logical mutation; independent recovery through SQLite backup
reopened with actual15 binary and exact original visits/logical equality. No live
downgrade, history deletion or customer database. Fault-injection tests separately
verify transaction rollback/backup failure/retry; native installer upgrade remains
NOT RUN.

- Previous sidecar SHA256: `e2d5d1aae179b6f0202dbcf403ad675d96442db5729a7f64b9b00547f605fc66`.
- New sidecar SHA256: `ff9890d4559c344de58db7f780bc9cb027650be97f0d634763d3ee80db603c9c`.

## Remaining work and decisions

Next #24 actual Rig dated occupancy/maintenance/inspection, then #27 consent from
actual weekend workers. Later visible daily UI/Locate/native offline acceptance
and #18/#29 Preview/locks/transaction revalidation/manual Apply/audit. Foreman
effective-date/merger/promotion/presence policy, company thresholds/authority,
qualification legal meaning/equivalence and historical reconciliation still need
designated owner/customer decisions. No green driver/capability subcheck accepts
Demo D/E or production. Human review only; keep109/25/99 and dependencies Open,
no automatic merge, Release or real-data upload.
