import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState, type SubmitEvent } from "react";
import {
  localToday,
  validLocalDate,
  assignmentFailureNeedsReload,
  type AssignmentSeed,
  type DraftAssignment,
} from "./assignment-fields";
import {
  readWorkspace,
  type Workspace,
  type Crew,
  type Project,
  type WorkItem,
} from "./workspace-data";
import { weekDays, shiftDay, displayDate, inWeek } from "./week";
import { Dialog } from "./dialog";
import { weekCells } from "./week-cells";
import { StaffingPanel, staffingLabel } from "./staffing";
import { EmployeeWeek } from "./employee-week";
import {
  WorkingCalendar,
  CalendarFeedback,
  DraftCalendarPreview,
} from "./working-calendar";

type Editor = {
  id: number | null;
  revision?: number;
  project_id: number;
  work_item_id: number;
  crew_id: number;
  local_date: string;
  slot: "AM" | "PM";
  notes: string;
};
export type ScheduleView =
  | "Job Schedule"
  | "Crew Board"
  | "Overview"
  | "Employee Week"
  | "Working calendars";
const emptyWorkspace: Workspace = {
  crews: [],
  people: [],
  rigs: [],
  projects: [],
  assignments: [],
  foremen: [],
};
export const publishBlockers = [
  "Draft worker choices are not dispatch approval. Time off and staffing validation remain pending (#22).",
  "Driver approval, qualifications, minimum staffing and Rig availability checks are pending (#15/#23).",
  "Locks and weekend approval checks are pending. AM/PM remains provisional for Demo B.",
  "No validated immutable Published snapshot exists (#17/#32). Formal export is unavailable.",
];

export function Schedule({
  seed,
  target,
  view,
  onView,
  day,
  onDay,
  employeeId,
  onEmployee,
}: {
  seed?: AssignmentSeed;
  target?: { id: number; date: string };
  view: ScheduleView;
  onView: (view: ScheduleView) => void;
  day: string;
  onDay: (value: string) => void;
  employeeId: number;
  onEmployee: (id: number) => void;
}) {
  const setDay = onDay;
  const [dateField, setDateField] = useState(day);
  useEffect(() => {
    setDateField(day);
  }, [day]);
  const [data, setData] = useState<Workspace>(emptyWorkspace);
  const [editor, setEditor] = useState<Editor>();
  const [cancelling, setCancelling] = useState<DraftAssignment>();
  const [selected, setSelected] = useState<number>();
  const [review, setReview] = useState(false);
  const [crewFilter, setCrewFilter] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  const [busy, setBusy] = useState(true);
  const [blocked, setBlocked] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [queueOpen, setQueueOpen] = useState(false);
  const alive = useRef(true);
  const assignButton = useRef<HTMLButtonElement>(null);
  const days = weekDays(day);

  async function load() {
    const loaded = await readWorkspace();
    if (alive.current) {
      setData(loaded);
      setBlocked(false);
    }
  }
  async function refresh(discard = false) {
    setBusy(true);
    setError("");
    setStatus("");
    if (discard) {
      setEditor(undefined);
      setCancelling(undefined);
      setSelected(undefined);
    }
    try {
      await load();
    } catch (failure) {
      if (alive.current) {
        setData(emptyWorkspace);
        setError(String(failure));
        setBlocked(true);
      }
    } finally {
      if (alive.current) setBusy(false);
    }
  }
  useEffect(() => {
    alive.current = true;
    void refresh();
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    if (seed) {
      setEditor({
        id: null,
        project_id: seed.projectId,
        work_item_id: seed.workItemId,
        crew_id: 0,
        local_date: day,
        slot: "AM",
        notes: "",
      });
      setSelected(undefined);
    }
  }, [seed]);
  useEffect(() => {
    if (!editor && selected && !busy) {
      const card = document.getElementById(`assignment-${selected}`);
      const scroll = card?.closest<HTMLElement>(".week-scroll");
      if (card && scroll) {
        const box = scroll.getBoundingClientRect();
        const rect = card.getBoundingClientRect();
        const headerHeight =
          scroll.querySelector("thead")?.getBoundingClientRect().height ?? 0;
        if (rect.top < box.top + headerHeight)
          scroll.scrollTop += rect.top - box.top - headerHeight;
        else if (rect.bottom > box.bottom)
          scroll.scrollTop += rect.bottom - box.bottom;
        const rosterWidth =
          scroll.querySelector("th")?.getBoundingClientRect().width ?? 0;
        if (rect.left < box.left + rosterWidth)
          scroll.scrollLeft += rect.left - box.left - rosterWidth;
        else if (rect.right > box.right)
          scroll.scrollLeft += rect.right - box.right;
        card.focus({ preventScroll: true });
      }
    }
  }, [editor, selected, busy, view]);
  useEffect(() => {
    if (target) {
      setDay(target.date);
      setDateField(target.date);
      setSelected(target.id);
    }
  }, [target]);
  function navigate(date: string) {
    if (!validLocalDate(date)) {
      setError("Choose a valid local date (years 0001–9999).");
      return;
    }
    setDay(date);
    setDateField(date);
    setSelected(undefined);
    setError("");
    setStatus("");
  }
  function begin(projectId = 0, workItemId = 0) {
    setError("");
    setStatus("");
    setSelected(undefined);
    setEditor({
      id: null,
      project_id: projectId,
      work_item_id: workItemId,
      crew_id: Number(crewFilter),
      local_date: day,
      slot: "AM",
      notes: "",
    });
  }
  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || busy || blocked) return;
    if (!validLocalDate(editor.local_date)) {
      setError("Enter a valid local date.");
      document.getElementById("assignment-date")?.focus();
      return;
    }
    setBusy(true);
    setError("");
    setStatus("");
    let saved: DraftAssignment;
    try {
      const { id, revision, project_id: _project, ...fields } = editor;
      saved = await invoke<DraftAssignment>("save_assignment", {
        id,
        assignment: {
          ...fields,
          ...(id === null ? {} : { expected_revision: revision }),
        },
      });
    } catch (failure) {
      setError(String(failure));
      setBlocked(assignmentFailureNeedsReload(String(failure)));
      setBusy(false);
      return;
    }
    setEditor(undefined);
    setSelected(saved.id);
    setQueueOpen(false);
    setDay(saved.local_date);
    setDateField(saved.local_date);
    setCrewFilter("");
    setProjectFilter("");
    setData(emptyWorkspace);
    setStatus("Draft saved. Validation pending.");
    try {
      await load();
    } catch {
      setError(
        "Draft was saved, but the board could not refresh. Reload assignments.",
      );
      setBlocked(true);
    } finally {
      setBusy(false);
    }
  }
  async function cancelSaved() {
    if (!cancelling || busy || blocked) return;
    setBusy(true);
    setError("");
    setStatus("");
    try {
      await invoke<DraftAssignment>("cancel_assignment", {
        id: cancelling.id,
        expectedRevision: cancelling.revision,
      });
    } catch (failure) {
      setError(String(failure));
      setBlocked(true);
      setBusy(false);
      return;
    }
    setCancelling(undefined);
    setSelected(undefined);
    setData(emptyWorkspace);
    setQueueOpen(true);
    setStatus(
      "Draft cancelled. Its slot is available; work without active visits returns to the unscheduled queue.",
    );
    try {
      await load();
    } catch {
      setError(
        "Draft was cancelled, but the board could not refresh. Reload assignments.",
      );
      setBlocked(true);
    } finally {
      setBusy(false);
      requestAnimationFrame(() => assignButton.current?.focus());
    }
  }
  const rows = data.assignments.filter(
    (row) =>
      inWeek(row.local_date, days) &&
      (!crewFilter || row.crew_id === Number(crewFilter)) &&
      (!projectFilter || row.project_id === Number(projectFilter)),
  );
  const selectedRow = data.assignments.find((row) => row.id === selected);
  const assigned = new Set(data.assignments.map((row) => row.work_item_id));
  const pending = data.projects.flatMap((project) =>
    project.work_items
      .filter((item) => !assigned.has(item.id))
      .map((item) => ({ project, item })),
  );
  const groups =
    view === "Crew Board"
      ? data.crews
          .filter((crew) => !crewFilter || crew.id === Number(crewFilter))
          .map((crew) => ({
            id: crew.id,
            title: crew.name,
            crew,
            project: undefined as Project | undefined,
          }))
      : data.projects
          .filter(
            (project) =>
              (!projectFilter || project.id === Number(projectFilter)) &&
              (projectFilter ||
                data.assignments.some((row) => row.project_id === project.id)),
          )
          .map((project) => ({
            id: project.id,
            title: project.site_name,
            project,
            crew: undefined as Crew | undefined,
          }));
  const controlsDisabled = busy || !!editor || !!cancelling;
  const closeEditor = () => {
    setEditor(undefined);
    if (!blocked) setError("");
    setStatus("");
    requestAnimationFrame(() =>
      blocked
        ? document.getElementById("reload-assignments")?.focus()
        : assignButton.current?.focus(),
    );
  };
  const navigation = (
    <nav className="view-tabs" aria-label="Schedule views">
      {(
        [
          "Overview",
          "Job Schedule",
          "Crew Board",
          "Employee Week",
          "Working calendars",
        ] as const
      ).map((name) => (
        <button
          key={name}
          aria-current={name === view ? "page" : undefined}
          disabled={controlsDisabled}
          onClick={() => onView(name)}
        >
          {name}
        </button>
      ))}
    </nav>
  );
  if (view === "Working calendars")
    return <WorkingCalendar navigation={navigation} />;
  return (
    <main className="schedule-page project-master">
      <p className="breadcrumb">Schedule / {view}</p>
      <h1>{view}</h1>
      {navigation}
      <div className="week-toolbar">
        <button
          aria-label="Previous week"
          disabled={controlsDisabled || days[0] < "0001-01-08"}
          onClick={() => navigate(shiftDay(day, -7))}
        >
          ‹
        </button>
        <button
          disabled={controlsDisabled}
          onClick={() => navigate(localToday())}
        >
          Today
        </button>
        <button
          aria-label="Next week"
          disabled={controlsDisabled || days[6] > "9999-12-24"}
          onClick={() => navigate(shiftDay(day, 7))}
        >
          ›
        </button>
        <strong className="week-range">
          {displayDate(days[0])} – {displayDate(days[6])}
        </strong>
        <form
          className="date-jump"
          onSubmit={(event) => {
            event.preventDefault();
            navigate(dateField);
          }}
        >
          <label className="sr-only" htmlFor="schedule-date">
            Jump to local date
          </label>
          <input
            id="schedule-date"
            type="date"
            value={dateField}
            disabled={controlsDisabled}
            onChange={(event) => setDateField(event.target.value)}
            required
          />
          <button disabled={controlsDisabled}>Go</button>
        </form>
        <span className="draft-state">Draft · Validation pending</span>
        <button
          disabled={controlsDisabled || view === "Employee Week"}
          onClick={() => setReview(true)}
        >
          Review &amp; Publish
        </button>
        <label className="filter-label" hidden={view === "Employee Week"}>
          Crew filter
          <select
            aria-label="Crew filter"
            disabled={controlsDisabled}
            value={crewFilter}
            onChange={(event) => {
              setCrewFilter(event.target.value);
              setSelected(undefined);
            }}
          >
            <option value="">All crews</option>
            {data.crews.map((crew) => (
              <option key={crew.id} value={crew.id}>
                {crew.name}
                {!crew.active && " · Inactive"}
              </option>
            ))}
          </select>
        </label>
        {(view === "Job Schedule" ||
          (projectFilter && view !== "Employee Week")) && (
          <label className="filter-label">
            Project filter
            <select
              aria-label="Project filter"
              disabled={controlsDisabled}
              value={projectFilter}
              onChange={(event) => setProjectFilter(event.target.value)}
            >
              <option value="">All projects</option>
              {data.projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.job_number} · {project.site_name}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      <div className="schedule-feedback" aria-live="polite">
        {busy ? "Loading or saving local schedule…" : status}
      </div>
      {!editor && error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="board-actions" hidden={view === "Employee Week"}>
        <button
          ref={assignButton}
          disabled={
            controlsDisabled ||
            blocked ||
            !data.crews.length ||
            !data.projects.length
          }
          onClick={() => begin()}
        >
          Assign Work Item
        </button>
        <button
          id="reload-assignments"
          className="secondary-button"
          disabled={busy}
          onClick={() => {
            if (editor && validLocalDate(editor.local_date))
              navigate(editor.local_date);
            void refresh(true);
          }}
        >
          Reload assignments
        </button>
      </div>
      {view === "Employee Week" ? (
        <EmployeeWeek
          people={data.people}
          crews={data.crews}
          days={days}
          employeeId={employeeId}
          onEmployee={onEmployee}
          rosterBusy={busy}
          rosterError={blocked}
          onRosterReload={() => void refresh(true)}
        />
      ) : view === "Overview" ? (
        <section className="schedule-overview">
          <dl>
            <div>
              <dt>Scheduled visits this week</dt>
              <dd>{rows.length}</dd>
            </div>
            <div>
              <dt>Crews with visits</dt>
              <dd>{new Set(rows.map((row) => row.crew_id)).size}</dd>
            </div>
            <div>
              <dt>Actual staffing not assigned</dt>
              <dd>
                {
                  rows.filter(
                    (row) =>
                      !row.staffing?.configured || !row.staffing.workers.length,
                  ).length
                }
              </dd>
            </div>
          </dl>
          <button onClick={() => onView("Job Schedule")}>
            Open Job Schedule
          </button>
        </section>
      ) : (
        <>
          <details
            className="unscheduled"
            open={queueOpen}
            onToggle={(event) => setQueueOpen(event.currentTarget.open)}
          >
            <summary>
              Unscheduled work items · {busy ? "Loading…" : pending.length}
            </summary>
            <p>
              No active visits on any date. Additional visits can always be
              assigned by Work Item ID; estimates are not automatically
              deducted.
            </p>
            <ul>
              {pending.map(({ project, item }) => (
                <li key={item.id}>
                  <span>
                    {project.job_number} · Site {project.site_id} ·{" "}
                    {project.site_name} · {item.type} #{item.id} ·{" "}
                    {item.estimated_half_days} half-days
                  </span>
                  <button
                    disabled={controlsDisabled || blocked}
                    onClick={() => begin(project.id, item.id)}
                  >
                    Assign
                  </button>
                </li>
              ))}
            </ul>
            {!busy && !pending.length && <p>No unscheduled work items.</p>}
          </details>
          <div
            className="week-scroll"
            tabIndex={0}
            aria-label="Scrollable weekly schedule"
            aria-busy={busy}
          >
            <table className="week-grid" aria-label={`${view} Sunday–Saturday`}>
              <thead>
                <tr>
                  <th scope="col">
                    {view === "Crew Board"
                      ? "Crew / Rig / Home roster"
                      : "Project / Job number"}
                  </th>
                  {days.map((date, index) => (
                    <th
                      key={date}
                      scope="col"
                      className={`${index === 0 || index === 6 ? "weekend" : ""} ${date === localToday() ? "today" : ""}`}
                    >
                      <span>
                        {
                          ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][
                            index
                          ]
                        }
                      </span>
                      <time dateTime={date}>
                        {date.slice(8)}
                        <small>{date.slice(0, 7)}</small>
                      </time>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => (
                  <tr key={group.id}>
                    <th scope="row">
                      <strong>{group.title}</strong>
                      {group.crew ? (
                        <HomeRoster crew={group.crew} data={data} />
                      ) : (
                        <small>
                          {group.project?.job_number} · Site{" "}
                          {group.project?.site_id}
                        </small>
                      )}
                    </th>
                    {weekCells(
                      days,
                      rows.filter((row) =>
                        group.crew
                          ? row.crew_id === group.id
                          : row.project_id === group.id,
                      ),
                    ).map((cell) => (
                      <td
                        key={cell.dates[0]}
                        colSpan={cell.dates.length}
                        className={
                          cell.dates.length > 1
                            ? "multiday-cell"
                            : cell.start === 0 || cell.start === 6
                              ? "weekend"
                              : ""
                        }
                      >
                        {cell.dates.length > 1 ? (
                          <div
                            className={`multiday-strip ${cell.assignments[0].work_type === "Tower" ? "tower-strip" : ""}`}
                            id={`assignment-span-${cell.assignments[0].id}`}
                            role="group"
                            aria-label={`Consecutive saved visits, ${cell.dates[0]} to ${cell.dates.at(-1)}, ${cell.assignments.length} Draft visits`}
                          >
                            <div className="strip-heading">
                              <strong>
                                {cell.assignments[0].work_type} · Draft ·{" "}
                                {cell.dates.length} dates
                              </strong>
                              <span>
                                {cell.assignments[0].job_number} · Site{" "}
                                {cell.assignments[0].site_id} ·{" "}
                                {cell.assignments[0].site_name} ·{" "}
                                {cell.assignments[0].crew_name}
                              </span>
                              <span>
                                {cell.assignments.length} saved AM/PM visits ·
                                Workers are recorded per AM/PM visit
                              </span>
                            </div>
                            <div className="strip-days">
                              {cell.dates.map((date, offset) => (
                                <div
                                  key={date}
                                  className={`strip-day ${cell.start + offset === 0 || cell.start + offset === 6 ? "weekend" : ""}`}
                                >
                                  <time dateTime={date}>
                                    {displayDate(date)}
                                  </time>
                                  {cell.assignments
                                    .filter((row) => row.local_date === date)
                                    .map((row) => (
                                      <ScheduleCard
                                        key={row.id}
                                        row={row}
                                        selected={selected}
                                        showCrew={false}
                                        compact
                                        onSelect={setSelected}
                                      />
                                    ))}
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          cell.assignments.map((row) => (
                            <ScheduleCard
                              key={row.id}
                              row={row}
                              selected={selected}
                              showCrew={view === "Job Schedule"}
                              onSelect={setSelected}
                            />
                          ))
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {!busy && !groups.length && (
              <p className="board-empty">
                {blocked
                  ? "Schedule unavailable. Reload assignments to retry."
                  : data.projects.length && data.crews.length
                    ? "No scheduled Projects. Expand Unscheduled work items or Assign Work Item to begin."
                    : "Add Projects with Work Items and Crews to begin planning."}
              </p>
            )}
          </div>
          {!busy && !blocked && !rows.length && (
            <p>No assignments in this view for the selected week.</p>
          )}
        </>
      )}
      <p className="schedule-footnote" id="assignment-safety">
        AM/PM is provisional for Demo B. Home roster and default Rig are
        reference data. Workers are explicitly selected per visit; time off is
        not configured. Drafts are not publishable.
      </p>
      {editor && (
        <Dialog
          title={
            editor.id === null ? "Assign work item" : `Edit draft #${editor.id}`
          }
          busy={busy}
          onClose={closeEditor}
        >
          {error && (
            <p className="error" role="alert">
              {error}
              {blocked && " Reload assignments before retrying."}
            </p>
          )}
          <AssignmentEditor
            key={editor.id ?? "new"}
            value={editor}
            projects={data.projects}
            crews={data.crews}
            disabled={busy || blocked}
            busy={busy}
            onChange={setEditor}
            onSubmit={save}
            onCancel={closeEditor}
          />
        </Dialog>
      )}
      {selectedRow && !editor && !cancelling && (
        <Dialog
          title={`${selectedRow.work_type} · Draft #${selectedRow.id}`}
          busy={busy}
          onClose={() => setSelected(undefined)}
        >
          <dl className="record-detail">
            <dt>Project</dt>
            <dd>
              {selectedRow.job_number} · {selectedRow.site_name}
            </dd>
            <dt>Job / Site</dt>
            <dd>
              {selectedRow.job_number} · {selectedRow.site_id}
            </dd>
            <dt>Work Item</dt>
            <dd>
              #{selectedRow.work_item_id} · Estimate{" "}
              {selectedRow.estimated_half_days} half-days · Requires{" "}
              {selectedRow.required_crew_count} crews
            </dd>
            <dt>Date / slot</dt>
            <dd>
              {displayDate(selectedRow.local_date)} · {selectedRow.slot}
            </dd>
            <dt>Crew</dt>
            <dd>
              {selectedRow.crew_name}
              {!selectedRow.crew_active && " · Inactive"}
            </dd>
            <dt>Actual staffing</dt>
            <dd>{staffingLabel(selectedRow)}</dd>
            <dt>Actual Rig</dt>
            <dd>Not assigned. Default Rig is reference only.</dd>
            <dt>State</dt>
            <dd>
              Draft · Validation pending · Revision {selectedRow.revision}
            </dd>
            <dt>Notes</dt>
            <dd className="preserve-lines">{selectedRow.notes || "—"}</dd>
            <dt>Locks / history</dt>
            <dd>Not configured. Current revision is preserved.</dd>
          </dl>
          <CalendarFeedback value={selectedRow.calendar_assessment} />
          <StaffingPanel
            key={selectedRow.id}
            row={selectedRow}
            people={data.people}
            crews={data.crews}
            onBusy={setBusy}
            requiresReload={blocked}
            onUncertain={() => {
              setBlocked(true);
              setError(
                "Worker selection outcome is uncertain. Reload assignments before retrying.",
              );
            }}
            onReload={() => void refresh(true)}
            onSaved={async () => {
              setData(emptyWorkspace);
              setStatus("Draft workers saved. Validation pending.");
              try {
                await load();
              } catch {
                setError(
                  "Workers were saved, but the board could not refresh. Reload assignments.",
                );
                setBlocked(true);
              }
            }}
          />
          <div className="actions">
            <button
              aria-label={`Edit Draft ${selectedRow.id}`}
              disabled={busy || blocked}
              onClick={() => {
                setError("");
                setEditor({
                  id: selectedRow.id,
                  revision: selectedRow.revision,
                  project_id: selectedRow.project_id,
                  work_item_id: selectedRow.work_item_id,
                  crew_id: selectedRow.crew_id,
                  local_date: selectedRow.local_date,
                  slot: selectedRow.slot,
                  notes: selectedRow.notes,
                });
              }}
            >
              Edit draft
            </button>
            <button
              className="secondary-button"
              aria-label={`Cancel Draft ${selectedRow.id}`}
              disabled={busy || blocked}
              onClick={() => setCancelling(selectedRow)}
            >
              Cancel draft
            </button>
          </div>
        </Dialog>
      )}
      {cancelling && (
        <Dialog
          title={`Cancel saved Draft #${cancelling.id}?`}
          busy={busy}
          onClose={() => setCancelling(undefined)}
        >
          <p>
            This releases {cancelling.crew_name} on {cancelling.local_date}{" "}
            {cancelling.slot}. The cancelled record and stable ID remain. A Work
            Item with other active visits stays scheduled.
          </p>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <div className="actions">
            <button
              disabled={busy || blocked}
              onClick={() => void cancelSaved()}
            >
              Confirm cancellation
            </button>
            <button disabled={busy} onClick={() => setCancelling(undefined)}>
              Keep draft
            </button>
          </div>
        </Dialog>
      )}
      {review && (
        <Dialog title="Publish review" onClose={() => setReview(false)}>
          <p>
            {displayDate(days[0])} – {displayDate(days[6])} · Draft
          </p>
          <p>{rows.length} visits in current filters. Validation pending.</p>
          <ul>
            {publishBlockers.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <button disabled>Publish schedule unavailable</button>
        </Dialog>
      )}
    </main>
  );
}

function ScheduleCard({
  row,
  selected,
  showCrew,
  compact = false,
  onSelect,
}: {
  row: DraftAssignment;
  selected?: number;
  showCrew: boolean;
  compact?: boolean;
  onSelect: (id: number) => void;
}) {
  return (
    <button
      id={`assignment-${row.id}`}
      className={`schedule-card ${row.work_type === "Tower" ? "tower-work" : "field-work"} ${compact ? "strip-visit" : ""}`}
      aria-label={`Draft ${row.id}, ${row.job_number}, ${row.local_date} ${row.slot}, ${row.crew_name}`}
      aria-pressed={selected === row.id}
      onClick={() => onSelect(row.id)}
    >
      <strong>
        {row.slot} · {compact ? `Draft #${row.id}` : `${row.work_type} · Draft`}
      </strong>
      {compact && <span>{staffingLabel(row)}</span>}
      {row.calendar_assessment && (
        <small>
          {row.calendar_assessment.status === "Blocked"
            ? "Calendar conflict"
            : row.calendar_assessment.status === "Pending"
              ? "Calendar pending"
              : "Calendar matched · Validation pending"}
        </small>
      )}
      {!compact && (
        <>
          <span>
            {row.job_number} · Site {row.site_id}
          </span>
          {showCrew && <span>{row.crew_name}</span>}
          <span>{staffingLabel(row)}</span>
        </>
      )}
    </button>
  );
}

function HomeRoster({ crew, data }: { crew: Crew; data: Workspace }) {
  const foreman = data.foremen.find((row) => row.crew_id === crew.id);
  const members = data.people
    .filter((person) => person.home_crew_id === crew.id)
    .sort(
      (a, b) =>
        Number(b.id === foreman?.employee_id) -
          Number(a.id === foreman?.employee_id) ||
        a.name.localeCompare(b.name) ||
        a.id - b.id,
    );
  const rigs = data.rigs.filter((rig) => rig.default_crew_id === crew.id);
  return (
    <div className="home-roster">
      <small>
        {crew.type}
        {!crew.active && " · Inactive crew"}
      </small>
      <small>
        Default Rig:{" "}
        {rigs
          .map((rig) => `${rig.number}${rig.active ? "" : " (inactive)"}`)
          .join(", ") || "Not configured"}
      </small>
      <small>Home roster</small>
      {foreman?.employee_id && (
        <strong className="foreman">
          Foreman · {foreman.employee_name}
          {foreman.employee_active === false && " · Inactive"}
          {foreman.employee_eligible === false && " · Eligibility removed"}
          {!members.some((person) => person.id === foreman.employee_id) &&
            " · Other Home Crew"}
        </strong>
      )}
      {members
        .filter((person) => person.id !== foreman?.employee_id)
        .map((person) => (
          <span key={person.id}>
            {person.id === foreman?.employee_id ? (
              <strong>{person.name}</strong>
            ) : (
              person.name
            )}
            {!person.active && " · Inactive"}
          </span>
        ))}
      {!members.length && <small>No Home Crew members</small>}
      <small>Time off not configured</small>
    </div>
  );
}

function AssignmentEditor({
  value,
  projects,
  crews,
  disabled,
  busy,
  onChange,
  onSubmit,
  onCancel,
}: {
  value: Editor;
  projects: Project[];
  crews: Crew[];
  disabled: boolean;
  busy: boolean;
  onChange: (value: Editor) => void;
  onSubmit: (event: SubmitEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}) {
  const [items, setItems] = useState<WorkItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [failure, setFailure] = useState("");
  const [attempt, setAttempt] = useState(0);
  const title = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    title.current?.focus();
  }, []);
  useEffect(() => {
    let active = true;
    setItems([]);
    setFailure("");
    if (!value.project_id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    void invoke<{ work_items: WorkItem[] }>("read_project", {
      id: value.project_id,
    })
      .then((project) => {
        if (active) setItems(project.work_items);
      })
      .catch((error) => {
        if (active) setFailure(String(error));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [value.project_id, attempt]);
  function update(changes: Partial<Editor>) {
    onChange({ ...value, ...changes });
  }
  return (
    <section aria-labelledby="assignment-editor-title">
      <h2 id="assignment-editor-title" ref={title} tabIndex={-1}>
        {value.id === null ? "Assign Work Item" : `Edit Draft #${value.id}`}
      </h2>
      <form
        className="project-editor"
        onSubmit={onSubmit}
        aria-describedby="assignment-safety"
      >
        <fieldset disabled={disabled}>
          <div className="project-fields">
            <label>
              Project
              <select
                id="assignment-project"
                required
                value={value.project_id || ""}
                onChange={(event) =>
                  update({
                    project_id: Number(event.target.value),
                    work_item_id: 0,
                  })
                }
              >
                <option value="">Select a project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.job_number} · {project.site_name} (#{project.id})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Work Item
              <select
                id="assignment-work-item"
                required
                disabled={loading || !!failure || !value.project_id}
                value={
                  items.some((item) => item.id === value.work_item_id)
                    ? value.work_item_id
                    : ""
                }
                onChange={(event) =>
                  update({ work_item_id: Number(event.target.value) })
                }
              >
                <option value="">Select a Work Item</option>
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.type} · Work Item #{item.id} ·{" "}
                    {item.required_crew_count} Crew(s),{" "}
                    {item.estimated_half_days} half-day(s)
                  </option>
                ))}
              </select>
            </label>
            <label>
              Crew
              <select
                id="assignment-crew"
                required
                value={value.crew_id || ""}
                onChange={(event) =>
                  update({ crew_id: Number(event.target.value) })
                }
              >
                <option value="">Select a Crew</option>
                {crews.map((crew) => (
                  <option key={crew.id} value={crew.id}>
                    {crew.name} ({crew.type} #{crew.id})
                    {!crew.active && " · Inactive; validation pending"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Local date (YYYY-MM-DD)
              <input
                id="assignment-date"
                required
                maxLength={10}
                placeholder="YYYY-MM-DD"
                value={value.local_date}
                onChange={(event) => update({ local_date: event.target.value })}
              />
            </label>
            <label>
              Half-day (provisional)
              <select
                id="assignment-slot"
                value={value.slot}
                onChange={(event) =>
                  update({ slot: event.target.value === "PM" ? "PM" : "AM" })
                }
              >
                <option>AM</option>
                <option>PM</option>
              </select>
            </label>
          </div>
          <label htmlFor="assignment-notes">Assignment notes (optional)</label>
          <textarea
            id="assignment-notes"
            maxLength={2000}
            value={value.notes}
            onChange={(event) => update({ notes: event.target.value })}
          />
          <p role="status">
            {loading
              ? "Loading Work Items…"
              : value.project_id && !items.length && !failure
                ? "This project has no Work Items. Add one in Projects."
                : ""}
          </p>
          {failure && (
            <p className="error" role="alert">
              {failure}{" "}
              <button type="button" onClick={() => setAttempt(attempt + 1)}>
                Retry Work Items
              </button>
            </p>
          )}
        </fieldset>
        <DraftCalendarPreview
          workItemId={value.work_item_id}
          crewId={value.crew_id}
          day={value.local_date}
          slot={value.slot}
        />
        <div className="actions">
          <button
            disabled={
              disabled ||
              loading ||
              !!failure ||
              !items.some((item) => item.id === value.work_item_id)
            }
          >
            Save to Draft
          </button>
          <button
            className="secondary-button"
            type="button"
            disabled={busy}
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}
