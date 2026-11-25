# Daily recommendations from synthetic SQLite (#103)

From `src/Rigarus.Backend`, after `uv sync --locked --group bundle`, run:

```powershell
uv run --locked python -m rigarus_backend.day_recommendation_example
uv run --locked python -m unittest discover -s tests -p test_day_recommendations.py -v
uv run --locked python -m unittest discover -s tests -p test_day_recommendation_adapter.py -v
```

Only the example's temporary synthetic profile is seeded. Recommendation reads
never initialize/migrate/write; production daily-input/day-Draft HTTP gates remain
closed. Do not change this example to point at a customer profile.

For confirmed2 days, C1 has Monday/Friday, C2 Tuesday/Wednesday. EarliestFinish
returns C2,C1; EarliestStart returns C1,C2. Skipped dates retain reasons and resource
checks stay Pending. After explicitly making Wednesday/Thursday Working for C1,
confirmed4 days allocates Monday23, Wednesday25, Thursday26, Friday27 November2026,
skips Tuesday and finishes Friday. Earlier snapshot is Stale after the input edit.

Independent input is `ConfirmedRemainingDays(4, True)`. Unconfirmed/fractional/bool
counts reject, missing duration is Needs Review. The old estimate99 half-days
does not set duration. The day query has no half-day field. WorkItem inherits actual
Project calendar; any active old half or new day Draft blocks its Crew's whole date.
Calendar Unknown/closure/stale and missing occupancy or weekend consent never count.

Every plan stays Pending / Apply=false / Publish=false. Dates are proposals; no
actual proposed employees, driver, Rig or approval is inferred. Reproducible
dates/order are stable for identical logical inputs; each fresh temporary path,
new recorded timestamps and edit revision intentionally produce different source
fingerprints. Current is a comparison result at read time, not dispatch authority.
