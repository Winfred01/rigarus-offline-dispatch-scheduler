# Issue113 / #27 — Full-day actual-worker consent

Baseline main3d87b27e306b9a3617fe7fcbc433ef333807ba89, human merge112;
main Windows CI45572428803 succeeded. Re-fetched main unchanged before delivery.
Branch codex/daily-weekend-consent; pre-code plan f966ad7.
[Design/source inventory](../design/2026-11-25-daily-weekend-checklist.md),
[owner scope](../10-CLIENT-DECISIONS.md),
[synthetic reproduction](../../samples/synthetic-only/daily-weekend.md).

PUBLIC repository. Windows developer host, networking active, Python3.13.7,
uv0.10.12, Node22, Rust1.95.0, .NET10. Synthetic temporary profiles only; original
designs/raw logs/profiles/backups/binaries remain local/ignored. No customer
database was opened. Engineering verification is separate from customer approval.

## Delivered scope and actual behavior

- Independent schema18 full-day per-worker Pending/Confirmed/Declined events,
  immutable WorkItem/Project/Crew/weekend-date/Employee scope, explicit employee
  decision/full-date/reference and exact roster fingerprint. Sequential revision,
  expected-revision reservation, no-op, atomic failure and retained history.
  SQL protects valid roster/current saved context/immutability/FKs.
- Planned versus saved provenance remains explicit. Saved helper reads actual
  workers and exact Assignment revision under the same transaction. Planned
  consent never fabricates saved attendance; saved records require independent
  actual-context review. Even remove-and-return of identical workers cannot
  resurrect an earlier saved confirmation. Note-only revision edits also expire
  saved positive consent conservatively. No old half becomes full-day approval.
- Actual missing/empty/partial/stale evidence Pending; applicable refusal Blocked
  even when other evidence is missing. Positive approval requires exact roster;
  removed employees are no longer required, remaining employees need re-review.
  HomeCrew, Available, calendar Working and driver approval never imply consent.
  Weekday consent not applicable; Cancelled capacity ignored.
- v6 snapshot observes consent source/event/native revisions and explicit weekend
  alternative rosters, including nominated worker metadata, in the existing
  single pinned query-only transaction. All previous daily/legacy calendar,
  staffing, driver, capability and Rig observations preserved. SHA256 binds
  query/roster/consent plus existing sources; relevant outside-horizon consent
  edits conservatively mark Stale. Shared100k units/64MiB/30second budget includes
  decoded consent memberships; read failures produce no false Current/partial
  proof. Reads never migrate17; legacy generation refuses new consent.
- T06 two-day Friday start: Pending/partial/Declined Saturday consent finishes
  Monday30; both exact workers Confirmed finishes Saturday28. Unapproved Sunday
  remains skipped. Closed/Unknown calendars or occupied Crew date still skip.
  Per-member consent reports remain available even for skipped planned dates.
  Consent alone never certifies actual worker availability or other resources.
- Existing daily generator/comparator retains gaps, deficits, annual bounds,
  EarliestFinish/EarliestStart and stable alternatives. Exact target weekend roster
  must match query even through lower-level personnel entry; changed workers
  require new query/candidate. Final proposal wraps existing people/driver/
  capability/Rig chain and rechecks source/target weekend consent. Source refusal
  excludes with Blocked evidence; changed positive source roster Pending.
  No implicit worker removal, approval transfer, reservation or saved mutation.
- Every root result Validation Pending / Apply=false / Publish=false. No consent
  HTTP/UI writer, employee contact, authority authentication, production daily
  gate opening, formal Apply/Publish/export or published-history edit.

## Actual engineering checks

| Check | Outcome |
| --- | --- |
| Python locked bundle restore / Ruff check/format | PASS;27 installed packages,120 Python files |
| Complete backend | PASS **545**, no skips;512 baseline +33 new |
| Focused weekend suite | PASS **33**:12 pure,18 integration,2 migration,1 legacy guard |
| PyInstaller / actual packaged sidecar tests | PASS **13** repeated source-sidecar coverage |
| Frontend locked npm ci / Prettier /42 tests / TypeScript/Vite build | PASS |
| Locked Rustfmt/fetch / native Tauri no-bundle build /8 release tests | PASS |
| Historical .NET locked restore/whitespace/Windows build/35 tests | PASS;0 build warnings/errors |
| Synthetic T06 console example | PASS; Pending/partial/refusal finish Monday, all confirmed Saturday; prior input Stale; false flags |
| Windows PowerShell5 synthetic acceptance harness | PASS; deliberate timeout/failure controls are expected mock scenarios, not a product GUI pass |
| Actual packaged17→18 preservation/verified backup/old rejection/independent recovery | PASS; below |
| Staged privacy/diff / nine UTF-8 Markdown link/fence checks | PASS;350 indexed paths, clean staged diff and nine Markdown checks |
| Exact-head Windows CI/installer/acceptance-kit build/upload | NOT RUN before push; final Draft PR/Issue records actual head/run/jobs |
| Production daily writers/consent HTTP writer/manual Apply | BLOCKED intentionally; existing gates closed, no new writer/Apply route |
| Native daily GUI/L09/Locate, disconnected installer/upgrade/reboot/clean-device, customer Demo E/UAT/production approval | NOT RUN |

Distinct inventory **630** =545+42+8+35. Packaged13 repeats coverage; console,
synthetic harness and migration/recovery are additional checks, not distinct
unit-test counts. Initial existing migration assertions still named17 and were
updated to18 without dropping preservation checks; final full suite passed.
Console example initially used an old property spelling, corrected to the actual
day candidate fields before successful reproduction. No safety gate weakened.

Focused tests cover pending/partial/all-confirmed/refusal, precise work/project/
Crew/date scope, saved ID/revision and roster changes, returned/removed workers,
legacy AM/PM Needs Review, empty/unconfigured/cancelled, no Available/HomeCrew
inference, both-Crew borrowing/source refusal, lower-level roster mismatch rejection,
SQL invalid roster/history/revision/rollback and concurrent writers, coherent
concurrent read, SHA/Stale/outside edits, technical budgets, deterministic dense
indexing, local year/leap/DST dates, frozen core/no file/network/SQL/time calls,
full logical no-writes and retained sorting. Existing full suites retain calendar,
availability, resource, annual-boundary and closed-production-gate regressions.

## Actual packaged17→18 recovery

Actual prior17 sidecar from PR112 created old AM/PM visits with distinct WorkItems/
notes, mixed calendars, partial availability and Rig inventory. Internal synthetic
recorders additionally seeded day members/daily calendars, old/daily driver,
old/daily policy/qualification, actual Rig allocation and an independent inspection
history. Native17 history was asserted before new startup; all original table
rows/types/IDs/relations/notes/revisions/history/sequences compared after18.
FK/integrity passed; day/calendar production writes stayed409; conversion count0.

Verified pre-DDL backup logically equalled17 including all resource histories.
Actual17 binary refused18 without logical writes. A separate copy restored using
SQLite backup reopened with actual17, original visits/logical content identical.
Live18 retained; no downgrade, history deletion or customer profile mutation.
Later18 edits are outside that recovery point and require separate reconciliation.
Fault-injection tests independently verify DDL/history/backup rollback and retry.

- Previous17 sidecar SHA256: `2fbdf4a7420632ca72c74642d45edc94cc1babedbef693de673e055a4d979efd`.
- New18 sidecar SHA256: `5d25da5ac0c60cf5a0bf2a51cec8ae55b3b83efa52918c379088ef7ed5a30cef`.

This is connected-host packaged-sidecar/SQLite recovery, not native/offline
installer/upgrade/reboot/customer acceptance.

## Remaining scope and next independent deliverable

Approval/recording authority, actual employee-decision collection/terminology,
Foreman policy, vehicle-category/legal qualifications and historical reconciliation
remain owner/customer decisions; no legal eligibility inferred. Full roster
availability remains an independent gate. #27 backend engineering is delivered,
not complete L09/customer Demo E/production acceptance.

Next development priority: day desktop weekly board + legacy visibility/detail
and read-only recommendation/consent/conflict preview, using real backend sources.
Then safe daily input/edit workflows and native offline regression; keep writes
closed until coherently reviewable. #18/#29 follows with Before/After, locks,
transaction revalidation, explicit human Apply/audit/recoverable versions.
Validated immutable company/Crew/employee PDF/XLSX follows those publication gates.
No further independent resource algorithm should displace that UI priority.
Keep113/27/99/16 and dependencies Open, one Draft PR, human review only.
No automatic merge, Release, production dispatch or real-data upload.
