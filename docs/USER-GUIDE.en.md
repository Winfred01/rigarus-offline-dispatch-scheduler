# Rigarus — English User Guide

[中文使用说明书](USER-GUIDE.zh-CN.md) · [Project README](../README.md)

**Edition:** November25,2026 engineering preview. **Source baseline:** main
`a3da29a` plus Issue117 read-only preview (awaiting human review). The desktop
interface is English. Confirm the commit of your installed build.
It is an operator reference, not customer acceptance or production authorization.

## Contents

- [1. Scope and current availability](#scope)
- [2. Install and start](#startup)
- [3. Navigation and search](#navigation)
- [4. Projects and WorkItems](#projects)
- [5. Crews, employees, Foreman and Rigs](#resources)
- [6. Legacy Draft lifecycle](#drafts)
- [7. Select actual workers](#staffing)
- [8. Crew and Project working calendars](#calendars)
- [9. Employee availability](#availability)
- [10. Employee Week](#employee-week)
- [11. Review and Locate](#locate)
- [12. Import preview and Bulk Add](#imports)
- [13. Daily recommendations and status meanings](#recommendations)
- [14. Local data, upgrades and recovery](#data)
- [15. Troubleshooting](#troubleshooting)
- [16. Synthetic practice checklist](#practice)

<a id="scope"></a>
## 1. Scope and current availability

Rigarus runs locally on Windows for a single dispatcher. It does not require a
software account or cloud calendar. Windows11 x64 is the primary target.

The owner has confirmed **one Full Day** as the minimum unit for new scheduling.
The current desktop still exposes **legacy AM/PM compatibility controls**.
Use the half-day instructions below only to inspect existing records or practise
with an isolated synthetic profile supplied by a maintainer. They are not a new
full-day dispatch procedure. Do not combine two old visits, round half-day estimates
or assume an AM/PM record proves a whole day.

| Feature | At this baseline |
| --- | --- |
| Projects, Crews, employees, Foreman, Rig inventory | Desktop management available |
| Weekly boards, existing Drafts, actual worker selection, Locate | Desktop legacy compatibility available |
| Working calendars and employee availability | Desktop half-day controls; independent daily backend also exists |
| Full-day Drafts, daily date generation and resource checks | Backend engineering; production daily writes remain closed |
| Full-day WorkItem Auto-Recommend | Read-only date alternatives, explanations and Current/Stale checks |
| Complete daily editing and full-day weekly boards | Awaiting desktop integration |
| Human Apply, locks, transaction revalidation, recoverable versions | Awaiting complete workflow |
| Published schedules and company/Crew/employee PDF/Excel | Unavailable; export controls remain disabled |

Every Draft/proposal remains **Validation Pending**. Do not distribute it as a
confirmed employee schedule. A resource subcheck passing does not approve dispatch.

<a id="startup"></a>
## 2. Install and start

1. Obtain a maintainer-reviewed Windows x64 engineering installer for an identified
   commit. Check the supplied filename/hash and, if provided, `build.json`.
   A CI artifact is not automatically a customer release.
2. Run the approved installer. It includes the Python local service/runtime and
   an offline WebView2 installer for machines that need it. Operator PCs do not
   need Python, Node.js, Rust or a .NET SDK.
3. Start **Rigarus Dispatch** from the Windows Start menu. Normal operation is
   local/offline; there is no sign-in. The initial view is **Schedule → Job Schedule**.
4. Use the same Windows account to return to the same default local data.
   For practice, ask the maintainer for an isolated synthetic profile rather than
   experimenting on customer data.

Use a complete reviewed package. Copying the desktop EXE alone omits its local
service/resources. Build instructions belong in the [README](../README.md#develop-and-test-windows);
operators do not need to run source-code commands.

<a id="navigation"></a>
## 3. Navigation and search

| Location | Purpose |
| --- | --- |
| Schedule | Job Schedule, Crew Board, Employee Week, Working calendars and supported overview/equipment views |
| Project Management | Project/WorkItem records and Bulk Add Projects |
| People | Employees, Crews and Availability |
| Items | Rig inventory |
| Reports | Weekly Export gate and missing prerequisites |
| Data | Import preview and separate synthetic Demo note |
| Settings / Help | Device appearance settings / contextual instructions |

Use **Previous/Next week**, **Today** or the date field and **Go** for local
Sunday–Saturday weeks. Enter dates as `YYYY-MM-DD`. Crew/Project filters affect
what is shown, not saved assignments. Scroll inside a long board to reach later
rows. Multi-day strips still contain individual saved visits.

Use the top workspace search or **Ctrl+K**, choose a record type and open a result.
A Schedule result can locate its saved card. **Tab**, **Shift+Tab** and
**Enter/Space** operate focused controls; respect disabled/loading controls.
In **Settings → Appearance**, changes preview immediately. **Save appearance**
keeps them on this device; cancelling restores the previous saved settings.

<a id="projects"></a>
## 4. Projects and WorkItems

1. Open **Project Management → New project**.
2. Enter **Job #**, **Site ID** and site name. Keep identifiers as text to preserve
   leading zeroes. Use fictional identifiers such as `SYN-1001` for practice.
3. Use **Add work item** when needed. Select the displayed Type and supply valid
   **Required crews** and **Estimated half-days** in this legacy form. The latter
   is historical estimate metadata, not confirmed Remaining Days.
4. Select **Save project**, then find/open the saved project using Search.
   Edit the existing record instead of creating a duplicate.

Follow field-level errors before retrying. A project needs a WorkItem before it
can be assigned. Civil/Tower WorkItems can remain separate within one Project;
both inherit the parent's working calendar. Saving a project does not schedule it
or reduce its remaining work. Never infer completed work from existing Drafts.

<a id="resources"></a>
## 5. Crews, employees, Foreman and Rigs

- **People → Crews → New crew:** enter the Crew name/type and save. Open **Edit**
  for changes; use **Foreman** to review/set/clear the current appointment and
  inspect history, then **Save Foreman**.
- **People → Employees → New employee:** choose the Home Crew, supply the displayed
  name/Level/eligibility/active fields and select **Save employee**. A Crew must
  exist before selecting it as Home Crew.
- **Items → New rig:** record Rig number/type, optional default Crew and notes,
  then **Save rig**.

Home Crew describes the employee's normal affiliation, not attendance on every
job. Appointing a Foreman or borrowing a worker does not change Home Crew.
A Level is not a professional certificate. An active Rig or default Crew link
does not prove actual dated vehicle allocation, inspection or company-driver
eligibility. Daily evidence editors are not available here yet.

<a id="drafts"></a>
## 6. Legacy Draft lifecycle

**Compatibility/synthetic use only:** the following existing editor is AM/PM.
There is no production full-day editor at this baseline.

1. Open **Schedule → Job Schedule**, choose the week and select **Assign Work Item**.
2. Select the Project, WorkItem and Crew; enter the local date and displayed
   legacy half-day. Add optional assignment notes.
3. Inspect the calendar feedback and select **Save to Draft**. Wait for the result.
   **Cancel** before saving makes no write.
4. Select the saved card to inspect its stable **Draft #**, date, Crew, workers,
   notes and revision. Use **Edit draft → Save to Draft** to change it.
5. To cancel a saved visit, use **Cancel draft → Confirm cancellation**.
   **Keep draft** leaves it unchanged. Cancellation retains identity/history and
   releases its capacity; other active visits to that WorkItem remain.
6. Close and reopen the app to check persistence in a synthetic practice session.

An existing Crew/slot collision is rejected. Daily storage also protects overlap
between full-day and old active half-day records; a different Slot is not a bypass.
Do not keep retrying a save whose result is uncertain—reload first.
Changing WorkItem/Crew/date/slot requires staffing reconfirmation; note-only
legacy edits retain the selected workers.

<a id="staffing"></a>
## 7. Select actual workers

1. Open a saved Draft card and its **Draft workers** section.
2. Select **Choose workers**, search **Find employee**, and explicitly select the
   workers intended for this visit.
3. Review each person's recorded availability and Home Crew/borrowed context.
4. Select **Save workers to Draft**, or **Cancel worker changes** to discard edits.
   Use **Reload worker availability** if that independent read failed.

Only the saved selection is used for Employee Week. Home Crew is never expanded
automatically. An empty or missing roster is not safe staffing; Available does not
approve dispatch, and Unavailable does not silently remove a selected Draft worker.
Borrowing must also recheck the original Crew's staffing, driver and qualifications;
the desktop selection alone does not complete those checks.

<a id="calendars"></a>
## 8. Crew and Project working calendars

1. Open **Schedule → Working calendars**.
2. Select **Crew** or **Project**, choose the record and week.
3. Inspect a cell or select **Record working dates**. Enter the inclusive dates,
   displayed legacy coverage and **Can work / Cannot work / Not recorded**.
4. Select **Save working dates** to replace only the selected coverage, or cancel.
   Use **Calendar change history** to inspect prior saves and **Reload calendar**
   after stale/uncertain results.

WorkItems inherit the parent Project calendar; there is no WorkItem override.
Both calendars must explicitly support work for a match. Blank means unknown,
not a default workweek or holiday permission. **Calendar matched** is only that
subcheck; it never supplies personnel/driver/Rig/weekend clearance.
The current **Full day** legacy control writes both old halves; it is not the
new independent daily contract or an automatic historical conversion.

<a id="availability"></a>
## 9. Employee availability

1. Open **People → Availability**, select the employee and week.
2. Select a cell or **Record availability**.
3. Choose the inclusive date range, displayed coverage and **Available /
   Unavailable / Not recorded**, then **Save availability**.
4. To discard the open edits use **Cancel availability changes**. Review the
   displayed history or reload after a stale/failed read.

These desktop controls still use the legacy Full day/AM/PM form. Recording only
one half as Available never proves whole-day availability. Not recorded is unknown.
Availability is independent of actual staffing, approved leave, driver eligibility,
qualifications and weekend consent; changing it does not rewrite assignments.

<a id="employee-week"></a>
## 10. Employee Week

Open **Schedule → Employee Week**, select the employee and week. It shows only
visits with explicit saved worker membership, along with borrowed-Crew context
and independently recorded availability. Home Crew alone creates no visits.
Select a visit for read-only details; use **Reload employee week** after an error.

**Export preview** is an in-app planning snapshot labelled **DRAFT – NOT CONFIRMED**.
Its **Export PDF / Export Excel** actions are disabled. It does not create a
sendable confirmed schedule or contact employees.

<a id="locate"></a>
## 11. Review and Locate

1. In Schedule, open **Review & Publish**. The review includes the week's saved
   visits even when board filters hide them.
2. For a listed record, select **Locate**. You can also use **Locate in Job
   Schedule** in Draft details, or open a Schedule result from global search.
3. The source dialog closes; **Job Schedule / 1 Week** switches to the record's
   local week, reveals the exact saved card and moves keyboard focus there.
   Compatible filters remain; obstructing filters/row limits can be adjusted.
4. The cue clears after about two seconds. Reduced motion uses static emphasis;
   consecutive Locate requests replace the old cue. Press Enter on the focused
   card to open details.

Locate uses the stable assignment identity, so same-day AM and PM remain
distinguishable. It does not change SQLite. Cancelled/missing targets produce
feedback instead of being recreated. Reload stale data before trying again.
The review shows observed calendar/staffing feedback, not all backend daily
resource checks. **Publish schedule unavailable** remains disabled.

<a id="imports"></a>
## 12. Import preview and Bulk Add

These are different workflows:

| Entry | Input and effect |
| --- | --- |
| Data → Import preview | Local `.xlsx` up to5MiB; **Preview workbook** is read-only, **Cancel preview** clears the preview |
| Project Management → Bulk Add Projects | Pasted CSV/Excel TAB-separated text or local `.xlsx`; **Preview projects** then explicit **Confirm … projects** can create new projects |

For **Import preview**, row1 uses **Job #, Site ID, Site Name**. Optional fields
are described on that screen; inspect diagnostics/source cells. This is not a
complete historical-workbook importer.

For **Bulk Add Projects**, use exactly these three headers and one project per
row; keep IDs as text:

```csv
Project Number,Site ID,Site Name
SYN-1001,0010,Synthetic North Site
SYN-1002,0020,Synthetic South Site
```

Review Ready/Skipped counts and errors before confirming. Existing/duplicate
projects are skipped, not overwritten. Changing text/file/tab invalidates the old
preview; preview again. Cancel before confirmation saves nothing. Bulk Add does
not create daily assignments, infer WorkItems or reconcile real historic schedules.

<a id="recommendations"></a>
## 13. Daily recommendations and status meanings

In **Project Management**, open a saved Project and choose **Auto-Recommend**
beside its WorkItem. This reads the existing daily snapshot; it saves no assignment.

1. Enter a positive whole number of **Remaining Days** and explicitly confirm it.
   Nothing is prefilled from estimated half-days or deducted from saved visits.
2. Select candidate Crews as alternatives, not simultaneous staffing. Select local
   start/end dates (inclusive, at most366 dates) and1–10 alternatives (default3).
3. Choose **Preview full-day dates**. **Earliest Finish** is the default;
   **Earliest Start** rebuilds the same input with that sort order.
4. Expand **Dates and missing checks** for accumulated/skipped dates, reasons and
   missing-check counts. Incomplete candidates show Needs Review without a false
   finish. A result limit omits additional complete alternatives, not their capacity.
5. **Recheck inputs** distinguishes Current, Stale and Unavailable. Returning to the
   window also rechecks. Current is true only at the last read, never a reservation.
   Changed inputs require another preview. Editing inputs clears old output.
6. **Close preview** or Escape cancels the read-only dialog and returns focus.
   Reopening starts with blank, unconfirmed Remaining Days.

All cards stay **Validation pending**. Actual workers and Rig are not selected;
**Apply to Draft** and **Publish** remain disabled. Production daily writers and
daily calendar/consent evidence editors remain closed or unimplemented. Old AM/PM
calendar controls do not create full-day facts. Without explicit daily input,
expect Unknown/Needs Review; ask the maintainer to use an isolated synthetic
profile for engineering demonstrations. Do not edit a customer database manually.

Weekend planning needs every relevant worker Confirmed; partial/Pending/refusal
cannot shorten a plan through that weekend.

| Status | Meaning / action |
| --- | --- |
| Draft / Validation Pending | Saved planning only; do not issue as confirmed work |
| Calendar matched | Crew and Project calendar subcheck matched; other checks remain |
| Pending / Not recorded / Unknown | Evidence missing or unresolved; do not assume available/approved |
| Blocked / Declined | Known blocker/refusal; resolve and rebuild/review |
| Needs Review / Legacy / Conversion Required | Incomplete or incompatible evidence; preserve originals and obtain explicit review |
| Current | Observed inputs equal at the freshness check; not a future lock |
| Stale | Inputs changed; rebuild the proposal, do not reuse old dates/proof |

All proposals remain **Apply=false / Publish=false**. Reports cannot export
validated company/Crew/employee files yet. Human Before/After, locks, transactional
Apply, audit and recoverable versions must precede formal dispatch/export.

<a id="data"></a>
## 14. Local data, upgrades and recovery

Default database: `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`.
Use the same Windows account/profile. Keep customer information, attachments,
WAL files, backups and diagnostics on authorized local storage.

There is no complete operator Backup/Restore interface yet. Arrange a verified
consistent backup with the maintainer before upgrades or recovery. Do not copy
only a running WAL-mode `rigarus.db`, delete `-wal/-shm` files, edit SQL or erase
migration history. For a maintenance copy, first close all Rigarus instances and
have the maintainer confirm the local service has stopped; preserve the entire
relevant profile and verify the copy before changing the original.

Current startup has additive migration and verified pre-upgrade backup safeguards.
A newer database may be rejected by an older build. Recovery requires a verified
independent backup and its compatible binary, retaining the newer profile for
reconciliation of later edits. Never overwrite the live database to force a
downgrade. See [data guidance](07-SECURITY-BACKUP.md).

<a id="troubleshooting"></a>
## 15. Troubleshooting

| Symptom | Action |
| --- | --- |
| Empty board | Check week, Crew/Project filters and whether saved visits exist; no visible cards is not proof of completed work |
| No WorkItems / employees | Add the required master records, then reload; Home Crew does not auto-fill staffing |
| Calendar pending/conflict | Inspect both Crew and parent Project dates; unknown is not a loading error |
| Revision changed / stale | Reload current records, review differences, then make a deliberate new edit |
| Save outcome uncertain | Reload before retrying; check whether it already committed |
| Saved, but refresh failed | The write may have succeeded; reload instead of duplicating it |
| Local service unavailable | Close/reopen Rigarus; if persistent, check the complete reviewed installation with the maintainer |
| Database locked / unavailable | Close other Rigarus instances; check local-folder access; do not delete database/WAL files |
| Compatible version required | Stop; use the matching build or verified independent recovery copy |
| Disabled Apply/Publish/export | Expected at this baseline; there is no approved bypass |

For support record the build commit/version, steps, visible message and expected
result. Share only sanitized descriptions/synthetic reproduction. Keep original
customer workbooks, databases, screenshots with real personnel and raw logs local.

<a id="practice"></a>
## 16. Synthetic practice checklist

With a maintainer-prepared isolated synthetic profile:

1. Create `SYN-1001`, a Civil WorkItem, a Crew and two fictional employees.
2. Inspect/record legacy Crew/Project calendars and employee availability.
3. Save a legacy Draft, explicitly select workers and inspect Employee Week.
4. Locate it from review/details/search; verify the exact date/card and cue.
5. Edit notes, reload/reopen, then explicitly cancel the visit; check other visits
   remain. Confirm form Cancel makes no change.
6. Preview the synthetic CSV above; confirm Bulk Add only when ready.
7. Confirm Publish/PDF/Excel remain unavailable and no file is sent.

This guide was checked against source labels/contracts. This documentation change
does **not** constitute a newly executed native GUI/offline install/UAT run.
See the [engineering acceptance index](05-DEMO-ACCEPTANCE.md) for actual conditions.
