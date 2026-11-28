# Issue135 — qualification observation contract

## Design Compliance Checklist

Inspected November28 UTC (November27 client date), public repository, freshly
fetched main `1923b564d95c8bb790ad00c82864f5b6fb52c6fe`. Isolated branch
`codex/issue-135-qualification-proof`; preserve root README/untracked design work
and the independent Issue130 fault-test PR134. Issue135 records the actual native
D01 failure before any Restore submission. No pending request or SQL change.

Required files exist and current versions were checked against the Issue130
inventory already read in this execution: AGENTS/checklist `d3b9bea`; six sources
00/09/02/03/05 `1bf8341`, decisions10 `3be3cd4`; original130 design `f3a68da`,
implementation/sample `1bf8341`, native follow-up `d4c3f1f`. Full revisions,
checkout UTC modification times and hashes remain in local inventory. Relevant
sections: daily capability engineering (#109), schema16 policy/provenance,
schema21 desktop Restore, exact observations, immutable receipts and D01/D03/D13.
Issue130 and live PR134/CI were checked; PR133 remains merged. No duplicate fix.

Original November24 local UI source SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`:
L10 paragraphs54–58/image62, L12 paragraphs64–68/image64, L13 paragraphs69–73/
image65 were inspected during this execution. These are paragraph/figure locators,
not page numbers. No UI layout changes; retain review, cancel, retained request,
pending checkboxes and mixed typed Locate. Original DOCX/images remain local.

| Requirement | Existing evidence / needed action | Acceptance |
| --- | --- | --- |
| Complete qualification proof | Native/TS require one aggregate; current backend omits it for explicit policy | Reproduce strict contract failure, then real Python-to-native/TS proof |
| Unknown never passes | Existing capability model emits Pending for missing policy | Unknown projection and old contract unchanged |
| Explicit empty is distinguishable | Existing capability proposal aggregate uses explicit requirement provenance | Empty, satisfied, missing-proof, known-failure cases |
| Hard conflict preserved | Keep individual Qualification:code checks/reasons and derive aggregate | Known failure remains Blocked; Restore rejects |
| History and mixed IDs | Projection only; do not touch schema21/history/AM/PM | Logical read equality, equal integer typed IDs |
| Authorizations | User A/B/C permits bounded synthetic fixes; no platform override | Default production gates closed; native evidence separate |

No new business rule is proposed. An explicitly configured empty qualification
list is already distinct from an absent policy in the approved capability model.
The root result remains Validation Pending / Apply=false / Publish=false.

## Implementation Plan — committed before product code

1. Add a failing projection regression and extend the real Python Restore fixture
   to explicit policy so unchanged Rust/TypeScript strict validators reproduce it.
2. In `schedule_workbench.py`, reuse the existing capability aggregate semantics
   to add the missing Qualifications summary only when no generic summary exists.
   Preserve individual checks/reasons; unknown-policy output stays byte-shape
   compatible. Do not weaken either native validator or rewrite saved JSON.
3. Test unknown, explicit empty, named satisfied/pending/blocked qualification
   evidence, mixed namespaces and read-only integrity. Recheck complete Restore
   plan/receipt contracts, not just HTTP200.
4. Run applicable locked restores/formats/full regressions, package matching
   sidecar/Windows EXE/NSIS, privacy/docs and Windows CI. Native inspection uses
   independent synthetic profiles; no production gate change. Record actual
   artifact identity and distinguish pre-fix failure from post-fix evidence.

No migration/API route/UI redesign. Existing historical JSON and receipts remain
immutable. Risks: aggregate disagreeing with individual checks, treating unknown
as satisfied, changing fingerprints. Recompute new plans; never replay a changed
payload under an existing request key. Offline licensed VM remains BLOCKED;
customer UAT/production/Release remain unapproved.
