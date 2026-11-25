import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState } from "react";
import { Dialog } from "./dialog";
import { validLocalDate } from "./assignment-fields";
import { reasonLabel } from "./day-preview-state";
import {
  readJournal,
  remember,
  sendRemembered,
  settle,
  refreshCommitted,
  editorDeadline,
  type DraftRecord,
  type EditorRequest,
  type EditorResult,
} from "./day-editor-state";
type Work = {
  id: number;
  project_id: number;
  job_number: string;
  type: string;
};
type Person = {
  id: number;
  name: string;
  home_crew_id: number;
  active: boolean;
};
type History = {
  revision: number;
  local_date: string;
  crew_id: number;
  notes: string;
  status: string;
  staffing_configured: boolean;
  workers: [number, string, number][];
}[];
const call = <T,>(action: string, input: object = {}) =>
  editorDeadline(invoke<T>("day_editor", { action, input }));

export function DayEditor({
  id,
  day,
  works,
  crews,
  people,
  onClose,
  onSaved,
}: {
  id?: number;
  day: string;
  works: Work[];
  crews: { id: number; name: string; active: boolean }[];
  people: Person[];
  onClose: () => void;
  onSaved: (row: DraftRecord) => Promise<boolean>;
}) {
  const [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false);
  const lock = useRef(false),
    alive = useRef(true);
  const [profile, setProfile] = useState(""),
    [enabled, setEnabled] = useState(false);
  const [base, setBase] = useState<DraftRecord>(),
    [history, setHistory] = useState<History>();
  const [savedId, setSavedId] = useState("");
  const [work, setWork] = useState(""),
    [crew, setCrew] = useState(""),
    [date, setDate] = useState(day),
    [notes, setNotes] = useState("");
  const [configured, setConfigured] = useState(false),
    [members, setMembers] = useState<number[]>([]),
    [confirmed, setConfirmed] = useState(false);
  const [cancelConfirmed, setCancelConfirmed] = useState(false),
    [broken, setBroken] = useState(false);
  const [pending, setPending] = useState<EditorRequest>(),
    [result, setResult] = useState<EditorResult>();
  const [message, setMessage] = useState(""),
    [refreshed, setRefreshed] = useState(false);
  function fields(r: DraftRecord) {
    setBase(r);
    setWork(String(r.work_item_id));
    setCrew(String(r.crew_id));
    setDate(r.local_date);
    setNotes(r.notes);
    setConfigured(r.employee_ids !== null);
    setMembers(r.employee_ids ?? []);
    setConfirmed(r.employee_ids !== null);
    setCancelConfirmed(false);
  }
  useEffect(() => {
    alive.current = true;
    void (async () => {
      try {
        const status = await call<{
          profile_id: string;
          test_writes_enabled: boolean;
          production_writes_enabled: false;
        }>("status");
        if (!alive.current) return;
        setProfile(status.profile_id);
        setEnabled(
          status.test_writes_enabled === true &&
            status.production_writes_enabled === false,
        );
        const saved = readJournal(localStorage, status.profile_id);
        if (saved) {
          setPending(saved);
          setMessage(
            "An earlier request needs reconciliation. Resolve it before any new Save. No request was retried.",
          );
        } else if (id) {
          const row = await call<DraftRecord>("read", { id });
          if (alive.current) fields(row);
        }
      } catch {
        if (alive.current) {
          setBroken(true);
          setMessage(
            "Unable to load the editor or its recovery journal. No save is allowed. Reopen or investigate local storage; do not clear an unresolved request.",
          );
        }
      } finally {
        if (alive.current) setLoading(false);
      }
    })();
    return () => {
      alive.current = false;
    };
  }, []);
  const committed = result?.outcome === "Committed";
  const frozen =
    loading ||
    busy ||
    !!pending ||
    committed ||
    broken ||
    base?.status === "Cancelled";
  function changed(context = false) {
    if (context) setConfirmed(false);
    setResult(undefined);
    setMessage(
      "Unsaved changes. Safety observations will be re-read under the Save transaction.",
    );
  }
  async function refresh(value: EditorResult) {
    if (!value.record) return;
    try {
      const ok = await refreshCommitted(value, onSaved);
      if (alive.current) {
        setRefreshed(ok);
        setMessage(
          ok
            ? "Saved receipt confirmed. Both weekly views now use refreshed persisted data."
            : "Saved successfully, but weekly refresh failed. Do not Save again. Retry refresh or use the typed saved ID after reopening.",
        );
      }
    } catch {
      if (alive.current) {
        setRefreshed(false);
        setMessage(
          "Saved successfully; refresh failed. Retry refresh only, not Save.",
        );
      }
    }
  }
  async function accept(request: EditorRequest, value: EditorResult) {
    const resolved = settle(localStorage, request, value);
    if (!alive.current) return;
    setResult(value);
    if (!resolved) {
      setMessage(
        value.outcome === "NotFound"
          ? "No committed receipt was observed. The earlier request could still complete. Resolve again or explicitly retry the SAME unchanged request; never create a replacement."
          : "Request identity/profile conflict. Keep the original recovery journal and investigate; no replacement request is allowed.",
      );
      return;
    }
    setPending(undefined);
    if (value.outcome === "Committed") {
      if (value.record) fields(value.record);
      await refresh(value);
    } else
      setMessage(
        value.message ??
          "Draft rejected. Your unsaved fields remain; reload current saved values before resolving a stale revision.",
      );
  }
  async function action(mode: "Save" | "Cancel" | "Resolve" | "Retry") {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    let request = pending;
    try {
      if (mode === "Resolve") {
        if (!request) return;
        const value = await call<EditorResult>("receipt", {
          profile_id: request.profile_id,
          request_id: request.request_id,
        });
        await accept(request, value);
        return;
      }
      if (!enabled || broken) return;
      if (mode === "Retry") {
        if (!request) return;
      } else {
        if (request) return;
        if (mode === "Cancel") {
          if (!base || !cancelConfirmed) return;
          request = {
            profile_id: profile,
            request_id: crypto.randomUUID(),
            action: "Cancel",
            id: base.id,
            expected_revision: base.revision,
          };
        } else {
          const selected = works.find((w) => w.id === Number(work));
          if (
            !selected ||
            !crews.some((c) => c.id === Number(crew)) ||
            !validLocalDate(date) ||
            Array.from(notes).length > 2000 ||
            notes.includes("\0") ||
            members.length > 1000 ||
            (configured && !confirmed)
          ) {
            setMessage(
              "Choose a saved WorkItem and Crew, a valid local date, notes up to 2000 characters, and explicitly confirm any recorded employee list.",
            );
            return;
          }
          request = {
            profile_id: profile,
            request_id: crypto.randomUUID(),
            action: base ? "Edit" : "Create",
            ...(base ? { id: base.id, expected_revision: base.revision } : {}),
            work_item_id: selected.id,
            expected_project_id: selected.project_id,
            crew_id: Number(crew),
            local_date: date,
            notes,
            employee_ids: configured
              ? [...members].sort((a, b) => a - b)
              : null,
            staffing_confirmed: configured && confirmed,
          };
        }
        remember(localStorage, request);
        setPending(request);
      }
      const value = await sendRemembered(localStorage, request, (a, input) =>
        call<EditorResult>(a, input),
      );
      await accept(request, value);
    } catch {
      if (alive.current) {
        if (request && readSafely(profile)) {
          setPending(request);
          setMessage(
            "Save result is UNKNOWN. Keep the original request. Resolve its receipt before any other save; retry may only use the same unchanged request.",
          );
        } else {
          setBroken(true);
          setMessage(
            "The recovery journal could not be retained or read. No further Save is allowed; investigate local storage before proceeding.",
          );
        }
      }
    } finally {
      lock.current = false;
      if (alive.current) setBusy(false);
    }
  }
  function readSafely(p: string) {
    try {
      return !!readJournal(localStorage, p);
    } catch {
      return false;
    }
  }
  async function reload() {
    if (!base || pending || lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      fields(await call<DraftRecord>("read", { id: base.id }));
      setResult(undefined);
      setMessage(
        "Current saved values loaded. Review them before making a new edit.",
      );
    } catch {
      setMessage(
        "Current Draft could not be read. Unsaved values retained; no Save was retried.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function openSaved() {
    const target = Number(savedId);
    if (lock.current || pending || !Number.isSafeInteger(target) || target <= 0)
      return;
    lock.current = true;
    setBusy(true);
    try {
      fields(await call<DraftRecord>("read", { id: target }));
      setResult(undefined);
      setHistory(undefined);
      setMessage(
        "Saved Full Day Draft loaded, including cancellation state. Unsaved entry values were replaced by your explicit request.",
      );
    } catch {
      setMessage(
        "Saved Full Day ID could not be loaded. Existing fields retained; no write was attempted.",
      );
    } finally {
      lock.current = false;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <Dialog
      className="day-editor-dialog"
      title={
        pending
          ? "Full Day Draft — recover earlier request"
          : base
            ? `FullDayDraft #${base.id} · revision ${base.revision}`
            : "New Full Day Draft"
      }
      onClose={onClose}
      busy={busy}
    >
      <p className="preview-pending">
        Draft / Validation pending · Production daily writes closed · Apply /
        Publish unavailable.
      </p>
      {base && (
        <p>
          Loaded saved status: <strong>{base.status}</strong> · Full Day ·
          revision {base.revision}
        </p>
      )}
      <p>
        {enabled
          ? "Synthetic engineering profile: explicit manual Draft writes enabled for testing only."
          : "Read-only editor preview. Synthetic test opt-in is required; production rollout is not approved."}
      </p>
      {loading && (
        <p role="status">Reading saved revision and recovery state…</p>
      )}
      {message && (
        <p
          role={
            pending || result?.outcome === "Rejected" || broken
              ? "alert"
              : "status"
          }
          className="editor-outcome"
        >
          {message}
        </p>
      )}
      {pending && (
        <section className="editor-recovery">
          <h3>Original request · {pending.action}</h3>
          <p>
            Request {pending.request_id} ·{" "}
            {pending.id ? `FullDayDraft #${pending.id}` : "new record"} ·{" "}
            {pending.local_date ?? "saved cancellation"}
          </p>
          <button disabled={busy} onClick={() => void action("Resolve")}>
            Resolve original request
          </button>{" "}
          <button
            disabled={
              busy ||
              !enabled ||
              ["REQUEST_REUSED", "WRONG_PROFILE"].includes(result?.code ?? "")
            }
            onClick={() => void action("Retry")}
          >
            Retry same unchanged request
          </button>
        </section>
      )}
      {!pending && !loading && !broken && (
        <>
          {!committed && (
            <details>
              <summary>Open saved Full Day ID, including cancelled</summary>
              <div className="day-preview-toolbar">
                <label>
                  Open saved FullDayDraft ID, including cancelled
                  <input
                    inputMode="numeric"
                    value={savedId}
                    disabled={busy}
                    onChange={(e) => setSavedId(e.target.value)}
                  />
                </label>
                <button
                  disabled={busy || !/^\d+$/.test(savedId)}
                  onClick={() => void openSaved()}
                >
                  Load saved ID — replace unsaved fields
                </button>
              </div>
            </details>
          )}
          <div className="day-editor-fields">
            <label>
              WorkItem / Project
              <select
                id="day-editor-work"
                disabled={frozen}
                value={work}
                onChange={(e) => {
                  setWork(e.target.value);
                  changed(true);
                }}
              >
                <option value="">Select a WorkItem</option>
                {works.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.job_number} · {w.type} · WorkItem #{w.id}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Crew
              <select
                id="day-editor-crew"
                disabled={frozen}
                value={crew}
                onChange={(e) => {
                  setCrew(e.target.value);
                  changed(true);
                }}
              >
                <option value="">Select a Crew</option>
                {crews.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                    {c.active ? "" : " · Inactive"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Full local date
              <input
                id="day-editor-date"
                type="date"
                disabled={frozen}
                value={date}
                onChange={(e) => {
                  setDate(e.target.value);
                  changed(true);
                }}
              />
            </label>
            <label>
              Staffing record
              <select
                disabled={frozen}
                value={configured ? "Explicit" : "Unknown"}
                onChange={(e) => {
                  setConfigured(e.target.value === "Explicit");
                  setConfirmed(false);
                  changed();
                }}
              >
                <option value="Unknown">Not recorded — Unknown</option>
                <option value="Explicit">Explicit employee list</option>
              </select>
            </label>
          </div>
          <label>
            Draft notes
            <textarea
              id="day-editor-notes"
              disabled={frozen}
              value={notes}
              onChange={(e) => {
                setNotes(e.target.value);
                changed();
              }}
            />
          </label>
          {configured && (
            <fieldset disabled={frozen}>
              <legend>
                Actual employees · {members.length} explicitly selected
              </legend>
              <p>
                Home Crew is reference only. Inactive, unavailable or
                conflicting employees do not become eligible by selecting them.
                No other Crew is changed.
              </p>
              <div className="day-editor-members">
                {people.map((p) => (
                  <label key={p.id}>
                    <input
                      type="checkbox"
                      checked={members.includes(p.id)}
                      onChange={(e) => {
                        setMembers(
                          e.target.checked
                            ? [...members, p.id]
                            : members.filter((x) => x !== p.id),
                        );
                        setConfirmed(false);
                        changed();
                      }}
                    />
                    {p.name} · #{p.id} · Home Crew #{p.home_crew_id}
                    {p.active ? "" : " · Inactive"}
                  </label>
                ))}
              </div>
              {members
                .filter((e) => !people.some((p) => p.id === e))
                .map((e) => (
                  <p key={e}>
                    Retained employee #{e} — current directory unavailable;
                    reload before changing this selection.
                  </p>
                ))}
              <label className="day-editor-confirmation">
                <input
                  id="day-editor-confirm-workers"
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                I explicitly confirm this list (including an empty list) for
                this WorkItem, Crew and full date.
              </label>
            </fieldset>
          )}
          <div className="day-preview-toolbar">
            <button
              className="editor-primary"
              disabled={frozen || !enabled}
              onClick={() => void action("Save")}
            >
              Save Full Day Draft
            </button>
            {base && (
              <button
                disabled={busy || !!pending || committed}
                onClick={() => void reload()}
              >
                Use current saved values — replace unsaved fields
              </button>
            )}
          </div>
          {base && !committed && base.status === "Draft" && (
            <section>
              <h3>Cancel saved Draft #{base.id}</h3>
              <p>
                Retains ID, notes, actual-member history and all legacy records.
                Unsaved form edits are not saved by this action.
              </p>
              <label className="day-editor-confirmation">
                <input
                  type="checkbox"
                  disabled={frozen}
                  checked={cancelConfirmed}
                  onChange={(e) => setCancelConfirmed(e.target.checked)}
                />
                I want to cancel FullDayDraft #{base.id} at revision{" "}
                {base.revision}.
              </label>
              <button
                className="editor-cancel"
                disabled={frozen || !enabled || !cancelConfirmed}
                onClick={() => void action("Cancel")}
              >
                Cancel saved Full Day Draft
              </button>
            </section>
          )}
        </>
      )}
      {result?.outcome === "Committed" && result.record && (
        <section className="editor-receipt">
          <h3>Saved receipt · {result.record.status}</h3>
          <p>
            FullDayDraft #{result.record.id} · revision {result.record.revision}{" "}
            · {result.record.local_date} · Request {result.request_id}
          </p>
          <p>
            Receipt records this commit, not a guarantee that another edit has
            not occurred since.{" "}
            {refreshed
              ? "Weekly data refreshed."
              : "Weekly refresh still needed."}
          </p>
          {result.observation && (
            <ul>
              {result.observation.checks.map((c, i) => (
                <li key={i}>
                  <strong>
                    {reasonLabel(c.check)}: {c.state}
                  </strong>{" "}
                  — {[...new Set(c.reasons)].map(reasonLabel).join("; ")}
                </li>
              ))}
            </ul>
          )}
          <button disabled={busy} onClick={() => void refresh(result)}>
            Retry weekly refresh — no writes
          </button>
        </section>
      )}
      {base && !pending && (
        <>
          <button
            disabled={busy}
            onClick={() =>
              void call<History>("history", { id: base.id })
                .then(setHistory)
                .catch(() =>
                  setMessage("History unavailable; no write was attempted."),
                )
            }
          >
            Read latest 100 immutable Draft revisions
          </button>
          {history !== undefined && (
            <ol className="day-editor-history">
              {history.map((h) => (
                <li key={h.revision}>
                  <strong>
                    Revision {h.revision} · {h.status}
                  </strong>{" "}
                  · {h.local_date} · Crew #{h.crew_id}
                  <p>{h.notes || "No notes"}</p>
                  <p>
                    {h.staffing_configured
                      ? h.workers
                          .map((w) => `${w[1]} (#${w[0]}, Home Crew #${w[2]})`)
                          .join("; ") || "Explicitly empty"
                      : "Actual employees not recorded"}
                  </p>
                </li>
              ))}
            </ol>
          )}
        </>
      )}
      <div className="day-preview-toolbar">
        <button disabled={busy} onClick={onClose}>
          {pending
            ? "Close — retain request for recovery"
            : committed
              ? "Return to schedule"
              : "Close without saving"}
        </button>
        <button disabled>Apply / Publish — unavailable</button>
      </div>
    </Dialog>
  );
}
