# Issue105 — Daily personnel conflicts and explicit candidate checks (2C1)

Baseline main `98eacce9a2767b958133a7e6750af2215988ec40`, human merge PR104.
Branch `codex/daily-personnel-conflicts`; pre-code plan commit `2437a81`.
[Design/source inventory](../design/2026-11-24-daily-personnel-checklist.md),
[owner decision](../10-CLIENT-DECISIONS.md),
[reproduction](../../samples/synthetic-only/daily-personnel.md).
Scope is #15 daily personnel only, not complete2C/dispatch or UI delivery.

## Delivered behavior

- Pure daily_personnel_conflicts validator groups explicit actual workers by
  local date/Employee ID. Different Crews Blocked, with every namespaced record ID,
  revision, WorkItem/Project/Crew and raw legacy slot. Any old AM/PM participates;
  opposite legacy halves in different Crews conflict under the new daily rule.
  Old records/history and the old half-day validator's semantics are unchanged.
- Cancelled retains identity and frees capacity. Latest members replace history;
  no Home Crew/Foreman/Available attendance or default worker selection. Existing
  Crew day/slot overlap invariants are preserved, invalid duplicate inputs reject.
- Empty/unconfigured/incomplete staffing Pending; unknown other-Crew staffing
  on that date prevents false clear checks. Known conflict stays Blocked even
  with other missing evidence. Collision Satisfied is not dispatch eligibility.
- Day snapshot recommendations include a saved-only personnel report. Unstaffed
  date candidates retain PersonnelConflicts Pending, no inherited saved pass.
- Optional proposed_employee_ids captures explicit additional people in the same
  pinned query-only transaction, including unused employees from other Home Crews;
  metadata/daily/raw availability and old resources are observations, not staffing.
- Daily snapshot format v2/SHA256 includes that query scope and source data.
  Rebuild v1 proofs; old/new staffing, visits, employee and availability changes
  expire prior results. Source errors never fabricate Current or an empty safe view.
- Detached explicit candidate checker verifies exact plan/context by regeneration,
  accepts immutable per-date members, rejects duplicates/out-of-plan context,
  and keeps uncaptured/missing people Pending. It compares one alternative against
  all saved current visits. PR91 excludes Blocked candidates before limiting.
  Unrelated saved conflicts remain visible separately from candidate-specific state.
- Borrowing never removes source members. Known original dated references carry
  mandatory Pending driver/minimum/skills/qualification/availability rechecks.
  Markers identify known overlaps, not an exhaustive transfer workflow. Later
  #23/#25 must validate all affected source/destination actual Crews after changes;
  #18/#29 must preserve before/after context and transactionally revalidate/audit.
- Separate proposal SHA256 binds input fingerprint, exact candidate and normalized
  member choices. Freshness re-reads the original query; Current is scoped equality
  then, not authentication/lock/approval. Changed choice means a new proposal proof.
- All root plans/reports remain Validation Pending / Apply=false / Publish=false.
  No migration/UI/Rust/HTTP/write-gate change, automatic worker transfer, resource
  safety certification, Apply/Publish/export, historical conversion or customer DB.

## Actual local checks

Windows developer host, networking active, only synthetic temporary profiles.
Python3.13.7/locked bundle (27 installed packages), Node22, Rust1.95.0/.NET10.
Raw diagnostics/DBs/backups/binaries remain ignored local evidence.

| Check | Actual result |
| --- | --- |
| Locked Python restore/Ruff check/format | PASS;92 Python files |
| Full backend | PASS **394**, no skips;364 baseline +13 pure daily +17 SQLite/candidate cases |
| Actual packaged sidecar build/tests | PASS **13** existing authenticated/gated/restart tests; repeated source-sidecar coverage |
| Frontend locked npm ci/Prettier/tests/TypeScript/Vite | PASS **42** |
| Historical .NET locked restore/format/Windows build/tests | PASS **35** (16+2+17) |
| Locked Rustfmt/fetch/Tauri Windows no-bundle build/Rust tests | PASS **8** |
| Synthetic SQLite/personnel console example | PASS; unstaffed Pending, source-occupied Blocked/excluded, separate worker collision-clear but full Pending/false flags |
| New migration | N/A; schema14 unchanged; all prior migration/preservation/rollback tests retained in full suite |
| Synthetic PowerShell harness | PASS on connected developer host; synthetic controls, not native/offline acceptance |
| Staged privacy/diff/Markdown links | PASS;310 indexed paths, clean staged diff,9 affected UTF-8 sources/fences/local links |
| Exact-head Windows CI/installer/kit build/upload | NOT RUN before push; final Draft PR records actual head/run/jobs |
| Production daily-input/day-Draft write rollout | BLOCKED intentionally; default closed and tested; later visible UI/resource integration required |
| Native daily GUI/Locate, disconnected installation/upgrade/reboot/clean-device, customer Demo B/D/E/UAT/production approval | NOT RUN; no GUI or installation executed, networking active |

Distinct executed regression inventory:479
(394+42+8+35). Packaged13 repeat source-sidecar tests and are not additional
distinct coverage. Synthetic example/harness are extra checks, not unit counts.
Packaged checks establish existing API/restart/gate compatibility, not a new
personnel recommendation HTTP/GUI workflow.

## Focused evidence

Pure13 grouped cases: full-day cross-Crew actual people; old AM/PM versus day,
equal IDs in different namespaces; old opposite halves/new daily versus unchanged
old half-day rule; same Crew old halves/independent days/workers;3+ Crews/multiple
people/all references; Cancelled retained/released; empty/missing/incomplete/no
active Pending; unknown other-Crew same date versus another date; known conflict
despite unknown/incomplete data; existing Crew occupancy/duplicate-current-record
invariants; strict IDs/dates/revision/member/status/raw-slot scope; shuffled stable
frozen/no file/socket/SQL/system-time computation; cross-year/leap/DST/year9999,
dense100-Crew/20-worker grouping and1000 unconfigured Crews, workload bounds.
Unknown-Crew checking uses constant-time set size/membership, avoiding repeated
set copies; deterministic grouping/sorting is O((V+M) log(V+M)), storage O(V+M).

SQLite/candidate17 grouped cases: saved day/day report/default unstaffed Pending;
day/old PM equal-ID namespaces; cancellation/latest staffing/history retention;
same-view explicit extra employees/daily availability/no attendance; unstaffed,
empty/uncaptured members never pass; source borrowing Blocked/no removal with
Pending driver/minimum/skills/qualifications rechecks; old opposite half sources
and PM cannot be ignored; other-Crew unknown Pending; unrelated saved conflict
visible without inventing candidate membership; strict exact-plan/date/context;
normalized query/proposal SHA256; staff/visit/cancel/extra employee old and daily
availability/master changes Stale; frozen pure detached checks/logical no-writes;
pinned extra employee/staffing read stays complete old view during concurrent
changes then Stale; limits/sanitized source errors; both production gates/no new API.

Targeted13+17 and prior day-adapter27 passed before the full394. No failing new
test required a product rule relaxation. Code review found a per-visit unknown-
Crew set copy that would scale poorly; replaced with size/membership lookup and
verified a1000-unknown-Crew case within the existing pure boundary test.

## Next required work

1. Whole-day #23 actual company-approved driver, #25 staffing/levels/separate
   qualifications, using complete dated evidence and all affected source/destination
   actual membership. Old half-day proof never automatically certifies a full day.
2. Actual Rig #24 occupancy/maintenance/inspection, then actual-worker #27 consent.
3. Daily UI/review/Locate and native/offline acceptance; #18/#29 Preview/locks/
   transactional revalidation/manual Apply/audit. No automatic production writes.

Human review only; keep105/15/99/28 and dependencies Open, no merge or Release.
Customer terminology, historical reconciliation, approval authority and business
thresholds remain designated owner/customer decisions, not defaults from tests.
