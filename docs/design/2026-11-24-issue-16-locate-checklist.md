# Issue #16 — Locate exact saved half-day cards

Baseline main3101a726a8a5acd18b852d0b00a58ba860a178f5 includes human-merged
PR97/96 and prior #16 PR73/75. Latest Issue16 November24 P1 UI update read;
M2 / Demo B. PUBLIC visibility verified; public open-PR endpoint returned no
open pulls (connector search erroneously returned already merged97; verified
state before proceeding). Root README/Chinese README/local designs preserved.
Isolated codex/issue-16-locate-cards; owner prioritizes Locate before #28 UI.
Existing basic selection scrolling is not complete Locate; no fallback to #28.

## Design Compliance Checklist

| Source | Exists / declared version / reread | Last-changing revision | Checkout mtime UTC (not authority) | Read-at UTC |
| --- | --- | --- | --- | --- |
| AGENTS.md | Yes, November 2026 baseline | d3b9bea778529c47bb502e59914cbdd0100697a0 | 2026-11-24T23:25:44.751065+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/DEV-DESIGN-CHECKLIST.md | Yes, November 2026 baseline | d3b9bea778529c47bb502e59914cbdd0100697a0 | 2026-11-24T23:25:44.757573+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/00-PROJECT-PLAN.md | Yes, November 2026 baseline | 2a074876b0d8283578af7464a97ea12837c244d9 | 2026-11-24T23:25:44.752568+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/09-DELIVERY-PLAYBOOK.md | Yes, November 2026 baseline | 2a074876b0d8283578af7464a97ea12837c244d9 | 2026-11-24T23:25:44.755573+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/02-ARCHITECTURE.md | Yes, November 2026 baseline | 27c7c1c6a6dfdc4bc2d6f17da4cd2706304a2ec7 | 2026-11-24T23:25:44.753573+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/03-DATA-MODEL.md | Yes, November 2026 baseline | 27c7c1c6a6dfdc4bc2d6f17da4cd2706304a2ec7 | 2026-11-24T23:25:44.753573+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/05-DEMO-ACCEPTANCE.md | Yes, November 2026 baseline | 27c7c1c6a6dfdc4bc2d6f17da4cd2706304a2ec7 | 2026-11-24T23:25:44.754573+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/10-CLIENT-DECISIONS.md | Yes, November 2026 baseline | 27c7c1c6a6dfdc4bc2d6f17da4cd2706304a2ec7 | 2026-11-24T23:25:44.756575+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/acceptance/2026-11-22-issue-16-desktop-week.md | Yes, November 2026 baseline | da66698fd9949735b9735a7f698d57e83ca02280 | 2026-11-24T23:25:44.760592+00:00 | 2026-11-24T23:33:46.415411+00:00 |
| docs/acceptance/2026-11-22-issue-16-multiday.md | Yes, November 2026 baseline | 29f9e95eddca2d4b6269d3d504466e58ffee4bcb | 2026-11-24T23:25:44.761596+00:00 | 2026-11-24T23:33:46.415411+00:00 |

Relevant sections: Scope/Milestones/Gates; architecture desktop weekly projection,
actual staffing/calendars and separate safety services; data Draft IDs/revisions/
Crew-slot uniqueness; acceptance Desktop weekly planning/multiday/current safety
gates; decisions confirmed owner UI/Draft and pending publication policies.
User's current UI-first order supersedes prior backend-validator priority.
No inference of implementation/customer acceptance from milestone or prototype.

### Original UI actually inspected

Authorized local Rigarus_UI_Design_Updated_2026-11-24.docx SHA256
 d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c
mtime UTC2026-11-24T23:15:38. Latest text says L01–L25 supersede historical UI01–47.
Extracted and visually inspected original embedded images, not Word-rendered
page numbers: L01 p10–14/image53, L02 p15–19/image54, L03 p20–24/image55,
L08 p45–49/image60, L14 p75–79/image66 (p means XML paragraph locator).
These are browser prototype reference screenshots, not product evidence.
L03 requires exact AM/PM focus, internal centering, two1-second pulses then clear
around2 seconds, static under reduced motion; unavailable/paused must not jump.
Original images, extracted references and absolute paths remain local/ignored.

Expected Locate HTML Rigarus_Desktop_Prototype_Locate(1).html not found by named
Locate/locate/Prototype HTML search in workspace/hidden worktrees or design
folder (excluding build/dependency trees). Original DOCX text and five actual
figures plus current Issue16 supply this slice; no claim of live prototype QA.
The owner explicitly allows continuing from Issue16 if an attachment is absent.

| Requirement / source | Existing implementation / gap | Planned acceptance |
| --- | --- | --- |
| Confirmed owner/L02–L03: real source rows only | Publish review generic blockers; actual visits have saved calendar/staffing feedback | Add dated review rows from existing calendar/missing-staffing observations; no fabricated Rig/driver conflicts |
| Confirmed exact stable ID / AM-PM | Individual IDs exist inside normal and multiday buttons | Read actual latest record, reveal exact ID, never first card of project/date |
| Confirmed close source / Job Schedule /1 Week / Sunday anchor | Detail/global search routes exist; target currently opens details | Separate Locate from selected/detail; close source, switch view/week, visibly show1 Week |
| Confirmed compatible filters / row visibility | Only Crew/Project filters exist; board has no project row cap | Preserve matching filters, reset only blocking filters; scroll beyond100th project; do not invent Rig/status controls or cap |
| Confirmed internal centering/focus / pulse clear | Existing selection scrolls into view but no timed cue | Center within week-scroll respecting sticky header/roster, focus preventScroll; no page scroll; 2s cue/reduced-motion CSS |
| Confirmed repeated/stale/removed | No Locate request lifecycle | Request identity guards, latest record date, cancellation/unmount cleanup, informative non-jump on cancelled/paused/missing/read failure |
| Confirmed Draft persistence/gates | Real add/edit/cancel/staff/calendar and disabled publication/export | Preserve all commands/revisions/Crew uniqueness; no save/Apply/Publish changes |
| L08/L14 broader prototype features | No exception queue/maintenance/paused/locks/published API | No fake entry points/data; wire current review/details/search only; defer unsupported controls |

App-screen guidance applies to readable data, keyboard/focus and honest states.
Keep owner-approved existing palette/type/layout and L03 amber attention cue;
no redesign/style kit, invented metrics or extra navigation. Screen's question:
which exact saved half-day needs attention? Identity comes from Job/Site/Crew,
local date/half and persistent Draft ID. Prototype-only features remain excluded.

## Implementation Plan

1. Add schedule-locate.ts with testable observed review feedback, current-record
   validation/unavailable messages, compatible Crew/Project filter reveal,
   internal viewport-center geometry and cancellable two-second cue lifecycle.
   Reuse existing date/week/calendar text helpers. No domain safety validator.
2. schedule.tsx: add real dated observed rows to existing Publish review, anchored
   to entire selected week regardless of visible filters; retain global blockers
   and disabled Publish. Add Locate from existing draft details and route current
   global-search target through the same handler. No new Needs Attention/Rig data.
3. Handler re-reads persisted ID/current workspace, validates active/current
   record and parent visibility before navigating. Preserve compatible filters,
   show Job Schedule/1 Week and target Sunday anchor. Use request tokens to ignore
   stale asynchronous results; avoid dropping unsaved editor/cancellation forms.
   Separate temporary highlight from selected/detail state. After render close
   dialogs then center/focus exact button (including individual multiday visits),
   start2s cue, clear/cancel on repeat/navigation/unmount. Geometry respects sticky
   header/roster and clamps container scroll; no document scrollIntoView.
4. desktop.css: amber outline/two1-second pulses using existing visual language;
   reduced-motion animation:none. Keep native focus visible after cue expires.
   UI states: locating/loading, real empty feedback list, source-read error with
   reload, cancelled/paused/missing feedback; keyboard buttons and live status;
   narrow internal scroll. No modal auto-reopen on Locate.
5. Unit regressions for stable identity/cross-year/filters, current versus stale
   date, unavailable/invalid records, review source truth, geometry/bounds and
   overlapping timer cancellation. Real-browser synthetic scenarios cover current
   review, detail/search, far rows/AM-PM/continuous visits, filters, repeated
   requests/focus/clear/reduced motion, read failures and Draft lifecycle.
6. Build packaged Windows candidate with matching sidecar, independent synthetic
   profile via existing RIGARUS_SMOKE_DATA_ROOT, and test native controls/screenshots
   through Computer Use when available. Keep screenshots/raw DB/logs local; record
   exact network/tool/GUI conditions. Do not use customer profile. Browser proxy
   tests are separate from native Rust/sidecar behavior and offline installation.
7. No schema/dependency/API/Tauri command or backend business change. Run locked
   Python/sidecar/frontend/Rust/.NET, applicable synthetic harness/privacy/CI.
   Update source/acceptance/design comparison and priority decisions; one Draft
   PR refs16, keep Issue Open; no merge/Release/customer DB/automatic publishing.

## Actual checks

NOT RUN at this design commit. Customer Demo B/E/UAT pending; production not approved.
