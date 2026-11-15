import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState, type SubmitEvent } from "react";

type HomeCrew = {
  id: number;
  name: string;
  type: "Civil" | "Tower";
  active: boolean;
};
type EmployeeDraft = {
  name: string;
  home_crew_id: number;
  skill_level: number;
  foreman_eligible: boolean;
  active: boolean;
};
type Employee = EmployeeDraft & { id: number; driver_status: "Unverified" };

const emptyEmployee: EmployeeDraft = {
  name: "",
  home_crew_id: 0,
  skill_level: 0,
  foreman_eligible: false,
  active: true,
};

function crewLabel(crew: HomeCrew) {
  return (
    crew.name +
    " (" +
    crew.type +
    " #" +
    crew.id +
    (crew.active ? ")" : ", inactive)")
  );
}

export function EmployeeRoster() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [crews, setCrews] = useState<HomeCrew[]>([]);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [editor, setEditor] = useState<{
    id: number | null;
    draft: EmployeeDraft;
  }>();
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const crewsById = new Map(crews.map((crew) => [crew.id, crew]));

  async function load(term: string) {
    const [matches, homeCrews] = await Promise.all([
      invoke<Employee[]>("search_employees", { term }),
      invoke<HomeCrew[]>("search_crews", { term: "" }),
    ]);
    setEmployees(matches);
    setCrews(homeCrews);
    setAppliedSearch(term);
  }

  async function refresh(term: string) {
    setBusy(true);
    setError("");
    setStatus("");
    try {
      await load(term);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh("");
  }, []);

  function edit(employee?: Employee) {
    setError("");
    setStatus("");
    if (employee) {
      const { name, home_crew_id, skill_level, foreman_eligible, active } =
        employee;
      setEditor({
        id: employee.id,
        draft: { name, home_crew_id, skill_level, foreman_eligible, active },
      });
    } else {
      setEditor({ id: null, draft: emptyEmployee });
    }
  }

  function update(changes: Partial<EmployeeDraft>) {
    if (editor)
      setEditor({ ...editor, draft: { ...editor.draft, ...changes } });
  }

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || busy) return;
    setBusy(true);
    setError("");
    try {
      await invoke<Employee>("save_employee", {
        id: editor.id,
        employee: editor.draft,
      });
      setEditor(undefined);
      setStatus("Employee saved.");
      await load(appliedSearch);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="frame project-master">
      <div className="page-heading">
        <h1>Employees</h1>
        <button
          disabled={busy || !!editor || !crews.length}
          onClick={() => edit()}
        >
          New employee
        </button>
      </div>
      {editor ? (
        <section aria-labelledby="employee-editor-title">
          <h2 id="employee-editor-title">
            {editor.id === null ? "New employee" : "Edit employee"}
          </h2>
          <form className="project-editor" onSubmit={save}>
            <fieldset disabled={busy}>
              <div className="project-fields">
                <label>
                  Employee name
                  <input
                    id="employee-name"
                    value={editor.draft.name}
                    maxLength={100}
                    required
                    onChange={(event) => update({ name: event.target.value })}
                  />
                </label>
                <label>
                  Home crew
                  <select
                    id="employee-home-crew"
                    required
                    value={editor.draft.home_crew_id || ""}
                    onChange={(event) =>
                      update({ home_crew_id: Number(event.target.value) })
                    }
                  >
                    <option value="">Select a crew</option>
                    {crews.map((crew) => (
                      <option key={crew.id} value={crew.id}>
                        {crewLabel(crew)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Skill level
                  <select
                    id="employee-skill"
                    required
                    value={editor.draft.skill_level || ""}
                    onChange={(event) =>
                      update({ skill_level: Number(event.target.value) })
                    }
                  >
                    <option value="">Select a level</option>
                    {[1, 2, 3].map((level) => (
                      <option key={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Foreman eligibility
                  <select
                    value={
                      editor.draft.foreman_eligible
                        ? "eligible"
                        : "not-eligible"
                    }
                    onChange={(event) =>
                      update({
                        foreman_eligible: event.target.value === "eligible",
                      })
                    }
                  >
                    <option value="not-eligible">Not eligible</option>
                    <option value="eligible">Eligible</option>
                  </select>
                </label>
                <label>
                  Status
                  <select
                    value={editor.draft.active ? "active" : "inactive"}
                    onChange={(event) =>
                      update({ active: event.target.value === "active" })
                    }
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </label>
              </div>
              <div className="actions">
                <button>Save employee</button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setEditor(undefined);
                    setError("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </fieldset>
          </form>
        </section>
      ) : (
        <section aria-labelledby="employee-list-title">
          <h2 id="employee-list-title">Employee roster</h2>
          <form
            className="project-search"
            onSubmit={(event) => {
              event.preventDefault();
              if (!busy) void refresh(search);
            }}
          >
            <label htmlFor="employee-search">Employee name</label>
            <div className="search-controls">
              <input
                id="employee-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <button disabled={busy}>Search</button>
            </div>
          </form>
          <p className="project-status" role="status">
            {busy ? "Loading employees…" : status}
          </p>
          {employees.length ? (
            <div className="project-table">
              <table>
                <thead>
                  <tr>
                    {[
                      "Employee",
                      "Home crew",
                      "Skill level",
                      "Foreman eligibility",
                      "Driver",
                      "Status",
                      "Action",
                    ].map((label) => (
                      <th key={label} scope="col">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {employees.map((employee) => {
                    const crew = crewsById.get(employee.home_crew_id);
                    return (
                      <tr key={employee.id}>
                        <td>{employee.name}</td>
                        <td>
                          {crew
                            ? crewLabel(crew)
                            : "Crew #" + employee.home_crew_id}
                        </td>
                        <td>{employee.skill_level}</td>
                        <td>
                          {employee.foreman_eligible
                            ? "Eligible"
                            : "Not eligible"}
                        </td>
                        <td>{employee.driver_status}</td>
                        <td>{employee.active ? "Active" : "Inactive"}</td>
                        <td>
                          <button
                            className="job-link"
                            aria-label={"Edit " + employee.name}
                            disabled={busy}
                            onClick={() => edit(employee)}
                          >
                            Edit
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : !busy && !error ? (
            <p>
              {!crews.length
                ? "Create a crew before adding an employee."
                : appliedSearch
                  ? "No employees match your search."
                  : "No employees yet."}
            </p>
          ) : null}
        </section>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </main>
  );
}
