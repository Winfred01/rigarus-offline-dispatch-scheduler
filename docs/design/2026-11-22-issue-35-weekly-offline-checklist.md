# Issue #35 weekly desktop offline verification checklist

## Baseline and source identity

Independent branch `codex/issue-35-weekly-offline`, verified main `e0fc234e590c9ce6df74589e7cee00fc2b5af09e`. PR #72 (#14) and PR #73 (#16) were manually merged. No competing open PR was found. Current code already implements #22 Stage A home-roster/current-Foreman/default-Rig display; do not duplicate it or claim Stage B actual staffing exists. M2 / Demo B customer acceptance remains pending. This is #35's bounded engineering installation/verification slice, not the full M7 production gate.

Repository visibility is PUBLIC. The original workspace README/design changes and other worktrees are preserved. Complete original designs, databases, backups, diagnostics and screenshots remain local.

The following sources were read again this session; current checkout modification times were recorded at November 22, 2026 13:02:24 UTC, independently of authoring dates. Markdown sources declare a November 2026 planning baseline rather than release versions.

| Source | Inspected content revision | Relevant sections |
| --- | --- | --- |
| `AGENTS.md` | `d3b9bea778529` | Mandatory Design-First, privacy and human gates |
| `docs/00-PROJECT-PLAN.md` | `cc9613a61a09` | Offline scope, M2 and M7 gates |
| `docs/09-DELIVERY-PLAYBOOK.md` | `e6326dff3c75` | Engineering / Demo / Production separation |
| `docs/02-ARCHITECTURE.md` | `da66698fd994` | Authenticated local sidecar; desktop framework/week projection |
| `docs/03-DATA-MODEL.md` | `587a3ec620e7` | Seven migrations, stable IDs and backup/fallback |
| `docs/05-DEMO-ACCEPTANCE.md` | `e0b657aba5b6` | Native/offline conditions; superseded selected-date verifier; weekly cases |
| `docs/10-CLIENT-DECISIONS.md` | `e0b657aba5b6` | Confirmed desktop shell; provisional half-days; open safety rules |
| #16 engineering evidence | `da66698fd994` | Native host pass; matching disconnected installer and normal exit not yet run |

Current #14/#16/#22/#35 and #42 were inspected through GitHub. #42 engineering evidence is historical; its open Issue does not imply the merged Tauri migration is absent. #35's prior PR #69 installed-package evidence establishes the synthetic installed-image baseline, not acceptance of the new #73 package.

Latest accessible original: `Rigarus_UI_Design_Updated_2026-11-22.docx`, declared November 22, SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, modified UTC `2026-11-22T08:14:42.434606Z`. Fresh OOXML extraction and original embedded UI 01 / 04 / 13 images were inspected. Relevant text: P043–P114 Schedule; UI 01 P199–203, UI 04 P214–218, UI 05–10 P219–248, UI 13–14 P259–268. These are original concept images, not executed screenshots; rendered page numbers are not claimed. Exact local paths and full metadata stay in local evidence.

## Design Compliance Checklist

| Requirement | Existing code / required work | Acceptance |
| --- | --- | --- |
| Actual seven-day boards, UI 01/13 | #73 is merged; old verifier still expects a single-day table | Read actual Job Schedule / Crew Board cards by stable Assignment ID/date/slot |
| Assign/edit/cancel, UI 04–09 | Existing #14 API and modal details; no new domain rule | Actual UI save, definite conflict/correction, edit, Keep/confirm cancel, freed-slot reuse, reopen |
| Exact WorkItem identity | Existing Civil/Tower IDs remain authoritative | Read selected editor option by ID after restart; do not depend on adjacent accessibility text being coalesced |
| No-write unsaved Cancel | Existing close-only form | Compare synthetic main DB + WAL digest; ignore transient SHM reader locks; assert saved cards unchanged |
| Nine Crews / 100+ Projects | Available master-data and bulk UI | Generate synthetic records via GUI; scroll real native table; compare left/right row geometry and sticky dates |
| Long/wrapped roster | Design allows taller rows; no member/name-length rule confirmed | Last row's top and bottom must both be reachable, with aligned cells. Do not require a row taller than the body viewport to fit simultaneously |
| Draft safety, UI 10 | No personnel/driver/Rig/leave publication validation | Publish remains unavailable; Home roster and time-off-not-configured warnings stay explicit |
| Offline install/upgrade and retention, #35 | Original #73 CI package available | Verify archive/build/installer identity; independent no-NIC non-admin VM; preserve original rows/IDs/notes and compare normal reopen/reboot |
| Reliable native automation | Native options use SelectionItem; aria-pressed cards use Toggle; HTML date SetValue can silently do nothing | Use supported UIA patterns, native locale date segments and committed-value check; retain bounded failure diagnostics |

## Implementation Plan

1. Preserve and hash the original #73 CI kit; verify its build commit tree equals `da66698` and merged `e0fc234`. Do not rebuild/patch the tested installer. Keep a verified final local candidate separate from CI installed-package evidence.
2. Update `scripts/Test-TauriDesktop.ps1` only: native option/card actions, date navigation, modal completion conditions, actual weekly-card assertions, private synthetic DB/WAL no-write digest, GUI-created scale fixture, scroll geometry and normal process-restart/exit checks. Use the target window's DPI when sizing the test window. No product UI/API/schema/dependency changes.
3. Extend `scripts/Test-TauriAcceptanceHarness.ps1` with CI-compatible regression checks of actual helper functions: locale date layouts/invalid inputs, read-only versus DB/WAL mutation, exact stable card identities and bounded missing-card diagnostics. Keep original installer-failure, GUI-timeout and sidecar-failure tests.
4. Reuse an authorized disposable overlay over the existing PR #69 synthetic installed image. Capture a consistent pre-upgrade backup; upgrade in place, verify default-path original data, save/reopen a default-profile Draft, run the full new native smoke against the installed program, then reboot only this VM and verify again. Distinguish same-version-number overwrite from a version-increment upgrade. Local launchers and worker waits must be bounded.
5. Record actual PASS/FAIL/BLOCKED/NOT RUN, package hashes/conditions and tool limitations in the engineering record and GitHub. Run syntax, harness regressions, staged whitespace/privacy and Windows CI. Create a Draft PR for human review; never merge, release or close Issues automatically.

## Open gates and risks

No new SQLite migration is introduced; the original #73 program upgrades supported older schemas to its existing seventh migration. Older binaries require their verified pre-upgrade backup for fallback. Do not edit migration history.

Native UIA scroll actions do not certify physical wheel/scrollbar dragging or human assistive-technology use. The VM is not a representative corporate policy device. Missing-WebView2 clean install, version-number changes, uninstall/reinstall, interrupted setup recovery, cross-machine application backup/restore, actual staffing/leave, final AM/PM rules, full safety/immutable publication, customer acceptance and production readiness remain separate unless explicitly executed and recorded. See the [engineering record](../acceptance/2026-11-22-issue-35-weekly-offline.md).
