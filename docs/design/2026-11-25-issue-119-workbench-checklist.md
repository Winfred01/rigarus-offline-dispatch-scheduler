# Issue119 — Full Day weekly workbench, first read-only slice

## Design Compliance Checklist

Baseline main6d93916c5891b1b988996ff683c659712c3b7c43 includes human-merged
PR118. PUBLIC visibility/no open PR verified. Root README/language/design files
and previous worktrees retained. Issue119 child of99/16; milestone3/Demo B is a
delivery label, not customer acceptance. Owner November25 next priority is daily
workbench → independent daily editor → human Apply/version recovery → formal
company/Crew/employee PDF/Excel. This bounded first slice implements visibility;
daily editor follows independently. It does not complete that operating loop.

Re-read current AGENTS; docs00/09 scope/milestones/gates; docs02 current full-day
resources/readonly preview, day snapshot/compatibility, Locate and desktop
projection; docs03 schema18 and daily/legacy identity/occupancy/history; docs05
daily resource/day compatibility/Locate acceptance; docs10 confirmed daily owner
rules and open authority/policy. Also read current Issues99/16/119, PR118 and
current117 evidence, old Locate checklist, actual HTTP/SQLite/Rust/React tests.
Versions: AGENTS d3b9bea;00/09/03/05 7604d2a;02 79e14eb;10 f966ad7.
Local inventory retains exact SHA256/UTC mtimes (checkout time is not authority).

Latest accessible original UI November24 DOCX SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c,
mtime2026-11-24T23:15:38.711423Z. Actually reread L01 P9–13/image53,
L03 P19–23/image55, L14 P74–78/image66 and viewed those original images.
Paragraph/media locators, not verified page numbers. L02/L08/L13/L20 text also
read; their additional figures not claimed inspected. These are prototype
screenshots, not product/acceptance evidence. Originals remain local.

| Requirement | Existing / planned implementation and case |
| --- | --- |
| L01 real Job Schedule / Crew Board, Sun–Sat | Existing desktop sees only legacy visits; add one bounded coherent weekly source for both record kinds, shared grids and empty cells, date jump/filters/internal scroll |
| Explicit Full Day owner rule | Day cards no AM/PM encoding; retain raw legacy slots, IDs, notes and Needs Review. No merging/progress deduction |
| L03 exact saved record Locate | Typed FullDayDraft/LegacyHalfDay+ID, reread current state and whole target week in same snapshot; never use integer alone. Close detail/review, reveal filters, center/focus exact card;2second static/reduced-motion cue |
| L14 actual staffing/resource reasons | Reuse current independent saved personnel/driver/capability/Rig/consent validators, explicit calendar feedback; known blockers/unknown stay distinct; no default Rig/Home Crew attendance inference |
| L13 recommendations visible from workbench | Reuse merged real readonly modal for persisted WorkItem; no synthetic overlay/reservation/saved assignment |
| Safe rollout | Loading/error/retry/stale-response/removed/cancelled states; no writes from read/cancel/Locate, no migration. Legacy compatibility entry retained distinctly |
| Independent daily editor | Not implemented by this first read-only PR. Follow-up must add explicit full-date create/edit/cancel/revisions, uncertain outcomes, mixed occupancy, restart/offline evidence before write rollout |
| Apply/version/export | Remain later18/29/17/32, overall Pending and Apply/Publish false. Prototype active save/lock/validated/published examples are not authorization |

No critical source absent for this first visibility slice. Exact approver,
Foreman/date/category/legal policy and legacy conversion remain unresolved; no
new hard business defaults are introduced. Missing source/unknown read must fail,
not become safe empty data. Actual native/offline/customer checks stay separate.

## Implementation Plan — before product code

1. Commit this plan. Add `schedule_workbench.py` readonly reader/API and one
   fixed Rust command: week range and typed Locate only, no writer path. One
   pinned schema18 read transaction, shared existing100k units/64MiB/30second
   budget, whitelist projections. Reuse current daily snapshot source helpers
   and pure saved-resource validation; no copied algorithms or migrations.
2. Add pure typed card identity/date/filter/grouping helpers and a React daily
   workbench for Job Schedule/Crew Board. Preserve legacy component behind an
   explicitly labeled compatibility entry; main/day global Locate retains kind.
   Source details/review, date navigation, retries and old/new records use the
   same result; independent actual workers versus Home roster, no false-safe badge.
3. Reuse L13 modal from WorkItem choice/detail. No saved recommendation overlay,
   new day editor/calendar writer, delay/locks/Apply/versions or formal export.
   Async request identities clear old week/results, guard unmount; Locate is
   read-only and never silently discards a currently open editor. Actual card
   DOM IDs include kind and ID, internal centering/sticky header and2second cue.
4. Test colliding numeric IDs, current/moved/cancelled/missing typed targets,
   daily+legacy details/notes/workers, cross-year/leap/local dates, known conflicts,
   no-write logical/integrity, coherent concurrent reads, bounds/errors and
   closed writes. Frontend pure projection/timers/request cases, locked restore,
   format/Windows builds/backend/packaged/frontend/Rust/.NET/privacy and CI.
5. Observe actual native synthetic desktop states and original design comparison;
   record connectivity/package/hash and coverage limitations honestly. One Draft
   PR, human review, no Issue closure/merge/Release/customer DB.

Legacy acceptance continuation must explicitly enter the compatibility view when
the new default board is present; retain every original card/date/save/reopen
assertion. A narrowly optional navigation hook in the existing verifier is part
of preserving that tool, not evidence that the full native legacy suite passed.

Final source review found that Today / same-week Go invalidates the active read
without changing its effect key. Navigation must always request a new bounded
read, including unchanged week ranges, so a cancelled request cannot leave the
board permanently loading. Rebuild and check the same-week native interaction.
