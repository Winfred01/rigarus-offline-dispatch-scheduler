# Issue103 — Daily recommendation engine and coherent snapshot (slice2B)

Baseline main `d281ff78feb52681ad77970a1884a1c036586780`, human merge PR102.
Branch `codex/day-recommendation-snapshot`; pre-code design commit `65f63c1`.
See [source inventory/plan](../design/2026-11-24-day-recommendations-checklist.md),
[decision](../10-CLIENT-DECISIONS.md) and
[synthetic reproduction](../../samples/synthetic-only/day-recommendations.md).
Engineering scope is backend algorithms/read-only snapshots; no desktop cutover.

## Delivered contracts and algorithm

- Reuse independent `ConfirmedRemainingDays(days, confirmed_by_operator)` from
  slice1. Strict positive integer/explicit True only. DayRecommendationQuery and
  DayGenerationRequest accept that object or missing None, never half-day counts.
  Missing/multi-Crew is Needs Review; no estimate fallback or visit deduction.
- Actual local whole-date scan across nonworking gaps, bounded before annual
  anniversary and at most366 dates. Both Crew/parent Project must be explicitly
  current Working. Unknown/closed/conflicting/stale review, known occupancy/
  blockers and unapproved weekends skip with reasons. Unknown occupancy coverage
  also skips; absent evidence is not known free. Other resources stay Pending.
- Return actual allocated dates, confirmed/accumulated/unfilled days, proposed
  start/finish, per-date skipped/source states/reasons, calendar counters and
  missing checks. Partial plans retain dates/deficit but no finish/ranked option.
- PR91 shared constraint/rank engine now supports true full-date contracts;
  hard filter before limit, EarliestFinish default/EarliestStart alternate,
  Crew/option-ID stable ties. No fake AM/PM representation of a Full Day.
- Dedicated schema14 mode=ro/query-only snapshot includes schema13 day Drafts,
  current immutable members, all-Crew legacy visits/current staffing, actual
  WorkItem parent, selected Crew/Foreman/master data, related daily employee
  availability/raw old evidence and old driver/capability/qualification sources.
  All helper reads share the same pinned connection; frozen DTOs/canonical JSON
  are detached before calculation. Home Crew/Foreman is never attendance.
- Any active old half or new day Draft blocks the Crew's whole date; Cancelled
  remains observational history and frees capacity. Distinct ID namespaces
  survive equal integer IDs. No saved work is deducted from confirmed days.
- Format `rigarus-day-recommendation-input-v1`: SHA256 of canonical logical query,
  confirmation/days/bounds/sort/limit, opaque normalized source scope, migrations,
  metadata, daily/raw old cells/revisions/receipts, visits/members and related
  resources. Same-query re-read gives Current/Stale; no DB/WAL byte digest.
  Relevant old/new calendar, visit, staffing and evidence changes cannot remain
  Current. Missing/moved target Stale; storage/schema/read errors propagate.
- Shared100,000-unit materialization/projection budget,30-second SQL progress/end
  deadline,5-second busy wait, no partial snapshot/fingerprint on failure. OS/native
  calls still need an independent caller watchdog; no hard real-time claim.
- Every proposal/comparison/snapshot/wrapper stays Validation Pending, false
  Apply/Publish. Current is equality at read time, not approval or a lock.
  Existing production daily-input/day-Draft writes remain default closed.

## Actual local checks

Windows developer host; networking active; all profiles/records synthetic.
Python3.13.7, existing locked uv bundle (27 installed packages), Node22,
Rust1.95.0/.NET10. Raw diagnostics/DBs remain ignored local files.

| Check | Actual result |
| --- | --- |
| Locked Python restore/Ruff check/format | PASS;88 Python files |
| Full backend | PASS **364**, no skips (324 baseline +13 pure day +27 adapter cases) |
| Packaged Windows sidecar | PASS **13** existing authenticated/gated/restart tests; repeated source-sidecar coverage |
| Frontend locked restore/Prettier/tests/TypeScript/Vite | PASS **42**, zero npm audit findings at execution |
| Locked Rustfmt/fetch/Windows Tauri no-bundle release build/Rust tests | PASS **8** |
| Historical .NET locked restore/format/Windows build/tests | PASS **35** (16+2+17) |
| Synthetic SQLite console example | PASS; two opposite sort orders,4-day gap completion, Current→Stale after edit |
| New migration | N/A; current14 consumed read-only; existing migration/preservation/rollback regressions included in full suite |
| Synthetic PowerShell acceptance harness | PASS on connected developer host; synthetic protocol/failure/wait controls, not native/offline acceptance |
| Staged privacy/diff/Markdown links | PASS;303 indexed paths, clean staged diff,9 affected UTF-8 Markdown sources/fences/local links |
| Exact-head Windows CI, three jobs, installer/kit build/upload | NOT RUN before push; final PR records actual run/head/job outcomes |
| Production daily-input/day-Draft write rollout | BLOCKED intentionally pending visible daily UI/review and complete resource integration; gates tested closed |
| Native day GUI/Locate/no-AM-PM editing, disconnected install/upgrade/reboot/clean-device, customer Demo E/UAT/production acceptance | NOT RUN; no UI or installation executed, networking active |

Distinct tests **449** (=364+42+8+35). Packaged13 repeat existing tests and are
not added as new distinct coverage. Synthetic example/harness are additional
checks, not counted as unit tests. Packaged-sidecar regression verifies current
API compatibility/gates; it does not expose/run a new recommendation API or GUI.

## Focused acceptance evidence

Pure13 cases group: continuous4 days; Monday/Wednesday/Thursday/Friday across
Tuesday closure; all closed/Unknown/partial deficit; either calendar close/stale;
occupied/missing/partial occupancy; exact-date weekend proof; known blocked Rig
input and missing checks; multi-Crew/missing/invalid/unconfirmed/fractional/bool
duration; two sorts/ties/limit/incomplete; hard exclusion with complete supplied
checks still Pending; cross-year/leap/DST/0001/9999/annual boundary; invalid IDs/
dates/duplicate evidence/context/shared parent; deterministic frozen no file/
socket/SQL/system-time dependence.

SQLite27 cases group: real daily inputs/two sorts;4-day gap; full-date Draft and
cancellation/no deduction; any old half and equal IDs in separate namespaces;
other-Crew explicit staffing/borrowing and daily/raw old availability; old positive
pairs/mixed evidence not promoted; old calendar edits invalidate receipts; daily
Unknown tombstones; related daily/old availability changes Stale; old/new visits/
other-Crew members change Stale; unversioned metadata/old policy/driver change
Stale; missing/multi-Crew/inactive/type/parent review; Civil/Tower independent IDs
inherit parent; logical no-write/deep immutability/replay; pinned old view during
later multi-source commits;15 concurrent atomic writer states/15 snapshots never
mix metadata; unrelated scope/checkpoint Current, observed-owner conservative
out-of-range revision Stale; read-only write rejection/closed handles/budget;
deadline/projection quota/sanitized errors; old/future/missing/corrupt sources;
inconsistent day/legacy context and unencodable storage fail without fingerprint;
strict day query; production gate/no route; missing/moved-target Stale; weekend
calendars do not imply actual worker consent.

Initial focused tests used a nonexistent driver helper name/old positional
signature; corrected to DriverApprovalStore + DriverApprovalDraft. The deliberate
rejected-write connection probe started an implicit SQLite transaction; the test
now rolls that probe back before handing the connection to the actual reader.
No product constraint was relaxed. First full363 passed; added malformed stored
text sanitization plus a new regression, targeted27 and final364 passed.
Initial restore ran at repository root rather than backend; corrected working
directory and locked restore passed. No dependency/lock changes.

## Scope and next PRs

Changed core: day_recommendation_generator.py, day_recommendation_adapter.py,
day_recommendation_example.py and PR91 recommendation_comparison.py; two new test
modules; decision/design/architecture/data/acceptance/playbook/plan and synthetic
example documents. No DB schema, UI, Rust command, HTTP recommendation route,
actual proposed worker/Rig selection, stored-Draft edit or automatic conversion.
Historical half-day modules/tests remain compatibility-only; new query rejects
their duration contracts. No source/customer data/DB/raw log/original design uploaded.

Next: daily #15 actual-member collisions, whole-day #23 company driver and #25
minimum/skills/qualification evidence; actual #24 Rig/maintenance/inspection and
#27 actual-worker consent; then visible daily UI/Locate/native offline acceptance.
#18/#29 must preview/lock/revalidate in the write transaction before manual Apply
and audit. Historical conversion/reconciliation and company policies remain
operator/customer decisions. Do not infer production readiness from backend/CI.
Keep103/99/28 and dependencies Open; Draft PR/human review only, no merge/Release.
