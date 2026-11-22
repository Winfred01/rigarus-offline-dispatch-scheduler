import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState, type SubmitEvent } from "react";
import {
  localToday,
  validLocalDate,
  assignmentFailureNeedsReload,
  type AssignmentSeed,
  type DraftAssignment,
} from "./assignment-fields";

type Crew = { id: number; name: string; type: string; active: boolean };
type Project = { id: number; job_number: string; site_name: string };
type WorkItem = {
  id: number;
  type: string;
  required_crew_count: number;
  estimated_half_days: number;
};
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

export function Schedule({ seed }: { seed?: AssignmentSeed }) {
  const [day, setDay] = useState(localToday);
  const [dateField, setDateField] = useState(day);
  const [crews, setCrews] = useState<Crew[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [rows, setRows] = useState<DraftAssignment[]>([]);
  const [editor, setEditor] = useState<Editor | undefined>(() =>
    seed
      ? {
          id: null,
          project_id: seed.projectId,
          work_item_id: seed.workItemId,
          crew_id: 0,
          local_date: day,
          slot: "AM",
          notes: "",
        }
      : undefined,
  );
  const [cancelling, setCancelling] = useState<DraftAssignment>();
  const [selected, setSelected] = useState<number>();
  const [busy, setBusy] = useState(true);
  const [blocked, setBlocked] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const location = useRef<HTMLParagraphElement>(null);
  const assignButton = useRef<HTMLButtonElement>(null);

  async function load(date: string) {
    const [assignments, crewRows, projectRows] = await Promise.all([
      invoke<DraftAssignment[]>("list_assignments", {
        query: { start_date: date, end_date: date, include_cancelled: true },
      }),
      invoke<Crew[]>("search_crews", { term: "" }),
      invoke<Project[]>("search_projects", { term: "" }),
    ]);
    setRows(assignments);
    setCrews(crewRows);
    setProjects(projectRows);
    setDay(date);
    setDateField(date);
    setBlocked(false);
  }

  async function refresh(date: string, discard = false) {
    if (!validLocalDate(date)) {
      setError("Enter a valid local date as YYYY-MM-DD.");
      return;
    }
    setBusy(true);
    setError("");
    setStatus("");
    if (discard) {
      setEditor(undefined);
      setCancelling(undefined);
    }
    try {
      await load(date);
    } catch (failure) {
      setError(String(failure));
      setBlocked(true);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    void refresh(day);
  }, []);
  useEffect(() => {
    if (selected && !editor) location.current?.focus();
  }, [selected, editor, rows]);

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || busy || blocked) return;
    if (!validLocalDate(editor.local_date)) {
      setError("Enter a valid local date as YYYY-MM-DD.");
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
    setRows([]);
    setSelected(saved.id);
    setDay(saved.local_date);
    setDateField(saved.local_date);
    setStatus("Draft saved. Validation pending.");
    try {
      await load(saved.local_date);
    } catch {
      setError(
        "Draft was saved, but the list could not refresh. Reload assignments.",
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
    setRows([]);
    setStatus("Draft cancelled. The slot is available again.");
    try {
      await load(day);
    } catch {
      setError(
        "Draft was cancelled, but the list could not refresh. Reload assignments.",
      );
      setBlocked(true);
    } finally {
      setBusy(false);
    }
  }
  const selectedRow = rows.find((row) => row.id === selected);
  return (
    <main className="frame project-master schedule-drafts">
      <div className="page-heading">
        <h1>Schedule</h1>
        <button
          type="button"
          disabled
          title="Driver, personnel and Rig validation is pending"
        >
          Publish unavailable
        </button>
      </div>
      <p className="draft-warning" id="assignment-safety">
        Draft / Validation pending. Only Crew/date/half-day occupancy is
        checked. Driver approval, actual workers, time off, qualifications and
        Rig compliance are pending. These drafts cannot be published.
      </p>
      <p>
        AM/PM is provisional for Demo B; final scheduling granularity awaits
        customer confirmation.
      </p>
      <div className="actions">
        <button
          ref={assignButton}
          disabled={
            busy ||
            blocked ||
            !!editor ||
            !!cancelling ||
            !crews.length ||
            !projects.length
          }
          onClick={() => {
            setError("");
            setStatus("");
            setEditor({
              id: null,
              project_id: 0,
              work_item_id: 0,
              crew_id: 0,
              local_date: day,
              slot: "AM",
              notes: "",
            });
          }}
        >
          Assign Work Item
        </button>
        <button
          className="secondary-button"
          disabled={busy}
          id="reload-assignments"
          onClick={() =>
            void refresh(
              editor && validLocalDate(editor.local_date)
                ? editor.local_date
                : day,
              true,
            )
          }
        >
          Reload assignments
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
          {blocked && " Reload replaces the current form with saved records."}
        </p>
      )}
      <p role="status">
        {busy ? "Loading or saving draft assignments…" : status}
      </p>
      {editor ? (
        <AssignmentEditor
          key={editor.id ?? "new"}
          value={editor}
          projects={projects}
          crews={crews}
          disabled={busy || blocked}
          busy={busy}
          onChange={setEditor}
          onSubmit={save}
          onCancel={() => {
            setEditor(undefined);
            if (!blocked) setError("");
            setStatus("");
            requestAnimationFrame(() =>
              blocked
                ? document.getElementById("reload-assignments")?.focus()
                : assignButton.current?.focus(),
            );
          }}
        />
      ) : (
        <>
          <form
            className="project-search"
            onSubmit={(event) => {
              event.preventDefault();
              if (!busy) void refresh(dateField);
            }}
          >
            <label htmlFor="schedule-date">Local date (YYYY-MM-DD)</label>
            <div className="search-controls">
              <input
                id="schedule-date"
                value={dateField}
                onChange={(event) => setDateField(event.target.value)}
                maxLength={10}
                required
              />
              <button disabled={busy}>Show date</button>
            </div>
          </form>
          <section aria-labelledby="assignment-list-title">
            <h2 id="assignment-list-title">Draft assignments — {day}</h2>
            {selectedRow && (
              <p id="assignment-location" ref={location} tabIndex={-1}>
                Selected slot: {selectedRow.crew_name} (#{selectedRow.crew_id})
                · {selectedRow.local_date} {selectedRow.slot} · Work Item #
                {selectedRow.work_item_id} · {selectedRow.status} #
                {selectedRow.id}
              </p>
            )}
            {!busy && (!projects.length || !crews.length) && (
              <p>
                Add a Project with Work Items and a Crew before assigning work.
              </p>
            )}
            {rows.length ? (
              <div className="project-table">
                <table aria-label="Saved draft assignments">
                  <thead>
                    <tr>
                      {[
                        "Date / half-day",
                        "Project / Work Item",
                        "Crew",
                        "State",
                        "Notes",
                        "Action",
                      ].map((title) => (
                        <th key={title} scope="col">
                          {title}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr
                        key={row.id}
                        aria-current={selected === row.id ? "true" : undefined}
                      >
                        <td>
                          {row.local_date} {row.slot}
                        </td>
                        <td>
                          {row.job_number} · {row.site_id} · {row.site_name}
                          <br />
                          {row.work_type} · Work Item #{row.work_item_id}
                          <br />
                          Requires {row.required_crew_count} Crew(s) · Estimate{" "}
                          {row.estimated_half_days} half-day(s)
                        </td>
                        <td>
                          {row.crew_name} (#{row.crew_id})
                          {!row.crew_active && " · Inactive"}
                        </td>
                        <td>
                          {row.status === "Draft"
                            ? "Draft / Validation pending"
                            : "Cancelled"}
                        </td>
                        <td>{row.notes || "—"}</td>
                        <td>
                          {row.status === "Draft" && (
                            <>
                              <button
                                aria-label={`Edit Draft ${row.id}`}
                                disabled={busy || blocked || !!cancelling}
                                onClick={() => {
                                  setEditor({
                                    id: row.id,
                                    revision: row.revision,
                                    project_id: row.project_id,
                                    work_item_id: row.work_item_id,
                                    crew_id: row.crew_id,
                                    local_date: row.local_date,
                                    slot: row.slot,
                                    notes: row.notes,
                                  });
                                  setError("");
                                  setStatus("");
                                }}
                              >
                                Edit
                              </button>
                              <button
                                className="secondary-button"
                                aria-label={`Cancel Draft ${row.id}`}
                                disabled={busy || blocked || !!cancelling}
                                onClick={() => setCancelling(row)}
                              >
                                Cancel draft
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              !busy && !error && <p>No draft assignments on this date.</p>
            )}
            {cancelling && (
              <section aria-labelledby="cancel-draft-title">
                <h3 id="cancel-draft-title">
                  Cancel saved Draft #{cancelling.id}?
                </h3>
                <p>
                  This releases {cancelling.crew_name} on{" "}
                  {cancelling.local_date} {cancelling.slot}. The cancelled
                  record and its ID remain.
                </p>
                <div className="actions">
                  <button
                    disabled={busy || blocked}
                    onClick={() => void cancelSaved()}
                  >
                    Confirm cancellation
                  </button>
                  <button
                    className="secondary-button"
                    disabled={busy}
                    onClick={() => setCancelling(undefined)}
                  >
                    Keep draft
                  </button>
                </div>
              </section>
            )}
          </section>
        </>
      )}
    </main>
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
