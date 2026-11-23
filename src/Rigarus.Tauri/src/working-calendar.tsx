import { invoke } from "@tauri-apps/api/core";
import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type SubmitEvent,
} from "react";
import { Dialog } from "./dialog";
import { localToday, validLocalDate } from "./assignment-fields";
import { dayNumber, displayDate, shiftDay, weekDays } from "./week";
import {
  calendarMessage,
  workingText,
  type CalendarAssessment,
  type CalendarScope,
  type CalendarSnapshot,
  type WorkingState,
} from "./working-calendar-fields";
import type { Crew, Project } from "./workspace-data";

type Edit = {
  start_date: string;
  end_date: string;
  slot: "FullDay" | "AM" | "PM";
  state: WorkingState;
  expected_revision: number;
};
type Change = Edit & { id: number; revision: number; recorded_at: string };

export function CalendarFeedback({
  value,
}: {
  value?: CalendarAssessment | null;
}) {
  return (
    <section
      className="calendar-feedback"
      aria-label="Working calendar assessment"
    >
      <p>
        {value
          ? calendarMessage(value)
          : "Calendar assessment not loaded. Reload the Draft before relying on its calendar state."}
      </p>
      {value?.reasons.some((r) => r.code === "WEEKEND_APPROVAL_PENDING") && (
        <p>Weekend consent: pending.</p>
      )}
      <p>
        Draft / Validation pending. Personnel conflicts, driver qualifications
        and actual Rig availability require separate checks. Calendar feedback
        does not prevent saving a Draft.
      </p>
    </section>
  );
}

export function DraftCalendarPreview({
  workItemId,
  crewId,
  day,
  slot,
}: {
  workItemId: number;
  crewId: number;
  day: string;
  slot: "AM" | "PM";
}) {
  const [result, setResult] = useState<{
    key: string;
    value: CalendarAssessment;
  }>();
  const [failure, setFailure] = useState<{ key: string; message: string }>();
  const [attempt, setAttempt] = useState(0);
  const key = `${workItemId}:${crewId}:${day}:${slot}`;
  const ready = workItemId > 0 && crewId > 0 && validLocalDate(day);
  useEffect(() => {
    let active = true;
    setResult(undefined);
    setFailure(undefined);
    if (ready)
      void invoke<CalendarAssessment>("read_calendar_assessment", {
        workItemId,
        crewId,
        localDate: day,
        slot,
      })
        .then((value) => {
          if (active) setResult({ key, value });
        })
        .catch((error) => {
          if (active) setFailure({ key, message: String(error) });
        });
    return () => {
      active = false;
    };
  }, [workItemId, crewId, day, slot, key, ready, attempt]);
  if (!ready)
    return (
      <p>
        Select a WorkItem, Crew and valid local date to check working calendars.
      </p>
    );
  if (failure?.key === key)
    return (
      <p role="alert" className="error">
        Calendar check unavailable. {failure.message}{" "}
        <button type="button" onClick={() => setAttempt(attempt + 1)}>
          Retry calendar check
        </button>{" "}
        Drafts remain validation pending.
      </p>
    );
  if (result?.key !== key)
    return <p role="status">Checking working calendars…</p>;
  return <CalendarFeedback value={result.value} />;
}

export function WorkingCalendar({ navigation }: { navigation: ReactNode }) {
  const [crews, setCrews] = useState<Crew[]>([]),
    [projects, setProjects] = useState<Project[]>([]);
  const [scope, setScope] = useState<CalendarScope>("Crew"),
    [id, setId] = useState(0);
  const [day, setDay] = useState(localToday),
    [jump, setJump] = useState(day);
  const [rosterError, setRosterError] = useState(""),
    [rosterLoading, setRosterLoading] = useState(true),
    [rosterAttempt, setRosterAttempt] = useState(0);
  const [snapshot, setSnapshot] = useState<CalendarSnapshot>(),
    [loading, setLoading] = useState(false),
    [attempt, setAttempt] = useState(0);
  const [error, setError] = useState(""),
    [status, setStatus] = useState(""),
    [blocked, setBlocked] = useState(false);
  const [editor, setEditor] = useState<Edit>(),
    [busy, setBusy] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false),
    [history, setHistory] = useState<Change[]>(),
    [historyError, setHistoryError] = useState(""),
    [historyAttempt, setHistoryAttempt] = useState(0);
  const alive = useRef(true),
    saving = useRef(false),
    saved = useRef(false);
  const recordButton = useRef<HTMLButtonElement>(null),
    restore = useRef(false);
  const days = weekDays(day),
    validDays = days.filter(validLocalDate),
    start = validDays[0],
    end = validDays[validDays.length - 1];
  const selected = useRef(`${scope}:${id}`);
  selected.current = `${scope}:${id}`;
  const current =
    snapshot?.scope === scope &&
    snapshot.entity_id === id &&
    snapshot.start_date === start &&
    snapshot.end_date === end
      ? snapshot
      : undefined;
  const options =
    scope === "Crew"
      ? crews.map((c) => ({
          id: c.id,
          label: `${c.name} (#${c.id})${c.active ? "" : " · Inactive"}`,
        }))
      : projects.map((p) => ({
          id: p.id,
          label: `${p.job_number} · ${p.site_name} (#${p.id})`,
        }));
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
      invoke<Crew[]>("search_crews", { term: "" }),
      invoke<Project[]>("search_projects", { term: "" }),
    ])
      .then(([c, p]) => {
        if (active) {
          setCrews(c);
          setProjects(p);
        }
      })
      .catch((e) => {
        if (active) {
          setCrews([]);
          setProjects([]);
          setRosterError(String(e));
        }
      })
      .finally(() => {
        if (active) setRosterLoading(false);
      });
    return () => {
      active = false;
    };
  }, [rosterAttempt]);
  useEffect(() => {
    let active = true;
    setSnapshot(undefined);
    setError("");
    setStatus("");
    setLoading(!!id);
    if (id)
      void invoke<CalendarSnapshot>("read_working_calendar", {
        scope,
        entityId: id,
        startDate: start,
        endDate: end,
      })
        .then((s) => {
          if (active) {
            setSnapshot(s);
            setBlocked(false);
            if (saved.current) {
              saved.current = false;
              setStatus("Working calendar saved.");
            }
          }
        })
        .catch((e) => {
          if (active)
            setError(
              `${saved.current ? "Calendar was saved, but the week could not reload. " : "Could not load working calendar. "}${String(e)}`,
            );
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    return () => {
      active = false;
    };
  }, [scope, id, start, end, attempt]);
  useEffect(() => {
    if (restore.current && current && !loading) {
      restore.current = false;
      recordButton.current?.focus();
    }
  }, [current, loading]);
  useEffect(() => {
    let active = true;
    setHistory(undefined);
    setHistoryError("");
    if (historyOpen && id)
      void invoke<Change[]>("read_working_calendar_history", {
        scope,
        entityId: id,
      })
        .then((h) => {
          if (active) setHistory(h);
        })
        .catch((e) => {
          if (active) setHistoryError(String(e));
        });
    return () => {
      active = false;
    };
  }, [historyOpen, scope, id, historyAttempt]);
  function edit(date = day, slot: Edit["slot"] = "FullDay") {
    if (!current || blocked || busy) return;
    setEditor({
      start_date: date,
      end_date: date,
      slot,
      state: "Working",
      expected_revision: current.revision,
    });
    setError("");
  }
  function close() {
    if (!saving.current) {
      setEditor(undefined);
      restore.current = true;
    }
  }
  function reload() {
    if (saving.current) return;
    setEditor(undefined);
    restore.current = true;
    setSnapshot(undefined);
    setAttempt((v) => v + 1);
  }
  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || !current || blocked || saving.current) return;
    if (
      !validLocalDate(editor.start_date) ||
      !validLocalDate(editor.end_date) ||
      dayNumber(editor.end_date) < dayNumber(editor.start_date) ||
      dayNumber(editor.end_date) - dayNumber(editor.start_date) >= 366
    ) {
      setError("Choose an ordered range of at most 366 local dates.");
      return;
    }
    saving.current = true;
    setBusy(true);
    setError("");
    const owner = selected.current;
    try {
      await invoke("save_working_calendar", {
        scope,
        entityId: id,
        calendar: editor,
      });
      if (alive.current && selected.current === owner) {
        saved.current = true;
        setEditor(undefined);
        setSnapshot(undefined);
        restore.current = true;
        setAttempt((v) => v + 1);
      }
    } catch (e) {
      if (alive.current && selected.current === owner) {
        setBlocked(true);
        setError(
          `Save could not be confirmed. Reload before retrying. ${String(e)}`,
        );
      }
    } finally {
      saving.current = false;
      if (alive.current) setBusy(false);
    }
  }
  function move(offset: number) {
    const next = shiftDay(day, offset);
    if (validLocalDate(next)) {
      setDay(next);
      setJump(next);
    }
  }
  return (
    <main className="schedule-page project-master working-calendar-page">
      <p className="breadcrumb">Schedule / Working calendars</p>
      <h1>Working calendars</h1>
      {navigation}
      <p>
        Record when a Crew or Project can work. Every WorkItem inherits its
        Project calendar. Blank dates stay Not recorded, including weekends and
        holidays.
      </p>
      <div className="week-toolbar">
        <label>
          Calendar scope
          <select
            id="working-scope"
            value={scope}
            disabled={busy}
            onChange={(e) => {
              setScope(e.target.value as CalendarScope);
              setId(0);
              setBlocked(false);
              saved.current = false;
            }}
          >
            <option>Crew</option>
            <option>Project</option>
          </select>
        </label>
        <label>
          {scope}
          <select
            id="working-owner"
            value={id || ""}
            disabled={rosterLoading || !!rosterError || busy}
            onChange={(e) => {
              setId(Number(e.target.value));
              setBlocked(false);
              saved.current = false;
            }}
          >
            <option value="">Select a {scope}</option>
            {options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={() => move(-7)}
          disabled={!validLocalDate(shiftDay(day, -7))}
        >
          Previous week
        </button>
        <button
          onClick={() => {
            setDay(localToday());
            setJump(localToday());
          }}
        >
          Today
        </button>
        <button
          onClick={() => move(7)}
          disabled={!validLocalDate(shiftDay(day, 7))}
        >
          Next week
        </button>
        <label>
          Jump to local date
          <input
            id="working-date"
            value={jump}
            onChange={(e) => setJump(e.target.value)}
          />
        </label>
        <button disabled={!validLocalDate(jump)} onClick={() => setDay(jump)}>
          Go to date
        </button>
      </div>
      {rosterLoading && <p role="status">Loading Crews and Projects…</p>}
      {rosterError && (
        <p role="alert" className="error">
          Could not load calendar owners. {rosterError}{" "}
          <button onClick={() => setRosterAttempt((v) => v + 1)}>
            Retry owners
          </button>
        </p>
      )}
      {!rosterLoading && !rosterError && !options.length && (
        <p>
          No {scope === "Crew" ? "Crews" : "Projects"} yet. Create one before
          recording its calendar.
        </p>
      )}
      <div className="board-actions">
        <button
          ref={recordButton}
          disabled={!current || blocked || busy || loading}
          onClick={() => edit()}
        >
          Record working dates
        </button>
        <button disabled={!id || busy} onClick={() => setHistoryOpen(true)}>
          Calendar change history
        </button>
        <button disabled={!id || busy} onClick={reload}>
          Reload calendar
        </button>
      </div>
      {loading && <p role="status">Loading working calendar…</p>}
      {status && <p role="status">{status}</p>}
      {!editor && error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {id && current ? (
        <>
          <p>
            {options.find((o) => o.id === id)?.label} · {displayDate(start)}–
            {displayDate(end)} · Revision {current.revision}
          </p>
          <div
            className="week-scroll"
            tabIndex={0}
            aria-label="Working calendar scroll area"
          >
            <table
              className="week-grid availability-grid"
              aria-label="Working calendar"
            >
              <thead>
                <tr>
                  <th scope="col">Half-day</th>
                  {days.map((d, i) => (
                    <th
                      key={d}
                      scope="col"
                      className={i === 0 || i === 6 ? "weekend" : ""}
                    >
                      {validLocalDate(d)
                        ? displayDate(d)
                        : "Outside supported dates"}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(["AM", "PM"] as const).map((slot) => (
                  <tr key={slot}>
                    <th scope="row">{slot}</th>
                    {days.map((d, i) => {
                      const state =
                        current.entries.find(
                          (e) => e.local_date === d && e.slot === slot,
                        )?.state ?? "Unknown";
                      return (
                        <td
                          key={d}
                          className={i === 0 || i === 6 ? "weekend" : ""}
                        >
                          <button
                            id={`working-cell-${d}-${slot}`}
                            disabled={!validLocalDate(d) || blocked || busy}
                            className={`working-cell working-${state}`}
                            aria-label={`${d} ${slot}: ${workingText(state)}`}
                            onClick={() => edit(d, slot)}
                          >
                            {workingText(state)}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        !loading &&
        !error && <p>Select a Crew or Project to view its working dates.</p>
      )}
      <p className="draft-notice">
        Calendar match is not dispatch approval. Drafts can retain calendar
        conflicts. Driver, personnel, Rig and weekend-consent checks remain
        separate; Publish is unavailable.
      </p>
      {editor && (
        <Dialog
          title="Record working dates"
          busy={busy}
          onClose={close}
          initialFocus="#working-start"
        >
          <form className="project-editor" onSubmit={save}>
            <fieldset disabled={busy || blocked}>
              <p>
                {scope} calendar · {options.find((o) => o.id === id)?.label}
                {scope === "Project" ? " · Shared by all WorkItems" : ""}
              </p>
              <div className="project-fields">
                <label>
                  Start date (inclusive)
                  <input
                    id="working-start"
                    required
                    value={editor.start_date}
                    onChange={(e) =>
                      setEditor({ ...editor, start_date: e.target.value })
                    }
                  />
                </label>
                <label>
                  End date (inclusive)
                  <input
                    id="working-end"
                    required
                    value={editor.end_date}
                    onChange={(e) =>
                      setEditor({ ...editor, end_date: e.target.value })
                    }
                  />
                </label>
                <label>
                  Half-day
                  <select
                    id="working-slot"
                    value={editor.slot}
                    onChange={(e) =>
                      setEditor({
                        ...editor,
                        slot: e.target.value as Edit["slot"],
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
                    id="working-state"
                    value={editor.state}
                    onChange={(e) =>
                      setEditor({
                        ...editor,
                        state: e.target.value as WorkingState,
                      })
                    }
                  >
                    <option value="Working">Can work</option>
                    <option value="NotWorking">Cannot work</option>
                    <option value="Unknown">Not recorded (clear)</option>
                  </select>
                </label>
              </div>
              <p>
                Save explicitly replaces the selected slots only. Clearing keeps
                change history. Existing Drafts keep their dates and IDs; reopen
                them to read current calendar feedback.
              </p>
            </fieldset>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <div className="actions">
              <button disabled={busy || blocked}>
                {busy ? "Saving…" : "Save working dates"}
              </button>
              <button type="button" disabled={busy} onClick={close}>
                Cancel
              </button>
              {blocked && (
                <button type="button" disabled={busy} onClick={reload}>
                  Reload and discard changes
                </button>
              )}
            </div>
          </form>
        </Dialog>
      )}
      {historyOpen && (
        <Dialog
          title="Working calendar history"
          onClose={() => setHistoryOpen(false)}
        >
          <p>
            {scope} #{id}; latest 100 changes, older history retained.
          </p>
          {historyError ? (
            <p role="alert" className="error">
              {historyError}{" "}
              <button onClick={() => setHistoryAttempt((v) => v + 1)}>
                Retry history
              </button>
            </p>
          ) : !history ? (
            <p role="status">Loading calendar history…</p>
          ) : !history.length ? (
            <p>No calendar changes recorded.</p>
          ) : (
            <ol>
              {history.map((h) => (
                <li key={h.id}>
                  Revision {h.revision}: {h.start_date}–{h.end_date} · {h.slot}{" "}
                  · {workingText(h.state)} · {h.recorded_at}
                </li>
              ))}
            </ol>
          )}
        </Dialog>
      )}
    </main>
  );
}
