# Issue124 — human-confirmed unconfirmed Draft transaction

## Design Compliance Checklist (before product edits)

Inspected November26,2026 UTC. Public repository; fetched main
75dc07862a97ecd5522c0e617b7d81e2c4085083, human-merged123 (head6ab0556).
No open competing PR found. Isolated codex/safe-manual-apply; unrelated root
README/Chinese README/local original design changes preserved. Main Windows
CI45773860962 was running during discovery; require success before product edits.
Issues18/19/20/29/99/120 are Open; focused continuation124 remains Open.

Required sources re-read, including affected opening sections and historical
contracts; no declared standalone version beyond repository headings:

| Source | Last-changing revision | Checkout modified UTC | Sections used |
| --- | --- | --- | --- |
| AGENTS.md | d3b9bea | 2026-11-26T07:17:23.8837479Z | Mandatory Design-First, authority, privacy, isolated slice |
| DEV-DESIGN-CHECKLIST.md | d3b9bea | 2026-11-26T07:17:23.8902549Z | Source identity, requirements, pre-code plan |
| 00-PROJECT-PLAN.md | 64a0bde | 2026-11-26T07:17:23.8852510Z | Scope, milestones, current owner full days/Apply order |
| 09-DELIVERY-PLAYBOOK.md | 64a0bde | 2026-11-26T07:17:23.8882547Z | Current impact/editor gates, engineering versus Demo/production |
| 02-ARCHITECTURE.md | 64a0bde | 2026-11-26T07:17:23.8862543Z | Impact, schema19 editor/recovery, consistent resource snapshot |
| 03-DATA-MODEL.md | 64a0bde | 2026-11-26T07:17:23.8872563Z | Read-only impact, immutable receipts, daily/legacy compatibility |
| 05-DEMO-ACCEPTANCE.md | 64a0bde | 2026-11-26T07:17:23.8872563Z | Impact and daily resource acceptance |
| 10-CLIENT-DECISIONS.md | 64a0bde | 2026-11-26T07:17:23.8892548Z | Full days, no inference, manual Draft versus Apply, open policies |

Also read the reserved future Apply contract in
[impact design](2026-11-25-impact-preview-contract.md), existing
[impact acceptance](../acceptance/2026-11-26-issue-18-impact.md), current stores,
strict HTTP contracts, migration chain, resource orchestration and synthetic tests.
No product UI changes: original UI figures are not re-inspected for this backend
slice; desktop confirmation/recovery remains a later design-first UI slice.

### Authority, conflict resolution and invariants

Owner November26 explicitly answered: allow an explicitly confirmed plan to be
saved as **unconfirmed Draft**, retaining Pending and specific warnings. This
supersedes only the earlier incomplete-evidence refusal for this bounded Draft
recording operation. It does not certify dispatch, open production writes,
authorize Publish or guess locks/dependencies/Foreman/vehicle-category policies.
Known blockers still reject. Resource nominees are not actual Rig allocation.

| Requirement | Existing | Change / acceptance |
| --- | --- | --- |
| Exact confirmed proposal | Read-only SHA/UUID/typed revisions | Bind selected candidate, exact edits and all warnings; changed input rejects |
| Atomic Draft write | Single-record synthetic editor | One reserved transaction for reread, resources, selected changes, audit and receipt |
| Idempotence/recovery | Editor's separate receipt namespace | New immutable version receipt; same key/payload exact replay, mismatch rejects |
| Stable identity/history | Daily histories and SQL occupancy guards | Retain matching date/Crew IDs; cancel removed visits, create additional; never delete legacy |
| Hard conflicts | Existing coherent validators / SQL guards | Reject Blocked candidate/source and affected final records; rollback any late/storage/audit failure |
| Pending evidence | All current proposals Pending | Explicit exact warning acknowledgement; saved Draft still Pending/false flags |
| Recoverability | Per-record history; no schedule version | Exact touched before/after version; read-only inverse comparison with revision checks |
| UI/production rollout | Closed production writers | No desktop Apply button, no runtime production flag or Publish route |

Unsupported downstream calculation and lock persistence remain clearly warned;
no unrelated work is moved. Actual restore execution, complete database versions,
locks, dependency shifts and cross-instance UI journals are outside this slice.
An inverse preview is not permission to restore or proof that resources are safe.

## Implementation Plan

1. Add owner decision and this plan; commit before product edits.
2. Add schema20 immutable Draft transaction/version receipt, unique namespaced
   request UUID/hash, exact JSON before/after and review proof; existing verified
   pre-DDL backup and transactional migration, no old row/history conversion.
   Readers recognize the new migration/table set; older binaries reject20.
3. Extract connection-level impact computation without changing read-only API
   behavior. Preparation reads one query-only view; submission uses the same
   computation within BEGIN IMMEDIATE. Never call separate Store.read views.
4. New strict backend prepare/submit/receipt/version/recovery-preview contracts.
   Explicit confirmation and Pending acknowledgement bind deterministic plan SHA.
   Only a separate explicit synthetic test opt-in may submit. Missing production
   authorization rejects before any mutation. No Rust/React transport/UI changes.
5. Preserve matching Crew/date IDs. Record exact edits (explicit notes/members),
   cancellation and newly created visits; no actual Rig or source membership
   transfer. Revalidate affected saved rows using existing complete observations
   before atomically committing version/receipt; root Pending, Publish=false.
6. Read-only inverse preview compares current exact touched revisions/values to
   committed after state, reports subsequent edits Stale, shows original values
   and newly-created rows that would be cancelled. No restore endpoint/write.
7. Synthetic tests: extension/early finish, stable IDs, notes/staff, old halves,
   resources/known negatives, Pending acknowledgement, stale/tamper/UUID, replay
   after restart/lost response, competing writers, fault rollback, immutable audit,
   backup/upgrade/retry/integrity/FKs and recovery preview no writes. Run complete
   locked backend/packaged/frontend/Rust/.NET/Windows build/privacy/CI checks.

Errors distinguish invalid, blocked, stale, wrong lineage and unavailable/unknown
commit outcome; absence of a receipt never authorizes a new retry key. Bounded
requests, existing100k/64MiB source budget and30second transaction deadline remain.
No UI states/interactions change. Qualified disconnected Windows install/upgrade/
reboot is BLOCKED: owner reports no replacement for expired Evaluation VM.
Engineering checks do not accept customer Demo/UAT or enable production.
