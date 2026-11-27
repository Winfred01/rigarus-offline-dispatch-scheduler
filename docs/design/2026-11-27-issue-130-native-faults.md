# Issue130 second native fault round — pre-code checklist and plan

Fresh main1923b564d95c8bb790ad00c82864f5b6fb52c6fe, human-merged133/closed;
new independent codex/issue-130-native-faults worktree. Public repository; root
README/language/local original changes preserved. Main CI46083989992 was running
at inspection. Prior normal Confirm/reopen/Resolve/Archive evidence is reused as
history, never reimplemented or relabeled as fault coverage.

## Design Compliance Checklist

Fresh AGENTS/template d3b9bea; current affected00/09/02/03/05 chapters1bf8341,
decisions10 at3be3cd4; original130 designf3a68da, implementation1bf8341,
native follow-upd4c3f1f and synthetic sample1bf8341. Full file revisions/checkout
UTCmtime/read times are local. Fresh130/20/99, latest acceptance comments,
merged133, existing Restore domain/API, native transport/journal/React validators
and tests inspected. No claim that every historical subsection was reread.

Local November24 original UI DOCX re-extracted/viewed: SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c;
mtime2026-11-24T23:15:38.711423Z; L10 paragraphs54–58/image62, L12 paragraphs64–68/
image64, L13 paragraphs69–73/image65 explanation and original images. Paragraphs
are not pages. Inspection/compare/confirm flow applies; no new Published/full-week
restore or half-day editing authority follows from prototype examples.

| Requirement | Current implementation / needed evidence |
| --- | --- |
| D06/D07 timeout,original key,NotFound/replay | Existing strict recovery; missing native controlled transport faults |
| D11 rejected receipt/archive | Existing sealed backend rejection; native stale-after-review and storage failures |
| D12 Committed plus failed read | Existing pure test; actual one failed post-commit weekly GET needed |
| D05/D09 double-click/close/guard | Existing lock/guard; bounded held request enables real native observations |
| D08/D10 malformed proof/storage | Existing native/unit injection; controlled native boundary tests needed |
| D01/D03/D13–15 | Preserve mixed kinds/exact IDs and default gates; P2 after P0/P1 |
| D18/production | Qualified licensed VM unavailable; UAT/production/Publish remain unapproved |

## Implementation Plan — before product code changes

No demonstrated domain defect yet. Add minimal engineering-only instrumentation,
not a new Restore feature or writer. No schema/API-contract/business-rule change.
No new dependencies, cloud calls, authentication relaxation or product UI change.

1. `restore_faults.py`: pure ASGI transport around the real API, inside existing
   authentication. Require Restore synthetic opt-in, extra fault opt-in, exact
   smoke-root data/rigarus.db, canonical database UUID/source and a bounded fixed
   `data/restore-fault.json` manifest. Manifest format/version, synthetic marker,
   profile/source and mode enums are strict; unknown/malformed/out-of-root state
   fails closed. No HTTP fault-management endpoint or arbitrary path forwarding.
2. Fixed65s delays exceed unchanged60s native HTTP timeout and remain bounded.
   One mode holds a REAL Committed response after the real atomic transaction;
   another holds before invoking the handler and then returns unavailable without
   committing, so actual receipt is NotFound. Native original-key Replay is real
   backend execution, never fabricated success. One mode fails just the first
   post-commit weekly GET; one corrupts only the outgoing receipt profile, keeping
   authoritative SQLite receipt unchanged for subsequent verified Resolve.
3. Fault claims/events live only below the exact synthetic data directory. Atomic
   create+flush binds one original UUID/body and survives process restart; no
   rearming by reopen. Bound files/response sizes; no tokens/full headers/raw user
   documents in events. Log clear phases/elapsed time so seeded state, injected
   transport faults, native HTTP timeout and process exits remain distinct.
4. `sidecar.py`/Rust `sidecar.rs` add the separately default-closed startup flag;
   no fault enabled by the existing Restore flag alone. Keep all existing routes,
   validation and SQL30s/HTTP60s/renderer150s. Native archive instrumentation may
   inject one write/flush error only after complete receipt verification, under
   the shared guard and exact original profile/source. Existing tests' injection
   callback is reused; default storage code remains File::sync_all. No ACL, disk,
   Windows security or approval configuration changes.
5. Add focused mechanism/gate/real-contract tests before exercising native faults;
   compare real SQLite records/receipts/history under each API test. If a product
   defect is actually found, first add a stable regression and update this plan
   with root cause before a minimal fix. Do not weaken assertions to pass.
6. Build matched Release/sidecar/NSIS with locked restores. Prepare NEW synthetic
   cases via official stores/source Apply, never pre-submit Restore or inject
   committed/pending state to fake a network result. For each actual fault mode
   and protected Confirm/Resolve/Replay/Archive/process operation, get the required
   action-time approval naming root/profile/effect. Rejection stops that action;
   no tool/API/channel workaround. Independent checks continue.
7. P0 first: true native response timeout after commit; pre-handler timeout plus
   real NotFound and authorized same-key replay; real stale Rejected and verified
   archive; committed plus one failed weekly read and read-only recovery.
   Then P1 guarded concurrency/double click/in-flight close and native storage/
   malformed boundaries as authorized; P2 only after P0/P1 completed or blocked.
8. Coherent query-only logical snapshots/integrity/FK, exact profile/key/version/
   revisions/history and native pending/archive before/after. Preserve unrelated
   Projects, original versions, notes/workers/Rig and all LegacyHalfDay occupancy.
   Always Pending/Apply=false/Publish=false. End with flag-free native startup.
9. Fresh full Python/frontend/Rust/historical.NET/packaged-sidecar, locked formats,
   Windows Release/NSIS, staged privacy/docs checks and exact-head CI. Update
   actual D01–D18 by layer; compound native cases with unrun subcases stay NOT RUN.
   One new Draft PR and130/20/99 progress; no auto merge/closure/Release/deployment.

Risks: test-only transport must not affect normal auth/lifespan or buffer unbounded
data; a response fault must never rewrite a sealed receipt. Claims survive restart,
and storage errors retain original recovery evidence. Simulated sync callbacks
are native fault injection, not proof of real power-loss durability. Main source
records remain untouched except separately approved synthetic fixture changes.
Original DOCX/images/DBs/journals/backups/raw diagnostics remain local. Qualified
offline VM and customer/production gates remain separate and BLOCKED/unapproved.
