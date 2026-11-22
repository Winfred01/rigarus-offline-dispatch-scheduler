# Issue #14 manual Draft Assignment Design-First checklist

## Issue and baseline

- Issue #14, M2 / Demo B, explicitly prioritized by the owner. Isolated branch `codex/issue-14-manual-draft`, baseline `069e6b38cdbbc228b9630c18c9f1acf594309e67`. Root main checkout and unrelated worktrees were preserved. Repository currently PUBLIC.
- PR #70 was manually merged; no open PRs at inspection. Main CI run `44982588774` succeeded on this baseline. Project/WorkItem, Crew/Employee/Rig and Foreman master data are present in code. Open Issue numbers do not imply their merged engineering slices are absent. Customer Demo acceptance remains separate.
- Re-read current #14, #16 and #22, including their November 21 priority sequence: #14 persistence/API → #16 weekly board → bounded #22 roster visualization → later hard safety/actual membership gates. No existing assignment schema/API/UI was found.

## Design Compliance Checklist

The sources were read again before implementation; metadata below records the baseline versions and checkout times. Markdown sources have no separate release-version header; Git revisions identify their inspected version. Plans declare a November 2026 baseline. Full metadata/read timestamps and exact local-only source location are retained locally.

| Source | Exists/read | Baseline Git revision | Checkout mtime UTC | Relevant sections |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | Yes | `d3b9bea77852` | 2026-11-22T04:01:41.851436+00:00 | Mandatory Design-First workflow |
| `docs/00-PROJECT-PLAN.md` | Yes | `cc9613a61a09` | 2026-11-22T04:01:41.853438+00:00 | Scope / M2 / Option C |
| `docs/09-DELIVERY-PLAYBOOK.md` | Yes | `e6326dff3c75` | 2026-11-22T04:01:41.856433+00:00 | Engineering, Demo and production gates |
| `docs/02-ARCHITECTURE.md` | Yes | `6d2fbeb28613` | 2026-11-22T04:01:41.854435+00:00 | Tauri migration / local authenticated service |
| `docs/03-DATA-MODEL.md` | Yes | `06c37b12211f` | 2026-11-22T04:01:41.854435+00:00 | Project master / resources / Foreman history / migration check |
| `docs/05-DEMO-ACCEPTANCE.md` | Yes | `06c37b12211f` | 2026-11-22T04:01:41.855435+00:00 | Project/Crew/Foreman walkthrough and bounded native/offline conditions |
| `docs/10-CLIENT-DECISIONS.md` | Yes | `06c37b12211f` | 2026-11-22T04:01:41.856433+00:00 | Proposed AM/PM; open staffing, driver, weekend and remaining-work rules |

Original accessible source: `Rigarus_UI_Design_Updated_2026-11-21.docx`, declared November 21 update, SHA-256 `e2f91d38a5e31869183b7eda1e1a213103cf4962631818bd1bb074e4886c4664`, mtime UTC 2026-11-21T17:37:32.442670+00:00. Fresh OOXML extraction, original embedded Figure 1 (Schedule) and Figure 2 (Projects) inspected. Relevant locators: P018/P027 Project and WorkItems; P041–P086 Schedule / Assign Work Item / Draft; P091–P108 visual layout and details; P159 provisional AM/PM. These are concept figures, not implemented screenshots. Pagination was not independently rendered; no page number is invented. Full original and images remain local under owner instruction.

| Requirement | Authority / current baseline | Implementation and acceptance |
| --- | --- | --- |
| Stable WorkItem/Crew/local date/AM-PM Draft | Owner request and current #14 priority; absent at baseline | Additive migration/API/bridge/UI; same WorkItem multiple visits and Civil/Tower independence |
| Provisional AM/PM | Owner approves development use; customer decision still Proposed | Label in form/list; no hourly boundary or final customer approval claim; leap/cross-year/timezone tests |
| Crew-slot conflict | Explicit requested test and #14 conflict-safe slice | Partial unique index + transaction; actionable 409; concurrent create/edit tests |
| Form Cancel vs saved cancellation | Owner requires no-write cancel and API cancellation | Form Cancel sends no mutation; saved cancellation is confirmed, retains ID/notes, releases unique slot |
| Validation pending; no publication | Explicit owner request / #14/#16/#22 | Constant Pending/false API response, DB Draft/Cancelled only, no publish endpoint or Tauri command, disabled UI |
| Projects Assign entry / save location | Figure 2 and P027/P082; existing Projects details have three data columns | Add nonsortable Action; preselect exact WorkItem ID; after save show and focus persisted Crew/date/slot record |
| Seven-day/sticky/roster visual grid | Figure 1 and #16, deliberately separate next PR | NOT IMPLEMENTED here; range/crew-filter API ready for #16; current page honestly displays persisted per-date Draft list |
| Time off, actual workers, transfers, driver/Rig eligibility | #22 A/B and future safety gates; absent | NOT IMPLEMENTED; do not infer off days or approved drivers from roster/master fields |
| Existing SQLite data / notes | Plan/data model; six migrations in baseline | Preserve Projects/WorkItems/resources/demo note/Foreman history; rollback, packaged six-schema upgrade and older-backend rejection/backup tests |

## Implementation Plan

- `assignments.py`: pure canonical calendar date, AM/PM draft model, stable integer IDs, revision conflict rule. No timezone conversion, staffing/type eligibility, duration completion or remaining-day calculation.
- `storage.py`: seventh migration `20261122040000_AddDraftAssignments`; FK-linked stable row, Draft/Cancelled, notes, revision/UTC audit timestamps; partial unique Crew/date/slot index plus range/WorkItem indexes. All prior schemas remain unchanged.
- `assignment_store.py` / `assignment_api.py`: deterministic range/crew reads, get/create/update/cancel, atomic writes, strict inputs and sanitized 404/422/409/503. Cancelled rows retained; no hard-delete or publish route. Current labels are joins, not published snapshots.
- Tauri `main.rs` / `sidecar.rs`: list/read/save/cancel through existing token-authenticated loopback process. Reuse URL query-pair encoding under existing locked dependencies; test cross-year filters and query injection boundaries.
- React `assignment-fields.ts` / `schedule.tsx`, `main.tsx`, `projects.tsx`, scoped CSS: actual persistent Schedule list and Assign editor, per-WorkItem Project action; exact ID/crew/date/slot; loading/empty/invalid/collision/stale/error/unknown/success/cancel states. No writable Publish.
- Keyboard/focus: focus editor, preserve correction input, allow no-write Cancel, restore entry/reload focus, focus saved location after range data arrives. Narrow forms wrap; table scrolls within frame; dates remain intact.
- Failure behavior: known Crew-slot rejection permits correction; stale or uncertain write requires reload using the entered local date. A known committed mutation followed by failed read reports saved/cancelled and clears stale rows before refresh.
- Tests: domain/calendar/timezone, strict API, repeated visits, concurrency/revision/cancel, FK/unique/DB state invariants, rollback/retry, six-schema packaged upgrade, sidecar auth/restart; native Windows, isolated offline VM, actual React + packaged API/SQLite through test-only IPC proxy; screenshot comparison, historical .NET, CI and privacy.
- Compatibility: earlier Tauri backend rejects schema 7; fallback requires a verified consistent original backup and compatible build. Never edit operational migration history. Published snapshots/versions/locks, full undo/audit, backup/restore and production upgrade remain future gates.

## Design differences, results and remaining work

The owner explicitly requested the first persistence/manual-entry slice. Figure 1's seven-day board is reserved for #16; Figure 2's broader customer/report fields and consolidated Resources shell are not invented here. The existing application typography/colors are preserved. Full UI DOCX publication is not authorized. Customer granularity and business-rule decisions remain pending.

See the [engineering record](../acceptance/2026-11-21-issue-14-manual-draft.md) and final Draft PR verification for actual commands/results, hashes and CI. Cases remain NOT RUN until their recorded execution; browser proxy checks do not replace native Rust/offline evidence. Manual assistive-technology, customer Demo B, new installer/managed-device acceptance and production approval are separate. No automatic merge, Issue closure, release or customer database modification.
