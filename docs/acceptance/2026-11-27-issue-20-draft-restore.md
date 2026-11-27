# Issue20 — synthetic single-version Draft Restore acceptance

Engineering record, November27,2026. Source main
`99c9741297ae6158aec849fa3f6ce3337bd24513`; branch
`codex/issue-20-draft-restore`. Human-merged128 inspected; no competing open PR
at start. Pre-code authorization/plan committed as `d4052a3`. Full implementation
head/Windows CI are recorded in the Draft PR. Repository is public; only synthetic
fixtures and sanitized evidence are delivered. Root user's changes preserved.

## Authority and design

[Explicit scope confirmation](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/20#issuecomment-7227116880)
was read and reaffirmed by the current implementation request. It confirms bounded
engineering only, not independently authenticated legal/customer authority.
The [decision register](../10-CLIENT-DECISIONS.md) retains the prior Proposed
record as history and adds the dated five-condition confirmation plus future
mixed-display requirement. No half-day creation/editing policy is approved.

Fresh sources: AGENTS/DEV checklist d3b9bea, plan/playbook/current architecture/
model/acceptance80e6eb8 and decision record8f63b1c before this work. Relevant #20/
#99/#124/#126, original schema20 Apply/read-only inverse, migration/backup, day
persistence, weekly validators, native journal and tests inspected. Current source
revisions/hashes/checkout UTCtimes are retained in local `sources.local.json`.
Planning/playbook were reread, with affected current sections in other documents;
not every historical subsection is claimed read. Original local November24 DOCX
SHA256d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c,
mtime2026-11-24T23:15:38.711423Z. Fresh L10 paragraphs54–58/image62, L12
paragraphs64–68/image64 and L13 paragraphs69–73/image65 inspected. Paragraphs
are not pages; prototype Undo/Published history is not production authorization.
No original DOCX/images uploaded; no UI changed in this slice. See
[Design Compliance Checklist and plan](../design/2026-11-27-issue-20-draft-restore.md).

## Five confirmed conditions

| Condition | Implemented verification |
| --- | --- |
| Exact selected version only | Original DraftVersion kind and lineage bound; immutable source JSON, typed FullDayDraft scope; exact current status/business values/revision comparison. Any later mismatch Stale, no force |
| Append history/audit/version | Original IDs retained; every touched row receives a higher revision/history, old additions cancel and cancelled originals may reactivate under current constraints; source JSON/history never rewritten |
| Per-item Pending; Blocked refuses | Complete individual warning reasons and canonical warning IDs; exact complete acknowledgement set required. Root remains Pending/false/false; known SQL/resource conflicts refuse |
| Atomic revalidation/idempotency | BEGIN IMMEDIATE covers exact proof/current resource reads, SQL guards, inverse, final observations, immutable recovery version/audit and receipt; faults rollback. Independent UUID namespace, unchanged replay, changed-payload refusal and receipt reconciliation |
| Synthetic backend only | Separate explicit flag plus exact isolated root required for prepare/submit. No desktop command/control, production writer, Publish, client DB or deployment |

Preparation is a reserved synthetic SAVEPOINT dry run, **not query-only SQL**.
It always rolls back simulated revisions/history and commits no business/audit/
receipt rows. Unknown source/storage/SQL/audit errors return503 and preserve
uncertainty. Known rejection rolls back business changes and stores an immutable
Rejected receipt. NotFound never permits a blind new key. Native desktop
reconciliation journal behavior is unchanged and does not bridge Restore.

## Requested scenario matrix

The31 new Restore tests use an exact isolated synthetic root. Their initial
16.205s/28.956s runs exposed test-fixture/API-path/row-order expectation mistakes,
which were corrected without relaxing product assertions. The completed focused
run passed31 tests in30.847s before full-suite validation.

| # | Scenario | Actual result |
| --- | --- | --- |
| 1 | 5→8 inverse | PASS; five original IDs retained, three additions append Cancelled events |
| 2 | 5→2 inverse | PASS; three cancelled originals reactivate under same stable IDs and new revisions |
| 3 | Stable FullDayDraft identities | PASS; typed original IDs unchanged |
| 4 | Original notes/actual workers/history | PASS; exact employee IDs/notes restored, prior member/history events retained |
| 5 | Unselected project | PASS; separate Project/WorkItem Draft unchanged |
| 6 | Raw AM/PM preserved | PASS; legacy rows unchanged before/after |
| 7 | Equal integer IDs | PASS; FullDayDraft1 and LegacyHalfDay1 resolve independently, correct Project/notes/full-day versus PM |
| 8 | Legacy occupied date | PASS; reactivation conflicts reject, old AM record retained |
| 9 | Later touched-record edit | PASS; exact values/revision mismatch Stale; no forced overwrite |
| 10 | Resource hard negatives | PASS; actual personnel collision, unavailable employee, suspended driver, closed Project calendar, minimum/Level/NotVerified qualification, Rig maintenance and weekend refusal blocked |
| 11 | Missing per-item confirmation | PASS; missing/extra IDs, false confirmation and duplicate IDs cannot record a version |
| 12 | All warnings acknowledged | PASS; only unconfirmed Draft, Pending/Apply=false/Publish=false; old Rig readiness and saved weekend consent remain stale/Pending after revision |
| 13 | Exact same-key replay | PASS; no duplicate history/version; concurrent same-key calls return one result |
| 14 | Changed body under same key | PASS; rejected without replacing original receipt |
| 15 | Mid-batch SQL failure | PASS; entire business/history/version/receipt transaction rolled back; same key can be reconciled/replayed after fault removed |
| 16 | Audit/receipt insert failure | PASS; both fault points roll back all changes |
| 17 | Reopen durable result | PASS; authenticated packaged sidecar close/reopen retains exact version/receipt; default writer still closed |
| 18 | Schema compatibility/backup | PASS; unit DDL/backup faults/rollback/retry/reopen plus actual packaged20→21, prior20 refusal without writes and independent20 backup reopening |
| 19 | Default production gates | PASS; prepare and submit reject without separate test gate; missing/wrong root rejects; unauthorized loopback401; no Tauri Restore path |
| 20 | Never publishable | PASS; all successful/rejected structured results remain Pending/false/false |

Additional source-read/deadline/final-revalidation faults, malformed types/kind,
wrong profile, immutable UPDATE/DELETE triggers, unknown receipt and request-UUID
reuse across Apply/Restore namespaces are covered. Fault injection uses synthetic
exceptions/triggers only, never host disk/security failures or customer data.

## Mixed calendar compatibility

Existing Job Schedule/Crew Board and typed Locate implementation is retained.
New API regression combines distinct projects/Crews, FullDayDraft and a separate
Legacy PM with the same integer ID; correct kind, project, notes and slot are
verified through existing weekly/Locate routes after Restore. Full frontend
tests cover existing day/legacy labels and typed routing. No second calendar,
new half-day editor or automatic half-to-full conversion was introduced.
Cancelled records remain in immutable history; active Locate rejects cancelled
records rather than presenting them as current cards. No new native mixed-view
GUI execution is claimed in this backend slice. Future Employee Week/search/
PDF/Excel integration remains separately scoped; no mixed-view product defect
was established by this regression.

## Migration and actual binary recovery

Schema20 lacks source-linked recovery audit and a separate Restore receipt
namespace. Additive21 creates only DraftRestoreVersions/DraftRestoreReceipts and
immutable guards. All original tables, JSON, IDs, fields, staff and history are
preserved. See [data model](../03-DATA-MODEL.md). Recognized20 is backed up with
the existing consistent/integrity/FK/logical-digest verification before DDL.
Unknown schemas refuse; never remove a live migration to downgrade.

Actual CLI packaged test, host Windows with loopback allowed:

- Old20 sidecar SHA256
  `e497135b531453baa2aa4712c943a0c808f80d3cca83e6d52c7aec9219e80ac1`
  first reopened the synthetic20 profile unchanged.
- New21 sidecar SHA256
  `3d6e0e4fedbd3ecc761c54a719b7258ca44e583240d17800dbbe11c9fd61d15e`
  upgraded it. Every original table matched (apart from appended migration
  history); consistent20 backup matched the pre-upgrade logical digest.
- New packaged service prepared/committed/replayed one exact inverse. Original
  DraftVersion JSON remained unchanged. After shutdown, old20 refused live21
  without changing its logical digest.
- Verified20 backup restored into a SECOND isolated environment and reopened by
  the old binary unchanged. This is an engineering compatibility check, not
  permission to overwrite live21 or claim an offline VM restore pass.

Raw manifests/logs/databases/backups stay in authorized local evidence. Reproduce
the public-safe unit/packaged sequence using [synthetic instructions](../../samples/synthetic-only/draft-restore.md).

## Commands and actual checks

| Check | Result |
| --- | --- |
| `uv sync --locked --group bundle` | PASS; isolated worktree venv/cache |
| Ruff check / format --check | PASS,139 Python files |
| Full Python `python -m unittest discover -s tests -v` | First677 run FAIL14 obsolete schema20 expectations; changed to exact21/history assertions. Final PASS677 tests,289.114s |
| Packaged sidecar `test_sidecar.py` | PASS18 tests,29.204s; repeat subset, not18 additional distinct tests |
| `npm ci`, Prettier, `npm test`, TypeScript/Vite build | PASS89 frontend tests, no product UI changes |
| Rust1.95.0 locked Windows Release build/test | PASS15 tests |
| Journal fixture repeat check | Old baseline25 runs PASS; candidate50 runs PASS (3 journal tests each), repeat evidence only |
| .NET locked restore / whitespace / Release build / tests | PASS35 historical tests,0 build warnings/errors |
| PS5.1 synthetic acceptance harness | Initial package-integrity CommandNotFound failure; process-scoped compatible Windows PowerShell module-path retry PASS. Exact initial command cause not conclusively isolated; no script assertion change |
| Windows sidecar/Tauri Release/NSIS | PASS; own worktree resources, no installed host/VM package replaced |
| Documentation | PASS9 Markdown files/179 local links, UTF-8/fences/anchors; staged privacy count recorded in Draft PR |
| Exact-head Windows CI | See Draft PR; local checks are not a remote CI result |

Total distinct local automated tests:816 (Python677 + frontend89 + Rust15 +
historical.NET35). Packaged18 and repeated journal tests are reruns, not additional
distinct coverage. The restricted test attempt blocked inside Windows socketpair;
per-command loopback execution permission resolved that environment limit without
changing network/security policy. A diagnostic-only timed faulthandler attempt
crashed; final bounded test runs did not use that diagnostic timer and passed.

Current main CI46060107526 failed in an existing Rust journal test's initial
Journal::open. The test helper used process+wall-clock nanos and create_dir_all;
coarse clock collisions could share fixtures. Test-only hardening adds an atomic
sequence and exclusive directory creation; product lock/recovery policy is
unchanged. The old failure did not reproduce in25 local repeats, so the precise
runner cause is not claimed proven. Candidate50 repeats and full Rust passed;
final Windows CI remains the authoritative current-head engineering check.

Local NSIS0.1.0 x64 SHA256
`770abb259ac0a464908856f026c36936bcb71bdbe674855d70cb5105919cce09`;
Release EXE SHA256
`5e719762f4d492f61f7ec9955235d81da4f28f0c6d4e1b5440b93c4c24311f0f`.
Built from this branch's working product changes (subsequently committed), not
falsely attributed to the pre-code plan commit alone. CI package bytes are
separate artifacts; these local packages were not installed.

## Remaining independent gates

- **NOT APPLICABLE:** native Restore button/interaction; intentionally absent.
- **NOT RUN:** new native mixed-calendar GUI execution, screen-reader/viewport
  review; UI unchanged. No native PASS inferred from API/frontend checks.
- **BLOCKED:** qualified Windows11 x64 VM disconnected installation, upgrade,
  OS reboot/data retention and clean missing-WebView2 environment. Prior
  Evaluation guest expired; no qualified replacement used. No license/security
  bypass or development-host-as-offline claim.
- **Not approved:** customer Demo/UAT, production deployment/writes, dispatch,
  Publish, Release, new half-day editing and unconfirmed business/legal policies.
- Later work: human review of this backend slice, then independently authorized
  recovery UX/native/fault qualification and controlled-writer review before
  dependency-aware delay chains/formal exports. No automatic merge/Issue closure.
