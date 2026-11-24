# Issue #86 — resumed input/expansion investigation

November 23, 2026 America/Toronto. Main `ad87a521b9f75e2c7380747e06ccce1c1340e184` includes the human merges of PR87 and PR89. Reuse the existing `codex/issue-86-project-choice-uia` branch in its isolated worktree. Those merged PRs cannot receive a new code review; any further tool change needs a successor Draft PR for the same still-open Issue. Preserve root README/Chinese README/original-design work. Repository is PUBLIC.

## Current sources read

Existence, SHA256, last-write UTC and Git content revisions are recorded in local evidence; checkout timestamps are not approval dates.

| Source | Content revision | Relevant sections |
| --- | --- | --- |
| AGENTS.md | d3b9bea | Mandatory Design-First; evidence, privacy and human review |
| docs/00-PROJECT-PLAN.md | d43fa6d | Offline scope, dependency order, integration gates |
| docs/09-DELIVERY-PLAYBOOK.md | e6326df | Engineering, customer and production gates |
| docs/02-ARCHITECTURE.md | d43fa6d | Native lifecycle, read-only Employee Week, Project calendars |
| docs/03-DATA-MODEL.md | d43fa6d | Stable IDs, schema ten, WAL/consistent reads |
| docs/05-DEMO-ACCEPTANCE.md | 37bd903 | Project-choice investigation, unchanged waits, original complete flow, logical snapshots |
| docs/10-CLIENT-DECISIONS.md | d43fa6d | Draft warnings are not resource/safety approval |
| Previous #86/#88 design checklists, #35 supervisor evidence | dd12c43 / 37bd903 / e028564 | Preserved failure boundaries, raw diagnostic privacy and bounded supervision |
| Issue86, merged PR87/89 and final acceptance comments | Live GitHub | Full Hidden FIRST Project entry timeout150.195s; subsequent reduced success does not replace it |

No product UI change is planned. Original DOCX/figures are not applicable to this tool-only investigation; no fresh DOCX read is claimed. Product implementation requires a separate proven-defect Issue, affected original-page review and revised plan.

## Design Compliance Checklist

| Confirmed requirement | Current implementation/evidence | Case |
| --- | --- | --- |
| Compare full Hidden failure and reduced success | Both have enabled/onscreen/current working-owner and owned focus before a single SendWait; fail stays placeholder/Collapsed, success value changes and popup appears | Compare actual UTC/elapsed/navigation/focus/expansion/input sequence, not only screenshots |
| Determine observable input and provider response | Prior snapshots lack key/property-event sequence; closed child0 is not proof of absent Project options | Short owned-window numeric key trace plus target UIA Value/Expand/focus/enabled events; separate original keyboard, Expand/Selection and Expand+single keyboard controls |
| Retain assertion and bounded failure | Original label verification150s, GUI/exit150/60; no Save retry | Full command with new observation only; reduced controls report their narrower scope and unsupported Selection separately |
| Preserve data/package | Frozen installed0.1.0 and independent synthetic profiles | Before/after logical snapshots; closed all-table/integrity/FK/payload/process checks |
| Fix only confirmed tool fault | No product root cause established | Evidence-driven minimal tool fix and regression, or precise remaining blocker; separate product Issue before product work |

## Implementation Plan

1. Fetch/verify current main, Issue/PR/CI; reread current sources and previous actual local failure/success logs. Record source identities.
2. First use local-only diagnostics/probes. Observe the existing one-shot Project path without changing its key sequence, final label assertion, Save behavior or wait profiles. Capture target properties and a bounded short event trace only around the synthetic owned-window operation; never record unrelated-window text or credentials. OS key observation does not itself prove renderer consumption.
3. In a new no-NIC Win11x64 overlay, use the same frozen package and separate generated synthetic profiles. Compare Normal/Hidden original keyboard, UIA Expand/Selection capabilities and explicit expansion plus one original key sequence. Record unsupported patterns distinctly from a successful selection. Execute the original complete Hidden command with diagnostic observation; retain historical failures and observer timing limitations.
4. If evidence confirms a tool fault, update only necessary acceptance helpers and focused real/mock regressions. Preserve all final value/data/Save/exit assertions and finite bounds. Unknown errors fail. No new business defaults, API, persistence, migration, product dependencies or product changes.
5. After normal guest shutdown and process/QMP exit, audit actual reached data, complete logical records, SQLite integrity/FKs, payload and residual processes. Run appropriate PS5.1 harness/parser/docs/privacy and current-head Windows CI for any committed tool fix. Publish reviewed sanitized results in a focused Draft PR/Issues; raw traces/DBs/VMs stay local.

## Unmet items and risks at start

Exact cause remains unknown. A diagnostic observer can perturb timing; successful reduced cases do not prove the original intermittent full gate fixed. Hidden uses an interactive desktop, not Session0 or a representative enterprise-policy device. #26/#35 full native acceptance and #28 formal integration retain this risk. Customer UAT/production approval remain separate. Unexecuted scenarios are NOT RUN.

## Evidence-driven investigation refinement

The first observed comparison reproduced the same placeholder/Collapsed timeout
under Normal supervision, despite all 30 synthetic key down/up events being
observed with owned foreground and balanced modifier state. No target Value or
Expand property event followed. This locates the observed failure after OS input
injection; it does not prove renderer consumption or retroactively establish the
earlier Hidden sample's internal cause. Both native UIA Selection patterns are
unavailable on the exposed large-select proxies. One separate Normal Collapse
request also refused with `Could not open the process token`; retain that provider
failure without elevation or policy changes.

Explicit expansion followed by the same single key sequence succeeded under both
supervisors and ended selected/Collapsed. However, pre-input option diagnostics
added about 17 seconds, confounding state and elapsed time. Before changing the
formal selector, run matched local controls: expand/ack then immediately send
once without child enumeration, versus leave Collapsed and wait that same fixed
17 seconds. The fixed delay is an experimental control only, not a proposed
production wait or permission to inflate the original timeout. Keep all actual
outcomes and the original final selected-label assertion. A complete observed
Hidden run also passed both Project entries and lifecycle checks; this does not
erase the preserved failure or establish that the intermittent fault is fixed.

## Tool-only implementation refinement

Matched controls disproved the proposed one-shot Expand-only fix: one Hidden
Expand returned normally but never reached Expanded within150.075s, before any
keys; delayed closed controls also passed. Do not add a fixed delay or attribute
every historical failure to an unproven native-focus or renderer defect.

The subsequent acknowledged protocol succeeded twice per supervisor. Two real
cases required2 and4 nonpersisting Expand requests before an Expanded state was
observed. Each then sent the text once, observed the target value, sent Enter
once and observed the same value with Collapsed state, within one150s budget.
Native Win32 focus was owned in these successful controls; no failing native-
focus sample establishes a specific focus bug. All twelve reduced copies retain
all16 source tables exactly, including timestamps. This establishes the necessary
tool correction: explicitly acknowledge state transitions rather than equating
focus/action-return or one mixed key batch with a completed selection. The
underlying intermittent provider/renderer no-response mechanism remains unknown.

Update only `Test-TauriDesktop.ps1`, `TauriUiaDiagnostics.ps1` and focused harness
coverage. Reuse recognized UIA transient handling only for readiness/reads;
resolve current controls and retry a nonpersisting Expand only while observed
Collapsed. Never resend text, Enter, Save or an API/database operation. Retain the
same selected-label assertion and strengthen completion to Collapsed. All phases
share the existing Default30/SlowVm150s choice deadline. Pre-input snapshots must
explicitly omit child enumeration so logging does not insert the earlier17s
delay. Keep unknown errors and timeout verdicts fatal.

Regression cases cover silent no-effect Expand, recognized transient refusal,
never-ready/disabled target, missing/ambiguous/unsupported controls, wrong/missing
value, missing commit, unknown errors, foreign foreground, single text/commit
counts and shared deadline. Keep the numeric input hook/native focus prototype
local; it is not shipped in the tool or application. After checks, run canonical
complete Normal/Hidden flows on the frozen package **without the observer**, pin
the exact new script identity, audit closed records/files/exits, run current-head
Windows CI/privacy and submit one successor Draft PR for human review. Do not
claim that diagnostic successes certify an untested canonical tool revision.
