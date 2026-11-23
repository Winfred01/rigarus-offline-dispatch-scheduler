# Issue #26 — calendar model engineering evidence

Client date November 23, 2026, America/Toronto. Baseline main `9ae4161ee99c19cb31be477325a7036641c5988b`. See [the Design-First source record and plan](../design/2026-11-23-issue-26-calendar-checklist.md). This owner-approved first slice adds a pure calculation model and tests only; calendar entry, persistence and recommendation integration remain deferred. No installation or native GUI feature is delivered.

## Reproduce

Use Windows x64 with Python 3.13 and uv 0.10.12. From `src/Rigarus.Backend` run:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -p test_work_calendars.py -v
uv run --locked python -m unittest discover -s tests -v
```

Create separate `WorkCalendar("Crew", crew_id, cells)` and `WorkCalendar("WorkItem", work_item_id, cells)` snapshots using `WorkCalendarCell(local_date, "AM" or "PM", "Working" / "NotWorking" / "Unknown")`. Pass a read-only `AssignmentDraft` to `assess_draft_calendar`, or use `assess_calendar_range` for up to 366 inclusive dates. Missing cells remain Unknown. Results contain date/slot/IDs, both source states, deterministic status and structured reasons. There is no HTTP/Tauri command or app entry point for this model yet.

## Actual scope and results

| Case | Status | Evidence / limits |
| --- | --- | --- |
| Locked backend dependency restoration | PASS | `uv sync --locked --group bundle`; existing lock unchanged, Python 3.13.7. Initial sandbox DNS failure was resolved through authorized host execution |
| Ruff lint and format | PASS | `ruff check`, `ruff format --check`; 47 Python files formatted |
| Targeted new model and compatibility suite | PASS | 12 tests, 0.395 seconds on Windows development host |
| All nine Crew/WorkItem state pairs | PASS | Only Working/Working Matched; known NotWorking Blocked, otherwise Unknown Pending; explicit opposite states add CALENDAR_CONFLICT; both sources retained |
| No workweek/holiday/availability inference | PASS | Empty weekday/weekend/holiday stays Unknown; existing employee Available does not fill either calendar |
| AM/PM, stable IDs, Crew isolation, duplicate rejection | PASS | Wrong scope/ID and invalid cells reject; duplicate input never silently overwrites; known closure and unknown coexist in explanation |
| Cross-year, leap day, DST and end-of-calendar bounds | PASS | Inclusive ordinal-date ranges across spring/fall DST dates; identical outputs under different process TZ environment values; maximum 9999-12-31 supported. Does not claim native OS timezone reconfiguration |
| Weekend match and safety separation | PASS | Explicit Working/Working weekend remains pending consent; every assessment remains Validation pending / unpublishable. Driver, personnel and actual Rig checks are not implemented or certified here |
| Pure read-only and synthetic SQLite compatibility | PASS | File/socket/SQL creation forbidden during model calls; full logical SQLite snapshot/visit unchanged, integrity ok, foreign-key errors zero; existing Unverified driver preserved |
| Full backend regression | PASS | 104 tests in 35.323 seconds, including the 12 new tests and existing FastAPI/SQLite/sidecar tests |
| Windows sidecar build | PASS | Existing `scripts/Build-RigarusSidecar.ps1`, locked uv bundle group / PyInstaller 6.22.3, Windows x64 |
| Packaged sidecar regression | PASS | 10 existing loopback/auth/lifecycle/persistence tests in 16.131 seconds against the just-built Windows sidecar |
| Documentation links/fences and sanitized locators | PASS | Five changed Markdown files scanned; no missing local targets or unbalanced code fences |
| Staged whitespace/privacy | PASS | `git diff --cached --check`; `scripts/Test-RepositoryPrivacy.ps1` passed for 223 indexed paths; seven intended changed paths only |
| Current-branch Windows CI | NOT RUN | Starts after Draft PR creation; report its actual head/jobs separately from main CI |
| Native GUI, offline installation, upgrade and reboot | NOT RUN (not applicable) | No connected UI, API or schema change. Pure-model no-I/O test is not native/offline installation acceptance |
| Customer Demo E / production approval | NOT RUN / NOT GRANTED | Human review and client acceptance remain separate |

Raw logs, original UI DOCX/images, metadata and test databases remain local. Developer-host connectivity was active; no claim of a disconnected GUI run. Sandbox execution first encountered cache permissions and then a TestClient stall; host execution is used for full process/loopback checks. These infrastructure attempts do not constitute product defects or passing tests.

## Compatibility and remaining work

No SQLite migration/table/index/history, prior stable ID/note, dependency lock, FastAPI route, Tauri command or saved Draft validation rule is changed. The calculation uses only caller-supplied immutable snapshots and never writes. It cannot reserve capacity, create a candidate, change an assignment, approve a weekend or publish anything. Existing customer databases were not opened or changed.

Full #26 remains incomplete: calendar entry/persistence/history and approved exceptions/override UX are deferred, as are full M3/M4 dependencies. #27 must track actual-worker weekend consent; #28 must hard-filter personnel conflicts, qualified drivers, skills and actual Rig availability independently before suggesting feasible schedules; #29 must preserve locks, cancel without writes and revalidate at explicit Apply. Calendar Matched is never a substitute for those gates.

Draft PR for human review only. No auto merge, Issue closure or Release. Final commands, CI run/job URLs and unresolved gates are attached to that PR.
