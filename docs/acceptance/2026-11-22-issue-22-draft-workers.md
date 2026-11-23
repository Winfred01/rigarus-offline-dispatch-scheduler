# Issue 22: explicit Draft workers

Engineering slice, November 22, 2026. Baseline `9b24ffeeb8d78a2632c2c54e80837cec8ff178ba`, branch `codex/issue-22-actual-staffing`. Refs #22, first persisted-membership part of Stage B; #14/#16 and their weekly/multi-day behavior are already merged. Design sources, revisions, original figures, plan and unresolved rules are in [the Design-First checklist](../design/2026-11-22-issue-22-draft-workers-checklist.md). This is not completion or customer acceptance of all #22.

## Resulting behavior

From a saved Draft card, explicitly select workers by stable Employee ID, search the roster, then Save workers to Draft or Cancel worker changes. Cards on both boards and each individual multi-day AM/PM source show the same persisted selection. A worker can be borrowed from another Home Crew without changing Home Crew. The editor identifies inactive status and Unverified driver state; it never classifies them as approved. No association and an explicitly empty selection remain distinct, pending states. Neither establishes staffing compliance.

The new authenticated staffing command shares the visit revision. Stale/uncertain writes require reload even after closing/reopening the editor. Save followed by failed refresh clears stale board rows and reports that the write committed. Date/slot/Crew/WorkItem changes record a reconfirmation event atomically with that edit; note-only edits retain workers. Explicit Cancel makes no write. Cancelled visits retain history and are excluded from default employee queries.

No new dependencies, account/network service, actual Rig inference, leave/driver/qualification/minimum-size rule, Publish, export or automated distribution. All visits remain Draft / Validation pending / `publishable=false`.

## Migration and compatibility

Migration `20261122200000_AddAssignmentStaffing` is additive after schema seven. Two tables store context/revision events and employee membership snapshots; UPDATE/DELETE triggers preserve recorded history. Migration leaves all existing tables and their Project, WorkItem, Crew, Employee, Rig, Foreman and note values unchanged. Current labels/status reflect master-data edits; history retains names and Home Crew IDs as recorded. Reads use one SQLite snapshot for assignment and staffing.

Tests force migration failure after DDL and member/audit failures after writes, verify full rollback, then retry. Concurrent selections have one winner; stale selection/edit/cancel cannot overwrite a newer visit. Existing legacy migration fixtures explicitly remove the new child schema only when constructing disposable older test databases; that helper is not an application or operational downgrade command.

An independently copied consistent synthetic seven-schema database was upgraded. All original table records remained equal; the actual initializer from main `9b24ffe` opened the pre-upgrade backup and rejected schema eight without modifying it. Operational fallback requires that consistent pre-upgrade backup and its compatible build. Never drop tables or edit migration history to downgrade a live database. Application backup/restore and production upgrade remain separate gates.

## Candidate and executed evidence

Windows developer host: Windows 11 Pro x64 build 26200, network active, developer tools and WebView2 preinstalled. Runtime 0.1.0, standalone packaged client with matching independent sidecar, no installer modification. All profiles/fixtures are synthetic and isolated. This host result does not prove a disconnected installation, missing-WebView2 path, VM OS restart or customer-PC policy.

Final client SHA-256: `17facf1e0669865f11ed4d24923b6db0624499f30fe61050341dac1aab60cf68`. Final sidecar SHA-256 `b497855367015e4e40aab98ad1216051c59d6d81bb06e61af77e61510e47211e`; native verifier SHA-256 `f533a81b5700173a962407e9b342a3015aaa36d7a0fe33359ce605912681c65d` (working CRLF file, code equal to committed LF after normalization). Final native scenario PASS in **36.218 s**; client/sidecar exited normally. CI results are recorded in the PR before handoff; raw files stay local. An earlier successful native candidate used client `5a0b951f…` before checkbox-layout correction; its pass is retained separately and is not transferred to the final candidate.

| Check | Result | Coverage / conditions |
| --- | --- | --- |
| Locked backend sync, Ruff format/check, unittest | PASS, 80 | 68 prior tests plus 11 staffing regressions and one new authenticated sidecar test; strict IDs, explicit-only query, AM/PM, borrowing, empty/inactive, cancellation, context invalidation, snapshot retention, races, stale inputs, rollback/retry and migration |
| Actual separately packaged sidecar | PASS, 9 | Authenticated loopback, new workers/history/filter, parent-pipe shutdown and restart; also all previous packaged contracts |
| Frontend locked install / format / TypeScript / Vite | PASS | Existing lockfile/cache, no dependency change; the default sandbox cache missed Vite, then the authorized project cache restored successfully |
| Frontend tests | PASS, 30 | Existing weekly/multi-day/calendar/form compatibility suite; new interaction coverage is native/browser rather than implementation-mirroring assertions |
| Rust locked fetch / format / Windows Release build / tests | PASS, 6 | New staffing save/history bridge and employee range-filter forwarding; existing lifecycle tests |
| Historical .NET locked restore / format / Windows Release build / tests | PASS, 35 | Compatibility baseline only; zero new WPF product feature |
| PowerShell 5.1 acceptance harness | PASS | Existing bounded success/slow-success/real install failure/GUI timeout/sidecar failure and date/WAL/weekly regressions |
| Native `-IncludeStaffing` | PASS | Actual Tauri/Rust/packaged FastAPI/SQLite. Own synthetic two-worker fixture, existing nine-Crew/101-Project weekly scenario, both boards, saved IDs, borrowed label, independent PM, no-write Cancel, app reopen, normal exit and deliberate startup-error feedback. Default GUI 30 s / exit 12 s |
| Independent native database inspection | PASS | Only employee 1 selected for Draft 4; employee 2 not implicitly included. Home Crew ID 2 and Unverified status retained. History/context/revision and notes preserved; integrity ok / no FK errors |
| Browser interactions | PASS | Separate loopback test-only IPC proxy to packaged backend: focus/Escape, empty/inactive, retained filtered selection, lost-response reload gate across dialog close/reopen, history error/retry, committed-save/failed-refresh clearing and reload, both boards and no console errors |
| Visual comparison | PASS | Original UI 02/13 inspected against actual native client captures. Worker row layout corrected after screenshot review. 1440/768/480/390 CSS-pixel browser checks keep dialog/document within viewport; new editor scrolls vertically for long content. App inspector: 0 FAIL, 1 tiny-text WARN; retained 12px secondary Crew/day metadata follows original UI 13 and is not a new page redesign |
| Staged documentation / privacy / Windows CI | Recorded in PR | Run against final index/head, not inferred from prior green #74/#75 |

Failed initial runs remain local. The first native attempt included the pre-existing Foreman scenario and stopped at its aggregate-status assertion before staffing. The new minimal staffing fixture initially omitted a required skill selection and correctly timed out before any employee was inserted. The fixture was corrected; product skill validation was not relaxed. The final staffing switch uses its own minimal fixture, while an explicitly requested Foreman scenario retains its independent existing checks. A real uncertain-response retry-state issue was found during inspection and fixed; the browser regression verifies closing/reopening cannot bypass reload.

Native screenshots use the actual WebView client and Rust IPC, not the browser proxy; they exclude the OS frame. The browser proxy/fault controls are local-only test tooling, not product code or publication evidence. No human screen-reader certification is claimed. Complete DOCX, screenshots, raw logs, SQLite snapshots and backup/VM files are kept on the authorized workstation; GitHub receives synthetic code/fixtures and sanitized records only.

## Remaining design and approval gates

NOT RUN for this changed candidate: disconnected VM installation/upgrade, guest OS reboot, missing-WebView2 setup, uninstall/reinstall, enterprise policies/signing, application-level cross-machine restore and human assistive-technology review. Previous #35/#75 offline results apply only to their recorded binaries.

Full #22 Stage B leave/effective-date/transfer impact and staffing safety remain pending. #15 employee/Rig collision classification and #23 driver eligibility remain unresolved Draft checks; overlapping Draft worker selections are not dispatch approval. #71 Employee Week/PDF/XLSX, actual dated Rig, validated immutable Published snapshots and formal distribution remain separate. Customer terminology and final AM/PM/leave/qualification decisions still require confirmation.

Customer Demo B/D acceptance: NOT RUN. Production approval: NOT GRANTED. Deliver as one Draft PR for human review; no automatic merge, Issue closure or Release.
