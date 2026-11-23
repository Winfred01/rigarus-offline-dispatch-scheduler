# Issue #35 — Crew selector native regression

Client date November 23, 2026 (America/Toronto). Follow-up to human-merged PR #81, baseline `a7650c7022dc1cd1495ce0e760c9909678836a81`. See the [Design-First source/checklist](../design/2026-11-23-issue-35-uia-checklist.md) and [reproduction commands](../05-DEMO-ACCEPTANCE.md#native-uia-crew-choice-diagnosis-35). Only acceptance tooling/documentation changes; product source, API, dependencies, SQLite schema and tested installation stay unchanged.

## Exact package and environment

The installed package remains the original feature-CI build `1fc06dbc96670ff3c167d5bf64999ea826b86057`, version 0.1.0 x64, installer SHA-256 `F684B592A07C0E4FAA31119D7468A51DA0F5064CAB56AEE5815F5E5DB680F4AF`. Installed client SHA-256 `24B5BB5C3C7934E7FBC79283698003CE6A421C1A3E5FF1D1FF42CB42043B78C2`; sidecar `0599AADC205F6D544C3AD90D76FD5415BE0B950B1B6A1F5ED4F9354DBE53994C`. The new verifier is paired with that unchanged installation, not represented as its original CI script. The original verifier/installer and earlier failed logs remain retained locally.

One independent QEMU child overlay over the previous normally shut-down synthetic test disk; original/backing disks preserved. Windows 11 IoT Enterprise LTSC Evaluation x64 build 26100, four TCG CPUs, 6 GiB RAM, non-admin/non-elevated, **no virtual NIC**. Existing per-user WebView2 158.0.4370.33; no browser-runtime directory override, repair or security-policy change. Only one guest runs at a time. An interactive Windows desktop is required even when the PowerShell supervisor is hidden.

Each run creates its own synthetic SQLite profile. The installed default database remains separate. No original customer file, real employee or production database is used. Guest-reported UTC retains the earlier observed offset; no time change was performed, and Today/wall-clock accuracy is not certified. Explicit work dates use the existing local-date model.

## Confirmed tool failure

The instrumented original selector failed in the full fixture after 333.254 seconds (exit 1) at `ExpandCollapsePattern.Expand()` on `assignment-crew`. The complete local chain was `MethodInvocationException` → `InvalidOperationException`, HResult `0x80131509`, with stack through `MS.Internal.Automation.UiaCoreApi.CheckError`. The application was visible and foreground; target enabled, focused, on screen and Collapsed. A fresh lookup returned the same Runtime ID as the old reference. This observed failure is not evidence of a detached control or a missing focus.

The reduced two-Crew/one-WorkItem original-cadence case also failed at Expand, before its first AM save (87.742 seconds / exit 1). A previous reduced attempt passed (112.313 seconds). Thus saved AM data is not a prerequisite; the provider rejection is intermittent. The old polling callback allowed that non-persisting UIA exception to escape immediately instead of continuing its bounded readiness wait. #81's original failure lacks an inner chain, so not every historical failure's exact native method can be reconstructed.

Separately, the inherited hidden-supervisor scenario timed out at the first Crew-navigation control (187.079 seconds / exit 2). A one-time initial visibility correction still failed (190.259 seconds / exit 2): the window later had Win32 visibility false, while UIA flags were misleading. The fix checks actual visibility/minimization and current PID ownership at every bounded GUI probe, restoring only the application started by this verifier. The handle is reset on each launch.

The Crew-choice fix uses one existing GUI deadline, re-resolves controls/patterns on every probe, verifies a committed desired label before repeating an action and logs recognized UIA refusals as retrying. No Save button, API/storage write or assertion is inside that retry. Unknown, denied and unsupported failures remain fatal; persistent provider failure still times out. No WebView2 or product workaround was introduced, and no product defect requiring a product-code Issue was demonstrated.

## Actual execution matrix

| Case | Status | Evidence |
| --- | --- | --- |
| Original-cadence reduced Crew selection | FAIL, retained | Expand rejection before first Draft; 87.742 s / exit 1 |
| Original full Employee Week fixture | FAIL, retained | Native Expand rejection; 333.254 s / exit 1; whole flow not certified |
| Original hidden supervisor | FAIL, retained | First control wait exceeded 150 s; 187.079 s / exit 2 |
| Initial one-time visibility correction | FAIL, retained | Later actual visibility false; 190.259 s / exit 2 |
| Fixed hidden-supervisor reduced case | PASS | 95.047 s / exit 0; two Crews/one WorkItem, first AM saved, repeat/alternate selection and Cancel; normal exits, zero remaining product processes, offline and original default-DB hash retained |
| Fixed normal reduced case | PASS | 101.480 s / exit 0; same reduced workflow, normal exits, offline and original default-DB hash retained |
| Fixed full Draft lifecycle and native weekly scrolling | PASS | Same-day AM/PM, Crew collision rejection, independent/repeated visits, SQLite/WAL unchanged on form Cancel, edit/cancel/reuse, empty week and disabled publishing; nine-Crew / 101+-Project UIA ScrollPattern geometry checks |
| Fixed Availability and explicit Draft workers | PASS | Inclusive cross-year full-day range; independent AM/PM and clear history; Cancel no-write; employee isolation; explicit borrowed worker, other Home Crew unchanged and no AM selection inferred on PM |
| Fixed Employee Week and save/reopen | PASS | Actual selected worker/dated Crew, empty other worker, recorded availability, read-only digest, Draft preview/disabled PDF-XLSX and directory handoff; reopened assignment IDs, worker choice, Home Crew/Unverified driver and availability states |
| Fixed complete native worker | PASS | **631.149 s / exit 0**; all preceding full cases plus note persistence, normal desktop/sidecar exits and deliberate database-startup-error/Retry display. Offline afterwards; remaining product processes 0. One genuine crew-type Expand rejection was logged as retrying and recovered, with final selection verified |
| Independent final closed-disk audit | PASS | Guest normally powered off; default and all eight temporary profiles integrity `ok` / FK errors 0; default original tables unchanged and all 87 installed-file hashes equal to the frozen original installation |
| Customer Demo/RC/UAT and production | NOT RUN / NOT GRANTED | No sign-off or Release authorization |

The actual successful verifier's printed SHA-256 matched the delivered source bytes: `3AE70917D5B01A285B56B0E6D28B697EE5178928765BBEA0CB71856B798301D9`. Detailed-diagnostic helper SHA-256: `8635D18A8DC614FD965E63699BFED516FEF64D60459198A92D637C7AF7E0D737`. These identify the new tools, not a changed installer.

Final full-profile audit found 101 Projects, two WorkItems, 11 Crews, two Employees, four stored visits (three Draft and one Cancelled), one staffing-change/member and three current availability cells / three history events. IDs 1/2/4 retain Civil WorkItem 1; Tower visit 3 retains WorkItem 2; Crew ID 3 and cross-year local dates persist. Only Employee 1 is explicitly saved on visit 4, with recorded Home Crew 2 unchanged. The AM cancelled ID 1 stays retained; replacement ID 4 is independent. Schema history remains nine. No UIA retry was mistaken for a duplicate Save.

The separate installed default database remains the earlier one-Project/two-WorkItem/demo-note fixture, with original logical tables and main-file SHA-256 unchanged:

`1A079819A74C9F46BA795C3F41649975744E01326019868AE02859284BF1A201`

Normal versus hidden comparison covers the reduced test in both modes. The full successful chain used a Normal supervisor; a complete Hidden-supervisor chain was not separately run. These scoped results do not certify a locked/non-interactive session or every Windows/WebView2 edition.

## Reproduce and verify

Use a disposable authorized guest and the exact installed package/hash. Verify no network and no unrelated Rigarus process. Run the reduced verifier on an interactive Windows PowerShell 5.1 desktop with `-ReproduceCrewChoice -Profile SlowVm -RequireOffline -PreserveSyntheticProfile`, local event/JSONL paths and the installed executable. The helper creates two Crews, one Project/WorkItem, saves December 31 AM, reopens Assign, reselects the first Crew, selects the second and cancels. To compare supervisors, start that same command with Normal versus Hidden PowerShell window style; the application itself is made visible by the owned-window guard. Do not equate an HWND or UIA IsOffscreen flag with visible interactive content.

Run a separate fresh `-IncludeEmployeeWeek -Profile SlowVm -RequireOffline -PreserveSyntheticProfile` invocation. It includes the existing Crew, AM/PM/repeated-visit/conflict/cancel, availability, explicit-worker, read-only employee planning/preview, save/reopen and deliberate startup-error checks. The reduced flag cannot be combined with Include flags. UIA selection assertions require the intended final label, not only absence of an exception.

Wait limits remain Default GUI 30 / exit 12 seconds, SlowVm GUI 150 / exit 60; overrides retain their existing limits. This local supervisor bounded reduced workers to 600 seconds, full workers to 2,700 seconds and the launcher to 3,600. No unbounded retry or fixed success sleep was added. After product and guest normal shutdown, independently read profile/default SQLite including any WAL, integrity/FKs and all 87 installed files; compare the original default records and hashes. Live disk log reads are progress diagnostics, not final persistence evidence.

Detailed Message/InnerException/StackTrace/invocation and target before/after/fresh-control snapshots are sanitized JSONL on the authorized machine only. Paths/credentials are redacted; no clipboard or arbitrary desktop tree is dumped. Failed attempts remain alongside successes. Repository content contains only this reviewed summary, test scripts and synthetic harness data.

## Engineering checks and remaining gates

The following actual local engineering checks passed:

- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Test-TauriAcceptanceHarness.ps1` on Windows PowerShell 5.1, including new nested/aggregate chains and invocation evidence, redaction, healthy/detached targets, generated-kit helper inclusion, transient Expand/detached/disabled recovery, strict label/status matching, persistent failure deadlines, hard unknown/denied/unsupported errors, conflicting reduced/full scope and real foreign/invalid-HWND ownership rejection. Existing installer/GUI/sidecar/WAL harness cases also passed.
- PowerShell parser checks, Git whitespace check and Markdown local-link/fence/sanitized-locator checks. Staged privacy and current-head Windows CI are recorded with the associated Draft PR; CI remains independent of the actual native results above.

Product restores/builds were not repeated locally for this scripts/documentation-only change. The existing Windows CI performs its locked dependency restores, formatting, .NET/backend/frontend/Rust tests and Windows package builds. A newly built CI installer is not substituted for this unchanged original package.

This is native regression evidence, not a new offline installer/upgrade certification; previous same-package lifecycle results remain in PR #81. Managed-device policy, signing/SmartScreen, different-version upgrades, interrupted migration/setup recovery, cross-machine application restore, complete driver/qualification/Rig safety, real exports, customer acceptance and production approval stay separate. #35/#42 remain open. Draft for human review, no auto merge or Release.
