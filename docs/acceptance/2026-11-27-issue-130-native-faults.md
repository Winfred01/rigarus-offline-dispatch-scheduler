# Issue130 second native fault round — evidence and pending authorizations

This record does **not** claim the entire native fault matrix passed. Three
separate native scenarios have new evidence: real committed-response timeout,
no-handler timeout/NotFound/exact original Replay, and Committed plus one failed
weekly read followed by read-only recovery. Specific operation approvals and
remaining automatic approval blocks are detailed below. Prior-round approvals
identify another database/request and are not reused.
The prior [normal-loop record](2026-11-27-issue-130-native-followup.md) remains
historical evidence; its normal path is neither reimplemented nor mislabeled as
timeout/Rejected/storage coverage.

## Fresh sources, isolation and change

Fetched main `1923b564d95c8bb790ad00c82864f5b6fb52c6fe`;133 merged/closed.
Main Windows CI [46083989992](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/46083989992)
was freshly confirmed success, all3 jobs. New independent branch
`codex/issue-130-native-faults`, not reopened133. Root README/language/original
local work is preserved. Public repository receives only sanitized code/tests/MD.

The [pre-code Design Compliance Checklist and Implementation Plan](../design/2026-11-27-issue-130-native-faults.md)
was committed as `f9f9de1` before product instrumentation. Source inventory,
Git revisions, UTCmtime and observed times remain local. Fresh applicable
AGENTS/template,00/09/02/03/05/10,130 design/implementation/native follow-up,
synthetic sample,130/20/99 and current backend/native/React tests inspected.
Original November24 DOCX L10/L12/L13 text and image62/64/65 were re-extracted
and viewed; SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`.
Original DOCX/images/raw diagnostics are not committed.

No demonstrated scheduling/Restore domain defect has been found. Existing
logic tests cover the edge contracts but there was no bounded test mechanism
to produce the required native transport outcomes. Instrumentation commit
`6fb719326a04a89d5ba230e5829fa9442fb21f7c` adds a separately default-closed,
exact-root/profile/source, fixed local manifest and durable one-shot claims.
The real API authenticates first and supplies real SQL receipts; only selected
delivery/read/storage boundaries are injected. No new writer, business rule,
database migration, auth relaxation, dependency or deadline increase.

See [reproducible gated harness](../../samples/synthetic-only/desktop-restore-faults.md)
for exact modes, formats, bounds and honest classification. Source-side unit/API
tests replace65s sleep, so those tests cannot claim an actual GUI60s timeout.
Archive write/flush callbacks are synthetic boundary failures, not real physical
disk/power-loss proof. No ACL, network, licensing or Windows security change.

## Build and environment identity

Fresh Windows11Pro x64 host:25H2,10.0.26200.9974 (CIM+registry UBR). Connected
IPv4 Internet. Actual Rigarus WebView2 child version158.0.4370.45 was read by
owned-parent PID; an earlier unfiltered157 child belonged to another process and
is not used as Rigarus evidence. Visible normal native windows, not Hidden.
This is not an offline or clean VM. Existing expired Evaluation VM cannot be used
as a qualified replacement and its licensing is not bypassed.

All new isolated build artifacts are product version0.1.0, not a new Release or
modification of the previous installer. Release/NSIS build passed; the NSIS bundle
patch/restoration changes EXE bytes after the earlier direct Cargo build. Use the
final standalone hash actually recorded at native launch below. The temporary
mid-NSIS EXE hash was captured too early and is not the tested artifact. No old
installer was modified or installed. Installer payload and standalone need not
be byte-identical.

| Artifact | SHA256 |
| --- | --- |
| Actually tested final standalone Release EXE | `a677d647a1f29e795f86375ab7842952870aca09916927bd8807211b9bcf6a02` |
| Matching adjacent Rigarus.Sidecar.exe | `adba29a207de67a48d817044c3238deaeb9da643f4f858e18c1eb0f4d47b38e3` |
| Independent x64 NSIS installer (not installed) | `267cb65bf5993c6a4a5cdc1a9d7e9953762a5febf355811a7c10abb69153d378` |

## Prepared scenario and actual operation status

Local-only `.local/restore-fault-evidence/fault-timeout-01/data/rigarus.db`, profile
`9bd4a7d5-c4d9-422b-bfc3-0f852edf6b33`, source DraftVersion1. Official stores
and source Apply created FullDay1/2 rev1, unrelated FullDay3 with actual synthetic
Employee1, LegacyHalfDay1PM/2AM/3PM (distinct types/equal integer IDs), separate
Projects/Crews/notes. No actual Rig recorded; none invented. Setup never invoked
Restore, seeded a Restore receipt or injected pending. Exact synthetic identity
is disposable, not personal/account data.

Coherent read-only BEGIN baseline digest
`6e83fff60683219338e1f1af8bd8c585dd3be90c6127a730ca22aab66b371308`;
integrity ok,FK violations0; day3/legacy3/history3/source versions1/restore
versions0/restore receipts0; no recovery journal/archive at baseline. Subsequent
actual coherent snapshots and full table comparisons are detailed below.

| Actual protected operation | Action-time approval/result |
| --- | --- |
| Fault activation and test launch | Exact timeout profile/mode approved; same separate explicit approvals for NotFound and refresh profiles |
| Confirm | Specific first-profile double-click approval; user also allowed subsequent same-scope synthetic Confirm, referenced explicitly in each later approved scenario; three actual native commits/attempts below |
| Resolve | First timeout request specifically approved; NotFound Resolve initially rejected by automatic review,stopped,then explicitly approved for its actual UUID before execution |
| Replay | NotFound original UUID/payload specifically approved only after real NotFound; actual native Replay committed once |
| Archive | First timeout request specifically approved,verified and archived; NotFound request separately approved,verified and archived; refresh request-specific Archive approval pending |

No operation is treated as approved by elapsed waiting. No bypass, alternate API
write, pending deletion or replacement request. Automatic review did not accept
the user's broad subsequent-action permission for NotFound Resolve; its first
attempt was rejected and stopped. After exact-key user approval,Resolve returned
NotFound. Automatic review later separately rejected closing the refresh process
and starting Rejected/flush-injection process without new action-specific
confirmation. Neither action executed; exact PID/profile permission questions
were submitted. These are approval blocks,not product failures. No alternate
execution channel was used. Independent regression/documentation continues.

## Actual native fault evidence

All profiles use original DraftVersion1,typed day IDs1/2 plus unrelated day3 and
legacy IDs1/2/3. Per-launch flags only; Publish/production Restore stay false.
New artifacts have product/test source `6fb7193`; tested checkout `8f15744` adds
documentation only. The final EXE/sidecar above were unchanged through the runs.

| Scenario/profile | Original request | Actual result |
| --- | --- | --- |
| committed response timeout /9bd4a7d5-c4d9-422b-bfc3-0f852edf6b33 | 638ea0ac-6bed-4282-bcf3-43b4621cdcac | Real transaction committed before65s response hold; native Unknown,normal close/reopen,Retained Review,verified Committed Resolve,archive+flush/exact pending retirement |
| no-handler timeout /b93db8cd-8f3c-42da-9edc-f3c504f9492b | c194d38a-97dd-4e8a-b593-1efbae2c0aa2 | Native Unknown,zero SQL changes; close/reopen;actual Resolve NotFound preserves pending;authorized identical Replay commits once;verified archive retires exact pending |
| post-commit read failure /6b5f2619-0b10-4417-9ec6-82937f24dbf6 | 98c6f8fd-c9cc-4912-a5fa-f03d576bb361 | Real Committed version1 plus single503 weekly GET;UI retains Committed,explains read error;read-only Retry succeeds;no extra revision/version/receipt;pending retained awaiting archive approval |
| Stale/flush /dd808247-e77f-4c55-befa-b75bdac88755 | None yet | Official source fixture prepared;no later-note edit/Restore/journal;new specific fault-process launch blocked by approval review and awaiting user answer |

### Committed-response timeout

Actual Confirm double-click starts00:09:19.733Z. Native journal is flushed before
dispatch; actual request phase00:09:19.844Z,real atomic commit00:09:19.888Z.
Read-only snapshot DURING the hold already has one restore version/receipt,two
Cancelled rev2/history+2 and full pending. UI was still Submitting at54.1s,
then Unknown at76.9s; server released the real200 Committed response only after
65.019s. The native HTTP timeout remains60s. This is controlled response delay
causing real native timeout,not physical network outage or seeded SQL success.
No claim that UI sampling measured timeout at precisely60.000s.

After normal real process exit/restart (old PID gone),UI showed same UUID,
Retained Review/recorded acknowledgements,not Current. Separately approved
Resolve verified the authoritative original Committed version1 and refreshed
saved data. Separately approved Archive reread/proved receipt,flushed matching
archive and removed only pending. Archive SHA256
`81f4a54d1454c94d8b53c2ec3969ada282d99f7f2df47118bccef075af59e41c`.

Every table was compared: exactly DayDraftAssignments,DayDraftChanges,
DraftRestoreVersions,DraftRestoreReceipts and sqlite_sequence changed from
baseline. Stable day1/2 business contents except new status/revision/timestamp
preserved;day3,all legacy rows/history,source JSON,staff and unrelated tables equal.
Logical digest after commit,timeout,Resolve and Archive stays
`ba3b93c61c6866ac49ed3d0ef14da9f7201fc08a95b219745a2ecab3a5cc65da`.

### No-handler timeout and real Replay

Actual dispatch00:18:35.597Z;request received00:18:35.695Z;handler not invoked,
65.010s hold. Native Unknown observed67.0s. Before/during/after timeout and
real NotFound/reopen all logical tables equal baseline digest
`b4c4cba849853184065f46709572a6c2be9dbed1aa94d8ba7d3f4f1291450e83`;
pending complete envelope identical,including original UUID/body/source/plan/
all4 acknowledged warning IDs. NotFound did not retire it or create another key.

After specific original-key Replay approval,one real native click committed
version1;durable one-shot delivery claim survived restart and did not rearm.
Full independent receipt review matched profile/key/source,canonical namespaced
payload SHA,plan/source/warning hashes and exact proposed inverse/observations.
History3→5,restore versions0→1,receipts0→1;two Cancelled rev2;all unrelated/legacy
data equal. After Replay and authorized Archive digest stays
`d8d3bb2ac195f4cb2d356d67ba8fd240fa61776e7a17104660e006b2e7bc7443`.
Archive SHA256 `6a522fcbb75493b83c7c73e162cdd0f82e585f7277d2368564b3aadba7604599`.

### Committed plus failed weekly read

Real commit phase00:27:07.821Z,only first subsequent weekly read deliberately
503 at00:27:07.844Z. UI explicitly displayed Committed/DraftRestoreVersion1 and
"weekly refresh failed;retry reads only". Actual read-only Retry then showed
"saved weekly data refreshed";every table AND pending envelope equal across
failure/retry,digest
`bcb64db5d201770e8320807057bd81987394ec81328a992ff2a072db468bbdef`.
One restore version/receipt/history+2;original source and all unrelated/legacy
rows/history/member data retained. No new Restore request or repeated write.
Current pending remains;Archive/close require the outstanding specific approvals.

Some native input attempts hit stale UIA geometry after scroll and did not
dispatch (no journal/claim/SQL change). They are retained as local input-tool
diagnostics,not passing submit/fault evidence or product failures. Fresh actual
screenshots and current bounds were rechecked before the real dispatches. A
premature read-failure verifier correctly rejected the no-dispatch snapshot;
the genuine post-commit failure has separate immutable evidence filenames.

All actual snapshots integrity=ok,FK violations0;no physical row deletion,
revision rewind,half-day conversion or fabricated Rig approval. Result flags
Pending/Apply=false/Publish=false. Raw UI/state/claims/logs/DBs/archives remain
local. Rejected/storage/concurrency/native malformed cases remain separately
unexecuted unless newer evidence is appended below.

## Fresh checks (record creation)

PASS: locked uv/npm/.NET restores;9 new mechanism/API tests; frontend102;
Rust26 including existing proof/guard/namespace/flush tests and new archive claim;
historical.NET35; packaged sidecar18 repeated checks; TypeScript/Vite build;
Release+matching sidecar+NSIS; Python Ruff check/format; frontend format;
.NET whitespace check under normal developer-test permissions; staged privacy;
document links/UTF-8/fences. Final full Python687 passed333.107s,900s limit;
total850=687+102+26+35 distinct suite cases. First Python collection had686
because the last authentication test was added while it ran;final complete
collection was rerun,not counted twice. Packaged18 are repeated checks.
[PR134 Windows CI155](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/46085912665)
passed all3 jobs at `8f1574435ad289eb659592daae846e51f947df4a`,including
artifact assembly/upload. No CI success is an offline installation pass.

The initial restricted Python attempt did not return promptly and was stopped.
Restricted .NET format encountered named-pipe AccessDenied; the same read-only
check passed with approved normal developer-test permissions. Neither is a
product/native fault test. No test assertion/gate/deadline was weakened.

## D01–D18 updated strict native matrix

This matrix concerns the NEW artifact/fault round. Historical normal passes are
described explicitly and are not new fault evidence. Compound cases with unrun
required native subcases stay NOT RUN; API/Rust passes do not promote them.

| ID | Status | Actual evidence / remaining native scope |
| --- | --- | --- |
| D01 | NOT RUN | Prior two-addition inverse; new5→8/5→2 native variants not run |
| D02 | NOT RUN | Prior four-warning/scope pass retained; fresh mechanism rejects missing acknowledgements; new GUI not run |
| D03 | NOT RUN | Backend Stale/blocker tests; new real native conflict not run |
| D04 | NOT RUN | Prior Escape equality/focus pass retained; new build not exercised |
| D05 | NOT RUN | Actual authorized Confirm double-click produces one original key/version/receipt;real close AFTER timeout PASS;close DURING send not run |
| D06 | PASS | Real commit,65s response delay/native timeout,real process reopen,same retained UUID and authoritative Resolve;one version/history pair |
| D07 | NOT RUN | Native no-handler timeout,real NotFound/pending equality,exact original Replay/Archive PASS;separate service-error variant not run |
| D08 | NOT RUN | Strict Rust/frontend proof + outgoing-profile API corruption tests; new native malformed-wire matrix not run |
| D09 | NOT RUN | Rust same UUID/namespaces/OS guard/interlock PASS; two native process contention not run |
| D10 | NOT RUN | Rust pending preservation/flush/retry and durable one-shot archive claim PASS; native journal/storage faults not run |
| D11 | NOT RUN | New actual native Committed/complete proof/Archive PASS in two profiles;sealed Rejected/flush variant awaiting specific launch approval |
| D12 | NOT RUN | Actual native Committed+one503,explicit read retry succeeds with unchanged DB/pending PASS;both-board/Locate follow-through not yet run |
| D13 | NOT RUN | Synthetic same-integer types preserved in baseline; prior normal mixed-view/Locate pass retained; new artifact/Rig variant not run |
| D14 | NOT RUN | No new narrow/long-data/keyboard/Narrator execution |
| D15 | NOT RUN | Automated default-closed and ignored-manifest tests PASS; new flag-free native gate check not run |
| D16 | PASS | Final850 distinct local cases+18 packaged repeats,locked formats/build/NSIS/privacy/docs;product/test-head CI155 all3 PASS;later evidence-only docs must be checked separately |
| D17 | NOT RUN | Exact-artifact native fault/close/reopen/Resolve/Replay/Archive and full logical proof PASS above;post-archive same-profile native reopen/default-gate follow-through pending |
| D18 | BLOCKED | No qualified licensed disconnected VM: install/upgrade/WebView2/OS reboot not run |

P0 native scenarios have partial passing evidence above;P1 storage/guard/malformed
and P2 scope remain incomplete. No current-round product FAIL is demonstrated;
approval refusals are explicit blocks,not product failures. No complete fault
acceptance claim. Default production Restore/Publish remain closed;
customer Demo/UAT, deployment and delivery remain unapproved. Issues stay open,
Draft PR awaits human review, no merge/Release/deployment. Next priority is the
outstanding exact-operation approvals and sealed Rejected/archive-flush case,
then remaining P1 concurrency/storage/malformed and strict D12/D13 follow-through.
