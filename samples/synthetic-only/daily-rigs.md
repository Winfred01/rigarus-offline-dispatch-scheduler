# Actual daily Rig and replacement preview (synthetic only)

From src/Rigarus.Backend, locked Python environment:

```powershell
uv sync --locked --group bundle
uv run --locked python -m rigarus_backend.day_rig_example
uv run --locked python -m unittest discover -s tests -p 'test_daily_rig*.py' -v
```

Temporary fictional profile: two Crews, explicit actual R1/R2 allocations, separate
company/operational reference inputs and an independent three-day R1 repair.
Default R1 link alone is never actual occupancy. No operational/customer profile.

| Preview | Expected |
| --- | --- |
| R1 repair; propose R2 still occupied by Crew2 | Blocked, dated collision references |
| Cancel Crew2 visit, re-read, propose R2 | Rig subchecks Satisfied only; original R1 and Proposed R2 shown, SQLite actual still R1 |
| Generate next unoccupied working date, explicitly propose R2 without staffing | Dates generated, overall Pending; no employee/driver inference |
| Record R2 inspection after preview | Earlier proof Stale |

All overall Validation Pending / Apply=false / Publish=false. Proposed operational
evidence is an explicit planning assertion bound to the snapshot, not saved Rig
approval or legal/category certification. Swaps never reserve/change resources;
later human Apply must revalidate inside its transaction. Full personnel/Foreman,
vehicle-category and actual-worker weekend consent remain independent gates.
No native GUI, disconnected installation or customer acceptance is claimed.
