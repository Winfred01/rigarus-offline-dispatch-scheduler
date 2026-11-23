# Issue 22 — explicit Draft workers

## Issue, baseline and current sources

Refs #22 Stage B (first persisted-membership slice), #14/#16 dependencies and #71 handoff. Baseline `9b24ffeeb8d78a2632c2c54e80837cec8ff178ba`, after human merges of #74/#75. Repository visibility is PUBLIC. No open #22 implementation PR was found at start; unrelated root/worktree changes are preserved. One branch `codex/issue-22-actual-staffing`. This does not implement all Stage B or claim Demo D acceptance.

All mandatory sources were read again this session. Existence, last modification time (UTC), revision and original-design SHA-256 are recorded in local source metadata; checkout timestamps are not authoring dates.

| Source | Revision / declared version | Relevant sections |
| --- | --- | --- |
| Root AGENTS.md | `d3b9bea` | Mandatory Design-First 1–12, human/data boundaries |
| docs/00-PROJECT-PLAN.md | `cc9613a` | Scope, M2/M4, local independent domain |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326df` | Engineering / Demo / Production gates |
| docs/02-ARCHITECTURE.md | `da66698` | Manual Draft assignments, weekly projection, Home roster boundary |
| docs/03-DATA-MODEL.md | `587a3ec` | DraftAssignments revision, Crew/Employee IDs, incremental migrations |
| docs/05-DEMO-ACCEPTANCE.md | `32f9fe8` | Draft lifecycle, Employee/Foreman, desktop weekly/multi-day walkthroughs |
| docs/10-CLIENT-DECISIONS.md | `e0b657a` | Owner #14 scope, provisional AM/PM, Foreman boundary, unsettled safety rules |
| Latest accessible local UI DOCX | Rigarus_UI_Design_Updated_2026-11-22.docx | SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`; original last-write `2026-11-22T08:14:42.434606Z` |
| Current acceptance | #16 multi-day / #35 weekly records | Exact binaries, migration and offline limits; prior results do not certify this new code |
| Current GitHub Issues | #22/#71/#15/#23 | Explicit membership before personal calendar; unresolved Draft conflicts never authorize Publish |

Local original DOCX text and images were freshly extracted. Locators are XML paragraph numbers, not rendered page numbers. Read P122–126 (UI 02, image12.png), P142–151 (UI 06/07), P177–226 (UI 13–22); inspected original UI 02 image12.png, UI 13 image8.png, UI 16 image25.png and UI 07 image17.png. The mockups are concepts. Full DOCX, originals, raw logs, databases and screenshots remain local. Original customer XLSX/PDF files were not used.

## Design Compliance Checklist

| Requirement / status | Existing code and intended change | Acceptance case |
| --- | --- | --- |
| Explicit dated employee IDs — approved development scope | #22 owner clarification: never expand Home roster into actual attendance. Add explicit choices per existing stable visit ID; label Draft workers / Validation pending | Two employees share Home Crew, select only one; employee query excludes the other |
| Crew Board and detail — UI 02/13 | Existing weekly source buttons/details read DraftAssignments. Display the same persisted worker selection on Job/Crew cards, including individual AM/PM sources in multi-day strips | Borrow worker into another Crew; labels identify borrowing, original Home Crew unchanged |
| Empty / inactive / missing — #22/#71 | No choice is unconfigured; explicit empty choice is distinguishable and unpublishable. Show inactive/Unverified status without inventing a new eligibility gate | Empty save, inactive employee, nonexistent ID, no matching search, no employees |
| Persistence / audit / revisions — data model | Add tables only, shared assignment revision and write transaction; append-only recorded names/Home Crew snapshots | Race selects one winner; failed member/audit insertion rolls back; restart retains choice and old notes/IDs |
| Visit context edits — engineering safeguard | Crew/WorkItem/date/slot changes invalidate current selection with a retained audit event; note-only edits preserve it. Moving back cannot resurrect old staffing | Change each identity field, reconfirm; change notes; compare history |
| No write before Save | Native checkbox selection/Cancel makes no write; history/range reads are read-only | Compare synthetic SQLite main/WAL before/after Cancel |
| Calendar handoff | Add `employee_id` to existing inclusive date-range assignment read and authenticated Rust query bridge | AM/PM, cross-year, borrow, empty worker, cancellation excluded by default |
| Hard safety remains pending | #15 allows unresolved Draft choices; #23 driver and #22 leave/minimum/qualifications remain separate. No Publish/export route | All returned rows Pending / publishable false; disabled Publish retained |

## Implementation Plan

Add pure staffing types/ID validation, separate SQLite snapshot helpers/store, migration eight and API routes. Reuse authenticated loopback, Rust ownership and existing assignment revision checks. Persist explicit selections and audit in one transaction; no Home Crew, driver, Project, WorkItem, note or Rig writes. Read assignment+members in one SQLite snapshot. Recognized legacy files upgrade transactionally; old binaries require the original consistent pre-upgrade backup, never an operational schema downgrade.

UI: one embedded workers section in the existing detail dialog; labelled searchable checkboxes with IDs/Home Crew/borrowing/inactive/driver status; explicit Save/Cancel; current selection, empty/search-empty, busy/disabled, failure/reload and history states. Use existing dialog focus/escape behavior and match surrounding layout; no redesign or new dependency. Preserve input on uncertain errors, require explicit reload/discard before retry. After commit, clear stale board data before refresh; committed-but-unreadable status must report that outcome.

Tests: domain/API/SQLite rollback, migration seven→eight and all earlier upgrade regressions, concurrent/stale saves, cancellation and context invalidation, immutable snapshot regression, authenticated packaged-sidecar restart, native Windows worker lifecycle/reopen and visual/keyboard/narrow checks. Run locked restore/format/Windows builds, applicable CI, documentation and staged privacy scan. Use synthetic data only.

## Design differences and unresolved questions

The DOCX shows actual personnel in cards/details but has no complete persisted-membership editor. The bounded editor is an explicit #22 delivery addition using existing form/dialog conventions; it does not establish attendance terminology, approval, automatic membership or minimum size. An inactive worker may remain a Draft choice with a warning; this is not eligibility. Duplicate employee choices across visits remain unresolved Draft work for #15 and never publish. Actual Rig stays unassigned; default Rig remains reference data.

Leave types/approval/effective dates, source-Crew staffing/driver impact, full time-off persistence, skill/driver/minimum-staffing gates and customer AM/PM decision remain open/dependent work. #71 Employee Week and PDF/XLSX, immutable Published snapshots and formal distribution are not included. Engineering checks, customer acceptance and production approval are recorded separately in [the acceptance record](../acceptance/2026-11-22-issue-22-draft-workers.md).
