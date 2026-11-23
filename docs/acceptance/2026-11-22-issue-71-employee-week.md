# Issue 71 — Employee Week engineering evidence

November 22, 2026 client date. Baseline main `c10ce66ce0a3177a04cc75404e7b0e21b38f0d55`, after human merge of PR #78; main CI `45096686344` passed all three jobs. Branch `codex/issue-71-employee-week`. Source versions, original UI figures, mapping, plan and boundaries are in [the Design-First checklist](../design/2026-11-22-issue-71-employee-week-checklist.md). This is a first read-only planning/preview slice, not completion of all #71.

## Implemented and intentionally deferred

Schedule → Employee Week uses actual explicit latest configured Employee IDs and inclusive local week queries. It never expands Home Crew into attendance. A dated card shows AM/PM, Job #, Site ID/name, WorkItem ID/type, actual Crew, borrowed marker and record revision. Home Crew remains separate; Actual Rig is explicitly Not assigned, never inferred from a default vehicle. Inactive and Unverified master states remain visible. Recorded AM/PM availability is an independent administrative label, not approved leave/OFF, weekend consent or dispatch eligibility.

The selected Schedule date and employee are in-memory app navigation state. Directory names open the selected person's week; global-search Person detail offers Open employee week. Both retain the selected week. No jobs retain all seven Unscheduled dates. Old employee/week cards disappear immediately on switches or failed reads; delayed responses cannot populate another identity. Assignment, availability and roster failures have distinct retry paths. Read-only card details and copied preview rows use the same IDs/dates/revisions. Preview visibly says DRAFT – NOT CONFIRMED and PDF/Excel remain disabled. There is no download, file-write, publication or schedule-mutation path.

Original UI 16/17/18/20/42 were visually inspected against actual native calendar/preview/empty captures. The existing desktop shell and seven-day table are retained. Deliberate differences: actual Rig/WorkItem description are not invented from prototype examples; availability uses the owner's confirmed three states, not approved OFF; full formal publishing/export remains disabled. The employee page is read-only; assignment edits remain on Job Schedule. Existing 12px secondary card/availability metadata produces one inspector warning, retained for layout review rather than claimed as human accessibility certification.

No dependency, SQLite migration, HTTP endpoint or Rust command was added. Existing schema nine, employee-filtered assignment query and availability read are reused. Prior schema migration/recovery evidence is unchanged; no operational database was downgraded or modified. All generated records and test profiles are synthetic. The repository was verified PUBLIC. Original design files, screenshots, raw diagnostics, databases and backups remain local.

## Candidate and executed checks

Final standalone client SHA-256 `dff567842919bf1e7418460ad18f08c2f85afa3496b025426cff82cede470235`; matching packaged sidecar `ec5d5646eb2681e7fe509ba75de42a5c51ef781d8b25e1a99f8ff5c0d0c01fa8`. Native verifier `c6aa2da768bc70da44d9ad3946a2b1844ee37e7499bee314a28a96855ee6c0ec` is the working UTF-8-BOM/CRLF file; committed LF is equivalent after newline normalization. These are local candidate hashes, not the later CI installer's digest. Runtime version label stays 0.1.0.

| Check | Result | Conditions and actual coverage |
| --- | --- | --- |
| Backend locked restore / Ruff lint+format / unittest | PASS, 92 | Existing contracts, schema-nine compatibility and employee/availability reads; no backend source changes |
| Actual newly packaged sidecar | PASS, 10 | Authenticated loopback, persisted records/restart and pipe shutdown |
| Frontend locked offline restore / format / TypeScript / Vite | PASS | Existing project cache/lockfile; no dependency additions |
| Frontend tests | PASS, 34 | 30 prior checks plus four explicit-membership/cancelled/range/ordering/defensive-filter regressions; source rows remain unchanged |
| Rust locked offline fetch / format / Windows Release / tests | PASS, 7 | Existing native bridge/lifecycle regression |
| Historical .NET locked restore / format / Windows Release / tests | PASS, 35 | Compatibility baseline only |
| Windows PowerShell 5.1 harness | PASS | Existing bounded success/failure/date/WAL/weekly probes |
| Final native -IncludeEmployeeWeek | PASS, 46.304 s | Windows 11 Pro x64 build 26200, network active, developer tools/WebView2 preinstalled. Actual Tauri/Rust/packaged FastAPI/SQLite. Includes #77/staffing/assignment/Crew fixtures, explicit employee, empty inactive employee, availability, disabled preview export, directory week handoff, no-write SQLite/WAL checks before and after reopen, normal sidecar exit and startup-error/Retry |
| Independent retained SQLite audit | PASS | Nine migrations, 101 projects, four visits, only Employee 1 explicitly selected. Both Home Crew IDs remain 2; driver Unverified. Three retained availability events/cells, integrity ok/no FK errors |
| Browser interactions | PASS | Separate loopback proxy to actual packaged backend: three visits/mixed AM-PM, actual borrowed Crew, seven empty dates, identity/delayed-response race, assignment failure clears cards/disables preview, availability failure stays distinct, roster failure recovery, directory and global-search handoff, read-only detail/preview, Escape, no IPC write/console error |
| Visual/layout comparison | PASS with one WARN | Actual native screenshots use Rust IPC, no proxy. Browser document bounds at 1440/768/480/390; internal seven-day scrolling. App inspector confirms Employee Week at 1440/768/390, zero FAIL/one tiny-text WARN for secondary metadata |
| Final staged privacy / document links / Windows CI | Recorded in PR | Run on final index/head; no transfer of prior PR/main CI conclusions |

Representative executed commands: `uv sync --locked --group bundle`, `uv run --locked ruff check`, `uv run --locked ruff format --check`, `uv run --locked python -m unittest discover -s tests -v`; root `scripts/Build-RigarusSidecar.ps1` then actual packaged `test_sidecar.py`; `npm ci --offline`, `npm run format`, `npm test`, `npm run build`; `cargo +1.95.0 fetch --locked --offline`, `cargo +1.95.0 fmt --check`, `npm run tauri -- build --no-bundle -- --locked`, locked Release Rust tests; historical locked .NET restore/format/build/test. Commands use each project's working directory. The native walkthrough gives the full -IncludeEmployeeWeek command and bounded Default 30/12-second or SlowVm 150/60-second GUI/exit waits.

An initial native attempt timed out on the AM availability text: the paragraph's accessible name exposed its date but omitted the state. The date paragraph now names both current AM/PM states from the same renderer function; final native and browser checks passed. A separate browser test initially clicked the global-search handoff before asynchronous record details finished loading; its bounded wait now observes the actual button. Failed logs are retained locally and not counted as passes. A prior native pass was 46.400 s before the final SQLite/WAL no-write assertions; final reported verifier passed in 46.304 s.

## Remaining gates

NOT RUN for this candidate: disconnected installation/upgrade, missing-WebView2 setup, guest OS reboot, uninstall/reinstall, target enterprise policy and human screen-reader checks. The existing isolated evaluation VM self-powered off during the prior #77 attempt; its expired-license watermark was observed but cause not established. It is not a completed offline runtime pass, nor a basis for reusing a previous installer result. A stable authorized Windows 11 x64 image is required for that independent gate; no host clock/activation/security/network policy or reboot was changed.

Formal local PDF/XLSX, immutable validated Published snapshots, safety/driver/resource/leave rules and actual dated Rig remain #71/#15/#23/#17/#32/#22 follow-ups. Customer Demo B/D/export-layout acceptance: NOT RUN. Production approval: NOT GRANTED. One Draft PR for human review; no automatic merge, Issue closure or Release.
