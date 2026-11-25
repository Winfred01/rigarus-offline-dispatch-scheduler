# Daily staffing, Level and separate qualifications (synthetic)

In src/Rigarus.Backend using the locked Python environment:

```powershell
uv sync --locked --group bundle
uv run --locked python -m rigarus_backend.day_capability_example
uv run --locked python -m unittest discover -s tests -p 'test_daily_capabilit*.py' -v
```

Temporary fictional profile only. Both Crews have explicit full-day company
driver evidence and available actual people; minimums/Exact Level2 and SYN-Q
qualification counts are fictional explicit policy, never production defaults.

| Case | Expected |
| --- | --- |
| Borrow one of two source workers; source minimum2/Level2 minimum2 | Driver Satisfied but source capacity Blocked; excluded |
| Explicit qualified source replacement retains two workers | Capacity/driver subchecks Satisfied; full Validation Pending, one ranked option |
| Edit observed source qualification after preview | Earlier proof Stale |

The source override changes detached data only. No Home Crew inference, saved
transfer, employee/Rig selection, UI/API write or Apply/Publish. Level is never
equivalent to certification. Foreman, whole-roster availability, actual Rig,
weekend consent and operator review remain independent Pending. No native/offline
installation or customer acceptance is demonstrated by this console reproduction.
