import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState } from "react";
import { availabilityText, type SlotAvailability } from "./availability-fields";
import type { DraftAssignment } from "./assignment-fields";
import type { Crew, Person } from "./workspace-data";

export function staffingLabel(row: DraftAssignment): string {
  if (!row.staffing?.configured) return "Actual staffing not assigned";
  if (!row.staffing.workers.length)
    return "No workers selected · Validation pending";
  return row.staffing.workers
    .map(
      (worker) =>
        `${worker.name}${worker.active ? "" : " (inactive)"}${worker.home_crew_id === row.crew_id ? "" : " (borrowed)"}`,
    )
    .join(", ");
}

type Change = {
  id: number;
  assignment_revision: number;
  local_date: string;
  slot: string;
  crew_id: number;
  configured: boolean;
  recorded_at: string;
  members: {
    employee_id: number;
    recorded_name: string;
    recorded_home_crew_id: number;
  }[];
};

export function StaffingPanel({
  row,
  people,
  crews,
  onBusy,
  onSaved,
  onReload,
  requiresReload,
  onUncertain,
}: {
  row: DraftAssignment;
  people: Person[];
  crews: Crew[];
  onBusy: (value: boolean) => void;
  onSaved: () => Promise<void>;
  onReload: () => void;
  requiresReload: boolean;
  onUncertain: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [ids, setIds] = useState<number[]>([]);
  const [term, setTerm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<Change[]>();
  const [historyError, setHistoryError] = useState("");
  const [historyBusy, setHistoryBusy] = useState(false);
  const [availability, setAvailability] = useState<SlotAvailability>();
  const [availabilityError, setAvailabilityError] = useState("");
  const [availabilityRetry, setAvailabilityRetry] = useState(0);
  const [availabilityLoading, setAvailabilityLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setAvailability(undefined);
    setAvailabilityError("");
    setAvailabilityLoading(true);
    void invoke<SlotAvailability>("read_availability_on_slot", {
      localDate: row.local_date,
      slot: row.slot,
    })
      .then((data) => {
        if (active) setAvailability(data);
      })
      .catch((failure) => {
        if (active) setAvailabilityError(String(failure));
      })
      .finally(() => {
        if (active) setAvailabilityLoading(false);
      });
    return () => {
      active = false;
    };
  }, [row.local_date, row.slot, availabilityRetry]);
  const availabilityCurrent =
    availability?.local_date === row.local_date &&
    availability.slot === row.slot
      ? availability
      : undefined;
  function recordedAvailability(employeeId: number) {
    return availabilityLoading
      ? "Loading…"
      : availabilityError || !availabilityCurrent
        ? "Could not read"
        : availabilityText(
            availabilityCurrent.employees.find(
              (e) => e.employee_id === employeeId,
            )?.state ?? "Unknown",
          );
  }
  async function save() {
    if (busy || requiresReload) return;
    setBusy(true);
    onBusy(true);
    setError("");
    try {
      await invoke<DraftAssignment>("save_staffing", {
        id: row.id,
        staffing: { expected_revision: row.revision, employee_ids: ids },
      });
    } catch (failure) {
      setError(String(failure));
      onUncertain();
      setBusy(false);
      onBusy(false);
      return;
    }
    setEditing(false);
    setHistory(undefined);
    try {
      await onSaved();
    } finally {
      setBusy(false);
      onBusy(false);
    }
  }
  async function readHistory() {
    setHistoryBusy(true);
    setHistoryError("");
    try {
      setHistory(
        await invoke<Change[]>("read_staffing_history", { id: row.id }),
      );
    } catch (failure) {
      setHistory(undefined);
      setHistoryError(String(failure));
    } finally {
      setHistoryBusy(false);
    }
  }
  return (
    <section
      className="staffing-panel"
      aria-labelledby="staffing-title"
      aria-busy={busy}
    >
      <h3 id="staffing-title">Draft workers</h3>
      <p>{staffingLabel(row)}</p>
      <p className="staffing-warning">
        Explicit choice for this visit only; Home Crew stays unchanged. Time
        off, double booking, driver and qualification checks are pending. This
        is not confirmed attendance or dispatch approval.
      </p>
      <p>
        Recorded availability for {row.local_date} {row.slot} is advisory only.
        Available does not approve dispatch; Unavailable or Not recorded never
        silently removes a Draft worker.
      </p>
      <button
        type="button"
        className="secondary-button"
        disabled={busy || availabilityLoading}
        onClick={() => setAvailabilityRetry((n) => n + 1)}
      >
        Reload worker availability
      </button>
      {availabilityError && (
        <p className="error" role="alert">
          Could not read availability. {availabilityError}
        </p>
      )}
      {!editing ? (
        <button
          type="button"
          disabled={requiresReload}
          onClick={() => {
            setIds(row.staffing?.workers.map((w) => w.employee_id) ?? []);
            setEditing(true);
            setError("");
          }}
        >
          Choose workers
        </button>
      ) : (
        <>
          <label>
            Find employee
            <input
              id="staffing-search"
              value={term}
              disabled={busy}
              onChange={(e) => setTerm(e.target.value)}
              autoFocus
            />
          </label>
          <p>
            {ids.length} workers selected for {row.local_date} {row.slot}. An
            empty selection does not establish safe staffing.
          </p>
          <fieldset
            disabled={busy || requiresReload}
            className="staffing-options"
          >
            <legend>Employees for Draft #{row.id}</legend>
            {people
              .filter((p) =>
                `${p.name} ${p.id} ${crews.find((c) => c.id === p.home_crew_id)?.name ?? ""}`
                  .toLowerCase()
                  .includes(term.toLowerCase()),
              )
              .map((person) => (
                <label key={person.id} className="staffing-option">
                  <input
                    type="checkbox"
                    checked={ids.includes(person.id)}
                    onChange={(e) =>
                      setIds(
                        e.target.checked
                          ? [...ids, person.id]
                          : ids.filter((id) => id !== person.id),
                      )
                    }
                    aria-label={`Select worker ${person.id}, ${person.name}`}
                  />
                  <span>
                    <strong>
                      {person.name} · #{person.id}
                    </strong>
                    <small>
                      Home Crew:{" "}
                      {crews.find((c) => c.id === person.home_crew_id)?.name ??
                        `#${person.home_crew_id}`}
                      {person.home_crew_id !== row.crew_id &&
                        " · Borrowed for this visit"}
                      {!person.active && " · Inactive; validation pending"} ·
                      Driver: {person.driver_status}
                      <span className="worker-availability">{`Availability: ${recordedAvailability(person.id)}`}</span>
                    </small>
                  </span>
                </label>
              ))}
            {!people.length && (
              <p>
                No employees. Add employee records in People before selecting
                workers.
              </p>
            )}
            {!!people.length &&
              !people.some((p) =>
                `${p.name} ${p.id} ${crews.find((c) => c.id === p.home_crew_id)?.name ?? ""}`
                  .toLowerCase()
                  .includes(term.toLowerCase()),
              ) && <p>No matching employees. Other selections are retained.</p>}
          </fieldset>
          {error && (
            <p role="alert" className="error">
              {error} Reload before retrying; the outcome may be uncertain.
            </p>
          )}
          <div className="actions">
            <button
              type="button"
              disabled={busy || requiresReload}
              onClick={() => void save()}
            >
              Save workers to Draft
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={() => setEditing(false)}
            >
              Cancel worker changes
            </button>
            {requiresReload && (
              <button type="button" disabled={busy} onClick={onReload}>
                Reload and discard worker changes
              </button>
            )}
          </div>
        </>
      )}
      <details>
        <summary>Staffing change history</summary>
        <button
          type="button"
          disabled={historyBusy || busy}
          onClick={() => void readHistory()}
        >
          {historyBusy ? "Loading history…" : "Load staffing history"}
        </button>
        {historyError && (
          <p role="alert" className="error">
            {historyError}
          </p>
        )}
        {history?.length === 0 && <p>No saved staffing changes.</p>}
        {history?.map((change) => (
          <div key={change.id} className="staffing-change">
            Change #{change.id} · Revision {change.assignment_revision} ·{" "}
            {change.local_date} {change.slot} · Crew #{change.crew_id}
            <br />
            {change.configured
              ? change.members
                  .map(
                    (m) =>
                      `${m.recorded_name} (#${m.employee_id}, Home Crew #${m.recorded_home_crew_id})`,
                  )
                  .join(", ") || "No workers selected"
              : "Visit changed: reconfirm workers"}
            <br />
            <small>{change.recorded_at}</small>
          </div>
        ))}
      </details>
    </section>
  );
}
