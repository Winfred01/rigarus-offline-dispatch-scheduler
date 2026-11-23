# Issue #26 — shared Project calendars engineering record

November 23, 2026, America/Toronto. Follow-up to the human-merged `7435f35` foundation in PR #83. The owner merged it during implementation; this approved storage/editor continuation was moved onto main `3543e2c` using branch `codex/issue-26-project-calendars` and a separate Draft PR. See [the freshly read sources and Design-First plan](../design/2026-11-23-issue-26-project-calendar-checklist.md). Owner-confirmed order and ownership/Draft decisions are in [the project plan](../00-PROJECT-PLAN.md) and [decision register](../10-CLIENT-DECISIONS.md).

## Implemented behavior and data compatibility

Crew and Project calendars now persist explicit inclusive FullDay/AM/PM Working / NotWorking / Unknown ranges. WorkItems inherit their real persisted parent Project; no WorkItem write or override exists. Unknown clears current cells without removing history. Independent AM-only/PM-only edits preserve the other half-day. Saves share one write transaction, reject stale revisions and append nothing for unchanged state. History retains immutable ownership and every committed range event.

Draft cards, form preview and saved details consume the shared calendar model and report conflict/pending/matched states. Calendar closure/unknown can remain Draft; existing Crew-slot collision rejection remains. Calendar updates never move visits or alter original IDs, notes, workers or assignment revisions. Calendar match, employee Available and current Foreman master data do not certify driver/personnel/qualification/Rig or weekend compliance. Publish remains unavailable.

Migration `20261123020000_AddWorkingCalendars` adds schema ten only. Synthetic migration tests include populated Project/WorkItem, Crew/Employee, Rig, Foreman, availability, staffing, Draft and note records, with post-DDL rollback/retry and partial-cell failure rollback. The actual previous backend `41784e24b80e7515a6a04dc314ce488241a0b50e` created a schema-nine fixture: upgrading preserved all 12 original non-history tables, integrity `ok`, foreign-key errors 0. That prior backend rejects schema ten without logical mutation; its consistent pre-upgrade SQLite backup remains readable with original text IDs and notes. This is an engineering backup API demonstration, not a new user-facing backup/restore feature. Never drop tables or edit history for an operational downgrade.

## Reproducible automated checks

From `src/Rigarus.Backend`:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -v
```

From repository root run `scripts/Build-RigarusSidecar.ps1`, then rerun `test_sidecar.py` with `RIGARUS_SIDECAR_TEST_EXE` pointing to the built sidecar. From `src/Rigarus.Tauri` run `npm ci`, `npm run format`, `npm test`, `npm run build`, Rust 1.95 locked fetch/format/tests and `npm run tauri -- build -- --locked`. Run the existing PowerShell acceptance harness in Windows PowerShell 5.1, then stage explicit safe paths and execute `git diff --cached --check` and `scripts/Test-RepositoryPrivacy.ps1`.

| Check | Actual status | Evidence / boundary |
| --- | --- | --- |
| Locked dependency restores | PASS | Existing uv/npm/Cargo locks; no dependency changes. Rust fetch used cached locked dependencies offline |
| Backend regression | PASS | 111 tests / 40.240 seconds, including shared inheritance, independent Crews, advisory Draft saves, strict errors, concurrent/stale/no-op writes, sparse clear/history, rollback/retry and source-sidecar authentication/restart |
| Packaged Windows sidecar | PASS | 11 tests / 16.686 seconds; new calendar read/write/authentication/inheritance/restart included |
| Frontend format, unit and TypeScript/Vite build | PASS | 35 tests, no skipped tests; feedback preserves Unknown/closure and names inherited Project |
| Rust bridge/readiness tests | PASS | 8 tests, including path whitelist/ID limits and refusal of WorkItem calendar owner paths |
| Windows Release and NSIS packaging | PASS | Separate local candidate outputs; previous tested installation/installer preserved. Local candidate was built from source commit `3595eade23a314704191c89521c1c6e60c60ed21`; the follow-up branch has identical product and verifier content (only planning/provenance text changes after transfer). Final local candidate: client SHA-256 `44EA201CA1E1B03694DCF0FF5EF4F37576A2D29A68F58DC88D48D933DBE73F31`, sidecar `39B1E073F2E89553C0CC0C5A27718E006146659E44BD2E81C29099F1C1545EE8`, NSIS `CAE2E256DBC54F391EB7BF387EED1AEA6F12A193520EB7AAFCE6DA11FBA3021F`. Current-head CI is recorded with PR |
| Existing acceptance-tool harness | PASS | Windows PowerShell 5.1; bounded installer/GUI/sidecar/error/UIA and no-write/WAL cases. Local launcher used standard Windows PowerShell modules after inherited host module lookup failed |
| Native working-calendar GUI and reopen | PASS | Corrected full UIA run 41.987 seconds on connected Windows x64 build 26200; independent synthetic profile, shared Project/independent Crew ranges, AM/PM/clear/history, Cancel no-write, current Draft feedback/save, board refresh, app reopen and normal sidecar exit |
| Screenshot, keyboard, error and delayed-read checks | NOT RUN | Final outcomes/conditions attached to PR |
| Disconnected VM / installation / upgrade / reboot | NOT RUN | Any execution must be independently identified; host networking is active and model no-I/O tests are not an offline installer pass |
| Staged documentation/whitespace/privacy and current-head CI | NOT RUN | Final results attached after staging/push; original foundation CI is historical |
| Customer Demo E / UAT / production | NOT RUN / NOT RUN / NOT GRANTED | Human acceptance remains separate |

## Native reproduction and retained failures

Use only an independent synthetic profile and the matching candidate executable. Run the [opt-in working-calendar scenario](../05-DEMO-ACCEPTANCE.md#project-shared-working-calendars-engineering-check-26) with `-IncludeWorkingCalendars -Profile SlowVm -PreserveSyntheticProfile`; only add `-RequireOffline` when the test environment is actually disconnected. The case includes previous assignment create/edit/cancel/reuse, a shared Project range, independent Crew dates, AM/PM/clear/history, Cancel no-write, Draft feedback/save, application reopen and normal sidecar exit.

The first GUI launch failed before product startup because the developer runtime's inherited PowerShell module path could not resolve Get-FileHash. The launcher was corrected only for its child environment; no system module/security policy changed.

A subsequent native run timed out in the large Project picker. Recorded UIA reported a matching disabled DOM proxy without SelectionItem, while actual WebView DOM options were enabled. An independent native WebView keyboard probe selected the same Project correctly and closed normally. The new synthetic verifier uses the regular keyboard path for this large fixture picker only after checking the owned foreground window and the exact focused control; it verifies the committed complete label. It does not invoke a disabled UIA option, retry Save or relax product assertions. A separate new-scenario helper-name error was corrected to reuse the existing SQLite/WAL digest; its failed log remains local.

The next native run exposed a real follow-up defect: returning from calendar edits reused the Schedule component's pre-edit workspace, leaving old calendar feedback on saved Drafts. The new calendar route now has a separate component context; returning remounts the board and reads fresh data. Schedule date/employee remain owned by the outer shell. Old assignment navigation seeds are cleared on entry, preventing an already-consumed Assign request from replaying after return. Existing Job Schedule/Crew Board/Employee Week switching retains its shared context. The native conflict/pending/matched assertions exercise this exact return path.

Original designs/raw diagnostics/databases/screenshots and machine-specific paths remain local. The original November 22 Crew Board/Employee Week figures were compared as layout/state references; the working-calendar editor is an explicit new extension. Unknown cells use a neutral treatment, distinct from Working and NotWorking; existing Rigarus brand and offline assets are retained. Native WebView screenshots/keyboard checks and Windows UIA execution have separate evidence and conditions.

## Remaining work and gates

Recurring calendars, holiday defaults/import, exceptions/override priority, actual-worker weekend consent (#27), complete resource/driver/skills checks (#15/#23/#25/#24), proposals/sorting (#18/#28), locks/impact/Apply (#19/#20/#29) and validated Published exports (#17/#71/#32) remain separate. Follow the owner's dependency order; the M2–M5 numbers do not require a waterfall. Do not mark all of #26 complete from code, CI or this record; only executed acceptance cases may be checked, and customer sign-off remains the customer's decision.

One follow-up #26 branch and Draft PR for human review after the earlier foundation PR was human-merged. No auto merge, Issue closure, Release or customer-database edits.
