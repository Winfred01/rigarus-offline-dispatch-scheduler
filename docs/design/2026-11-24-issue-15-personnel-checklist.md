# Issue #15 — explicit employee AM/PM collision validator

## Baseline

2026-11-24, PUBLIC repository verified. Latest fetched main/current commit
`90d5454b5aec6f722bbb841be24139d9100ff924` includes human-merged PR94
(head fd08485). No Open PR or submitted PR94 reviews. Issue15 Open, M2 / Demo B;
read its scope, dependencies #8/#9/manual assignments and publishing hard gate.
Preserve root README, Chinese README and local designs; isolated branch/worktree
`codex/issue-15-personnel-collisions`. Owner's current request approves employee
cross-Crew collisions first, with #23/#25/#24/#27 and #18/#29 in later slices.

## Design Compliance Checklist

| Source | Exists/readable | Declared version | Last-changing revision | Checkout mtime UTC (not authority) | Read-at UTC |
| --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | Yes | November 2026 repository baseline | `d3b9bea778529c47bb502e59914cbdd0100697a0` | 2026-11-24T20:39:41.540727+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/DEV-DESIGN-CHECKLIST.md` | Yes | November 2026 repository baseline | `d3b9bea778529c47bb502e59914cbdd0100697a0` | 2026-11-24T20:39:41.549239+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/00-PROJECT-PLAN.md` | Yes | November 2026 repository baseline | `2a074876b0d8283578af7464a97ea12837c244d9` | 2026-11-24T20:39:41.542727+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/09-DELIVERY-PLAYBOOK.md` | Yes | November 2026 repository baseline | `2a074876b0d8283578af7464a97ea12837c244d9` | 2026-11-24T20:39:41.547241+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/02-ARCHITECTURE.md` | Yes | November 2026 repository baseline | `850e840ab7c57d4189097a7779aa4119d93fe0bb` | 2026-11-24T20:39:41.543727+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/03-DATA-MODEL.md` | Yes | November 2026 repository baseline | `850e840ab7c57d4189097a7779aa4119d93fe0bb` | 2026-11-24T20:39:41.544727+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/05-DEMO-ACCEPTANCE.md` | Yes | November 2026 repository baseline | `850e840ab7c57d4189097a7779aa4119d93fe0bb` | 2026-11-24T20:39:41.544727+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/10-CLIENT-DECISIONS.md` | Yes | November 2026 repository baseline | `850e840ab7c57d4189097a7779aa4119d93fe0bb` | 2026-11-24T20:39:41.548238+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/design/2026-11-24-issue-28-adapter-checklist.md` | Yes | November 2026 repository baseline | `fd084856bdcc5a1689fc58787e28234ae5d40c5b` | 2026-11-24T20:39:41.580339+00:00 | 2026-11-24T20:41:30.302132+00:00 |
| `docs/acceptance/2026-11-24-issue-28-adapter.md` | Yes | November 2026 repository baseline | `fd084856bdcc5a1689fc58787e28234ae5d40c5b` | 2026-11-24T20:39:41.565324+00:00 | 2026-11-24T20:41:30.302132+00:00 |

Latest accessible local UI original November22 DOCX: SHA256
`67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`;
mtime UTC 2026-11-22T08:14:42.434606+00:00.
Read `.//w:p` 85/109 (date/resource/affected assignments, hard publish gate),
238–246 (UI09/10 conflict/review concept), 277 (borrowing keeps Home Crew).
XML locators are not rendered pages; no original figures inspected. UI/API,
loading/keyboard/focus/ARIA/screenshot comparison are not applicable to this
pure backend/report slice. Full originals and exact local paths stay local.

Relevant sections: project Scope/Milestones; delivery Gates; architecture Draft,
explicit workers and consistent persisted inputs; data model active Crew slot
uniqueness/current staffing/history; acceptance #22/Employee Week/persisted
snapshot and consistent SQLite checks; decisions #14/#22 and G1–G3. Inspected
recommendation_adapter, assignment_store, staffing_store/persistence, staffing,
existing snapshot/generator/comparator tests and schema/migration contract.

| Requirement / authority | Existing / needed | Acceptance |
| --- | --- | --- |
| Confirmed owner / Issue15: same employee cannot work across Crews in same half | Actual saved workers exist; collision validator missing | Two/three Crews, several employees, borrowing, same/different dates and AM/PM |
| Confirmed: actual explicit staffing only | Existing latest configured change IDs; no Home Crew inference | Unconfigured/explicit empty remains Pending; no attendance from Foreman/Available |
| Confirmed: explain hard collisions | Return employee/date/half and exact Assignment/Crew/WorkItem/Project references | Deterministic complete conflict groups and per-visit Blocked |
| Confirmed: Cancelled releases capacity | Existing Draft/Cancelled contract | Ignore cancelled membership; preserve stable IDs/history |
| Confirmed: preserve Crew uniqueness | Existing unique active Crew/date/slot | Inconsistent duplicate active Crew-slot input rejected; no relaxation |
| Confirmed: combine with consistent snapshot | PR94 reads only selected Crew visits; insufficient for cross-Crew evidence | Add all-Crew/horizon staffing view in same read-only transaction, retain selected occupancy subset |
| Confirmed: detect source changes | Existing scoped fingerprint v1 | Bump input contract v2; include all horizon visits/staffing/related actual employees, including unselected Crews |
| Confirmed: missing is not success | New check states distinct from dispatch approval | Empty/unconfigured staffing Pending; populated conflict-free visit only Satisfied for this check |
| Confirmed: pure/read-only/offline | Core validator no DB/file/network/clock; adapter no writes | I/O guard, immutable/canonical replay, logical DB equality, WAL consistency, bounded errors |
| Confirmed: no automatic Apply/Publish | Existing dates have no explicit proposed workers | Saved-visit report stays separate; generated PersonnelConflicts remains Pending; all flags false |

No new driver/qualification/staffing minima/Rig/weekend standards are inferred.
Missing proposed membership blocks candidate safety certification, not this
independent saved-Draft detection. Issue15 remains partial because actual Rig
checks/UI/publish gate and customer acceptance are outside this slice.

## Implementation Plan (before product code)

1. Add pure personnel_conflicts.py: frozen explicit staffed-visit inputs, strict
   IDs/local dates/AM-PM/status/unique employee/visit/Crew-slot validation; bounded
   tuples and membership count. Index active memberships by date/half/Employee ID;
   multiple Crew IDs yield a complete sorted conflict group. Cancelled ignored.
   Per-visit check Blocked/Pending/Satisfied plus overall result, missing reasons,
   exact affected references. Empty/unconfigured/explicit-empty staffing cannot
   silently pass. Satisfied means only this bounded collision check, never safe
   dispatch; validation Pending / applyable=false / publishable=false always.
2. Extend RecommendationSnapshot with a required all-Crew personnel-assignment
   view in the same horizon/transaction. Existing selected assignments continue
   to feed only selected Crew occupancy; do not exclude target WorkItem visits.
   Read current staffing once per visit and related actual workers across all
   Crews. Preserve native assignment revisions/staffing change IDs. Bump FORMAT
   to v2 and fingerprint expanded logical scope; no fake global revision/byte hash.
   Reject malformed staffing source and bounded read failures, never fabricate
   an empty complete view. Existing 30s/5s/row limits and close policy retained.
3. Convert detached sources to pure inputs; expose validate_snapshot_personnel
   and attach saved-Draft report to PersistedRecommendations. Report scope is
   explicitly saved assignments/horizon, not proposed employees. No membership
   inference or PersonnelConflicts Satisfied evidence is fed to generated options.
4. Add pure unit tests and synthetic persisted integration: different Crews,
   WorkItems/Projects/types, multiple employees/three-way groups, cancel/clear/
   reconfirm/move and borrowing; stable permutations, wrong/duplicate/bounded
   input, leap/year/DST, I/O guards and immutable results; all-Crew outside filter,
   fingerprint staleness after other-Crew staffing changes, concurrent WAL old/new
   view, unchanged logical records and no extra database connection. Keep all
   existing core and adapter tests. No dependency/migration/HTTP/Tauri/UI change.
5. Record approved detection scope in decisions; update architecture/data/acceptance
   and sanitized evidence. Fingerprint v1 records must be rebuilt for expanded v2
   inputs; no on-disk migration/downgrade or persisted proposal rewrite. Future
   #18/#29 must acquire complete current proposed membership and revalidate within
   its own write transaction with locks, all resource gates, rollback and audit.
6. Run locked Python/Ruff/full regressions, sidecar build/packaged tests, frontend,
   Rust and historical .NET checks, staged privacy/docs and Windows CI. Native
   GUI/offline installation/upgrade/reboot NOT RUN (no connected new workflow).
7. One Draft PR refs15/94, update Issue15 and linked28 with exact results/limits;
   keep Issues open, human review, no merge/Release/customer DB/original uploads.

## Actual results

NOT RUN at this design commit. Customer Demo B/D/E and UAT NOT RUN;
production NOT APPROVED. Execution evidence will report actual gates separately.
