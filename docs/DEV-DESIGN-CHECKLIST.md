# Development Design-First checklist

Copy this template for each Issue and refresh it at every resumed implementation session. Follow [AGENTS.md](../AGENTS.md). Output **Design Compliance Checklist**, then **Implementation Plan**, before changing product code. Store only sanitized records in GitHub; keep absolute local paths, original designs and raw evidence on the authorized machine. The [initial #45/#65 dry run](design/DESIGN-FIRST-VALIDATION.md) demonstrates source location and conflict handling, not product acceptance.

## Issue and current baseline

- Issue / milestone / approved vertical slice:
- Inspection time (UTC) / author:
- Repository / current visibility / remote:
- Latest fetched `origin/main` commit / current commit / branch:
- Working-tree changes to preserve / isolated worktree:
- Linked Issues, dependencies, PRs and review feedback (state, head and checked-at time):
- Existing implementation, tests, CI and acceptance evidence inspected:
- Scope excluded / reason UI is not applicable, if applicable:

## Design Compliance Checklist

Read each required source again; do not reuse a prior chat as evidence. For tracked sources, use the file's last-changing commit as its revision and record the current checkout modification time separately. For untracked external sources, record SHA-256 and approved local location. Note unreliable metadata; modification time alone does not establish authority.

| Design document / source | Exists and readable? | Declared version/date | Git revision or SHA-256 | Last modified UTC | Read-at UTC | Relevant chapters/sections |
| --- | --- | --- | --- | --- | --- | --- |
| `docs/00-PROJECT-PLAN.md` | | | | | | |
| `docs/09-DELIVERY-PLAYBOOK.md` | | | | | | |
| `docs/02-ARCHITECTURE.md` | | | | | | |
| `docs/03-DATA-MODEL.md` | | | | | | |
| `docs/05-DEMO-ACCEPTANCE.md` and affected acceptance records | | | | | | |
| `docs/10-CLIENT-DECISIONS.md` and affected ADRs | | | | | | |
| Relevant original UI design (local-only unless separately authorized) | | | | | | |
| Current Issue, milestone and linked PR/review evidence | | | | | | |
| Additional affected mapping/specification | | | | | | |

### UI reference figures and pages

| Source version | Section / page / figure | Original image actually inspected? | Concept or implemented screenshot? | Relevant UI states | Sanitized evidence locator / review limitation |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

Use section/figure identifiers when pagination has not been verified. Record extraction versus page rendering accurately. A missing `docs/design/Rigarus_UI_Design.docx` is not proof that no authorized local source exists. Search accessible workspace files and record the expected path and search result locally. Do not upload the original to make a link work.

### Requirements and decision status

Use **Confirmed / Proposed / Open / Conflict / BLOCKED** for requirement authority; use **Existing / Partial / Missing / Out of scope** for implementation status. A requirement can be Confirmed but Missing. Do not equate implementation with customer approval.

| Requirement ID / functional requirement | Source section / original figure | Authority status and decision source/date | Current code and implementation status | Needed change or preserved invariant | Acceptance case |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

### Design differences and unresolved questions

| Difference / conflict / missing source | Affected requirement | Existing database/domain invariant | Decision owner / evidence needed | BLOCKED scope / independent work allowed |
| --- | --- | --- | --- | --- |
| | | | | |

Confirm that examples have not introduced requiredness, formats, enum values or false error states. Record the latest confirmed customer decision, not just the newest timestamp. Preserve current constraints pending an approved change. Link any resulting decision-register/ADR entry. Stop affected implementation for a critical missing design or material conflict.

## Implementation Plan

- Planned files and purpose / existing code to reuse:
- UI pages, layout, loading/empty/invalid/failure/success states:
- Input changes, cancellation, keyboard/focus, tooltip dismissal, ARIA and narrow-window behavior:
- Tauri commands / FastAPI API contracts and validation / no API change if applicable:
- Domain rules / SQLite tables and invariants / migration or explicit no-migration reason:
- Compatibility, rollback, fault recovery and preserved IDs/data:
- Tests and design-comparison evidence to produce:
- Risks, unresolved dependencies, blocked requirements and permitted independent work:
- Plan changes since prior session and the evidence requiring them:

## Acceptance cases and actual results

Leave execution results **NOT RUN** until executed. Use **PASS / FAIL / BLOCKED / NOT RUN** and give reasons; mark a check not applicable explicitly rather than inventing a pass. Include normal, boundary, failure, transactional, persistence and accessibility cases relevant to this slice.

| Case / linked requirement | Synthetic setup and reproducible steps | Expected result | Actual result/status | Command / sanitized evidence / environment |
| --- | --- | --- | --- | --- |
| | | | NOT RUN | |

- Locked restore / format / Windows build / automated tests:
- Staged `git diff --cached --check` / `scripts/Test-RepositoryPrivacy.ps1`:
- Windows CI URL, head, job results and artifact upload status:
- Native Windows GUI: OS / executable or installer version / commit / SHA-256 / WebView2 / developer-tool conditions:
- Offline check: actual networking condition / isolation / command / result (separate from CI):
- UI screenshot comparison and interactions executed / differences remaining:
- Migration, compatibility and recovery evidence, or no data change:
- Sanitization review: explicit staged paths, no original DOCX/Excel/PDF, customer/personnel data, secrets, raw diagnostics or databases:

## Delivery and final report

- Documents actually read and their versions/revisions:
- Implementation list / changed files / unmet design requirements:
- Engineering verification and limitations:
- Customer Demo acceptance (reviewer and decision, or pending):
- Production approval (separate decision, or pending):
- Branch / commit / Draft PR URL (human review required):
- Unresolved questions, missing exact source locations in local evidence, owners and next steps:
- Confirm no automatic merge, release, Issue closure or customer database modification:
