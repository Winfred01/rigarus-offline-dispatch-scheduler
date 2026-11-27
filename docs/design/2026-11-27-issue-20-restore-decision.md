# Issue20 — pending Draft Restore authority record

## Baseline and source verification

Documentation-only slice of #20 / M3, following the November27 technical review.
Public repository, freshly fetched main
`23be96f124d2e0a150d1ad36a3b81614dc8df522`; PR127 is human-merged and no open
PR competes with this work. Preserve unrelated root README, language-document
and local-design changes. Work in `codex/issue-20-restore-decision` independently.

On November27, existence, last-changing Git revision and UTC checkout mtime were
checked again. The plan/playbook were reread, along with the relevant current
architecture/model/acceptance/decision sections, #20 and its design comment,
PR127 and the prior #126 acceptance gates. This is not a full reread of every
historical subsection in those long documents.

| Source | Revision / version | Checkout modification UTC | Relevant material |
| --- | --- | --- | --- |
| AGENTS.md | d3b9bea | 2026-11-27T19:42:51.1860213Z | Mandatory Design-First6/9/11, authority and documentation-only checks |
| docs/00-PROJECT-PLAN.md | 80e6eb8 | 2026-11-27T19:42:51.1890225Z | Current next-slice order, Scope/Milestones |
| docs/09-DELIVERY-PLAYBOOK.md | 80e6eb8 | 2026-11-27T19:42:51.1932102Z | Current126/124 gates, engineering versus customer/production |
| docs/02-ARCHITECTURE.md | 80e6eb8 | 2026-11-27T19:42:51.1900218Z | Exact Draft confirmation/recovery, read-only inverse |
| docs/03-DATA-MODEL.md | 80e6eb8 | 2026-11-27T19:42:51.1900218Z | Schema20 immutable DraftVersions and preserved records |
| docs/05-DEMO-ACCEPTANCE.md | 80e6eb8 | 2026-11-27T19:42:51.1912103Z | Desktop126 and backend124 walkthroughs |
| docs/10-CLIENT-DECISIONS.md | 80e6eb8 before this edit | 2026-11-27T19:42:51.1932102Z | November26 recording authority excludes actual restore |

Latest accessible local original remains
`Rigarus_UI_Design_Updated_2026-11-24.docx`, SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`,
mtime2026-11-24T23:15:38.7114232Z, rechecked for this record. L10 paragraphs54–58
and image62 distinguish Published History/Inspect Snapshot/revision Draft from
separately verified whole-week rollback. L12 paragraphs64–68/image64 describe
preview, Apply and Undo Last Batch; they do not authorize actual restore writes.
The original text/images were freshly inspected in this session's preceding
#20 design investigation. This document-only continuation adds no UI and relies
on no new visual specification. No DOCX, original image or raw diagnostic upload.
Paragraph locators are not page numbers. Checkout mtime does not grant authority.

## Design Compliance Checklist

| Requirement / source | Authority and current implementation | This slice / acceptance |
| --- | --- | --- |
| November27 conditional technical review | Documentation permitted; review explicitly cannot substitute for project-owner approval | Record Proposed, not Confirmed; preserve exact five conditions |
| AGENTS6/11 and current decisions | Actual Restore not authorized by prior recording decisions | Explicit pending owner evidence fields; product coding remains blocked |
| L10/L12 original concepts | Current schema20 has immutable changesets and a read-only inverse; not Published/full-database rollback | Describe distinction; no new Restore control or contract |
| Exact selected version and revisions | Existing inverse reports touched-record Current/Stale only | Proposed future mismatch refusal, not a passed resource check |
| Audit, stable IDs, legacy records | Existing append-only/occupancy guards retained | Proposed new revisions/cancellation/audit, no code/data changes now |
| Pending and hard conflicts | Approved recording policy does not itself approve reverse writes | List per-item acknowledgements as a pending owner decision; no new default |
| Test and rollout authority | Offline VM blocked, customer/UAT/production separate | Do not promote technical review, merge or CI to those approvals |

## Implementation Plan — this documentation slice only

1. Add a dated Proposed entry at the top of the decision register. Preserve all
   historical decisions; identify conditional technical-review support separately
   from the absent authorized owner confirmation.
2. Retain the requested scope wording and five conditions: exact/Stale, new
   history/audit/recovery version, per-item Pending acknowledgement, atomic
   resource revalidation/idempotency/receipts, isolated synthetic backend only.
3. Leave owner identity/role, date and traceable confirmation source explicitly
   unrecorded. An explicit authorized-owner confirmation can be recorded in a
   later review/instruction; documentation merge alone is insufficient.
4. No UI/API/Tauri/domain/table/migration changes. `draft_restore.py`, restore
   transaction, independent idempotent audit and their tests are future product
   work, NOT implemented or started by this document. After owner confirmation,
   refresh the pre-code plan, including exact DDL/compatibility/rollback tests,
   before implementing the approved backend slice.
5. Check Markdown encoding, fences and local links/anchors; review the diff;
   run staged whitespace/privacy checks. Push this Issue branch and open one
   Draft PR. Report automatically triggered CI separately from doc checks.

## Actual checks and independent gates

| Check | Result / meaning |
| --- | --- |
| Live repository/main/PR and source authority inspection | PASS; main23be96f and human-merged127 verified |
| Existing inverse contract | Inspected: readonly=true, restore_enabled=false; no actual restore implementation claimed |
| Document/link/encoding | PASS; two documents,13 local links, intact historical decisions and explicit pending owner gate |
| Staged whitespace/privacy | PASS; only these two Markdown files changed,401 repository index paths scanned |
| Product restore tests/build/GUI | Not applicable to this document-only diff; no product code or migration changed |
| Future Restore implementation | BLOCKED pending explicit authorized project-owner confirmation |
| Offline VM install/upgrade/OS reboot | BLOCKED; no execution in this slice |
| Customer Demo/UAT and production approval | Not approved |

The Draft PR records actual document/privacy results and its current Windows CI
state. No original sources, customer data, raw diagnostics or databases are
staged. No automatic merge, Issue closure, Release or deployment.
