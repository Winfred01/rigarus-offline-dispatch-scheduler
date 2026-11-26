# Issue18 — read-only Before/After impact engineering evidence

Baseline main8f6e547d62c772d56d277d3e4a645a9aca272910, human-merged122.
Merged-main Windows CI45757807364 completed success/all3 jobs before product
edits. Pre-code checklist/plan f7e41c4, isolated codex/issue-18-impact-preview.
Public repository; synthetic fixtures only. No merge/Release/Issue closure.

## Implemented operator workflow

WorkItem Auto-Recommend (or weekly Locate & Auto-Recommend) → explicitly confirm
Remaining Days, candidate Crews/local horizon → Preview Impact. The first read
shows saved active visits. Explicitly check exact FullDayDraft IDs/revisions to
replace only in memory, then Recompute impact. No selection means additional
work, never implicit release. Legacy records remain visible/unselectable.

Compare Saved WorkItem/Crews/planned span/actual people/Rig/resource checks with
Proposed dates/remaining days/missing resources. Saved Remaining Days is Not
recorded, not inferred from five saved dates or EstimatedHalfDays. The desktop
does not choose proposed workers/actual Rig: their checks remain Pending. The
read-only API supports explicit worker/vehicle nominees for synthetic validation,
without transferring staff or supplying operational vehicle proof.

Protected visits remain occupied; IDs and skipped-date reasons explain gaps.
Locks are Not recorded/Unsupported. Complete downstream calculation is Needs
Review/Unsupported Dependency, never inferred from date order. No B/C movement.
Current is observed at read, not reservation/safety. Stale stays retired until
recompute; changed selected revisions require explicit Reload saved visits (clear
selection) and deliberate reselection, never automatic rebinding. Errors cannot
return a Current/empty-safe result. Cancel/Escape writes
nothing. Every root Pending / Apply=false / Publish=false; production daily
writers remain closed. No new migration, confirmation/lock/audit/version table.

## Reproducible synthetic cases

Run the backend locked environment:

```powershell
uv run --locked python -m unittest discover -s tests -p test_impact_preview.py -v
```

Five A visits November23–27,2026, explicitly selected by typed ID/revision:

| Proposed confirmed days | Protected occupation | Result |
| --- | --- | --- |
| 8 | None | November23–December2, skips unapproved weekend |
| 8 | B on November30, same Crew | November23–December3, retains B |
| 8 | B November30 + legacy PM December1 | Finishes December4; old integer ID1 remains separate from day ID1 |
| 2 | None | November23–24; remaining saved A dates are only proposed releases |
| 8 | No replacement selection | Existing A dates still occupy; no silent release |

## Actual engineering verification

| Check | Result |
| --- | --- |
| Latest-main baseline frontend70/backend580 | PASS |
| New focused impact tests27 | PASS, final focused rerun25.325seconds, including100 extra synthetic projects/visits and a10second read assertion |
| Full backend / frontend / Rust / historical .NET | PASS607 /74 /11 /35 =727 distinct tests; packaged16 repeats |
| Actual packaged sidecar build/tests | PASS16 repeat subset |
| Locked bundle/npm/.NET restores; Ruff/Prettier/TS/Vite | PASS; no lock/dependency changes |
| Windows Release and Rust tests | PASS11, including annual-scope transport whitelist/size tests |
| NSIS | PASS after normal client exit/retry; initial attempt FAIL due to running synthetic binary holding a build file |
| PS5 synthetic acceptance harness | PASS, including expected mock-failure checks |
| Documentation | PASS12 Markdown files/202 local links, UTF8/fences/unique anchors |
| Staged privacy/diff | PASS387 indexed paths; clean staged whitespace; no original designs, databases or raw diagnostics |
| Exact-head Windows CI | NOT RUN before push; final PR records observed head/run/jobs |
| Offline install/upgrade/reboot | BLOCKED: owner confirmed no qualified replacement for expired Evaluation VM |
| Customer Demo C/E/UAT/production approval | NOT RUN / pending human acceptance |

New regressions cover explicit positive-day confirmation, extension/early finish,
typed scope/revision/parent/status errors, legacy and daily occupation, false
gates, determinism, dual sort, minimum/Level/qualification/driver negatives,
actual employee cross-Crew and old PM collisions, source/target rechecks, actual
Rig collision/maintenance, saved weekend Pending/Declined, unknown calendars,
outside-horizon/staff/calendar Stale, read errors, bounded scenario/deadlines,
cross-year/leap/DST/annual boundary, pinned WAL concurrency and pure projection
with file/SQL/network/clock access forbidden. Full logical dumps remain equal.
Front-end tests bind exact scope and latch Stale across source reversion.
Actual final packaged-sidecar16 repeats include authenticated impact preview,
wrong/missing Host/token rejection, logical equality, and Current after restart.
One boundary fixture initially used the excluded annual anniversary and was
corrected to November22,2027; November23 is now explicitly tested as422.
An out-of-horizon replacement fixture was corrected rather than weakening exact
scope validation. No safety rule was relaxed to make tests pass.

Initial accepted local NSIS SHA256 before transport-bound follow-up
c9527931749f7cd267ab0ba44625d335dccaada1e1291dffd96075c171b523ab
(built, not installed or released; final PR records the subsequent64KiB build).
Native screenshots below belong to the
separately identified earlier executable; final sidecar additionally enforces
explicit confirmation at the direct service boundary. No borrowed final-native
fault/offline acceptance is claimed.

The actual366-row serialization was25,164bytes, exceeding the inherited16KiB
bridge. Both impact actions now accept at most64KiB; date-only actions retain
16KiB. Rust tests prove annual scope acceptance, oversized rejection before
network and refusal of Apply/Publish/injected action names. This is a technical
read-only transport correction, no writer or business-policy change.

## Actual native development-host check (not VM acceptance)

Connected Windows11 x64 development host, native Tauri/WebView2 Release executable
SHA256 c8558cec165e4279d28f058565db79a60f3c200577733d12c3a24fa895d20212.
Isolated new synthetic profile, production write test flag absent. Actual window
approximately1442×991 pixels; original L13/image65 modal/table/button vocabulary
retained, no complete-app redesign or prototype Apply/Validated/half-day input.

PASS: open actual WorkItem recommendation; explicit8 days and local November23;
Crew selection; Preview Impact; five distinct FullDayDraft checkboxes and raw
LegacyHalfDay ID1/PM visible; changing scope retires the old result; recompute;
Current and Saved November23–27 versus Proposed November23–December3 table;
Saved employee1, Proposed workers/Rig Pending; exact unsupported lock/dependency
labels; internal dialog scrolling; no active Apply/Publish. Screenshots were
actually inspected, including input/scope, Before/After and post-Escape board.
Table columns/typography/buttons match surrounding UI and remain readable at the
tested size. Long reason lists are scrollable; other viewport sizes NOT RUN.

PASS: Escape returns to unchanged weekly board with visible focus ring on
Auto-Recommend. Reopen clears confirmation/input/old result; Escape again and
normal app exit. Before/after full SQLite logical digest equality, integrity=ok,
zero foreign-key errors and zero editor receipts verified after cancellation and
again after exit. Original IDs/notes/workers/legacy data remain unchanged.

Additional latest-client native check: EXE SHA256
0cfaf02cf4c1331abea33f7a2b15b37882a2f6a0f9bc04591555a6784f582e08.
Independent consistent synthetic copy, confirmed1 day and selected FullDayDraft4
revision1. Verified unchanged initial digest; deliberately changed only its saved
note through the internal synthetic Store to revision2 (separate source mutation).
Actual Recheck showed Current→Stale. Recompute with old scope rejected, displaying
recovery guidance; Reload saved visits cleared selection and visibly showed
revision2. Deliberate reselection/recompute returned new Current. Escape/normal
exit; digest equals the baseline captured after the deliberate source edit,
zero added receipts, integrity=ok/FK0. Thus preview/reload/reselection made no
additional SQLite changes. Native scope/error/Stale/reload screenshots inspected.

Switching between multiple Crews, native storage/response fault injection, three
viewport sizes, screen-reader audit, installer execution,
upgrade/reboot and disconnected first launch NOT RUN in this slice. API/state
tests cover the corresponding implemented source/stale behaviors; do not replace
native/offline acceptance with them. No customer database or license/security
mechanism was changed.

## Remaining / future contract

See [design](../design/2026-11-25-impact-preview-contract.md) for future exact
before/after + database-lineage identity + typed revision/native-source vector +
locks + operator intent + namespaced idempotency + transaction audit/version
requirements. Current proposal SHA is not Apply authority. Manual Apply must be a
separately reviewed transaction with complete evidence/revalidation/rollback;
unknown lock/dependency/resource policy is not bypassed. Recoverable versions,
delay chains and formal PDF/Excel follow in the owner's confirmed order.
