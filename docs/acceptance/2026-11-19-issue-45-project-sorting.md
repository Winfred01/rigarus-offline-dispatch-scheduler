# Issue #45 existing-column sorting engineering evidence

## Scope and environment

Branch: `codex/issue-45-project-sorting`, based on main `e51207ad9f6e05bbc37c9c5e4b89abe4bc483ace`. The UI adds independent sorting to the existing Projects and Project work items columns. It makes no schema, API, scheduling or installer changes. The original 0.1.0 installer is unchanged.

Native GUI verification ran on the authorized Windows 11 Pro x64 development host (build 26200), with preinstalled WebView2 157.0.4341.60 and the host network available. It used the release Tauri executable and packaged Python sidecar, with a fresh temporary synthetic SQLite directory supplied through `RIGARUS_SMOKE_DATA_ROOT`. This is a developer-host GUI test, not clean-image installation or disconnected-VM acceptance.

Tested executable SHA-256: `6905FD1AD7678FF433C2AA06E65570D41BD9EB216624916B9665ABEBC1965D10`.

Local diagnostic evidence is retained under the ignored worktree path `artifacts/i45-sorting-gui.log`. Raw local logs and databases are not included in GitHub. The PR records its exact commit and CI run separately.

## Reproduction and results

Run on an interactive Windows desktop from the checked-out branch, after building the sidecar and native executable:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File scripts/Test-TauriDesktop.ps1 -Executable src/Rigarus.Tauri/src-tauri/target/release/rigarus-dispatch.exe -IncludeProjectSorting -IncludeCrews -DiagnosticLog artifacts/i45-sorting-gui.log
```

`ExecutionPolicy Bypass` applies only to this PowerShell process. Prepare the output directory before running. For a shared Cargo target directory, replace `-Executable` with the built executable path.

The script creates SYN-SORT-2 and SYN-SORT-10 through the GUI, filters by `sort`, selects SYN-SORT-2, and reads table cells through UI Automation GridPattern after clicking each header. The work items have crew counts 10 and 2 and durations 20 and 4 half-days. It then closes and reopens the app and checks the existing Project Master and demo-note fixtures. Temporary synthetic data is removed after the run.

| Check | Result | Evidence |
| --- | --- | --- |
| Existing project columns, ascending and descending | PASS | UI Automation asserts actual row order for Job #, Site ID, Site name and Work items |
| Crew count and duration numeric ordering | PASS | GUI verifies 2 before 10 and 4 before 20 ascending, reversed descending |
| Independent table sorting | PASS | Work-item order remains while every project column changes; project order remains after Type clicks |
| Search subset and selected project | PASS | Both filtered rows, `sort` input and SYN-SORT-2 detail remain after every project sort |
| Project and work-item persistence after reopen | PASS | Existing project-master smoke passes on same temporary database |
| Demo note, normal desktop/sidecar exit and startup-error display | PASS | Desktop smoke passes; both normal launches close with exit code 0 |
| Crew roster smoke | PASS | Synthetic crew edit/search/reopen passes |
| Clean-image installation / disconnected execution of this slice | NOT RUN | No installer or network behavior changed; previous installation evidence is a separate baseline |
| Customer Demo A acceptance | NOT RUN | Requires designated customer review |
| Production approval | NOT RUN | Separate RC/UAT/handover gates |

## Build and regression commands

The following checks passed on Windows:

- `npm ci`, `npm run format`, `npm test` (5 regressions), `npm run build` in `src/Rigarus.Tauri`.
- `uv sync --locked --group bundle`, `uv run --locked ruff check`, `uv run --locked ruff format --check`, `uv run --locked python -m unittest discover -s tests -v` (31 tests).
- `scripts/Build-RigarusSidecar.ps1`, then `RIGARUS_SIDECAR_TEST_EXE` set to its output and `uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v` (4 packaged-sidecar tests).
- `cargo +1.95.0 fmt --manifest-path src-tauri/Cargo.toml --check`, `cargo +1.95.0 fetch --locked --manifest-path src-tauri/Cargo.toml`, `npm run tauri -- build --no-bundle -- --locked`, `cargo +1.95.0 test --release --locked --features tauri/custom-protocol --manifest-path src-tauri/Cargo.toml` (4 tests).
- `dotnet restore Rigarus.sln --locked-mode`, `dotnet format whitespace Rigarus.sln --verify-no-changes --no-restore`, `dotnet build Rigarus.sln -c Release --no-restore`, `dotnet test Rigarus.sln -c Release --no-build --no-restore` (35 tests).
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/Test-TauriAcceptanceHarness.ps1` (9 synthetic wait/failure scenarios).

The frontend tests execute the actual TypeScript sorting helper through Node's type stripping; the production build separately type-checks it. The path privacy allowlist is extended only for TypeScript source and frontend `.test.mjs` files. Stage the intended files, then run `git diff --cached --check` and `scripts/Test-RepositoryPrivacy.ps1` before commit.

## Remaining Issue #45 work

This PR does not close #45. Code/Status columns require corresponding product data and behavior. Bulk Add Projects, paste preview, offline template and transactional confirmation need their own continuation of the issue. Identifier ordering is recorded as a proposed customer-facing default; no scheduling rule or persisted priority is introduced.
