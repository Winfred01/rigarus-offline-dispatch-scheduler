# Issue120 — independent Full Day Draft editor

## Design Compliance Checklist

Fresh baseline main9d40765 (human-merged PR121), public repository, no open PR
and no Issue120 comments/other implementation. Independent issue120 branch;
root README/language/design changes retained. Milestone3 remains a delivery
label, not customer acceptance. Read current AGENTS d3b9bea; plan/playbook/
architecture/client decisions be715d1; model/acceptance7604d2a. Read current
full-day/storage/recovery/resource/Locate sections and119 evidence/current code.
Local inventory records exact revisions, SHA256 and UTC modification times;
checkout time is not business authority.

Latest accessible original UI November24 DOCX remains local, SHA256
d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c,
mtime2026-11-24T23:15:38.711423Z. Freshly extracted/re-read L14 paragraphs74–78
and L20 paragraphs104–108 and viewed original image66/image72. Paragraph locators
are not verified page numbers; prototype is not tested product. Earlier L01/L03
weekly identity/Locate contract retained from merged119. No full DOCX upload.

| Requirement / state | Implementation and acceptance case |
| --- | --- |
| Confirmed Full Day local dates and stable kinds/IDs | Separate date-only editor, create/edit/cancel; no Slot/rounding/conversion. Same numeric day/legacy ID tests |
| L14 detail/revision and explicit removal | Open current persisted revision; Cancel before Save writes nothing; saved cancellation retains history and releases capacity |
| L20 actual people separate from Home Crew | Explicit IDs or unconfigured/explicit empty; preserve inactive/borrowed selections with reasons, no implicit source removal. Context changes require explicit reconfirmation; notes-only retains members |
| Existing hard occupancy/invariants | Preserve day Crew/date and legacy AM or PM exclusion, FK/history/Rig SQL guards, optimistic revision. No new default skill/Foreman/legal policy |
| Independent safety feedback | Reuse exact saved workbench validators under same write reservation after tentative mutation. Full Draft Pending, Apply/Publish false; warnings do not certify missing evidence |
| Unknown result and refresh failure | Atomic idempotent receipts, database identity, durable pre-dispatch journal. Resolve original request; manual same-payload/same-ID replay only. Saved success never becomes failure merely because refresh fails |
| Reliable boards/Locate/reopen | Re-read persisted current row/history; both boards reload; active record typed Locate, cancellation absent from active grid but retained history |
| Current rollout gate | Production writers remain disabled. Explicit synthetic-only opt-in with separate smoke root for native/VM tests. No operator gate opening from CI |
| Deliberate design differences | Full Day replaces prototype halves. Validated/locks/Apply/Rig editor/delay/version/export remain unavailable; actual recorded Rig only shown, never defaulted |

No critical original source is missing. Authenticated authority, Foreman/category/
legal thresholds and production gate review remain unresolved; no guessed rules.
Known calendar/resource reasons remain Draft feedback under existing contracts;
existing structural occupancy/SQL guards still reject. Fresh checks after Save
are observations, not dispatch permission. If source reading fails, roll back
instead of certifying an unchecked save. Offline/upgrade/VM/customer gates must
be reported separately, without borrowing older candidate results.

## Implementation Plan — before product code

1. Commit plan. Add schema19 workspace identity + immutable request/result receipt
   tables, verified18→19 backup/atomic migration/unsupported-old-binary recovery.
   Keep every old table/row/ID/note/member/history. Extend schema-aware readers.
2. Refactor existing DayDraftStore transaction body into connection operations,
   retaining existing public behavior/tests. New editor service reserves one
   BEGIN IMMEDIATE transaction: exact profile/request hash/revision/Project and
   staffing-context checks, old occupancy, mutation/history, existing saved
   resource observations, receipt. Same request returns original receipt; changed
   payload cannot reuse it. Storage/source errors roll back and remain unknown
   until read reconciliation. No automatic write retries or new safety defaults.
3. Add strict fixed FastAPI/Tauri status/read/history/submit/receipt operations;
   production gate false. Sidecar test opt-in requires explicit synthetic flag
   and dedicated smoke-root database; no root/profile/customer switch in UI.
4. Add independent React editor using existing dialog/control typography and
   current original design hierarchy. Inputs: WorkItem/Project, Crew/date/notes,
   explicit staffing choice/reconfirmation. Show current revision/observations,
   dirty/stale/rejected/busy/unknown/committed-refresh-failed and cancelled states.
   Journal original request before dispatch, scoped by database UUID, validated
   as untrusted local state; fail closed on malformed/unwritable journal.
   No double submit or dismiss-and-create during unresolved writes. Reopen can
   recover receipt before another save. Clear journal only for definite outcomes.
5. Connect new/details entry and current saved refresh/typed Locate in both boards;
   legacy editor remains distinct. Keep recommendation Apply/Publish disabled.
6. Tests: lifecycle/explicit members/history/no-op/context; legacy/daily occupancy;
   stale/concurrent revisions/idempotent replay/changed key/profile; storage and
   feedback failure atomic rollback; unknown receipt, restart/recovery and
   committed-refresh failure; cancellation/reopen/notes/old IDs. Locked restores,
   format/Windows builds/full tests/packaged sidecar/privacy/CI and original-image
   comparison. Native connected-host and available isolated offline Windows11
   installer/upgrade/reboot each need actual candidate provenance and result.

App-screen question: what will this dated Draft save, and what actually committed?
Retain Rigarus shell, local fonts, restrained status colors and two-column fields
that stack within the dialog; no new branding, charts, web assets or fake totals.
Known warnings and exact recovery actions are adjacent to the Save outcome.
Native desktop is the target; phone inspector findings cannot certify it.

Native first candidate: create/explicit borrowed worker/save/reveal exactID3 and
real stale-revision refusal passed. Original-image comparison found the generic
600px dialog truncates WorkItem IDs and inherited full-width checkbox styling
separates boxes from labels. Before further UI work, widen only this editor,
collapse saved-ID utilities, align checkboxes, and keep secondary/recovery actions
outlined. Preserve same request/revision logic; rebuild and repeat native checks.
App sheet framed-sheet seed744846122 retained brand palette/type. The original
Rigarus shell overrides the sheet's generic shell; no rebranding, charts or fonts.
