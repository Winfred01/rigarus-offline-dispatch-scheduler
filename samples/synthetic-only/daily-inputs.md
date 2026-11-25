# Synthetic daily input example (#101)

Run `python -m unittest discover -s tests -p test_daily_calendars.py -v`
from `src/Rigarus.Backend` after the locked bundle restore. These tests create
temporary synthetic SQLite profiles and use explicit app-factory test opt-in.
Production sidecar writes remain closed; no operator UI is shipped in this slice.

| Evidence for synthetic Crew / 2026-12-31 | Effective daily state | Explanation |
| --- | --- | --- |
| No evidence | Unknown | No default weekday work |
| Old AM Working only | Unknown / Needs Review | Missing full-date assertion |
| Old AM Working, PM NotWorking | NotWorking / Needs Review | Known blocker; raw halves retained |
| Read daily range, explicitly review raw halves, confirm a new daily Working assertion using revision/token | Working / Current | New assertion; old halves/history unchanged |
| Later legacy PM edit | Unknown or negative / Stale | Prior receipt invalid; re-review required |
| Explicit daily Unknown | Unknown | Stored tombstone; no positive fallback |

Read `GET /daily-calendars/Crew/{id}?start_date=2026-12-31&end_date=2026-12-31`.
The strict PUT body has start_date, end_date, state, confirmed_by_operator=true,
legacy_reviewed=true when raw old cells exist, notes, expected_revision and
expected_review_token from that exact range read. It has **no slot**. A changed
scope/ID/range/daily revision/legacy revision requires a new read (409); new
confirmation is mandatory. Employee uses Available/Unavailable/Unknown, with
Unknown labelled Not recorded. WorkItems inherit their actual Project daily input.

GET `/daily-calendars/assessment?work_item_id={id}&crew_id={id}&local_date=2026-12-31`
can report calendar Matched only when both current daily inputs say Working.
It always retains resource Validation Pending, Apply=false, Publish=false;
weekend consent is separately Pending. Availability never proves attendance,
driver status or eligibility. No generation/assignment is performed by this example.
