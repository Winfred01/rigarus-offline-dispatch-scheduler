# Issue #8 Foreman master-data engineering evidence

November 21, 2026 local / November 22 UTC. Refs #8; this is the remaining M1 appointment/history slice after the merged Crew and Employee work. It does not implement #25 scheduling eligibility or constitute customer Demo A/D acceptance. See the [Design-First record](../design/2026-11-21-issue-8-foreman-checklist.md) for source revisions, original UI locators, the owner's explicit scope approval and implementation plan.

## Baseline and candidate identity

- Latest fetched main at inspection: `7c91c2a7f94d63faf387c64f1518c8ea3d0933e3`; main Windows CI [44949432528](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/44949432528) succeeded. No open PRs at preflight. Repository visibility is PUBLIC, so only synthetic/sanitized evidence is included.
- Reused clean isolated branch `codex/issue-8-crew-roster`, fast-forwarded from `b4e8b05` to main. Original main checkout and unrelated worktree changes were preserved.
- Local Windows x64 development candidate: version `0.1.0`; desktop SHA-256 `edc301c988f309e175269ba31c2d7d87c36f4996a1cbddcf7f9f3c8913f91ef1`; bundled sidecar SHA-256 `b8e8cac0a5f6a1164465b4a71673134014b7f482cb4f931078bec357ebd0baec`. This source tree is the product change in this PR; these hashes identify the locally built candidate, not a GitHub installer.
- Existing PR #69 installer and its previous installed-package evidence remain unchanged. This slice requires a sixth SQLite migration; do not use the previous installer as proof of this feature.

## Reproduction and results

Use only temporary synthetic profiles. Run the existing build commands with the checked-in lock files; native GUI commands require an interactive Windows desktop. Record the actual tested executable hash separately from CI's installer.

| Case | Reproducible steps / assertion | Result |
| --- | --- | --- |
| Appointment lifecycle | Two Crews, two active eligible employees with the other Home Crew; appoint A, select B then cancel, reopen A, replace with B, clear, appoint A, reopen | PASS in Python and native Windows UI; four history entries remain newest first |
| Candidate validation | Missing/inactive/ineligible IDs, booleans/fractions/string IDs, missing revision or unsupported effective date | PASS; 422 and no write |
| Current status and immutable names | Rename/deactivate B and remove eligibility after appointment; inspect current status and earlier records | PASS; current name/warnings update, old snapshots/IDs remain; no automatic clearing |
| Home Crew and Driver | Read both employees after cross-Home-Crew appointments, replacement and clear | PASS; Home Crew unchanged and Driver Unverified in backend/native table checks |
| Stale/concurrent changes | Save two different employees from revision zero concurrently; retry stale revision | PASS; one winner, stale request 409, no overwritten event |
| Append-only history and references | Attempt UPDATE/DELETE history and deletion of referenced Crew/Employee in synthetic SQLite | PASS; triggers/FKs reject, history unchanged |
| Write failure and retry | Inject failing BEFORE INSERT trigger, save replacement, remove trigger and retry from retained revision | PASS; 503 without raw SQL diagnostics, old state intact, retry works |
| Read failure privacy | Inject SQLite read error with a synthetic private-path marker | PASS; actionable 503, marker absent |
| Migration rollback and retry | Upgrade synthetic Rig schema; inject failure when recording new migration after DDL; remove failure and retry twice | PASS; DDL/history roll back, all six existing table snapshots/IDs remain, integrity ok and no FK errors |
| Legacy upgrade and fallback | Existing M0/Project/Crew/Employee regression; separate experiment using actual `7c91c2a` backend source and consistent SQLite backup | PASS; older backend rejects upgraded schema without DB byte changes; original backup remains readable with the older backend |
| Actual bundled sidecar | Unauthenticated GET / wrong-token PUT, authenticated appointment, stdin-close exit, restart/history, stale write and clear | PASS; included in six packaged-sidecar cases |
| React states and keyboard | Actual built React UI with explicitly mocked IPC: candidate filtering, retained warnings, cancel/focus return, stale failure, lost-response reload, load failure/retry, empty/no-candidate, loading | PASS; no console errors. Mocked IPC is not database/offline proof |
| Native host GUI | `Test-TauriDesktop.ps1 -Executable <candidate> -IncludeForemen -DiagnosticLog <local-log>` | PASS; full lifecycle, note/Crew smoke, app reopen, sidecar exit 0 and startup-failure hint; about 19.1 seconds total |
| Independent disconnected VM | Same candidate on new no-NIC Windows test overlay, `-Profile SlowVm -RequireOffline -IncludeForemen -IncludeProjects` | PASS on its first VM run; worker/launcher exit 0; note/Project/Crew/Foreman persistence, four history entries, startup-error hint and sidecar exit 0 |
| Human assistive-technology / customer review | Real screen-reader review and customer Demo A/D field/workflow sign-off | NOT RUN; not replaced by ARIA/UI Automation |
| This feature's installer/enterprise rollout | New CI installer installation, managed-device policy and production data upgrade | NOT RUN; separate acceptance gates |

The native host was Windows 11 Pro x64 build 26200, WebView2 directory version `157.0.4341.60`, with developer tools and networking available. Its result is not an offline pass. The bounded Default profile uses GUI 30 s / exit 12 s. SlowVm uses GUI 150 s / exit 60 s; the VM worker is separately supervised for at most 1,200 s. No wait is unlimited.

The independent VM was Windows 11 IoT Enterprise LTSC Evaluation x64 build 26100 on QEMU TCG, 4 vCPU / 6 GiB, with no virtual NIC. Preflight reported `NetworkAvailable=False`, zero Node/Python/Rust/Cargo/dotnet commands, `AdministratorMember=False` and `elevated=False`. It used a new overlay of the previously authorized PR #69 fresh-install test image, preserving that source disk, with its existing WebView2 runtime. The candidate and scripts arrived on a read-only ISO, then ran from an isolated local candidate directory and temporary synthetic database. The complete GUI smoke took 293,274 ms; the Foreman reopen check passed at 260,942 ms. This was a candidate feature test, not an installation or upgrade test; the reused local launcher title contains the historical word “Upgrade” but this script invokes no installer. It does not establish missing-WebView2 installation or representative enterprise-device behavior. The test VM was normally shut down for read-only log extraction; all 86 candidate program/resource files in the guest matched the host payload SHA-256 manifest. Extracted logs confirmed PASS with no FAIL/TIMEOUT events. Host security and customer databases were unchanged.

Initial local harness runs exposed a same-name heading/table locator, a PowerShell reserved-variable mistake, unsupported select-pattern assumptions, a missing type/ID suffix in the expected Home Crew label and rapid-key timing. These test defects were corrected using unique table labels, existing displayed values and bounded key intervals. Final host run exited 0. Initial failures and diagnostic logs remain local; they are not presented as successful runs. No product persistence defect was inferred from those harness failures.

## Commands actually executed

- `uv sync --locked --group bundle`; `uv run --locked ruff check`; `uv run --locked ruff format --check`; `uv run --locked python -m unittest discover -s tests -v`: PASS, 56 tests.
- `scripts/Build-RigarusSidecar.ps1`; packaged `RIGARUS_SIDECAR_TEST_EXE` with `uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v`: PASS, 6 tests.
- `npm.cmd ci`; `npm.cmd run format`; `npm.cmd test`; `npm.cmd run build`: PASS, 14 frontend tests and TypeScript/Vite build.
- `cargo +1.95.0 fetch --locked --offline --manifest-path src-tauri/Cargo.toml`; `cargo +1.95.0 fmt --manifest-path src-tauri/Cargo.toml --check`; `npm.cmd run tauri -- build --no-bundle -- --locked`; `cargo +1.95.0 test --release --locked --features tauri/custom-protocol --manifest-path src-tauri/Cargo.toml`: PASS, Windows desktop and 4 Rust tests.
- `dotnet restore Rigarus.sln --locked-mode`; `dotnet format whitespace Rigarus.sln --verify-no-changes --no-restore`; `dotnet build Rigarus.sln -c Release --no-restore`; `dotnet test Rigarus.sln -c Release --no-build --no-restore`: PASS, 35 historical baseline tests; build has zero warnings/errors.
- Windows PowerShell 5.1 `scripts/Test-TauriAcceptanceHarness.ps1`: PASS for synthetic wait/failure scenarios.
- Staged whitespace/privacy and actual PR Windows CI are recorded in the final PR verification follow-up; no pending result is assumed here.

## Design comparison and remaining gates

Original local November 21 DOCX Resources description and Figure 1 establish the Foreman concept and roster identity, not an appointment editor specification. The owner approved the bounded master-data workflow before implementation. The editor extends the existing Crews page and established typography/colors; the Schedule concept was not copied into this milestone. Complete UI DOCX and original images remain local.

Actual browser screenshots at 1440, 768 and 390 px were inspected, including success/current-warning, conflict, loading and empty states. The final inspector reported 0 FAIL / 0 WARN and zero page-level horizontal overflow at all widths. Dates stay intact; history scrolls within its frame, long names and warnings wrap, and controls/focus remain visible. The first review found a history-table style-specificity problem; the final scoped styles fix it. The intentionally familiar resource form is not a complete Schedule/Resources visual redesign. This browser review is separate from native and disconnected verification.

Local evidence is retained under the Issue #8 engineering-evidence folder: source metadata, payload hashes, compatibility result, initial/final native logs, browser screenshots/reports and isolated VM traces. No raw diagnostics, database, backup, customer/personnel data, original spreadsheet/PDF or DOCX is uploaded. Engineering verification, human merge review, customer acceptance and production approval remain separate; no automatic merge, release or Issue closure.
