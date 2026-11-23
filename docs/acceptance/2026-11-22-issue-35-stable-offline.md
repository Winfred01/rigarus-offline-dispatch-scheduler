# Issue #35 — independent Windows offline acceptance

The client run started November 22, 2026 and continued November 23 (America/Toronto); raw execution logs use UTC. This record concerns the original feature installer, not a rebuilt documentation-PR package. See the [Design-First record](../design/2026-11-22-issue-35-stable-offline-checklist.md). Engineering verification, customer acceptance and production approval are separate.

## Baseline and exact package

PR #80 was human-merged as `ebc78409cead320e87922de8087c06ccad453c97`. Its [Windows CI 45103580324](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/45103580324), head `b95d048eb6126be588f548130f441a0414bdc474`, completed all three jobs successfully. That is a source/CI result, not an offline VM result.

The tested latest installer remains the unmodified original [feature CI 45098508871](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/45098508871), artifact `14784048866`, version 0.1.0 x64:

- Installer SHA-256: `F684B592A07C0E4FAA31119D7468A51DA0F5064CAB56AEE5815F5E5DB680F4AF`.
- Original manifest build: `1fc06dbc96670ff3c167d5bf64999ea826b86057`; source tree `21642491468dfad6dea81a7b9bf777131dc41b5a`, matching the merged feature baseline before documentation-only changes.
- Actually installed client: `24B5BB5C3C7934E7FBC79283698003CE6A421C1A3E5FF1D1FF42CB42043B78C2`; packaged sidecar: `0599AADC205F6D544C3AD90D76FD5415BE0B950B1B6A1F5ED4F9354DBE53994C`. Independent post-shutdown extraction found 87 installed files.
- Original kit script identities remain those in [the preceding attempt](2026-11-22-issue-35-latest-offline.md#exact-package). The original offline installer script and desktop worker ran unchanged. Separate local lifecycle helpers are explicitly additional test tools, not the original CI verifier.

The separately installed old baseline is the original PR #69 package, build `e3ee0edbd0ded74b5368ac223c47fa05eae5d0a3`, installer SHA-256 `BE8248634D37C720ECBF4924D1FEAEC50E66659090A2C61F72D005FD1F28F4C7`. Its actual client SHA-256 is `AC841EBEFE5795F463AC9B15D096C75F196AF87485D053E1D8A5D828EC130DF9`. This compares different builds carrying the same 0.1.0 version number; it is not a distinct semantic-version upgrade test. Old setup in the serial scenario exited 0 in 662.243 seconds, after starting from the separately confirmed absent-runtime state.

## Image preparation and scope

A new QEMU overlay was created over the existing authorized, synthetic Windows 11 IoT Enterprise LTSC Evaluation x64 build 26100 no-WebView2 test image. Source disks were preserved. The preparation guest alone temporarily had a NAT adapter. Normal Windows licensing reported `LicenseStatus=1`, with approximately 90 days remaining; after a normal power cycle the desktop changed from the old expired watermark to `Windows License valid for 90 days`. No rearm, product-key replacement, activation bypass, host reboot, host clock change or security-policy change was performed. No explicit activation command was needed in this attempt. The earlier guest poweroff's unique cause is not established by this observation; Microsoft's [evaluation guidance](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-11-iot-enterprise-ltsc) explains why licensing health is a prerequisite.

The prepared disk was shut down and frozen. Independent fresh-install and upgrade overlays were then started with **`-nic none`**, 6 GiB guest RAM and four emulated CPUs (TCG). Test-account membership and elevation were both false. Checked common Node/Python/Rust/.NET development commands were absent. Three runtime registration locations and four standard directories were inspected before setup: no WebView2 registration or executable was present. This is a prepared test image, not certification of a stock retail image or a representative managed enterprise device.

An initial attempt to run two emulated guests concurrently reduced host free RAM below 1 GiB. The unfinished upgrade attempt was stopped through normal guest ACPI shutdown, preserved locally and excluded from product results. Remaining work runs serially. No unrelated host application was closed. The guest's reported UTC was approximately eight hours ahead of the host; its clock was not manually changed. Do not use these logs to certify wall-clock accuracy or Today behavior; kernel-restart comparisons use the same guest, and explicit synthetic local dates are separate from UTC timestamps.

## Actual results

| Scenario | Status | Observed evidence |
| --- | --- | --- |
| Original latest package identity / disconnected non-admin no-SDK preflight | PASS | Manifest/SHA-256 matched; network unavailable; account not elevated; no runtime in checked locations |
| Clean prepared no-WebView2 installation | PASS | Original NSIS setup exit 0 in **708.203 s**; bundled per-user WebView2 **158.0.4370.33** installed without an observed administrator-credential prompt |
| Original offline kit / native first use | PASS | Original desktop worker exit 0 in **328.595 s**; outer original-kit worker exit 0 in **1103.653 s**. Actual Data/demo note, save/reopen, Project Master, sidecar normal exit and deliberate database-error/Retry checks completed; network remained unavailable |
| Start-menu/default-database save and application reopen | PASS | Exact installed executable/hash and matching shortcut; one synthetic Project, two WorkItems and demo note created through GUI; original rows/IDs/links/leading-zero Site ID retained |
| Actual Windows Restart, then installed-app relaunch | PASS | Guest `shutdown.exe /r /t 0`; kernel boot UTC changed from `2026-11-23T11:48:50.5000000Z` to `2026-11-23T12:39:52.5000000Z`. Same shortcut/app, SQLite records and normal desktop/sidecar exits; no NIC |
| Independent closed-disk audit after fresh scenario | PASS | Nine migrations, Project ID 1, WorkItem IDs 1/2 both referencing Project 1; Site ID `0007`; demo note equal; integrity `ok`, zero FK errors, installed hashes as above |
| Old installed build → latest overwrite upgrade and retained original data | PASS | Latest setup exit 0 in **189.207 s**; old tables/IDs/links/demo note preserved; migration history **5→9**, existing entries retained. Subsequent installed-app reopen and original-record comparison also passed; resource-aborted attempt excluded |
| Upgraded image actual Restart / preserved default data | PASS | Kernel boot UTC changed from `2026-11-23T11:48:50.5000000Z` to `2026-11-23T13:18:40.5000000Z`; Start-menu launch, original records and normal exit passed, still offline |
| Additional current Employee Week/availability/Draft native fixture | NOT RUN at this core snapshot | Separate opt-in verifier; any subsequent actual result is recorded in the associated PR/Issue follow-up, not inferred from the basic kit |
| Uninstall/reinstall retention for this package | PASS | Uninstall exit 0 / **22.486 s**; default DB retained and original rows equal. Same latest package reinstall exit 0 / **170.394 s**; matching client/sidecar, Start-menu GUI and stored records passed |
| Customer Demo / RC / production | NOT RUN / NOT GRANTED | No client sign-off or distribution approval is implied |

The fresh default database's main-file SHA-256 was identical after initial GUI save, normal application reopen and actual guest Restart:

`3790D24983D490ABD88DC03CF073CF3C2851BE78BEF4F94D9E508C44C273D481`

Across a schema-changing upgrade, a changed main-file hash is expected: compare original table contents and migration-history prefix, then compare the resulting schema-nine file through subsequent reopen/Restart.

The upgraded schema-nine database's SHA-256 was identical after migration, application reopen, real Restart, uninstall and same-package reinstall:

`1A079819A74C9F46BA795C3F41649975744E01326019868AE02859284BF1A201`

Independent closed-disk audit confirmed the original Project ID 1 / WorkItem IDs 1 and 2, associations, `0007` and demo note; integrity `ok`, zero FK errors. All **87 installed file hashes** matched the independently tested fresh installation, despite the different installation-directory names. This core snapshot was frozen before the additional opt-in desktop fixture; later results belong to the same unchanged installer and are reported separately.

Both in-guest read-only SQLite snapshots and an independent host read after guest shutdown verified the fresh records. The note in this case is the existing **demo note**; this does not invent Project/WorkItem note fields. Smoke-test temporary profiles are distinct from the default installed database. Live read-only log inspection was used for progress only, never as final persistence evidence.

## WebView2 findings and test-tool limitations

The preceding Sandbox failure remains a separate FAIL: it had inconsistent registered/actual runtime versions and a failed default loader probe. In this independent image, the same installer deployed a coherent per-user runtime from an absent-runtime state, and the installed app opened and reopened without specifying a browser-runtime directory. Registered and actual versions are both `158.0.4370.33`; runtime executable SHA-256 `B9845539AFFBB9C8346BF56FCC28F57FCC5A9E8F7DDC67B20FAD6EBCC663418E`. An x64 SDK-loader probe also returned default-discovery HRESULT `00000000` / version `158.0.4370.33`, with `browserFolderOverridePresent=false`; its API call had a 30-second limit. No product startup override or installer change was used. The original Sandbox's complete underlying cause remains unconfirmed; do not relabel its failure as a pass or infer a universal product defect from it.

The original offline kit passed before additional local-helper failures occurred. One extension used an invalid `Where-Object` parameter spelling; a later attached-process close lacked a retained handle, so the application really exited but its exit code was unavailable to that helper. Both local-tool defects were corrected and their failed logs retained. The explicit resume path required the original offline PASS, verified installed hashes and continued **without rerunning setup**. The subsequent save/reopen/Restart checks passed. A delayed post-login test entry was observed; this does not certify a product auto-start feature. An ACPI power cycle alone had preserved kernel startup time through Windows fast startup, so it was not counted as the actual Restart gate.

## Reproduction and remaining gates

Use only an authorized disposable test guest and synthetic records. Keep exact package/hash/manifest, old package if applicable, preflight, account/elevation, networking and runtime before/after evidence. Prepare/activate Windows normally before disconnecting; never conceal an expired evaluation by changing clocks or license data. Freeze the clean image, run guests serially with adequate host memory, and remove their virtual adapters before setup.

Run the unchanged kit from its directory on an interactive Windows PowerShell 5.1 desktop:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File .\Test-TauriOfflineInstall.ps1 -Profile SlowVm -InstallTimeoutSeconds 1800 -DiagnosticLog <new-local-log>
```

The explicit install override is 1,800 seconds; the SlowVm defaults otherwise remain GUI 150 / combined app-sidecar exit 60 seconds. The original full GUI-worker bound is 2,700 seconds; the local kit supervisor used 3,600 seconds and the local overall launcher 4,800 seconds. No wait was unlimited. Wake an idle guest display as normal user activity if needed; do not change security or power policies to manufacture a pass.

For default-data retention, launch the exact installed program via its verified Start-menu shortcut, save a synthetic Project/two WorkItems/demo note, close normally, take a consistent read-only snapshot, reopen and compare. Perform a real guest Restart and verify changed kernel startup time before comparing again. After normal guest shutdown, independently audit the default SQLite database, optional WAL, installed-file hashes, integrity and foreign keys. For upgrades, use a separate clean overlay and retain an old-build closed database backup; do not operationally downgrade schema history. Local orchestration/diagnostics, original designs, screenshots, disk images and raw databases remain on the authorized machine.

No product source, API, dependency or migration is changed in this evidence branch. Managed-device policy, approved Internet-download/distribution channel, signing/SmartScreen, different version-number upgrade/downgrade, interrupted-setup recovery, cross-machine application backup/restore, complete safety/publishing/export, customer UAT and production approval remain separate gates unless explicitly recorded in the associated PR/Issue follow-up. #35/#42 remain open; no automatic merge or Release.
