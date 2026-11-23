# Issue #26 — Project-shared editable working calendars

## Resumed baseline and source identity

November 23, 2026, America/Toronto. PUBLIC repository reverified; fetched main remains `9ae4161ee99c19cb31be477325a7036641c5988b`. Reuse branch `codex/issue-26-working-calendars` and open Draft PR #83 at `7435f35c5093e445108792274eb6b5854f941ec9`. Its previous Windows CI `45207490172` passed all three jobs; that result covers the foundation commit, not this follow-up. Root README/Chinese README/original designs and other worktrees remain untouched. The PR is not merged and no actionable code review was present at inspection.

Read the following sources again, checking existence, current revision and last modification UTC. Exact current checkout timestamps/hashes and the read command evidence remain in local source metadata; checkout times are not approval dates. Markdown summaries declare November 2026 rather than independent release versions.

| Source | Revision at resumed read | Sections used |
| --- | --- | --- |
| AGENTS.md | `d3b9bea` | Mandatory Design-First 1–12 and all preserved safety rules |
| docs/00-PROJECT-PLAN.md | `cc9613a` | Scope, milestones, Option C; amended here with owner's dependency order |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326df` | Engineering/Demo/Production gates, migration evidence and human review |
| docs/02-ARCHITECTURE.md | `7435f35` | Sidecar security, Drafts, explicit staffing, availability and pure calendar foundation |
| docs/03-DATA-MODEL.md | `a2f9fa2` | Stable IDs, existing schema nine, atomic migrations and recovery |
| docs/05-DEMO-ACCEPTANCE.md | `7435f35` | Draft/availability/Employee Week, native GUI and prior model-only scope |
| docs/10-CLIENT-DECISIONS.md | `7435f35` | Unknown availability, operator approval, open consent and bounded first-slice decision |
| #26 foundation checklist and engineering record | `7435f35` | Historical calculation scope, tests and deferred storage/UI |
| Current Issues #26/#15/#23/#25/#24/#27/#18/#28/#19/#20/#29/#17/#71/#32 | Live GitHub bodies | Actual dependencies and acceptance gates, all still open at inspection |

Latest accessible original UI is still `Rigarus_UI_Design_Updated_2026-11-22.docx`, SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, modified UTC `2026-11-22T08:14:42.434606Z`. Reread direct XML body paragraphs P30–61, P156–184; inspected original `word/media/image8.png` and `image25.png` again. These are prototype/design screenshots, not implementation acceptance or rendered page numbers. The original has no dedicated working-calendar editor. This owner-requested extension follows the existing Schedule tabs, Sun–Sat grid, local-date navigation, range form, dialog/focus and history conventions. It does not claim a nonexistent original calendar-entry figure. Full DOCX and raw local evidence stay local.

## Design Compliance Checklist

| Requirement / status | Source and needed implementation | Acceptance case |
| --- | --- | --- |
| Confirmed: actual dependency order, not milestone waterfall | Latest owner seven-step instruction; update plan/decision records while retaining per-Issue safety dependencies | #26 before complete #18 engine; #28 never treats absent M4 validation as satisfied |
| Confirmed: Project calendar shared by every WorkItem | Owner's explicit answer supersedes first-slice independent WorkItem ownership | Derive Project ID from SQLite WorkItem FK; both Civil/Tower inherit; reject WorkItem calendar writes |
| Confirmed: Crew calendar independent; Unknown preserved | Existing conservative calculation approval plus new ownership decision | Separate Crews/Projects, sparse unknown, independent AM/PM and inclusive range/clear |
| Confirmed: closure/unknown can remain Draft | Owner's explicit answer; preserve existing definite Crew-slot rejection | Existing and newly saved Draft show conflict/pending; no rewrite of IDs/dates/notes/workers or inferred publication |
| Confirmed: separate safety gates | Plan, #15/#23/#25/#24/#27 and owner instruction | Employee Available and calendar Matched never assert driver, staffing, Rig or weekend approval |
| Existing invariants: atomic, revision-safe local SQLite | Data model and existing availability/Foreman patterns | Additive migration rollback/retry, stale/concurrent save, partial-range failure rollback, append-only history, reopen and consistent backup compatibility |
| New UI extension: functional, reversible editing | Original weekly/grid conventions plus requested storage/editing | Loading/empty/invalid/error/retry/success, Cancel/Escape no write, focus restoration, long owner labels, scrolling and keyboard |
| Design source conflict resolved | UI 09 depicts duplicate resource save failure; current Crew occupancy rule retained. New owner calendar advice applies only to calendar feedback | A calendar closure does not silently remove the existing Crew unique-slot constraint |

## Implementation Plan (announced before product edits)

1. Keep the pure foundation; add a Project adapter that projects the authoritative shared Project cells onto each WorkItem context, preserving the real WorkItem ID. Only Crew/Project can be persisted or written; the old in-memory WorkItem cell model is a calculation projection, never an override store.
2. Add schema ten `20261123020000_AddWorkingCalendars`: immutable Crew-or-Project owner, append-only revisioned range changes and sparse AM/PM cells linked to their own calendar/history. Use one migration transaction, no changes to original rows. Unknown clears current cells but retains history; no-change saves do not append.
3. Add FastAPI read/save/history and WorkItem-derived assessment, with strict scope/IDs, bounded 366-date operations, 404/422/409/503 mapping and sanitized errors. Existing Draft reads/list/save responses include current calendar feedback in the same transaction, with independent calendar revisions. Dates, assignment revisions and workers do not change when only a calendar changes.
4. Add four authenticated Rust commands; constrain owner paths to Crew/Project and encode assessment query values. Reuse existing loopback/parent-token lifecycle, no new dependencies or external services.
5. Add Schedule → Working calendars: owner picker, Sun–Sat AM/PM table, date jump, range edit/clear and history. Save explicitly; Cancel/Escape do not invoke writes. Guard delayed reads by owner/week; distinguish failed reads from Unknown. Unknown/failed write requires fresh reload; successful write/failed refresh clears old cells and identifies the committed outcome. Block double submit and restore focus after dialogs.
6. Add live advisory feedback to the Draft form, saved details and cards. A failed preview is an error, never fabricated Unknown or a reason to mark eligibility. Saving still runs the existing transactional Draft path; all results remain Pending/unpublishable.
7. Run locked backend/frontend/Rust restores, formatting, unit/integration/packaged tests, Windows build, native UIA/reopen and screenshot/interaction checks, migration compatibility/recovery, privacy and current-head Windows CI. Add opt-in `-IncludeWorkingCalendars` to the existing native verifier, preserving all bounded waits and previous cases. Record host connectivity and any VM execution separately.

The existing Rigarus design takes priority over a new visual direction; `design-taste-frontend` app-screen review is used for clarity, states, focus and responsive checks. No brand/font/navigation redesign or online asset is introduced. The screen asks: “When can this Crew or Project work?” Its meaningful data is the dated AM/PM three-state grid; fake statistics and recommendations are absent.

## Remaining boundaries

No recurring workweek, holiday import/default, WorkItem override, weekend approval recorder, personnel/driver/qualification/Rig validator, proposal generator, lock/Apply/publication or formal export is added. Calendar Matched is not a safe candidate. Those Issues remain open and follow the owner's dependency order. Customer Demo E and production remain pending. Actual outcomes and limitations belong in [the follow-up engineering record](../acceptance/2026-11-23-issue-26-project-calendars.md).
