# Issue #14 manual Draft Assignment engineering evidence

This is the owner's first M2 persistence/manual-entry slice. Refs #14; #16 and #22 remain separate. The [Design-First checklist](../design/2026-11-21-issue-14-manual-draft-checklist.md) records the six required documents, original November 21 UI figures/sections, baseline revisions, rule authority and implementation plan output before product edits.

## Identity and scope

- Baseline main: `069e6b38cdbbc228b9630c18c9f1acf594309e67`, manually merged PR #70. Main CI [44982588774](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/44982588774) succeeded. Repository PUBLIC; original main/local changes were preserved in a separate worktree.
- Branch `codex/issue-14-manual-draft`. Local Windows x64 candidate version 0.1.0: EXE SHA-256 `22213a1fab81b633c4fdabaa260a57c9c5cb732364a8701e65c423de3303f117`; bundled sidecar SHA-256 `de0e90650f70141a3727cef78f1c74089d693ad4372b719484ac2d65f88a0179`.
- Migration `20261122040000_AddDraftAssignments` adds a seventh schema entry, assignment table and indexes. Existing records/IDs/notes remain in place. Keep a verified consistent pre-upgrade backup; the older Tauri backend rejects schema 7 and requires its original backup for fallback.
- This is an actual persistent Draft path, not a mock schedule. AM/PM remains provisional; `validation_status=Pending`, `publishable=false`, no publish endpoint/command, and Publish unavailable in UI. Current labels are joins; immutable published snapshots and full scheduling history are future work.

## Reproducible cases

| Case | Synthetic steps and actual evidence | Result |
| --- | --- | --- |
| Separate Civil/Tower WorkItems | Create one Project with two items; use each item's Assign action; compare selected ID/type and saved record | PASS in actual React/packaged API and native Windows |
| Same day AM/PM and repeated visits | Save Civil to one Crew on December 31 AM and PM; retain WorkItem ID across visits | PASS; two persisted slots, separate Assignment IDs, no inferred duration completion |
| Crew-slot collision | Attempt Tower on occupied AM; retain fields/notes, choose January 1 and save | PASS; actionable 409, no overwrite; browser/native corrective flow |
| Concurrency and revisions | Concurrent same-slot creates; concurrent edits from same revision; stale cancel | PASS; one winner, stale 409 and retained newer data |
| Form Cancel | Fill an unsaved visit then Cancel; compare write-call count, persisted records and read-only DB digest | PASS; no mutation request or new record |
| Saved cancellation | Keep one confirmation, then confirm; retain ID/notes/refs and reuse released slot | PASS; Cancelled row retained, default range API excludes it |
| Persistence / cross-year dates | Reopen application and sidecar; read December 31 / January 1 visits, IDs, edited notes and Cancelled row | PASS native host and packaged tests; no UTC work-date conversion |
| Date/ID/state boundaries | Leap dates, year 0001/9999, invalid calendars/timestamps/IDs/extra publication flags; SQLite FK/date/status/unique constraints | PASS; invalid requests do not write; unsupported publish request 404 |
| Transaction failure | Inject post-insert/post-update failures; test edit/cancel and retry; sanitize read failures | PASS; unchanged earlier data/revision, actionable 503 without diagnostic marker |
| Additive migration | Force failure after Assignment DDL before history entry; compare all existing table snapshots; retry twice | PASS; full rollback/retry, integrity ok, no FK errors |
| Actual previous backend / backup | Run actual `069e6b3` storage code to create six-schema data including Foreman history; consistent backup, upgrade, create visit, retry older backend | PASS; original data/notes unchanged; old backend rejects upgraded file without byte changes; original backup remains compatible |
| Packaged six-schema upgrade | Start the real bundled sidecar on a synthetic six-schema fixture, create assignment, stop and compare all prior records | PASS, including Project/WorkItem IDs, demo/Rig notes and Foreman refs |
| Error / empty / loading / keyboard | Actual built React through test-only IPC proxy to actual packaged FastAPI/SQLite; empty WorkItems, read failures/retry, conflicts, stale editor, cancel/focus and narrow forms | PASS; native Rust/desktop evidence is recorded separately |
| Lost response | Commit create then simulate response loss; preserve form, block blind retry, Reload entered date | PASS; saved record found without duplicate creation |
| Committed write / failed refresh | Save onto a new date, or cancel, then fail list read | PASS after fix; reports saved/cancelled and clears stale rows. Initial test reproduced old-date rows under new date; fixed and re-run |
| Native host GUI | `Test-TauriDesktop.ps1 -Executable <candidate> -IncludeAssignments -DiagnosticLog <local-log>` | PASS; lifecycle at 9.836 s, reopen at 12.187 s, full smoke 13.634 s, sidecar exit 0 and startup failure hint |
| Independent offline VM | Same payload, no NIC, `-Profile SlowVm -RequireOffline -IncludeAssignments` | PASS first final run; lifecycle 224.696 s, reopened data 286.234 s, full smoke 325.037 s; GUI exit 0 |
| Human assistive technology / customer Demo B | Human screen-reader and customer workflow/granularity acceptance | NOT RUN; UIA/ARIA tests do not sign off customer acceptance |
| New CI installer / representative managed device / production | Install/upgrade the feature's CI package and validate target policies/real migration under separate authorization | NOT RUN; candidate feature validation is distinct |

## Commands and conditions

- `uv sync --locked --group bundle`, `uv run --locked ruff check`, `uv run --locked ruff format --check`, `uv run --locked python -m unittest discover -s tests -v`: PASS, **68 tests**.
- `scripts/Build-RigarusSidecar.ps1`; actual `RIGARUS_SIDECAR_TEST_EXE` plus `uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v`: PASS, **8 tests**. The packaged upgrade/restart/authentication cases use synthetic files only.
- `npm.cmd ci`, `npm.cmd run format`, `npm.cmd test`, `npm.cmd run build`: PASS, **17 tests**, TypeScript/Vite build. Toronto/Tokyo tests around UTC midnight validate local-day handling.
- `cargo +1.95.0 fetch --locked --offline --manifest-path src-tauri/Cargo.toml`, `cargo +1.95.0 fmt --manifest-path src-tauri/Cargo.toml --check`, `npm.cmd run tauri -- build --no-bundle -- --locked`, `cargo +1.95.0 test --release --locked --features tauri/custom-protocol --manifest-path src-tauri/Cargo.toml`: PASS, desktop build and **6 Rust tests**. The first query bridge compile exposed an unavailable optional reqwest method; fixed with the existing URL-pair encoder, with no dependency/lock changes.
- `dotnet restore Rigarus.sln --locked-mode`, `dotnet format whitespace Rigarus.sln --verify-no-changes --no-restore`, `dotnet build Rigarus.sln -c Release --no-restore`, `dotnet test Rigarus.sln -c Release --no-build --no-restore`: PASS, **35 historical baseline tests**, zero build warnings/errors.
- Windows PowerShell 5.1 `scripts/Test-TauriAcceptanceHarness.ps1`: PASS. `git diff --cached --check` and Windows PowerShell 5.1 `scripts/Test-RepositoryPrivacy.ps1`: PASS, **174 indexed paths**. Actual PR CI is recorded in the PR/Issue verification follow-up; no pending gate is assumed to pass.

Host GUI: Windows 11 Pro x64 build 26200, preinstalled WebView2, networking/developer tools available. This is not an offline pass. Initial host harness runs exposed an incorrect browser selector, PowerShell dynamic variable shadowing and intermittent index-based select input. Original Foreman helper was restored unchanged. The #14-only helper now checks real focus and actual committed ValuePattern text with explicit synthetic choices; final original-script run passed. Initial failed logs remain local and are not presented as successful runs.

All native probes retain existing bounded profiles (Default GUI 30 s / exit 12 s; SlowVm GUI 150 s / exit 60 s). The VM worker has a 1,500 s cap and the local launcher a 1,600 s cap. No wait is unlimited.

Offline VM: independent disposable QEMU overlay, Windows 11 IoT Enterprise LTSC Evaluation x64 build 26100, preinstalled WebView2, no virtual NIC (`-nic none`), `NetworkAvailable=False`, no developer commands found, administrator membership/elevation both false. The final candidate completed Civil/Tower selection, AM/PM, collision rejection, repeated WorkItem visits, no-write form cancellation, edit, saved cancellation and slot reuse. Application restart preserved three Draft visits and one Cancelled record, stable IDs, notes and cross-year dates. Normal exit and startup-failure feedback passed. After normal guest shutdown, read-only evidence extraction verified all **86 candidate files** against the payload manifest and found `OFFLINE_DRAFT_RESULT=PASS` / `DRAFT_GUI_EXIT=0`. This tests the candidate program; it does not claim installation of a new CI installer, missing-WebView2 installation, OS reboot retention or managed-enterprise-policy acceptance.

## Design comparison and remaining work

Original Figure 2 supports Assign per concrete WorkItem. Figure 1 and Schedule written guidance establish the future weekly board. This slice honestly displays the persistent selected Crew/date/slot and preserves existing shell styling; it does not substitute a list or screenshot for the #16 seven-day grid. Actual screenshots/states at 1440/768/390 and forms at 768/390 were checked: final inspector **0 FAIL / 0 WARN**, no page overflow. Dates are kept intact; long text wraps and the table scrolls inside its frame. Complete DOCX/original figures remain local.

- **#16 not implemented:** Sunday–Saturday grid, sticky Crew/date headers, week navigation, nine-Crew aligned roster/grid scrolling, multi-day blocks, collapsible panels and published-version board. The range API is ready for its next separate PR.
- **#22 not implemented:** home-roster overlay, persisted time off/OFF labels, actual date/half-day employees, temporary transfers and their history/impact. No absences or approved drivers were invented.
- **Other pending gates:** complete #15/#23 safety/publish validation, staffing/driver/Rig policies, remaining-work/AM-PM customer decisions, published versions, production-layout reporting and operational backup/restore.

Raw logs, synthetic databases/backups, screenshot reports, original source extraction and VM traces are retained in the local Issue #14 evidence folder. Only sanitized records/source/tests are submitted to GitHub. Engineering verification, human PR review, customer Demo B and production approval remain distinct. No automatic merge, Issue closure, release or real customer database modification.
