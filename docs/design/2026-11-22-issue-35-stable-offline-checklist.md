# Issue #35 — independent offline acceptance Design-First record

## Baseline and source check

Approved slice: check PR #80 CI, prepare a stable authorized Windows 11 x64 test guest, investigate WebView2 and test existing installed-package lifecycle. No feature/UI redesign or scheduling rule change. PR #80's three Windows CI jobs passed and it was human-merged as `ebc78409cead320e87922de8087c06ccad453c97`; branch `codex/issue-35-stable-offline` was created in a new isolated worktree. Existing root README/design changes and other worktrees were preserved. Repository visibility is PUBLIC.

Required files were read again in this session, with existence, current content revisions and UTC filesystem modification metadata recorded locally. The content revisions below are unchanged by the documentation-only #80 merge; checkout modification time is not business authority. Current #35, the prior #35 attempt, delivery handbook, original kit and historical installed-lifecycle tools were also inspected. Source metadata and exact local UI path remain in local evidence.

| Read source | Revision | Relevant sections |
| --- | --- | --- |
| `AGENTS.md` | `d3b9bea778529c47bb502e59914cbdd0100697a0` | Mandatory Design-First; synthetic-only tests, actual gates and human review |
| `docs/00-PROJECT-PLAN.md` | `cc9613a61a09bee488255b96ac7f2e581b45a1a2` | Offline scope; M7/M8 acceptance; operator-approved proposals |
| `docs/09-DELIVERY-PLAYBOOK.md` | `e6326dff3c75bc1670a73dfd37638376efd15804` | Engineering versus Demo/Production; frozen version/hash evidence |
| `docs/02-ARCHITECTURE.md` | `f7e650c63d9217a10e5127d53f85aa54fa908fc9` | Tauri/Rust/packaged FastAPI lifecycle; local-only storage |
| `docs/03-DATA-MODEL.md` | `a2f9fa25bcbfb0be555a6979f9c8be744f51dde6` | Stable Project/WorkItem IDs and schema-nine compatibility |
| `docs/05-DEMO-ACCEPTANCE.md` | `f7e650c63d9217a10e5127d53f85aa54fa908fc9` | Tauri/demo-note, Project Master, availability and Employee Week checks |
| `docs/10-CLIENT-DECISIONS.md` | `a2f9fa25bcbfb0be555a6979f9c8be744f51dde6` | Recorded availability is not eligibility or assignment; unpublishable Drafts |

Latest accessible original UI source metadata was checked: `Rigarus_UI_Design_Updated_2026-11-22.docx`, SHA-256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`. No original figure/page reread is claimed for this no-UI-code-change task. UI design implementation/comparison is not applicable; existing native verifiers exercise the current product. The complete original remains local under the owner's instruction.

## Design Compliance Checklist

| Requirement and authority | Existing implementation / planned validation | Case and current result |
| --- | --- | --- |
| #35: no-SDK offline install and usable first launch | Unmodified original CI installer, bundled runtime and original offline kit | Fresh prepared no-runtime standard-user guest: PASS; exact hash and actual GUI verified |
| Delivery gates: installation is not data retention | Separate default-profile GUI seed, read-only SQLite snapshots and independent closed-disk audit | Fresh save/reopen and real Restart: PASS; stable IDs/links/note, nine migrations |
| Actual Restart must be observed | Windows fast startup can preserve kernel time after a power cycle | Explicit guest Restart and changed kernel boot time; no host reboot |
| Upgrade must preserve old original rows | Separate old installed build, closed backup and new overwrite setup; no history edits | Serial upgrade PASS, migrations 5→9 and old records retained; upgraded actual Restart and original-data comparison also PASS. Aborted resource-pressure attempt excluded |
| Existing Draft/availability boundaries | Existing schema nine and current native fixture; no new algorithm | Available stays administrative; no qualification, attendance or publication inferred |
| Privacy and human gates | Synthetic-only VM; original documents/raw evidence remain local | Only sanitized Markdown submitted; no auto merge, Issue closure, Release or real customer DB access |

## Implementation Plan

1. Verify latest main/PR state and original package identity. Preserve original installation/GUI failures and distinguish them from local orchestration failures.
2. Clone authorized synthetic Windows storage into a preparation overlay. Check normal licensing, OS/account/tools/runtime and prepare the image; disconnect through `-nic none` before formal testing. Do not change host time, security settings, components or unrelated applications.
3. Run bounded original install/GUI checks, then separate matching Start-menu/default-database save/reopen and actual Windows Restart. Audit only after normal product/guest exit; live read-only logs are diagnostic, not final data evidence.
4. Use a separate clean overlay for old installed version → same-version-number new build. Verify path, old IDs/links/notes, additive migration history, actual Restart and SQLite integrity. Run additional native/retention cases only when prerequisites exist; report exact remaining cases.
5. Record the [sanitized results](../acceptance/2026-11-22-issue-35-stable-offline.md); run documentation/link/whitespace/privacy checks, then publish the evidence branch/Draft PR for human review. Report actual CI head/result separately from the older source package CI. No product code, API, UI state, domain rule, dependency or migration is planned.

## Differences, limitations and unresolved gates

Initial concurrent emulated guests caused host memory pressure; an incomplete upgrade attempt was normally stopped, retained and not classified as a product defect. Work continued serially. Local lifecycle helpers required parameter/attached-handle corrections and an explicit resume path; the original kit had already passed, setup was not silently rerun, and raw failed tool logs remain local. Existing legacy and current navigation labels must be handled separately by the test wrapper.

The prepared image is IoT Enterprise LTSC Evaluation, not an approved representative customer endpoint. The guest clock had an observed offset; no manual clock/activation bypass was used and wall-clock/Today correctness is not certified. The earlier Sandbox runtime inconsistency and evaluation guest poweroff remain historical limits, not causal proof of a product defect. Current original package behavior is tested separately.

Engineering PASS rows do not establish complete #35, customer Demo/RC acceptance or production approval. Remaining endpoint-policy/signing/distribution, version-number changes, recovery/restore and unimplemented report/safety rules remain pending. No critical UI source is missing for this validation-only scope, no business rule was changed, and no new customer decision was inferred. Owner sequence after this gate remains #26 then #28, with Design-First and operator approval constraints intact.
