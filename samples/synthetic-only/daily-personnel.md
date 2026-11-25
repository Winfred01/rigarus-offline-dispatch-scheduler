# Synthetic daily personnel/candidate validation (#105)

From src/Rigarus.Backend after locked bundle restore:

```powershell
uv run --locked python -m rigarus_backend.day_recommendation_example
uv run --locked python -m unittest discover -s tests -p test_daily_personnel_conflicts.py -v
uv run --locked python -m unittest discover -s tests -p test_day_personnel_validation.py -v
```

The example seeds a temporary synthetic schema14 profile only, then computes
read-only proposals. New personnel output demonstrates:

| Explicit candidate membership | Collision subcheck | Candidate comparison | Full validation |
| --- | --- | --- | --- |
| No actual members supplied | Pending | Pending option | Pending / Apply=false / Publish=false |
| Worker still in Crew2's saved Monday PM, proposed Crew1 Monday | Blocked | Excluded | Pending / Apply=false / Publish=false |
| Separate explicitly nominated worker | Satisfied for collision only | Pending option for other resources | Pending / Apply=false / Publish=false |

Source Crew2/member/date/revision/raw PM reference is retained. Driver, minimum,
skills, qualification and availability rechecks remain Pending; source membership
is never removed. Daily #23/#25 must inspect both sides of a real transfer later.
No Home Crew attendance, automatic worker selection or half-day approval inference.

Use DayRecommendationQuery.proposed_employee_ids only to capture extra explicit
workers' sources in the same pinned view. It does not assign them. Pass immutable
ProposedDayMembers per generated date to validate_day_candidate_personnel; missing
dates mean unknown, duplicate/out-of-plan dates reject. Uncaptured employee context
cannot pass. The v2 input and separate proposal SHA256 bind current sources and
member choices; freshness Current is not an Apply lock/approval. All production
daily-input/day-Draft writes stay closed; no UI or recommendation API is added.
