# Issue 45 Excel clipboard Design-First checklist

## Issue and current baseline

Issue #45, M1 / Demo A, continuation after merged sorting PR #63, bulk PR #64 and governance PR #67. Baseline `57c2fbc12074063ef16cd9170c2d23de35d5c115`; isolated branch `codex/issue-45-excel-clipboard`. GitHub reports public. No open PR at inspection on 2026-11-21; #45 updated 17:39:09 UTC, #65 updated 17:39:24 UTC. The main workspace README/design files and a separate worktree's staged UX/TSV draft are preserved. Only its reviewed TSV parser and backend tests are reused here; #65 product changes remain outside this slice.

## Design Compliance Checklist

Each source was read again. These files have no declared semantic version; their last-changing Git revision identifies content. Filesystem times below are fresh-worktree observations, not authoring dates.

| Source | Content revision | Observed last modified UTC | Read result |
| --- | --- | --- | --- |
| `AGENTS.md` | `d3b9bea` | 2026-11-21T18:57:30.5985758Z | Read |
| `docs/00-PROJECT-PLAN.md` | `cc9613a` | 2026-11-21T18:57:30.5995761Z | Read |
| `docs/09-DELIVERY-PLAYBOOK.md` | `e6326df` | 2026-11-21T18:57:30.6037387Z | Read |
| `docs/02-ARCHITECTURE.md` | `6d2fbeb` | 2026-11-21T18:57:30.6005761Z | Read |
| `docs/03-DATA-MODEL.md` | `fdef9ab` | 2026-11-21T18:57:30.6016820Z | Read |
| `docs/05-DEMO-ACCEPTANCE.md` | `471c89d` | 2026-11-21T18:57:30.6026825Z | Read |
| `docs/10-CLIENT-DECISIONS.md` | `471c89d` | 2026-11-21T18:57:30.6037387Z | Read |
| `docs/11-IMPORT-MAPPING.md` | `471c89d` | 2026-11-21T18:57:30.6047361Z | Read |
| `docs/acceptance/2026-11-20-issue-45-bulk-projects.md` | `471c89d` | 2026-11-21T18:57:30.6067363Z | Read |

UI source: local-only `Rigarus_UI_Design_Updated_2026-11-21.docx`, dated update 2026-11-21; last modified 2026-11-21 17:37:32 UTC; SHA-256 `e2f91d38a5e31869183b7eda1e1a213103cf4962631818bd1bb074e4886c4664`. Its text was reread and original **Figure 3A** inspected. Exact machine path and extraction remain local. Canonical repository DOCX remains absent under the owner's local-only instruction. Full-page rendering is unavailable without LibreOffice; section/figure labels are used, with no pagination claim.

Relevant chapters: project plan Scope/M1, delivery Gates/For each Demo, architecture Tauri migration, data model Project master data, Demo acceptance Bulk Add Projects, decision register Site ID/Job #/bulk conventions, import mapping Bulk Add Projects and Limits. UI section **批量添加：Excel 表格粘贴与纯文本样例（新增设计 · 2026-11-21）**, especially 复制 Excel 表格直接粘贴, 可复制示例, 纯文本 CSV 示例, 交互与校验 and 格式及安全约束. Figure 3A is a concept, not evidence of working UI.

| Requirement | Authority / existing implementation | Planned acceptance case |
| --- | --- | --- |
| True TAB/CSV with fixed headers, CRLF/LF, zeroes and quoted cells | #45 / Figure 3A; main parses CSV only; local uncommitted TSV draft inspected | Equivalent classification; quoted tabs/commas/newlines; physical source lines; mixed newline and repeated-header feedback |
| Copyable TSV and CSV examples with real separators and nearby Ctrl+C/Ctrl+V guidance | #45 / Figure 3A; main missing; local draft has selectable CSV only | Actual Copy -> clipboard -> paste -> preview, same three ready rows; permission-denied copy feedback/manual selection |
| Keyboard-accessible format/row/preview/no-overwrite/limit help | #45 / Figure 3A; missing | Focus/click opens, Escape/Close dismisses; one native auto-popover at a time; responsive layout |
| Read-only preview/Cancel; changed text/file/tab invalidates Confirm | Existing BulkProjects state and SQLite read-only preview | Regression; no inserts before confirmation; copied examples alone do not change input/preview |
| Eligible-only atomic writes, no overwrite, rollback/retry and preserved IDs | Existing BulkProjectStore and database constraints | TSV confirm, duplicate retry, stale input, existing Project/WorkItem preservation and restart |
| Existing .xlsx/template safety and 2,000 rows / 5 MiB | Existing mapping/parser; unchanged | Existing Excel/formula/source-cell/limit suites and packaged-sidecar tests |

## Design differences and unresolved questions

Site ID requiredness and Job # character/non-ASCII rules remain Open in #41/client decisions. Preserve existing nonempty and SQLite ASCII NOCASE constraints; do not introduce four-digit IDs or guessed character restrictions. No database, enum or scheduling fields are added. Code/Status/Assign and New Project error UX (#65) are out of scope.

The existing shell uses Segoe UI and teal/neutral controls and is retained. This is an existing component enhancement, so no new design direction is drawn. Two readable example fields replace the concept's single visual sample because #45 explicitly requires both formats; help uses small native auto-popovers, not permanently overlapping illustration bubbles. The screen's question is whether the pasted projects are ready to add; live preview/counts and explicit confirm remain the main action. Synthetic VM project IDs/site IDs and source lines are the product-specific content; no personnel/customer examples or network assets are used.

## Implementation Plan

- `bulk_projects.py`: reuse fixed-header delimiter detection; reject repeated header rows explicitly. The existing kind=text API remains unchanged; detect format authoritatively in the service, not with a second frontend parser.
- Backend `test_bulk_projects.py` / `test_sidecar.py`: TSV equivalence, malformed/quoted/limit/source-line input, transaction/preservation and packaged restart cases.
- `bulk-projects.tsx` / local CSS: updated input label/guidance, exact TAB/CSV copy actions, selectable fallback with honest error feedback, responsive example columns and native help buttons. Keep loading, invalidation, diagnostics, success and failure handling.
- `Test-TauriDesktop.ps1`: actual clipboard, help Escape, existing CSV/edit/Cancel/confirm plus TSV/duplicate/reopen. Restore clipboard privately and keep synthetic cleanup within its verified temporary directory.
- Update mapping, acceptance walkthrough and this record. No API shape, schema, migration, database path, installer strategy or business-default change. Legacy WPF remains a compatibility test baseline.
- Run locked npm/uv/Cargo/.NET restores, format, Windows native build/tests, packaged sidecar, GUI and privacy checks; record actual offline conditions separately. CI must run against the final Draft PR head. Do not overwrite the historical 0.1.0 installer or claim customer acceptance.

## Acceptance cases and actual results

Execution results and exact commands are recorded in the [acceptance evidence](../acceptance/2026-11-21-issue-45-excel-clipboard.md) and Draft PR. PASS: local locked restores/format/builds, 48 Python tests, 5 packaged-sidecar tests, 5 frontend sorting regressions, 4 Rust tests, 35 .NET compatibility tests, 9 acceptance-harness scenarios, final native host GUI, browser permission-denial/help checks, and final three-width visual inspection (0 FAIL / 0 WARN; all images inspected). The identical final executable also passed the independent no-NIC Windows VM suite in 300.448 seconds with exit 0, common developer commands absent and bounded SlowVm waits. Staged privacy/whitespace, PowerShell syntax and changed Markdown links passed. Windows CI must be reported against the final PR head; it is not inferred from these local results.

Microsoft Excel application copying, new-candidate installation/upgrade/uninstall, no-WebView2 provisioning, VM reboot and customer policy acceptance remain NOT RUN. Raw logs, original designs, clipboard contents and databases remain local. Customer Demo A acceptance and production approval are pending. No automatic merge, release or Issue closure.
