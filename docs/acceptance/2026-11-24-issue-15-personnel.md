# Issue #15 — saved-Draft employee collision engineering evidence

Main baseline `90d5454b5aec6f722bbb841be24139d9100ff924` includes human-merged
PR94. Latest main rechecked unchanged before delivery. Isolated branch
`codex/issue-15-personnel-collisions`; Design-First commit d50bbd5 preceded
product code. See [design/source inventory](../design/2026-11-24-issue-15-personnel-checklist.md).
Issue15 remains partial/Open: this is actual employee collision detection only.
PUBLIC repository; synthetic sources/sanitized evidence only.

## Contract and reproduction

Pure `validate_employee_conflicts(visits, start_date=..., end_date=...,
scope_complete=...)` takes immutable explicit staffed visits, not Home Crew
rosters. It groups active Draft memberships by local date, AM/PM and Employee ID.
Multiple Crew IDs produce one complete deterministic conflict group per worker/
half, with compact Assignment/Crew/WorkItem/Project references. Duplicate input,
invalid IDs/dates/status, duplicate active Crew-slot and workload/range violations
reject explicitly. Cancelled membership does not occupy capacity.

Per visit: known collision Blocked; missing/empty staffing or incomplete scope
Pending; otherwise Satisfied for this collision check alone. No active visits
means Pending. Known collisions remain visible in partial views. Every report
stays Validation pending / applyable=false / publishable=false.

Snapshot v2 reads all Crews' visits/current actual members in the same pinned
read-only transaction, even when only one Crew is requested for dates. Selected
occupancy remains a subset. Saved staffing context/revision is validated.
Global horizon assignments/current staffing/related actual employees enter the
fingerprint; unselected Crew changes make it Stale. Rebuild v1 inputs; no SQLite
migration. Existing logical comparison is retained, not a DB/WAL byte hash.
Source failures never produce an empty apparently complete report.

`validate_snapshot_personnel` converts detached sources;
`generate_from_persisted_snapshot(...).personnel_validation` exposes the report.
This report concerns saved Drafts. Generated dates have no actual proposed
membership and retain PersonnelConflicts Pending in PR91's comparator and the
pending-validator list. No successful saved-Draft check authorizes a proposal.

From src/Rigarus.Backend using Python3.13 / uv0.10.12:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -p "test_personnel*.py" -v
uv run --locked python -m unittest discover -s tests -q
```

Executed synthetic Store-backed fixture (the first integration test) selected
only Crew1 but staffed Employee1 on Assignment1/Crew1 and Assignment2/Crew2,
both WorkItem1/Project1 at 2026-11-23 AM. Actual result:

```text
state=Blocked; scope=SavedDraftAssignments
EMPLOYEE_DOUBLE_BOOKED employee=1 date=2026-11-23 half=AM
affected=(Assignment1,WorkItem1,Project1,Crew1),
         (Assignment2,WorkItem1,Project1,Crew2)
validation_status=Pending; applyable=false; publishable=false
```

## Scenario evidence

| Scenario | Actual result |
| --- | --- |
| Two/three Crews, several shared workers | PASS, complete groups and affected references, deterministic |
| Different dates/AM-PM/nonshared workers | PASS, independent; Satisfied collision check only |
| Empty/unconfigured/no active/incomplete scope | PASS, Pending; no roster/Available/Foreman inference |
| Cancel, clear, replace current membership; note edit; move | PASS, cancellation releases, latest event only, move requires reconfirmation |
| Civil/Tower, real distinct WorkItems/Projects, borrowing/inactive Crew | PASS, actual IDs/parent preserved and active Drafts count |
| Unselected Crew collision/change | PASS, all-Crew scope and Stale fingerprint |
| Malformed saved staffing context | PASS, DATABASE_INVALID before snapshot/fingerprint |
| Concurrent WAL writer | PASS, complete old snapshot then new conflict/fingerprint; no mixed view |
| Determinism/immutability/no file-SQL-network-clock core | PASS, patched I/O guards, canonical frozen outputs |
| SQLite immutability | PASS, entire logical dump equal; assignments/employees/calendars/history unchanged; integrity/FK checks |
| Invalid/duplicate/bounded input | PASS, explicit errors; no Crew-slot relaxation |
| Cross-year/leap/DST/weekends/date.max | PASS, local dates and AM/PM only; no weekend approval implied |
| Scale/independent oracle | PASS, 2,000 visits / 1,000 complete groups and 50 seeded independent comparisons |
| Existing date generator/comparator/adapter regressions | PASS, included in full backend suite |

## Actual gates

Connected Windows11 developer host build26200, synthetic temporary profiles only.
No customer database or original customer files opened/uploaded.

| Gate | Actual result |
| --- | --- |
| Python locked restore | PASS, uv0.10.12 / Python3.13.7; no dependency/lock change |
| Ruff check/format | PASS, 61 files |
| Backend | PASS, 208 tests in 56.914s, 27 new (16 pure + 11 persisted) |
| Sidecar | PASS, locked PyInstaller build and 11 packaged regression tests in 19.805s; internal validator has no UI route |
| Frontend | PASS, npm ci, Prettier, 35 tests, TypeScript/Vite build |
| Rust | PASS, 1.95.0 locked fetch/fmt/Windows Release compilation and 8 tests |
| Historical .NET | PASS, 10.0.100 locked restore/format/Release build, 35 tests (16 Domain / 2 Application / 17 Infrastructure) |
| Acceptance harness | PASS, Windows PowerShell synthetic controls; not a native GUI run |
| Staged privacy / whitespace / documentation | PASS, 260 indexed paths; intended source/sanitized docs only; changed-document links/fences and staged whitespace checked |
| Final-head Windows CI | Pending before push; final PR/Issue records exact SHA/run/jobs/artifact |
| Native GUI / disconnected install / upgrade / reboot | NOT RUN; no new UI/HTTP workflow, prior results not borrowed |
| Customer Demo B/D/E / UAT | NOT RUN |
| Production | NOT APPROVED |

No migration, dependency, UI, API, automatic save, Apply, Publish, employee
reassignment, existing Draft edit or published/history mutation is introduced.
Local detailed logs, temporary DBs and UI originals remain untracked.

## Remaining work

Actual proposed workers and their current availability/eligibility must be known
before a proposal can pass this check. Complete #23 approved drivers, #25 minimum
staffing/skills/qualifications, #24 actual Rig occupancy/maintenance and #27
actual-worker weekend consent with explicit evidence. Issue15 still needs its
remaining resource/UI/publish-gate scope. Then #18/#29 Preview, locks, complete
transactional revalidation, human Apply, rollback and audit; customer acceptance
remains separate. No merge, Issue closure, Release or production approval.
