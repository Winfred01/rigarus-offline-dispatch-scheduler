# Issue #45 Bulk Add Projects initial engineering evidence

Branch `codex/issue-45-bulk-add` starts at main `3f611cf75f798f61b8a18d2a392ed047cc5ed404`, after the owner merged the sorting slice in PR #63. This continuation implements the three-field Bulk Add workflow, without new schema, work-item import or scheduling behavior.

## Initial Windows checks

Environment: authorized Windows 11 Pro x64 development host, build 26200, preinstalled WebView2 157.0.4341.60, network available. Native release executable and packaged Python sidecar; fresh temporary synthetic SQLite data for every UI Automation run. Raw logs stay local in ignored artifacts.

Executable SHA-256: `7774DD51C218747B2BE099998DB84A36B22957C0CD9E939E10114072C733CABE`.

| Check | Result |
| --- | --- |
| CSV and Excel preview equivalence, errors, source references and leading zeroes | PASS, backend tests |
| Preview and template database byte hash remains unchanged | PASS, backend tests |
| Eligible-only insert and unchanged existing project/work-item IDs and fields | PASS, backend tests |
| Changed input, competing insert and repeated confirmation | PASS; stale preview rejected without extra inserts |
| Concurrent confirmations | PASS; one inserts, the other sees stale classification |
| Injected second-insert failure | PASS; whole batch rolled back and subsequent retry succeeded |
| Authenticated packaged Excel preview/confirm/template and reopen | PASS, packaged-sidecar test |
| Actual pasted-text GUI preview, edit invalidation, Cancel, confirm, duplicate retry, refresh and reopen | PASS, Windows UI Automation |
| Existing table sorting, Project Master, Crew and demo-note/recovery/exit GUI regressions | PASS, Windows UI Automation |
| Actual native Download Excel Template | PASS; valid local .xlsx produced, 22240 bytes |
| Native Excel file selection and disconnected VM execution | NOT RUN in this initial snapshot; supplemental results belong in the PR |
| Installer execution / upgrade / absent-WebView2 provisioning | NOT RUN in this slice; unchanged earlier installation evidence is separate |
| Customer Demo A acceptance / production approval | NOT RUN; separate human gates |

The first local GUI attempt timed out on an automation assertion for a combined Site ID text label that WebView2 exposes as separate nodes. The harness was corrected to read the actual table cell and the complete affected run passed. This was not an observed product data-loss failure.

## Reproducible commands

- In `src/Rigarus.Backend`: `uv sync --locked --group bundle`; `uv run --locked ruff check`; `uv run --locked ruff format --check`; `uv run --locked python -m unittest discover -s tests -v` — 43 tests passed.
- Run `scripts/Build-RigarusSidecar.ps1`, set `RIGARUS_SIDECAR_TEST_EXE` to its executable, then rerun `uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v` — 5 tests passed.
- In `src/Rigarus.Tauri`: `npm ci`; `npm run format`; `npm test` (5 tests); `npm run tauri -- build --no-bundle -- --locked`. Rust 1.95.0: `cargo fmt --manifest-path src-tauri/Cargo.toml --check`; `cargo fetch --locked --manifest-path src-tauri/Cargo.toml`; `cargo test --release --locked --features tauri/custom-protocol --manifest-path src-tauri/Cargo.toml` — 4 tests passed. A shared Cargo target directory was used locally; no existing installer was overwritten.
- At root: `dotnet restore Rigarus.sln --locked-mode`; `dotnet format whitespace Rigarus.sln --verify-no-changes --no-restore`; `dotnet build Rigarus.sln -c Release --no-restore`; `dotnet test Rigarus.sln -c Release --no-build --no-restore` — 35 tests passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/Test-TauriAcceptanceHarness.ps1` — 9 synthetic wait/failure scenarios passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -STA -File scripts/Test-TauriDesktop.ps1 -Executable <built-executable> -IncludeBulkProjects -IncludeProjectSorting -IncludeCrews -DiagnosticLog artifacts/i45-bulk-gui-pass.log` — passed. ExecutionPolicy applies only to the test process.
- Stage only the intended source/tests/docs, then run `git diff --cached --check` and `scripts/Test-RepositoryPrivacy.ps1` before commit. The PR records the actual CI run and final source commit separately.

## Compatibility and remaining scope

There is no database migration. Inserts use the existing Project model and SQLite constraints; existing records, work items, demo notes and migration history are not overwritten. Legacy migration and persistence suites remain green. Preview reads through a read-only SQLite connection; confirmation uses a single immediate transaction. Fingerprints are transient, and retries guarantee no duplicate insertion rather than durable replay receipts.

The separate Import preview screen remains read-only. Persistent batch history and historical reconciliation belong to #31. Code/Status columns still require their product data and behavior. Proposed field/duplicate conventions are in the decision register. Keep #45, #35 and #42 open for their remaining scope and human review.
