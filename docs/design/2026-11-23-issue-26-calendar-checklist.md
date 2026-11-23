# Issue #26 — explicit calendar calculation foundation

## Baseline and approved boundary

Client date November 23, 2026, America/Toronto. PUBLIC repository verified; fetched main `9ae4161ee99c19cb31be477325a7036641c5988b`, including human-merged PR #82. No open PR or existing #26 branch was found at inspection. Main CI `45205067700` was still running at inspection; its result is separate from this branch's validation. Isolated branch `codex/issue-26-working-calendars`; unrelated root README/design changes and other worktrees are preserved.

Read #26/#28/#29 and dependency scope in #14/#15/#22/#27; M5 is Workdays and recommendations / Demo E. Existing implementation has Draft visits, explicit worker membership and recorded employee availability, but no Crew/WorkItem working calendars, full M3 proposal engine or complete M4 safety validation. The owner explicitly reprioritized #26 → #28 → #29 and then approved **the conservative calculation model and tests first**, with calendar entry/persistence deferred. This does not declare the M3/M4 dependencies complete.

## Fresh source inventory

The following sources were read again. Repository documents declare the November 2026 planning baseline, not individual release versions. Fresh checkout modification times fall between `2026-11-23T15:28:14.379707Z` and `2026-11-23T15:28:14.383892Z`; these are checkout times, not approval dates. Exact per-file UTC modification times, hashes, local source paths and inspection evidence remain local.

| Source | Last-changing revision | Relevant sections |
| --- | --- | --- |
| AGENTS.md | `d3b9bea778529c47bb502e59914cbdd0100697a0` | Mandatory Design-First 1–12, privacy/human gates |
| docs/00-PROJECT-PLAN.md | `cc9613a61a09bee488255b96ac7f2e581b45a1a2` | Scope, M3–M5 and Option C |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326dff3c75bc1670a73dfd37638376efd15804` | Engineering / Demo / Production gates |
| docs/02-ARCHITECTURE.md | `f7e650c63d9217a10e5127d53f85aa54fa908fc9` | Manual Drafts, actual workers, recorded availability |
| docs/03-DATA-MODEL.md | `a2f9fa25bcbfb0be555a6979f9c8be744f51dde6` | Stable IDs, local dates, schema nine and retained history |
| docs/05-DEMO-ACCEPTANCE.md | `41784e24b80e7515a6a04dc314ce488241a0b50e` | Draft, availability, Employee Week and native UIA boundaries |
| docs/10-CLIENT-DECISIONS.md | `a2f9fa25bcbfb0be555a6979f9c8be744f51dde6` | Unknown availability, operator approval, open weekend policy |
| docs/DEV-DESIGN-CHECKLIST.md | Current checked-in template | Required source/requirements/plan/result fields |
| #35 UIA checklist and engineering record, November 23 | Current merged #82 versions | Prior native pass is a historical package/tool result, not this slice's acceptance |

Accessible original planning copies were found in local planning storage after the original root paths were absent. Read their working-calendar/data-model sections, engine inputs/outputs, R01–R11, T14, and Demo E/decision-gate sections. Their content and exact local locations remain outside Git. They prohibit hard-coded Mon–Fri, unsafe recommendations, implicit weekend approval and proposal writes before operator confirmation.

Latest accessible original UI: `Rigarus_UI_Design_Updated_2026-11-22.docx`, SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, last modified UTC `2026-11-22T08:14:42.434606Z`. Read Schedule explanations at direct body paragraph locators P30–61 and UI 09–10 P156–165; inspected original `word/media/image8.png` (Crew Board) and `image25.png` (Employee Week). These are design/prototype screenshots, not acceptance evidence. XML paragraph locators are not rendered page numbers. Weekend display does not approve weekend capacity. No dedicated working-calendar entry screen or authoritative override hierarchy was located in these relevant sections. Complete DOCX/images stay local; no UI is changed in this calculation-only slice.

## Design Compliance Checklist

| Requirement / authority | Existing code and planned change | Acceptance case |
| --- | --- | --- |
| Owner-approved separate Crew/WorkItem AM/PM cells | Add pure `work_calendars.py`; retain stable IDs; no Employee scope or Home Crew expansion | Reject wrong scopes/IDs; AM/PM and Crew isolation |
| Blank remains unknown, no assumed workweek/holidays | Missing cells resolve Unknown only | Weekday, weekend and holiday blanks remain Pending |
| Both Working required for calendar match | Matched / Blocked / Pending assessment with structured source reasons | All nine state combinations; explicit opposite states report conflict |
| No override by a contradictory calendar | Reject duplicate cells rather than last-entry-wins; known closure dominates unknown | Duplicate rejection, both conflict directions, known closure plus unknown |
| #26 T14: deterministic local dates | ISO date validation and ordinal date ranges, bounded to 366 inclusive dates | Year boundary, leap day, DST transition dates, maximum date, reverse/oversized range |
| Calendar match is not dispatch eligibility | Always Pending / unpublishable; explicit weekend-approval-pending reason; other validators remain independent | Weekend Working/Working still has pending approval; employee Available cannot fill Crew/WorkItem cells or approve driver/Rig/personnel safety |
| Option C/no mutation and compatibility | Pure in-memory evaluation only; no API, command, migration, persistence, new dependency or Draft write-path change | Forbid file/socket/SQL calls during calculation; compare synthetic full SQLite logical snapshot and existing visit before/after |

## Implementation Plan (output before code)

1. Add immutable validated calendar snapshots and structured per-slot explanations in the independent Python domain. Consume an `AssignmentDraft` only as a read-only context. Calendar result is never a candidate, reservation, proposal acceptance or publication authorization.
2. Add bounded range evaluation, sorted by local date then AM/PM. Preserve Unknown and every source's reason; do not add calendar precedence, holiday service or consent-write mechanism.
3. Add meaningful unit tests plus a synthetic existing FastAPI/SQLite compatibility test. Run locked restore, Ruff checks, full backend regressions and Windows CI, which also builds/tests legacy compatibility and Tauri. Stage explicit safe paths and scan privacy.
4. Update architecture, decision register and acceptance instructions/evidence, create one Draft PR for #26, retain the Issue open. No frontend/UI states, Rust command, HTTP endpoint, SQLite schema or dependency change; native GUI/installation comparison is not applicable to this unconnected pure model. Do not rebuild a local installer as if a new calendar UI existed.

## Differences, unresolved rules and blocked scope

Owner approval covers this calculation foundation only. Calendar entry UX, persistence/revisions/history, recurring rules, exceptions/holiday provenance, approval recorder, actual weekend consent, full M3 impact/locks, M4 personnel/driver/qualification/Rig checks and #28/#29 implementation remain separate. No hypothetical availability-to-safety conversion or new business constraint is applied to saved Drafts. The model can evaluate explicit cells supplied by a future adapter but the current app does not expose it. Full #26 and Demo E are not complete.

Actual commands/results, source limitations and delivery links are recorded in [the engineering record](../acceptance/2026-11-23-issue-26-calendar-model.md). Customer acceptance remains NOT RUN; production approval NOT GRANTED. Human PR review only, no Issue closure or Release.
