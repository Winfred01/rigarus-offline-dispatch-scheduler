# Issue111 / #24 — Actual daily Rig safety

## Design Compliance Checklist

November25,2026 inspection, PUBLIC Winfred01/rigarus-offline-dispatch-scheduler.
Latest fetched main `afcb504a80eb77962d1f221316893d991b3c76d8`, human merge110;
exact-head PR110 CI121 passed, merge CI45558589366 initially running. No Open PRs
or110 review submissions. Branch codex/daily-rig-validation in isolated worktree;
root README/local design changes preserved. #24/#99/child111 and milestone5 M4
People, drivers and rigs Open. #9 inventory/#23 driver/#25 actual members reused.

Required sources all exist/readable and reread at November25 06:10–06:20 UTC.
Checkout timestamps are observation, not decision authority.

| Source | Declared identity / revision | Modified UTC | Sections read |
| --- | --- | --- | --- |
| AGENTS / DEV-DESIGN-CHECKLIST | Mandatory Design-First /d3b9bea |06:10:53 checkout | Instructions/template |
|00-PROJECT-PLAN.md | November2026 repository summary /4734a38 |06:10:53 | Daily2C3, scope/milestone/priority3, Option C |
|09-DELIVERY-PLAYBOOK.md | November2026 repository summary /4734a38 |06:10:53 | Resource previews, engineering/Demo/production gates |
|02-ARCHITECTURE.md | Living architecture /4734a38 |06:10:53 | Actual-member/driver/capability read-only proposals |
|03-DATA-MODEL.md | SQLite /4734a38 |06:10:53 | Schema16/history/recovery and Rig inventory/default link |
|05-DEMO-ACCEPTANCE.md | Living acceptance /4734a38 |06:10:53 | Daily capability and remaining actual Rig/consent |
|10-CLIENT-DECISIONS.md | Register /c9f9801 |06:10:53 | Daily actual-resource scope, Rig defaults, driver/category policy |
|acceptance/2026-11-25-daily-capabilities.md | Engineering /4734a38 |06:10:53 |558 regressions, false flags, resource limitations |
| Local UI design Updated2026-11-24.docx | SHA256 d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c | November24 23:15:38.7114232 | L14/L20 actual resources, L21 maintenance text |

DOCX XML text inspected; no original image/page/screenshot claim. Backend-only,
no UI layout/focus/keyboard states; N/A. Original stays local. Half-day captions
remain historical under owner daily decision. Missing sources: none for this scope.

| Requirement / authority | Existing implementation | Planned acceptance |
| --- | --- | --- |
| Confirmed owner November25 / #24 T04/T05 actual daily Rig | Inventory only, default Crew has no dated eligibility | Explicit original/actual allocation, same-date cross-Crew conflict and SQL concurrency guards |
| Confirmed no repair/inspection/inactive pass | Master Active only, no dated condition evidence | Independent dated conditions; all overlapping active conditions block, missing operational proof Pending |
| Confirmed swaps proposals only | Pure driver/capability previews | Detached original/default/actual/proposed distinction, no write, before/after and reasoned exclusion |
| Confirmed coherent snapshot/Stale/closed writes | Schema16/v4 query-only budgeted view | New17 sources and v5 SHA in same transaction, no initialization on read |
| Historical Issue default fallback versus latest no actual-Rig inference | DefaultCrewId master link only | Latest owner rules prevail: defaults are suggestions, never actual capacity/qualification |
| Open driver vehicle-category/legal/inspection policy | Rig.Type free text, generic company driver proof | Category eligibility remains Pending, no type-to-license inference or automatic due-date rules |

## Implementation Plan (before product code)

1. Commit plan and owner scope. Additive schema17 four tables: immutable Rig
   allocation identity (day or legacy visit), allocation changes with dated
   assignment context/revision/original/actual Rig/operational confirmation and
   native condition revision; independent Rig condition-period identity and
   immutable dated Active/Cancelled changes (Maintenance/Inspection/OutOfService).
   No old values/IDs/Slot/history/notes/revisions/FKs changed. Independent overlapping
   periods remain blocking until individually cancelled/corrected; a readiness
   assertion cannot clear them. No business defaults or actual vehicle inference.
2. SQL views expose current allocation/visit context and conservative occupancy.
   Any recorded old half occupies its complete date for new daily safety. Cancelled
   visits release capacity; stale allocations reserve recorded/current dates until
   reviewed, and cannot supply positive readiness. Cross-Crew occupancy guards
   protect allocation writes and saved visit move/restore, not just Python checks.
   Same-Crew legacy halves may retain the same Rig; no Crew invariant weakened.
3. Internal stores only, BEGIN IMMEDIATE expected assignment/allocation/period
   revisions, explicit company/reference and full-date operational confirmation
   for new days; legacy observation is explicitly partial. All history/identity
   immutable, save/no-op/failure rollback. Original Rig remains distinct from
   current actual Rig. Native condition changes invalidate prior readiness even
   outside the query horizon; master Active false always blocks. No API/UI writer.
4. Extend pre-DDL verified backup prefix through16, incremental rollback/retry/
   idempotence and actual16 prior-binary independent recovery; never delete live
   migration history. Read-only snapshots never migrate a profile.
5. Pure indexed whole-date Rig validator: known same Rig/different Crew collision
   Blocked, other-Crew unknown allocation Pending, known condition/master negative
   Blocked, absent/full-date/stale operational evidence Pending. Keep all IDs,
   periods/original/actual/default locators and reasons. Generic driver pass never
   proves selected vehicle-category qualification; category gate stays Pending.
6. Daily query proposed_rig_ids captures explicit additional nominees without
   allocation. Read all related allocation/period/master/default observations and
   native revisions using the same pinned query-only view, row/byte/deadline budgets;
   v5 SHA256/Current-Stale bind consumed sources. Legacy adapter refuses daily Rig
   evidence. Defaults never select actual/proposed Rig automatically.
7. Detached candidate Rig choices reuse prior capability/driver/borrowed-worker
   validation and comparator states; independent saved-visit swap preview checks
   exact source assignment/allocation revisions and before/after without writes.
   Explicit date/operational planning confirmation is input, never assumed. Source
   original/actual history remains visible; no reservation/Apply/Publish/export.
8. Synthetic pure/SQL/concurrency/context move/legacy/stale/budget/no-I/O/no-writes
   tests, reproducible example, full locked Python/sidecar/frontend/Rust/.NET,
   PowerShell harness/privacy/docs, exact-head Windows CI. Initial results NOT RUN.

One Draft PR for111. All overall validation Pending / Apply=false / Publish=false,
production daily gates closed. Follow #27 actual-worker consent, then daily UI,
visible preview/manual Apply, version history and PDF/Excel. No automatic merge,
Release, Issue closure, actual customer database or original-data upload. Customer
Demo D/E/UAT and production acceptance remain separate and pending.
