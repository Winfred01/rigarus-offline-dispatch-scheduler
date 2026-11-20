import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState, type SubmitEvent } from "react";
import { nextSort, sortRows, type SortState } from "./table-sort";
import { BulkProjects } from "./bulk-projects";

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
  const [error, setError] = useState("");

  function changeItem(key: number, patch: Partial<DraftItem>) {
    setItems(
      items.map((item) => (item.key === key ? { ...item, ...patch } : item)),
    );
  }

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setWorking(true);
    setError("");
    try {
      const work_items = items.map((item, index) => {
        const counts = [item.crews.trim(), item.halfDays.trim()];
        if (
          counts.some(
            (count) =>
              !/^\+?\d+$/.test(count) ||
              Number(count) < 1 ||
              Number(count) > 2147483647,
          )
        ) {
          throw new Error(
            `Work item ${index + 1} needs a positive whole number for crews and estimated half-days.`,
          );
        }
        return {
          id: item.id,
          type: item.type,
          required_crew_count: Number(counts[0]),
          estimated_half_days: Number(counts[1]),
        };
      });
      const { job_number, site_id, site_name } = fields;
      const saved = await invoke<Project>("save_project", {
        id: project?.id ?? null,
        project: { job_number, site_id, site_name, work_items },
      });
      onSaved(saved);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setWorking(false);
    }
  }

  const labels = {
    job_number: "Job #",
    site_id: "Site ID",
    site_name: "Site name",
  };
  return (
    <section aria-labelledby="editor-title">
      <h2 id="editor-title">{project ? "Edit project" : "New project"}</h2>
      <form className="project-editor" onSubmit={save}>
        <fieldset disabled={working}>
          <div className="project-fields">
            {(Object.keys(labels) as (keyof ProjectFields)[]).map((field) => (
              <label key={field}>
                {labels[field]}
                <input
                  id={field}
                  required
                  value={fields[field]}
                  onChange={(event) =>
                    setFields({ ...fields, [field]: event.target.value })
                  }
                />
              </label>
            ))}
          </div>
          <h3>Work items</h3>
          {items.map((item, index) => (
            <fieldset key={item.key} className="work-item">
              <legend>Work item {index + 1}</legend>
              <label>
                Type
                <select
                  id={`type-${index}`}
                  value={item.type}
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
              </label>
              <label>
                Required crews
                <input
                  id={`crews-${index}`}
                  inputMode="numeric"
                  value={item.crews}
                  onChange={(event) =>
                    changeItem(item.key, { crews: event.target.value })
                  }
                />
              </label>
              <label>
                Estimated half-days
                <input
                  id={`half-days-${index}`}
                  inputMode="numeric"
                  value={item.halfDays}
                  onChange={(event) =>
                    changeItem(item.key, { halfDays: event.target.value })
                  }
                />
              </label>
              {item.id === null && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    setItems(
                      items.filter((candidate) => candidate.key !== item.key),
                    )
                  }
                >
                  Remove draft
                </button>
              )}
            </fieldset>
          ))}
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setItems([
                ...items,
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
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </form>
    </section>
  );
}
