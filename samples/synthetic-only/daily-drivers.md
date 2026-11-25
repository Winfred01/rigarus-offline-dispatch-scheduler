# Daily company-driver preview (synthetic only)

From src/Rigarus.Backend in the locked Python environment:

```powershell
uv sync --locked --group bundle
uv run --locked python -m rigarus_backend.day_driver_example
uv run --locked python -m unittest discover -s tests -p 'test_daily_driver*.py' -v
```

The console example creates only a temporary fictional profile. It explicitly
seeds source/target Crews, two employees, daily availability and independent daily
company-driver assertions, then reads one coherent snapshot. No Home Crew implies
attendance. No operational profile, customer data or saved transfer is used.

| Preview | Expected |
| --- | --- |
| Propose source's still-assigned driver without source override | Blocked: source/target personnel overlap; no ranked option |
| Explicitly remove source's sole driver | Blocked: source has known zero drivers; target remains conservatively Pending because2C1 empty-source scope is unknown |
| Explicitly replace source with the other eligible worker | Personnel/company-driver subchecks Satisfied, one ranked candidate; full validation Pending |
| Edit source replacement's company approval after snapshot | Earlier proof Stale |

All cases keep Apply=false / Publish=false. The explicit source roster is a
detached what-if input, never a staffing write. #25 minimum/skills/independent
qualifications, actual #24 Rig/#27 consent and operator review remain required.
Company authority, legal/category/expiry policy and operator UI are not certified.
This example is engineering reproduction, not native Windows/offline customer UAT.
