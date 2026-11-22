# Issue #35 weekly desktop installer verification

Refs #35, supporting the merged #14/#16 implementation. See the [Design-First source/version checklist](../design/2026-11-22-issue-35-weekly-offline-checklist.md). Engineering checks, customer Demo acceptance and production approval are separate.

## Package and code identity

- Baseline main `e0fc234e590c9ce6df74589e7cee00fc2b5af09e`, manually merged PR #73; head `da66698fd9949735b9735a7f698d57e83ca02280`. Original [Windows CI 45017551111](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/45017551111) succeeded, including upload.
- Original CI artifact `14751903688`, 315,401,356 bytes; archive SHA-256 `f3e9a28c8ee7e7bf99724580d9bd39ab0a66ebd0fd25a48720e3a9c0515c27db` matches GitHub's digest.
- Installer 0.1.0 Windows x64 SHA-256 `8D1C520EA46E8FABB6B61FBFE7615A3071F899219C99DBDAD503756B4EE0B2D4`, matches original `build.json`. Build commit `2b1fd0272d0360576062e4a55ecd4798dd7094c5`, head `da66698` and merged main `e0fc234` all have source tree `1fe71a25667ccab24ac76274e4e109cd6cc66754`.
- The installer is unmodified. Original kit/scripts remain separately retained; the new verifier and its hash are distributed as explicit test-tool overrides on read-only media. Do not call an overridden verifier the unmodified original CI script.
- Final local candidate EXE `018f27ef36e3485d75574015d5f052a1dbd094aa5ffc4bddede373dbe70d42d9` is used for host tool development. It is distinct from the installed CI binary and from intermediate local candidates. Intermediate/debug runs are not final acceptance evidence.

## Harness changes and scope

`Test-TauriDesktop.ps1 -IncludeAssignments` now follows the actual weekly board and modal lifecycle. Native select options use SelectionItem, pressed cards support Toggle, and date navigation uses the actual Year/Month/Day segment order. The entered ISO value is verified before Go; WebView2's advertised date ValuePattern silently retained the old date during the original approach.

The synthetic native workflow creates nine Crews, 100 bulk-added Projects plus the scheduling Project, and independently selected Civil/Tower WorkItems. It checks both saved boards, AM/PM, conflicts with retained notes, form Cancel via unchanged main DB/WAL digest, edit, Keep/confirm saved cancel, freed-slot reuse, empty-week navigation, unavailable Publish, exact WorkItem IDs and notes after application restart, normal window close/sidecar exit and startup-error Retry. Date segments are targeted individually and their numeric values verified: MDY auto-advance cannot be safely modeled by a fixed right-arrow sequence. Native injected input is guarded by the test window's foreground ownership and point ownership; it does not target arbitrary other windows.

Scroll checks compare actual UIA rectangles and fixed date/roster positions. A long roster row may exceed the body viewport; both its top and bottom must be reachable with matching date-cell geometry, rather than requiring an unapproved maximum member/name/row height. Window size is 1000x720 DIPs with target-window DPI conversion. This is native UIA ScrollPattern evidence, not a physical mouse-wheel or scrollbar-drag certification.

## Executed checks

| Check | Actual result |
| --- | --- |
| Original CI archive, manifest, installer and source-tree provenance | PASS |
| Correctly identified final local candidate, native Windows host | PASS: scale scroll at 16.932 s, assignment lifecycle 17.736 s, reopen 20.800 s, full smoke 24.544 s; desktop/sidecar normal exits 0 |
| Same-day AM/PM, repeated WorkItem visits, Crew-slot collision/correction | PASS host; independent Civil/Tower identity verified after restart |
| No-write form Cancel and saved cancellation | PASS host; DB/WAL unchanged on form cancellation; saved cancelled card absent and freed slot reused |
| Nine Crews, 100+ Projects and long last-row label | PASS host; shared views and actual native scroll geometry |
| PowerShell 5.1 harness regressions | PASS: original success/slow-success/install-failure/GUI-timeout/sidecar-failure cases plus real weekly helpers; three locale date orders, invalid date/segments, unchanged reads, WAL/main-file mutations and exact missing-card timeout/diagnostic |
| Retained host synthetic SQLite, independently read after normal close | PASS: 101 Projects, 9 Crews, 3 Draft / 1 Cancelled, IDs 1–4, original cancelled notes, edited PM notes and distinct Civil/Tower IDs; unsaved January 2 absent, integrity ok / no FK errors |
| Local locked restores / format / Windows builds / regression | PASS: `uv sync --locked --group bundle`, ruff check/format, 68 Python tests; PyInstaller build and 8 actual packaged-sidecar tests; `npm ci --offline`, format, 22 frontend tests and Vite build; locked offline Cargo fetch/rustfmt, Windows Release desktop build and 6 Rust tests; .NET locked restore/format/Release build and 35 tests |
| Isolated offline original CI installed-package upgrade and original data retention | PASS: setup 171.262 s / exit 0, migrations 5→7, original records/IDs/notes retained; further weekly/reboot verification is recorded in the PR/Issue follow-up |
| Staged whitespace/privacy and branch CI | Recorded after staging and actual PR execution |

Host conditions: Windows 11 Pro x64 build 26200, preinstalled WebView2, network active and developer tools present. Host run explicitly overrides GUI waits to 15 s; exit bound is 12 s. No test-only IPC proxy or browser CDP replacement is used by this UIA verifier. Tests use generated temporary SQLite profiles; the default operational database is not touched on the host. `-PreserveSyntheticProfile` explicitly retains only that generated profile for local evidence; the normal default still cleans it up. Never upload retained database files.

Debug evidence is retained locally, including unsuccessful native action/date/text/geometry probes. An intermediate local candidate was initially used by mistake; its runs are excluded from the final hash-matched result. Only a subsequent serial final-candidate run provides the reported host PASS. The complete DOCX, raw screenshots/logs and databases are not uploaded.

## Offline VM result

A new isolated overlay over the authorized PR #69 installed synthetic image has no virtual NIC. Preflight recorded Windows 11 IoT Enterprise LTSC Evaluation x64 build 26100, `NetworkAvailable=False`, zero checked developer commands, `AdministratorMember=False / elevated=False`. Preinstalled WebView2 is 158.0.4370.33. The evaluation guest displays an expired-license watermark; activation, time and security policy are not changed. This is not a managed customer device.

Original CI setup completed in 171.262 seconds, exit 0, without an observed elevation/credential prompt. Its signer is `NotSigned`. Installed program SHA-256 is `9b3a657dd0fd211b392a82833e78acfd7ff44bd5e8329429eac1409b5c32a548`; read-only post-shutdown extraction found 87 installed files. The default database path and original Project ID 1, WorkItem IDs 1/2 / ProjectId 1, counts/estimates, leading-zero Site ID and note are preserved. Existing history has 5 entries before and 7 after. A consistent pre-upgrade backup remains local; logical original-table comparisons and integrity/FK checks passed.

This is an in-place upgrade between different builds with the same version number 0.1.0, not a version-increment upgrade, missing-WebView2 clean installation or representative managed-device certification. The first post-upgrade outer verifier failed at its MDY date-entry helper after installation/data-preservation checks had passed. The error was an unsubmitted date input; it is not evidence of product data loss. Original failure logs are retained. The corrected verifier resumes the same installed program with its exact hash checked; setup is not silently rerun.

The default-profile checks must distinguish the preserved installed database from the full verifier's temporary synthetic profile. Installation, Start-menu launch, actual original Project/WorkItem/note reads, a new saved default-profile Draft, normal application reopen and an actual VM power cycle require their own recorded evidence. Do not infer them from a package build or host run.

The frozen-script full weekly run and actual final VM power-cycle outcome are recorded in the associated PR / Issue #35 verification follow-up when executed. Any not-yet-recorded stage remains pending; the preceding limited PASS rows do not complete the full Issue or customer gate.

## Reproduction and remaining gates

After separately verifying/recording installation of the intended package, run the verifier against its installed executable:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File scripts/Test-TauriDesktop.ps1 -Executable <installed-exe> -IncludeAssignments -Profile SlowVm -RequireOffline -DiagnosticLog <local-log>
```

Default GUI/exit bounds remain 30/12 seconds; SlowVm 150/60 seconds. The local VM workflow bounds setup at 900 seconds, full GUI worker at 1,500 seconds and launcher at 3,000 seconds. No wait is unlimited. Keep the original installer/hash/build manifest separately from test-tool overrides.

No product UI/API/domain/dependency/schema changes are introduced by this branch. The tested #73 program contains the existing additive migrations through schema 7. Migration history is never edited to downgrade; earlier builds need their consistent original backup.

NOT RUN unless separately evidenced: different version-number upgrade/downgrade, uninstall/reinstall, interrupted installation recovery, cross-machine application backup/restore (#34), new clean no-WebView2 path for this package, managed enterprise policy/approved distribution/signing, physical input and human assistive technology. #22 actual staffing/leave, #71 Employee Week/export, #15/#23 complete hard validation/immutable publication and customer AM/PM decisions remain open. Customer Demo B / RC / UAT and production approval remain pending. No automatic merge, Issue closure, release or real customer database access.
