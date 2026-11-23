# Issue 77: recorded employee availability

Engineering slice, November 22, 2026 client date. Baseline `9694c5f9e674dd3818c6f5161cc6bc9d5805b222`; branch `codex/issue-77-availability`; parent #22. Sources, revisions, original figures, owner-confirmed decisions and the pre-implementation plan are in [the Design-First checklist](../design/2026-11-22-issue-77-availability-checklist.md). Full UI DOCX, images, raw diagnostics and databases remain local. Repository visibility was checked: PUBLIC; only synthetic source and sanitized evidence are submitted.

## Resulting behavior

People → Availability records explicit Available / Unavailable / Not recorded by stable Employee ID, local date and AM/PM. Full day writes both slots and inclusive ranges include both endpoints. Blank cells, including weekends, stay unknown. Saving replaces only selected slots; clearing removes current cells but retains an append-only range event. Same-state saves are no-ops. The 366-date limit bounds each operation, not employee eligibility. Employee selection/search, week navigation, history and inactive status are visible.

The calendar is an owner-requested extension of the original UI 13/16 weekly patterns; the original DOCX does not contain a complete dedicated availability editor. Actual native screenshots were compared with the original weekly/card and People conventions. The range form and selected-employee calendar are deliberate additions. Draft worker selection then reads the same date/slot state through one authenticated bulk query. It is advisory: saved selections, Draft visits and Home Crew are never automatically modified. All Drafts stay Validation pending and unpublishable. No leave approval, inferred Mon–Fri/weekend consent, driver/qualification/minimum staffing, Publish, export or new online service.

Read failures are errors, not fabricated Unknown. Per-employee optimistic revisions prevent stale overwrite. Uncertain saves block further writes until reload, including across editor close/reopen. A committed save followed by refresh failure clears stale cells and reports the saved outcome. The editor receives focus after the native dialog opens and restores it after the refreshed save.

## Migration and recovery

Additive migration `20261123010000_AddEmployeeAvailability` is schema nine. `EmployeeAvailability` stores sparse current cells; `EmployeeAvailabilityChanges` records immutable revisions, inclusive range, slot, state and UTC audit time. Local work dates are not converted to UTC. All cells and the history event commit in one transaction. Composite employee/change foreign keys prevent cross-employee associations. Original Project/WorkItem/Crew/Employee/foreman/Rig/Draft/staffing IDs, notes and rows are preserved.

Tests force migration DDL and partial cell/clear failures, verify rollback, retry and one concurrent winner. An independent consistent synthetic schema-eight backup was upgraded; every original table's records remained equal. The actual initializer from baseline main opened the pre-upgrade backup and rejected schema nine without changing its bytes. Operational fallback requires that consistent pre-upgrade backup and a compatible build. Never drop tables or migration history to downgrade a live database. Application backup/restore and production upgrades remain separate gates.

## Candidate and executed checks

Final standalone Windows client SHA-256 `de986cf037e4ebfbe941b45b85a2ee5e057e05161b08717b9a6b92b374962b0b`; matching packaged sidecar `380d6d423a26a40cef7ed3fb535454fb3790e4b131fd3df62cae263b25b18882`. Runtime label remains 0.1.0; existing installers were not modified. Native verifier SHA-256 `95f40639743571867a674437abaf612701821732a81674a8636a89bc56bf28de` is the working UTF-8-BOM/CRLF file; committed LF is equivalent after newline normalization. CI installer results are linked in the PR and are distinct from this local standalone candidate.

| Check | Result | Conditions / coverage |
| --- | --- | --- |
| Locked backend sync / Ruff format and lint / unittest | PASS, 92 | 80 prior checks plus 11 availability regressions and one authenticated sidecar test; inclusive Full day/AM/PM, unknown, overlap/clear/no-op, invalid/date boundaries, stale/concurrent saves, migration and partial-write rollback/retry, no Draft/Home Crew changes |
| Actual packaged Python sidecar | PASS, 10 | Authenticated routes, persisted availability/history/slot query after restart, token rejection, parent-pipe shutdown and existing contracts |
| Frontend locked offline install / format / TypeScript / Vite | PASS | Existing project cache and lockfile; no dependency change |
| Frontend regression suite | PASS, 30 | Existing weekly, multi-day, local-date and validation compatibility tests; new interaction cases run separately below |
| Rust locked offline fetch / format / Windows Release build / tests | PASS, 7 | Native bridge, URL escaping for range/date/slot queries and existing readiness/lifecycle tests |
| Historical .NET locked restore / format / Windows Release build / tests | PASS, 35 | Legacy compatibility baseline, no new WPF product feature |
| PowerShell 5.1 acceptance harness | PASS | Bounded wait/failure checks; final result recorded before commit |
| Native `-IncludeAvailability` | PASS, 38.481 s | Windows 11 Pro x64 build 26200 developer host, network active/WebView2 preinstalled. Actual Tauri/Rust/packaged FastAPI/SQLite: 101 projects, weekly board, independent Draft workers, three states/cross-year range, no-write Cancel, app reopen, sidecar normal exit and database startup error/Retry. Default GUI/exit 30/12 s |
| Independent native SQLite audit | PASS | Nine migrations, three current cells and three history events. Dec 31 AM Unavailable / PM missing Unknown; Jan 1 AM/PM Available. Employee 1 explicitly retained for Draft 4; Home Crew IDs, inactive/Unverified state unchanged; integrity ok / no FK errors |
| Browser fault and keyboard interactions | PASS | Test-only loopback proxy to actual packaged backend: range/slot/clear/cancel, employee switch and delayed response, invalid range, uncertain write/reload gate, committed-save/read-failure, history, Draft advisory/no auto deselection, read error/retry, focus/Escape, no console errors |
| Native visual comparison / browser layout | PASS | Actual native calendar/editor/history/worker captures use Rust IPC, not the proxy. Availability at 1440/768/480/390 CSS pixels stays inside the document viewport with an internal weekly scroller. General existing shell inspector at 1440/768/390: zero FAIL, one tiny-text WARN for retained secondary Crew/day metadata; no screen-reader certification claimed |
| Disconnected VM portable runtime | Recorded separately in PR | Same candidate hashes, no-NIC disposable Windows 11 x64 image, standard user and no developer commands. The bounded run is independent of the host pass; its actual result and limitations are recorded in the PR, not inferred here. This is not a fresh installer test |
| Staged document links / privacy | PASS | 20 local link targets; 206 indexed paths; no unexpected path/secret or staged whitespace error |
| Windows CI | Recorded in PR | Head-specific results, never inferred from prior CI |

Earlier native attempts remain local. The first stopped before availability because an inherited keyboard-index dropdown fixture did not save the second employee. Fixture selection now uses the existing native SelectionItem helper; product skill validation is unchanged. The second completed the availability lifecycle but an accessibility assertion could not match split status text. Worker availability is now one accessible text span and the final full native run passed. Browser testing found initial-focus and post-save-focus problems, both corrected and rechecked. These failed attempts are not counted as final passes.

Native screenshots use the actual client with an isolated SQLite backup; browser fault controls and CDP are local test tools, not shipped product paths. Logs, profiles, image sources, database backups, ISO and VM disks remain on the authorized workstation. Only sanitized summaries are sent to GitHub.

## Remaining design and approval gates

NOT RUN for the changed candidate: fresh installer setup/upgrade, missing-WebView2 installation, uninstall/reinstall, guest OS restart data lifecycle, enterprise policy/signing and application-level cross-machine restore. Host tests and portable VM execution do not certify those scenarios. Existing #35/#75 installer evidence applies only to its original recorded hashes.

Full #22 effective leave/work calendars, driver/qualification/minimum staffing and collision rules; #71 actual-job Employee Week and PDF/XLSX; validated immutable Published snapshots and distribution remain separate. Availability records are administrative input, not certified attendance or dispatch eligibility. Customer Demo acceptance: NOT RUN. Production approval: NOT GRANTED. One Draft PR waits for human review; no automatic merge, Issue closure or Release.
