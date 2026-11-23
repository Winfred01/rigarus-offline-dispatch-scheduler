# Issue #35 — latest installed-package offline attempt

November 22 client date; execution continued on November 23 UTC. This is an unsuccessful engineering acceptance attempt, not a completed offline gate. See the [Design-First record](../design/2026-11-22-issue-35-latest-offline-checklist.md). PRs #78 and #79 were already human-merged before this run.

## Exact package

- Main: `cb1da4892b8945c937dfa4fba8d56dcb47864f71`; branch `codex/issue-35-latest-offline`.
- Original [Windows CI 45098508871](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/45098508871), all three jobs successful; artifact `14784048866`. Archive SHA-256 `d4e8e51af06cec44ac57e7b05414dac520cd00d6359fcfb077a50e1c8e1d9538`.
- Unmodified 0.1.0 x64 `Rigarus-Dispatch-x64-setup.exe`: SHA-256 `F684B592A07C0E4FAA31119D7468A51DA0F5064CAB56AEE5815F5E5DB680F4AF`, matching original `build.json`.
- Build commit `1fc06dbc96670ff3c167d5bf64999ea826b86057` is the PR test merge. Its tree and main's tree are both `21642491468dfad6dea81a7b9bf777131dc41b5a`.
- Original `Test-TauriDesktop.ps1`: `4049FDE7DDB1D11403A0EBDF98C41CF92E1D056A9815E91611CC1CAD7E6E1567`; `Test-TauriOfflineInstall.ps1`: `2997AC64709BB6AA30F365F4EA6AB0311A5A8EDBCAA17FC5C2738610BDC35D54`; `TauriAcceptanceSupport.ps1`: `4ED08E74AF4044DEA1895BDACDDB3D14B46F3AC644CE128DE331DAD1C0ABCF1D`. Original files remain unchanged; local orchestration/probes are separate tools.

## Environment and results

Fresh Windows Sandbox guest: Windows 11 Enterprise x64 build 26100, 6 GiB assigned RAM, networking disabled in the `.wsb` configuration. Guest network API returned false before installation and at final collection. The checked common developer commands were absent. Only the kit was mapped read-only; a dedicated synthetic-results folder was writable. Host Windows 11 Pro build 26200 is not the tested guest.

The default Sandbox account was an administrator and elevated. This run cannot certify standard-user installation, managed enterprise policy or a clean no-WebView2 image. WebView2 was already registered as `157.0.4341.46` before setup.

| Case | Result | Actual evidence |
| --- | --- | --- |
| Package/build/script provenance | PASS | Manifest, hashes and source-tree comparison above |
| Disconnected guest/common developer-tool preflight | PASS | `preflight.json`; original `install-events.log` |
| Original installer execution | PASS, installation phase only | Exit 0 in 20.463 seconds; 900-second bound |
| Usable first launch | FAIL / GUI TIMEOUT | Top-level window appeared in 0.195 seconds, but remained blank with a native missing-WebView2 error. `Data` never became ready within 150 seconds. Original desktop worker exit 2; full smoke elapsed 152.760 seconds |
| Employee Week, availability and Draft GUI behavior | NOT RUN | Blocked before usable frontend; no transfer of earlier host/native results |
| Save/reopen, default-profile IDs/notes and restart persistence | NOT RUN | First-launch failure prevented synthetic data creation |
| Installed-old-to-latest upgrade, VM reboot and uninstall/reinstall | NOT RUN | No stable usable image established for this package |
| Clean image without WebView2 / standard non-admin context | BLOCKED | This Sandbox has registered runtime and an elevated account; the older independent evaluation VM had self-powered off |
| Normal application/sidecar exit | NOT RUN | Sidecar was not observed running; discarding a failed guest is not a normal-exit pass |
| Customer Demo / RC / production | NOT RUN / NOT GRANTED | Engineering attempt did not complete |

Original local evidence identifiers: `preflight.json`, `install-events.log`, `install-output.log`, `pristine-runtime-error.png`, `runtime-probe.json` and `final-environment.json`. Raw files, screenshots and machine paths stay on the authorized machine; this document is a reviewed summary.

The local outer orchestration helper also failed to capture its redirected worker's exit code (null). Its message is not the basis for the first-launch conclusion: the original inner script independently recorded the GUI timeout/exit 2, and the retained guest screenshot shows the runtime error. A future helper must access the child process handle immediately after `Start-Process -PassThru`, then wait/read the exit code; preserve this failed attempt rather than overwrite its logs.

## Separate image diagnostics — not acceptance passes

1. Before image changes, the registration said `157.0.4341.46`, but the only discovered standard runtime executable was in `157.0.4341.60`; the registered-version directory was absent. The executable had a valid Microsoft signature. Do not conclude that the version mismatch alone caused the failure.
2. Running the same embedded signed Microsoft standalone runtime installer separately returned `-2147219198` (`0x80040902`) in 38.508 seconds. Its inner installer reported exit 11 / unable to create a temporary directory. The guest had free disk space and SYSTEM temp-directory probes succeeded; the underlying cause remains unestablished. This was separate from Rigarus setup's successful exit 0.
3. In this disposable guest only, aligning the recorded version with the signed existing executable did not make the application launch. A separate native smoke again timed out after 150.009 seconds, exit 2. No host registration, security setting, clock or activation was changed.
4. The SDK loader API returned `0x80070002` and no version with its default search. Supplying the existing runtime directory explicitly returned success and `157.0.4341.60`. This establishes a default-discovery failure in this image, not usable application behavior. No runtime-path override was introduced into the product or counted as a pass.

Microsoft documents both registry detection and the [runtime version API](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution#detect-if-a-webview2-runtime-is-already-installed). In this image they disagree. A nonzero registry version and setup exit 0 are insufficient evidence that this actual first launch worked. A healthy independent Windows image is needed before attributing the failure to either the product or Sandbox components.

## Reproduction and next gate

1. Retain the exact CI kit above and verify the installer SHA-256 against `build.json`. Use a fresh authorized Windows 11 x64 VM with enough uninterrupted uptime; record license/image health without changing its clock or activation to conceal expiry.
2. Before disconnecting, prepare the image as required. Record account membership/elevation, OS/build, checked development tools, WebView2 registration and actual files; probe default runtime discovery. A no-runtime scenario must be separately demonstrated, not inferred from a broken existing registration.
3. Remove/disable the guest virtual network, verify it is unavailable, and run the original kit on its interactive desktop:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File .\Test-TauriOfflineInstall.ps1 -Profile SlowVm -DiagnosticLog C:\RigarusResults\fresh-install.log
```

4. SlowVm bounds are installation 900 seconds, each GUI readiness 150 seconds and combined desktop/sidecar exit 60 seconds. The original installer verifier caps its full GUI worker at 2,700 seconds; the local outer launcher used a 1,500-second bound. A top-level window alone does not establish frontend or sidecar readiness.
5. Only after first launch succeeds, run the original desktop verifier with `-IncludeEmployeeWeek -Profile SlowVm -RequireOffline` against the installed executable. Separately test old installed build → current build, stable Project/WorkItem IDs and associations/notes, reopening, actual guest reboot and uninstall/reinstall retention. Do not use temporary smoke-profile data as proof of default-database retention.

Earlier #35/#69 installed-package passes remain historical. The #77 VM attempt was interrupted by guest poweroff; an expired-evaluation watermark was observed, but the cause was not established. Neither result completes acceptance for this latest installer. No new installer, product code, dependency, API or database migration was made in this branch; existing schema nine remains unchanged.

Owner's next sequence: finish stable offline acceptance, then inspect/design #26 Crew/WorkItem working calendars, followed by #28 explainable candidate proposals. Available means recorded availability only; it grants neither qualification nor assignment/publication. #28 still depends on validation and calendars, must explain missing checks, and must never automatically commit a recommendation. No #26/#28 feature is implemented here. Human review, customer acceptance and production approval remain separate; no Issue closure, merge or Release is authorized by these results.
