# Synthetic full-day weekend consent preview

From src/Rigarus.Backend after locked restore:

```powershell
uv run --locked python -m rigarus_backend.day_weekend_example
```

Creates a temporary fictional project/Crew/two employees and explicit Crew/Project
daily Working cells November27–30,2026. Remaining Days=2, explicitly confirmed;
Saturday's planned actual workers are declared independently of HomeCrew.

| Saturday employee decisions | Allocated planning dates | Finish |
| --- | --- | --- |
| Missing/Pending | Friday27, Monday30 | November30 |
| One Confirmed, one missing | Friday27, Monday30 | November30 |
| One Confirmed, one Declined | Friday27, Monday30 | November30 |
| Both Confirmed | Friday27, Saturday28 | November28 |

Prints skipped local dates/reasons, consent subcheck and root Pending/false flags.
Original snapshot becomes Stale after decisions change. Sunday never inherits
Saturday consent. No actual employees are contacted, no saved assignments or
staffing are created/changed, and no Apply/Publish or file delivery occurs.
Console engineering reproduction is not a desktop workflow or customer Demo E.
