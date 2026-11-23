import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState } from "react";
import { validLocalDate, type DraftAssignment } from "./assignment-fields";
import {
  availabilityText,
  stateAt,
  type AvailabilitySnapshot,
} from "./availability-fields";
import { employeeVisits } from "./employee-week-data";
import type { Person, Crew } from "./workspace-data";
import { displayDate } from "./week";
import { Dialog } from "./dialog";

type Snapshot = { key: string; rows: DraftAssignment[] };
type Preview = { person: Person; days: string[]; rows: DraftAssignment[] };

export function EmployeeWeek({
  people,
  crews,
  days,
  employeeId,
  onEmployee,
  rosterBusy,
  rosterError,
  onRosterReload,
}: {
  people: Person[];
  crews: Crew[];
  days: string[];
  employeeId: number;
  onEmployee: (id: number) => void;
  rosterBusy: boolean;
  rosterError: boolean;
  onRosterReload: () => void;
}) {
  const [search, setSearch] = useState("");
  const [snapshot, setSnapshot] = useState<Snapshot>();
  const [availability, setAvailability] = useState<{
    key: string;
    data: AvailabilitySnapshot;
  }>();
  const [error, setError] = useState("");
  const [availabilityError, setAvailabilityError] = useState("");
  const [loading, setLoading] = useState(true);
  const [availabilityLoading, setAvailabilityLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [detail, setDetail] = useState<DraftAssignment>();
  const [preview, setPreview] = useState<Preview>();
  const validDays = days.filter(validLocalDate),
    start = validDays[0],
    end = validDays.at(-1)!;
  const person = people.find((p) => p.id === employeeId);
  const key = `${employeeId}/${start}/${end}`;
  const current =
    !rosterBusy && !rosterError && person && snapshot?.key === key
      ? snapshot
      : undefined;
  const recorded =
    !rosterBusy && !rosterError && availability?.key === key
      ? availability.data
      : undefined;
  const rows = current ? employeeVisits(current.rows, employeeId, days) : [];
  useEffect(() => {
    if (!rosterBusy && !rosterError && !people.some((p) => p.id === employeeId))
      onEmployee(people[0]?.id ?? 0);
  }, [people, employeeId, rosterBusy, rosterError, onEmployee]);
  useEffect(() => {
    let active = true;
    setSnapshot(undefined);
    setAvailability(undefined);
    setError("");
    setAvailabilityError("");
    setDetail(undefined);
    setPreview(undefined);
    if (!person || rosterBusy || rosterError) {
      setLoading(false);
      setAvailabilityLoading(false);
      return;
    }
    setLoading(true);
    setAvailabilityLoading(true);
    void invoke<DraftAssignment[]>("list_assignments", {
      query: { employee_id: employeeId, start_date: start, end_date: end },
    })
      .then((result) => {
        if (active) setSnapshot({ key, rows: result });
      })
      .catch((f) => {
        if (active) setError(String(f));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    void invoke<AvailabilitySnapshot>("read_availability", {
      employeeId,
      startDate: start,
      endDate: end,
    })
      .then((data) => {
        if (active) setAvailability({ key, data });
      })
      .catch((f) => {
        if (active) setAvailabilityError(String(f));
      })
      .finally(() => {
        if (active) setAvailabilityLoading(false);
      });
    return () => {
      active = false;
    };
  }, [employeeId, start, end, retry, people, rosterBusy, rosterError]);
  function slotState(date: string, slot: "AM" | "PM") {
    return recorded
      ? availabilityText(stateAt(recorded, date, slot))
      : availabilityError || rosterError
        ? "Could not load availability"
        : "Loading availability…";
  }
  return (
    <section className="employee-week" aria-label="Employee weekly assignments">
      <div className="search-controls">
        <label>
          Find employee
          <input
            id="employee-week-search"
            value={search}
            disabled={rosterBusy}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label>
          Employee
          <select
            id="employee-week-person"
            value={person ? employeeId : ""}
            disabled={rosterBusy || rosterError || !people.length}
            onChange={(e) => onEmployee(Number(e.target.value))}
          >
            <option value="" disabled>
              Choose employee
            </option>
            {people
              .filter(
                (p) =>
                  p.id === employeeId ||
                  `${p.name} ${p.id}`
                    .toLowerCase()
                    .includes(search.toLowerCase()),
              )
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (#{p.id}){!p.active && " · Inactive"}
                </option>
              ))}
          </select>
        </label>
        <button
          id="reload-employee-week"
          disabled={rosterBusy || loading || availabilityLoading}
          onClick={() =>
            rosterError ? onRosterReload() : setRetry((n) => n + 1)
          }
        >
          Reload employee week
        </button>
        <button
          disabled={!current || loading || !!error}
          onClick={() =>
            setPreview(structuredClone({ person: person!, days, rows }))
          }
        >
          Export preview
        </button>
      </div>
      {search &&
        !people.some((p) =>
          `${p.name} ${p.id}`.toLowerCase().includes(search.toLowerCase()),
        ) && <p>No matching employees. Current selection retained.</p>}
      <p role="status">
        {rosterBusy || loading
          ? "Loading employee schedule…"
          : current
            ? `${rows.length} explicit Draft visits this week. Validation pending.`
            : ""}
      </p>
      {error && (
        <p role="alert" className="error">
          Could not load employee assignments. {error} Reload employee week to
          retry.
        </p>
      )}
      {availabilityError && (
        <p role="alert" className="error">
          Could not load recorded availability. {availabilityError} Assignments
          remain separate; reload to retry.
        </p>
      )}
      <div
        className="week-scroll"
        tabIndex={0}
        role="region"
        aria-label="Employee weekly calendar"
        aria-busy={rosterBusy || loading}
      >
        <table
          className="week-grid employee-week-grid"
          aria-label="Employee assignments Sunday–Saturday"
        >
          <thead>
            <tr>
              <th scope="col">Employee / Home Crew</th>
              {days.map((date, i) => (
                <th
                  key={date}
                  scope="col"
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
                    {person.active ? "Active" : "Inactive"} · Driver:{" "}
                    {person.driver_status}
                  </small>
                </th>
                {days.map((date, i) => (
                  <td
                    key={date}
                    className={i === 0 || i === 6 ? "weekend" : ""}
                  >
                    <div className="employee-day" id={`employee-day-${date}`}>
                      {validLocalDate(date) && (
                        <>
                          {!current ? (
                            <p>
                              {error || rosterError
                                ? "Assignments unavailable"
                                : "Loading…"}
                            </p>
                          ) : (
                            <>
                              {!rows.some((row) => row.local_date === date) && (
                                <p className="employee-unscheduled">
                                  Unscheduled
                                </p>
                              )}
                              {rows
                                .filter((row) => row.local_date === date)
                                .map((row) => (
                                  <button
                                    key={row.id}
                                    id={`employee-visit-${row.id}`}
                                    className={`schedule-card ${row.work_type.toLowerCase()}`}
                                    aria-label={`Employee Draft ${row.id}, ${row.job_number}, ${date} ${row.slot}, ${row.crew_name}`}
                                    onClick={() => setDetail(row)}
                                  >
                                    <strong>
                                      {row.slot} · {row.work_type} · Draft
                                    </strong>
                                    <span>
                                      {row.job_number} · Site {row.site_id}
                                    </span>
                                    <span>{row.site_name}</span>
                                    <span>
                                      {row.crew_name}
                                      {row.crew_id !== person.home_crew_id &&
                                        " · Borrowed"}
                                      {!row.crew_active && " · Inactive"}
                                    </span>
                                    <small>
                                      Work Item #{row.work_item_id} · Revision{" "}
                                      {row.revision}
                                    </small>
                                    <small>Actual Rig: Not assigned</small>
                                  </button>
                                ))}
                            </>
                          )}
                          <p
                            className="employee-availability"
                            aria-label={`${date} recorded availability; AM: ${slotState(date, "AM")}; PM: ${slotState(date, "PM")}`}
                          >
                            {(["AM", "PM"] as const).map((slot) => (
                              <span key={slot}>
                                {`${slot}: ${slotState(date, slot)}`}
                              </span>
                            ))}
                          </p>
                        </>
                      )}
                    </div>
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
        {!rosterBusy && !people.length && !rosterError && (
          <p>No employees. Add records in People / Employees.</p>
        )}
      </div>
      {current && !rows.length && (
        <p>No actual assignments for this employee this week.</p>
      )}
      <p>
        Explicit saved workers only; Home Crew is not attendance. Recorded
        availability is not approved leave, weekend consent or dispatch
        clearance. Actual dated Rig is not configured.
      </p>
      {detail && current && (
        <Dialog
          title={`Employee visit · Draft #${detail.id}`}
          onClose={() => setDetail(undefined)}
        >
          <dl className="record-detail">
            <dt>Employee</dt>
            <dd>
              {person?.name} · #{employeeId}
            </dd>
            <dt>Job / Site</dt>
            <dd>
              {detail.job_number} · Site {detail.site_id} · {detail.site_name}
            </dd>
            <dt>Work Item</dt>
            <dd>
              #{detail.work_item_id} · {detail.work_type}
            </dd>
            <dt>Date / slot</dt>
            <dd>
              {detail.local_date} · {detail.slot}
            </dd>
            <dt>Assigned Crew</dt>
            <dd>
              {detail.crew_name} · #{detail.crew_id}
            </dd>
            <dt>Actual Rig</dt>
            <dd>Not assigned; default Rig is reference only.</dd>
            <dt>State</dt>
            <dd>Draft · Validation pending · Revision {detail.revision}</dd>
            <dt>Notes</dt>
            <dd className="preserve-lines">{detail.notes || "—"}</dd>
          </dl>
          <button onClick={() => setDetail(undefined)}>
            Back to employee week
          </button>
        </Dialog>
      )}
      {preview &&
        current &&
        preview.person.id === employeeId &&
        preview.days[0] === days[0] && (
          <Dialog
            title="Employee export preview"
            onClose={() => setPreview(undefined)}
          >
            <h3>
              {preview.person.name} · #{preview.person.id}
            </h3>
            <p>
              {displayDate(preview.days[0])} – {displayDate(preview.days[6])}
            </p>
            <strong>DRAFT – NOT CONFIRMED</strong>
            {preview.rows.length ? (
              <ul>
                {preview.rows.map((row) => (
                  <li key={row.id}>
                    {row.local_date} · {row.slot} · {row.work_type} ·{" "}
                    {row.job_number} · Site {row.site_id} · {row.site_name} ·{" "}
                    {row.crew_name} · Actual Rig: Not assigned · Draft #{row.id}
                    , revision {row.revision}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No actual assignments for this employee this week.</p>
            )}
            <p>
              A validated immutable Published weekly snapshot is required for
              PDF or Excel export. Driver, staffing, resource and leave checks
              remain pending. This read-only preview writes no file and is not a
              confirmed employee schedule.
            </p>
            <div className="actions">
              <button disabled>Export PDF</button>
              <button disabled>Export Excel</button>
              <button onClick={() => setPreview(undefined)}>
                Close preview
              </button>
            </div>
          </Dialog>
        )}
    </section>
  );
}
