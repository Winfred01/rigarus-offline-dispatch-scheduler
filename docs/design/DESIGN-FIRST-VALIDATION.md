# Design-First source and rule validation

This is the documentation-only dry run for [Issue #66](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/66), requested by the owner on November 21, 2026. It validates the permanent workflow against [#45](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/45) and [#65](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/65). It does not implement their remaining features or establish customer acceptance.

## Baseline and source identity

Inspection began on November 21, 2026 at 17:46 UTC. Repository identity was verified through its remote and GitHub API. The API reports **public**, unlike historical private-repository wording. The owner explicitly chose to keep the complete UI DOCX local and publish only rules, the template and sanitized locators. No DOCX, extracted image, customer workbook/PDF or raw log is included here.

Latest fetched main at the start of this work: `a89f1d399f89fe1156b7dd7eae94aeb77871044e`, which merges PR #64. Local main and its existing README/design-folder changes were preserved in the original workspace. Work uses an independent `codex/issue-66-design-first-rules` worktree. PR #64 is merged (17:45:17 UTC), so its CSV/Excel bulk-add implementation must not be reimplemented. #45, #65, #41 and #42 remain open at inspection. #65 is assigned to M1 / Demo A; #41 retains customer field decisions.

All sources below were read from this main baseline. They have no separate semantic version; their last-changing commit is the content revision. Last-modified times are UTC filesystem observations in the fresh worktree, **not** authoring dates or proof of authority.

| Read document | Last-changing commit | Observed last modified UTC | Relevant sections |
| --- | --- | --- | --- |
| `AGENTS.md` (before this change) | `e6326df` | 2026-11-21 17:46:54.769 | All six existing rules |
| [Project plan](../00-PROJECT-PLAN.md) | `cc9613a` | 2026-11-21 17:46:54.771 | Scope; Milestones / M1 |
| [Delivery playbook](../09-DELIVERY-PLAYBOOK.md) | `e6326df` | 2026-11-21 17:46:54.774 | Gates; For each Demo |
| [Architecture](../02-ARCHITECTURE.md) | `6d2fbeb` | 2026-11-21 17:46:54.772 | Tauri migration; WPF baseline |
| [Data model](../03-DATA-MODEL.md) | `fdef9ab` | 2026-11-21 17:46:54.772 | Project master data; Migration check |
| [Demo acceptance](../05-DEMO-ACCEPTANCE.md) | `471c89d` | 2026-11-21 17:46:54.773 | Project Master; Demo A draft; Tauri sorting; Bulk Add checks |
| [Client decisions](../10-CLIENT-DECISIONS.md) | `471c89d` | 2026-11-21 17:46:54.775 | Site ID, Job #, sorting, bulk conventions and separate gates |
| [Import mapping](../11-IMPORT-MAPPING.md) | `471c89d` | 2026-11-21 17:46:54.775 | Bulk Add Projects; Limits and data lifecycle; Verification |
| [Bulk engineering evidence](../acceptance/2026-11-20-issue-45-bulk-projects.md) | `471c89d` | 2026-11-21 17:46:54.777 | Initial Windows checks; Compatibility and remaining scope |

The locally accessible source is `Rigarus_UI_Design_Updated_2026-11-21.docx`. Its in-document title identifies a November 12 design updated November 21 for New Project validation and Bulk Add examples. Local last-modified time: **2026-11-21 17:37:32 UTC**; size: **7,094,076 bytes**; SHA-256: `e2f91d38a5e31869183b7eda1e1a213103cf4962631818bd1bb074e4886c4664`. The DOCX core metadata says revision 1 and dates in 2013; these are generator defaults inconsistent with the dated title and must not be treated as the current design date.

The full OOXML text and all five embedded figures were read/visually inspected locally. Structural inspection found no comment parts or tracked insertions/deletions, and no external relationships in the main document relationship part. This is not a certification that the entire original is suitable for publication. Full-page rendering was attempted but **BLOCKED** because `soffice.exe` was unavailable. No pagination/layout approval is claimed; section and figure labels, checked against their original embedded images, are used below.

Expected repository copy `docs/design/Rigarus_UI_Design.docx`: **not present / not authorized for upload under the current local-only instruction**. The accessible original and its exact machine path are recorded locally and in the owner's handoff. This record does not replace the original; another machine without access must mark dependent UI work BLOCKED. It must not infer absence from the missing canonical path, invent a replacement design, or force-add a DOCX through existing privacy protections.

## Design Compliance Checklist for #45

Current Issue body updated **2026-11-21 17:39:09 UTC**. Read its original scope, November 21 supplement, comments and linked merged PRs #63/#64. PR #64 head `471c89d` and its review/CI evidence describe the delivered CSV/Excel and transaction slice, not the new clipboard UX.

Original design locators: **Projects 项目管理界面 / Figure 2**, **Bulk Add Projects 批量添加项目 / Figure 3**, and **批量添加：Excel 表格粘贴与纯文本样例（新增设计 · 2026-11-21） / Figure 3A**. The updated section includes **复制 Excel 表格直接粘贴**, **可复制示例（TAB 分隔，保留前导零）**, **纯文本 CSV 示例**, **交互与校验**, and **格式及安全约束**. Figure 3A is a visual concept, not an executed GUI test. The original text contains real TAB characters; its quoted-comma CSV example is also relevant even though the Issue's simpler CSV sample differs.

| Requirement | Current implementation inspected | Rule validation / future acceptance case |
| --- | --- | --- |
| Excel range paste: true TSV plus CSV, CRLF/LF, leading zeroes and source lines | `src/Rigarus.Tauri/src/bulk-projects.tsx` labels Paste Text / CSV; backend `bulk_projects.py::text_rows` uses comma-default `csv.reader` without TSV detection | **Missing delta located.** Plan delimiter recognition across UI/service and compare equivalent TSV/CSV; include quoted commas, newlines, blanks, repeated headers and duplicates. Do not rebuild existing bulk flow. |
| Two copyable monospace examples, exact TAB/CSV bytes and nearby paste guidance/help | No Copy example action or updated label in `BulkProjects` | **Missing delta located.** Copy each example, paste, preview, inspect exact separators/zeroes; keyboard/focus/help dismissal and narrow Windows layout need actual tests. |
| Preview/edit/cancel/confirm invariants and no overwrite | Existing `invalidate`, confirmation gating, `bulk_project_store.py::confirm`, source diagnostics and `BEGIN IMMEDIATE` revalidation already exist | **Existing safeguards located.** Preserve read-only preview/Cancel, input/file/tab invalidation, eligible counts, existing IDs/work items and full rollback; regression test after future clipboard changes. |
| Offline template, .xlsx safety and limits | Existing template, import preview parser/mapping and bulk limits | **Existing baseline located.** Preserve formula/external-reference non-execution, source cells and 2,000 rows / 5 MiB limits; verify actual packaged offline path separately. |

Open business rules: Site ID requiredness, accepted Job # characters and non-ASCII case handling remain in the decision register and #41. Existing Site ID nonempty validation/SQLite constraints remain in force pending an approved change. Neither `0001` in a sample nor a mockup authorizes a four-digit constraint. Figure 2's Code/Status/Assign and additional project fields are outside this clipboard slice and do not authorize schema expansion.

## Design Compliance Checklist for #65

Current Issue body updated **2026-11-21 17:39:24 UTC**, M1 / Demo A; no Issue comments at inspection. Read the current Project Master implementation rather than assuming CRUD is missing. Its historical CRUD dependency #7 is already delivered; #42 is the selected Tauri migration baseline and #41 owns unsettled customer decisions.

Original design locator: **单项目录入：醒目校验与字段提示（新增设计 · 2026-11-21） / Figure 2A**. Read **视觉层级与操作路径**, **气泡与字段说明**, **校验行为与可访问性**, and **未确认规则**. The original Figure 2A was inspected, including its contradictory sample error colors/tooltips; explanatory corrections and the Issue explicitly address them.

| Requirement or conflict | Actual baseline / authoritative correction | Rule validation / future acceptance case |
| --- | --- | --- |
| Field-level errors, summary navigation, first-invalid focus and clear grouping | `projects.tsx::ProjectEditor` has New project / Work items groups, HTML required inputs and one bottom `error`; no custom field-error map, navigable summary or help popovers | **Partial baseline and missing delta located.** Plan per-field/per-row messages, correction clearing, retained drafts, first-invalid focus and responsive hierarchy; do not reimplement CRUD. |
| Six concise keyboard-accessible help controls | No corresponding controls in current `ProjectEditor` | **Missing delta located.** Exercise Tab/Shift+Tab, open/close/Escape, visible focus, ARIA relationships and avoiding overlapping bubbles. |
| Mockup marks crews `2` and half-days `4` as errors | Both satisfy current frontend, FastAPI `PositiveInt` and SQLite constraints | **Conflict resolved by written correction.** Valid 2/4 stay valid; use genuinely invalid input for error screenshots and boundary tests. |
| Mockup says Small/Medium/Large | `projects.tsx`, `projects.py::WorkType` and SQLite support Small/Civil/Tower/Other; updated text/#65 agree | **Conflict resolved.** Test actual enum help and submitted values; no new enum/schema. |
| Mockup says four-digit Site ID and limited Job # characters | Written design/#65 call these examples; client decision register remains Open | **Business tightening BLOCKED pending #41.** Preserve current nonempty/uniqueness rules and leading zeroes, add no guessed format/character restriction. |
| No partial writes; existing IDs/search/reopen | `project_api.py`, `projects.py`, `project_store.py`, `storage.py` provide existing contracts and constraints | **Existing invariants located.** Future tests cover duplicate field feedback, invalid row isolation, multiple work items, atomic save and native offline reopen. |

The outcome is a successful **source-location and planning dry run**, not a product test pass. UI implementation cases above are **NOT RUN** in this documentation task. Customer Demo A acceptance and production approval remain pending.

## Implementation Plan for this governance slice

- Preserve the original six root AGENTS rules and append the twelve mandatory Design-First requirements.
- Add [the reusable checklist](../DEV-DESIGN-CHECKLIST.md) covering source identity, figures, authority/status, code comparison, implementation plan, acceptance cases, design differences, unresolved questions and separate delivery gates.
- Add this sanitized dry run. Keep full original/extracted content, images and diagnostics local.
- Change no product UI state, API, database model, migration, installer or business default. Product compatibility is unchanged; rollback is a documentation revert reviewed normally.
- Validate Markdown paths/anchors, template coverage, preservation of the original rules, explicit changed paths, whitespace and staged privacy. Report full Windows CI for this new PR separately from local documentation checks. No new product GUI pass is claimed.
- Risks: the original is not available in every clone; stale DOCX properties and old PR descriptions can mislead. Require fresh reads, live Issue/main checks and BLOCKED status when originals are unavailable. These are agent instructions, not automated proof that a future agent read a document. Human merge is required before main carries these rules.

## Governance verification

Local documentation checks **PASS**: UTF-8/LF/final newline, no trailing whitespace, all relative Markdown links resolve, original six AGENTS rules remain intact, twelve new rules are present, required template fields and both Issue/figure/conflict mappings are present. `git diff --cached --check` and `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Test-RepositoryPrivacy.ps1` **PASS** for 150 indexed paths. Only the three intended Markdown files are staged; no product, installer, database or original design files are changed. The independent documentation checker and raw output remain local.

Product builds and native GUI tests are **NOT RUN locally / not applicable to this documentation-only change**. The Draft PR records its own Windows CI URL and actual job/upload status; historical PR #64 results are not reused as this PR's result. Original DOCX full-page rendering remains BLOCKED as described above. Engineering documentation verification is separate from customer acceptance and production approval, which remain pending.
