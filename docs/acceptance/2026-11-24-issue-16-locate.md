# Issue16 exact saved-card Locate — engineering verification

Baseline: `3101a726a8a5acd18b852d0b00a58ba860a178f5` (main, after PR97).
Isolated branch: `codex/issue-16-locate-cards`. Design-first commit: `7f5da5b`.
This is a partial Issue16 UI delivery, not Demo B/E customer sign-off.
No same-scope open PR was found at inspection. Existing unrelated checkout
changes and local design originals were preserved.

## Design comparison and operator path

The updated November24 local UI design's original embedded L01, L02, L03, L08
and L14 figures were inspected, rather than reconstructed from captions.
The [design checklist](../design/2026-11-24-issue-16-locate-checklist.md) records
the exact source hash and XML paragraph/figure mapping; Word pagination was not
verified. No Locate prototype HTML was found in the requested local search.

L01: retain existing project/Crew boards and local Sunday–Saturday dates; add
visible 1 Week. L02: existing Review & Publish now lists real dated saved calendar
and staffing observations with persisted visit IDs and per-row Locate. It
explicitly includes visits hidden by Crew/Project filters. L03: close source,
re-read current ID/date, reveal the exact AM/PM card within the internal sticky
grid, focus it, amber pulse twice for about two seconds, then clear. Reduced
motion retains a static outline. A second Locate cancels the preceding cue.
L14: existing saved draft details supply the same Locate action. Global Schedule
search reuses it for cross-week navigation. Existing resource/Pending wording and
disabled Publish/export remain; no false resource approvals or Apply path.

L08 has no real exception queue source in this baseline. Maintenance, operational
pause/resume, locks and version restore are not implemented by this slice.
The current board has no project row cap or Rig/status filters to adjust.
Missing/cancelled records receive feedback; the unsupported Paused status is
guarded in pure tests, not claimed as an existing SQLite/UI workflow.

Native inspection found the first review table hid its action column in a narrow
modal. The final implementation widens this review only and pins its action column.
Desktop and narrow browser retests passed after that correction.

## Actual verification

All data synthetic:105 Projects,9 Crews,18 Employees,9 reference Rigs and55
saved visits initially. This includes distinct AM/PM IDs, unknown calendars,
missing actual staffing, and a Saturday PM visit on the final project row.
These deliberately incomplete records are planning Drafts, never dispatch approval.

| Check | Result | Conditions/evidence |
| --- | --- | --- |
| Locked frontend install, format, TypeScript/Vite build | PASS | npm ci, Prettier, tsc --noEmit and Vite production bundle; lockfiles unchanged |
| Frontend regression | PASS |42 tests,0 failures;7 new pure Locate tests: ID/status/date guards, local year/leap/DST boundaries, compatible filters, real feedback, internal scroll geometry and overlapping timer/cleanup |
| Browser interaction scenarios | PASS |10 scenario groups with current production frontend and actual packaged FastAPI/SQLite through a local test-only IPC proxy; distinct IDs, hidden far row, preserved compatible filters, Crew Board→Job Schedule, detail/search sources, cross-year week, repeated cues, focus, timed clear, reduced motion, cancelled stale source, no Locate writes, Draft collision correction/create/edit/reload/cancel, publish gate and no console exceptions |
| Review action visibility/narrow layout | PASS |1440/768/480/390px; Locate remains visible, exact target receives cue, no document horizontal overflow |
| Native Windows compiled Tauri client | PASS (scoped) | Windows host, release EXE and matching packaged sidecar, real Rust IPC, isolated synthetic profile via existing smoke-data environment variable; physical mouse/keyboard through Computer Use. Review Locate reached AM ID1; Tab/Enter opened same-day PM ID2 detail; detail Locate reached ID2; Ctrl+K/search/Enter crossed to ID55 on2027-01-02 PM in week2026-12-27–2027-01-02, internal scrollTop1522, exact focused ID. Source closed on Locate. Native observed cue intervals2003/1974/1988ms (50ms polling plus screenshot overhead), focus retained after clearing |
| Native source/highlight/cleared screenshots | PASS | Saved locally only. `native-source.png`, `native-highlight.png`, `native-cleared.png` under ignored Locate evidence directory. They capture actual native WebView content, excluding OS frame; Computer Use also inspected the OS-framed window. Originals/prototype images are not product evidence |
| Native reduced-motion / all filter permutations / Draft CRUD | NOT RUN | Those interactions were exercised in browser proxy; native default-motion review/detail/search/focus paths were exercised as stated above. Native restart retained the synthetic database; no native installer/upgrade acceptance claimed |
| Python locked restore/lint/format/full regression | PASS | uv sync --locked --group bundle, Ruff check/format;266 tests,0 failures, including packaged-sidecar cases |
| Packaged Windows sidecar | PASS | PyInstaller build and separate11-test sidecar rerun,0 failures; loopback authentication and persistence |
| Rust locked fetch/format/release build/tests | PASS | Toolchain1.95.0;8 tests,0 failures; native release client built with --no-bundle |
| Historical .NET locked restore/format/Release build/tests | PASS |35 tests (16 Domain,2 Application,17 Infrastructure),0 failures |
| Synthetic acceptance harness | PASS | Windows PowerShell5 via powershell.exe; shared deadlines, failure handling and logical SQLite snapshots. This is a harness test, not an offline installation |
| Staged privacy scan / final Windows CI | NOT RUN at initial evidence commit | Record exact commit/run results in PR and Issue16 before delivery |
| Disconnected installation/upgrade, fresh device, human Demo B/E | NOT RUN | Host networking active; no NIC-disconnected run, installer acceptance, customer acceptance or production approval |

The sandbox initially blocked Chrome/sidecar startup and MSBuild named pipes;
authorized reruns outside that process sandbox passed. One initial browser
startup failed to attach; rerun passed. Initial geometry assertions incorrectly
required horizontal scrolling in a wide viewport, and an old active-tab selector
was corrected in the local test harness. The default PowerShell7 harness run
failed its integrity subprocess check; the workflow-prescribed Windows
PowerShell5 run passed. Rebuilding while the previous client was open hit a file
lock; closing that client and rebuilding succeeded. No unrelated process was
terminated to obtain these results.

Native candidate SHA256:
`1c2329fb8b3dc90cc4b5112867f10cce8777da5ad720a6c3ec43d7160339f9ca`.
Matching sidecar SHA256:
`4bc3ea647041269fda59bc9ad6edae100fa0fc753034115564b6a453874bf3c8`.
Builds/screenshots/raw logs/databases remain on the authorized local machine;
no binaries or original designs are committed or released.

## Reproduction and remaining scope

1. On a synthetic Windows profile create two saved visits for one Project/date,
   AM and PM, plus a late-week visit on a far Project row and a different week.
   Leave calendars/staffing unconfigured to produce honest Pending feedback.
2. Restrict Crew/Project filters to a different saved visit. Open Review & Publish;
   Locate the hidden visit. Verify the selected date becomes its week Sunday,
   1 Week is visible, only blocking filters clear, and exact ID/button is focused.
3. Repeat with compatible filters, same-day AM/PM, detail Locate and Ctrl+K
   Schedule search across New Year. Observe a second Locate replacing the cue
   and removal about two seconds after the last target. Check reduced motion.
4. Keep a review entry open while cancelling its record in the synthetic service;
   Locate must give recovery feedback, remove its stale card and issue no write.
5. Correct a real Crew collision in Draft editor, save, edit, reload and cancel.
   Publish and formal export must remain unavailable. Customer review is separate.

No database migration, backend contract, dependency, Tauri command or Draft write
behavior changed. Resource checks remain separate and incomplete at this UI gate.
Issue16 stays Open pending remaining board/exception flows and human acceptance.
Owner's next priority is automatic scheduling UI, then version rollback and
employee calendar export. Issue45 remains separate. No #28 UI fallback was
implemented because Locate was still missing at the baseline.
