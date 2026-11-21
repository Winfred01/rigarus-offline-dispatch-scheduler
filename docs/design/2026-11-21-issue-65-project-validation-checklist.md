# Issue 65 Design-First checklist

## Issue and current baseline

[Issue #65](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/65), M1 / Demo A: improve the existing New/Edit Project editor's validation and field help. Inspection began November 21, 2026 at 20:03 UTC. GitHub reports the repository **public**. The owner merged [PR #68](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/pull/68) at 20:00:15 UTC; its three Windows CI jobs passed, including artifact upload. Latest fetched main: `8219fe13f94866458f942ae2bd7e62f983abe2ff`. Independent branch: `codex/issue-65-project-validation`. Original main's README/design-folder changes and the previous mixed draft's staged files are preserved.

Read #65's body (updated 18:57:37 UTC), linked #7 (closed), #41/#42 (open), PR #68, current CI, editor, FastAPI models/routes/store and SQLite constraints. No open PR or actionable review existed at inspection. The earlier local count-validation candidate is partial work, not acceptance of the full Issue. Reuse its numeric helper/tests; do not copy unrelated bulk changes or reuse old results as current passes.

## Design Compliance Checklist

Sources were reopened this session at **20:04:38 UTC**. Revisions are last-changing commits; none declares an independent semantic version. Modification times are checkout observations, not authoring dates. Full hashes/read timestamps remain in local `source-versions.json`.

| Source read | Revision | Modification UTC, 2026-11-21 | Relevant sections |
| --- | --- | --- | --- |
| [Root instructions](../../AGENTS.md) | `d3b9bea` | 20:03:25.498 | Original safeguards and twelve Design-First rules |
| [Project plan](../00-PROJECT-PLAN.md) | `cc9613a` | 20:03:25.500 | Scope; M1 / Demo A |
| [Delivery playbook](../09-DELIVERY-PLAYBOOK.md) | `e6326df` | 20:03:25.503 | Gates; Demo evidence; human review |
| [Architecture](../02-ARCHITECTURE.md) | `6d2fbeb` | 20:03:25.501 | Tauri/React/FastAPI and legacy compatibility |
| [Data model](../03-DATA-MODEL.md) | `fdef9ab` | 20:03:25.501 | Project/work-item identity, quantities, SQLite |
| [Acceptance guide](../05-DEMO-ACCEPTANCE.md) | `5246914` | 20:03:25.502 | Project Master; sorting; Bulk Add regressions |
| [Client decisions](../10-CLIENT-DECISIONS.md) | `471c89d` | 20:03:25.503 | Open Site ID/Job # decisions; acceptance gates |
| [Checklist template](../DEV-DESIGN-CHECKLIST.md) | `d3b9bea` | 20:03:25.504 | Identity, authority, plan, evidence |
| [Prior clipboard evidence](../acceptance/2026-11-21-issue-45-excel-clipboard.md) | `5246914` | 20:03:25.506 | Delivered bulk/keyboard baseline and limitations |

### UI reference figures and source

The local-only `Rigarus_UI_Design_Updated_2026-11-21.docx` was accessible and reread, including **单项目录入：醒目校验与字段提示（新增设计 · 2026-11-21）**, subsections **视觉层级与操作路径 / 气泡与字段说明 / 校验行为与可访问性 / 未确认规则**, and original **Figure 2A**, visually inspected. The figure is a concept, not a GUI test. Pagination is unverified because no full-page renderer is available; use section/figure locators.

Source: 7,094,076 bytes; modified **2026-11-21 17:37:32.4426697 UTC**; SHA-256 `e2f91d38a5e31869183b7eda1e1a213103cf4962631818bd1bb074e4886c4664`. Use the dated title; its 2013 core dates/revision 1 are inconsistent generator defaults. The owner explicitly keeps the original local. `docs/design/Rigarus_UI_Design.docx` is absent by instruction, not a missing source on this machine. Another machine without the original must block dependent UI work. Exact machine paths, DOCX and extracted images stay local.

### Requirements and decision status

| Requirement | Authority / previous implementation | Planned acceptance |
| --- | --- | --- |
| Prominent title, grouped work items, primary Save, secondary Cancel, responsive labels | Confirmed #65 / Figure 2A; partial | Preserve shell, strengthen hierarchy; native and 1440/768/390 comparison |
| Field/row errors, actionable summary, first-invalid focus/scroll | Confirmed #65; one generic error previously | Stable item keys/control refs; independent correction, removal, offscreen focus, retained drafts |
| Six keyboard helps, Escape/Close, no overlap | Confirmed #65; missing | Native auto-popovers; Tab/Shift+Tab/Enter/Escape; one open at a time |
| Nonempty text/unique Job #, leading zeroes, Small/Civil/Tower/Other | Existing FastAPI/SQLite invariants; confirmed preservation | Reuse contracts, target duplicate to Job #, leave storage failures generic |
| Valid 2 crews / 4 half-days; 1 = 0.5 day, 4 = 2 days | Written correction overrides contradictory mockup | Never mark 2/4 red; test empty, zero, negative, fraction, overflow and valid bounds |
| Four-digit Site ID, alphanumeric/dash-only Job #, Small/Medium/Large | **Conflict / Open**: mockup contradicts written correction/code | No guessed format/enum. #41 owns business decisions; preserve existing Site ID nonempty rule |
| Atomic save, stable IDs, search and reopen | Existing implementation; confirmed preservation | Real SQLite contract regressions and bundled native reopen; no schema/API migration |
| Screen-reader usability / customer Demo | Human acceptance, separate from ARIA/UIA | Manual screen-reader review NOT RUN; automation is partial evidence |

## Implementation Plan

Output to the owner before product edits: extend existing `projects.tsx` and scoped `styles.css`; add text/count helpers and frontend tests; extend backend contract regressions and the bounded Windows UIA script; add checklist/acceptance documentation. No unrelated feature or bulk import change.

- States: initial/empty, individual invalid fields/rows, correction, duplicate, generic failure, saving, cancellation, successful detail/reopen. Invalid Save retains drafts; summary buttons focus actual inputs; removed draft rows remove only their errors.
- Use focusable buttons, `popover="auto"`, error `aria-describedby`/`aria-invalid`, fieldset/legend rows and an announced summary. Test actual Windows WebView2 and browser behavior; record human accessibility separately.
- Keep `save_project`, FastAPI and SQLite transactions, database paths/IDs/types unchanged. Persisted work-item removal remains unavailable. No migration required; UI rollback does not alter saved data.
- Run locked restore, format, frontend/backend/packaged-sidecar/Rust/legacy tests, native GUI, independent offline VM, real browser screenshots/interactions, staged privacy/whitespace and Windows CI on the actual PR head.
- Risks: WebView2/accessibility variation; unconfirmed customer formats; separate installer lifecycle and enterprise-policy tests. Stop any business-rule tightening pending #41; independently implement confirmed UX.

## Acceptance and delivery

See [engineering evidence](../acceptance/2026-11-21-issue-65-project-validation.md) for reproducible cases, results, candidate hashes, conditions and unmet requirements. Final Draft PR records its commit/current CI. Original source publication, automatic merge/release/Issue closure and customer DB changes are unauthorized. Customer Demo A acceptance and production approval remain pending.
