import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState, type SubmitEvent } from "react";

type Employee = {
  id: number;
  name: string;
  home_crew_id: number;
  active: boolean;
  foreman_eligible: boolean;
};
type ForemanState = {
  crew_id: number;
  revision: number;
  employee_id: number | null;
  employee_name: string | null;
  employee_active: boolean | null;
  employee_eligible: boolean | null;
  history: {
    id: number;
    employee_id: number | null;
    crew_name: string;
    employee_name: string | null;
    recorded_at: string;
  }[];
};

export function ForemanEditor({
  crew,
  crews,
  onClose,
}: {
  crew: { id: number; name: string };
  crews: { id: number; name: string }[];
  onClose: () => void;
}) {
  const [state, setState] = useState<ForemanState>();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(true);
  const [needsReload, setNeedsReload] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [pending, setPending] = useState("Loading Foreman…");
  const heading = useRef<HTMLHeadingElement>(null);

  async function load() {
    setPending("Loading Foreman…");
    setBusy(true);
    setError("");
    setStatus("");
    try {
      const [record, roster] = await Promise.all([
        invoke<ForemanState>("read_foreman", { crewId: crew.id }),
        invoke<Employee[]>("search_employees", { term: "" }),
      ]);
      setState(record);
      setEmployees(roster);
      setSelected(record.employee_id?.toString() ?? "");
      setNeedsReload(false);
    } catch (failure) {
      setError(String(failure));
      setNeedsReload(true);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    heading.current?.focus();
    void load();
  }, [crew.id]);

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!state || busy || needsReload) return;
    setPending("Saving Foreman…");
    setBusy(true);
    setError("");
    setStatus("");
    try {
      const record = await invoke<ForemanState>("save_foreman", {
        crewId: crew.id,
        change: {
          employee_id: selected ? Number(selected) : null,
          expected_revision: state.revision,
        },
      });
      setState(record);
      setSelected(record.employee_id?.toString() ?? "");
      setStatus("Foreman saved.");
    } catch (failure) {
      setError(String(failure));
      // A lost response may have committed. Read the authoritative record first.
      setNeedsReload(true);
    } finally {
      setBusy(false);
    }
  }

  const eligible = employees.filter(
    (item) => item.active && item.foreman_eligible,
  );
  const retained =
    state?.employee_id != null &&
    !eligible.some((item) => item.id === state.employee_id);
  const unchanged =
    !!state && selected === (state.employee_id?.toString() ?? "");
  const currentLabel = state
    ? `Current Foreman: ${state.employee_id === null ? "Unassigned" : `${state.employee_name} (#${state.employee_id})`}${state.employee_active === false ? " · Inactive" : ""}${state.employee_eligible === false ? " · No longer marked Foreman eligible" : ""}`
    : "";

  return (
    <section aria-labelledby="foreman-title" className="foreman-editor">
      <h2 id="foreman-title" ref={heading} tabIndex={-1}>
        Foreman — {crew.name}
      </h2>
      <p>
        Changing Foreman leaves the employee’s Home Crew unchanged. This record
        does not approve dispatch.
      </p>
      <p role="status">{busy ? pending : status}</p>
      {error && (
        <p role="alert" className="error">
          {error} Reload discards the unsaved selection.
        </p>
      )}
      {state && (
        <>
          <p id="foreman-current" role="status" aria-label={currentLabel}>
            {currentLabel}
          </p>
          <form onSubmit={save} className="project-editor">
            <fieldset disabled={busy || needsReload}>
              <label htmlFor="foreman-employee">Foreman</label>
              <select
                id="foreman-employee"
                value={selected}
                aria-describedby="foreman-current foreman-choice-help"
                onChange={(event) => {
                  setSelected(event.target.value);
                  setStatus("");
                }}
              >
                <option value="">Unassigned (clear appointment)</option>
                {retained && (
                  <option value={state.employee_id!.toString()} disabled>
                    {state.employee_name} (current; inactive or ineligible)
                  </option>
                )}
                {eligible.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name} (#{employee.id}) — Home:{" "}
                    {crews.find((item) => item.id === employee.home_crew_id)
                      ?.name ?? `Crew #${employee.home_crew_id}`}
                  </option>
                ))}
              </select>
              <p id="foreman-choice-help">
                Choose an active employee marked Foreman eligible, or
                Unassigned. Saving adds a history entry; it does not change
                earlier entries.
              </p>
              {!eligible.length && (
                <p>
                  No active employees are marked Foreman eligible. Update
                  Employees to add a candidate.
                </p>
              )}
              <button disabled={unchanged}>Save Foreman</button>
            </fieldset>
          </form>
        </>
      )}
      <div className="actions">
        <button type="button" disabled={busy} onClick={() => void load()}>
          Reload Foreman
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={busy}
          onClick={onClose}
        >
          Back to Crews
        </button>
      </div>
      {state && (
        <section aria-labelledby="foreman-history-title">
          <h3 id="foreman-history-title">Foreman history</h3>
          <p>
            Newest first. Names are retained as recorded at the change; times
            are UTC.
          </p>
          {state.history.length ? (
            <div className="project-table">
              <table aria-label="Foreman change records">
                <thead>
                  <tr>
                    <th scope="col">Recorded at (UTC)</th>
                    <th scope="col">Crew at change</th>
                    <th scope="col">Foreman at change</th>
                  </tr>
                </thead>
                <tbody>
                  {state.history.map((change) => (
                    <tr key={change.id}>
                      <td>
                        <time dateTime={change.recorded_at}>
                          {change.recorded_at}
                        </time>
                      </td>
                      <td>{change.crew_name}</td>
                      <td>
                        {change.employee_id === null
                          ? "Unassigned"
                          : `${change.employee_name} (#${change.employee_id})`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No Foreman changes yet.</p>
          )}
        </section>
      )}
    </section>
  );
}
