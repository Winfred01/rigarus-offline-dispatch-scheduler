# Issue #35 — native Crew selector regression

## Baseline and sources

Approved slice: diagnose and repair the native acceptance regression following the first AM Draft, then rerun Employee Week / availability / explicit Draft workers and reopen. PR #81 was human-merged as `a7650c7022dc1cd1495ce0e760c9909678836a81`. Work starts from this verified main on isolated `codex/issue-35-uia-regression`. The repository is PUBLIC. Existing root README/design changes and other worktrees remain untouched.

All required sources were reread in this session; existence, UTC filesystem modification, Git revision and SHA-256 are recorded locally. Checkout timestamps are not approval dates.

| Read source | Content revision | Relevant section |
| --- | --- | --- |
| AGENTS.md | `d3b9bea` | Mandatory Design-First 1–12 |
| docs/00-PROJECT-PLAN.md | `cc9613a` | Offline scope, M2/M4 and M7 engineering |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326df` | Engineering, Demo and Production gates |
| docs/02-ARCHITECTURE.md | `f7e650c` | Manual Draft assignments, explicit workers, recorded availability, Employee Week |
| docs/03-DATA-MODEL.md | `a2f9fa2` | Stable IDs, Draft/Cancelled, revisions, schema nine |
| docs/05-DEMO-ACCEPTANCE.md | `f7e650c` | #14/#22/#77/#71 native lifecycle and interactive-desktop requirements |
| docs/10-CLIENT-DECISIONS.md | `a2f9fa2` | Administrative availability, explicit staffing, unpublishable Drafts |
| #35 stable offline record/checklist, PR #81 and current #35 discussion | `8da57cf` / live GitHub | Frozen core PASS versus subsequent GUI FAIL; exact tested package |
| #22/#77/#71 Design-First checklists | Current checked-in versions | Existing screen/state boundaries and actual-worker/calendar scenarios |

Latest accessible original local UI source metadata was checked: `Rigarus_UI_Design_Updated_2026-11-22.docx`, SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, original last-write UTC `2026-11-22T08:14:42.434606Z`. This task initially changes only test tooling, with no product UI/behavior change, so original figure comparison is not applicable at this stage; no fresh figure read is claimed. The original stays local. If diagnostics establish a product defect, create a defect Issue and reread affected original pages before that implementation.

## Design Compliance Checklist

| Requirement / authority | Existing implementation and planned action | Acceptance case |
| --- | --- | --- |
| #35 / #81 exact package | Keep original installer and installed client/sidecar unchanged; clone only a synthetic test disk | Verify source manifest/hash and all 87 installed file hashes, preserve default database |
| #14 stable Draft flow | Observe actual native Crew/select patterns around the second assignment | Two Crews, one WorkItem, saved first AM visit, repeat/select another Crew |
| Exception evidence requested by owner | Current catch logs type only; add local sanitized complete exception chain, invocation/stack and UIA before/after properties | Actual failure plus synthetic nested/stale-element diagnostic regression |
| Interactive desktop requirement | Compare visible UI script and hidden supervisor; inspect visibility, focus and bounded waits | Preserve both failures and successes; no headless result inferred from CI |
| #22/#77/#71 invariants | Exercise current explicit-worker, unknown/available/unavailable and read-only planning boundaries | Cancel no-write, cross-year AM/PM, advisory status, borrowed Home Crew unchanged, disabled publication/export, restart persistence |
| Human/privacy gates | Raw JSONL/logs/DB/screenshots stay local; publish sanitized conclusions | Separate Engineering, customer acceptance and production statuses |

## Implementation Plan

1. Instrument `scripts/Test-TauriDesktop.ps1` at the exception and native selector boundaries. Put local-only sanitized diagnostic helpers in `scripts/TauriUiaDiagnostics.ps1`; include this support file in the acceptance-kit generator. Do not dump clipboard, credentials, arbitrary desktop trees or customer data.
2. Add an opt-in minimal Crew-choice reproduction that uses a unique synthetic profile. Reuse existing product commands/GUI, current timeout profiles and matching installed executable. Compare normal/hidden supervision and pre/post UIA identity, enabled/focus/offscreen/value/pattern state. Preserve the original selector logic until a diagnostic failure is captured.
3. If the cause is the tool, change only the failing automation/launch behavior and add focused synthetic harness regressions. If it is product behavior, first create the required defect Issue, update this design plan and use a separate Draft PR for that defect.
4. Rerun minimal cases and the complete `-IncludeEmployeeWeek` chain with availability, staffing, Draft lifecycle, save/reopen, normal exits and default-data preservation in the disconnected guest. All waits and supervisors have finite limits; raw failed evidence remains local.
5. Run PowerShell parsing/harness tests, whitespace/document/privacy checks and Windows CI. Record native PASS/FAIL/BLOCKED/NOT RUN independently; create a Draft PR for human review and update #35. No auto merge, Issue closure or Release.

No API, domain rule, SQLite migration, dependency or product UI change is planned. Qualification/driver/Rig compliance, approved leave, automatic planning, Published snapshots and actual exports remain separate; Available never grants dispatch approval. Results and any confirmed cause will be recorded in a separate acceptance document after actual execution.

## Diagnostic findings and tool-only refinement

The instrumented full baseline failed at native `Expand()` on `assignment-crew` (exit 1, 333.254 s). The complete chain is MethodInvocationException → InvalidOperationException (`0x80131509`) from `UiaCoreApi.CheckError`. The window was visible/foreground; the target enabled, focused and on screen. Old and freshly resolved Runtime IDs were equal. This capture does not support a detached control or missing focus as its cause. The unhandled UIA refusal escaped the existing polling callback immediately instead of consuming its remaining bounded readiness wait.

A reduced original-cadence run failed at the same Expand call before its first Draft save (87.742 s); a previous reduced run had passed. The defect is not dependent on saved AM data. Historical #81 did not retain its inner exception, so these observations must not be used to assert that every past failure arose from the exact same native method. No product defect is demonstrated; no product fix/defect Issue is required for this tool-only change.

Refinement: one bounded selection probe re-resolves the control/pattern, verifies an already-committed desired label before repeating selection, permits only recognized UIA-operation exceptions to continue, and records fatal versus retrying evidence separately. Save buttons, HTTP, SQLite and assertions remain outside this retry boundary. Unknown/denied/unsupported errors stay fatal; persistent provider refusal remains a timeout. Exact labels and explicit metadata/status delimiters replace arbitrary prefix acceptance.

The hidden-supervisor baseline failed in 187.079 s. An initial one-time visibility correction still failed in 190.259 s; the later Win32 visibility was false despite misleading UIA flags. The refined tool checks PID ownership and visibility/minimization on every bounded GUI probe, restoring only the verifier-owned application window. It resets the handle for each launch and records before/after state. No host security, power or clock setting is changed.

Actual fixed reduced runs passed under Hidden (95.047 s) and Normal (101.480 s) supervision. The full Normal-supervisor Employee Week/availability/staffing/Draft/reopen chain passed in 631.149 s, including recovery from one genuine native Expand rejection. Independent final audits found integrity/FKs healthy and the default original data plus all 87 installed-file hashes unchanged. See [the complete acceptance record](../acceptance/2026-11-23-issue-35-uia-regression.md). Full Hidden supervision, other endpoints and customer/production gates remain separately untested; no result is inferred from CI.
