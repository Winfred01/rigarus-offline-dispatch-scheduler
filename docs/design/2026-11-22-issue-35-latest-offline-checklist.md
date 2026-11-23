# Issue #35 — latest offline acceptance Design-First record

## Baseline and inspected sources

Bounded documentation/validation slice only: original latest CI installer in an isolated disconnected guest. No new product or UI implementation. Verified PUBLIC repository, fetched main `cb1da4892b8945c937dfa4fba8d56dcb47864f71`, isolated branch `codex/issue-35-latest-offline`. Root README/design changes and unrelated worktrees remain untouched. PR #78 and #79 were already human-merged; the original #79 package has the same source tree as main. Current #35, #26 and #28 were read; their remaining acceptance gates are not assumed complete.

The following current files were read again. Git content revisions are authoritative source identities; checkout modification times (recorded locally) fall between `2026-11-23T02:32:49.523586Z` and `2026-11-23T02:32:49.528837Z`, not authoring/approval times. Markdown planning summaries declare a November 2026 baseline rather than release versions.

| Source | Last-changing revision | Related sections |
| --- | --- | --- |
| `AGENTS.md` | `d3b9bea778529c47bb502e59914cbdd0100697a0` | Mandatory Design-First; privacy, human review and actual test evidence |
| `docs/00-PROJECT-PLAN.md` | `cc9613a61a09bee488255b96ac7f2e581b45a1a2` | Scope; M5/M7/M8 gates; proposals require operator approval |
| `docs/09-DELIVERY-PLAYBOOK.md` | `e6326dff3c75bc1670a73dfd37638376efd15804` | Gates; package identity and separate Engineering/Demo/Production decisions |
| `docs/02-ARCHITECTURE.md` | `f7e650c63d9217a10e5127d53f85aa54fa908fc9` | Tauri migration; recorded availability; Employee Week projection |
| `docs/03-DATA-MODEL.md` | `a2f9fa25bcbfb0be555a6979f9c8be744f51dde6` | Stable Draft/employee IDs; schema nine; migration check |
| `docs/05-DEMO-ACCEPTANCE.md` | `f7e650c63d9217a10e5127d53f85aa54fa908fc9` | Recorded availability; desktop weekly planning; Employee Week |
| `docs/10-CLIENT-DECISIONS.md` | `a2f9fa25bcbfb0be555a6979f9c8be744f51dde6` | Three-state availability; no inferred attendance/leave/qualification; explicit Draft workers |
| `docs/08-RELEASE-HANDBOOK.md` | `ad996ad9f84044ead31c69439428eb52fc5cb30f` | Offline kit, SlowVm bounds and diagnostic exit codes |

Also inspected: #71 engineering acceptance and prior #35 weekly-install evidence, original CI kit/scripts, current installer configuration and existing installed-lifecycle helpers. Their older passes are not acceptance of this package.

Latest accessible local original UI design: `Rigarus_UI_Design_Updated_2026-11-22.docx`, SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`, modified UTC `2026-11-22T08:14:42.434606Z`. Existence/hash/metadata checked; original figures were not re-read for this no-UI-change acceptance attempt. UI implementation and visual redesign are not applicable. Existing #71/#77 verifiers were reused; no invented image/page references or new design requirements. The complete DOCX and exact local path remain local as instructed.

## Design Compliance Checklist

| Requirement / authority | Existing implementation and acceptance case | Actual outcome / gap |
| --- | --- | --- |
| #35 and delivery gates: offline use without SDKs | Original NSIS package and original offline verifier; no package modifications | Environment/hash/setup checks passed; actual first launch failed |
| Availability decision: unknown stays unknown; Available is not eligible/assigned | Existing schema-nine records and read-only Employee Week projection | Preserved, no rule change; current guest frontend did not become ready |
| Stable IDs, notes and migration compatibility | Existing supported migrations and installed-lifecycle helpers | Latest-package upgrade/restart comparison NOT RUN; no schema edit |
| Demonstrate actual GUI and normal sidecar lifecycle | Bounded Data/frontend readiness, native verifier and process evidence | GUI timeout, no sidecar observed; no false normal-exit pass |
| #26 before #28, as requested by owner | #26 depends on schedule engine; #28 also requires validation/calendars | Future sequence recorded only; default Crew calendar and safety rules not invented |
| Separate engineering/customer/production | Actual results matrix with package hashes and image limits | Offline gate incomplete; customer acceptance NOT RUN; production NOT GRANTED |

## Implementation Plan and execution boundary

1. Preserve the unmodified original CI kit and verify main/build/tree/hash identity. Run the original SlowVm verifier in an isolated guest with networking disabled and only synthetic mappings.
2. Capture account/OS/tool/runtime preflight, setup exit/duration, actual frontend readiness and process state. Only proceed to Employee Week, original-data upgrade/reopen/reboot checks after usable first launch. All waits are bounded.
3. Preserve original failures. Keep separate image probes/registration diagnostics explicitly outside acceptance; do not patch product startup, lower its requirements, set runtime overrides or infer qualification from Available.
4. Add only this checklist and the [sanitized engineering record](../acceptance/2026-11-22-issue-35-latest-offline.md). No UI states, API, Tauri command, domain rule, dependency, data migration or product code is changed. Run Markdown/link, staged whitespace/privacy checks and report actual branch CI separately from prior package CI.
5. Push the focused documentation branch and open a Draft PR. Keep #35/#42 open; human review only. Do not develop #26/#28 in this slice.

## Design differences, remaining questions and delivery gates

The default Sandbox account is elevated, its registered WebView2 is not discoverable by the default loader, and the older evaluation VM had interrupted the prior attempt. The installation phase's exit 0 cannot override the blank GUI/runtime error. A healthy authorized Windows 11 x64 image with usable runtime discovery or a verifiably absent runtime is still required. This is an environment dependency, not a missing UI source or confirmed product root cause.

No original-data mutation was performed on the host, no business decision is needed to document the failure, and no new business default was approved. Crew/WorkItem calendar defaults, override precedence, weekend approvals and complete safety/driver/Rig requirements must be reconciled with current sources before #26/#28 product work. Owner priority is not approval of guessed calendar rules.

Actual command/results, package provenance, reproducible steps and PASS/FAIL/BLOCKED/NOT RUN are in the engineering record. Raw diagnostic data, original designs, screenshots and test databases remain local. Documentation checks/branch CI are recorded in the associated Draft PR; they cannot make the failed offline GUI test pass. Customer sign-off and production approval remain pending. No automatic merge, Issue closure or Release.
