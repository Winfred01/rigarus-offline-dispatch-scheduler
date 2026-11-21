# Issue 45 Excel clipboard engineering evidence

Baseline `57c2fbc12074063ef16cd9170c2d23de35d5c115`, branch `codex/issue-45-excel-clipboard`. This continues merged bulk PR #64 after the owner merged Design-First PR #67. See the [current design checklist](../design/2026-11-21-issue-45-clipboard-checklist.md) for sources, versions, Figure 3A and the implementation plan.

## Resulting behavior and compatibility

Bulk Add accepts header-inclusive Excel TAB-separated clipboard text and existing CSV. Detection uses the fixed header, not punctuation in project values. It preserves quoted delimiters/newlines, doubled quotes, identifiers and physical source lines. Repeated header rows produce Invalid / Skip feedback instead of creating a project. Existing .xlsx/template validation and limits remain.

The input is labeled Paste from Excel or plain text and has Ctrl+C/Ctrl+V guidance. Both synthetic monospace examples have real Copy actions and exact TAB/CSV separators. Denied/unavailable clipboard access selects the example and gives Ctrl+C instructions without reporting success. Copy alone changes neither input nor database. Five native auto-popover help controls provide format, row, read-only preview, no-overwrite and limit explanations; keyboard activation, Escape and Close help are available.

The API input shape, SQLite schema, database path and transaction implementation are unchanged. Preview and Cancel remain read-only. Input/file/tab changes invalidate confirmation. Confirm revalidates and inserts only eligible new projects under the existing transaction, preserving Project/WorkItem IDs and fields, with rollback and duplicate/stale protection. No database migration, installer strategy or customer business default changes. #65 New Project UX remains outside this PR; its local staged draft was not copied.

## Reproducible local checks

Windows 11 Pro x64 development host, build 26200; networking available; developer tools present; WebView2 157.0.4341.60. Native GUI tests use a fresh temporary synthetic profile and the independently assembled executable/sidecar candidate. Historical 0.1.0 installers and prior VM results are not replaced.

| Check / command | Actual result |
| --- | --- |
| Backend: `uv sync --locked --group bundle`; `uv run --locked ruff check`; `uv run --locked ruff format --check`; `uv run --locked python -m unittest discover -s tests -v` | PASS, 48 tests |
| `scripts/Build-RigarusSidecar.ps1`, then set `RIGARUS_SIDECAR_TEST_EXE` and run `uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v` | PASS, rebuilt PyInstaller process and 5 protocol/packaged tests |
| Frontend: `npm ci`; `npm run format`; `npm test`; `npm run build` | PASS; 5 existing sorting regressions and production typecheck/bundle |
| Rust 1.95.0: `cargo fmt --manifest-path src-tauri/Cargo.toml --check`; `cargo fetch --locked --offline --manifest-path src-tauri/Cargo.toml`; `npm run tauri -- build --no-bundle -- --locked`; `cargo test --release --locked --features tauri/custom-protocol --manifest-path src-tauri/Cargo.toml` | PASS; native release executable and 4 Rust tests |
| `dotnet restore Rigarus.sln --locked-mode`; `dotnet format whitespace Rigarus.sln --verify-no-changes --no-restore`; `dotnet build Rigarus.sln -c Release --no-restore`; `dotnet test Rigarus.sln -c Release --no-build --no-restore` | PASS; build without warnings/errors, 35 compatibility tests |
| Windows PowerShell 5.1: `scripts/Test-TauriAcceptanceHarness.ps1` | PASS; 9 bounded wait/failure scenarios, including intentionally failing synthetic cases |
| Windows PowerShell 5.1 STA: `scripts/Test-TauriDesktop.ps1 -Executable <candidate> -IncludeBulkProjects -IncludeProjectSorting -IncludeCrews -DiagnosticLog <local-log>` | PASS, 13.962 seconds on the final host run; exact clipboard delimiters for both examples, preview, help/Escape, CSV edit/Cancel/confirm, TSV confirm/retry/reopen, preserved IDs/zeroes, sorting/crew/note/recovery and child exit |
| Browser-only permission-denied Copy / help states | PASS; rejected write selects the matching example, announces the failure, leaves input untouched; one help popover, Escape dismissal, no JS exceptions |
| Final Chromium visual inspection at 1440, 768 and 390 pixels | PASS, 0 FAIL / 0 WARN; all six generated fold/page images inspected locally. Narrow example fields scroll horizontally; the page does not. This does not establish a web/mobile product target. |

The first native attempts used UI Automation Invoke for native popover controls and synthetic clipboard activation. The former exposed Unsupported Pattern; later clipboard calls timed out without a real user gesture. The harness now uses focus plus Enter for Copy and the exposed ExpandCollapse pattern for native popovers. The full run passed afterward; unsuccessful diagnostic logs remain local. No product validation was bypassed.

Final candidate executable SHA-256: `583437996cdd2909c2688a130ca11d7e3a9438ebc9386d37a698fd20ded866de`. Packaged sidecar SHA-256: `c286c02a9e117e476d9ebeb953e3f09dda20c4f6cc4d887168693e2888329ef9`. The final executable includes the final TAB display alignment. The final host run and final browser inspection use this same final implementation. The VM result below must identify the final executable explicitly.

## Independent offline Windows VM

**PASS**, Windows 11 IoT Enterprise LTSC Evaluation x64 build 26100, QEMU TCG 4 vCPU / 6 GiB. A dedicated overlay backed by the existing authorized test image, separate UEFI variables and a read-only ISO were used; the existing backing image was not edited. No virtual NIC was configured. Preflight reported `NetworkAvailable=False` and zero available `node`, `python`, `rustc`, `cargo`, `dotnet` commands. This is an engineering VM, not a managed customer PC.

The guest printed the final executable SHA-256 above, matching the host and ISO manifest. Windows PowerShell 5.1 ran the current desktop script with `-RequireOffline -Profile SlowVm -IncludeBulkProjects -IncludeProjectSorting -IncludeCrews`. Final output: `status=PASS phase=desktop-smoke elapsedMs=300448`, `OFFLINE_CLIPBOARD_GUI_EXIT=0`, `OFFLINE_CLIPBOARD_GUI_RESULT=PASS`. The suite covers exact clipboard separators and both example previews, format help/Escape, existing CSV invalidation/Cancel/confirm, TSV confirmation/retry, preserved Project/WorkItem and identifier values after reopen, sorting, crew and note persistence, startup failure instructions and process exit. GUI probes were bounded at 150 seconds and exit waits at 60 seconds.

Local evidence includes the ISO payload manifest, VM arguments, immutable final candidate, QEMU action trace and screenshots `007-vm-test-progress.png` (OS/network/tools/hash), `009-vm-clipboard-stage.png` (both successful Copy confirmations), and `011-vm-final-result.png` (exit 0/PASS and clean-exit events). Guest logs and synthetic data remain on the dedicated local overlay. This is an unpacked bundled-executable check; installer execution, upgrade/uninstall, absent-WebView2 provisioning and guest reboot were not performed for this candidate.

## Design comparison and remaining gates

Compared the actual implementation with the local November 21 UI design, Figure 3A. The existing Segoe UI/teal shell and transaction UI are retained. Two explicit TSV/CSV example fields satisfy the Issue's expanded requirement; the concept shows one visual sample. Help is a small centered native popover instead of the illustration's permanently open bubbles. Only one is open at a time. No layout overlap was observed in the inspected states. No new design direction, online fonts/assets or personnel examples were introduced.

Native .xlsx file selection/template download were not newly repeated in this clipboard slice; backend and packaged-sidecar Excel regressions passed. Microsoft Excel application copying, current installer/upgrade/uninstall, absent-WebView2 provisioning, VM reboot and customer enterprise policy are NOT RUN here. Source input is synthetic true-TAB text, not proof that an Office application was present. Site ID requiredness and Job # character/non-ASCII decisions remain pending #41; existing database invariants stay in force. Code/Status/Assign and #65 remain outside scope.

Staged privacy scan **PASS** for 152 indexed paths, staged whitespace check **PASS**, PowerShell syntax and changed Markdown relative links **PASS**. Final Windows CI is recorded in the Draft PR against its actual head. Raw logs, screenshots, clipboard payloads, source DOCX and synthetic databases stay local. Engineering verification does not constitute customer Demo A acceptance or production approval. No automatic merge, release or Issue closure.
