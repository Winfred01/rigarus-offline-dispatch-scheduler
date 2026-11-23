import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState, type SubmitEvent } from "react";
import { Dialog } from "./dialog";
import { localToday, validLocalDate } from "./assignment-fields";
import { dayNumber, displayDate, shiftDay, weekDays } from "./week";
import {
  availabilityText,
  stateAt,
  type AvailabilityState,
  type AvailabilitySlot,
  type AvailabilitySnapshot,
} from "./availability-fields";
import type { Person, Crew } from "./workspace-data";

type Edit = {
  start_date: string;
  end_date: string;
  slot: AvailabilitySlot;
  state: AvailabilityState;
  expected_revision: number;
};
type Change = {
  id: number;
  revision: number;
  start_date: string;
  end_date: string;
  slot: AvailabilitySlot;
  state: AvailabilityState;
  recorded_at: string;
};

export function AvailabilityCalendar() {
  const [people, setPeople] = useState<Person[]>([]),
    [crews, setCrews] = useState<Crew[]>([]);
  const [selected, setSelected] = useState(0),
    [search, setSearch] = useState("");
  const [day, setDay] = useState(localToday),
    [dateField, setDateField] = useState(day);
  const [snapshot, setSnapshot] = useState<AvailabilitySnapshot>();
  const [editor, setEditor] = useState<Edit>();
  const [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [rosterLoading, setRosterLoading] = useState(true),
    [blocked, setBlocked] = useState(false);
  const [error, setError] = useState(""),
    [rosterError, setRosterError] = useState(""),
    [status, setStatus] = useState("");
  const [retry, setRetry] = useState(0),
    [rosterRetry, setRosterRetry] = useState(0);
  const [history, setHistory] = useState<Change[]>(),
    [historyError, setHistoryError] = useState(""),
    [historyBusy, setHistoryBusy] = useState(false);
  const [historyEmployee, setHistoryEmployee] = useState(0);
  const visibleHistory = historyEmployee === selected ? history : undefined;
  const recordButton = useRef<HTMLButtonElement>(null);
  const restoreFocus = useRef(false);
  const savedFlag = useRef(false),
    selection = useRef(selected),
    alive = useRef(true);
  selection.current = selected;
  const days = weekDays(day),
    validDays = days.filter(validLocalDate),
    start = validDays[0],
    end = validDays[validDays.length - 1];
  const current =
    snapshot?.employee_id === selected &&
    snapshot.start_date === start &&
    snapshot.end_date === end
      ? snapshot
      : undefined;
  const person = people.find((p) => p.id === selected);
  useEffect(() => {
    if (restoreFocus.current && current && !loading) {
      restoreFocus.current = false;
      recordButton.current?.focus();
    }
  }, [current, loading]);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    let active = true;
    setRosterLoading(true);
    setRosterError("");
    void Promise.all([
      invoke<Person[]>("search_employees", { term: "" }),
      invoke<Crew[]>("search_crews", { term: "" }),
    ])
      .then(([p, c]) => {
        if (active) {
          setPeople(p);
          setCrews(c);
          setSelected((id) =>
            p.some((person) => person.id === id) ? id : (p[0]?.id ?? 0),
          );
        }
      })
      .catch((f) => {
        if (active) {
          setPeople([]);
          setCrews([]);
          setSelected(0);
          setRosterError(String(f));
        }
      })
      .finally(() => {
        if (active) setRosterLoading(false);
      });
    return () => {
      active = false;
    };
  }, [rosterRetry]);
  useEffect(() => {
    let active = true;
    setSnapshot(undefined);
    setError("");
    setHistory(undefined);
    setHistoryError("");
    if (!selected) {
      setLoading(false);
      return () => {
        active = false;
      };
    }
    setLoading(true);
    void invoke<AvailabilitySnapshot>("read_availability", {
      employeeId: selected,
      startDate: start,
      endDate: end,
    })
      .then((data) => {
        if (active) {
          setSnapshot(data);
          setBlocked(false);
          if (savedFlag.current) {
            savedFlag.current = false;
            setStatus("Availability saved.");
          }
        }
      })
      .catch((f) => {
        if (active) {
          setSnapshot(undefined);
          setBlocked(true);
          setError(
            (savedFlag.current
              ? "Availability was saved, but the calendar could not reload. "
              : "Could not load availability. ") +
              "Reload availability to retry. " +
              String(f),
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selected, start, end, retry]);
  function navigate(value: string) {
    if (!validLocalDate(value)) {
      setError("Choose a valid local date (YYYY-MM-DD).");
      return;
    }
    savedFlag.current = false;
    restoreFocus.current = false;
    setDay(value);
    setDateField(value);
    setStatus("");
    setError("");
  }
  function begin(date = day, slot: AvailabilitySlot = "FullDay") {
    if (!current || busy || blocked) return;
    setError("");
    setEditor({
      start_date: date,
      end_date: date,
      slot,
      state: slot === "FullDay" ? "Available" : stateAt(current, date, slot),
      expected_revision: current.revision,
    });
  }
  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || busy || blocked) return;
    if (
      !validLocalDate(editor.start_date) ||
      !validLocalDate(editor.end_date) ||
      editor.end_date < editor.start_date
    ) {
      setError("Enter valid inclusive start and end dates.");
      document.getElementById("availability-start")?.focus();
      return;
    }
    if (dayNumber(editor.end_date) - dayNumber(editor.start_date) + 1 > 366) {
      setError("Choose at most 366 dates per save.");
      document.getElementById("availability-end")?.focus();
      return;
    }
    setBusy(true);
    setError("");
    try {
      await invoke<AvailabilitySnapshot>("save_availability", {
        employeeId: selected,
        availability: editor,
      });
    } catch (f) {
      if (alive.current) {
        setError(
          String(f) +
            " Reload availability before retrying; the save outcome may be uncertain.",
        );
        setBlocked(true);
        setBusy(false);
      }
      return;
    }
    if (alive.current) {
      savedFlag.current = true;
      restoreFocus.current = true;
      setStatus("Availability saved. Reloading calendar…");
      setSnapshot(undefined);
      setEditor(undefined);
      setDay(editor.start_date);
      setDateField(editor.start_date);
      setRetry((n) => n + 1);
      setBusy(false);
    }
  }
  async function loadHistory() {
    const id = selected;
    setHistoryEmployee(id);
    setHistoryBusy(true);
    setHistoryError("");
    try {
      const records = await invoke<Change[]>("read_availability_history", {
        employeeId: id,
      });
      if (alive.current && selection.current === id) setHistory(records);
    } catch (f) {
      if (alive.current && selection.current === id) {
        setHistory(undefined);
        setHistoryError(String(f));
      }
    } finally {
      if (alive.current) setHistoryBusy(false);
    }
  }
  const locked = busy || !!editor;
  return (
    <main className="schedule-page project-master availability-page">
      <p className="breadcrumb">People / Availability</p>
      <h1>Employee availability</h1>
      <p>
        Record dates and half-days explicitly. Blank dates are Not recorded,
        including weekends. Availability is not a job assignment, leave approval
        or dispatch clearance.
      </p>
      <div className="week-toolbar">
        <button
          aria-label="Previous availability week"
          disabled={locked || days[0] < "0001-01-08"}
          onClick={() => navigate(shiftDay(day, -7))}
        >
          ‹
        </button>
        <button disabled={locked} onClick={() => navigate(localToday())}>
          Today
        </button>
        <button
          aria-label="Next availability week"
          disabled={locked || days[6] > "9999-12-24"}
          onClick={() => navigate(shiftDay(day, 7))}
        >
          ›
        </button>
        <strong>
          {displayDate(start)} – {displayDate(end)}
        </strong>
        <label className="date-jump">
          Local date
          <input
            id="availability-date"
            value={dateField}
            maxLength={10}
            placeholder="YYYY-MM-DD"
            disabled={locked}
            onChange={(e) => setDateField(e.target.value)}
          />
        </label>
        <button disabled={locked} onClick={() => navigate(dateField)}>
          Go to availability date
        </button>
      </div>
      <div className="search-controls">
        <label>
          Find employee
          <input
            id="availability-employee-search"
            value={search}
            disabled={locked || rosterLoading}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label>
          Employee
          <select
            id="availability-employee"
            value={selected || ""}
            disabled={locked || rosterLoading || !people.length}
            onChange={(e) => {
              savedFlag.current = false;
              restoreFocus.current = false;
              setStatus("");
              setSelected(Number(e.target.value));
            }}
          >
            <option value="" disabled>
              Choose employee
            </option>
            {people
              .filter(
                (p) =>
                  p.id === selected ||
                  `${p.name} ${p.id}`
                    .toLowerCase()
                    .includes(search.toLowerCase()),
              )
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (#{p.id}){p.active ? "" : " · Inactive"}
                </option>
              ))}
          </select>
        </label>
        <button
          id="record-availability"
          ref={recordButton}
          disabled={locked || loading || !current || blocked}
          onClick={() => begin()}
        >
          Record availability
        </button>
        <button
          disabled={busy}
          className="secondary-button"
          onClick={() => {
            setEditor(undefined);
            setRetry((n) => n + 1);
            setRosterRetry((n) => n + 1);
          }}
        >
          Reload availability
        </button>
      </div>
      {!rosterLoading &&
        !!search &&
        !people.some((p) =>
          `${p.name} ${p.id}`.toLowerCase().includes(search.toLowerCase()),
        ) && <p>No matching employees. The current selection is retained.</p>}
      <p role="status" aria-live="polite">
        {rosterLoading
          ? "Loading employees…"
          : loading
            ? "Loading recorded availability…"
            : status}
      </p>
      {rosterError && (
        <p role="alert" className="error">
          Could not load employees. {rosterError}
        </p>
      )}
      {error && !editor && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div
        className="week-scroll"
        role="region"
        aria-label="Employee availability calendar"
        aria-busy={loading || rosterLoading}
        tabIndex={0}
      >
        <table
          className="week-grid availability-grid"
          aria-label="Availability Sunday–Saturday"
        >
          <thead>
            <tr>
              <th scope="col">Employee / Home Crew</th>
              {days.map((date, i) => (
                <th
                  scope="col"
                  key={date}
                  className={i === 0 || i === 6 ? "weekend" : ""}
                >
                  {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][i]}
                  <br />
                  {validLocalDate(date)
                    ? displayDate(date)
                    : "Outside supported dates"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {person && (
              <tr>
                <th scope="row">
                  {person.name}
                  <small>
                    Home Crew:{" "}
                    {crews.find((c) => c.id === person.home_crew_id)?.name ??
                      `#${person.home_crew_id}`}
                  </small>
                  <small>
                    {person.active
                      ? "Active"
                      : "Inactive · availability does not reactivate employee"}
                  </small>
                </th>
                {days.map((date, i) => (
                  <td
                    key={date}
                    className={i === 0 || i === 6 ? "weekend" : ""}
                  >
                    {(["AM", "PM"] as const).map((slot) => {
                      const state = current
                        ? stateAt(current, date, slot)
                        : undefined;
                      return (
                        <button
                          key={slot}
                          id={`availability-cell-${date}-${slot}`}
                          className={`availability-cell ${state?.toLowerCase() ?? "loading"}`}
                          aria-label={`${date} ${slot}: ${state ? availabilityText(state) : "Availability not loaded"}`}
                          disabled={
                            locked ||
                            loading ||
                            blocked ||
                            !current ||
                            !validLocalDate(date)
                          }
                          onClick={() => begin(date, slot)}
                        >
                          <strong>{slot}</strong>
                          <span>
                            {state
                              ? availabilityText(state)
                              : error
                                ? "Could not load"
                                : "Loading…"}
                          </span>
                        </button>
                      );
                    })}
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
        {!rosterLoading && !people.length && !rosterError && (
          <p className="board-empty">
            No employees. Add employee records in People / Employees.
          </p>
        )}
      </div>
      <p className="availability-legend">
        Available · Unavailable · Not recorded. Existing Draft visits and worker
        choices stay unchanged. All Drafts remain Validation pending.
      </p>
      {selected > 0 && (
        <details>
          <summary>Availability change history</summary>
          <p>Latest 100 saved changes; earlier history remains stored.</p>
          <button
            disabled={locked || historyBusy || rosterLoading}
            onClick={() => void loadHistory()}
          >
            {historyBusy ? "Loading history…" : "Load availability history"}
          </button>
          {historyError && historyEmployee === selected && (
            <p className="error" role="alert">
              {historyError}
            </p>
          )}
          {visibleHistory?.length === 0 && (
            <p>No saved availability changes.</p>
          )}
          {visibleHistory?.map((change) => (
            <p key={change.id}>
              Revision {change.revision} · {change.start_date} –{" "}
              {change.end_date} ·{" "}
              {change.slot === "FullDay" ? "Full day" : change.slot} ·{" "}
              {availabilityText(change.state)}
              <br />
              <small>{change.recorded_at}</small>
            </p>
          ))}
        </details>
      )}
      {editor && (
        <Dialog
          title="Record employee availability"
          initialFocus="#availability-start"
          busy={busy}
          onClose={() => {
            setEditor(undefined);
            if (!blocked) setError("");
          }}
        >
          <p>
            {person?.name} · #{selected}. Dates include both endpoints. Saving
            replaces the selected slots only; no assignments or Home Crew
            change.
          </p>
          <form onSubmit={save}>
            <fieldset disabled={busy || blocked} className="availability-form">
              <label>
                Start date (YYYY-MM-DD)
                <input
                  id="availability-start"
                  required
                  maxLength={10}
                  value={editor.start_date}
                  onChange={(e) =>
                    setEditor({ ...editor, start_date: e.target.value })
                  }
                />
              </label>
              <label>
                End date (inclusive)
                <input
                  id="availability-end"
                  required
                  maxLength={10}
                  value={editor.end_date}
                  onChange={(e) =>
                    setEditor({ ...editor, end_date: e.target.value })
                  }
                />
              </label>
              <label>
                Half-day
                <select
                  id="availability-slot"
                  value={editor.slot}
                  onChange={(e) =>
                    setEditor({
                      ...editor,
                      slot: e.target.value as AvailabilitySlot,
                    })
                  }
                >
                  <option value="FullDay">Full day (AM + PM)</option>
                  <option>AM</option>
                  <option>PM</option>
                </select>
              </label>
              <label>
                Recorded state
                <select
                  id="availability-state"
                  value={editor.state}
                  onChange={(e) =>
                    setEditor({
                      ...editor,
                      state: e.target.value as AvailabilityState,
                    })
                  }
                >
                  <option>Available</option>
                  <option>Unavailable</option>
                  <option value="Unknown">
                    Not recorded (clear selected slots)
                  </option>
                </select>
              </label>
            </fieldset>
            <p>
              Maximum 366 dates per save. Not recorded clears the selected slots
              while preserving change history. Available does not grant leave,
              weekend, driver or dispatch approval.
            </p>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            <div className="actions">
              <button disabled={busy || blocked}>Save availability</button>
              <button
                type="button"
                disabled={busy}
                className="secondary-button"
                onClick={() => {
                  setEditor(undefined);
                  if (!blocked) setError("");
                }}
              >
                Cancel availability changes
              </button>
              {blocked && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    setEditor(undefined);
                    setRetry((n) => n + 1);
                  }}
                >
                  Reload and discard availability changes
                </button>
              )}
            </div>
          </form>
        </Dialog>
      )}
    </main>
  );
}
