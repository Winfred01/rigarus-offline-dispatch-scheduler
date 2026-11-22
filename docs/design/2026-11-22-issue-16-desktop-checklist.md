# Issue 16 desktop framework and weekly planning

## Design Compliance Checklist

Inspection: November 22, 2026. Public repository verified through GitHub. Fresh main `8723089` merges #14 via PR #72; no open PR found. Independent branch `codex/issue-16-desktop-schedule`. Original workspace README and untracked design files are preserved.

Read current AGENTS (`d3b9bea`), project plan (`cc9613a`, M2 / Demo B), delivery playbook (`e6326df`), architecture, data model, acceptance walkthrough, client decisions and #14 engineering evidence (each `587a3ec`). Fresh-checkout modification times are November 22 at 10:19:12 UTC and are not authoring dates. Read current Issue #16 plus #14, #22, #45, #71, #17 and #32 bodies through GitHub. Latest owner request authorizes this bounded UI slice. M2 requires manual scheduling, provisional half-days, conflict checks and weekly output; complete publication and customer acceptance remain separate.

Local-only source: `Rigarus_UI_Design_Updated_2026-11-22.docx`, declared November 22, SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`. Text extracted from OOXML and embedded original images inspected for UI 01–15 and 40–47; this is image/section inspection, not a rendered-page pagination claim. Prototype v2 HTML and screenshots ZIP not found in the provided design directory or tracked file inventory. Original figures, extracted text, exact paths and machine metadata remain local. No original customer workbook/PDF is used as test data.

| Requirement / reference | Authority / baseline | Change and acceptance |
| --- | --- | --- |
| UI 01 shell, UI 40–47 tools | Confirmed owner request; legacy top tabs / no global search | Dark left rail in requested order, local typed search with stable-ID routing, Ctrl+K/arrows/Enter/Escape, appearance preview/cancel/save/reopen, contextual Help |
| UI 01–03, 11–15 week grids | Confirmed UI scope; #14 selected-date list exists | Shared stored assignments, Project/Crew views, Sunday–Saturday local dates, sticky dates/roster, nine-Crew scroll, pending queue and details; empty/loading/read-failure states |
| UI 04–09 draft lifecycle | Existing #14 API, SQLite IDs, slot conflict and revision rules | Reuse commands/editor; preserve no-write Cancel, stale/uncertain reload protection, locate saved week, synchronize views and release cancelled work |
| UI 10 review / UI 38 export | #15/#23/#17/#32 prerequisites missing | Explicit blocker reasons; no publish command or formal export |
| UI 13 roster and #22/#71 | Home Crew and immediate Foreman master data exist; no dated staffing/leave | Foreman first/bold including cross-Home-Crew appointment, inactive markers, default Rig labelled as default, Time off not configured; Actual staffing not assigned. No invented OFF, actual Rig or approved driver |
| UI 23–39 later panels | #45 operations already merged; other panels tracked separately | Retain Project CRUD/bulk/sort, Crew/Employee/Foreman/Rig CRUD and import preview; link follow-up scopes without fabricated records |

Visual differences: requested Schedule-first navigation order overrides the prototype's order. Safety text and stable record IDs remain visible even where mockups omit them. Existing schema has work type/estimate rather than arbitrary work descriptions; display those stored fields. Consecutive visits must retain individual AM/PM identity; no inferred duration, remaining-work deduction, employee assignment or publication. Full multi-day spanning remains an explicit comparison case.

## Implementation Plan

Update React main shell and schedule component; add shared typed workspace reads, local-calendar helpers, native accessible dialogs, local search and appearance preferences. Preserve existing dependencies and Tauri/FastAPI/SQLite commands. No schema/migration change: #14 assignment and #8 roster IDs/revisions remain authoritative. Appearance uses versioned local device preferences, validates values, reports write failure and restores saved preview on cancellation.

Use one bounded workspace load and guard stale responses/unmounts. Failed or uncertain writes retain draft input and require reload; committed write/failed refresh clears stale displayed records. All filtering is read-only. Test shared views, pending cancellation, same-day AM/PM, cross-year/weekend/local timezone boundaries, selection/focus, missing staffing, nine-Crew vertical and horizontal scroll, search routing and settings retention. Run locked frontend/backend/.NET/Rust checks, native Windows build/GUI where available, then staged privacy checks and Draft PR. Record offline installer execution separately; host networking is not an offline pass.

Customer Demo B acceptance and production approval are pending. Human review required; no automatic merge, release, Issue closure or customer database modification.
