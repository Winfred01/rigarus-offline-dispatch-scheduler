# Issue120 — recoverable Full Day Draft editor evidence

## Scope and provenance

Engineering evidence for Issue120 only; not customer Demo, UAT, production rollout,
Apply or Publish approval. Production daily writes remain CLOSED. Repository
visibility was checked as public: synthetic source and this sanitized summary only.
Original UI DOCX, native diagnostics, databases, backups, installers and VM images
remain local. Existing root-workspace changes were preserved in an isolated
`codex/issue-120-day-editor` worktree.

Baseline: main `9d40765a28703216f636802e7349a84dac3f7e84`, human-merged PR121.
Pre-code design/implementation plan commit `98f0a34`. See the
[Design Compliance Checklist](../design/2026-11-25-issue-120-day-editor-checklist.md).
Fresh source inventory: AGENTS d3b9bea; plan/playbook/architecture/decisions
be715d1; data model/demo acceptance7604d2a. Local evidence includes exact SHA256,
Git revisions and UTC modification times. Latest accessible original UI design:
November24 DOCX, SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`,
mtime `2026-11-24T23:15:38.711423Z`. L14 paragraphs74–78/image66 and L20
paragraphs104–108/image72 were freshly read/viewed. These are paragraph/image
locators, not verified page numbers. Full Day/Pending overrides prototype halves
and Validated controls; no new business defaults were inferred.

## Implemented boundary

- Independent dated Draft editor: create, notes/personnel/context edit, explicit
  saved cancellation, current revision and latest100 history entries. Cancel before
  Save closes without business writes. Cancelled records remain readable by typed ID.
- Explicit actual employee IDs, unconfigured versus explicit empty list, context
  reconfirmation, borrowed employees and retained historical members. Home Crew is
  reference only; no implicit roster removal or safety approval.
- Schema19 `20261125040000_AddDayEditorReceipts`: additive database UUID and
  immutable operation receipts. No conversion of legacy half-day records or rewrite
  of existing business tables. Verified backup precedes migration.
- One writer reservation includes exact profile/request/payload/revision checks,
  existing Crew/date, legacy AM/PM and SQL/Rig guards, mutation/history, persisted
  resource observations and receipt. Unknown source/storage failure rolls back.
  Definite rejection does not change business rows. Same request replays its
  original receipt; changed payload cannot reuse the key.
- Database-scoped, validated pre-dispatch journal; unresolved request prevents a
  replacement write. Receipt lookup and explicit same-payload retry only. A failed
  board refresh retains Committed and retries reads, never Save.
- Active saved results reload typed Locate/current week; cancellation reloads the
  week without erasing history. Both Job Schedule and Crew Board use persisted data.
- Strict FastAPI/Tauri operations. SQL observation budget30s, HTTP60s, desktop
  operation/refresh deadline150s; no automatic write retry. Timeout means Unknown,
  not cancellation of the original transaction.

Known calendar/personnel/driver/skill/Rig/weekend observations are Draft feedback;
missing evidence is Pending/Unknown, never Passed. Existing structural occupancy
guards remain hard. Every result stays Pending, applyable=false, publishable=false.
No new Foreman, qualification, staffing or weekend policy was invented.

## Automated engineering results

Windows11 Pro25H2 x64 build26200.9974 development host, connected network,
preinstalled WebView2/developer tools. Python3.13.7, uv0.10.12, Node22.20,
Rust1.95.0, .NET10/VS2022. These results do not certify a clean offline machine.

| Check / actual command | Result |
| --- | --- |
| Backend `uv sync --locked --group bundle`; `uv run --locked ruff check`; `uv run --locked ruff format --check` | PASS;128 Python files formatted |
| Backend `python -X faulthandler -m unittest discover -s tests -v` in locked venv | PASS580 tests,186.110s test time; wrapper186.982s/900s cap |
| `scripts/Build-RigarusSidecar.ps1`; `RIGARUS_SIDECAR_TEST_EXE` + unittest `-p test_sidecar.py -v` | PASS16 packaged tests,25.642s; repeated subset, not16 additional distinct tests |
| Frontend `npm ci`; `npm run format`; `npm test`; `npm run build` | PASS66 tests,0 skipped; TypeScript and Vite build PASS |
| `cargo +1.95.0 fmt --manifest-path src-tauri/Cargo.toml --check`; locked release build/test with `tauri/custom-protocol` | PASS9 Rust tests |
| `dotnet restore Rigarus.sln --locked-mode`; format whitespace verify; Release build/test without restore | PASS35 tests; build0 warnings/errors |
| Windows PowerShell5.1 `scripts/Test-TauriAcceptanceHarness.ps1` | PASS synthetic/mock harness; NOT native UIA execution |
| `npm run tauri -- build -- --locked` | PASS local x64 NSIS candidate with offline WebView2 payload; no host installation |

Total690 distinct backend/frontend/Rust/.NET tests. New editor coverage includes13
backend cases,10 frontend state/recovery cases,1 packaged-sidecar scenario and1
Rust path-identity case. Historical migration assertions were updated to schema19
without deleting compatibility/data-preservation assertions. Initial stale schema18
expectations failed and were corrected; final full suite passed. A concurrent receipt
tuple/list mismatch and an initial Rust bridge signature error were corrected before
these passes. Restricted-cache/process execution failures were retried with existing
approved local tools; they are not product failures.

| Acceptance scenario | Result and evidence limit |
| --- | --- |
| Create/edit/cancel, stable ID/employee list/notes/history, reopen | PASS service tests and native candidates below |
| Explicit empty versus unrecorded, context reconfirmation, no Home Crew inference | PASS automated; borrowed worker also native |
| Crew/date collision with legacy PM or full-day Draft, existing rows retained | PASS automated; no native collision injection claimed |
| Stale revision and concurrent distinct requests | PASS automated; stale revision also native |
| Same request concurrent/lost reply/restart replay; changed payload/profile | PASS automated and authenticated packaged sidecar |
| Source-observation failure or receipt-storage failure | PASS automatic rollback tests, including safe same-request retry after storage recovery |
| Journal malformed/unwritable, NotFound uncertainty, late response after deadline | PASS frontend state tests; native fault injection NOT RUN |
| Committed save plus failed refresh, retry refresh without writing | PASS frontend state tests; native fault injection NOT RUN |
| All old schema18 business tables preserved; DDL failure rollback/retry/idempotence | PASS automated migration/integrity/FK tests |
| Actual old schema18 executable refuses19, opens independently restored18 backup | PASS local packaged executable check; health200/normal exit, restored logical digest unchanged |

## Native desktop reproduction actually executed

Separate synthetic smoke root, own release EXE/sidecar on the connected development
host. No production profile, installed application or customer database used.
Explicit synthetic write test uses both `RIGARUS_DAY_EDITOR_TEST=1` and a separate
`RIGARUS_SMOKE_DATA_ROOT`; the sidecar independently checks the exact smoke database
path. Remove the write-test variable to verify the ordinary closed gate. Never use
this opt-in with real data or as rollout approval.

1. Seed one synthetic Project/WorkItem, nine Crews and one actual employee whose Home
   Crew is1. Seed FullDayDraft1/2 and LegacyHalfDay1/2, including a PM record; day and
   legacy ID1 intentionally overlap numerically. Record original IDs/notes/revisions.
2. Launch, choose New Full Day Draft, select WorkItem1/Crew3/November25, explicitly
   choose employee1 and reconfirm the list; note `Synthetic native full day create`.
   Save returns FullDayDraft3/revision1. Close editor and Enter the focused typed
   card: exact date, ID, member and note persist.
3. Reopen editor at revision1. Type an unsaved note; separately perform one authorized
   synthetic concurrent edit to revision2. Save the old revision: Stale rejection,
   unsaved fields retained, current saved record unchanged. Close normally.
4. Reopen same profile. Detail shows revision2 and concurrent saved note. Edit notes
   to `Synthetic native final edited note`, save same ID3/revision3/member1. Return
   to its typed card and verify exact saved values.
5. Open edit again, explicitly confirm cancellation of ID3/revision3, cancel. Receipt
   is Cancelled/revision4; current week count drops5→4. Crew Board shows the same
   four active records and empty Crew3. Normal close/reopen retains cancellation.
6. Without write-test opt-in, New editor Save is disabled. Open saved Full Day ID3,
   including cancelled: revision4/member1/note retained, history4/3/2/1 visible.
7. Final rebuilt EXE recheck: same four active records; ordinary gate closed; saved
   ID3 visibly says **Loaded saved status: Cancelled**, revision4, correct employee,
   date and note. Normal close; readonly DB verification still identical.

Steps2–3 native EXE SHA256:
`bf9d361b07ac1119eaf52ded03845b440bbd03aff2ad3090f1b09eecea55228d`.
Steps4–6 widened UI candidate:
`cb4ccaf9bc5c1a078d3eacea25690d5b61f6f3ab31c9fe76465e5bedbace51b2`.
Step7 final EXE:
`a8f7d6526169e58b0a398891b4dcc231b5fdb6e08f2e32d79aeca21d13123d5a`.
Full create/edit/cancel was not rerun on this last cosmetic/status/deadline rebuild;
final source has all automated checks and the limited native recheck above.
Local final NSIS0.1.0 SHA256:
`db6364b2260b7d6a930833bf482fc6bdfd87944f3daf6dd695fb0d70b2af3bf2`.
This is a local feature-branch candidate, not a published Release or the later CI
artifact (whose build commit/hash must be checked independently).

Readonly post-close verification: SQLite integrity=ok, FK errors0; ID3 revision4,
four immutable history entries with employee1; original day/legacy fixture rows and
WorkItem estimate/requirements retained. Four receipts: three Committed and one
Stale Rejected. Logical digest
`6cf4c9cbed10c9b8f4b6b8961d462c134ebed2069bce8d7694047aa31a772e45`.
Old-binary restored18 digest
`8b065ffaeda49f3dde13b1e2f987e3cf6e47fe6e083241953852aab6d2e4fea3`.
No owned application/sidecar remains after normal close.

Original-image comparison led to editor-only900px dialog, aligned checkboxes,
collapsible saved-ID utility, outlined secondary actions and explicit saved status.
Existing shell/type/colors retained. Native1442×992 window and keyboard Escape/Enter
were exercised. Three viewport sizes, full screen-reader audit, and Normal/Hidden
full legacy UIA regression are NOT RUN. App style lint:0 FAIL/1 WARN for em-dash
state/action labels retained in existing product wording; browser inspector NOT RUN.

## Offline installer/upgrade/reboot gate

| Gate | Result |
| --- | --- |
| Own QCOW2 overlay, unchanged backing image, `-nic none`, boot/discovery | PASS environment preparation only |
| Qualified stable Windows11 x64 VM | BLOCKED: guest visibly reports Windows11 IoT Enterprise LTSC Evaluation/build26100 and **Windows License is expired** |
| New candidate offline install/first launch/WebView2 | BLOCKED; neither candidate nor baseline installer was executed in this VM |
| Old-version replacement, upgrade data preservation and VM reboot | BLOCKED same prerequisite; no pass borrowed from another package/run |
| User-license/security policy or host component changes | NOT RUN; no rearm, bypass, host uninstall or security-policy changes |
| Uninstall/reinstall and representative corporate standard account | NOT RUN this slice |

VM was normally powered down; original image retained. A valid licensed Windows11
x64 source path is required to resume. Same product version0.1.0 means the planned
upgrade check is a **same-version replacement**. Prepared baseline installer from
PR121 Windows CI run45703461343: build commit
`35ff8fe421abddccccfc9df6e13a4bde74188db7`, SHA256
`7d164c667d990da941f2dbc3e12ed16980d252ab7f54c06aa0489628992309ba`.
This preparation is not installation/upgrade evidence.

## Local evidence and remaining gates

Raw evidence stays in the ignored sibling `day-editor-evidence` directory:
source/UI inventories; `full.log`/`full-result.json`; `packaged.log`/result;
frontend/Rust/.NET/build logs; `native-final.local.json`; binary/installer hashes;
`old-binary-recovery.json`. VM overlay/helper manifests remain separate local-only.
No raw logs, screenshots, databases, original figures or installers are committed.

Documentation/link/UTF8 checks, staged privacy scan and exact-head Windows CI are
recorded in the Draft PR once actually executed; this file does not claim a pending
remote result. CI is an engineering check, never proof of native/offline GUI success.
No Issue closure, automatic merge or Release. Customer Demo/UAT/production remain
unapproved. Daily-write gate review remains blocked on the agreed editor/recovery/
safety and qualified offline VM acceptance scope.

Parent14/16/22/99 remain open: broader weekly/employee workflows, locks, real driver/
qualification/Rig safety and hard publication gates are not completed by this editor.
Human Apply/version rollback, delay-chain replanning and PDF/Excel export remain
later slices. The latest100 Draft history view is not schedule-version rollback.
