# Issue 16 desktop framework and weekly planning evidence

## Scope and source

Refs #16. This is the first desktop framework/core week-flow slice, based on main `87230896feb6c5fe60984b49e8f2580b1948b1d9` (merged #14 / PR #72). Repository visibility was verified as public; original workspace README/design changes were preserved in an independent worktree. No open competing PR was found. See the [Design Compliance Checklist](../design/2026-11-22-issue-16-desktop-checklist.md) for required source revisions and requirement mapping.

Read the November 22 local UI DOCX, relevant explanatory text and original embedded images for UI 01–15 / 40–47. Original files and extraction stay local. Prototype v2 HTML and screenshots ZIP were not found in the supplied design directory/tracked inventory. DOCX figure locators were used; full-document rendered pagination is not claimed. The current #16/#22/#45/#71/#17/#32 and #14 bodies were read through GitHub. M2 / Demo B remains a separate customer acceptance gate.

## Delivered behavior

- Schedule / Job Schedule opens immediately. The module rail follows the owner's requested order with Settings/Help at the bottom; global local search occupies the light top bar. No Leads, Timesheets or account routes exist. Existing Project CRUD, validation, sorting, bulk CSV/TSV/XLSX, People/Crew/Foreman, Rig and read-only import workflows remain available. Historical master-data smoke navigation is adapted to the module rail.
- Job Schedule, Crew Board and Overview project the same saved Draft Assignment IDs. Sunday–Saturday navigation, Previous/Today/Next/date jump, Crew/Project filters, sticky dates/roster, one grid scroll area, details and a collapsible unscheduled queue are implemented. Projects with stored visits remain visible in an empty week; unscheduled Projects stay in the queue instead of adding hundreds of blank grid rows.
- Assign/edit/cancel reuse the unchanged #14 commands, authenticated loopback API and SQLite schema/revisions. Saved dates locate their week and successful Save collapses the pending queue to reveal the board. Active Project filters remain visible/clearable in Crew Board and Overview. Definite slot conflicts retain input and allow correction; stale or uncertain writes require reload. Confirmed cancellation retains the record/ID and releases occupancy. A committed write followed by failed refresh clears stale board data. Form Cancel makes no write.
- Home roster, current Foreman and default Rig are labelled as master data. Cross-Home-Crew Foreman appointments, inactive references and missing membership remain honest. Foreman appears once and first/bold. Actual staffing not assigned and Time off not configured are explicit; no fabricated OFF labels, actual employees, actual Rig or approved driver.
- Local search supports Project, Work Item, Person, Crew, Equipment and Schedule records; Ctrl+K, type selection, arrows/Enter, stable-ID routing, empty/error/retry and Escape. Appearance supports live preview, Cancel/X/Escape rollback, Reset, explicit device Save and restart retention. Help identifies the current view.
- Publish review and company/Crew formal exports explain the missing staffing, safety/driver/resource/locks/weekend checks and validated immutable Published snapshot. Publish/export remain unavailable; no publishing command/endpoint is introduced.

## Executed checks

All records below are synthetic. No business database was opened.

| Check | Result and limits |
| --- | --- |
| Frontend locked dependency install / format / TypeScript / Vite | PASS: `npm ci --offline` with existing cache, `npm run format`, `npm run build` |
| Frontend unit regressions | PASS: 22 tests, including local dates in Toronto/Tokyo, DST/cross-year/weekend boundaries, low years, appearance validation, prior project/assignment/sorting rules |
| Python locked install / lint / format / tests | PASS: `uv sync --locked --group bundle`, ruff checks, 68 tests. Initial sandboxed HTTP execution stalled; the complete unrestricted local-loopback rerun passed |
| Bundled backend | PASS: PyInstaller sidecar build and 8 tests against that actual executable, covering authenticated access, schema compatibility, restart and startup failure |
| Rust and Windows desktop | PASS: locked offline Cargo fetch, rustfmt, Release Tauri build and 6 Rust tests; no lock/dependency changes |
| Windows installer | PASS: matching NSIS x64 bundle, 300.38 MiB. First attempt encountered a test executable file lock; rebuilding after isolating the test candidate succeeded |
| Historical .NET compatibility | PASS: locked restore, whitespace verification, Windows Release build (0 warnings/errors), 35 tests. Initial sandbox named-pipe failure was resolved by the unrestricted required-check rerun |
| Acceptance-harness infrastructure | PASS: existing PowerShell bounded wait, process exit/failure and installer-integrity scenarios. Modified desktop-smoke navigation parses successfully; historical assignment UIA assertions are not a weekly-board verifier |
| Actual React + packaged sidecar/SQLite | PASS: 12 scenario groups against a test-only IPC proxy, with 9 Crews, 105 Projects and independent Civil/Tower Work Items. Includes cross-year dates, AM/PM/weekends, both boards, wheel/sticky scroll, long Foreman name/filter, collision/input retention, create/edit/cancel/queue, uncertain committed response/reload, stale revision, search keyboard/type/record route, settings Cancel/save/reload, failed reads/retry and narrow widths 768/480/390 |
| Actual native Tauri client | PASS: actual Tauri WebView → Rust → bundled FastAPI → SQLite, without IPC proxy. Native default week, same-day AM/PM/weekends, nine-Crew wheel scroll, fully visible last row, physical DevTools scrollbar drag, Previous/Today/Next/empty week, details/Overview, conflict/save/edit/cancel, synchronized views, Ctrl+K/Enter/type/empty/Escape, appearance and contextual Help |
| Native application restart | PASS: complete process restart retains the native-created Draft ID/date/PM/notes and saved appearance; cancellation remains retained. Restart used test process termination, not a normal window-close assertion |
| Visual inspection | PASS after fixing a reproduced outer-page-scroll/card-location defect and removing duplicate Foreman text. Actual native client screenshots checked; final inspector has no remaining findings with two declared reference exceptions: compact rail edge labels and uppercase wordmark. No document horizontal overflow at tested widths |
| Staged whitespace/privacy | Recorded in the Draft PR after staging; only intended source, tests and sanitized Markdown are included |
| Current PR Windows CI / artifact | Recorded separately in the Draft PR. Local passes are not substituted for pending CI/upload results |

Native environment: Windows 11 Pro x64 build 26200, preinstalled WebView2, active network and developer tools present. A temporary loopback WebView developer endpoint was enabled only in the isolated test launch environment, never in product configuration. Windows capture/AX helpers timed out; native screenshots were instead captured directly from the real Tauri WebView renderer. They show the client area, excluding the OS window frame. The final last-row test asserts the grid bottom fits within the native viewport. The scrollbar drag is native WebView input through its developer protocol, not a Windows UIA or human pointer certification.

Final native executable SHA-256: `018f27ef36e3485d75574015d5f052a1dbd094aa5ffc4bddede373dbe70d42d9`.
Matching installer SHA-256: `0c16ad02800fd013c12e88c85375daccf63ceaa6c0a5b6cf0bc51f5da38df9fa`.
Packaged sidecar SHA-256: `67a290d0f636550b3e026ec5e66dd5708e08b096ec1838333d889cb051150b9a`.

## Screenshot index

Actual native client-area PNGs are retained in the owner's local Issue 16 evidence gallery, not uploaded as source material. The gallery maps UI 01 (Job Schedule), 02 (card detail), 03 (queue), 04 (Assign), 05 (saved), 06 (draft detail/reopened), 07 (edit), 08 (cancelled), 09 (conflict), 10 (publish review), 11 (Overview), 12 (empty week), 13 (Crew Board), 14 (last row, wheel and scrollbar), 40–43 (search/type/record/empty) and 44–47 (appearance/preview/save/Help). Original DOCX figures are not represented as executed screenshots. UI 15 Equipment Board is a later supported-data panel, not delivered by this first slice.

## Remaining acceptance and deliberate limits

- NOT RUN: matching installer installation/upgrade on a disconnected clean Windows device; missing-WebView2 path, reboot, normal window-close/sidecar-exit smoke for this candidate, full Windows UIA board verifier, human screen reader/pointer review and customer Demo B signoff. No host network adapter was disabled. A built offline installer is not an offline installation pass.
- The old `-IncludeAssignments` UIA flow expects #14's selected-date table. Its full conversion to the new weekly board remains pending; current native verification used the actual WebView developer protocol instead. Base/master-data navigation was adapted but that UIA automation was not run in this turn.
- Continuous multi-day visits remain separate explicit AM/PM cards, not one spanning bar. Estimated half-days are shown in details/editor/queue; no automatic remaining-work deduction or inferred completion. Pending-queue semantics are a proposed UI convention for Demo B review.
- UI 15 Equipment Board and full UI 16–39 panel redesigns remain staged follow-ups. #22 owns actual dated staffing/leave/borrowing; #71 employee calendar/PDF/XLSX; #45 remaining Project visual updates; #17/#32 validated snapshot/report layouts. No unsupported business operation is simulated.
- Full #15/#23 safety checks, immutable Published versions, formal dispatch/export and final AM/PM/customer business decisions remain open. No human acceptance or production readiness is inferred from engineering results.

No SQLite migration/data conversion occurred. Existing IDs/constraints/revisions and prior compatibility tests are preserved. Code rollback is the prior UI on the same supported schema. Raw logs, test databases/backups, original designs, local paths and screenshots remain local. No automatic merge, release, Issue closure or real customer data upload.
