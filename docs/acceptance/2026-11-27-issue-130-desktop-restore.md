# Issue130 desktop Restore — new engineering evidence, November27,2026

This is a new product slice after human-merged design131/maind4f97ad8, not a
relabeling of backend129's tests. Design/authorization was committed first as
3be3cd4 on `codex/issue-130-desktop-restore-ui`. Human review, customer Demo/UAT,
production Restore and Publish remain separate and unapproved.

## Sources and implementation

Freshly read AGENTS/checklist d3b9bea; six required documents' affected/current
sections: plan00/playbook09/decisions10 f3a68da, architecture02/model03/
acceptance05 0323f9e. Inspected current130/merged131 and original source21,
Restore preview/API, Apply bridge/journal and mixed weekly code. Original local
November24 UI DOCX SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`,
mtime2026-11-24T23:15:38.711423Z: L10 paragraphs54–58/image62, L12 paragraphs64–68/
image64, L13 paragraphs69–73/image65 text and original figures. These are paragraph
locators, not page numbers. Original DOCX/figures stay local. Full source revisions/
checkout UTC metadata are retained locally. See [pre-code checklist/plan](../design/2026-11-27-issue-130-implementation.md).

New independent Restore Dialog, strict TypeScript/Rust proof validation, fixed
authenticated bounded command, independent actual synthetic status/flag,
operation-specific journals with shared profile OS guard, cross-operation pending
interlock, and flush-before-retirement. Resolve is read-only; replay and archive
are explicit and separate. No SQLite migration, new business rule, legacy record
rewrite or production gate opening. Existing schema21 backend inverse remains
the transaction authority. Source/plan/warning digests use already-locked sha2
0.10.9; adding it as a direct dependency introduces no new locked version.

The original mockups do not define an exact Restore screen. The deliberate
adaptation retains the existing shell, typography, colour, Dialog and typed row
tables; four complete scrollable views replace a misleading generic Undo.
Native inspection found/repaired initial focus and retained-snapshot/recorded-
acknowledgement presentation. No screen-reader/narrow-window pass is inferred.

## Actual local engineering checks

Windows11Pro26200 x64 development host, installed WebView2, network **not
disconnected**. Synthetic local profiles only. Python3.13.10, Rust1.95.0,
VS2022 x64 build environment. Native interaction used normal visible windows,
not Hidden or a VM. No security/licensing changes, host restart, old installer
modification or real database access.

| Command/check | Result | Local evidence label |
| --- | --- | --- |
| `uv sync --locked --group bundle`; Ruff check/format | PASS;140 formatted files | backend-restore/final-format logs |
| `python -m unittest discover -s tests -v` | PASS678;0 skips,325.610s | backend-full.log / backend-result.json |
| packaged sidecar `test_sidecar.py` against candidate EXE | PASS18;30.233s;status/auth/default-reopen included | packaged-final.log |
| `npm ci`; Prettier; `npm test`; TypeScript/Vite build | PASS102;0 skips;build PASS | frontend logs |
| locked Windows Release build and `cargo +1.95.0 test --release --locked --features tauri/custom-protocol` | PASS25;0 ignored;2.03s, real Python contract included | cargo-ui-final-elevated.log |
| locked .NET restore, whitespace, Release build/test | PASS35;0 skips;0 build warnings/errors | dotnet logs |
| staged path/secret scan; diff/docs link checks | PASS417 indexed paths;whitespace;9 docs/192 local links | local validation logs |
| new NSIS candidate build | PASS301.06MiB;not installed | installer-build.log |
| new PR Windows CI | Pending product PR run | PR checks, independent of native acceptance |

The678+102+25+35 distinct suite tests total840; packaged18 are an additional
execution mode, not18 new distinct tests. A restricted-sandbox Rust/Python child
hit its45s bound; rerunning the same test under the existing authorized local
test context passed25/25. No deadline/assertion was relaxed. Initial contract
fixture import/normalization errors were corrected before the final passing run.
Ruff caught a formatting-only test change; the final check passed.

## Fresh18-case matrix

PASS entries describe the stated layer only. Native columns do not inherit
automated/backend results. BLOCKED cases are unfinished acceptance targets.

| ID | Automated/engineering result | Native result and remaining scope |
| --- | --- | --- |
| D01 | PASS exact original/current/inverse,5→8/5→2,IDs/notes/staff/revisions | PASS read-only two-addition inverse and retained5→8 views; live5→2 completion NOT RUN |
| D02 | PASS exact per-warning set,missing/extra/mutated refusal | PASS initial0/4 disabled; individually checked4/4 plus separate scope enables confirm in initial candidate; final native submission BLOCKED |
| D03 | PASS blockers/stale/profile/kind refusal | PASS final candidate old AM occupancy Blocked/disabled/no-write; later edit Stale/no submit |
| D04 | PASS cancellation semantics/late epoch invalidation | PASS Escape before dispatch, business/audit/receipt logical equality |
| D05 | PASS immutable envelope/late-response and request reuse checks | BLOCKED live submit/double-click/close during send |
| D06 | PASS full native validator against actual Python committed contract; journal reopen | PASS seeded pending key survives close/reopen; BLOCKED live Resolve/commit-lost-response; seeded state is not GUI-induced timeout |
| D07 | PASS NotFound uncertainty,exact original key/body checks | BLOCKED live timeout/NotFound/unchanged replay |
| D08 | PASS malformed/mismatched operation/profile/request/source/plan/After/flags/resources refused | NOT RUN wire fault injection in native GUI |
| D09 | PASS same-key separate archives,shared exclusive handle and pending interlock | NOT RUN two visible processes/Apply↔Restore end-to-end |
| D10 | PASS malformed/oversize/guard/archive/flush faults; retry reflushes existing archive,keeps pending on failure | NOT RUN OS fault injection in GUI |
| D11 | PASS complete Committed versus sealed Rejected/native archive validation and exact retirement | BLOCKED live receipt Resolve/Archive |
| D12 | PASS committed survives failed read refresh and read-only retry | BLOCKED committed GUI+failed board refresh/Locate |
| D13 | PASS existing mixed projection/typed equal-ID Locate and source/database preservation regressions | PASS final Job Schedule/Crew Board simultaneously show FullDayDraft1 and LegacyHalfDay1 PM; native Locate-after-Restore NOT RUN |
| D14 | PASS epoch/focus-state and explicit accessible labels by inspection | PASS initial input focus,Escape and long retained review/66 recorded items; narrow window/Narrator/complete keyboard traversal NOT RUN |
| D15 | PASS actual status/default gate/exact root/auth/flags regressions | NOT RUN default-gate visible native launch |
| D16 | PASS full local840 and packaged18/build; final scan/CI recorded below when executed | Windows CI does not supply a native GUI pass |
| D17 | PASS below read-only host snapshots/integrity | BLOCKED complete exact-package native write/reconcile gate; installed package NOT RUN |
| D18 | NOT RUN disconnected installer/upgrade/OS reboot | BLOCKED qualified licensed stable VM missing; expired Evaluation is not bypassed |

## Reproducible native sequence and local evidence

Follow [synthetic steps](../../samples/synthetic-only/desktop-draft-restore.md).
All raw screenshots, original diagrams, SQLite files and journals stay local;
only this sanitized record is committed. Test roots are identified by local
labels, not machine/user-specific paths. No synthetic database is uploaded.

- `gui-fresh-1`: original two-date addition, plus unrelated legacy PM with equal
  integer ID. Open Schedule Restore, original1, prepare; inspect four views,
  individually tick4 warnings and exact scope. Confirm becomes enabled. Native
  submit was denied by automatic approval review and did not run. Escape closes;
  before/after logical digest
  `036f8986d9813b8f198b08cba95b05a18b7ff4e00dc0e45bb1e7d4ceff7059ac`,
  integrityok,FKempty,history2,zero restore versions/receipts.
- `gui-blocked-1`:5→2 source with an old AM occupying a cancelled original day.
  Final native prepare shows Blocked and disabled submit. Before/after digest
  `078f745ef444d787aae5737468e29638ae303bff8d4a46218290a399c4967ff3`,
  integrityok,FKempty,history8. Close normally.
- `gui-stale-1`:5→8 source edited later. Prepare shows Stale and no enabled
  submit. No before-launch native logical equality claim; automated no-write
  checks cover that assertion. Close normally.
- `gui-unknown-1`: deliberately seeded **already backend-committed** inverse plus
  its exact pending native envelope, simulating a lost response. Native reopen
  displays the unchanged original request key; no automatic replay. Final UI
  correctly labels Retained review/not a current read and recorded66/66 items.
  Resolve was also denied by automatic approval review. Close/reopen and read-only
  board checks preserve digest
  `a32048474d8dd39e23a29b13a666e5a6fb2619a37972fb02a163ab8828b133c1`,
  integrityok,FKempty,history18. Pending remains; no archive/retirement occurred.

Native executable SHA256 after final display/focus fix:
`086cdd3639f5c5026a66451e2230832fbf1eec92d87b5ac118b10c1596414793`.
The earlier0/4→4/4 inspection used an earlier candidate; final retained review
and mixed board checks used the hash above. No installed-package/VM pass is
claimed from this host Release executable or from building an NSIS artifact.

Separately built, uninstalled candidate NSIS installer SHA256:
`157632d95a25d849d3fcfca7822f64cd883039ddcfce376e632c331b93c1c786`.
The0.1.0 product metadata remains unchanged; this is a new branch-local candidate,
not a replacement of an old installer or a released version. Bundle patching may
change its embedded executable hash; installer and inspected EXE identities are
reported separately. Raw build logs include local paths and are not committed.

Automatic approval review denied Confirm and later Resolve, requiring new
action-time user confirmation. Resolve's implementation is GET-only and Archive
is separate, but the denial was not bypassed through another tool/API. An explicit
question requesting only isolated synthetic submit/receipt/archive testing is
pending. These native gates remain BLOCKED until actually authorized/executed.

## Remaining gates

Finish the blocked/unrun native matrix, review the Draft PR and preserve pending
evidence. Qualified disconnected Windows installation/upgrade/reboot remains
BLOCKED. Employee Week/search/export mixed-type audits remain future independent
work. Manual-editor coordination is not covered by the new Apply/Restore mutex.
No new half-day editor, calendar conversion, production writer, formal Publish,
automatic merge/Issue closure/Release/deployment or customer acceptance.
