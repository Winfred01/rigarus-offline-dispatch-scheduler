# M0 acceptance walkthrough

## Employee collision engineering check (#15 first slice)

Use [the synthetic evidence](acceptance/2026-11-24-issue-15-personnel.md)
and [Design-First checklist](design/2026-11-24-issue-15-personnel-checklist.md).
Check same actual employee / local date / AM-PM across two or three Crews,
multiple employees, WorkItems/Projects, Civil/Tower and borrowed workers.
Explanations must include employee/date/half and every affected stable
Assignment/Crew/WorkItem/Project ID. Different dates/halves are independent.
Cancelled frees capacity; latest staffing replaces history. Missing/empty
staffing, incomplete scope or no active visits stays Pending.

Verify unselected and inactive Crews' Draft visits remain in the same consistent
snapshot, other-Crew changes make it Stale, WAL reads return a complete old/new
view, and logical records/history/assignments/employees/calendars remain unchanged.
Retain duplicate-Crew-slot rejection and deterministic/bounded pure computation.
The saved-Draft collision check may be Satisfied, but generated proposals still
lack actual proposed workers and retain PersonnelConflicts Pending. No Apply,
Publish, resource substitution or existing-Draft edit is introduced.
Drivers #23, staffing/skills/qualifications #25, actual Rig #24 and weekend consent
#27 remain required, followed by #18/#29 transaction/approval/audit.
CI is engineering verification; native GUI, disconnected installation/upgrade,
customer Demo B/D/E/UAT and production approval require separate evidence.

## Persisted recommendation adapter engineering check (#28 phase three)

Read the [Design-First record](design/2026-11-24-issue-28-adapter-checklist.md)
and [scope-specific evidence](acceptance/2026-11-24-issue-28-adapter.md).
Run the complete locked backend suite and focused `test_recommendation_adapter.py`.
Use only temporary synthetic databases populated through current application
Stores. Generate C1/C2 from stored parent calendars and visits; compare both sorts.

Verify real FK context, missing/inactive/mismatched Crew, confirmed Remaining,
multi-Crew, gaps/unknown/closed, Crew/date/slot occupancy and cancellation. Observe
borrowed actual employees separately from Home Crew/availability/Foreman and keep
missing drivers/skills/qualifications/Rig/consent Pending. During a paused read,
commit a multi-source WAL write from another connection: the result must equal
the complete old view, then re-read must see the changed sources/fingerprint.

Check native revisions and unversioned field changes, stable replay, unrelated
scope, checkpoint/VACUUM, full logical no-write equality, read-only write rejection,
invalid/corrupt/locked/old/new sources and closed handles on success/failure.
This internal service has no GUI/API/Apply workflow. Native GUI, physical offline
installation/upgrade/reboot and customer Demo E/UAT remain NOT RUN, separately
from developer-host regressions and Windows CI. Production is not approved.

## Automatic date generator engineering check (#28 phase two)

Read the [Design-First record](design/2026-11-24-issue-28-generator-checklist.md)
and [actual results](acceptance/2026-11-24-issue-28-generator.md). From the backend
folder run the locked suite and `python -m rigarus_backend.recommendation_example`.
Verify C1 Mon AM/Wed PM/Thu AM/Fri PM reaches 4/4 on Friday PM;
C2 starts later but finishes Wednesday PM. Both sorts must be deterministic.

Check missing/unconfirmed Remaining, multi-Crew, all closed/Unknown, gaps,
weekend consent, Crew occupancy, independent resource blocks, wrong IDs/ranges,
duplicates, year/leap/DST and annual bounds. Insufficient capacity retains
partial/unfilled counts with no finish or complete ranked option. Guard
file/network/SQL/clock calls and compare full synthetic SQLite logical records,
IDs, assignments, staffing, employees and calendars before/after calculation.

No HTTP/Tauri/UI or Apply/publication path exists here. Packaged-sidecar,
frontend/Rust and legacy .NET checks establish compatibility only. New native
GUI, disconnected installation/upgrade and customer Demo E remain NOT RUN.

## Historical M0 walkthrough

Use the synthetic dataset. For a physical offline check, disconnect Wi-Fi and Ethernet after building or extracting the package.

1. Start `Rigarus.Desktop.exe` on Windows. Verify the title, Dashboard, sidebar placeholders and Demo Mode.
2. Verify `DEMO-001`, `Example Site` and the initial demo note appear. In a fresh environment, verify `data\rigarus.db` was created.
3. Replace the note with a fictional value and select **Save note**. Verify the local save confirmation.
4. Close the window and start the same executable again. Verify the new note remains and the original project still appears.
5. Record the commit, package hash, Windows version, connectivity condition, and the result for each step.

The Windows UI Automation script uses a unique temporary data directory and checks the initial fixture, save, clean close and reopen. Use Windows PowerShell from an interactive desktop. Add `-RequireOffline` after disconnecting to require Windows to report no active network adapter.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File scripts/Test-M0Desktop.ps1 -Executable releases/m0-win-x64/Rigarus.Desktop.exe
```

## Project Master engineering check

1. Open **Projects** and create a fictional job with no work items. Verify the backlog count and project details.
2. Attempt to create the same Job # in a different ASCII case. The editor shows the duplicate error and the original project remains.
3. Edit the site name and add a Civil and a Tower work item. A fractional half-day count shows a validation error. Use a positive whole number and save.
4. Search by Job #, Site ID, and the edited site name. Verify that a term with no matches shows an empty result.
5. Restart the application. Verify the site, work items and demo note still appear.

The combined smoke test runs these checks on a temporary database. The automated SQLite suite also verifies search across 121 synthetic projects and upgrades an M0 database without losing its demo note.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File scripts/Test-M0Desktop.ps1 -Executable src/Rigarus.Desktop/bin/Release/net10.0-windows/Rigarus.Desktop.exe -IncludeProjects
```

## Demo A draft, pending customer confirmation

Create a fictional project with a work item and add it to the backlog. Try the same job number a second time and verify the original stays intact. Create one Civil and one Tower crew with a foreman, employees and rigs. Preview a duplicate or invalid import row and verify that preview leaves persisted data intact. Reopen to verify saved master data. Ask the operator to confirm field names, split rules and everyday search needs.

## Tauri demo note engineering check

From an interactive Windows desktop, run the smoke script against the built or installed executable. It uses a temporary synthetic database.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable src/Rigarus.Tauri/src-tauri/target/release/rigarus-dispatch.exe
```

The script opens the synthetic job, edits and saves the note, closes the window and confirms the sidecar exited, then restarts and checks the saved value. It also induces a database startup failure and checks the recovery message and Retry button. Record the Windows build, executable or installer hash, Git commit, and connection state. On the clean Windows 11 x64 test device, disconnect all network adapters before installing, then run the script against the installed executable with `-RequireOffline`. Record whether Node, Python and Rust are absent and whether WebView2 was already present.

The desktop waits up to 60 seconds for the sidecar to confirm SQLite and its loopback listener are ready. On a slow VM, add `-Profile SlowVm` so the GUI probe allows 150 seconds, including WebView2 startup. From a cold start, verify the dashboard loads without needing a second launch. If the readiness deadline expires, the dashboard explains that the local service took too long and offers **Retry**. For a database startup failure, verify the database-specific instructions still appear.

Add `-IncludeProjects` to verify Project Master in the same run. The script creates a synthetic project without work items, checks duplicate handling and whole half-day validation, edits and searches the project, and reopens it after restart.

For Issue #42, use the [offline acceptance kit](08-RELEASE-HANDBOOK.md#offline-acceptance-kit) to run the installer and both desktop checks on the same clean, disconnected Windows image. Record this result separately from CI and Demo A customer acceptance.

On November 13, 2026, the installer from commit `6d2fbeb28613f35211ce80db966aaa2296677e2d` passed installation and the full synthetic desktop smoke in a fresh, disconnected Windows 11 Enterprise x64 Sandbox (build 26100). The preflight found no common developer tools or .NET SDKs and recorded WebView2 157.0.4341.46 before and after setup. This verifies the preinstalled-runtime path. A separate test image without WebView2 is needed to exercise setup of the bundled runtime.

## Manual Draft Assignment engineering check (#14)

Create a synthetic Project with independent Civil/Tower WorkItems and a Crew. Use a WorkItem's **Assign** action: confirm its stable ID/type is selected, choose Crew/local date/AM-PM and **Save to Draft**. The current weekly board locates that saved week/card and opens its details. Schedule also has **Assign Work Item**. AM/PM stays provisional; all records must show Draft / Validation pending and Publish unavailable.

1. Save Civil visits for the same Crew on December 31 AM and PM; attempt Tower in the occupied AM slot. Check the actionable conflict and retained form, then move it to January 1 and save. Repeated Civil visits must retain the same WorkItem ID; Tower must remain independent.
2. Enter another unsaved visit and Cancel; compare records and confirm no write. Edit a saved draft's notes, cancel another only after confirmation, retain its ID/notes and reuse its released slot.
3. Reopen the app and verify cross-year local dates, Crew/WorkItem IDs, edited notes, three Draft visits and one Cancelled record. Confirm publication remains unavailable. Do not treat a roster or Unverified driver flag as compliance.
4. Separately test stale updates, uncertain committed creates, list-read failures after save/cancel, missing/empty WorkItems, retries, loading, keyboard focus and narrow layout. A committed write followed by read failure must not display the previous date's rows under the new date.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeAssignments
```

Add `-Profile SlowVm -RequireOffline -DiagnosticLog <local-log>` only in an actually disconnected authorized VM. The flag is opt-in; existing wait limits remain bounded. Record the candidate hash, OS, connectivity, native outcomes and conditions. Browser testing through a test-only IPC proxy does not replace the native Rust or offline run. #16's weekly board is now merged; the updated verifier follows its actual cards/modals, shared Job Schedule/Crew Board, empty week and native scroll area. #22's actual dated staffing/time off remain separate. See the historical [#14 Design-First record](design/2026-11-21-issue-14-manual-draft-checklist.md) and current [#35 native/offline verification](acceptance/2026-11-22-issue-35-weekly-offline.md).

## Explicit Draft workers engineering check (#22)

Read [the current design checklist](design/2026-11-22-issue-22-draft-workers-checklist.md) and [candidate-specific evidence](acceptance/2026-11-22-issue-22-draft-workers.md). Open a saved Draft card and **Choose workers**. Search by employee/name/Home Crew, explicitly select one employee and Save workers to Draft. Both boards and the individual AM/PM buttons in a multi-day strip must show that same choice. Home roster does not imply attendance. Borrowing labels the other Home Crew and never changes master data.

1. Create two synthetic workers in one Home Crew, the second inactive. Select only the first on an AM visit in another Crew. Open PM: no employee is automatically selected. Cancel checkbox changes and compare SQLite/WAL to confirm no write. Reopen the app and compare employee IDs, Home Crew, Unverified driver status and saved history.
2. Save an empty selection and check the explicit no-workers / Validation pending state. Select the inactive worker and check its warning; this is not dispatch eligibility. Correct selection, search with no match and confirm hidden selections are retained. Check keyboard focus, Escape, failure/reload, long names and narrow layout.
3. Read Staffing change history. Note-only edits keep selection. Change date/slot/Crew/WorkItem and verify current staffing requires reconfirmation while old snapshots remain. Concurrent/stale or uncertain writes require reload, including after closing/reopening the worker editor. A successful save followed by failed refresh reports the committed outcome and clears stale rows.
4. Query selected employee and local date range through the existing assignment read: only explicit latest configured associations appear. Cancelled visits are excluded by default. Empty query returns no records; Home Crew tasks must not be fabricated. All rows remain Draft / Validation pending, Publish unavailable. Full #15/#23 and leave workflow are separate.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeStaffing -PreserveSyntheticProfile -DiagnosticLog <local-log>
```

The switch implies the existing assignment and Crew scenarios and creates its own minimal synthetic employees; it may also reuse `-IncludeForemen` fixtures when that scenario is explicitly requested. Existing bounded Default/SlowVm waits remain. Use `-RequireOffline` only on an actually disconnected authorized VM; host/native screenshots do not prove offline installation. Preserve a consistent pre-upgrade backup: migration eight requires a compatible build, not an in-place downgrade. Customer acceptance and production approval remain separate.

## Recorded employee availability engineering check (#77)

Read [the availability Design-First checklist](design/2026-11-22-issue-77-availability-checklist.md) and [candidate evidence](acceptance/2026-11-22-issue-77-availability.md). In **People → Availability**, select a synthetic employee. Empty dates, including weekends, must show **Not recorded**, never assumed Available. Record an inclusive December 31–January 1 range as Full day / Available. Set December 31 AM to Unavailable; PM must remain Available. Open PM, choose Not recorded, then Cancel and confirm no write. Repeat and Save: PM becomes Not recorded; January 1 stays Available. Switching employee must not show the previous employee's cells.

1. Open change history, check the three revisions and reopen the application. Confirm stable employee IDs, Home Crew, driver state, previous projects/notes and all Draft worker choices. An unchanged save makes no new history event. Clearing records is explicit and retains history.
2. From a saved December 31 AM Draft, **Choose workers**: the same employee displays **Availability: Unavailable**. This is advisory; explicit existing selection stays checked. Not recorded and Available never approve attendance, leave, weekend work, driver eligibility or dispatch. Publish remains unavailable.
3. Test reversed/invalid dates, the 366-date per-operation bound, AM-only/PM-only, year boundaries, keyboard focus/Escape, empty roster, inactive labels, search and narrow horizontal calendar scrolling. A failed read must show an error, not a fabricated unknown state. Stale/uncertain writes require reload even after closing the editor. A committed save followed by failed calendar refresh clears stale cells and identifies the saved outcome.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeAvailability -PreserveSyntheticProfile -DiagnosticLog <local-log>
```

The opt-in switch includes the existing staffing, assignment and Crew scenarios and creates only synthetic records. Default GUI/exit limits remain 30/12 seconds; `-Profile SlowVm` uses 150/60 seconds. Add `-RequireOffline` only in an actually disconnected authorized environment. All waits are bounded. This checks the packaged desktop lifecycle, not installation, missing-WebView2 setup or human acceptance. For schema nine, retain a consistent schema-eight backup and its compatible build before upgrade; never drop tables or migration records to downgrade a live database. Full leave/working-calendar, eligibility and #71 actual-job calendar/export remain separate.

## Tauri Crew roster engineering check

In a disposable profile, open Crews and add a synthetic Civil or Tower crew. Search for it, edit its name or status, close the application and check that the edits appear after reopening. An inactive crew remains editable in the roster. The backend tests also cover invalid data, deactivation and reactivation on the same ID, and migration rollback with retry.

For native UI Automation, run the Tauri desktop smoke command above with -IncludeCrews. It uses a temporary synthetic database, creates a Civil crew, edits the name, verifies hit and empty search results, then reopens the crew after restarting. For an offline check, disconnect the test machine and add -RequireOffline.

## Tauri Employee roster engineering check

Use a disposable synthetic profile. Create a Civil or Tower crew, open Employees, and add a synthetic employee with that home crew and a skill level. Check that Driver shows Unverified. Search by name, edit the name and skill, toggle foreman eligibility, and deactivate the employee. Reopen the app and verify that the new values and home crew remained. Reactivate the same row and confirm it remains a single record.

The backend tests cover invalid skill levels, missing home crews, attempts to set driver approval, and an injected migration failure with safe retry from the Crew-only schema.

## Foreman appointment and history (#8)

In a disposable profile, create two Crews and two active employees marked Foreman eligible with the second Crew as Home Crew. From the first Crew's **Foreman** action, appoint one employee, choose the other then **Back to Crews** without saving, reopen and confirm no change. Replace the Foreman and check newest-first history. Rename/deactivate the current employee and remove eligibility: current status must warn, prior history names and references must remain. Clear the appointment, appoint an eligible employee again and reopen the application. Verify four history entries and unchanged Home Crew/Unverified driver status.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeForemen
```

This switch also executes the Crew smoke. Add `-Profile SlowVm -RequireOffline -DiagnosticLog <local-log>` inside an actually disconnected authorized VM. All waits use the existing bounded profiles. Browser-only checks separately exercise empty/loading/no-candidate/error/stale-write states, candidate filtering, keyboard navigation and narrow layouts. Backend tests verify a stale revision returns 409, concurrent saves have one winner, immutable snapshots, foreign keys, insert failure rollback and legacy migration retry. This master-data evidence does not establish staffing eligibility, retrospective scheduling, customer acceptance or production readiness.

## Tauri Rig inventory engineering check

In a disposable synthetic profile, open Rigs and create SYN-RIG-009 with a type and note. Verify that a rig may be saved with Unassigned as its default Crew. Try the same number in a different ASCII case and confirm the original remains intact. Search by number, type and note, then try a term with no matches.

Create a synthetic Crew and associate it with the rig. Edit the rig number, type and note, deactivate it, close the app and reopen. Verify all fields and the default Crew remain. Reactivate the same row and clear its default Crew. Inactive rig numbers stay reserved. Customer review still needs to confirm Rig fields and default vehicle expectations.

The automated suite covers this lifecycle, validation failures, concurrent duplicate creation, packaged sidecar access control, and migration failure/rollback/retry. Record native Windows GUI conditions separately from CI.

## Tauri Excel import preview engineering check

Prepare a synthetic .xlsx workbook following the [mapping dictionary](11-IMPORT-MAPPING.md). Include a valid row, a case-variant duplicate, a missing Site ID, #REF! and an unknown date column. Open Import preview, choose the file and select Preview workbook. Check row counts, proposed Create/Update/Skip outcomes and the source worksheet/cell references. Expand Fields and diagnostics to inspect the source values and warnings.

Select Cancel preview and verify the selected file and results clear. Navigate to Projects and reopen the app. Confirm no workbook row was inserted. Record SQLite SHA-256 and logical-content comparisons from the automated suite, the desktop executable hash, Windows build, connection state and package conditions. Demo A/F still needs approval of the real field layout.

## Tauri Project and Work Item sorting engineering check

Click any existing column header in Projects or Project work items. A new column starts ascending; click again for descending. The active column has a blue directional arrow and `aria-sort`; other columns show neutral double arrows. Headers are keyboard buttons. The tables sort independently. Crew counts, estimated half-days and work-item counts compare numerically. Job # and Site ID remain text, including leading zeroes. Sorting is a display preference for the current Projects screen and resets when leaving that screen or restarting; it does not change database order or scheduling priority.

Use synthetic projects SYN-SORT-2 and SYN-SORT-10, with Site IDs 02 and 10. Give one project two work items with 2 and 10 crews and 4 and 20 half-days (2 and 10 days). Search for `sort`, select that project and sort both ways. Confirm both matching projects remain, the search text and selected project stay unchanged, and changing the project table does not reset the work-item order. Review the text identifier convention in the decision register.

The native smoke script creates this fixture in a temporary database, asserts actual table rows using Windows UI Automation, and also reruns project creation/edit/reopen and note/startup-error checks:

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable src/Rigarus.Tauri/src-tauri/target/release/rigarus-dispatch.exe -IncludeProjectSorting
```

Use `-Profile SlowVm` for a slow Windows VM and `-RequireOffline` only after disconnecting the test environment. Each GUI probe and exit wait retains its existing upper bound. Run `npm ci`, `npm run format`, `npm test` and `npm run build` in `src/Rigarus.Tauri` for the pure sorting regressions and frontend checks (Node 22.13 or newer). Windows CI includes these tests.

This is the existing-column sorting slice of [Issue #45](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/45). Work Item Code and Status fields remain outside it. Bulk Add Projects is the subsequent slice below. See the [November 19 engineering evidence](acceptance/2026-11-19-issue-45-project-sorting.md). Customer Demo A acceptance and production readiness remain separate gates.

## Tauri Bulk Add Projects engineering check

Use the [three-column template and CSV mapping](11-IMPORT-MAPPING.md#bulk-add-projects) with synthetic data. Preview equivalent CSV and Excel inputs: a ready row, a changed existing project, case-variant repeats, a missing Site ID, a formula/error and a numeric Excel identifier. Check counts, source references and diagnostics. Confirm that changing the input removes the old confirmation. Cancel, search Projects and verify that no new row exists. Preview again and explicitly confirm the ready rows. Verify created/skipped counts, the new project and retained leading zeroes; existing project IDs, work items and notes must remain. Reopening or resubmitting must not create extra copies.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable src/Rigarus.Tauri/src-tauri/target/release/rigarus-dispatch.exe -IncludeBulkProjects -IncludeProjectSorting
```

This bounded native UI Automation run covers the pasted-text preview/edit/cancel/confirm/repeat/reopen flow plus the Project Master and sorting regressions. Excel template/file selection is a separate native GUI check; record whether it was actually executed, the WebView2 version, network state and executable hash. Use `-Profile SlowVm -RequireOffline` in an already disconnected VM. The backend and packaged-sidecar suites cover the Excel roundtrip, actual rollback on an injected second insert failure, concurrent confirmation and snapshot preservation. See [November 20 evidence](acceptance/2026-11-20-issue-45-bulk-projects.md); customer acceptance and production approval remain pending.

For the Excel clipboard follow-up, run the same command against the current candidate. It now also checks both Copy buttons using a real keyboard gesture and verifies the clipboard separators, pastes the examples into Preview, opens format help and dismisses it with Escape, then confirms synthetic TSV projects and verifies leading zeroes after reopening. The script privately restores the prior clipboard; it never records it. WebView2 exposes native popover buttons through ExpandCollapse rather than Invoke in UI Automation. The test handles that pattern and keeps its waits bounded.

Separately deny clipboard access in a browser-only test and verify that the selected example and Ctrl+C instructions appear without a false success. Compare the actual screen with the local UI design's November 21 section 批量添加：Excel 表格粘贴与纯文本样例, Figure 3A. Record keyboard focus, one open help popover, narrow-window layout and the unchanged preview/Cancel/transaction behavior. A real Microsoft Excel application copy is separate from synthetic TAB clipboard verification; do not claim Office was used when it was absent.

## New/Edit Project field validation (#65)

Compare the current editor with the authorized local November 21 UI design, section 单项目录入：醒目校验与字段提示 / Figure 2A, including its written corrections. See the [Design-First checklist](design/2026-11-21-issue-65-project-validation-checklist.md) and [engineering evidence](acceptance/2026-11-21-issue-65-project-validation.md).

1. Open New project and Save empty fields. Confirm three specific messages, first-field focus, no write and a summary that focuses the selected input. Correct one field; other errors and all draft values must remain.
2. Enter a unique synthetic Job #, Site ID `A-7` and a descriptive synthetic name. Add work items. Blank/zero/negative/fractional/overflow counts must identify only the invalid control and row. Valid `2` crews / `4` half-days must save. Do not enforce four-digit Site IDs or an unconfirmed Job # character policy.
3. Add/remove draft rows after errors; confirm summary labels follow visible rows and removed errors disappear. Save from the bottom of a long form; first invalid input must scroll into view. Cancel must leave saved data unchanged.
4. Use Tab and Shift+Tab to reach all six help types. Open by keyboard; Escape and Close help dismiss. Opening another help closes the previous one. Check positive whole counts, actual type values, leading zeroes and half-day examples. Check focus outlines, field/summary descriptions and narrow-window wrapping.
5. Attempt a duplicate Job #. Only Job # is marked; draft rows remain. Distinguish a storage/service failure from a field error. Save valid multiple work items, edit an invalid count then correct it, reopen the application and compare project/work-item records and IDs.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeProjectValidation -IncludeBulkProjects -IncludeProjectSorting -IncludeCrews
```

The new switch is opt-in; existing bounded Default waits (GUI 30 s, exit 12 s) and SlowVm waits (GUI 150 s, exit 60 s) remain. Add `-Profile SlowVm -RequireOffline -DiagnosticLog <local-log>` only inside an actually disconnected authorized VM. Use synthetic data; keep raw evidence local. Automated ARIA/UIA checks do not establish a manual screen-reader pass. Record human assistive-technology review, matching installer tests, customer acceptance and production approval separately.


## Desktop weekly planning and tools (#16)

Read [the design checklist](design/2026-11-22-issue-16-desktop-checklist.md) and [current engineering evidence](acceptance/2026-11-22-issue-16-desktop-week.md). Original UI 01–15 / 40–47 remain local. Customer Demo B is a separate pending gate.

1. Launch into Schedule / Job Schedule. Verify module order, light local-search bar, bottom Settings/Help and absence of Leads/Timesheets/account routes. Existing Projects/bulk import, People/Foreman and Equipment actions remain accessible.
2. With nine synthetic Crews and 100+ Projects, compare saved visit IDs in Job Schedule and Crew Board. Scroll via wheel and scrollbar to the last row; dates and roster stay aligned. Exercise horizontal overflow, long Foreman names and inactive references. Home roster/default Rig must not imply actual staffing or approval.
3. Use Previous / Today / Next and date jump for an empty week, weekend, December 31 / January 1, AM/PM on one day and repeated visits. Open details, create/edit via #14, correct a Crew-slot collision without losing notes, and cancel only after confirmation. Work Items with other active visits stay scheduled; otherwise they return to the queue. Reopen the application and compare IDs/revisions/dates/notes.
4. Use Ctrl+K, type filters, arrows/Enter and Escape for local stable-ID record routing and empty results. Test appearance preview/Cancel/Save and application-restart retention. Help must name the current view. Publish review and Reports explain missing staffing/safety/immutable-snapshot prerequisites.
5. Record native runtime/network/tooling conditions. Native WebView developer-protocol screenshots prove the actual Tauri/Rust/sidecar path but exclude the OS frame; they do not prove physical pointer operation or an offline installer pass. The updated `-IncludeAssignments` UIA verifier now follows this weekly board and generates nine Crews / 100+ Projects. It verifies stable card IDs, Civil/Tower selections, modal lifecycle, date segments, DB/WAL no-write cancellation, shared views, restart and normal exit. Native ScrollPattern checks last-row top/bottom reachability and matching roster/day geometry; a wrapped row may exceed the body viewport and is not required to fit simultaneously. Record physical wheel/drag and human accessibility separately. See [#35 evidence and package identity](acceptance/2026-11-22-issue-35-weekly-offline.md) for the matching installed-package execution, limits and remaining gates.

For consecutive saved dates, also read [the multi-day checklist](design/2026-11-22-issue-16-multiday-checklist.md) and [candidate-specific evidence](acceptance/2026-11-22-issue-16-multiday.md). Save all four AM/PM visits for the same WorkItem/Crew and exact notes on December 31, 2027 and January 1, 2028. Both boards should show one strip spanning Friday/Saturday, with four individually reachable source buttons. Edit one source's notes to split the strip, restore to reform it, then cancel one PM and replace it. Check that the replacement has a new ID and that restart retains the original IDs/revisions/cancellation. Missing shifts, different notes, empty dates and parallel project rows must retain independent cards. No extra visit, staffing, duration or publishing approval may be inferred.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeMultiDay
```

`-IncludeMultiDay` implies the existing `-IncludeAssignments` scenario and preserves its original checks. Add `-Profile SlowVm -RequireOffline -PreserveSyntheticProfile -DiagnosticLog <local-log>` only in a verified disconnected synthetic VM. Keep raw logs/profiles local and distinguish developer-host execution from matching installed-package evidence.

## Employee Week first engineering slice (#71)

Read [the Design-First checklist](design/2026-11-22-issue-71-employee-week-checklist.md) and [candidate evidence](acceptance/2026-11-22-issue-71-employee-week.md). Open Schedule → Employee Week. Choose one of two employees with the same Home Crew; only the explicitly saved worker has cards. Borrow into a different Crew: the dated card shows that Crew and Borrowed, while Home Crew stays unchanged. Check local cross-year Sun–Sat, AM/PM, independent repeated visits and recorded availability. An empty employee/week retains all seven dates and Unscheduled cells. Inactive status and Unverified driver remain visible; no approval is inferred.

1. Open a card and compare IDs, date/slot, Job #, Site text identifiers, actual Crew, revision/notes and Actual Rig: Not assigned. Default Rig never supplies dated equipment.
2. Export preview must retain the same selected employee/week/visits and show DRAFT – NOT CONFIRMED. Export PDF and Export Excel remain disabled. Close/Escape, card view, week navigation and previews must not change SQLite/WAL.
3. From People / Employees choose a worker's name. From global search open a Person and use Open employee week. Both preserve the selected Schedule week and route the stable employee ID. Switch to an empty/inactive employee; previous cards must disappear. Test delayed responses, assignment/availability/roster errors and retry, narrow internal scroll and keyboard focus.
4. Reopen and verify saved explicit worker IDs, Home Crew, notes, AM/PM dates and recorded availability. UI date/employee selection itself is in-memory navigation, not a persisted preference.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeEmployeeWeek -PreserveSyntheticProfile -DiagnosticLog <local-log>
```

The switch implies availability/staffing/assignment/Crew fixtures. Default GUI/exit bounds remain 30/12 seconds; SlowVm uses 150/60 seconds. Use -RequireOffline only on an actually disconnected authorized environment. No new migration; schema nine and all prior compatibility gates remain. This is an internal read-only planning/preview slice; actual PDF/XLSX, validated Published snapshots, leave/driver/resource safety, installation, customer acceptance and production remain separate.

## Working-calendar calculation foundation (#26)

The initial `7435f35` slice was an internal Python model. The follow-up below connects Project-shared calendars to the app. Read [the Design-First checklist](design/2026-11-23-issue-26-calendar-checklist.md) and [engineering record](acceptance/2026-11-23-issue-26-calendar-model.md). Run the synthetic model/compatibility tests from `src/Rigarus.Backend`:

```powershell
uv sync --locked --group bundle
uv run --locked python -m unittest discover -s tests -p test_work_calendars.py -v
```

Check all Crew/WorkItem state pairs, independent AM/PM, different Crew calendars, explicit closure/conflict reasons, unknown weekdays/weekends/holidays, inclusive cross-year/leap/DST dates and bounded invalid ranges. Even a weekend Working/Working match retains WEEKEND_APPROVAL_PENDING. Calculation makes no file/socket/SQL call; existing saved Draft, employee availability, Unverified driver and the complete logical SQLite snapshot stay unchanged.

All results remain Validation pending / unpublishable. A matched calendar does not validate personnel collisions, driver qualifications, actual Rig occupancy or other safety rules. That initial model-only result did not establish calendar entry/persistence/API/Tauri UI or full #26. The following engineering check covers the later integration; #27 consent, #28 recommendations and #29 Apply remain separate. Native GUI/install/upgrade acceptance does not apply to this unconnected calculation-only slice; previous package results do not certify it. Customer Demo E and production approval remain pending.

## Project-shared working calendars engineering check (#26)

Read [the resumed Design-First record](design/2026-11-23-issue-26-project-calendar-checklist.md) and [follow-up evidence](acceptance/2026-11-23-issue-26-project-calendars.md). Open Schedule → Working calendars, choose Project, select a synthetic two-WorkItem project and jump to December 31. Empty weekday/weekend/holiday dates must remain Not recorded. Record December 31–January 1 as Full day / Can work, change December 31 AM to Cannot work, then try clearing PM and Cancel. Compare SQLite/WAL: Cancel does not write. Repeat and explicitly Save clear; PM becomes Not recorded while January 1 stays Can work. History retains all three range changes.

Select a Crew and record its dates independently. Return to Job Schedule. Saved Civil/Tower WorkItems inherit the same parent Project calendar; no WorkItem override exists. Draft details/form/cards show matched/conflict/pending feedback for the selected local date/AM-PM. Explicit calendar closure or unknown remains saveable as Draft; the existing Crew-slot occupancy rejection still holds. Editing a calendar never moves existing dates or changes visit IDs/notes/workers. Reopen and confirm cells, revisions, history and original Draft data remain.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <candidate-exe> -IncludeWorkingCalendars -Profile SlowVm -PreserveSyntheticProfile -DiagnosticLog <local-log>
```

This opt-in switch implies existing assignment scenarios, adds working-calendar normal/Cancel/history/form-feedback cases and verifies calendar/Draft reopen. Existing Default/SlowVm wait bounds remain. Add `-RequireOffline` only on an actually disconnected authorized test environment; a connected developer-host native pass does not establish offline installation/upgrade. Also exercise stale/concurrent writes, delayed owner/date responses, storage read failure, uncertain save/reload, committed-save/failed-refresh, keyboard/Escape, focus restoration and internal horizontal scrolling. All fixtures must be synthetic; retain raw logs/databases/screenshots locally.

Calendar Matched remains Draft / Validation pending and unpublishable. Employee Available is separate from actual staffing/personnel conflict, approved driver, skills, actual Rig availability and weekend consent. No automatic recommendation/Apply, publication or formal export is delivered. Schema ten operational fallback requires a consistent schema-nine backup and compatible build, not table/history edits. Customer Demo E and production approval stay separate.

## Native UIA Crew-choice diagnosis (#35)

Use an interactive authorized Windows desktop and the same verified installed executable. The verifier always creates an independent synthetic profile. Detailed sanitized exception chains, invocation/stack locations, target properties/runtime identity and before/after states go only to a local JSONL file. `-UiaDiagnosticLog <local-jsonl>` selects it; by default it is `<DiagnosticLog>.uia.jsonl` (the event log itself defaults to a unique temporary file). Keep these raw diagnostics, screenshots and databases on the authorized machine; publish only reviewed sanitized findings.

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <installed-exe> -ReproduceCrewChoice -Profile SlowVm -RequireOffline -PreserveSyntheticProfile -DiagnosticLog <local-events> -UiaDiagnosticLog <local-jsonl>
```

This opt-in reduced case creates exactly two Crews and one Project/WorkItem, saves an AM Draft, reopens Assign, reselects the original Crew and chooses the other Crew, then cancels. It cannot be combined with any `-Include*` scope; use a separate fresh run for the complete `-IncludeEmployeeWeek` chain. Test normal and hidden supervision separately and record each result. A hidden supervisor still requires an interactive desktop: the tool restores only its owned application window and checks that process's HWND ownership before doing so. It does not change security, session, WebView2 or power policies.

Crew/other native choices use one existing GUI deadline for the complete interaction: Default 30 seconds or SlowVm 150, with finite overrides unchanged. Each probe resolves current controls/patterns again and verifies the committed label. Recognized UIA operation refusals are logged as retrying; a persistent refusal still times out, and unknown/denied/unsupported failures remain fatal. This retry does not cover Save buttons, API/storage writes or product assertions. A successful CI harness run does not establish native or offline acceptance. See [the current Design-First diagnosis](design/2026-11-23-issue-35-uia-checklist.md).

## Project-choice investigation (#86)

The working-calendar Project path acknowledges **focus → Expanded → target text
value → committed target value / Collapsed**. Large native-select proxies in the
tested WebView2 expose no usable SelectionItem pattern. The tool reacquires the
current control and may repeat only a nonpersisting readiness action while its
state is still unacknowledged, including a silent no-effect Expand. Recognized
UIA refusals are recorded; unsupported/ambiguous/unknown errors remain fatal.
Text is sent once. Enter is sent at most once, only after the target value is
observed and if the popup still needs committing. No direct provider Collapse,
text resend, Save retry, API/database retry or fixed delay is used. The original
selected-label assertion remains; completion additionally requires Collapsed.

All Project stages share one existing GUI budget: Default30 / SlowVm150 seconds,
with the same finite override. A late response fails; stages do not each restart
that budget. Synchronous provider calls may overrun a probe deadline, so keep the
independent whole-worker watchdog. Pre-input target/focus snapshots explicitly
mark `childrenOmittedForTiming` rather than enumerating a large list and changing
readiness timing. Full final snapshots retain the 120-child bound/truncation
flag. No children exposed by a closed popup is not proof of unloaded options.
The local UIA JSONL includes current/fresh identities, values, enabled/offscreen
state, owned focus and foreground state. Unowned focus never copies another
window's text. Logs record stages, elapsed time and actual failure; retain worker
and watchdog exits. The short numeric-key/native-focus prototype used for the
investigation remains local and is not part of the distributed tool.

Run `scripts/Test-TauriProjectChoiceHarness.ps1` in Windows PowerShell5.1, or the
complete `scripts/Test-TauriAcceptanceHarness.ps1` used by Windows CI. Regressions
cover silent/transient/partially effective Expand, missing/disabled/ambiguous or
unsupported controls, wrong value, absent text/commit response, unknown errors,
foreign/lost foreground, one-shot input counts and the shared deadline.

Run the existing `-IncludeWorkingCalendars -IncludeEmployeeWeek` command on a
fresh synthetic profile, separately under ordinary and Hidden supervision on an
interactive authorized desktop. A shortened read-only investigation may clone a
verified, closed synthetic fixture into another generated smoke profile, but its
result must be identified as reduced coverage rather than a complete installation
or lifecycle PASS. Keep the original package, final value assertion and finite
GUI/exit bounds unchanged. Do not retry Save or change product code based only on
a screenshot of `Select a Project`. See [the original checklist](design/2026-11-23-issue-86-project-choice-checklist.md),
[the resumed protocol checklist](design/2026-11-23-issue-86-input-sequence-checklist.md)
and [scope-specific evidence](acceptance/2026-11-23-issue-86-project-protocol.md).

## Supervisor progress JSON (#35)

Windows PowerShell 5.1 attaches filesystem Provider/Drive properties to strings returned by `Get-Content`. Do not place that extended object directly into a JSON progress record: deep serialization can traverse the attached object graph and stop the supervisor's polling, deadline and final exit report while its native worker continues independently. This is a test-tool failure, not proof that the product is stuck or that a worker's last PASS implies aggregate exit zero.

Use the support reader to materialize a plain string before building a primitive-only record:

```powershell
. scripts/TauriAcceptanceSupport.ps1
$lastEvent = Read-AcceptanceProgressText -Path $localEventLog
if ($null -ne $lastEvent) {
    @{ phase = 'native-progress'; lastEvent = $lastEvent } |
        ConvertTo-Json -Depth 4 -Compress
}
```

The reader returns no event for a missing/empty/non-file path. A real read failure propagates; it is not a fabricated PASS or unknown state. Keep the event text, paths and detailed diagnostics local; publish reviewed summaries only. Do not serialize a Process, UIA control, provider object or arbitrary diagnostic object graph. Retain the worker timeout and an independent outer watchdog so a synchronous diagnostic call cannot disable every deadline. Original installer/executable hashes and native assertions must remain unchanged.

`Write-AcceptanceEvent` uses an explicit append stream with read/write sharing so the single verifier can append while its supervisor reads. It preserves UTF-8 detection and earlier lines; real write failures still fail. Do not replace it with Windows PowerShell 5.1 `Add-Content`, whose sharing behavior reproduced a fatal `0x80070020` writer failure with a live reader. An advisory live poll may log a narrowly recognized sharing/lock violation as busy and defer to the next existing bounded poll; it must not retry native saves, fabricate a PASS or hide other errors. The native exit code and final evidence remain required.

Run `scripts/Test-TauriAcceptanceHarness.ps1` in Windows PowerShell 5.1. Its real-file regression verifies the extended-string fixture, the plain final event, a depth-12 JSON round trip without Provider/Drive metadata, absent/empty/non-file inputs and an actual locked-file read error. It also holds a reader open during append, checks retained Unicode/lines and a single UTF-8 preamble, and verifies exclusive-lock write failure. See [the resumed checklist](design/2026-11-23-issue-35-supervisor-checklist.md) and [separate engineering evidence](acceptance/2026-11-23-issue-35-supervisor-finalization.md). Only a completed native run and captured exit code can remove the aggregate BLOCKED status; CI alone cannot.

## Consistent active SQLite verification (#88)

Current Cancel and read-only checks compare **logical SQLite snapshots**, not
separately hashed live DB/WAL files. This supersedes earlier byte-digest wording
in the walkthroughs above. Normal checkpoints, WAL cleanup and SHM reader locks
are not changes to a Project, visit, worker, availability or calendar record.

`TauriSqliteSnapshot.ps1` opens the existing generated synthetic database through
the Windows system `winsqlite3.dll`, with READONLY, PRIVATECACHE, query-only and an
explicit read transaction. All schema, explicit column values, ID sequences and
integrity/FK checks share that snapshot. Typed length-prefixed encoding preserves
NULL, empty text/BLOB, integers, reals, Unicode and duplicate records; canonical
row ordering does not depend on physical page order. Schema definitions and
user/application versions are included; page headers, WAL/SHM bytes and internal
statistics are not. No app endpoint, product dependency or migration is added.
Never use `immutable`/`nolock` or copy only the live main database to avoid locks.

The reader uses the configured GUI timeout: Default 30 seconds, SlowVm 150, with
the existing finite override. SQLite busy waits are at most 5 seconds and a
progress callback enforces the overall SQL deadline. Technical limits are 256
tables, one million encoded schema/data rows and 128 MiB counted read/encoding
work. Missing/corrupt/inaccessible storage, integrity/FK errors, missing native
exports, limits and unknown read errors **fail without a fingerprint**; nothing
is silently skipped or truncated. Keep the independent process watchdog for
synchronous native/OS calls. Reading may participate in normal WAL/SHM file/lock
management; read-only means no committed business/schema mutation, not that every
filesystem byte is unchanged. A before/after fingerprint detects net committed
logical differences, not every transient write subsequently reverted.

`Get-SyntheticAssignmentDigest` retains every existing equality assertion. It
records local START/PASS/FAIL/TIMEOUT events with elapsed time, SQLite version and
table/row counts; it never logs record values. The matching reader is copied into
the offline acceptance kit. Run the real-file controls in Windows PowerShell 5.1:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Test-TauriSqliteHarness.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Test-TauriAcceptanceHarness.ps1
```

The controls cover active-WAL/checkpoint/last-connection cleanup, actual
insert/update/delete/type/schema/sequence changes, Unicode/NUL and duplicate
encoding, missing/corrupt/locked files, explicit timeout/error propagation, kit
identity and 100 concurrent multi-table snapshots. Unknown errors remain fatal.

Rerun the **original** combined native command on the frozen installed package,
separately under Normal and Hidden supervisors on an interactive no-NIC test VM:

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <frozen-installed-exe> -IncludeEmployeeWeek -IncludeWorkingCalendars -Profile SlowVm -RequireOffline -PreserveSyntheticProfile -DiagnosticLog <local-events> -UiaDiagnosticLog <local-uia-jsonl>
```

Retain all Save/Cancel, Employee Week, availability, actual staffing, calendar
feedback/history, app-reopen, startup-error and exit assertions. Capture worker
and independent supervisor exits, exact package/script hashes, window mode,
actual OS/SQLite/WebView2 versions and closed logical-data/integrity/file audits.
The previous #86 navigation-only success is not this full run. See [the #88
Design-First checklist](design/2026-11-23-issue-88-sqlite-snapshot-checklist.md)
and [scope-specific evidence](acceptance/2026-11-23-issue-88-sqlite-snapshot.md).
Do not mark #26/#35 complete or approve #28 integration from CI or a partial run;
customer acceptance and production remain separate gates.
