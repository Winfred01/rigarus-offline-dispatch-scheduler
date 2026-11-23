# Issue #35 — supervisor progress serialization

November 23, 2026, America/Toronto. This slice diagnoses the outer local VM supervisor, not a new product UI or business rule. Latest main is `3543e2ca05e76ee69a45287c065e5e043afa6e81`; PR #81/#82 tooling is already merged. PR #84 at `d43fa6d` is open and was manually marked ready for review; preserve that state and its product changes. Work uses an isolated `codex/issue-35-supervisor-finalization` branch. The repository is PUBLIC. Root README/design changes, existing packages, databases and VM base disks stay intact.

## Sources read again

Existence, content revision, SHA-256 and filesystem last-write UTC are recorded locally for every required source. Checkout timestamps are metadata, not approval dates.

| Source | Revision read | Relevant sections |
| --- | --- | --- |
| AGENTS.md | `d3b9bea` | Design-First, local evidence, human/data boundaries |
| docs/00-PROJECT-PLAN.md | `cc9613a` on main; `d43fa6d` follow-up | Offline/single-operator scope; owner dependency order in PR #84 |
| docs/09-DELIVERY-PLAYBOOK.md | `e6326df` | Engineering versus Demo/Production gates |
| docs/02-ARCHITECTURE.md | `7435f35`; compare `d43fa6d` | Parent/sidecar lifetime, Draft and calendar boundaries |
| docs/03-DATA-MODEL.md | `a2f9fa2`; compare `d43fa6d` | Separate synthetic profiles, stable IDs and consistent backups |
| docs/05-DEMO-ACCEPTANCE.md | `7435f35`; compare `d43fa6d` | Native GUI, UIA, bounded waits and current calendar scenario |
| docs/10-CLIENT-DECISIONS.md | `7435f35`; compare `d43fa6d` | No inferred safety/publication approval; confirmed owner priority |
| #35 UIA checklist/evidence | `41784e2` content on main | Original selector failure versus hidden-window behavior; previous native success |
| #26 calendar checklist/evidence and current #35/#84 discussion | `d43fa6d` / live GitHub | Two final native PASS logs with blocked outer summary, not aggregate exit zero |

There is no product UI change, so original UI figures are not applicable to this tooling slice. No new original-figure read is claimed and the complete DOCX stays local. If a product defect is later established, stop this scope, create its defect Issue and inspect the affected original UI before product implementation.

## Design Compliance Checklist

| Requirement | Current finding / action | Acceptance case |
| --- | --- | --- |
| Locate the stalled phase instead of repeating full runs | Read frozen logs; isolate tail reading, serialization, serial calls, process polling, exit and transcript close | Independent short-lived child/watchdog, before/after local stage markers |
| Preserve the original package and native assertions | Change only test progress extraction and guidance | Verify unchanged installer/installed client/sidecar hashes; rerun the same native verifier |
| Logs contain text, not arbitrary runtime objects | Get-Content strings carry six filesystem note properties on Windows PowerShell 5.1 | Exact depth-10 reproduction stalls; plain text serializes promptly; real-file depth-12 harness round trip |
| Keep failures visible and waits finite | Missing/empty event differs from actual read error; no Save retry or timeout relaxation | Locked-file error propagates; raw/fixed probes have independent finite watchdogs |
| Privacy and human review | Raw metadata, paths, diagnostics and SQLite stay local | Only sanitized record/checklist/scripts in Draft PR; no merge, Issue closure or Release |

## Implementation Plan and refinement

1. Inspect main, Issues, PRs, source metadata and prior local failure evidence. Preserve the owner-set review state of PR #84.
2. Before product changes (none planned), announce a tool-only plan: short synthetic probes around each possibly blocking operation. Confirm the specific failing boundary before coding a fix.
3. The host exact reproduction identifies deep JSON serialization of an extended Get-Content string. Add `Read-AcceptanceProgressText` to existing `TauriAcceptanceSupport.ps1`; materialize `.ToString()` before a progress object is serialized. Reuse it in the local VM wrapper. No HTTP, Rust, frontend, database, dependency, publication, UIA action or wait-profile change.
4. Extend the existing acceptance harness with a real decorated-file fixture, primitive-only JSON round trip, missing/empty/non-file inputs and a locked-file failure. Keep existing wait/sidecar/UIA/WAL tests.
5. Document the safe progress boundary and independent watchdog requirement. In an isolated no-NIC guest compare the unchanged raw depth-10 boundary with the fixed reader, then execute matching native scenarios. Capture the actual exit summary and closed-disk evidence; retain any failure.
6. Run PowerShell 5.1 harness/parser, documentation/whitespace/privacy checks and current-head Windows CI. Product builds are not repeated locally for support/docs-only changes; CI still performs its standard locked restores/builds/tests. Create a focused Draft PR and update #35/#84 with scoped results.

No business default needs a new decision. Engineering evidence does not grant customer acceptance or production approval. Driver/personnel/Rig/consent gates, recommendations and publication remain outside this slice.
