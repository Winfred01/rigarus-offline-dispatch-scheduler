# Issue135 — complete qualification proof regression

Engineering verification only. Main baseline
`1923b564d95c8bb790ad00c82864f5b6fb52c6fe`; independent branch
`codex/issue-135-qualification-proof`. [Design checklist/plan](../design/2026-11-27-issue-135-qualification-proof.md)
committed `43d5db3da07304d3171b8790f543985bedc9cbac` before fix
`d5e7a161fea49ed85f228562d39b1807e7fe4c5f`.
[Issue135](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/135),
[Draft PR136](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/pull/136),
parent130. PR134 remains separate instrumentation/pre-fix fault evidence.

## Failure, minimal fix and safety

Actual native explicit-policy5→8 Restore preparation failed closed, although
Python prepare returned a valid plan. No pending/request/Restore was created.
Four new projection cases fail before fix with zero Qualifications aggregate;
unknown-policy case already passes. Existing Rust/renderer require exactly one
summary; the common weekly projection supplied it only for unknown policy.

`schedule_workbench.py` now adds a missing aggregate using existing
`day_capability_proposal._groups` semantics. Explicit empty requirements remain
distinct from missing policy. Individual Qualification:code states/reasons stay
present, known failure propagates Blocked, unknown remains Pending. Existing
unknown-policy output is unchanged, not rewritten. No native/renderer proof or
hash/revision/request validation was weakened. Root Validation Pending /
Apply=false / Publish=false remains unchanged.

No migration or schema21 changes; no persisted historical JSON, AM/PM or source
version rewrite. New plan fingerprints naturally reflect complete observations;
never change an already retained original request payload to obtain a new plan.
No new qualification requirement/default, production writer or UI redesign.

Changed implementation/test files: backend schedule_workbench.py, new
test_qualification_projection.py, shared desktop_restore_fixture.py (now explicit
policy), frontend draft-restore-state.test.mjs (real Python proof, no product TS
change), plus design/acceptance Markdown.

## Exact matched artifacts and environment

Built after fix d5e7a16, all version0.1.0. Separate worktree/output; prior installer
unchanged. Windows11Pro x64 25H2,10.0.26200.9974; WebView2 runtime158.0.4370.45,
connected native development host, not offline VM. NSIS built, not installed.

| Artifact | SHA256 |
| --- | --- |
| Launched standalone EXE | `0b8722823e632f7da3e0bee6c9445ec6d71543ece40ab454fd168be8ea203239` |
| Matching adjacent sidecar | `41911c897c442715bce74f5992e48853c5459736e31f61fd06995702ee365934` |
| Independent x64 NSIS installer | `42c0f6446f98c39df5f1f898f77106cf5277a0800ae9b9013c09502d106d00d3` |

## Actual native regression

Process-only smoke root and Restore synthetic opt-in; production gates remain
closed. Original fault-injection feature is absent from this main-based fix;
these are normal previews, not timeout instrumentation tests. No protected
Restore/Replay/Archive was attempted in these new profiles. Owner Class A scope
verified; no platform rejection encountered here. Existing refused wire request
from PR134 is untouched.

| Case | Result | Actual evidence |
| --- | --- | --- |
| Original failure reproduced | PASS | Pre-fix EXEa677/sidecaradba rejects same5→8 profile; zero Restore/pending |
| Fixed5→8 preparation | PASS | Profilea93ec70d-711e-4332-91a3-4ac787b5a1a6, source1, Current/proposed inverse displayed; five original rows retain IDs/staff, three additions proposed Cancelled;34 warnings initially0/34, Confirm disabled |
| Long note and Escape | PASS |1824-character synthetic note wraps in scrollable table; native Escape closes dialog, opener focus returns; no SQL/journal writes |
| Fixed5→2 preparation | PASS | Separate profile42fdfa98-af0d-481b-9c95-1b74a748f448 shows Cancelled original dates and proposed reactivation at new revisions;34 unconfirmed warnings, disabled Confirm; Escape preserves all data |
| Known driver blocker | PASS | Separate synthetic backup clone (same preserved database UUID but different root), official Suspended evidence; native explicitly Blocked, warning acknowledgement cannot override, Confirm disabled; no write |
| Full5→8/5→2 native submit/reopen | NOT RUN | This regression verifies preparation and cancellation; actual committed variant acceptance is not borrowed from backend contracts |
| Complete mixed typed Locate/Rig/history UI | NOT RUN | Actual initial board contains independent Full Day/Legacy PM projects and equal typed integer IDs; complete post-Restore view/Locate flow remains separate |
| Offline install/upgrade/WebView2/OS reboot | BLOCKED | No qualified licensed replacement VM; host/CI/NSIS do not substitute |
| Narrator speech | NOT RUN | No speech/readout acceptance claimed |

Coherent read-only BEGIN snapshots cover every table, integrity_check=ok and
foreign_key_check empty. All values/history/legacy rows identical before/after
each preview/cancel; zero RestoreVersion/receipt/pending:

- 5→8 day rows9/history19/source1, digest
`ebca7fec5f06cd8dddfec54ee1deedab6c19ae6d699b0018372d106b4fa43d09`.
- 5→2 day rows6/history16/source1, digest
`1bdadd77b42c5a43f0e651f36ecc19b2ad7032f66d689dc3d25eba49ee7d9458`.
- Blocked clone day rows6/history16/source1, digest
`9e6e47d739918ad279ab1058bee38b526a7638ff83a544c251eb7cedf8012f52`.

Source original5/after8 and original5/after2-active fixtures were created through
official stores/source Apply before testing. No Restore outcome/receipt/pending
was pre-seeded. Clone uses consistent backup and preserves identity deliberately;
physical smoke roots and process flags remain isolated. No actual employee/Rig
is invented from Home Crew or approval; current Rig may remain stale/Pending.

## Commands and independent tests

PASS locked `uv sync --locked --group bundle`, `npm ci`,
`dotnet restore Rigarus.sln --locked-mode`.
PASS `ruff check` / `ruff format --check`, `npm run format`, `npm run build`,
`cargo +1.95.0 fmt --check`, `.NET format whitespace --verify-no-changes`.

PASS full `python -m unittest discover -s tests -v`:684 tests,316.695s
(wrapper317.757s,900s upper bound). Includes six new projection/Restore tests:
unknown, explicit empty, missing/verified/known-failed named proof, real Blocked
Restore with only sealed Rejected receipt. Read-only digests/integrity/FK and
equal-integer namespaces checked.
PASS `npm test`:103 tests, including actual generated Python envelope/receipt.
PASS Rust Release locked custom-protocol tests:25, including same real Python
explicit-policy envelope/receipt through unchanged strict native validation.
PASS historical.NET Release:35, zero build warnings/errors.
Distinct total847=684+103+25+35; packaged sidecar18 repeated checks PASS45.163s,
not added to distinct total. No skipped tests claimed as executed.

PASS Windows Release + scripts/Build-RigarusSidecar.ps1 + locked Tauri NSIS;
privacy421 tracked/staged paths, diff whitespace and Markdown UTF8/fences/links.
[Windows CI158](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/46093570582)
on d5e7a16 completed successfully: all3 jobs passed, including desktop/NSIS and
acceptance artifact assembly/upload. Later evidence-only commit has its own CI;
do not present an unfinished latest-head run as passed. Raw logs/screenshots/
databases/original UI remain local only.

Strict18-case parent matrix remains in PR134's acceptance record and is scoped
to its original artifacts. This fix adds matched native preview/cancel/Blocked
evidence only; does not turn every compound D01/D03/D13 into PASS or claim new
fault injection on these artifacts. Review PR136, then finish native variant
commits/typed Locate and remaining unblocked parent cases. Customer Demo/UAT,
production Restore/Publish, deployment/delivery and Release remain unapproved.
