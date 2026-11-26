# Issue126 — desktop exact Draft confirmation and recovery

Engineering record: November26,2026. Refs #126, #124, #18, #20, #29, #99,
#120. Draft PR required; human review, customer Demo/UAT and production approval
remain separate. No Issue closed, Release published or production gate enabled.

## Source and build identity

- Fresh remote main `0f128221b496e38a49267b0625e860b4d055f694`; PR125 was
  externally merged before implementation. Main CI45839749613 passed all three
  Windows jobs before product edits. Remote main remained the same at delivery.
- Branch `codex/issue-126-draft-confirmation`; design-only commit `3378abb` came
  before product edits. Product candidate was built from this branch's recorded
  working changes, not falsely attributed to that design-only commit.
- Fresh sources: AGENTS d3b9bea; plan/playbook/architecture/model/acceptance
  b6eb695; decisions1858259. Source SHA256 and checkout UTCmtime recorded locally;
  see [Design Compliance Checklist and plan](../design/2026-11-26-issue-126-desktop-confirmation.md).
- Original local UI design dated November24 was freshly inspected: L10
  paragraphs54–58/image62, L12 paragraphs64–68/image64, L13 paragraphs69–73/image65.
  These are paragraph/image locators, not page numbers. Complete DOCX and original
  figures remain local. Owner-approved Full Day/unconfirmed Draft boundaries
  override prototype half-day/Apply/Undo concepts.
- Final local Release EXE SHA256:
  `a25504988ef243b457cea6ce5eabd7a05ab17d30eac69a9b9aa6396a2e2105b0`.
- Final locally built NSIS0.1.0 x64 SHA256:
  `1f8a85f80811b92b313f23e4bd53884bf8f2ebf6271686d6ed90cc46c9b79078`.
  This is a new development candidate, not a replaced published installer. It
  was built but NOT installed in this session. CI artifacts have separate bytes.

## Changes and compatibility

React displays exact saved/proposed values, dates, typed FullDayDraft IDs,
revisions, actual employee IDs/null/empty semantics, notes, cancellation IDs and
complete Pending warnings. Two explicit acknowledgements are needed before the
synthetic test-only transaction. No inferred staffing or actual Rig allocation.

Rust retains the exact original request before HTTP in a database-identity-scoped
native journal. Exclusive Windows file handles serialize cooperative operations;
bounded reads, create-new writes and flush errors fail closed. Closing/restarting
does not clear the request. Unknown/NotFound never authorizes a new key.
Acknowledgement verifies the authenticated server result and writes an exact
local receipt archive before removing pending. Known rejection retirement
explicitly replays the SAME request/key and requires the same known rejection;
rejections are not immutable backend receipt rows. This is an engineering-only
qualification limit, not production dispatch authorization.

Existing schema20 transaction/receipt/changeset/inverse are reused. **No new
SQLite migration.** Original IDs, notes, staff, history and legacy AM/PM remain
protected. Full Day board refresh and typed Locate read persisted records.
Version Current/Stale is a touched-record comparison, not proof a restore would
be safe. Actual Restore, dispatch Apply/Publish, locks and dependency rescheduling
remain unavailable. Production writes remain false.

## Executed commands and outcomes

Commands below ran in the isolated feature worktree using existing authorized
local toolchains. Raw logs, paths, synthetic databases and recovery archives stay
in the ignored local evidence directory `draft-confirmation-evidence`.

| Check | Actual result |
| --- | --- |
| `uv sync --locked --group bundle` | PASS |
| `uv run --locked ruff check`; `uv run --locked ruff format --check` | PASS,135 Python files |
| `uv run --locked python -m unittest discover -s tests -v` | PASS,645 tests,263.719s on final backend |
| `scripts/Build-RigarusSidecar.ps1` | PASS, own bundled Python sidecar |
| `uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v` with packaged-sidecar EXE | PASS,17 tests,31.070s; repeated subset, not17 additional distinct tests |
| `npm ci`; `npm run format`; `npm test`; `npm run build` | PASS,89 frontend tests; TypeScript/Vite build |
| `cargo +1.95.0 fmt --manifest-path src-tauri/Cargo.toml --check` | PASS |
| `cargo +1.95.0 build --release --locked --features tauri/custom-protocol --manifest-path src-tauri/Cargo.toml` | PASS |
| Corresponding `cargo +1.95.0 test --release --locked ...` | PASS,15 Rust tests |
| `npm run tauri -- build -- --locked` with Rust1.95.0 | PASS, local NSIS candidate above |
| `dotnet restore Rigarus.sln --locked-mode` | PASS |
| `dotnet format whitespace Rigarus.sln --verify-no-changes --no-restore` | PASS |
| `dotnet build Rigarus.sln -c Release --no-restore` | PASS,0 warnings/errors |
| `dotnet test Rigarus.sln -c Release --no-build --no-restore` | PASS,35 historical compatibility tests |
| PS5.1 `scripts/Test-TauriAcceptanceHarness.ps1` | Initial FAIL: existing package-integrity helper could not find uv; retry with existing uv on process PATH PASS. Mock harness, not actual offline GUI |
| Actual synthetic FastAPI prepare/commit/inverse → frontend validators | PASS; malformed/mismatched variants rejected |

Total distinct automated tests: **784** (645 Python +89 frontend +15 Rust +35
historical .NET). Packaged-sidecar17 are a rerun subset. Tests include exact
receipt/plan mismatch, malformed/default gate, replay identity, journal
reopen/exclusive handle/other-key/oversize/archive failure and Current/Stale
read-only handling. The native stale-source regression first failed because
HTTP409 lacked a machine-readable code; it passed after the minimal known-stale
normalization. Unknown errors and identity/idempotency mismatch stay unresolved.

Final documentation/privacy and exact-head Windows CI are recorded in the Draft
PR after staging/push; a local pass is not a remote CI or offline installation
pass.

## Native Windows reproduction and observations

Actual host: Windows11 Pro x64,10.0.26200 (25H2,UBR9974), WebView2 already
available. Normal interactive window,1442×992. Ethernet and Hyper-V adapter were
Up; **network was not disconnected**. Test used packaged Release EXE plus own
sidecar resources, not a browser mock or installed application. All UI actions
used native CUA. Synthetic CLI seeding/inspection was limited to the isolated
test database; no customer database or host security policy changed.

Reproduce with a fresh isolated `RIGARUS_SMOKE_DATA_ROOT` and explicit
`RIGARUS_DRAFT_TRANSACTIONS_TEST=1`. Keep the independent daily-editor flag unset.
Seed one Project/WorkItem, two Crews, explicit daily calendars, five active
FullDayDraft visits and a separate Crew's legacy PM visit. Choose an eight-day
recommendation with exact replacement scope. This flag is an engineering test
opt-in; ordinary profiles remain read-only.

| Case / steps | Result and evidence |
| --- | --- |
| Prepare5→8 dates, inspect IDs/notes/warnings; Escape before Save | PASS on first candidate. Logical digest unchanged; versions0/no pending. Final candidate repeats exact preparation with date-sorted display |
| Check plan only | PASS, Save disabled; both confirmations needed |
| After prepare, synthetic concurrent note edit changes ID6 rev1→2; submit old scope | Initial desktop result UNKNOWN, original journal retained, no business writes. API uncoded409 reproduced; coded-stale regression/fix followed |
| Close, rebuild, reopen SAME smoke root and resolve original request | PASS on final EXE. NotFound explicitly remains uncertain; original key retained |
| Explicit same-key retry, then recheck/retire rejection | PASS, known stale rejection; no version or business write, exact rejection archived. No journal manually deleted |
| Freshly prepare current5→8; Before shows ID6rev2 and concurrent note; both confirmations; double-click Save | PASS, exactly version1. Actual rows and persisted-week refresh shown; no duplicate version |
| Close without acknowledging saved receipt; reopen with test-write flag REMOVED | PASS, original key recovered; Retry disabled; Resolve returns Committed version1 and refreshes week |
| Read exact version1 and inverse | PASS, Current; explicit read-only warning. Restore disabled |
| Acknowledge verified receipt | PASS, native archive written; pending removed only after server verification |
| Return to Schedule, typed Locate FullDayDraft13 | PASS, jumps to December7 week; one new saved Draft visible with Validation pending |
| Switch Crew Board | PASS, same ID13/date/Crew from persisted data |
| Normal application close | PASS, owned app/sidecar processes absent after close |

Earlier candidate hashes are retained only in local records. The stale attempt
was created on candidate5dc69137…, then recovered/rechecked on finala2550498…;
this transition is deliberate restart/recovery evidence, not a claim both builds
were identical. First cancellation candidate7befee9e… preceded display polish.

Read-only SQLite verification after the final close: `integrity_check=ok`, no
foreign-key errors, exactly one DraftVersion, exactly three added daily visits,
all preexisting daily row values unchanged from the post-concurrent-edit baseline.
Only DayDraftAssignments, DayDraftChanges, DraftVersions and sqlite_sequence
changed. All other37 tables, including legacy records and Project/WorkItem data,
were unchanged. Final logical digest:
`2dc21f56fb05020800a1ff4f58c47224d1b11480d25961d9547ecc862cd47cae`.
Pending count0; two local receipt archives (one rejection and one Committed).

Native observations/AX and synthetic screenshots are in the local task session;
`native-verified.local.json`, `db-before-success.local.json`,
`native-source-edit.json`, build/test logs and source inventories are retained
locally. No raw diagnostics, databases, recovery envelopes, original UI images or
customer data are included in GitHub evidence.

## Remaining gates

| Gate | Status / limitation |
| --- | --- |
| Clean Windows11 x64 VM offline installation, upgrade, OS reboot and retained data | BLOCKED: known Evaluation guest expired; no qualified replacement image available/authorized in this run. New NSIS built but not installed. Application reopen above is not OS reboot |
| VM with no preinstalled WebView2 | BLOCKED: no qualified clean image; host component not removed/bypassed |
| Hard power loss, multi-process native GUI race, forced refresh failure/transport loss, Hidden supervisor | NOT RUN natively. Unit/journal/contract coverage does not qualify these GUI conditions |
| Native stale inverse after another post-commit edit | NOT RUN; automated Current/Stale coverage only |
| Three viewport widths/browser inspector/screen-reader | NOT RUN. Existing desktop shell and1442×992 normal-window comparison only; table/warning scroll and Escape observed |
| Style lint | PASS0 failures;1 warning for six retained em-dash state/action labels |
| Human PR review | Pending |
| Customer Demo / UAT | NOT APPROVED |
| Production daily writes / dispatch Apply / actual Restore / Publish / Release | CLOSED / NOT IMPLEMENTED / NOT APPROVED as applicable |
