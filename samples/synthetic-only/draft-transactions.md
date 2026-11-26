# Synthetic confirmed-plan Draft transaction

Backend-only engineering interface for Issue124. No desktop Apply button or
production writer is enabled. Use only an isolated synthetic profile. Pending
evidence may be explicitly acknowledged for an **unconfirmed Draft**; this is
not safe dispatch, Publish, automatic transfer or actual vehicle allocation.

Run in the locked backend environment:

```powershell
uv run --locked python -m unittest discover -s tests -p test_draft_apply.py -v
```

The fixture provides five saved A dates November23–27,2026 and explicit daily
Crew/Project calendars through December4. Preparation with confirmed8 remaining
days produces November23–27 and November30–December2; weekends do not count.
The five matching Crew/date IDs and unchanged notes survive; three new IDs are
created. With confirmed2 days instead, the last three original visits become
Cancelled with new revisions/history, never deleted.

## Interface sequence

1. `POST /draft-transactions/prepare`: `{query: <strict ImpactQuery>,
   selected_crew_id: <candidate ID>, notes: <optional explicit text>}`. Query
   contains operator-confirmed positive Remaining Days, local horizon, candidate
   Crew IDs, parent Project, exact typed replacement IDs/revisions, and optional
   explicit workers. Omitted workers mean unconfigured, not inherited attendance.
   Omitted notes retain matching saved notes; new visits use empty notes.
2. Inspect `before`, `proposed`, `cancel_ids`, all warnings, affected IDs and
   Pending/false flags. Cancel here does nothing. Rig nominees are refused because
   this slice does not record an actual vehicle or operational approval.
3. Synthetic-only `POST /draft-transactions/submit` supplies the unchanged prepare
   input as `plan`, database UUID as `profile_id`, original `plan_fingerprint`, a
   fresh `request_id` UUID, `confirmed:true`, `pending_acknowledged:true`.
   The fingerprint binds the exact values, resource reasons, unsupported locks/
   dependencies and source proof; changing/reverting a source may still require
   a new preparation. No client-provided After values are trusted as authority.
4. Committed returns immutable `version_id`, exact before/after, explicit
   confirmation, resource observations and UTC time. Same key and payload return
   the original result after restart; changed payload with that key rejects.
   Record the exact request before dispatch. An HTTP timeout/storage error may
   leave the result uncertain: resolve `GET /draft-transactions/receipt/{profile_id}/{request_id}`.
   NotFound is not proof of rejection; use explicit unchanged same-key replay,
   never a new blind create key. Rejections are not persisted as version receipts.
5. `GET /draft-transactions/version/{profile_id}/{version_id}` retrieves the
   committed changeset. `GET /draft-transactions/recovery-preview/{profile_id}/{version_id}`
   compares current touched records with committed After and shows an inverse:
   original values for existing IDs, cancellation for newly created IDs. Subsequent
   edits make this comparison Stale. Current means exact touched records still
   match, **not** that a restore is safe. Proposed restore values contain current
   expected revisions, never instructions to rewind historical revisions.

There is no restore/Publish endpoint, runtime production opt-in, Rust Apply
bridge or operator recovery UI. Actual restore requires a new reviewed transaction
with complete current occupancy/resource/lock/dependency checks and explicit intent;
it must append revisions/history rather than delete events or replace a database.
No full-database version browser or downstream shift is supplied by this changeset.

## Transaction and compatibility

One BEGIN IMMEDIATE reserves writes before re-reading schema20, lineage, source
snapshot and exact plan. Existing generator/comparison and people/driver/skills/
Rig/consent validators run in that same view. Matching date/Crew visits retain
IDs; only reviewed old dates cancel, explicit proposed days save. Existing SQL
Crew/day, legacy-half overlap and Rig guards remain. Actual final saved records
receive another resource observation; a known blocker rolls back the whole batch.
Missing evidence stays visible/Pending; no nominal vehicle, Home Crew or half-day
positive proof is promoted. Final revision-bound approvals can become stale and
require independent reconfirmation, explicitly warned before submission.

Schema20 adds only append-only DraftVersions, atomically serving as audit,
changeset version and unique request receipt. All prior tables/IDs/FKs/slots/
notes/history remain. A verified consistent19 backup precedes DDL; migration
failure rolls back and retry is safe. Older binaries reject20. Independent backup
recovery requires its compatible binary and reconciliation of later changes;
it is not schedule undo or an in-place downgrade.
