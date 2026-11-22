# Issue 16: consecutive saved visits

Engineering verification, November 22, 2026. Refs #16. Baseline `e10c0c4cf30ea756f9c6083eb3059de446e35db6` includes merged #73 desktop shell and #74 weekly/offline acceptance; this slice does not recreate them. Design sources and decisions are recorded in [the checklist](../design/2026-11-22-issue-16-multiday-checklist.md). Original DOCX and all raw diagnostics, database copies, VM disks, screenshots and local paths remain on the authorized workstation. Every fixture is synthetic.

## Result and scope

Job Schedule and Crew Board display adjacent complete saved AM/PM dates as one strip when WorkItem, Project, Crew and exact notes match. Each AM/PM remains its original keyboard-accessible Draft button, with its own ID, revision and existing detail/editor/cancel command. Editing one note splits the strip; restoring it reforms the strip. Cancelling one source releases only that slot; saving its replacement reforms the strip with a new ID. Missing shifts, empty dates and parallel project rows stay independent; no inferred duration, estimated-work deduction or new domain rule is introduced.

Files: `week-cells.ts` adds the pure projection; `schedule.tsx` and `desktop.css` render it; `week-cells.test.mjs` covers boundaries/identity; `Test-TauriDesktop.ps1 -IncludeMultiDay` adds native regression coverage and implies the existing assignments scenario. No schema, migration, backend/API, dependency, publish gate or actual-staffing change. Home roster/default Rig remain reference data. Formal Publish/export remain blocked for the specific missing checks and immutable snapshot described in the existing UI.

## Candidate identity and conditions

Local working-tree build on the recorded main baseline, branch `codex/issue-16-multiday-board`. Version stays 0.1.0. EXE SHA-256 `2bbd798071c0ea3256fb5cd7a4b8b925e6c93e7ea3c33e47d0f911e824054084`; NSIS setup SHA-256 `1b770a5f4155d4b5ab215876a8b17661caa035ce9121d73b11ba98b0e54e0788`. The frozen tested executable is the one packaged by this setup. Backend and bundled sidecar source are unchanged from main. Local install media has a per-file manifest; it is not a GitHub Release or signed production distribution.

Developer host: Windows 11, networking active, SDKs and WebView2 preinstalled. The native verifier launches this packaged executable with a separate synthetic profile, uses Windows UI Automation and existing Tauri/FastAPI/SQLite commands, normally closes the window/sidecar and reopens the application. It does not use browser IPC stubs. Browser visual tests run separately through a loopback test-only IPC proxy to the real packaged backend and a separate synthetic database; those checks do not prove native/offline behavior.

## Executed checks

| Check | Result | Evidence / practical coverage |
| --- | --- | --- |
| Locked frontend install, format, TypeScript and Vite | PASS | `npm ci --offline` with locked cache; `npm run format`, `npm run build` |
| Frontend tests | PASS, 30 | Existing 22 plus 8 projection cases: gaps, same-day AM/PM, cross-year/weekend, exact identity/notes, parallel jobs, cancel/edit, week clipping and 14-source full week; no input mutation |
| Backend locked sync, Ruff check/format, unittest | PASS, 68 | `uv sync --locked --group bundle`; existing domain, SQLite, API/conflict and revision checks |
| Frozen packaged sidecar | PASS, 8 | Existing executable contract suite against the matching unchanged backend bundle |
| Rust locked restore, format, Windows build/test | PASS, 6 | Existing Rust integration/lifecycle tests |
| .NET compatibility locked restore, format, Windows Release build/test | PASS, 35 | Historical baseline only; no WPF UI feature added; zero build warnings/errors |
| NSIS Windows setup build | PASS | `npm run tauri -- build -- --locked`; candidate hashes above |
| Native host final serialized smoke | PASS, 69.981 s | Original weekly suite plus multi-day source IDs 5/6/7/8, individual note edit/restore, cancel 6, replacement 9, both boards, nine-Crew sticky scroll, normal exit/reopen and startup-error feedback |
| Independent SQLite inspection after native lifecycle | PASS | Integrity `ok`, no foreign-key errors; 7 Draft/2 Cancelled, IDs/revisions/notes retained; cancelled 6 is not replaced in place |
| Browser interactions and keyboard | PASS | Civil/Tower strips, 15 source visits, parallel/missing shifts, Enter opens the selected PM source, independent edit/cancel, reload and slot reuse with new ID |
| Responsive/visual checks | PASS | 1600/768/480/390 CSS px, no document overflow or console errors; inspector at 1600/768/390 returned 0 FAIL/0 WARN with documented reference-design label/edge exceptions |
| Staged privacy scan and diff checks | PASS | `git diff --cached --check`; repository staged scan passed for 190 tracked/staged paths; raw evidence remains local |
| Windows CI for this PR head | PENDING | Will be linked after branch push |
| Independent no-NIC installed candidate | IN PROGRESS | Separate copy-on-write clone of synthetic #74 guest, no original guest writes; result recorded separately below |

The first development native run timed out waiting for a strip because one automated note input committed an extra trailing character. Read-only SQLite inspection confirmed that the grouping correctly refused unequal notes. The verifier now observes two exact committed values before Save; it does not retry writes. The subsequent development native run passed in 38.917 s. The first final-candidate attempt timed out at the existing foreground-owned date-segment guard while browser testing also ran. No guard was weakened; a serialized retry passed in 69.981 s. Both unsuccessful runs and their synthetic profiles are retained locally. This is an automation timing/focus limitation, not evidence of unconditional reliability.

## Actual screenshots and comparison

Local screenshot index uses original design numbers. Actual packaged Windows WebView client images: UI 01 Job Schedule across Dec 31, 2027 / Jan 1, 2028; UI 13 the same saved strip on Crew Board; UI 14 the fully reachable last of nine Crews; UI 06 source Draft #9 detail; UI 44 Settings; UI 47 contextual Help. They exclude the OS frame and retain real Rust IPC. Capture uses an isolated SQLite backup of the passing native profile; it performs no domain writes. Its CDP close request did not close the OS window; a checked normal Windows `CloseMainWindow` then succeeded. Native lifecycle acceptance comes from the separate passing UIA run, not that CDP close request.

Separate browser screenshots document UI 05 strip restoration, UI 07 split after one-source note edit, UI 08 split after cancellation and Civil/Tower/parallel examples. They are labelled browser checks in the local gallery. Compared with original UI 01/13, the continuous multi-date visual and fixed date/roster alignment are implemented; AM/PM source buttons deliberately expose the actual stored granularity. UI 02/09/10 and UI 40–47 original shell/tool behavior and test evidence are in the merged #73 acceptance record; the wider offline weekly baseline is in #74. Those older hashes do not certify this changed candidate.

## Remaining scope and approval

Human Demo B/client acceptance and production approval: NOT RUN. Missing-WebView2/fresh-device prerequisite and signed production release: NOT RUN. Full prototype HTML/ZIP visual reconciliation: NOT RUN, files absent from supplied design inventory; accessible original DOCX figures were used. Partial-day and overlapping project rows intentionally keep independent cards. No drag/drop, automatic duration, actual personnel assignment or formal publication/export is added. Follow-up panels remain #22, #45, #71, #17 and #32; existing supported commands remain available. #16 remains open for human review. Do not merge, close issues or publish a Release automatically.
