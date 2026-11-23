# Issue 77 — recorded employee availability

## Current sources and scope

Owner's next priority is employee available-date management and an availability calendar, followed by a connection to Draft worker selection. Parent #22; PR #76 was human-merged. Main baseline `9694c5f9e674dd3818c6f5161cc6bc9d5805b222`; main Windows CI `45090918019` passed. No open implementation PR existed at start. Repository is PUBLIC. Branch `codex/issue-77-availability` uses an isolated worktree; unrelated workspace changes stay untouched.

Mandatory sources were read again, with existence, checkout modification time UTC and last Git revision recorded locally. Checkout timestamps are not business authority.

| Source | Revision / version | Relevant sections |
| --- | --- | --- |
| AGENTS.md | `d3b9bea` | Mandatory Design-First 1–12; privacy, human review and one-slice boundaries |
| docs/00-PROJECT-PLAN.md | `cc9613a` | Windows single-operator offline scope; M2/M4/M5 separation |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326df` | Engineering, Demo and Production gates |
| docs/02-ARCHITECTURE.md | `ca28c63` | Sidecar authentication, weekly dates, explicit Draft workers |
| docs/03-DATA-MODEL.md | `ca28c63` | Stable Employee IDs, schema eight, transactional revisions and retained history |
| docs/05-DEMO-ACCEPTANCE.md | `ca28c63` | Employee roster, Draft workers and weekly native checks |
| docs/10-CLIENT-DECISIONS.md | `ca28c63` | No inferred attendance/eligibility; pending leave, weekend and publishing rules |
| #22 / PR #76 engineering evidence | `ca28c63` | Existing selected workers, context invalidation, exact previous binaries; prior passes do not certify this candidate |
| Original local UI DOCX | Rigarus_UI_Design_Updated_2026-11-22.docx | SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, original last-write `2026-11-22T08:14:42.434606Z` |
| Relevant local updated plans | November 22 sections on actual staffing, TimeOff and working calendars | Recorded availability must not imply approved leave, Mon–Fri or weekend consent |

Fresh extraction: XML paragraphs P043/P052–058 (roster/off-date boundary), P177–206 (UI 13–18), P207–216 (People context). Original UI 13 image8.png, UI 16 image25.png and UI 18 image27.png were visually inspected. These are paragraph/image locators, not invented rendered page numbers. The original DOCX and all raw images/diagnostics/databases remain local. Real customer XLSX/PDF files were not used.

## Confirmed decisions

The owner explicitly answered both questions this session (November 22, 2026 client date):

1. Available / Unavailable / Not recorded; blank remains unknown.
2. Full day, AM only or PM only; date ranges include both endpoints.

No new default workweek, approved leave state, driver/qualification gate or weekend-consent rule was confirmed. The new page extends the existing original UI 13/16 weekly pattern under the owner's new request; the DOCX has no dedicated availability editor. It is not claimed to contain this complete new screen specification. Employee actual-job calendar/export remains #71.

## Design Compliance Checklist

| Requirement | Implementation boundary | Acceptance case |
| --- | --- | --- |
| Positive and negative availability, unknown blank | Explicit sparse Employee/date/AM-PM cells; no absence-of-record inference | Empty employee/week, weekend and unrecorded PM stay Not recorded |
| Inclusive date ranges / partial days | Pure canonical local-date validation; Full day projects to AM and PM; 366-date technical per-operation bound | Cross-year Dec 31/Jan 1, leap day, first/last date, AM-only overwrite and clear |
| No silent write / preserved context | Save explicitly replaces selected slots; Cancel makes no write; retained per-employee revision/history | DB/WAL unchanged on Cancel, other employees/dates/slots and all Drafts untouched |
| Weekly calendar | People → Availability, employee search/picker, Sun–Sat/Prev/Today/Next/date jump, clear three-state text | Switch employee/week without residual records; inactive marker, long names, keyboard, narrow viewport and scroll |
| Error and stale states | Read failure is an error, not Unknown. Write uncertainty/stale revision requires reload, including after closing editor | Failed/stale saves retain values, retry after explicit read; committed-save/refresh failure clears stale cells |
| Migration / recovery | Additive schema nine, history append-only; optimistic employee revision and one SQLite transaction | Eight→nine preservation, forced post-DDL/cell failure rollback/retry, one concurrent winner, restart, old build rejection and consistent backup fallback |
| Draft connection after independent calendar | One authenticated bulk date/slot read feeds worker picker; labels are advisory | Same person/slot matches calendar; failed read is not Available/Unknown; Unavailable does not auto-remove saved worker or approve dispatch |
| Human gates | No publish/export or leave/work-calendar/driver-policy expansion | Draft remains Validation pending / unpublishable; customer/production statuses separate |

## Implementation Plan

Add `availability.py` domain/date-range rules, `availability_store.py` snapshot/write/history and `availability_api.py` HTTP mapping. Migration `20261123010000_AddEmployeeAvailability` creates current cells and append-only range changes without rewriting original rows. Strict IDs and per-employee expected revision protect range overwrites; an unchanged state is a no-op. Clearing removes current cells while retaining the audit event. The 366-date limit bounds processing, not employee eligibility.

Build the independent management/calendar first, then integrate read-only date/slot status in Draft worker selection. Reuse authenticated Rust/loopback ownership, local-date helpers and established People/dialog/week styles; no new dependency, account or online API. Explicit loading/empty/invalid/failure/success, keyboard/focus, inactive and narrow states are required. Keep availability distinct from actual assignments and Home Crew; do not silently deselect or mutate Draft records. A new management form is an intentional owner-requested addition, using existing visual conventions rather than an invented claim about the original DOCX.

Run domain/API/SQLite concurrency/rollback/migration regressions, actual packaged-sidecar authentication/restart checks, frontend/Windows builds, native availability + Draft lifecycle/reopen, browser fault/keyboard/layout comparison, Windows CI and staged privacy. Preserve failed-run evidence and state actual connectivity/tooling/package hashes. Deliver one Draft PR for #77, no auto merge/Issue closure/Release.

## Unmet design and business items

Full approved leave workflow and OFF summary semantics, Crew/project working calendars, weekend consent, driver/qualification/minimum staffing, automatic resource exclusion, Published snapshots, #71 actual-job Employee Week and PDF/XLSX remain separate. Available is a recorded administrative state, not certified attendance or dispatch eligibility. See [candidate-specific engineering evidence](../acceptance/2026-11-22-issue-77-availability.md) for actual outcomes and conditions.
