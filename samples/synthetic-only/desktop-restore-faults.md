# Issue130 native Restore fault harness (synthetic only)

Read the [pre-code plan](../../docs/design/2026-11-27-issue-130-native-faults.md)
and [original source setup](desktop-draft-restore.md) first. This adds test
instrumentation, not production Restore authority or a new business operation.
Schema21, SQL30s, native HTTP60s, renderer150s, authentication, strict receipt
proof and all Pending/Apply=false/Publish=false rules remain unchanged.

## Gates and fixed scope

Create a NEW isolated root through the official stores/source Apply. Its database
must be exactly `<root>/data/rigarus.db`. Never seed a Restore receipt or pending
journal to claim a network timeout. Record the actual database UUID/source ID,
coherent read-only baseline, EXE/sidecar/installer hashes and tested Git revision.

Only after scenario-specific action approval, place a small UTF-8 manifest at
`<root>/data/restore-fault.json` (maximum4096bytes, exactly these six fields):

```json
{
  "format": "rigarus-restore-fault-v1",
  "synthetic_only": true,
  "profile_id": "11111111-1111-4111-8111-111111111111",
  "source_version_id": 1,
  "transport": "after_commit_timeout",
  "archive": "none"
}
```

The UUID above is a placeholder, never a substitute for the actual selected DB.
Only the owned native process receives `RIGARUS_SMOKE_DATA_ROOT=<root>`,
`RIGARUS_DRAFT_RESTORE_TEST=1` AND independent
`RIGARUS_DRAFT_RESTORE_FAULT_TEST=1`. No system/user-global environment change,
cloud endpoint, arbitrary fault path/URL, token logging or security modification.
No new dependency is required. Native passes `--synthetic-restore-faults` only
with the separate Restore gate; the sidecar validates actual DB identity/root
and manifest before readiness. Missing/bad manifest prevents test startup.
Existing Restore opt-in alone never enables faults; default startup ignores the
manifest and keeps production writes closed.

## Bounded transport modes

| Mode | Injected behavior; honest evidence classification |
| --- | --- |
| none | Normal unchanged API; can pair with an archive fault |
| after_commit_timeout | Real authenticated API transaction and sealed Committed receipt first; hold response65s, exceeding unchanged native60s HTTP timeout |
| before_commit_timeout | Hold65s without invoking submit handler, then503; no business write or receipt, so actual receipt lookup is NotFound |
| refresh_once | Real commit response; only first subsequent weekly GET fails503, later reads normal |
| wrong_profile_once | Real commit; corrupt only outgoing profile UUID; authoritative SQLite receipt remains intact for Resolve |

These are controlled ASGI response/delivery faults in a real native process,
not physical network loss. Unit/API tests replace the sleep callable to avoid
65s delays; they prove transaction ordering, not real native elapsed timeout.
Only actual UI execution, elapsed times and local phase evidence can establish
native timeout/refresh behavior. Never prepopulate committed SQL to fake it.

Claims/events are fixed below `data/restore-fault-state`. Atomic exclusive claims
with flush bind the exact original key and canonical payload fingerprint. They
survive restart, so exact Replay is not delayed a second time. Changed keys/body,
corrupt or unreadable claims fail closed. Claims and phase events are local-only;
retain them, never delete/rearm a used scenario. Use a fresh root for each case.
Body2MB/result8MB/state4KB/events64KB budgets are bounded. No SQL or handler
mutation is performed by the injector.

## Archive modes

`none` uses unchanged File::sync_all and exact pending retirement. `write_once`
returns one explicit synthetic write-boundary failure after authoritative receipt
proof under the profile guard; pending remains. `flush_once` uses the existing
archive sync callback to fail once after writing; pending remains. These are
callback-injected native storage errors, not physical disk/ACL/power-loss proof.
Retry requires a new action-time Archive approval and the exact same original
request. Existing matching archive must be read, compared and actually synced
before pending removal. Mismatch/oversize/IO error cannot release recovery.

## Execution and evidence

Follow the current [A/B/C test authorization](../../docs/10-CLIENT-DECISIONS.md#development-and-synthetic-test-authorization-november272026):
verified isolated synthetic flows are preauthorized,including original-key recovery
and recoverable faults;do not interrupt the user for every low-risk step. Any
platform/OS/tool action-time requirement remains mandatory. Declined action stops
immediately;do not change tool/API path to bypass it. Record the exact scope and
approval basis;never replace an uncertain UUID or infer production authority.

Snapshot actual logical records in one read-only SQLite BEGIN before/after:
profile, typed full/half IDs, revisions, original/restore versions, immutable
history, receipts, exact pending/archive, integrity/FK. For a single two-addition
inverse expect two Cancelled rev2, one new restore version/receipt, unrelated
FullDay3 and every legacy AM/PM record unchanged. Rejected may add a sealed
receipt but no restore version/business edits. Resolve/Archive/read refresh must
not grow business revisions or recovery versions. Never use WAL byte hashes as
the sole assertion. Reopen native process, inspect Retained Review/original ID,
then verify complete receipt before any retirement.

Keep original sources, DBs, journals, screenshots, logs and backups local. Publish
only sanitized Markdown/code/synthetic tests. D01–D18 must distinguish API/unit,
Rust contract, injected versus seeded state, actual native interaction and granted
operations. Incomplete compound cases remain NOT RUN. End with a flag-free native
launch to test the closed gate; do not claim it from a unit test alone. Licensed
offline VM install/upgrade/WebView2/OS reboot remain BLOCKED until available.
