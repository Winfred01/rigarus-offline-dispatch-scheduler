# Issue #25 — explicit staffing, skill and qualification requirements

Main 860e02d01c515fa8883c17759e9e1dc6fa81c205 includes human-merged PR96
(a9967a6). Issue25 Open, milestone5 M4 People/drivers/rigs / Demo D; no Open PR.
PUBLIC visibility verified live. Owner November24 priority plus Continue
approves the next resource slice. Root README/Chinese README/local designs
preserved; isolated codex/issue-25-capability-validation worktree.

## Design Compliance Checklist

| Source | Exists / declared version / reread | Last-changing revision | Checkout mtime UTC (not authority) | Read-at UTC |
| --- | --- | --- | --- | --- |
| AGENTS.md | Yes, November 2026 baseline | d3b9bea778529c47bb502e59914cbdd0100697a0 | 2026-11-24T22:48:13.260231+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/DEV-DESIGN-CHECKLIST.md | Yes, November 2026 baseline | d3b9bea778529c47bb502e59914cbdd0100697a0 | 2026-11-24T22:48:13.266232+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/00-PROJECT-PLAN.md | Yes, November 2026 baseline | 2a074876b0d8283578af7464a97ea12837c244d9 | 2026-11-24T22:48:13.261231+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/09-DELIVERY-PLAYBOOK.md | Yes, November 2026 baseline | 2a074876b0d8283578af7464a97ea12837c244d9 | 2026-11-24T22:48:13.265230+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/02-ARCHITECTURE.md | Yes, November 2026 baseline | a9967a60f2afeaf16bec590b0e16347694f804f1 | 2026-11-24T22:48:13.262231+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/03-DATA-MODEL.md | Yes, November 2026 baseline | a9967a60f2afeaf16bec590b0e16347694f804f1 | 2026-11-24T22:48:13.263231+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/05-DEMO-ACCEPTANCE.md | Yes, November 2026 baseline | a9967a60f2afeaf16bec590b0e16347694f804f1 | 2026-11-24T22:48:13.264231+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/10-CLIENT-DECISIONS.md | Yes, November 2026 baseline | a9967a60f2afeaf16bec590b0e16347694f804f1 | 2026-11-24T22:48:13.265230+00:00 | 2026-11-24T22:51:26.462250+00:00 |
| docs/acceptance/2026-11-24-issue-23-drivers.md | Yes, November 2026 baseline | a9967a60f2afeaf16bec590b0e16347694f804f1 | 2026-11-24T22:48:13.276471+00:00 | 2026-11-24T22:51:26.462250+00:00 |

Relevant sections: plan Scope/Milestones, playbook Gates, architecture actual
workers/availability/consistent snapshots/collision/driver reports, data employee
levels/Foreman history/migrations, acceptance actual staffing/Foreman/driver,
decisions open minimum/skill/qualification/effective-date rules. Inspected
Issue25 R04/R05/R06, #8/#22 dependency implementation, PR96 metadata and existing
storage/driver/roster/adapter/migration fixtures and tests. Current #23 acceptance
is engineering evidence, not customer policy authority.

Local-only UI original November22 DOCX SHA256
67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487:
XML paragraphs13 (People),152 (resource checks),218 (staffing feedback),247
(review),302 (current Foreman). No rendered page/original figure inspected.
No UI/API/keyboard/focus/ARIA/layout change; corresponding UI comparison N/A.
Complete originals/absolute paths stay local. Local updated plan v2.1 November24
SHA256 098783c8d59232fe717a2f7fe7bb18719b275aabf5438e65d6e3d0679b2993b5,
sections source lines204/215/227/297/345–346/532: per-project requirements,
Level not certification, both borrowing sides, no invented safety standard.
Playbook v2.1 November24 SHA256
cfc0d55860073df8ebdce967080da46c0fb72279d4baccd723b77e5dc78551b7,
lines185/200/311–315: configured thresholds and customer approval remain open.

| Requirement / authority | Existing / needed | Acceptance |
| --- | --- | --- |
| Confirmed owner priority / Issue25 | Actual dated workers and Level1..3 exist | Count actual available active workers, never Home Crew/Foreman expansion |
| Confirmed no invented defaults / plan D07 | Numeric thresholds, hierarchy and certificates Open | Only explicit dated confirmed WorkItem requirements; missing policy Pending |
| Proposed engineering contract | No persisted requirement/verified qualification source | Require minimum_members, all three level minima, Exact or AtLeast mode, explicit qualification count list; no default values; independent overlapping counts, not disjoint roles |
| Confirmed Level is not certification | No qualification evidence | Exact case-sensitive company-defined code + Verified/NotVerified/Unknown dated evidence; no code equivalence or legal standard inferred |
| Confirmed both borrowing sides and conflicts | #15 all-Crew snapshot exists | Evaluate all visits; inactive/unavailable/double-booked excluded, unknown observations retain possible count |
| Confirmed capability context | Civil/Tower persisted types, inactive Crews retained | Civil/Tower mismatch/inactive Blocked; Small/Other mapping Pending; real parent IDs preserved |
| Open Foreman/effective history/mergers | Current master appointment is not dated attendance | Foreman check always Pending; no promotion/merger rewrite or inferred presence |
| Confirmed consistency/read-only calculation | v3 includes drivers only | v4 related WorkItem policies, Crew type/active, qualification owner revisions/cells in same read-only view/fingerprint/budget |
| Confirmed proposal limits | No proposed workers or full gates | Saved-visit report only; generated Staffing/Skills/Qualifications/Foreman evidence stays Pending; Apply/Publish false |

No actual company thresholds, qualification codes, hierarchy or legal standards
are supplied/confirmed by this task. Support explicit requirements as input;
only synthetic tests seed values. Approval authority and actual company policy
remain owner/customer questions; recording confirmation is not authentication.

## Implementation Plan

1. Pure capability_validation.py: immutable validated requirements (positive
   minimum members, explicit three nonnegative minima, explicit Exact/AtLeast
   mode, bounded exact qualification-code counts), dated requirement/qualification
   cells with explicit confirmation/change IDs, Crew/WorkItem/worker observations.
   Reuse #15 strict visit/collision validation and #23 worker availability shape.
   Counts report required/confirmed/possible IDs and reasons: known upper bound
   below confirmed requirement Blocked; enough definite workers Satisfied for
   that subcheck only; missing/unknown Pending. Empty/unconfigured staffing Pending.
   Levels never create verified certificates; no default hierarchy. Foreman stays
   Pending; per-Crew visit scope does not certify simultaneous multi-Crew work.
2. Necessary additive schema12 CapabilityEvidenceOwners/Changes/Cells: XOR FK
   owners for one WorkItem policy or employee+qualification code, immutable owner
   and history, confirmed/reference/versioned bounded payload, exact dated cells,
   per-owner revision. No existing business fields/tables rewritten. Internal
   capability_store only, explicit requirement/qualification recording with
   BEGIN IMMEDIATE/expected revision/no-op/history/atomic rollback; no UI/API.
3. Expand read-only adapter to v4: all horizon assignments plus selected target
   WorkItem supply real parent/type/policy observations; all their Crews supply
   type/active, related employees supply dated qualification evidence. Same pinned
   transaction, budgets and fingerprint, detached sources. Add capability report
   alongside #15/#23; do not feed unstaffed proposals safety passes. Old v3 inputs
   rebuilt; old schema11 read-only inputs rejected until separate startup upgrade.
4. Tests: explicit/missing policy, Exact versus AtLeast, distinct qualification
   codes/no equivalence, known shortage versus possible unknown, types/inactive,
   borrowing both sides, collisions/cancel/empty, invalid/duplicate/limits/local
   year/leap/DST, determinism/pure I/O guards/scale; real Store no-op/history/stale/
   concurrency/partial rollback, FK/context/payload failures, schema11 original
   record preservation/failure/retry/idempotence, WAL complete old/new snapshots,
   other-Crew policy/qualification/master change staleness, logical read immutability.
5. Refresh decisions/architecture/data/acceptance/evidence. Existing schema11
   binaries reject schema12; recovery requires a verified consistent pre-upgrade
   backup and compatible binary, never remove tables/history on a live profile.
6. Locked restore/format/full Python, packaged sidecar, frontend/Rust/historical
   .NET, synthetic harness/privacy/Windows CI. Native GUI/disconnected install/
   upgrade/reboot NOT RUN; customer Demo D/E/UAT NOT RUN; production NOT APPROVED.
7. Draft PR refs25/96/28, keep Issues Open; no merge/Release/actual Draft mutation.

## Actual results

NOT RUN at design commit; actual execution evidence will be recorded separately.
