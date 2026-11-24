# Issue #86 — Project input protocol evidence

Source snapshot, November23,2026 America/Toronto. Latest main `ad87a52` includes
human merges87/89. Work reuses the existing Issue86 branch; product/package/API/
database/dependencies are unchanged. See [sources and refined plan](../design/2026-11-23-issue-86-input-sequence-checklist.md).
Final canonical native and current-head CI results will be attached to the Draft
PR/Issue; a pending row here is not an acceptance claim.

## Established boundary and controls

The old one-shot text/Enter path reproduced the same Project placeholder and
Collapsed timeout under Normal supervision (150.405s), despite all30 injected key
down/up events being observed with owned foreground and balanced modifiers. No
target Value/Expand event followed. This excludes a simple absence of OS input
injection in that sample, not lack of renderer consumption. Earlier full Hidden
failure remains preserved; its exact internal cause is not retroactively proven.

The first explicit-Expand success had a confound: enumerating102 children added
about17s before input. Matched controls therefore omitted that enumeration and
compared immediate input after one Expand with a closed17s-delay control. Both
delayed controls passed, while one Hidden Expand returned normally but never
reached Expanded within150.075s, before any keys. One-shot Expand is insufficient
and no fixed delay is proposed as a fix. Parent Selection / child SelectionItem
were unavailable on102 disabled DOM proxies. A separate Normal Collapse request
threw `Could not open the process token` while a collapse event was observed;
retain the provider failure without privilege or policy changes.

The acknowledged protocol passed twice per supervisor. Two real cases needed2
and4 nonpersisting Expand requests before an Expanded state was observed. Each
then sent text once, observed the target value, sent Enter once and observed the
same value / Collapsed. Project interaction snapshots completed in approximately
6.3–10.3s under the shared150s limit. Native Win32 focus remained owned in these
successful controls. No failing Win32-focus sample establishes a specific native
focus defect. These observations establish the tool's missing state handshakes;
the intermittent provider/renderer no-response mechanism is still unknown.

## Actual diagnostic matrix

Independent no-NIC QEMU TCG4CPU/6GB overlays; Windows11x64 IoT Enterprise LTSC
Evaluation26100, ordinary synthetic account, preinstalled WebView2
158.0.4370.33/system SQLite3.43.2. Hidden still uses an interactive desktop, not
Session0 or an enterprise-policy representative. Guest clock offset means no
Today/real-clock claim; fixed synthetic December31/January1 dates were used.

| Case | Actual result / boundary |
| --- | --- |
| Original reduced keyboard Normal | FAIL; Project timeout150.405s, worker1/230.073s, outer257.194s |
| Original reduced keyboard Hidden | PASS; worker0/138.397s, outer186.043s |
| UIA Selection capability Normal / Hidden | Unavailable in both; no forced selection. Normal provider Collapse FAIL, Hidden diagnostic completed; not a selection PASS |
| Expand plus original batch with pre-input child diagnostics | PASS Normal/Hidden; timing confounded, not proof of fix |
| Fast one-shot Expand matched controls | Three selections PASS; one Hidden FAIL at Expanded acknowledgement before keys, outer252.099s |
| Closed17s-delay controls | Two PASS; experimental timing controls only |
| Original batch with extra native-focus observation | Two PASS; observer can perturb timing |
| Acknowledged protocol Normal / Hidden, two each | Four PASS; outer103.967/106.189s Normal,100.673/111.381s Hidden; text/Enter once each, no fixed delay |
| Original full Hidden with diagnostic observer | PASS; worker0/964.814s, outer0/984.158s; first/reopened Project, calendars, EmployeeWeek twice, persistence, startup-error and exit |
| Closed record/integrity/payload audit | PASS: all18 reduced copies exactly match source16 tables including timestamps; full fresh16 match expected except fresh recording timestamps; integrityok/FK0/86 payload files matched |
| Earlier instrumentation-scope error | EXCLUDED: new diagnostic received null HWND before keys; later cases interrupted by normal guest shutdown. Preserved locally, not a product failure |

The observed complete Hidden success does not erase the intermittent failed
sample or certify an untested canonical tool revision. The numeric-key/focus
observer remains local; subsequent canonical validation must run without it.

## Frozen package and canonical rerun

Same installed0.1.0x64 source `3595eade23a314704191c89521c1c6e60c60ed21`;
its product tree equals this tool-only branch.

| Identity | SHA256 |
| --- | --- |
| Original NSIS | `CAE2E256DBC54F391EB7BF387EED1AEA6F12A193520EB7AAFCE6DA11FBA3021F` |
| Installed client | `0EC8F67F6C5A154C432616156867C7AD49A7310797F04AFCFD8E7DF2AFD16E74` |
| Installed sidecar | `39B1E073F2E89553C0CC0C5A27718E006146659E44BD2E81C29099F1C1545EE8` |

```powershell
powershell.exe -NoProfile -STA -File scripts/Test-TauriDesktop.ps1 -Executable <frozen-installed-exe> -IncludeEmployeeWeek -IncludeWorkingCalendars -Profile SlowVm -RequireOffline -PreserveSyntheticProfile -DiagnosticLog <local-events> -UiaDiagnosticLog <local-uia-jsonl>
```

Run separately under Normal/Hidden supervision, fresh synthetic profile per run,
unchanged150/60s GUI/exit configuration and existing2700/2800s independent worker/
outer limits. No extra observer or prototype script. Pin the new canonical script
hash, actual worker/watchdog exits and closed all-table/integrity/FK/payload/
process audit. The same final label and all business/persistence assertions stay.

| Final delivery gate | Status at source snapshot |
| --- | --- |
| Focused protocol / full PowerShell5.1 harness | Pending final execution |
| Canonical complete Normal / Hidden, without observer | Pending |
| Canonical closed records/files/processes | Pending |
| Parser/docs/whitespace/staged privacy | Pending |
| Current-head Windows CI | Pending |
| Customer UAT / production | NOT RUN / NOT APPROVED |

Raw exception chains, input traces, screenshots, original designs, DBs and VM
disks remain local. PUBLIC GitHub receives reviewed synthetic/sanitized results.
No product defect is asserted, no business rule/migration is introduced, no
package is replaced, and no Issue is automatically closed, PR merged or Release
published. New install/upgrade/OS-reboot/missing-WebView2 scenarios are NOT RUN in
this tool slice; prior evidence is not a new execution claim.
