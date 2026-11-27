# Synthetic single-version Draft Restore reproduction

Engineering-only #20. Use the locked Windows backend environment and temporary
synthetic databases created by the tests; never point these steps at customer
data. The [confirmed decision](../../docs/10-CLIENT-DECISIONS.md) does not authorize
production or desktop Restore. No network service/login/cloud is used at runtime;
integration tests use authenticated local loopback.

From `src/Rigarus.Backend`:

```powershell
uv sync --locked --group bundle
uv run --locked python -m unittest discover -s tests -p test_draft_restore.py -v
```

`RestoreTests` builds a separate root/data/rigarus.db, opts in explicitly for that
exact root and uses the existing Apply foundation to create an original version.
The synthetic client first calls gated POST `/draft-restores/prepare` with lineage
UUID, `source_record_kind=DraftVersion`, source_version_id. Preparation reserves
the DB, tries new inverse revisions/SQL guards/resource checks under a savepoint,
then always rolls back. Verify logical equality and no persistent audit/receipt.

Inspect `before_restore`, `proposed_restore`, `observations`, `blockers` and every
`warnings[].warning_id/reason/state`. Submit only the unchanged exact plan SHA,
the same explicit source and profile, a new independently namespaced request UUID,
confirmed=true and the complete exact list `acknowledged_warning_ids`. The test
acts as a fictional operator; this is not real customer confirmation. Missing,
extra or duplicate acknowledgements cannot certify the plan.

For5→8, the inverse retains five original IDs/business content and appends
Cancelled events for the three additions. For5→2, the three cancelled originals
reactivate with new revisions. All touched IDs receive appended history. Compare
notes/members, unrelated projects, raw AM/PM tables and immutable source JSON;
same integer FullDay/Legacy IDs remain distinct through the existing mixed weekly
projection and `/schedule-workbench/locate/{kind}/{id}`. Cancelled records remain
in history and cannot be mistaken for active Locate cards.

Same UUID+body returns the same immutable receipt, including known rejection;
different content under it rejects. GET `/draft-restores/receipt/{profile}/{key}`
and `/draft-restores/version/{profile}/{recoveryVersionId}` reconcile/read only.
Unknown/NotFound never means a write failed: retain the original request and
resolve or explicitly replay that exact key/body. No automatic retry/new key.
Default startup rejects both Restore prepare and submit. No desktop bridge exists.

Packaged sidecar regression, after building from repository root:

```powershell
./scripts/Build-RigarusSidecar.ps1
# Then from src/Rigarus.Backend:
$env:RIGARUS_SIDECAR_TEST_EXE = (Resolve-Path '../../artifacts/sidecar/Rigarus.Sidecar/Rigarus.Sidecar.exe').Path
uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v
```

The dedicated packaged test requires the separate CLI flag and exact isolated
smoke-root; checks unauthenticated401, inverse commit/replay, pipe shutdown,
reopen receipt and default-closed write gates. No flag is passed by Tauri.

Migration tests reconstruct a synthetic20 fixture, preserve all tables/versions,
verify pre-DDL consistent backup, DDL/backup failure rollback/retry and21 reopen.
For binary compatibility, independently build20 from main99c9741 and the new21
candidate. First open the20 fixture with the old sidecar, close it, start21 and
verify original-table equality/backup/integrity/FKs. The old sidecar must refuse
the retained live21 DB unchanged. Restore the verified20 backup into a SECOND
isolated environment and reopen it with the old binary. Never overwrite live21
or delete migration history to make an older binary accept it.

This is not whole-week/database undo, Published recovery, restore-of-restore,
new half-day editing, automatic source transfer, dispatch or production approval.
Keep all databases/journals/raw logs/backups local; publish sanitized results only.
