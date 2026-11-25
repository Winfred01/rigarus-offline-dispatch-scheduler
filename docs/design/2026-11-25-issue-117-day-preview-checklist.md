# Issue117 — WorkItem full-day read-only recommendation preview

## Baseline and design compliance

PUBLIC repository; inspected/fetched main `a3da29ae62a6acae77b8e6de1a8ba92c4de7affb`
includes human-merged PR114 daily consent and PR116 bilingual guides. No open PR
or existing preview implementation found. Isolated `codex/issue-117-day-preview`;
unrelated root README/language/design files and other worktrees retained.
Child Issue117 of #28/#99 follows the explicit next UI priority recorded in
Issue113 and docs/10. This is one WorkItem preview, not the entire daily cutover.

Re-read AGENTS and docs00/09/02/03/05/10, current daily weekend design/acceptance,
Issue99/113/115/117, source generator/snapshot/HTTP/Rust/Project UI and closed
writer gates. Exact Git revisions, SHA256, UTC mtimes and local original paths
are recorded locally; checkout times are not business approval dates. Current
main revisions are the versions of those sources; later records supersede old
half-day/waiting statements. PR91/92/94/95/96/97 are merged history, not open work.

Latest local original UI `Rigarus_UI_Design_Updated_2026-11-24.docx`: XML text
P69–73 and original `word/media/image65.png` **actually inspected** (L13 single
WorkItem recommendation); L01 P9–10/image53 also inspected for entry context.
These are prototype screenshots, not implemented/accepted product evidence.
Locators are zero-based XML paragraphs/media IDs, not rendered page numbers.
The latest L09 is weekend approval, not the single-item recommendation; old L09
references do not override L13. Full DOCX/images stay local. Updated local plan
and playbook November24 are reference history; confirmed November25 daily owner
decisions in the current register supersede their half-day examples.

| Requirement / authority | Implementation boundary and case |
| --- | --- |
| Latest owner Full Day/Remaining Days | Explicit positive integer Remaining Days and confirmation; no estimate/history deduction or AM/PM controls in this modal |
| L13 entry and comparison | Project WorkItems Auto-Recommend, dialog, Crew/date input, earliest finish default/earliest start; queue entry/daily boards deferred |
| Option C / no writes | Existing coherent read-only snapshot/generator; no initialization/migration/checkpoint in preview, no Apply/Publish endpoint or gate opening |
| Known incomplete safety | Unstaffed date-only alternatives remain Validation Pending; no inferred workers/default Rig/weekend consent, no feasible/safe badge |
| Explanations | Actual accumulated/unfilled dates, skipped days/reasons, missing evidence and Crew review; incomplete horizon never fabricates finish |
| Stale/async | Fingerprint re-read for the same query, manual/focus recheck; input changes/late replies/close invalidate old output; Current is read-time only, not reservation |
| UI states | Loading/empty/invalid/failed/needs-review/stale distinct; retry clears stale data; Cancel/Escape and focus return work while reads finish |
| Bounded privacy | Strict safe IDs/dates/100 Crews/1–10 results, existing read limits; response whitelist excludes full snapshots, DB paths and raw resource records |

## Implementation Plan (before product code)

1. Commit this pre-code plan. Add strict read-only preview/freshness HTTP models
   and projection using the existing daily adapter, no domain-rule change.
2. Add only preview/freshness actions to the authenticated sidecar/Rust bridge,
   rejecting unknown actions and oversized payloads. Existing writers stay closed.
3. Add Project WorkItem modal following existing Dialog/styles and L13 hierarchy.
   Explicit Remaining Days confirmation, Crew alternatives and horizon; no
   persistent preferences/evidence editors, proposals-to-Draft or new schedule.
4. Test real synthetic HTTP/SQLite unchanged data, failure/strict input/closed
   gates/staleness; pure UI state/bridge safety, actual interactions and design
   screenshots; applicable locked tests/builds, privacy and exact-head Windows CI.
5. Record actual native/offline conditions separately. No borrowed old installer
   acceptance, customer Demo/UAT signoff or production approval. One Draft PR;
   no automatic merge/Issue closure/Release.

## Explicitly unmet / intentional differences

Prototype half-days, feasible badge and active Apply are superseded by confirmed
whole-day/false-gate rules. Prototype Rig is not fabricated. Daily Job/Crew/
Employee boards, queue entry, day/evidence editing, proposed memberships, transfer
Preview/locks/transaction revalidation/Apply/audit/version recovery, publication
and PDF/Excel remain later #99/#18/#29 slices. No critical original design is
missing for this bounded read-only modal. Actual approval/Foreman/category/legal
policies remain independent Open rules, never inferred from a positive subcheck.

## Source versions and implementation outcome

At baseline a3da29a: AGENTS revision d3b9bea; docs00/09/02/03/05 revision
7604d2a; docs10 revision f966ad7. Existence/UTC mtimes and SHA256 are recorded in
the local inventory. UI November24 SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`,
local mtime 2026-11-24T23:15:38.711423Z. No original content copied into Git.
Main was re-fetched during delivery and remained a3da29a.

Implemented readonly HTTP projection, authenticated fixed-path Rust actions,
Project WorkItem modal, pure form/request state, tests and bilingual guidance.
No migration/schema18 change, dependency update or production writer opening.
Native screenshot comparison confirms L13 dialog hierarchy, explicit inputs,
dual sort and expandable reasons. FullDay/Pending and disabled Apply replace
unapproved prototype half-day/feasible/active-action examples intentionally.
Quantity-limited complete alternatives are omitted, not mislabeled incomplete.

Actual native checks used an isolated synthetic profile on a connected developer
Windows host, not a VM or installed package. Both sorts, skipped/resource reasons,
Stale after deliberate synthetic input edit, Escape/focus return, reopen reset,
invalid zero and final-build result limit passed. Narrow-screen/assistive-reader,
induced late HTTP race and disconnected installer rollout remain NOT RUN. Epoch
unit checks do not replace those interaction cases. See the detailed
[engineering matrix](../acceptance/2026-11-25-issue-117-day-preview.md).
