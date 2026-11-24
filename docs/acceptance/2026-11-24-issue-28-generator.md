# Issue #28 phase two — automatic date generation engineering evidence

Base main `ca503e135d0788aee1c8bf23cf843c92e1204a2f` includes human-merged PR91
(`cbd7b06`). Main CI run 45419720452 was independently checked completed/success.
Design-first commit `c24d88f` preceded product edits and records the source
revisions/hashes and owner-confirmed G1–G3. See the
[checklist and plan](../design/2026-11-24-issue-28-generator-checklist.md).
Branch `codex/issue-28-date-generator`; Issue #28 remains Open / Demo E pending.

## Delivered internal interface

`GenerationRequest` requires stable option/WorkItem/parent Project/Crew IDs,
required Crew count, Remaining Half-days (or explicit None), strict operator
confirmation bool, earliest date, inclusive horizon, and immutable Crew/Project
`WorkCalendar`s. Optional `CrewOccupancySnapshot` explicitly declares its complete
covered range; absent/out-of-coverage occupancy is Pending, not free.
Per-slot `ProposedSlot` / `ConstraintEvidence` inputs are scoped to that request.
Wrong context, duplicate cells/slots/evidence, invalid counts/dates/IDs, mutable
input shapes and out-of-range snapshots reject with ValueError.

`generate_candidate(request)` indexes snapshots and enumerates each local date,
AM then PM, using the existing #26 calendar assessment. Both Working is required.
Calendar Unknown/NotWorking/conflict, known occupied Crew slots, supplied Blocked
resource evidence and weekends without exact-slot Satisfied consent are skipped
and explained. Other missing resource checks remain Pending for planning only.
Accumulate without resetting across gaps; stop at confirmed Remaining or horizon.
No estimate, Draft visit or historic progress inference changes remaining work.

Results retain IDs, proposed first/last DateSlot, accumulated slots and counts,
unfilled work, scanned/skipped assessments/reasons, calendar match/conflict/
unknown/blocked counts and missing/pending check explanations. Calendar counts
cover scanned slots only, not unvisited dates after completion; counts may overlap.
Multi-Crew/missing or unconfirmed duration returns Needs Review without scanning.
Insufficient capacity has partial slots and unfilled amount, no finish and no
complete option. A partial first slot is an explanatory start, never completion.

`generate_and_compare(work_item_id, project_id, requests, max_options=..., order=...)`
generates one earliest plan per scenario, validates same requirement and consistent
overlapping shared Project calendars, passes only complete `ExplicitOption`s to
PR91 `compare_explicit_options`, and retains incomplete diagnostics separately.
Default EarliestFinish uses finish/start/Crew ID/option ID; EarliestStart reverses
the first two. Return 1–10 ranked options from at most 100 supplied scenarios.
These are alternative plans, not joint Crew reservations or an exhaustive search.

The inclusive horizon ends before the next annual anniversary, clamping Feb29
to Feb28, and never exceeds 366 dates / 732 slots. Near year 9999 no overflow is
attempted. Indexed scan is linear in bounded input; canonical comparator sorting
is O(H log H). Calendar/occupancy checks cannot be overridden by evidence entries.
No clock/file/network/SQL, dependency, schema/migration, API/Tauri/UI, write,
actual-worker selection, Apply or Publish path is added. All flags remain
`validation_status=Pending`, `applyable=false`, `publishable=false`, including
all-supplied-Satisfied cases.

## Reproduce and actual synthetic dates

From `src/Rigarus.Backend`, Python 3.13 / pinned uv 0.10.12:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -v
uv run --locked python -m rigarus_backend.recommendation_example
```

Actual output: C1 starts **2026-11-23 AM**, accumulates Mon AM, Wed PM, Thu AM,
Fri PM, finishes **2026-11-27 PM**, 4/4. C2 starts **2026-11-24 AM**, accumulates
Tue AM/PM and Wed AM/PM, finishes **2026-11-25 PM**, 4/4. EarliestFinish=C2,C1;
EarliestStart=C1,C2. Every skip and pending safety check is printed. A separate
test supplies blocked Rig evidence for faster C3, leaving no completed ranked C3.
The example is a console engineering preview, not an installed product workflow.

## Actual local verification (Windows developer host)

| Check | Result / scope |
| --- | --- |
| Locked Python restore | PASS, existing lock unchanged; uv 0.10.12, Python 3.13.7 |
| Ruff check / format | PASS, 56 Python files |
| Full Python regression | PASS, 156 tests, including 27 new generator/example/SQLite cases; 40.933 s |
| Windows sidecar build | PASS, locked PyInstaller 6.22.3; compatibility build, generator not connected to packaged app |
| Packaged sidecar regression | PASS, all 11 authenticated loopback/persistence/restart/upgrade cases; 39.512 s |
| Frontend locked install / format / tests / build | PASS, npm ci; Prettier; 35 tests; TypeScript/Vite build |
| Rust locked fetch / format / Release tests | PASS, Rust 1.95.0; 8 tests; Windows release compilation |
| Historical .NET locked restore / format / Release build / tests | PASS, SDK 10.0.100; 35 tests (2 Application + 16 Domain + 17 Infrastructure); 0 build warnings/errors |
| Acceptance-tool harness | PASS, Windows PowerShell 5.1 synthetic deadline/failure/UIA/WAL/consistent-snapshot harness; not a native app pass |
| Staged privacy / whitespace / documentation links | PASS; 251 indexed paths; intended source/docs only; changed links/fences resolve |
| Current feature-head Windows CI | Pending before push/PR; final PR and Issue comment record current-head run/jobs/artifact result |
| New native GUI / disconnected install / upgrade / reboot | NOT RUN; no new connected UI workflow; historical package PASS not reused |
| Customer Demo E / UAT | NOT RUN; owner development confirmation is not customer acceptance |
| Production | NOT APPROVED |

The first restricted TestClient invocation stalled and was stopped. The isolated
authorized full run then completed with all tests; no compatibility case was
silently skipped. First focused run exposed a test-fixture duplicate option ID
masking its intended context error; corrected to unique IDs before the full pass.
Initial local .NET execution could not use its default CLI home; the configured
local CLI-home rerun passed all required stages. No product workaround was used.
Host is Windows 11 build 26200 with developer tools; network was connected for
dependency/GitHub work. I/O guards prove pure computation does not call those
services, not that a new native installer was verified on a disconnected PC.

## Required scenarios

| Scenario | Actual result |
| --- | --- |
| Four consecutive half-days | PASS; Nov23 AM → Nov24 PM, exact four generated slots |
| Nonconsecutive Mon/Wed/Thu/Fri | PASS; 4/4, Fri PM finish, Tuesday closure and other skips retained |
| All unavailable / Unknown | PASS; Needs Review, no start/finish when empty, no ranked completion |
| Nine Crew/Project state pairs | PASS; closure blocks, explicit conflict explained, unknown not accumulated |
| Weekend absent/Pending/Blocked consent | PASS; skipped, no shorter finish; supplied Satisfied still cannot enable Apply/Publish |
| Existing Crew occupancy | PASS; occupied slot skipped even for same work; uncovered range remains Pending |
| Civil/Tower / Project identity | PASS; independent WorkItem IDs, same inherited parent, mixed-context comparison rejected |
| Multi-Crew | PASS; Needs Review, no simplified single-Crew completion |
| Missing/unconfirmed Remaining | PASS; no scan, no estimate fallback |
| Cross-year / leap / spring and autumn DST / date.max | PASS; local dates identical under three TZ settings |
| Twelve-month boundary / insufficient horizon / final PM | PASS; 732-slot leap-year scan bounded, no fabricated completion, no scan beyond finish |
| Dual sort / stable permutations / 100 scenarios | PASS; C2,C1 vs C1,C2; stable ties, limit omission count |
| Every supplied resource block | PASS; known hard blocks skipped, later safe slots used, absent other checks Pending |
| SQLite logical immutability | PASS; whole synthetic iterdump before/after equal; saved assignment/staffing/employee/calendar IDs and values unchanged, integrity ok / FK empty |
| No I/O / clock / immutable inputs / complexity | PASS; open/os.open/socket/SQL/time guards; exactly 732 constant-size assessments at maximum empty horizon |
| Invalid dates / duplicate slots / IDs / ranges / requirements | PASS; explicit errors; inconsistent shared Project snapshots rejected |
| Independent seeded oracle | PASS; 50 deterministic calendar cases agree on accumulated slots, shortage and finish |

## Remaining before operational automatic scheduling

- A read-only production adapter must resolve WorkItem.ProjectId and current
  required Crew count, obtain operator confirmation of Remaining, snapshot
  Crew/Project/occupancy and bind all evidence to actual workers/Rig/revisions.
- #15 employee and actual Rig collision validation; #23 recognized drivers per
  actual slot and source-Crew borrowing impact; #25 type/minimum staffing/skills/
  verified qualifications/Foreman; #24 dated actual Rig/maintenance/swaps;
  #27 actual-worker consent and stale-approval invalidation remain incomplete.
  Evidence enums are not those validators, and availability is not eligibility.
- #18/#29 revision-aware preview/locks/revalidation/transaction Apply/audit,
  operator UI, immutable Published snapshots and customer acceptance remain.
- Joint multi-Crew work, cross-WorkItem dependencies, progress deduction and
  global optimization require separate confirmed contracts and slices.

PUBLIC GitHub receives only synthetic source and sanitized records. Updated
original planning files, full UI DOCX, DBs/raw logs remain local. No automatic
merge, Issue closure, Release, installer publication or real-data modification.
