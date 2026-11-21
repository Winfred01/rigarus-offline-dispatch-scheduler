# Issue 65 Project editor engineering evidence

Baseline `8219fe13f94866458f942ae2bd7e62f983abe2ff`, branch `codex/issue-65-project-validation`, after the owner's merge of PR #68. See [Design-First checklist](../design/2026-11-21-issue-65-project-validation-checklist.md) for documents/versions, original Figure 2A, conflicts and the plan output before product edits.

## Resulting behavior and compatibility

New/Edit Project has a prominent title, grouped work items and primary Save / secondary Cancel. Save retains drafts, highlights only invalid controls/rows and focuses/scrolls the first invalid field in visible order. The bottom summary links to individual controls. Correction clears only that error; removing a new draft row removes its errors without discarding other rows. Stable keys are not reused after removal.

Six keyboard focusable helps explain uniqueness, text Site IDs/leading zeroes, descriptive site names, Small/Civil/Tower/Other, positive whole crews and whole half-days (`1 = 0.5 day`, `4 = 2 days`). Native auto-popovers open one at a time with Escape/Close. Text/attention markers, ARIA descriptions and an announced summary supplement error colors. Valid 2 crews / 4 half-days remain accepted. No guessed four-digit/character/length restriction or new business default.

Canonical duplicate/invalid-text responses target the corresponding input; unknown storage/service errors remain separate and do not mark valid fields red. Existing API, SQLite transactions/schema/path, IDs, enums and requiredness are unchanged. No migration required; restoring the former UI leaves saved data intact. Backend regressions cover invalid/duplicate writes, ownership, rollback, reopen and legacy compatibility.

## Reproducible local checks

Windows 11 Pro x64 development host build 26200; WebView2 157.0.4341.60; network available, developer tools present. Native tests use isolated temporary synthetic profiles, never the customer's installed database. Independent no-bundle 0.1.0 candidate; historical installer unchanged:

- Desktop SHA-256 `3fdc57116aea320a712531243ed075e4ba54c42debcd306218109142ad7c561b`.
- Sidecar SHA-256 `5871472ac4766a8ba9900d80fa3e0afcc395d9c30555effdc4c9a2f7d096490f`.

| Check / executed command | Actual result |
| --- | --- |
| Backend `uv sync --locked --group bundle`; `uv run --locked ruff check`; `uv run --locked ruff format --check`; `uv run --locked python -m unittest discover -s tests -v` | PASS, 49 tests, including whitespace/NUL, open identifier formats and valid 2/4 |
| `scripts/Build-RigarusSidecar.ps1`; set `RIGARUS_SIDECAR_TEST_EXE`; `uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v` | PASS, fresh bundle and 5 packaged protocol tests |
| Frontend `npm ci`; `npm run format`; `npm test`; `npm run build` | PASS, 14 tests including text/count boundaries, duplicate mapping, stable keys and sorting; production TS/Vite |
| Rust 1.95.0 `cargo fmt --manifest-path src-tauri/Cargo.toml --check`; `cargo fetch --locked --offline --manifest-path src-tauri/Cargo.toml`; `npm run tauri -- build --no-bundle -- --locked`; `cargo test --release --locked --features tauri/custom-protocol --manifest-path src-tauri/Cargo.toml` | PASS, native release executable and 4 Rust tests |
| `dotnet restore Rigarus.sln --locked-mode`; `dotnet format whitespace Rigarus.sln --verify-no-changes --no-restore`; `dotnet build Rigarus.sln -c Release --no-restore`; `dotnet test Rigarus.sln -c Release --no-build --no-restore` | PASS, 35 historical compatibility tests; build without warnings/errors |
| Windows PowerShell 5.1 `scripts/Test-TauriAcceptanceHarness.ps1` | PASS, 9 bounded wait/failure scenarios, including intentionally failing synthetic cases |
| Windows PowerShell 5.1 STA `scripts/Test-TauriDesktop.ps1 -Executable <candidate> -IncludeProjectValidation -IncludeBulkProjects -IncludeProjectSorting -IncludeCrews -DiagnosticLog <local-log>` | PASS, final host run 17.930 seconds; field/summary/help/Tab/Shift+Tab/Enter/Escape/removal/offscreen-focus/valid-save/reopen plus Project Master, bulk clipboard/confirm, sorting, crews, note, startup recovery and child exit |
| Actual React browser interactions, explicitly mocked IPC | PASS: invalid saves suppressed; ARIA/summary focus; valid 2/4; stable row removal; drafts retained; six one-at-a-time helps; Tab/Shift+Tab/Enter/Escape/Close help; duplicate targeting; generic failure not mislabeled. This is not SQLite/native proof |
| Chromium inspection at 1440 / 768 / 390 pixels | PASS interaction/layout review; 0 FAIL, 1 automated WARN for empty desktop space below a short form. All six fold/page images plus valid/error/help images inspected; no horizontal page overflow/truncated field labels. Empty application canvas is intentional |

Initial sandbox runs blocked Python loopback and .NET named pipes/restore; normal approved local process/network reruns passed. A Rust format command used the wrong directory, corrected before passing. Browser setup initially lacked its temp directory and Enter text event; correcting the harness made keyboard checks pass. No product validation was bypassed; failed raw logs stay local.

## Independent offline Windows VM

First run **FAIL**: `field-help-escape-dismissed` timed out at 150 seconds on the third help; script exit 2. Prior two helps dismissed successfully. Preserve this failed run rather than treating the timeout as a pass. The harness now confirms keyboard focus on the trigger, opens with Enter, then confirms focus on Close help inside the specific visible popover before Escape. The same product binaries passed the updated host script. Final same-VM retry results, timings, evidence locators and current-head CI are recorded on [Issue #65 and its linked Draft PR](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/65); this first failed attempt alone does not establish offline success.

Prepared environment: fresh overlay over the authorized Windows x64 test image, separate UEFI variables, read-only ISO and **no virtual NIC**. Backing image, existing installer and host components are unchanged.

## Design comparison and remaining gates

Compared against local Figure 2A and written corrections. Existing Segoe UI/teal shell retained; title/grouping strengthened. Actual errors use `0` crews / `1.5` half-days, rather than the mockup's false-red 2/4. Help uses one centered native popover instead of simultaneously illustrated bubbles. Error text wraps; fields stack in narrow windows. Screenshot/ARIA review does not replace a person using a screen reader.

- **NOT RUN:** actual screen-reader usability with named assistive technology and human reviewer.
- **NOT RUN:** matching installer execution, upgrade/uninstall, absent-WebView2 provisioning, guest reboot and enterprise policy. An unpacked bundle test is not installer acceptance.
- **Open / #41:** Site ID requiredness, Job # characters and non-ASCII case semantics; preserve existing invariants.
- Customer Demo A signoff and production approval remain **pending**.

Staged privacy scan **PASS** for 158 indexed paths; staged whitespace, PowerShell syntax and changed Markdown links **PASS**. Final Windows CI and VM results are recorded against the delivered commit in the linked Draft PR, separately from this historical first-attempt failure. Original design, screenshots, raw diagnostics, databases and VM media stay local. Only sanitized Markdown and synthetic code/tests are published. No automatic merge, release or Issue closure.
