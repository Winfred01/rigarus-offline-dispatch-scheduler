import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState, type SubmitEvent } from "react";
import { nextSort, sortRows, type SortState } from "./table-sort";
import { BulkProjects } from "./bulk-projects";
import {
  projectLabels,
  projectFieldError,
  projectFieldErrors,
  projectServerFieldError,
  type ProjectField,
} from "./project-validation";
import {
  workItemCountError,
  validateWorkItemCounts,
} from "./work-item-validation";

const projectColumns = [
  ["job_number", "Job #"],
  ["site_id", "Site ID"],
  ["site_name", "Site name"],
  ["work_item_count", "Work items"],
] as const;
const workItemColumns = [
  ["type", "Type"],
  ["required_crew_count", "Required crews"],
  ["estimated_half_days", "Estimated half-days"],
] as const;

function SortHeader({
  label,
  table,
  direction,
  disabled,
  onSort,
}: {
  label: string;
  table: string;
  direction?: "ascending" | "descending";
  disabled: boolean;
  onSort: () => void;
}) {
  const nextDirection = direction === "ascending" ? "descending" : "ascending";
  return (
    <th scope="col" aria-sort={direction}>
      <button
        type="button"
        className="sort-header"
        disabled={disabled}
        aria-label={`Sort ${table} by ${label} ${nextDirection}`}
        onClick={onSort}
      >
        {label}{" "}
        <span className="sort-indicator" aria-hidden="true">
          {direction === "ascending"
            ? "↑"
            : direction === "descending"
              ? "↓"
              : "⇅"}
        </span>
      </button>
    </th>
  );
}

type ProjectFields = { job_number: string; site_id: string; site_name: string };
type Summary = ProjectFields & { id: number; work_item_count: number };
const workTypes = ["Small", "Civil", "Tower", "Other"] as const;
type WorkType = (typeof workTypes)[number];
type WorkItem = {
  id: number | null;
  type: WorkType;
  required_crew_count: number;
  estimated_half_days: number;
};
type Project = ProjectFields & { id: number; work_items: WorkItem[] };
type DraftItem = {
  id: number | null;
  key: number;
  type: WorkType;
  crews: string;
  halfDays: string;
};

export function ProjectMaster() {
  const [term, setTerm] = useState("");
  const [appliedTerm, setAppliedTerm] = useState("");
  const [rows, setRows] = useState<Summary[]>([]);
  const [detail, setDetail] = useState<Project>();
  const [editor, setEditor] = useState<{ project?: Project }>();
  const [bulk, setBulk] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [projectSort, setProjectSort] =
    useState<SortState<(typeof projectColumns)[number][0]>>();
  const [workItemSort, setWorkItemSort] =
    useState<SortState<(typeof workItemColumns)[number][0]>>();

  async function refresh(search: string, preferredId?: number, reveal = false) {
    setError("");
    setLoading(true);
    try {
      let found = await invoke<Summary[]>("search_projects", { term: search });
      if (
        reveal &&
        search.trim() &&
        !found.some((row) => row.id === preferredId)
      ) {
        found = await invoke<Summary[]>("search_projects", { term: "" });
        setTerm("");
        search = "";
      }
      setRows(found);
      setAppliedTerm(search);
      const selected = found.find((row) => row.id === preferredId) ?? found[0];
      setDetail(
        selected
          ? await invoke<Project>("read_project", { id: selected.id })
          : undefined,
      );
    } catch (failure) {
      setDetail(undefined);
      setError(String(failure));
    } finally {
      setLoading(false);
    }
  }

  async function select(id: number) {
    setLoading(true);
    setError("");
    try {
      setDetail(await invoke<Project>("read_project", { id }));
    } catch (failure) {
      setDetail(undefined);
      setError(String(failure));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh("");
  }, []);

  return (
    <main className="frame project-master">
      <div className="page-heading">
        <h1>Projects</h1>
        <div className="search-controls">
          <button
            disabled={loading || !!editor || bulk}
            onClick={() => {
              setStatus("");
              setEditor({});
            }}
          >
            New project
          </button>
          <button
            disabled={loading || !!editor || bulk}
            onClick={() => {
              setStatus("");
              setBulk(true);
            }}
          >
            Bulk Add Projects
          </button>
        </div>
      </div>
      {bulk ? (
        <BulkProjects
          onCancel={() => setBulk(false)}
          onSaved={(message, firstId) => {
            setBulk(false);
            setStatus(message);
            void refresh(appliedTerm, firstId ?? detail?.id, true);
          }}
        />
      ) : editor ? (
        <ProjectEditor
          project={editor.project}
          onCancel={() => setEditor(undefined)}
          onSaved={(project) => {
            setEditor(undefined);
            setStatus("Project saved.");
            void refresh(appliedTerm, project.id, true);
          }}
        />
      ) : (
        <>
          <section aria-labelledby="backlog-title">
            <h2 id="backlog-title">Unscheduled backlog</h2>
            <form
              className="project-search"
              onSubmit={(event) => {
                event.preventDefault();
                setStatus("");
                void refresh(term, detail?.id);
              }}
            >
              <label htmlFor="project-search">
                Search by Job #, Site ID or site name
              </label>
              <div className="search-controls">
                <input
                  id="project-search"
                  type="search"
                  value={term}
                  onChange={(event) => setTerm(event.target.value)}
                />
                <button disabled={loading}>Search</button>
              </div>
            </form>
            <p className="project-status" role="status">
              {loading
                ? "Loading projects…"
                : `${rows.length} ${rows.length === 1 ? "project" : "projects"}`}
              {status && ` · ${status}`}
            </p>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            {rows.length > 0 ? (
              <div className="project-table">
                <table aria-label="Unscheduled projects">
                  <thead>
                    <tr>
                      {projectColumns.map(([key, label]) => (
                        <SortHeader
                          key={key}
                          label={label}
                          table="projects"
                          direction={
                            projectSort?.key === key
                              ? projectSort.direction
                              : undefined
                          }
                          disabled={loading}
                          onSort={() =>
                            setProjectSort((current) => nextSort(current, key))
                          }
                        />
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sortRows(rows, projectSort).map((row) => (
                      <tr key={row.id}>
                        <th scope="row">
                          <button
                            type="button"
                            className="job-link"
                            disabled={loading}
                            aria-current={
                              detail?.id === row.id ? "true" : undefined
                            }
                            onClick={() => void select(row.id)}
                          >
                            {row.job_number}
                          </button>
                        </th>
                        <td>{row.site_id}</td>
                        <td>{row.site_name}</td>
                        <td>{row.work_item_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              !loading &&
              !error && (
                <p>
                  {appliedTerm.trim()
                    ? "No projects match your search."
                    : "No projects yet. Create a project to start the backlog."}
                </p>
              )
            )}
          </section>
          {detail && (
            <section className="project-detail" aria-labelledby="detail-title">
              <div className="page-heading">
                <h2 id="detail-title">
                  {detail.job_number} · {detail.site_name}
                </h2>
                <button
                  disabled={loading}
                  onClick={() => {
                    setStatus("");
                    setEditor({ project: detail });
                  }}
                >
                  Edit project
                </button>
              </div>
              <p>Site ID {detail.site_id}</p>
              <h3>Work items</h3>
              {detail.work_items.length > 0 ? (
                <div className="project-table">
                  <table aria-label="Project work items">
                    <thead>
                      <tr>
                        {workItemColumns.map(([key, label]) => (
                          <SortHeader
                            key={key}
                            label={label}
                            table="work items"
                            direction={
                              workItemSort?.key === key
                                ? workItemSort.direction
                                : undefined
                            }
                            disabled={loading}
                            onSort={() =>
                              setWorkItemSort((current) =>
                                nextSort(current, key),
                              )
                            }
                          />
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sortRows(detail.work_items, workItemSort).map((item) => (
                        <tr key={item.id}>
                          <th scope="row">{item.type}</th>
                          <td>{item.required_crew_count}</td>
                          <td>{item.estimated_half_days}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p>No work items yet.</p>
              )}
            </section>
          )}
        </>
      )}
    </main>
  );
}

const fieldHelp = {
  job_number:
    "Use a unique project number. Existing project numbers cannot be overwritten. Example: SYN-100.",
  site_id:
    "Enter the site identifier as text to keep leading zeroes, for example 0001.",
  site_name:
    "Use a clear, descriptive site name, for example Synthetic North Yard.",
  type: "Choose Small, Civil, Tower or Other.",
  crews: "The number of crews needed. Enter a whole number greater than zero.",
  halfDays:
    "Enter whole half-days: 1 = 0.5 day and 4 = 2 days. The minimum is one half-day.",
};

function FieldHelp({
  id,
  label,
  text,
}: {
  id: string;
  label: string;
  text: string;
}) {
  return (
    <>
      <button
        type="button"
        className="field-help-button secondary-button"
        aria-label={`Help: ${label}`}
        popoverTarget={`${id}-help`}
      >
        <span aria-hidden="true">i</span>
      </button>
      <div
        id={`${id}-help`}
        popover="auto"
        className="field-help-popover"
        role="note"
      >
        <strong>{label}</strong>
        <p>{text}</p>
        <button
          type="button"
          className="secondary-button"
          popoverTarget={`${id}-help`}
          popoverTargetAction="hide"
        >
          Close help
        </button>
      </div>
    </>
  );
}

function ProjectEditor({
  project,
  onCancel,
  onSaved,
}: {
  project?: Project;
  onCancel: () => void;
  onSaved: (project: Project) => void;
}) {
  const [fields, setFields] = useState<ProjectFields>(
    project ?? { job_number: "", site_id: "", site_name: "" },
  );
  const [items, setItems] = useState<DraftItem[]>(() =>
    (project?.work_items ?? []).map((item, key) => ({
      key,
      id: item.id,
      type: item.type,
      crews: String(item.required_crew_count),
      halfDays: String(item.estimated_half_days),
    })),
  );
  const [nextKey, setNextKey] = useState(items.length);
  const [working, setWorking] = useState(false);
  const [attempted, setAttempted] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [failure, setFailure] = useState("");
  const [focusRequest, setFocusRequest] = useState<{ id: string }>();
  const controls = useRef(new Map<string, HTMLElement>());
  const fieldOrder = [
    ...(Object.keys(projectLabels) as ProjectField[]).map((id) => ({
      id,
      label: projectLabels[id],
    })),
    ...items.flatMap((item, index) => [
      { id: `type-${item.key}`, label: `Work item ${index + 1} Type` },
      {
        id: `crews-${item.key}`,
        label: `Work item ${index + 1} Required crews`,
      },
      {
        id: `half-days-${item.key}`,
        label: `Work item ${index + 1} Estimated half-days`,
      },
    ]),
  ];
  const issues = fieldOrder.filter((field) => errors[field.id]);

  useEffect(() => {
    if (!focusRequest) return;
    const control = controls.current.get(focusRequest.id);
    control?.scrollIntoView({ block: "center" });
    control?.focus({ preventScroll: true });
  }, [focusRequest]);

  function controlRef(id: string) {
    return (element: HTMLElement | null) => {
      if (element) controls.current.set(id, element);
      else controls.current.delete(id);
    };
  }

  function updateError(id: string, message: string | undefined) {
    setErrors((current) => {
      const next = { ...current };
      if (message) next[id] = message;
      else delete next[id];
      return next;
    });
  }

  function changeField(field: ProjectField, value: string) {
    setFields((current) => ({ ...current, [field]: value }));
    setFailure("");
    if (attempted) updateError(field, projectFieldError(value, field));
  }

  function changeItem(key: number, patch: Partial<DraftItem>) {
    setItems((current) =>
      current.map((item) => (item.key === key ? { ...item, ...patch } : item)),
    );
    setFailure("");
    if (!attempted) return;
    for (const field of ["crews", "halfDays"] as const) {
      if (patch[field] !== undefined)
        updateError(
          `${field === "crews" ? "crews" : "half-days"}-${key}`,
          workItemCountError(patch[field], field),
        );
    }
    if (patch.type !== undefined)
      updateError(
        `type-${key}`,
        workTypes.includes(patch.type)
          ? undefined
          : "Choose Small, Civil, Tower or Other.",
      );
  }

  function removeDraft(key: number) {
    setItems((current) => current.filter((item) => item.key !== key));
    setErrors((current) => {
      const next = { ...current };
      for (const prefix of ["type", "crews", "half-days"])
        delete next[`${prefix}-${key}`];
      return next;
    });
    setFailure("");
  }

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (working) return;
    setAttempted(true);
    setFailure("");
    const checked: Record<string, string> = { ...projectFieldErrors(fields) };
    const counts = validateWorkItemCounts(items);
    for (const item of items) {
      if (!workTypes.includes(item.type))
        checked[`type-${item.key}`] = "Choose Small, Civil, Tower or Other.";
      const messages = counts.errors[item.key];
      if (messages?.crews) checked[`crews-${item.key}`] = messages.crews;
      if (messages?.halfDays)
        checked[`half-days-${item.key}`] = messages.halfDays;
    }
    setErrors(checked);
    const first = fieldOrder.find((field) => checked[field.id]);
    if (first) {
      setFocusRequest({ id: first.id });
      return;
    }
    setWorking(true);
    try {
      const saved = await invoke<Project>("save_project", {
        id: project?.id ?? null,
        project: {
          ...fields,
          work_items: items.map((item) => ({
            id: item.id,
            type: item.type,
            required_crew_count: Number(item.crews.trim()),
            estimated_half_days: Number(item.halfDays.trim()),
          })),
        },
      });
      onSaved(saved);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const fieldError = projectServerFieldError(message);
      if (fieldError) {
        setErrors({ [fieldError.field]: fieldError.message });
        setFocusRequest({ id: fieldError.field });
      } else setFailure(message);
    } finally {
      setWorking(false);
    }
  }

  function fieldMessage(id: string) {
    return errors[id] ? (
      <p id={`${id}-error`} className="field-error">
        <span aria-hidden="true">! </span>
        {errors[id]}
      </p>
    ) : null;
  }

  return (
    <section className="project-editor-panel" aria-labelledby="editor-title">
      <div className="editor-heading">
        <h2 id="editor-title">{project ? "Edit project" : "New project"}</h2>
      </div>
      <form className="project-editor" onSubmit={save} noValidate>
        <fieldset disabled={working}>
          <div className="project-fields">
            {(Object.keys(projectLabels) as ProjectField[]).map((field) => (
              <div className="project-field" key={field}>
                <div className="field-heading">
                  <label htmlFor={field}>{projectLabels[field]}</label>
                  <FieldHelp
                    id={field}
                    label={projectLabels[field]}
                    text={fieldHelp[field]}
                  />
                </div>
                <input
                  id={field}
                  ref={controlRef(field)}
                  required
                  value={fields[field]}
                  aria-invalid={errors[field] ? true : undefined}
                  aria-describedby={
                    errors[field] ? `${field}-error` : undefined
                  }
                  onChange={(event) => changeField(field, event.target.value)}
                />
                {fieldMessage(field)}
              </div>
            ))}
          </div>
          <div
            className="work-items-group"
            role="group"
            aria-labelledby="work-items-heading"
          >
            <h3 id="work-items-heading">Work items</h3>
            {items.length === 0 && (
              <p className="project-status">
                No work items yet. You can add them now or after saving the
                project.
              </p>
            )}
            {items.map((item, index) => {
              const invalid = ["type", "crews", "half-days"].some(
                (prefix) => errors[`${prefix}-${item.key}`],
              );
              return (
                <fieldset
                  key={item.key}
                  className={`work-item${invalid ? " has-errors" : ""}`}
                >
                  <legend>
                    Work item {index + 1}
                    {invalid && (
                      <span className="work-item-attention">
                        Needs attention
                      </span>
                    )}
                  </legend>
                  <div className="project-field">
                    <div className="field-heading">
                      <label htmlFor={`type-${item.key}`}>Type</label>
                      <FieldHelp
                        id={`type-${item.key}`}
                        label={`Type for work item ${index + 1}`}
                        text={fieldHelp.type}
                      />
                    </div>
                    <select
                      id={`type-${item.key}`}
                      ref={controlRef(`type-${item.key}`)}
                      value={item.type}
                      aria-invalid={
                        errors[`type-${item.key}`] ? true : undefined
                      }
                      aria-describedby={
                        errors[`type-${item.key}`]
                          ? `type-${item.key}-error`
                          : undefined
                      }
                      onChange={(event) =>
                        changeItem(item.key, {
                          type: event.target.value as WorkType,
                        })
                      }
                    >
                      {workTypes.map((type) => (
                        <option key={type}>{type}</option>
                      ))}
                    </select>
                    {fieldMessage(`type-${item.key}`)}
                  </div>
                  {(
                    [
                      ["crews", "Required crews", "crews"],
                      ["halfDays", "Estimated half-days", "half-days"],
                    ] as const
                  ).map(([field, label, prefix]) => {
                    const id = `${prefix}-${item.key}`;
                    return (
                      <div key={field} className="project-field">
                        <div className="field-heading">
                          <label htmlFor={id}>{label}</label>
                          <FieldHelp
                            id={id}
                            label={`${label} for work item ${index + 1}`}
                            text={fieldHelp[field]}
                          />
                        </div>
                        <input
                          id={id}
                          ref={controlRef(id)}
                          inputMode="numeric"
                          required
                          value={item[field]}
                          aria-invalid={errors[id] ? true : undefined}
                          aria-describedby={
                            errors[id] ? `${id}-error` : undefined
                          }
                          onChange={(event) =>
                            changeItem(item.key, {
                              [field]: event.target.value,
                            })
                          }
                        />
                        {fieldMessage(id)}
                      </div>
                    );
                  })}
                  {item.id === null && (
                    <button
                      type="button"
                      className="secondary-button remove-draft"
                      aria-label={`Remove draft work item ${index + 1}`}
                      onClick={() => removeDraft(item.key)}
                    >
                      Remove draft
                    </button>
                  )}
                </fieldset>
              );
            })}
            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setItems((current) => [
                  ...current,
                  {
                    id: null,
                    key: nextKey,
                    type: "Small",
                    crews: "1",
                    halfDays: "1",
                  },
                ]);
                setNextKey(nextKey + 1);
              }}
            >
              Add work item
            </button>
          </div>
          <div className="actions">
            <button>Save project</button>
            <button
              type="button"
              className="secondary-button"
              onClick={onCancel}
            >
              Cancel
            </button>
          </div>
        </fieldset>
        {issues.length > 0 && (
          <div
            id="project-error-summary"
            className="error-summary"
            role="alert"
            aria-labelledby="validation-title"
          >
            <h3 id="validation-title">
              Check {issues.length} {issues.length === 1 ? "field" : "fields"}{" "}
              before saving
            </h3>
            <ul>
              {issues.map((field) => (
                <li key={field.id}>
                  <button
                    type="button"
                    className="error-link"
                    aria-label={`Go to ${field.label}`}
                    onClick={() => setFocusRequest({ id: field.id })}
                  >
                    {field.label}: {errors[field.id]}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {failure && (
          <p className="error" role="alert">
            {failure}
          </p>
        )}
        <p role="status">{working ? "Saving project…" : ""}</p>
      </form>
    </section>
  );
}
