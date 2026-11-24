# Issue #28 — explicit-option comparison engineering record

Baseline main `f48f55961fb888391f5b5af51c128d08a710d203`, isolated
`codex/issue-28-explainable-candidates`. See the [Design-First source inventory,
requirements and plan](../design/2026-11-23-issue-28-comparison-checklist.md).
This is a source-level pure Python foundation. No automatic date allocator,
actual safety validators, HTTP/Tauri/UI connection or user-facing recommendation
feature is claimed.

## Reproduce

From `src/Rigarus.Backend`, with Python 3.13 and the repository's pinned uv:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -p test_recommendation_comparison.py -v
uv run --locked python -m unittest discover -s tests -v
```

The synthetic C1 plan starts November 23 AM and ends November 25 PM with four
unplanned half-days inside; C2 starts November 24 AM and ends the same PM; C3
ends earlier but has a supplied Rig-conflict block. Expected earliest-finish
C2,C1; earliest-start C1,C2. C3 is excluded before the result limit, and every
reason retains date/slot/check/state/source. The raw gap count does not declare
nonworking periods, duration correctness, continuity policy or a score weight.

Other checks exercise every independent gate, late-slot conflicts, missing
evidence, pending/blocked weekend consent, permutations, local AM/PM/date
boundaries, immutable bounded input and wrong Project/WorkItem context. Missing
does not turn into Satisfied; neither all supplied satisfied evidence nor
availability produces a confirmed recommendation, Apply or publication.

The compatibility test creates a real synthetic Draft using the existing
FastAPI/SQLite fixture, compares its read-only proposed option, then checks the
whole logical SQLite snapshot, saved visit/IDs/notes, integrity and foreign keys.
No migration or schema/history rewrite is required. No real database is opened.

## Actual results at source snapshot

| Check | Status / scope |
| --- | --- |
| Locked restore | PASS, existing lockfile and dependency versions |
| Initial focused suite | PASS, 18 tests including synthetic HTTP/SQLite compatibility |
| Final full backend suite | PASS, 129 tests, including all 18 new comparison/compatibility cases |
| Ruff check/format | PASS, 53 Python files |
| Windows Python sidecar build | PASS, existing locked PyInstaller build; new internal comparator is not connected to the packaged app |
| Staged privacy / whitespace | PASS, 246 indexed paths; six intended changed files |
| Packaged-sidecar compatibility | PASS, all 11 existing authenticated loopback/persistence/startup/upgrade cases against the new local Windows sidecar |
| Current-head Windows CI | Pending at commit-time snapshot; final PR update records actual outcome |
| New native/offline UI, install, upgrade, reboot | NOT RUN / not applicable to unconnected comparison-only core |
| Customer Demo E / UAT | NOT RUN |
| Production | NOT APPROVED |

The restricted local TestClient run stalled at the compatibility case after all
pure cases passed. It was stopped and rerun through the existing authorized
local execution path with independent 180s focused / 600s full bounds: focused
completed in under a second and full in about 37s. This is not a product defect
or a silent skipped test. Raw outputs and exact timings remain local. The
canonical native GUI results from PR90 do not certify this source revision.

## Unmet requirements

- Automatic allocation from remaining half-days, Crew/employee dates, gap rules
  and multi-Crew duration; owner clarification pending.
- Real trusted context/revision adapters and personnel/driver/skill/Foreman/
  staffing/actual Rig/weekend checks. The enum inputs model evidence, not the
  implementation of those business validators.
- Feasible/confirmed candidate certification, weights, UI comparison, Apply,
  locks/revalidation/publication and a native customer workflow. Proposed date
  bounds are not verified completion of work. All flags remain Pending/false.

Raw logs, diagnostics, original design, DBs and local paths stay local. PUBLIC
GitHub receives synthetic code and this sanitized evidence only. One Draft PR
for human review; no automatic merge, Issue closure or Release.
