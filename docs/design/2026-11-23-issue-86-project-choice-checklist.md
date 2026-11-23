# Issue #86 — bounded Project-choice UIA investigation

November 23, 2026, America/Toronto. Reverified PUBLIC repository, human merges of #84/#85 and latest main `fa2a9e97b156a113715ec5740896c057226ae47b`. Work is isolated on `codex/issue-86-project-choice-uia`; root README, Chinese README, local original designs and other worktrees are preserved. Issue #86 records the newly bounded investigation; #35/#26 remain open.

## Sources checked again

Existence, content revision, SHA-256 and last-write UTC are recorded in local source metadata. Checkout modification times are filesystem metadata, not design approval dates.

| Source | Content revision | Relevant sections |
| --- | --- | --- |
| AGENTS.md | `d3b9bea` | Design-First, local evidence, human review |
| docs/00-PROJECT-PLAN.md | `d43fa6d` | Offline scope; dependency order; #26 before integration of recommendations |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326df` | Separate engineering, customer and production gates |
| docs/02-ARCHITECTURE.md | `d43fa6d` | Synthetic profiles, parent/sidecar lifetime and calendar boundaries |
| docs/03-DATA-MODEL.md | `d43fa6d` | Stable IDs, schema ten, sparse calendar cells/history and consistent backups |
| docs/05-DEMO-ACCEPTANCE.md | `fa2a9e9` | Calendar reopen, UIA diagnostics, bounded waits, progress serialization/sharing |
| docs/10-CLIENT-DECISIONS.md | `d43fa6d` | Draft warnings versus dispatch eligibility, no inferred business defaults |
| #26 Project-calendar and #35 supervisor checklists/evidence | `d43fa6d` / `fa2a9e9` | Frozen package, saved synthetic fixture, actual timeout versus earlier phase PASS |
| #86, current #35/#26 discussion, #84/#85 | Live GitHub | Actual failure boundary and merged tooling baseline |

No product UI change is planned. Original UI figures are not applicable to this tooling-only slice; no fresh original-figure read is claimed. The complete original DOCX remains local. Establishing a product defect requires a defect Issue, affected original-UI review and a revised plan before product implementation.

## Design Compliance Checklist

| Requirement | Existing finding / scope | Acceptance case |
| --- | --- | --- |
| Diagnose the actual target | Prior timeout was `working-project-choice-verified`, while last diagnostic context still pointed at `working-scope` | Snapshot `working-owner` before focus, before/after keys and final verification/failure |
| Distinguish provider, focus, options and product state | No established root cause yet; an unexposed UIA option is not proof of absent application data | Current/fresh runtime identities, enabled/offscreen/value, owned focus, foreground/window state and bounded exposed children |
| Bound the investigation | Reuse a closed, frozen synthetic calendar fixture in a new no-NIC VM overlay | Normal/Hidden supervision; direct reopen and Employee Week handoff; independent per-process watchdog |
| Preserve baseline behavior first | One existing keyboard send and committed-label assertion; no Save retry | Capture the original operation before considering a tool correction |
| Preserve package/data/security | Same verified installed client/sidecar; fresh cloned synthetic profile per case | Closed-disk integrity, original-data and installed-payload comparisons; no host failure injection |
| Keep evidence truthful and local | Prior aggregate native run failed despite earlier phase PASS | Actual PASS/FAIL/BLOCKED/NOT RUN, local raw logs only, sanitized public summary |

## Implementation Plan

1. Read current sources/implementation and prior frozen failure. Record source identity and create this independent Issue/branch.
2. Add primitive-only, bounded target/focus/option snapshots in `TauriUiaDiagnostics.ps1`; instrument only the existing Project keyboard helper in `Test-TauriDesktop.ps1`. Do not alter selection, API, React, Rust, SQLite, migrations or package contents during baseline capture.
3. Reuse existing native functions in a local AST-imported read-only probe. Clone the closed saved synthetic fixture, launch/close/reopen the same installed app, optionally reproduce the Employee Week handoff, and verify saved Project calendar/history. Compare ordinary and Hidden supervisors with independent finite watchdogs. Keep the probe, raw logs, DBs and VM disks local.
4. Refine the tool interaction only if captured evidence establishes a test-tool fault. Preserve final selection assertions, failure propagation and finite bounds. If a product defect is proven, create a separate defect Issue and revise this plan before product code changes.
5. Add focused diagnostic/interaction harness regressions, document actual native results and limitations, run PowerShell 5.1 harness/parser, staged privacy/whitespace checks and current-head Windows CI. Create a Draft PR, update GitHub with sanitized findings, and wait for human review.

## Design differences and open items

No new business rule, required field, publication gate or migration. Calendar matching remains independent of personnel, approved driver, Rig, skills and weekend-consent validation. #28 design is independent; formal integration retains the failed complete native GUI gate until actually rerun. Customer acceptance and production approval remain pending.

Native case outcomes and any evidence-driven plan refinement belong in the linked acceptance record; leave unexecuted cases NOT RUN.
