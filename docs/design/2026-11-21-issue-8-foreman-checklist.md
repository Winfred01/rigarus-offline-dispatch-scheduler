# Issue #8 Foreman master-data Design-First checklist

## Issue and baseline

- Issue #8, M1; remaining Foreman appointment/history vertical slice. Baseline `7c91c2a7f94d63faf387c64f1518c8ea3d0933e3` (latest fetched main). Repository currently PUBLIC. No open PRs at preflight. Latest main Windows CI run `44949432528` succeeded. Earlier Crew PR #54 and Employee PR #59 were merged; Rig #9, import #11 and backup design #10 already have engineering evidence. #41 customer acceptance remains pending.

- Reuse isolated `codex/issue-8-crew-roster`; fast-forwarded clean worktree from `b4e8b05` to main. Original main changes and other worktrees preserved.
- Owner approved the exact bounded Foreman proposal in this session (November 21 local / November 22 UTC). This is development authority, not customer acceptance. No M2 scheduling, M4 qualification or M7 restore implementation.

## Design Compliance Checklist

Required sources re-read in this session; source metadata refreshed at 2026-11-22T03:10Z. Last-changing Git commits below refer to baseline documents before this slice. Checkout timestamps are filesystem facts, not decision authority. These Markdown sources have no independent release-version header; the last-changing Git revision identifies their inspected version. The declared original plan/playbook baseline is November 2026; the UI source explicitly declares its November 21 update.

| Source | Exists/read | Baseline revision | Checkout mtime UTC | Relevant section |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | Yes | `d3b9bea77852` | 2026-11-22T03:05:03.432256+00:00 | Mandatory Design-First workflow |
| `docs/00-PROJECT-PLAN.md` | Yes | `cc9613a61a09` | 2026-11-15T03:13:06.283487+00:00 | Milestones / Crew and Employee model |
| `docs/09-DELIVERY-PLAYBOOK.md` | Yes | `e6326dff3c75` | 2026-11-15T03:13:06.286486+00:00 | Demo A / Demo D / delivery and privacy gates |
| `docs/02-ARCHITECTURE.md` | Yes | `6d2fbeb28613` | 2026-11-15T03:13:06.284487+00:00 | Tauri migration |
| `docs/03-DATA-MODEL.md` | Yes | `fdef9abea7cf` | 2026-11-22T03:05:03.434258+00:00 | Crew roster / Employee roster / migration check |
| `docs/05-DEMO-ACCEPTANCE.md` | Yes | `55b960d7cadf` | 2026-11-22T03:05:03.434258+00:00 | Crew and Employee engineering checks / Demo A |
| `docs/10-CLIENT-DECISIONS.md` | Yes | `471c89dabd6b` | 2026-11-22T03:05:03.435258+00:00 | Employee Home Crew / qualification and Foreman replacement questions |

Original local-only `Rigarus_UI_Design_Updated_2026-11-21.docx`: declared update November 21; SHA-256 `e2f91d38a5e31869183b7eda1e1a213103cf4962631818bd1bb074e4886c4664`; 7,094,076 bytes; mtime UTC 2026-11-21T17:37:32.442670+00:00. Read OOXML text and inspected original embedded Figure 1, with sections 页面导航 / Resources and Schedule 显示规则与交互 / Crew 和 Rig 标题及组员名单 (paragraph locators P011, P101–104). No verified pagination is claimed. The original figure is a concept, not implemented UI evidence. It shows Foreman first/bold, but no Resources appointment editor detail. Full source, extracted figure and exact machine location remain local. The owner-approved workflow extends the existing Crews form rather than inventing a Schedule page.

| Requirement | Authority / implementation baseline | Change and acceptance case |
| --- | --- | --- |
| Optional single current Foreman per Crew | Owner confirmed in this session; missing in baseline | Crews action/editor; appoint, replace, clear, reopen |
| Active and Foreman eligible for new appointment | Owner confirmed; eligibility flag already exists | Validate inside write transaction; reject missing/inactive/ineligible IDs |
| Cross-Home-Crew appointment preserves Home Crew | Owner confirmed; required HomeCrew FK preserved | Assign from another Crew, compare employee records and driver status |
| Immutable recorded history and retained IDs | Issue #8 and owner confirmed; stable IDs already exist | Append with name snapshots, FK restrictions, reject UPDATE/DELETE, restart |
| Employee later inactive/ineligible | Owner-approved retention; no automatic dispatch approval | Current warning, old name snapshots unchanged; clear/replace explicitly |
| Staffing, cross-Crew exclusivity, effective dating | Open Demo D / #25; out of scope | No new staffing or dispatch constraints; timestamps are recording time only |
| GUI shell vs concept | Existing app uses separate resource entries; no detailed editor in DOCX | Preserve current shell and styles; intentional difference, not full Schedule conformance |

## Implementation Plan

- Python: new `foremen.py`, `foreman_store.py`, `foreman_api.py`; register routes in `api.py`. GET/PUT `/crews/{id}/foreman`; strict nullable `employee_id`, required nonnegative `expected_revision`; 404/422/409/503 sanitized errors. One consistent read transaction, one BEGIN IMMEDIATE write transaction. Stale writes fail; same-choice save at matching revision creates no event.
- SQLite `storage.py`: sixth migration `20261122030000_AddForemanHistory`, append table + Crew/Employee FKs + Crew/ID index + update/delete protection triggers. Preserve existing schemas/records. Forced post-DDL migration failure rolls back and retries. Earlier apps require original consistent backup for fallback; no operational downgrade mutation.
- Tauri `main.rs`/`sidecar.rs`: read/save commands through existing authenticated sidecar with bounded HTTP lifecycle.
- React `foreman-editor.tsx`, `roster.tsx`: one Foreman action per Crew; optional choice, current status, read-only newest-first history; loading/empty/no-candidate/save/load/conflict states. Failure preserves selection and requires explicit reload, which warns of discarded selection. Back cancels unsaved choice and restores row-button focus. Keep established Segoe UI/teal shell; scoped styles contain long names and history scrolling at narrow width. `employees.tsx` gains stable existing-select IDs for native tests.
- Tests: backend lifecycle/strict validation/concurrency/snapshots/foreign keys/insert rollback/migration rollback; packaged sidecar token/restart; bounded `Test-TauriDesktop.ps1 -IncludeForemen` (also Crew smoke); browser actual React state checks and 1440/768/390 comparison; historical .NET regression; format/privacy; Windows CI.
- Risks: migration is forward-only; actual scheduling policy remains open; browser mock IPC does not prove database behavior; native candidate test is distinct from installer/customer acceptance.

## Acceptance cases and actual results

Results are recorded in the [engineering evidence](../acceptance/2026-11-21-issue-8-foreman-history.md). Until recorded there, cases are NOT RUN. Customer Demo A/D, managed-device acceptance and production approval remain pending. No merge, release, Issue closure or real customer database edits are authorized by this checklist.
