# Issue #88 — active SQLite guard evidence

Source snapshot, November 23, 2026. The prior PR #87 was human-merged into main `e6cb19d`; #88 work is isolated. Only acceptance tooling/tests/docs change. Native/CI rows below remain pending until actual final evidence is attached to the associated Draft PR/Issue; this source snapshot is not an aggregate acceptance claim.

## Established failure boundary

The preserved Normal case completed Employee Week UI then failed the old DB/WAL byte comparison. Hidden failed opening the active WAL in `Get-FileHash` with a sharing error, before Employee Week navigation. Both preserved closed profiles subsequently matched all 16 source tables, integrity ok/FK0. Those failures remain failures; they do not establish a product mutation or the cause of the original intermittent 150-second Project selection timeout.

Independent real-file Windows PowerShell 5.1 controls reproduce both limitations: a held SQLite WAL writer prevents the old hash's sharing mode; closing the last connection/checkpoint changes physical DB/WAL state while logical records remain equal. The new tool uses the engine's read-only transaction rather than physical file hashes.

## Executed host controls

| Check | Result / condition |
| --- | --- |
| Existing complete acceptance harness | PASS on Windows PowerShell 5.1, system SQLite 3.53.4; synthetic temporary files |
| Active WAL, checkpoint, last-connection cleanup and VACUUM | PASS: logical digest stable; old hash sharing failure reproduced |
| Genuine insert/update/delete, notes, SQLite storage types, schema and ID sequence | PASS: each changes the fingerprint; exact restoration regains it |
| NULL/empty/integer/real/text/BLOB distinctions, Unicode after NUL, duplicate rows, WITHOUT ROWID and quoted identifiers | PASS |
| Concurrent transaction consistency | PASS: 100 reads with an actual atomic two-table writer; every fingerprint matches a complete committed state |
| Missing/corrupt/exclusively locked file and invalid FK | PASS: explicit failure, no fingerprint or fallback |
| Exclusive SQLite lock | PASS: finite deadline; no silent success |
| Wrapped timeout and unknown error at real verifier boundary | PASS: original chain retained; exit2/TIMEOUT or exit1/FAIL, no fingerprint |
| Matching reader in offline kit | PASS: checked by existing kit/UIA harness |

Commands: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Test-TauriSqliteHarness.ps1` and `... scripts/Test-TauriAcceptanceHarness.ps1`. Actual command output and synthetic raw fixtures/diagnostics remain local. These controls are engineering tests, not native GUI acceptance.

## Frozen native candidate and required reruns

The same installed 0.1.0 x64 package remains frozen. Its source is `3595eade23a314704191c89521c1c6e60c60ed21`; its `src` tree equals the later calendar product commit and this tool-only branch.

| Identity | SHA-256 |
| --- | --- |
| Original NSIS installer | `CAE2E256DBC54F391EB7BF387EED1AEA6F12A193520EB7AAFCE6DA11FBA3021F` |
| Installed client payload | `0EC8F67F6C5A154C432616156867C7AD49A7310797F04AFCFD8E7DF2AFD16E74` |
| Installed sidecar | `39B1E073F2E89553C0CC0C5A27718E006146659E44BD2E81C29099F1C1545EE8` |

Planned environment: fresh independent QEMU no-NIC overlay, ordinary synthetic test account, Windows 11 x64 IoT Enterprise LTSC Evaluation build26100, preinstalled WebView2. Record actual guest SQLite version; host runtime is not evidence of guest compatibility. No missing-WebView2, enterprise-policy, new installer, OS reboot or new Release claim.

| Native / delivery gate | Source-snapshot status |
| --- | --- |
| Matching old guard Normal/Hidden reduced reproductions | Pending; retain actual outcome, including non-reproduction |
| Guest system-SQLite controls | Pending |
| Original full Employee Week / Availability / staffing / working-calendar / reopen / startup-error / close, Normal | Pending |
| Same original full command, Hidden | Pending |
| Additional Employee Week → Availability → staffing → Project navigation | Pending; separate result after original flow |
| Closed integrity/FK, all expected logical records, payload identity and remaining processes | Pending |
| Parser/docs/whitespace/staged privacy and current-head Windows CI | Pending; final links in Draft PR |
| Customer acceptance / production | NOT RUN / NOT APPROVED |

No business/schema migration, forced publication, data-rule relaxation, Save retry, selection assertion change or GUI/exit deadline increase. Raw originals/logs/DBs/VM disks stay local; PUBLIC GitHub receives reviewed synthetic/sanitized results only. Keep #35/#26/#42 open and wait for human merge review. The original #86 timeout remains an independent risk until its matching full rerun actually passes; a tool fix is not proof of a product root cause.
