# Synthetic read-only impact reproduction

No real personnel, customer profile or workbook is needed. From the backend
folder after locked restore, run:

```powershell
uv run --locked python -m unittest discover -s tests -p test_impact_preview.py -v
```

The tests create temporary schema19 databases, daily calendars, saved five-day
A visits, optional protected B/legacy PM, actual workers and independent resource
evidence. They call the real FastAPI preview/freshness projection and compare
complete SQLite logical dumps; no production writer is enabled.

Core request to authenticated local POST `/day-impact/preview`:

```json
{
  "work_item_id": 1,
  "expected_project_id": 1,
  "crew_ids": [1],
  "remaining_days": 8,
  "remaining_confirmed": true,
  "earliest_start_date": "2026-11-23",
  "horizon_end_date": "2026-12-04",
  "order": "EarliestFinish",
  "max_options": 3,
  "replacements": [
    {"record_kind": "FullDayDraft", "record_id": 1, "expected_revision": 1}
  ]
}
```

IDs/revisions above are illustrative; use exact loaded synthetic rows. Select all
five A IDs to reproduce November23–December2; protected November30 B extends to
December3. Selecting one does not release the other four. No selected record is
actually changed. Before Remaining Days stays Not recorded.

POST `/day-impact/freshness` with `query` equal to the original request and its
`input_fingerprint`. Notes, staffing, old calendars, resource evidence, scope or
database identity changes invalidate it. This is an observation, never a lock or
Apply credential. Overall Pending/false flags remain even if a subcheck passes.

See [engineering evidence](../../docs/acceptance/2026-11-26-issue-18-impact.md).
