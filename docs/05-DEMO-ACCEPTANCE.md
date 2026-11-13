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
