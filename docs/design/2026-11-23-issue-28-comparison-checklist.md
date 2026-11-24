# Issue #28 — explicit-option comparison foundation

## Baseline and authority

Inspected November 23, 2026 America/Toronto (November 24 UTC). PUBLIC repository
verified. Latest fetched main `f48f55961fb888391f5b5af51c128d08a710d203`
contains the owner's human merge of PR #90; its complete Normal/Hidden result
is separate from this slice. No open PR or existing branch for #28 was found.
Use isolated branch `codex/issue-28-explainable-candidates`; preserve unrelated
root README, Chinese README and design-folder changes.

Read live #28 (M5 / Demo E), #18 and #15/#23/#24/#25/#26/#27. Driver, actual Rig,
complete staffing/qualification and consent validators are not implemented by
the current backend. Current source has Draft visits, explicit saved workers,
recorded availability and inherited Project/Crew work calendars, not a proposal
generator. Issue text saying planned is not itself proof of implementation.

The owner now prioritizes #28 design/algorithm development and gradual resource
constraints. This bounded slice compares **explicitly supplied options** only.
Date generation from duration and availability is still separate: the owner has
been asked to confirm remaining-work, gaps and initial single-Crew semantics.
That pending question does not block independent dual sorting and explanation.
No approval of those generation rules is inferred from silence.

## Design Compliance Checklist

Sources were read again. Repository documents use the November 2026 baseline;
last-changing revisions below are versions, not fresh checkout times. Observed
checkout UTC modification times are between `2026-11-24T04:22:36.943804Z` and
`2026-11-24T04:22:36.948803Z`. Exact per-file hashes/times/read evidence stay local.

| Source | Last-changing revision | Relevant sections |
| --- | --- | --- |
| AGENTS.md | `d3b9bea778529c47bb502e59914cbdd0100697a0` | Mandatory Design-First, human/privacy gates |
| docs/00-PROJECT-PLAN.md | `d43fa6db88660fb623572aad9450774e9cc1f880` | Scope, dependency order, Option C, M5 |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326dff3c75bc1670a73dfd37638376efd15804` | Engineering / Demo / Production gates |
| docs/02-ARCHITECTURE.md | `d43fa6db88660fb623572aad9450774e9cc1f880` | Draft, actual workers, availability, inherited calendars |
| docs/03-DATA-MODEL.md | `d43fa6db88660fb623572aad9450774e9cc1f880` | Stable IDs, schema ten, local slots and future revalidation |
| docs/05-DEMO-ACCEPTANCE.md | `1c23cfd9a7a6613d1d05d870f775a751768b4f87` | Employee Week, calendar model/storage, native verification boundaries |
| docs/10-CLIENT-DECISIONS.md | `d43fa6db88660fb623572aad9450774e9cc1f880` | Earliest finish/start, independent safety checks, unknown and operator approval |

Accessible original planning copies are in authorized local planning storage;
the old root paths no longer exist. Read planning sections 4.1–4.4 (pure
proposals, R01–R12, recommendations, T06/T07/T14) and playbook 1.3/1.4, Demo E,
engineering/customer/production gates. Old WPF/private-repo assumptions do not
override the current Tauri/Python selection or verified PUBLIC visibility.
The planned `docs/04-SCHEDULING-RULES.md` is absent. No complete dispatch rule
catalogue is claimed; this slice uses the confirmed rules below only.

Latest accessible local original UI source:
`Rigarus_UI_Design_Updated_2026-11-22.docx`, SHA-256
`67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, modified
UTC `2026-11-22T08:14:42.434606Z`. Read extracted body paragraphs 89–90
(delay/pause, preview, locks, earliest finish/start, revalidate Apply) and
148–151 (Demo C and D–E). These are zero-based XML paragraph locators, **not
rendered pages**. Original figures were not inspected in this slice: no UI or
interaction change is made. Text extraction is not screenshot comparison or
native acceptance. Full DOCX/images and raw local paths remain local.

| Requirement / authority | Existing / needed change | Acceptance case |
| --- | --- | --- |
| Confirmed: Option C, preview never writes | Pure comparison of immutable supplied plans; no SQL/file/socket/API call | Forbid I/O; full synthetic SQLite logical snapshot unchanged |
| Confirmed: hard-filter unsafe options first | Any supplied Blocked check in any slot excludes the entire option before limiting | Faster unsafe C3 excluded, every constraint, late-slot conflict |
| Confirmed: earliest-finish default / earliest-start alternative | Stable local date/AM-PM bounds, other date then Crew/option ID ties | C1/C2 different orders; permutations/AM-PM ties |
| Confirmed: availability is one input only | Independent named calendar, availability, type/occupancy, personnel, driver, skill, Foreman, staffing and Rig evidence | Available/calendar checks cannot fill missing independent checks |
| Confirmed: missing remains pending; weekends need consent | Missing required evidence Pending; weekend consent required only on weekend slots | Missing/pending/blocked consent distinct; no inferred workweek/holiday |
| Confirmed: no automatic Apply/Publish | Every result always Pending, applyable=false, publishable=false, even all supplied evidence satisfied | Positive flags cannot be constructor input; no mutation endpoint |
| #28: a small configurable set and explanations | Explicit required max_options 1–10; evaluate/filter all then limit, report omitted count and per-slot reasons | Limit after unsafe filtering; empty/all-excluded; reasons retain source/state/date |
| Technical guardrails, not business policies | At most 100 input options, 732 unique AM/PM slots in at most 366 dates; strict immutable IDs/context | Wrong Project/WorkItem, duplicate/invalid/unknown evidence fail explicitly |
| No guessed continuity weights | Report raw unplanned half-days between proposed first/last only | Gapped explicit C1 explained, not scored by invented weight |
| OPEN: duration-to-date generation, remaining work/gaps/multi-Crew | No automatic allocator, no estimate deduction, no certified duration/completion | BLOCKED pending owner rule decision; compare supplied plans independently |

## Implementation Plan (output before code)

1. Add `recommendation_comparison.py`: strict immutable options/slot evidence,
   canonical explanations, known-block exclusion and two deterministic sorts.
   This is an internal comparison foundation, not a production recommender.
2. Keep each actual validator independent. Supplied Satisfied means only what a
   caller supplied, never current verified safety. Missing maps to Pending;
   even AllSuppliedSatisfied cannot enable Apply/Publish. Do not create fake
   passing adapters, infer Home Crew attendance/default Rig, define qualification
   equivalence/minimum staffing, or reuse stale evidence as actual validation.
3. Add focused algorithm and synthetic FastAPI/SQLite compatibility tests. Cover
   C1/C2/C3, all constraints, late-slot failures, independent AM/PM, weekend
   consent, deterministic permutations, limits, cross-year/leap/DST/max dates,
   immutable inputs and no I/O/committed data changes.
4. No UI states/keyboard/focus changes, HTTP contract, Tauri command, dependency,
   SQLite migration or persistence path. Existing schema/IDs/notes/visits/history
   remain; source-only internal core has no new packaged user workflow.
5. Run locked Python restore/Ruff/full regressions, Windows build/package smoke,
   documentation/whitespace/staged privacy and current-head Windows CI. Native
   UI, clean-PC install, upgrade/reboot are not applicable to this unconnected
   model and must not be borrowed from PR90 as a new pass.
6. One Draft PR; update the Issue with actual results, unresolved generation and
   validator dependencies. No Issue closure, merge or Release. Demo E/customer
   UAT and production approval remain separate.

## Execution and remaining design gaps

See [engineering record](../acceptance/2026-11-23-issue-28-comparison.md) for
actual local checks and final PR/CI evidence. The independent core does not
fulfil all of #28. Needed next: approved generation policy; real snapshot adapters
that resolve Project via persisted WorkItem FK and bind every check to current
workers/Rig/slot/revisions; #15/#23/#24/#25/#27 domain validators; #18 preview
revision/lock contract; original UI page/figure review before product UI work;
#29 transaction Apply/revalidation; customer acceptance. No missing original
design is fabricated or replaced by this checklist.
