# Issue #28 phase two — date generator Design-First record

## Baseline

Inspected 2026-11-24; PUBLIC repository verified through GitHub. Latest fetched
main `ca503e135d0788aee1c8bf23cf843c92e1204a2f` includes merged PR #91
(head `cbd7b06994e27eb265d7a0f75f2461e15d2aae61`); no open PRs and no PR91
submitted reviews. Issue #28 remains Open, M5 / Demo E. Read linked Issues
#26/#15/#23/#24/#25/#27/#18/#29 and current calendar/comparison code/tests.
Root README, Chinese README and local design-folder changes are preserved.
Independent worktree/branch: `codex/issue-28-date-generator`.

## Design Compliance Checklist

| Source | Exists/readable | Declared version/date | Revision/hash | Checkout mtime UTC (not authority) | Read-at UTC |
| --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | Yes | November 2026 repository baseline | `d3b9bea778529c47bb502e59914cbdd0100697a0` | 2026-11-24T15:03:13.974386+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/DEV-DESIGN-CHECKLIST.md` | Yes | November 2026 repository baseline | `d3b9bea778529c47bb502e59914cbdd0100697a0` | 2026-11-24T15:03:13.979888+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/00-PROJECT-PLAN.md` | Yes | November 2026 repository baseline | `d43fa6db88660fb623572aad9450774e9cc1f880` | 2026-11-24T15:03:13.976388+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/09-DELIVERY-PLAYBOOK.md` | Yes | November 2026 repository baseline | `e6326dff3c75bc1670a73dfd37638376efd15804` | 2026-11-24T15:03:13.979386+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/02-ARCHITECTURE.md` | Yes | November 2026 repository baseline | `cbd7b06994e27eb265d7a0f75f2461e15d2aae61` | 2026-11-24T15:03:13.977386+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/03-DATA-MODEL.md` | Yes | November 2026 repository baseline | `d43fa6db88660fb623572aad9450774e9cc1f880` | 2026-11-24T15:03:13.977386+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/05-DEMO-ACCEPTANCE.md` | Yes | November 2026 repository baseline | `1c23cfd9a7a6613d1d05d870f775a751768b4f87` | 2026-11-24T15:03:13.978386+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/10-CLIENT-DECISIONS.md` | Yes | November 2026 repository baseline | `cbd7b06994e27eb265d7a0f75f2461e15d2aae61` | 2026-11-24T15:03:13.979888+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/acceptance/2026-11-23-issue-28-comparison.md` | Yes | November 2026 repository baseline | `cbd7b06994e27eb265d7a0f75f2461e15d2aae61` | 2026-11-24T15:03:13.987893+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| `docs/acceptance/2026-11-23-issue-26-project-calendars.md` | Yes | November 2026 repository baseline | `d43fa6db88660fb623572aad9450774e9cc1f880` | 2026-11-24T15:03:13.987893+00:00 | 2026-11-24T15:11:55.739568+00:00 |
| Local updated playbook | Yes | v2.1 / 2026-11-24 | SHA256 `cfc0d55860073df8ebdce967080da46c0fb72279d4baccd723b77e5dc78551b7` | 2026-11-24T15:09:02.973194+00:00 | 2026-11-24T15:11:55.739568+00:00; current sections A–H/A–J read; historical appendices are not current authority |
| Local updated project plan | Yes | v2.1 / 2026-11-24 | SHA256 `098783c8d59232fe717a2f7fe7bb18719b275aabf5438e65d6e3d0679b2993b5` | 2026-11-24T15:08:37.798007+00:00 | 2026-11-24T15:11:55.739568+00:00; current sections A–H/A–J read; historical appendices are not current authority |

Relevant sections: project Scope/Milestones; playbook Gates/For each Demo;
architecture Explicit working-calendar / Explicit-option comparison; data model
Project master data / Manual Draft assignments / Shared Project and Crew
working calendars / Migration check; acceptance calendar foundation/storage,
Employee Week and active SQLite verification; decision rows #14/#22/#26/#28,
weekend and dual sorts. Updated local plan B–I and updated local playbook B/D/G
confirm G1–G3, internal Pending generation and separate customer gates.
The checklist was absent in the stale root checkout, but exists/read again in
latest main. No missing required repository source is claimed. Local original
planning files remain local, with hashes above; no full originals are uploaded.

UI figures/pages: not applicable. This slice changes only internal Python
calculation and documents; no UI/API/interaction/keyboard/loading state changes.
Original UI images were not inspected and no screenshot comparison is claimed.

| Requirement | Authority/status | Existing / planned change | Acceptance |
| --- | --- | --- | --- |
| G1 one Crew per WorkItem, inherited Project | Confirmed owner 2026-11-24; missing generation | Scope/ID checked immutable input; multi-Crew Needs Review | Civil/Tower identity, wrong context, multi-Crew |
| G2 confirmed positive remaining half-days | Confirmed owner 2026-11-24; missing | Explicit confirmation bool; missing/unconfirmed Needs Review; no estimate/draft deduction | Invalid counts, absent confirmation, saved visits unchanged |
| G3 accumulate across gaps | Confirmed owner 2026-11-24; missing | Enumerate local dates AM then PM; skip closure/unknown/conflict/known occupied/blocked evidence | Continuous, Mon/Wed/Thu/Fri, unknown, all closed |
| Weekend capacity requires consent | Confirmed conservative gate; actual approval validator missing | Skip unless explicitly supplied Satisfied for exact slot; still Pending | Missing/Pending/Blocked consent, no shorter dates |
| Independent safety checks | Existing PR91 comparison; validators Partial/Missing | Reuse evidence types/comparator; no inferred workers/Rig/driver | Each blocked check, missing evidence stays Pending |
| Small deterministic dual sorts | Confirmed; comparison Existing | One earliest cumulative plan per input Crew/earliest-date scenario, up to 100 scenarios; comparator limits 1–10 | C1 early start vs C2 early finish; stable permutations |
| Bounded planning | Existing technical maximum 366 local dates; 12-month business boundary | Inclusive end must be before next annual anniversary, Feb29 clamps to Feb28; at most 366 dates | Cross-year/leap/DST, max date, exhaustion |
| Pure proposals only | Confirmed; existing immutable core | No DB/file/network/clock, API/UI/Apply/Publish | Guard I/O; full synthetic SQLite snapshot and input equality |

No material rule conflict: local v2.1 replaces old #28 Open with owner's explicit
2026-11-24 development decision. Demo E remains unaccepted. Qualification,
weekend approver identities, actual-work deduction, multi-Crew efficiency and
continuity weights remain Open/out of scope; do not invent defaults.

## Implementation Plan (committed before product code)

1. First update decisions #28 to Confirmed (owner development scope), recording
   G1–G3 and separate Demo E acceptance. Preserve every other pending rule.
2. Add pure `recommendation_generator.py` using existing WorkCalendar,
   ProposedSlot/ConstraintEvidence, ExplicitOption and comparator. Strict frozen
   request holds option/WorkItem/parent Project/Crew IDs, required Crew count,
   explicit remaining/confirmation, earliest and inclusive horizon, calendars,
   context-scoped per-slot evidence and optional bounded Crew occupancy snapshot.
   No production context adapter or source-revision freshness certification.
3. Scan AM/PM in local date order once, index snapshots once. Only both Working
   count; known blocks and missing weekend consent skip. Other missing resource
   evidence stays Pending. Stop after N slots; insufficient result has no finish,
   includes accumulated/unfilled counts and all scanned skips/reasons.
   Complete results expose an ExplicitOption; generator/comparison wrapper reuses
   PR91 ordering/filtering and retains incomplete results separately. Always
   Validation pending / applyable=false / publishable=false.
4. Add focused boundary/invalid/determinism/no-I/O tests, synthetic whole-DB
   compatibility, and a reproducible no-DB example with actual generated dates.
   Algorithm bounded by 732 slots per request; requests at most 100.
5. Update architecture/acceptance/design records and repository-safe planning
   summaries for the confirmed scope. No migration: schema ten/IDs/history unchanged.
   No dependency/HTTP/Tauri/UI/save change; rollback is source-only, not DB downgrade.
6. Run locked restore, Ruff, full Python, bundled-sidecar build/smoke, frontend,
   Rust and legacy .NET checks, staged privacy, Windows CI. Record actual statuses.
   Native GUI/offline install/reboot NOT RUN (no connected new workflow);
   host tests cannot certify disconnected Windows/customer acceptance.
7. Draft PR refs #28/#91, evidence on Issue #28; no merge/close/Release.

## Actual execution

All new implementation/verification cases NOT RUN at this design commit.
Customer Demo E / UAT NOT RUN; production NOT APPROVED. Final outcomes will be
recorded separately in the linked acceptance evidence and PR.


## Implementation and final local checks

The [engineering record](../acceptance/2026-11-24-issue-28-generator.md) records
156 Python / 27 new tests, 11 packaged-sidecar, 35 frontend, 8 Rust and 35 legacy
.NET tests, locked restores/formats/builds and synthetic acceptance-tool harness.
Shared Project snapshot consistency was added as input validation; it preserves
inheritance rather than introducing a business rule. The per-slot scan reuses
#26's assessment with indexed single-cell calendars, avoiding quadratic lookup.
M5 milestone 6 was read live: Workdays and recommendations (Demo E), Open;
main CI 45419720452 completed successfully at the recorded baseline. Original
UI figures remain not applicable; no UI/API/migration/write path changed.
Final staging/privacy/docs and feature-head Windows CI are reported in the PR;
no native/offline GUI, customer acceptance or production approval is implied.
