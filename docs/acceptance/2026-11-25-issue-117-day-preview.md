# Issue117 / #28 — Read-only full-day WorkItem preview

Baseline main `a3da29ae62a6acae77b8e6de1a8ba92c4de7affb`, human merge116.
Branch `codex/issue-117-day-preview`; pre-code Design-First commit a34d629.
Refs #28/#99/#113. [Source/design mapping](../design/2026-11-25-issue-117-day-preview-checklist.md).
The current repository is PUBLIC; synthetic data only. Original designs, DBs,
profiles, local logs and binaries stay ignored/local. Root unrelated changes retained.

## Delivered slice and preservation

- Strict readonly FastAPI preview/freshness DTOs over the existing schema18 v6
  coherent snapshot and generator. Stable Project/WorkItem/Crew IDs, local dates,
  explicit Remaining Days confirmation, bounded choices and safe failure messages.
  Missing confirmation remains Needs Review; no estimate or visit deduction.
- Projection returns coherent title, ranked alternatives, actual accumulated/
  skipped dates/reasons and grouped missing-evidence counts, not raw records or
  full snapshots. Input/context edits produce Stale; unknown read errors cannot
  silently produce Current. Actual sidecar retains bearer/Host enforcement.
- Fixed-path Rust preview/freshness actions,16KiB input and60second HTTP bound;
  no writer or generic path. React WorkItem Auto-Recommend follows local L13,
  explicit inputs, both sorts, explanations, invalid/loading/failed/stale states,
  independent request epochs, manual/focus recheck and cancel/unmount guards.
- Every root FullDay / Validation Pending / Apply=false / Publish=false.
  Actual workers and Rig remain unselected; no calendar/evidence approval inferred.
  Missing day data stays Unknown/Needs Review. Existing AM/PM controls are not a
  full-day editor. Production daily inputs/day-Draft gates remain closed.
- No migration, schema/version change, historical-data rewrite, sidecar lifecycle
  change, dependency update, installer replacement, human Apply/Publish or export.
  HTTP integration compares every logical SQL record before/after and integrity/FKs.

## Commands and actual engineering outcomes

Windows11 x64 developer host (25H2, build26200.9974), networking active, development tools and WebView2
already present. Python3.13.7 / uv0.10.12, Node22, Rust1.95.0, .NET10.
Local wrappers bound backend900seconds, focused180seconds, harness300seconds;
each Rust/native build was observed to completion. This is not a clean device.

| Executed check | Outcome |
| --- | --- |
| `uv sync --locked --group bundle`; `uv run --locked ruff check`; `ruff format --check` | PASS;122 Python files |
| Locked environment `.venv/Scripts/python.exe -m unittest discover -s tests -v` | PASS **554**, no skips;545 baseline +8 API +1 sidecar |
| Focused `test_day_recommendation_api.py` | PASS **8**; strict IDs/bools/unknown fields, both sorts, missing confirmation/horizon, limit,404/409/503, no writes/closed gates, Stale |
| `scripts/Build-RigarusSidecar.ps1`; packaged `test_sidecar.py` with `RIGARUS_SIDECAR_TEST_EXE` | PASS **14** repeated source-suite cases, real Windows process/authenticated read/restart |
| Locked `npm ci`; `npm run format`; `npm test`; `npm run build` | PASS **49** tests, TypeScript/Vite build |
| Rustfmt / locked release build / `cargo +1.95.0 test --release --locked --features tauri/custom-protocol` | PASS **8**, final Windows executable rebuilt |
| .NET locked restore / whitespace verify / Windows Release build / no-build tests | PASS **35**,0 warnings/errors |
| Windows PowerShell5.1 `scripts/Test-TauriAcceptanceHarness.ps1` direct | PASS; synthetic deliberate failure/timeout/SQLite/UIA protocol cases, not native installation |
| Markdown UTF-8/fences/anchors/local links; staged diff/privacy | PASS7 documents/115 local links,360 indexed paths; no raw design/data/logs |
| Exact-head Windows CI including installer/kit upload | Follow live Draft PR checks; final result/link recorded in PR/Issue, never inferred from local build |

646 distinct automated tests (554+49+8+35); packaged14 repeats are not counted
again. The initial new Host-rejection test incorrectly expected403; existing
sidecar correctly returns401. Only that test assertion was corrected and the
entire backend rerun passed. Initial nested harness launch reported
package-integrity CommandNotFoundException; unchanged script rerun directly in
Windows PowerShell5.1 passed all cases. Initial PS5 build wrapper treated normal
PyInstaller stderr as an error; actual build rerun under PS7 passed. No validation
step was bypassed or weakened to conceal those failures.

## Native desktop reproduction and observations

Run only against an independent synthetic profile. Launch own release executable
with `RIGARUS_SMOKE_DATA_ROOT` scoped to that profile, existing application data
untouched. The seed uses a new Project `SYN-PREVIEW-117`, WorkItem1/Civil/one Crew
required/legacy estimate99, and separate Crew1/Crew2. No actual worker or Rig.
Using the internal daily store for test setup only, Project Working November23–27;
C1 Working23/27 and explicitly NotWorking24–26; C2 Working24/25. These are test
fixtures, not instructions to edit customer SQL or open production writers.

1. Open Project Management and the saved WorkItem's Auto-Recommend.
2. Enter Remaining Days2, explicitly confirm, select C1/C2, start November23,
   end November27, default3 alternatives. Preview.
3. Earliest Finish: C2 November24→25 then C1 November23→27. Earliest Start:
   C1 then C2. Open C1 details: accumulated23/27; skipped24–26/calendar conflict;
   driver/personnel/availability/skills/qualifications/Rig checks missing/Pending.
4. Verify Apply/Publish disabled and Current qualified as read-time observation.
   Before any deliberate fixture edit, all logical records equal the seed.
5. Deliberately set only isolated C1 November25 Working. Recheck inputs shows
   **Stale — inputs changed. Preview again.** No automatic application occurs.
6. Escape closes; actual screenshot shows focus returned to Auto-Recommend.
   Return reopens blank Remaining Days, confirmation unchecked. Enter0 and submit:
   specific positive-whole-number error, no candidate generated.
7. Close the owned app normally. Final build additionally previews this changed
   fixture with limit1: C1 November23→25, one complete alternative omitted by
   result limit; C2 is not labeled capacity-deficient. Close normally again.

| Native scenario | Outcome / conditions |
| --- | --- |
| Real Tauri→Rust→packaged FastAPI→SQLite preview, both sort orders | PASS, normal visible window, connected host |
| Original L13 hierarchy / scroll / explanations / Pending and disabled actions | PASS at1442×992; no half-day or feasible badge in new dialog |
| Deliberate synthetic daily input change and Stale | PASS |
| No committed data change from preview/sort/cancel; IDs/estimate retained | PASS, logical hashes and SQL integration |
| Escape, visible focus return, reopen reset and invalid0 | PASS |
| Final-build complete-option limit1, normal close | PASS |
| SQLite integrity / FK checks; app/sidecar exit | PASS, `ok`,0 FK errors, no owned test process remaining |
| Source failure/late reply/range limits | Automated coverage only; induced native HTTP race/failure NOT RUN |
| Hidden supervisor / narrow viewport / screen reader | NOT RUN for this new dialog |
| New installer offline/upgrade/VM reboot/clean-device rollout | NOT RUN; no earlier offline package result borrowed |
| Customer Demo/UAT and production permission | NOT RUN / NOT APPROVED |

First native executable SHA256
`af6d31fc114fb0db2466820966f74ee71210d485d80bfd777da96c4f72530c11`.
After final limit-display correction, executable SHA256
`05af8b895da053d14c29287f7ad4772f9c1e95716e17c1afd409cfd54c459d5f`.
Raw hashes/logs/source inventory stay local under the ignored evidence folder.
Seed logical digest `ede81833edfb8a737d6296440a071118dab646408fb978ad532eafc01939229f`
matched after first preview/sorts. Deliberate fixture edit produced
`8680ecee870672d9bab1667750c83f9c020d1cd60017674d54f1d7634e4f72b0`;
subsequent cancellation/reopen/final preview retained exactly that value.

CUA initially lost its tool session; no native success was claimed until bounded
recovery and actual observations. Numeric element input lacked geometry; actual
screen-coordinate interactions and observed screenshots were used. Tool issues
are not product acceptance. Raw desktop/window inventories are not published.

## Remaining boundaries

Daily boards/Locate and day-input/evidence editors, actual proposed members/Rigs,
complete eligibility/Foreman/category/legal/authority policy, locks/Before-After,
transaction revalidation/human Apply/audit/recoverable versions and official
PDF/Excel remain separate #99/#18/#29 slices. No Issue closure, merge or Release.
Human review, full offline rollout, customer acceptance and production approval
remain independent gates; a successful date alternative is not safe dispatch.
