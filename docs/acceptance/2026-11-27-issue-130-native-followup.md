# Issue130 native synthetic Restore follow-up, November27,2026

**Normal native submission → process reopen → original receipt Resolve → durable
Archive → another process reopen: PASS.** Each protected action received its own
explicit user confirmation immediately before execution. No native approval was
rejected in this run. This does not complete every fault case, disconnected VM,
customer UAT, production Restore or Publish.

## Fresh baseline, sources and scope

Fetched main `11beff665de61c3e6b199f823eb1d58ea4ecdbe7`, human-merged132/closed.
Product commit `1bf8341e267969e88fe272e601cc0a5d8777d87c` and main have exactly
the same Git tree `54f28cbf28fb4f24e0d61501ffbcea214004746c`. The unchanged
existing132 Release/sidecar were reused for native testing after fresh hash/source
verification; newly built binaries are separate regression artifacts, not silently
substituted during testing. New isolated branch `codex/issue-130-native-acceptance`
does not append to, reopen or duplicate the merged product PR132.

Fresh Design-First source versions and original UI L10/L12/L13 are in the
[pre-test checklist/plan](../design/2026-11-27-issue-130-native-acceptance.md).
AGENTS/template d3b9bea; current affected chapters of00/09/02/03/05 at1bf8341,
decisions10 at3be3cd4; original130 designf3a68da, implementation/acceptance/sample
at1bf8341. Checkout UTCmtime/read times/full revisions are local. Original
November24 DOCX text and image62/64/65 were re-extracted and inspected; SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`.
Paragraph locators54–58/64–68/69–73 are not page numbers. Original diagrams and
all raw evidence remain local; only this sanitized Markdown is published.

No demonstrated product defect, source-code change, business-rule change or
migration was needed. Schema21, all gates and original historical records remain
unchanged. The prior [implementation-run record](2026-11-27-issue-130-desktop-restore.md)
is historical; its then-blocked native normal path is superseded by this run,
not retrospectively marked passed. Original prototypes do not authorize Published
or whole-week rollback, legal/resource assumptions, or new half-day entry.

## Exact test environment and binary identity

Windows11Pro x64,25H2, **10.0.26200.9974**; Win32 OS caption independently read.
Legacy registry ProductName still says Windows10Pro; it was not used to mislabel
the OS. Actual WebView2 child **158.0.4370.45**. Networking was connected; normal
visible native Tauri windows on the authorized development test host, not Hidden,
VM, developer-tools-free installation or disconnected acceptance. No security,
approval, licensing or host restart changes.

All tested artifacts retain product version0.1.0; no old installer was modified.

| Actually inspected artifact | SHA256 |
| --- | --- |
| Native Release EXE from132, including NSIS bundle patch | `5967457f41aa21e78e00ee4cf54123fdc5e19a21293e3282d68530107fb4814f` |
| Its adjacent matching Rigarus.Sidecar.exe | `5f8bbe174783965e2c6355542d1bb399d8d018e6190d415bc4df47ba23bc6ec3` |
| Corresponding existing, uninstalled NSIS installer | `157632d95a25d849d3fcfca7822f64cd883039ddcfce376e632c331b93c1c786` |

EXE/sidecar hashes were rechecked unchanged after native tests. A separate fresh
main-equivalent NSIS regression build passed301.06MiB, SHA256
`42fb04a76c80fccfc05eba6082e85050398e88d2f5d41a29b5fab815f2972e4e`;
it was not installed or substituted into the above run. Build timestamps/paths
and bundle patching can change binary hashes; source equivalence does not mean
different builds are byte-identical. No new version/Release was published.

## Synthetic setup and independent authorizations

Fresh local root `confirm-01`, database exactly `data/rigarus.db`, database
identity `fc72b335-6810-452f-b94f-6c8b52e38a90`. Existing official source Apply
preparation/transaction and stores created original DraftVersion1 with two new
FullDayDrafts1/2 on November23/24, Crew1, WorkItem1, Project1 and a synthetic
two-day note. No Restore submission or pending injection was used for setup.

An unrelated Project2 has FullDayDraft3/Crew3/November23, a saved actual synthetic
Employee1 and distinct note. LegacyHalfDay1PM/2AM/3PM belong to Project2/Crew2
on November23/24/25. Thus both cancelled1 versus active legacy1 and active day3
versus active legacy3 have equal integers and distinct types. No actual Rig is
recorded in this fixture; no Rig is invented. Positive recorded-Rig native display
remains a separate gap; automated Rig hard-conflict/revalidation tests were rerun.

Only the owned native process received `RIGARUS_SMOKE_DATA_ROOT` and
`RIGARUS_DRAFT_RESTORE_TEST=1`; no Apply/editor test flag. Actual authenticated
gate status caused the synthetic preparation message; production gate remained
false. Default startup was tested again with every writer test flag absent.

| Protected action | Separate action-time approval | Actual operation/result |
| --- | --- | --- |
| Confirm | User explicitly answered “批准本次 Confirm”, naming this profile/original1/targets1,2 | One click only; two Cancelled rev2 rows, recovery version1 and receipt committed |
| Resolve | User explicitly answered “批准本次 Resolve”, naming original request below; GET-only scope | After real process close/reopen, queried and fully validated the same committed result; no replay/archive/retirement |
| Archive | User explicitly answered “批准本次 Archive”, naming exact request/recovery1 and pending removal | Native reread/verification, matching archive write+flush, exact pending retirement; archive persisted across another process restart |
| Replay | Not requested or authorized for execution | NOT RUN; normal committed result required no replay; no alternate key/API workaround |

Original Restore request `88ae121a-bfcc-4f8a-9571-466e3b891d50`, source
DraftVersion1, DraftRestoreVersion1, plan fingerprint
`4897fb4c389612ec19b717e43521ef02279318396a3f5d4be158caeb74ce4e3e`.
These are disposable synthetic identifiers, not personnel/account information.
The native Committed receipt records2026-11-27; its exact UTC timestamp remains
in local receipt evidence. Approval messages were not uploaded as raw transcripts.

## Actual native steps and observations

1. Launch matching Release/sidecar with the exact isolated root. Job Schedule
   shows target1/2 plus unrelated day3 and legacy1/2/3. Open Restore, original1,
   prepare exact inverse; inspect original Before(empty)/After(two rows), reviewed
   current rev1 and inverse Cancelled rev2. Dates, typed IDs, Project/WorkItem/Crew,
   notes and missing actual staff remain explicit. Four Pending warnings start
   unchecked; submit disabled. Escape cancels and returns visible focus to opener.
   Coherent full logical snapshot, history, versions and receipts unchanged.
2. Reopen/reprepare; warnings again0/4. Independently check lock policy,
   dependency policy, unconfirmed-Draft-only and no historical resource approval
   inheritance, then the separate exact inverse scope. Screenshots show1/4,2/4,
   3/4 and4/4; submit remains disabled without separate scope. After the explicit
   Confirm approval, click once. While pending/submitted, controls freeze; final
   UI states Committed/recovery1 and successful weekly read refresh, with
   Validation pending / Apply=false / Publish=false. No double-click was sent.
3. Verify SQLite logically: stable target IDs1/2 now Cancelled revision2, same
   WorkItem/Crew/dates/notes; original history retained, exactly two new history
   rows. Day3 and every other pre-existing table except expected inverse/audit/
   sequence changes remain identical. One immutable source version remains,
   exactly one recovery version and one independent receipt exist. Pending retains
   operation=DraftRestore, exact source/review/request and all4 warning IDs.
4. Close the real process, reopen same unchanged EXE/root, open Restore. Exact
   original UUID remains; UI says Retained review/not a current database read,
   recorded acknowledgements, not fresh Current. No automatic replay occurs.
   After separate Resolve approval, click once. Complete original Committed
   receipt passes native/renderer validation and original recovery1 is shown.
   Complete logical snapshot and pending remain unchanged by Resolve.
5. Independently compare receipt against pending and immutable SQLite audit:
   operation/profile/key/original source, exact seven-field confirmation,
   canonical source/plan/warning digests, warning set, typed exact inverse/revisions,
   observations and Pending/false flags match. PayloadSha uses the backend's
   **namespaced `(format, canonical-request-string)` digest**, not a plain object
   digest. The local verifier initially used the latter incorrectly; corrected
   the verifier to the inspected contract, without relaxing checks or product code.
6. After separate Archive approval, click once. UI confirms verified receipt
   archived/flushed and exact pending retired. Read-only inspection confirms
   one `restore-receipt-<original UUID>.json` with the exact SQLite receipt,
   no pending, and no database change. Close/reopen again: same archive remains,
   no new pending/key/version/history. Archive SHA256
   `f9db908184cf594414b58f608a671e50c80a6f79308497ff6b8e3cf59704bbe7`.
7. Post-restore Job Schedule/Crew Board retain full-day versus AM/PM, unrelated
   Projects/Crews and recorded staffing. Typed Locate FullDayDraft3 highlights
   November23 full-day/Crew3; LegacyHalfDay3 highlights November25PM/Crew2.
   Same integer does not alias. Read-only daily editor loads cancelled1/rev2,
   original note and both immutable rev1 Draft / rev2 Cancelled history entries.
8. Final process starts with all three writer test flags absent. Original1 is a
   valid input: Inspect original enabled, Prepare exact inverse disabled, actual
   status says production Restore closed. Child sidecar command metadata confirms
   no synthetic Restore/Apply/editor flags; token/complete command line never
   exposed. Publish disabled. Close normally; no residual owned app/sidecar remains.

## Coherent SQLite comparison

All snapshots use one read-only BEGIN transaction, logical records/schema/history,
integrity_check and foreign_key_check. No raw WAL hash is used as an assertion.

| Point | Logical digest / invariant |
| --- | --- |
| Before native / after pre-submit Escape | `682d3a7fa9bbf57fa57438b9d5b0ccbd959ab02b675d7fc245da927753e59c70` identical |
| After Confirm / Resolve / Archive / archive-reopen / final close | `8e1e5aceb5fbefbbd9fc6a66af76701762598a67a2659bce52dd9fbaf879fbf0` identical after the one expected commit |
| Every snapshot | integrity=ok;FK violations0; source versions1; day records3; legacy records3 |
| One allowed transaction | history3→5,restore versions0→1,receipts0→1; no repeated history/version |

Exactly DayDraftAssignments,DayDraftChanges,DraftRestoreVersions,
DraftRestoreReceipts and their sqlite_sequence metadata changed from baseline.
The unrelated day row, original source JSON, legacy rows/history, saved members,
other resources and all other pre-existing tables were compared equal. No rows
were physically removed or revision rewound. No legacy capacity was released.

## Fresh regression and build checks

New isolated main-equivalent worktree, locked dependencies and current source;
results below were executed again, not copied from132's report.

| Check | Result / local evidence label |
| --- | --- |
| uv sync locked bundle; Ruff check/format | PASS;140 formatted files;locked-backend/ruff logs |
| Full Python unittest | PASS678,0 skips,317.059s;backend-full.log/result |
| npm ci,Prettier,TypeScript/Vite | PASS; sandbox npm exit-handler failure resolved by same locked restore in authorized local test context |
| Full frontend | PASS102,0 skips;frontend-tests.log |
| Windows Release and Rust1.95 locked tests | PASS25,0 ignored,3.55s;real Python→native contract included;cargo-build.log |
| .NET locked restore,whitespace,Release build/test | PASS35,0 skips;dotnet logs |
| Fresh packaged sidecar | PASS18,31.913s;packaged-tests.log |
| Fresh NSIS build | PASS301.06MiB;separate hash above;not installed |
| Staged privacy,whitespace,document links | PASS419 indexed paths,whitespace,3 Markdown files/6 local links |
| Merged-main CI46078749110 | Tauri PASS,.NET/Harness PASS,Python exceeded10m budget after suite PASS570.382s;packaging cancelled;not3/3 |
| New evidence-PR CI | Pending new PR;report final exact-head outcome in PR,not a native/VM substitute |

Distinct suites total840; packaged18 repeat another execution mode. Safe automated
fault tests cover Stale/Blocked driver/people/Rig/calendar/legacy constraints,
missing/altered warning sets, SQL/audit rollback, NotFound/replay/reuse, wrong
identity/malformed complete receipts, namespaced same-key journals, exclusive OS
guard, archive/write/flush faults and committed-plus-failed-read refresh. Their
passes are not native fault-injection passes. No assertion/runtime deadline/gate weakened.

GitHub backend check140772531969 explicitly annotated exceeding the maximum
execution time10m0s. After the [plan update](../design/2026-11-27-issue-130-native-acceptance.md),
only the backend CI job budget changes10→15 minutes, still bounded, to cover
the full570.382s suite plus packaging/tests/setup. Test-level SQL/HTTP/native
deadlines and all required commands/assertions remain unchanged. The new PR CI
must validate this minimal pipeline fix; the original main run stays cancelled.

## D01–D18 native matrix (strict full-case status)

For compound original cases, NOT RUN means some required native fault/edge
subcases remain unexecuted even when the stated normal subcase passed. The normal
end-to-end success above is independent and must not mark all18 cases green.

| ID | Native full-case status | Actual new evidence / remaining subcases |
| --- | --- | --- |
| D01 | NOT RUN | PASS two-addition inverse and complete views; native5→8/5→2 variants remain |
| D02 | PASS | Four independent unchecked warnings, incremental acknowledgement and separate scope gate; malformed sets covered automatically |
| D03 | NOT RUN | Fresh automated Stale/known blocker/profile/kind tests PASS; no new native blocker fault injection |
| D04 | PASS | Pre-submit Escape logical equality and visible opener focus return |
| D05 | NOT RUN | Real single Confirm PASS,one version/history pair and disabled repeat control; double-click/in-flight close not performed or authorized by single-click approval |
| D06 | NOT RUN | Real close/reopen/same UUID/Resolve PASS; true GUI lost-response/timeout fault not induced; no seeded simulation claimed |
| D07 | NOT RUN | No native NotFound/HTTP timeout/Replay; confirmed commit required no replay; automated uncertainty/exact-key tests PASS |
| D08 | NOT RUN | Automated native/TS malformed proof/full receipt refusal PASS; no native wire corruption |
| D09 | NOT RUN | Automated same UUID/OS guard/interlock PASS; two native processes not raced |
| D10 | NOT RUN | Automated archive/flush failure retains pending PASS; no new native OS storage fault injection |
| D11 | NOT RUN | Complete Committed Resolve/Archive/reopen PASS; sealed Rejected native branch not exercised |
| D12 | NOT RUN | Successful committed weekly refresh PASS; failed-refresh/read-retry covered automatically,not injected in native GUI |
| D13 | PASS | Actual restored boards,typed equal-ID3 Locate,cancelled1 history,exact unrelated/member/legacy preservation;positive recorded-Rig fixture still absent |
| D14 | NOT RUN | Input focus,Escape/opener focus,keyboard legacy selection PASS;window-resize drag did not change geometry,so narrow-window NOT RUN;Narrator/full traversal NOT RUN |
| D15 | PASS | Real flag-free reopen with valid original1 disables prepare;actual sidecar flags absent;no pending reappears;wrong-root guards rerun automatically |
| D16 | NOT RUN at record creation | All fresh local suites/builds PASS;new exact-head CI awaited and linked in evidence PR |
| D17 | PASS normal Release path | Actual unchanged EXE/sidecar Confirm→reopen→Resolve→Archive→reopen and full logical/integrity review;installed NSIS not tested |
| D18 | BLOCKED | Qualified licensed replacement VM unavailable;offline installation/upgrade/WebView2 supplement/OS reboot retention not executed |

No current native FAIL/product defect was demonstrated. The unsuccessful resize
gesture and initial local verifier mistake are tooling/coverage limits, not
evidence of a product defect. No uncertainty/replay was fabricated to claim PASS.

## Delivery and remaining gates

This branch changes pre-test design/acceptance documentation and the demonstrated
backend CI job budget; no product fix, migration or new installed software.
Original source/synthetic data/scripts,
UI screenshots, logs, SQLite snapshots/backups/journals remain local. Public
repository receives no originals, personal data, credentials or raw diagnostics.
Issue130/20/99 remain open; new Draft PR waits for human review. Do not append
to merged132 or automatically merge/close/publish/deploy.

Next bounded work is the remaining native fault matrix with new scenario-specific
action approvals where needed, then qualified licensed offline VM acceptance.
Future Employee Week/global search/company-Crew-employee PDF/Excel mixed-type
audits remain separate. Customer Demo/UAT, production Restore, formal Publish
and delivery are still unapproved. Normal engineering success supplies none of
those approvals or legal/resource qualifications.
