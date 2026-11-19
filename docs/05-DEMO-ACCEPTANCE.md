# M0 acceptance walkthrough

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

## Tauri Crew roster engineering check

In a disposable profile, open Crews and add a synthetic Civil or Tower crew. Search for it, edit its name or status, close the application and check that the edits appear after reopening. An inactive crew remains editable in the roster. The backend tests also cover invalid data, deactivation and reactivation on the same ID, and migration rollback with retry.

For native UI Automation, run the Tauri desktop smoke command above with -IncludeCrews. It uses a temporary synthetic database, creates a Civil crew, edits the name, verifies hit and empty search results, then reopens the crew after restarting. For an offline check, disconnect the test machine and add -RequireOffline.

## Tauri Employee roster engineering check

Use a disposable synthetic profile. Create a Civil or Tower crew, open Employees, and add a synthetic employee with that home crew and a skill level. Check that Driver shows Unverified. Search by name, edit the name and skill, toggle foreman eligibility, and deactivate the employee. Reopen the app and verify that the new values and home crew remained. Reactivate the same row and confirm it remains a single record.

The backend tests cover invalid skill levels, missing home crews, attempts to set driver approval, and an injected migration failure with safe retry from the Crew-only schema.

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

This is the existing-column sorting slice of [Issue #45](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/45). Work Item Code and Status fields, Bulk Add Projects and transactional import confirmation remain outside this slice. See the [November 19 engineering evidence](acceptance/2026-11-19-issue-45-project-sorting.md). Customer Demo A acceptance and production readiness remain separate gates.
