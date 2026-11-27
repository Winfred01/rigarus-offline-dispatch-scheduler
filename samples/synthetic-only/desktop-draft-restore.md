# Isolated desktop Draft Restore engineering sequence (#130)

Use only disposable synthetic profiles and this candidate's own built EXE and
sidecar. Do not reuse a customer profile, alter an old installer or infer that a
development-host check is an offline VM pass. No production Restore switch exists.

1. Follow [backend synthetic source setup](draft-restore.md) to create one original
   DraftVersion, including5→8/5→2, another unrelated Project and a distinct old
   AM/PM record. Keep schema21 profile, notes/staff/history and typed equal-ID
   baselines. For a simple native confirmation use an original batch containing
   two new dates: its inverse cancels both and retains all history.
2. Set process-scoped `RIGARUS_SMOKE_DATA_ROOT` to that dedicated test folder
   (database exactly `data/rigarus.db`) and `RIGARUS_DRAFT_RESTORE_TEST=1` before
   launching the candidate. The Apply flag is independent and is unnecessary
   for Restore unless testing that separate workflow. Remove both flags to test
   the default closed gate. No UI preference enables production writing.
3. In Schedule open single-version Draft Restore. Enter the explicit ORIGINAL
   DraftVersion ID, inspect its original Before/After, then prepare the exact
   inverse. Preparation is a gated rolled-back reservation. Inspect all typed
   IDs/revisions/notes/actual employees, proposed cancellations/reactivations,
   recorded actual Rig evidence and every Pending reason. Missing names or
   resources are not invented. Blocked or Stale cannot submit.
4. Cancel/X/Escape before dispatch and compare a coherent read-only SQLite
   logical snapshot, integrity/FK, business rows/history/versions/receipts. Avoid
   raw WAL hashes. Reopen and deliberately prepare again; every Pending starts
   unchecked. Confirm each exact warning and the separate inverse scope.
5. When the native write action is authorized, submit once. Closing after send
   does not cancel its possible commit. Retain the exact original key, source,
   plan and acknowledgements under the profile's `draft-recovery` folder.
6. Reopen an uncertain request: inspect the same original key and the explicitly
   retained reviewed snapshot. Resolve only queries the authoritative receipt.
   NotFound/timeout/bare failure/mismatch never authorizes a replacement key.
   Explicit replay, if needed, uses the same original key/body. Never delete or
   replace an unresolved journal to force another request.
7. A complete Committed or sealed Rejected receipt must match the retained
   operation/profile/key/source/request; committed plan/After/resources must also
   match. Explicit Archive rereads that receipt natively, flushes the operation-
   specific archive, then retires only its exact pending request. Injected write/
   flush faults must keep pending. Apply and Restore cannot overwrite each other.
8. A committed result remains committed if weekly refresh fails. Retry reads;
   inspect Job Schedule/Crew Board and typed Locate without another Restore.
   FullDayDraft and LegacyHalfDay with equal integers stay distinct. Preserve
   AM/PM labels, notes, actual staff/Rig/history, and legacy occupancy. No new
   half-day editing, conversion, merging or Publish is authorized.

Use bounded SQL30s/HTTP60s/renderer150s and complete bounded payloads; oversized
proofs fail closed rather than truncate. Capture local-only synthetic screenshots,
exact binary/installer SHA256, OS/WebView2/network conditions and independent
logical snapshots. Record each [acceptance case](../../docs/acceptance/2026-11-27-issue-130-desktop-restore.md)
as actually executed. Seeded lost-response state is fault simulation, not proof
that the GUI produced a timeout. A built installer is not an installed/updated/
rebooted disconnected Windows VM. Customer UAT and production remain unapproved.
