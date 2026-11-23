# Issue 71 — Employee Week first slice

Baseline main `c10ce66ce0a3177a04cc75404e7b0e21b38f0d55`, after human merge of #78. No open PR or actionable review feedback at start. One isolated branch `codex/issue-71-employee-week`; repository PUBLIC. Original root README/design files and earlier worktree indexes remain untouched.

## Sources reread and verified

Existence, checkout mtime UTC and last Git revision were checked afresh. Checkout timestamps are not authoring/approval dates. AGENTS `d3b9bea`; project plan `cc9613a`; delivery playbook `e6326df`; architecture, data model, acceptance and client decisions `a2f9fa2`. Read all six mandatory documents, #71, parent #22, #77, #15/#23/#42 and current #77 acceptance/PR #78 evidence. Main CI is checked independently of PR CI.

Original accessible local `Rigarus_UI_Design_Updated_2026-11-22.docx` SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, last-write UTC `2026-11-22T08:14:42.434606Z`. Fresh XML text and original UI 16/image25, UI 17/image26, UI 18/image27, UI 20/image29 and UI 42/image47 were inspected. Paragraph locators use direct zero-based body paragraphs P191–215 and P321 onward; they are not rendered page numbers. Complete DOCX, original images, logs and databases remain local.

## Design Compliance Checklist

| Requirement / source | Existing behavior / change | Acceptance |
| --- | --- | --- |
| UI 16 Employee Week; #71 actual membership | Existing employee-filtered Assignment query returns latest explicit workers. Add employee picker and Sun–Sat grid using that read, never Home Crew expansion | Same Home Crew, only explicitly selected employee has work; borrowing shows target Crew, home unchanged |
| UI 18 empty week | Retain picker, dates and seven Unscheduled cells; clear old rows on identity changes/failure | No jobs, inactive worker, cross-year, rapid employee/week switches, failed read/retry |
| UI 17 preview/gates | Read-only in-memory snapshot of selected employee/week/record revisions; DRAFT – NOT CONFIRMED. PDF/XLSX remain disabled | Preview and grid agree; no writes, downloads or publishing endpoint; error/loading prevents preview |
| UI 20/42 handoff | Directory and global-search person detail route to selected employee; retain current Schedule date in app state | Correct stable ID and selected week after People/search navigation |
| #77 owner-confirmed states | Existing availability range read supplies separate AM/PM administrative labels | Available/Unavailable/Not recorded distinguished from failed read; never infer OFF approval or attendance |
| Product invariants | Existing English Tauri/React/FastAPI/SQLite stack, no login/dependency/migration | No changes to stored records/IDs/notes/Home Crew; all Drafts remain pending and unpublishable |

## Implementation Plan before product edits

Add `employee-week.tsx` and a pure explicit-membership/date projection helper. Reuse existing `list_assignments` with employee_id/start_date/end_date and `read_availability`; no new HTTP/Rust command or SQLite schema. Keep shared Schedule date/employee identity in app state for handoffs, extend existing Schedule tabs and directory/search routes. Read-only card details and preview keep real dated Crew/work item/status, actual Rig explicitly Not assigned. No Crew default inference, no work-item description field invented.

Use independent assignment/availability loading/error/retry, identity guards and cancellation for delayed responses; clear old employee/week records immediately. Empty and inactive states, keyboard focus/Escape, long names, seven-day horizontal scroll and narrow document bounds are explicit checks. Native tests reuse synthetic #77 staffing/availability fixture and add employee switch/preview/handoff/reopen; pure tests defend explicit IDs/cancelled dates; browser faults exercise race/retry. Run locked restores/format, Windows build, relevant tests, CI, staged privacy and source/candidate hashes.

This is #71's read-only employee planning/preview slice, not full #71. Formal PDF/XLSX and immutable Published snapshots depend on #15/#23/#17/#32; leave approval remains separate. Available does not certify attendance. Existing no-NIC VM attempt was BLOCKED by guest self-power-off; do not reuse its initial-window result as an offline lifecycle pass. Customer acceptance and production remain separate.
