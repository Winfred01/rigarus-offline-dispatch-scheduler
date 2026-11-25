import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState } from "react";
import type { ScheduleView } from "./schedule";
import { Dialog } from "./dialog";
import { DayRecommendationPreview } from "./day-recommendation-preview";
import { PreviewEpoch, reasonLabel } from "./day-preview-state";
import { localToday, validLocalDate } from "./assignment-fields";
import { displayDate, shiftDay } from "./week";
import { locateScroll, createLocateCue } from "./schedule-locate";
import {
  savedKey,
  savedKind,
  weekRange,
  revealTypedFilters,
  visitsForCell,
  activeProblems,
  type SavedVisit,
  type SavedKind,
  type SavedTarget,
} from "./workbench-state";
type Work = {
  id: number;
  project_id: number;
  job_number: string;
  site_id: string;
  site_name: string;
  type: string;
};
type Weekly = {
  start_date: string;
  end_date: string;
  crews: { id: number; name: string; type: string; active: boolean }[];
  work_items: Work[];
  people: SavedVisit["workers"];
  records: SavedVisit[];
  readonly: true;
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  view_fingerprint: string;
  target?: { record_kind: SavedKind; id: number; revision: number };
};
function validResult(value: Weekly) {
  return (
    value.readonly === true &&
    value.validation_status === "Pending" &&
    value.applyable === false &&
    value.publishable === false &&
    Array.isArray(value.records) &&
    value.records.every(
      (r) =>
        savedKind(r.record_kind) &&
        r.validation_status === "Pending" &&
        r.applyable === false &&
        r.publishable === false &&
        validLocalDate(r.local_date),
    )
  );
}
export function DayWorkbench({
  view,
  onView,
  day,
  onDay,
  target,
  onLegacy,
}: {
  view: ScheduleView;
  onView: (v: ScheduleView) => void;
  day: string;
  onDay: (d: string) => void;
  target?: SavedTarget;
  onLegacy: () => void;
}) {
  const range = weekRange(day),
    rangeKey = `${range.start}/${range.end}`;
  const [data, setData] = useState<Weekly>(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0),
    [field, setField] = useState(day);
  const [crew, setCrew] = useState(""),
    [project, setProject] = useState("");
  const [detail, setDetail] = useState<SavedVisit>(),
    [review, setReview] = useState(false),
    [recommend, setRecommend] = useState<Work>();
  const [workId, setWorkId] = useState(""),
    [kind, setKind] = useState<SavedKind>("FullDayDraft"),
    [identity, setIdentity] = useState("");
  const [focusKey, setFocusKey] = useState<string>(),
    [highlight, setHighlight] = useState<string>();
  const epoch = useRef(new PreviewEpoch()),
    alive = useRef(true),
    skipRange = useRef("");
  const consumed = useRef<SavedTarget | undefined>(undefined);
  const tools = useRef<HTMLDetailsElement>(null);
  const [cue] = useState(() =>
    createLocateCue<string>(setHighlight, {
      schedule: (run, ms) => window.setTimeout(run, ms),
      cancel: (id) => window.clearTimeout(id),
    }),
  );
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      epoch.current.next();
      cue.dispose();
    };
  }, []);
  useEffect(() => setField(day), [day]);
  useEffect(() => {
    if (skipRange.current === rangeKey) {
      skipRange.current = "";
      return;
    }
    const ticket = epoch.current.next();
    setBusy(true);
    setData(undefined);
    setError("");
    void invoke<Weekly>("schedule_workbench", {
      action: "week",
      input: { start_date: range.start, end_date: range.end },
    })
      .then((value) => {
        if (!alive.current || !epoch.current.current(ticket)) return;
        if (
          !validResult(value) ||
          value.start_date !== range.start ||
          value.end_date !== range.end
        )
          throw Error("Wrong weekly context");
        setData(value);
      })
      .catch(() => {
        if (alive.current && epoch.current.current(ticket)) {
          setData(undefined);
          setError(
            "Unable to read a complete week. Reload; unknown data is not a clear schedule.",
          );
        }
      })
      .finally(() => {
        if (alive.current && epoch.current.current(ticket)) setBusy(false);
      });
  }, [rangeKey, attempt]);
  function navigate(next: string) {
    epoch.current.next();
    cue.clear();
    setFocusKey(undefined);
    setDetail(undefined);
    skipRange.current = "";
    onDay(next);
    setAttempt((x) => x + 1);
  }
  async function locate(recordKind: SavedKind, id: number) {
    if (!savedKind(recordKind) || !Number.isSafeInteger(id) || id <= 0) {
      setError("Choose a record type and a positive saved ID.");
      return;
    }
    const ticket = epoch.current.next();
    cue.clear();
    setFocusKey(undefined);
    setBusy(true);
    setError("");
    setDetail(undefined);
    setReview(false);
    try {
      const value = await invoke<Weekly>("schedule_workbench", {
        action: "locate",
        input: { kind: recordKind, id },
      });
      if (!alive.current || !epoch.current.current(ticket)) return;
      const row = value.records.find(
        (r) => r.record_kind === recordKind && r.id === id,
      );
      if (
        !validResult(value) ||
        !row ||
        value.target?.record_kind !== recordKind ||
        value.target.id !== id ||
        value.target.revision !== row.revision
      )
        throw Error("Wrong target");
      const revealed = revealTypedFilters({ crew, project }, row);
      setCrew(revealed.crew);
      setProject(revealed.project);
      const next = weekRange(row.local_date);
      if (`${next.start}/${next.end}` !== rangeKey)
        skipRange.current = `${next.start}/${next.end}`;
      setData(value);
      if (tools.current) tools.current.open = false;
      onView("Job Schedule");
      onDay(row.local_date);
      setFocusKey(savedKey(row));
    } catch {
      if (alive.current && epoch.current.current(ticket))
        setError(
          "Locate failed: the typed record may be removed, cancelled or unreadable. Week and filters were retained; reload and check its type/ID.",
        );
    } finally {
      if (alive.current && epoch.current.current(ticket)) setBusy(false);
    }
  }
  useEffect(() => {
    if (target && target !== consumed.current) {
      consumed.current = target;
      void locate(target.record_kind ?? "LegacyHalfDay", target.id);
    }
  }, [target]);
  useEffect(() => {
    if (!focusKey || busy || !data) return;
    const card = document.getElementById(`saved-${focusKey}`),
      scroll = card?.closest<HTMLElement>(".week-scroll");
    if (!card || !scroll) {
      setError("The exact typed card could not be revealed. Reload the week.");
      setFocusKey(undefined);
      return;
    }
    const p = scroll.getBoundingClientRect(),
      r = card.getBoundingClientRect();
    const pos = locateScroll(
      p,
      r,
      {
        top: scroll.scrollTop,
        left: scroll.scrollLeft,
        height: scroll.scrollHeight,
        width: scroll.scrollWidth,
      },
      {
        top: scroll.querySelector("thead")?.getBoundingClientRect().height ?? 0,
        left: scroll.querySelector("th")?.getBoundingClientRect().width ?? 0,
      },
    );
    scroll.scrollTop = pos.top;
    scroll.scrollLeft = pos.left;
    card.focus({ preventScroll: true });
    cue.start(focusKey);
    setFocusKey(undefined);
  }, [focusKey, busy, data, view]);
  const shown =
    data?.start_date === range.start && data.end_date === range.end
      ? data
      : undefined;
  const rows =
    shown?.records.filter(
      (r) =>
        (!crew || r.crew_id === Number(crew)) &&
        (!project || r.project_id === Number(project)),
    ) ?? [];
  const projects = [
    ...new Map(
      (shown?.work_items ?? []).map((w) => [w.project_id, w]),
    ).values(),
  ];
  const groups =
    view === "Crew Board"
      ? (shown?.crews ?? [])
          .filter((c) => !crew || c.id === Number(crew))
          .map((c) => ({ id: c.id, title: c.name, sub: c.type, crew: true }))
      : projects
          .filter(
            (p) =>
              (!project || p.project_id === Number(project)) &&
              rows.some((r) => r.project_id === p.project_id),
          )
          .map((p) => ({
            id: p.project_id,
            title: p.job_number,
            sub: `${p.site_id} · ${p.site_name}`,
            crew: false,
          }));
  function openRecommendation(w?: Work) {
    if (w) {
      setDetail(undefined);
      setRecommend(w);
    }
  }
  return (
    <main className="schedule-page project-master day-workbench">
      <p className="breadcrumb">Schedule / {view} / Full Day workbench</p>
      <h1>{view}</h1>
      <nav className="view-tabs" aria-label="Schedule views">
        {(
          [
            "Job Schedule",
            "Crew Board",
            "Employee Week",
            "Working calendars",
          ] as const
        ).map((v) => (
          <button
            key={v}
            aria-current={v === view ? "page" : undefined}
            onClick={() => onView(v)}
          >
            {v}
          </button>
        ))}
        <button id="legacy-schedule-mode" onClick={onLegacy}>
          Legacy compatibility
        </button>
      </nav>
      <p className="preview-pending">
        <strong>Full Day workbench · Draft / Validation pending</strong> —
        read-only saved records. Legacy AM/PM is retained for review. Daily
        editor, human Apply, locks and version recovery are not available here.
        No dispatch or publication approval.
      </p>
      <div className="week-toolbar">
        <button
          aria-label="Previous week"
          disabled={range.start < "0001-01-08"}
          onClick={() => navigate(shiftDay(day, -7))}
        >
          ‹
        </button>
        <button onClick={() => navigate(localToday())}>Today</button>
        <button
          aria-label="Next week"
          disabled={range.end > "9999-12-24"}
          onClick={() => navigate(shiftDay(day, 7))}
        >
          ›
        </button>
        <strong>
          {displayDate(range.start)} – {displayDate(range.end)}
        </strong>
        <label>
          Jump to local date
          <input
            type="date"
            value={field}
            onChange={(e) => setField(e.target.value)}
          />
        </label>
        <button
          onClick={() =>
            validLocalDate(field)
              ? navigate(field)
              : setError("Choose a valid local date.")
          }
        >
          Go
        </button>
        <span>1 Week</span>
        <button
          onClick={() => {
            setDetail(undefined);
            setReview(true);
          }}
          disabled={!shown}
        >
          Review saved checks
        </button>
        <button disabled>Publish — not available</button>
      </div>
      <div className="week-toolbar">
        <label>
          Crew filter
          <select
            value={crew}
            onChange={(e) => {
              cue.clear();
              setCrew(e.target.value);
            }}
          >
            <option value="">All Crews</option>
            {shown?.crews.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Project filter
          <select
            value={project}
            onChange={(e) => {
              cue.clear();
              setProject(e.target.value);
            }}
          >
            <option value="">All Projects</option>
            {projects.map((p) => (
              <option key={p.project_id} value={p.project_id}>
                {p.job_number}
              </option>
            ))}
          </select>
        </label>
        <button
          id="reload-day-workbench"
          onClick={() => {
            skipRange.current = "";
            cue.clear();
            setDetail(undefined);
            setAttempt((x) => x + 1);
          }}
        >
          Reload week
        </button>
      </div>
      <details ref={tools} className="workbench-tools">
        <summary>Locate &amp; Auto-Recommend</summary>
        <form
          className="week-toolbar"
          onSubmit={(e) => {
            e.preventDefault();
            void locate(kind, Number(identity));
          }}
        >
          <label>
            Record type
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as SavedKind)}
            >
              <option>FullDayDraft</option>
              <option>LegacyHalfDay</option>
            </select>
          </label>
          <label>
            Saved ID
            <input
              inputMode="numeric"
              value={identity}
              onChange={(e) => setIdentity(e.target.value)}
            />
          </label>
          <button disabled={busy || !/^\d+$/.test(identity)}>
            Locate saved record
          </button>
        </form>
        <div className="week-toolbar">
          <label>
            WorkItem recommendation
            <select value={workId} onChange={(e) => setWorkId(e.target.value)}>
              <option value="">Select a WorkItem</option>
              {shown?.work_items.map((w) => (
                <option value={w.id} key={w.id}>
                  {w.job_number} · {w.type} · WorkItem #{w.id}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={!workId || !shown}
            onClick={() =>
              openRecommendation(
                shown?.work_items.find((w) => w.id === Number(workId)),
              )
            }
          >
            Auto-Recommend
          </button>
        </div>
      </details>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {busy && <p role="status">Reading a coherent saved week…</p>}
      {shown && (
        <>
          <p role="status">
            {shown.records.length} saved record(s) in the complete loaded week ·{" "}
            {rows.length} visible · Checks observed at load time; reload after
            changes.
          </p>
          <div
            className="week-scroll"
            tabIndex={0}
            aria-label="Full Day and legacy weekly schedule"
          >
            <table className="week-grid">
              <thead>
                <tr>
                  <th>
                    {view === "Crew Board"
                      ? "Crew / reference roster"
                      : "Project / Job number"}
                  </th>
                  {range.days.map((d) => (
                    <th
                      key={d}
                      className={
                        [0, 6].includes(range.days.indexOf(d)) ? "weekend" : ""
                      }
                    >
                      {validLocalDate(d) ? (
                        <>
                          <time dateTime={d}>
                            {new Intl.DateTimeFormat("en", {
                              weekday: "short",
                              timeZone: "UTC",
                            }).format(new Date(d + "T12:00:00Z"))}
                          </time>
                          <br />
                          {d}
                        </>
                      ) : (
                        "Outside supported dates"
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groups.map((g) => (
                  <tr key={g.id}>
                    <th>
                      <strong>{g.title}</strong>
                      <p>{g.sub}</p>
                      {g.crew && (
                        <>
                          <small>
                            Home roster — reference only, not attendance
                          </small>
                          {shown.people
                            .filter((p) => p.home_crew_id === g.id)
                            .map((p) => (
                              <div key={p.id}>
                                {p.name}
                                {p.active ? "" : " · Inactive"}
                              </div>
                            ))}
                        </>
                      )}
                    </th>
                    {range.days.map((d) => (
                      <td key={d}>
                        {visitsForCell(
                          rows.filter((r) =>
                            g.crew ? r.crew_id === g.id : r.project_id === g.id,
                          ),
                          d,
                        ).map((r) => (
                          <button
                            key={savedKey(r)}
                            id={`saved-${savedKey(r)}`}
                            className={`schedule-card ${r.record_kind === "LegacyHalfDay" ? "workbench-legacy" : ""} ${highlight === savedKey(r) ? "locate-highlight" : ""}`}
                            onClick={() => {
                              setError("");
                              setDetail(r);
                            }}
                            aria-label={`${r.record_kind} ${r.id} ${r.job_number} ${r.local_date} ${r.slot ?? "Full Day"}`}
                          >
                            <strong>
                              {r.record_kind === "FullDayDraft"
                                ? "Full Day"
                                : `Legacy ${r.slot}`}{" "}
                              · {r.work_type}
                            </strong>
                            <span>
                              {r.job_number} · {r.crew_name}
                            </span>
                            <span>
                              {r.record_kind} #{r.id} · Draft
                            </span>
                            <span>
                              {r.staffing_configured
                                ? `${r.workers.length} explicitly selected worker(s)`
                                : "Actual staffing not assigned"}
                            </span>
                            <span>
                              {activeProblems(r).some(
                                (c) => c.state === "Blocked",
                              )
                                ? "Known blocker(s)"
                                : "Validation pending"}
                            </span>
                          </button>
                        ))}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {!groups.length && (
              <p>
                No saved records match this week/view. Empty dates do not imply
                completed work.
              </p>
            )}
          </div>
        </>
      )}
      {detail && (
        <Dialog
          title={`${detail.record_kind} #${detail.id} · ${detail.job_number} · ${detail.local_date} ${detail.slot ?? "Full Day"}`}
          onClose={() => setDetail(undefined)}
        >
          <p>
            Draft / Validation pending · revision {detail.revision} ·{" "}
            {detail.compatibility_status}
          </p>
          <dl>
            <dt>WorkItem / Project / Crew IDs</dt>
            <dd>
              {detail.work_item_id} / {detail.project_id} / {detail.crew_id}
            </dd>
            <dt>Site</dt>
            <dd>
              {detail.site_id} · {detail.site_name}
            </dd>
            <dt>Notes</dt>
            <dd className="preserve-lines">{detail.notes || "None"}</dd>
            <dt>Actual workers</dt>
            <dd>
              {detail.staffing_configured
                ? detail.workers
                    .map(
                      (w) =>
                        `${w.name} (#${w.id}, Home Crew #${w.home_crew_id})`,
                    )
                    .join(", ") || "Explicitly empty"
                : "Not configured; Home Crew is not attendance"}
            </dd>
            <dt>Recorded actual Rig ID</dt>
            <dd>
              {detail.actual_rig_id ?? "Not assigned"}
              {detail.rig_context_stale
                ? " · Context stale — Needs Review"
                : ""}
            </dd>
          </dl>
          <Checks row={detail} />
          <div className="day-preview-toolbar">
            <button onClick={() => void locate(detail.record_kind, detail.id)}>
              Locate exact saved card
            </button>
            <button
              onClick={() =>
                openRecommendation(
                  shown?.work_items.find((w) => w.id === detail.work_item_id),
                )
              }
            >
              Auto-Recommend
            </button>
            <button disabled>Daily edit — next slice</button>
            <button disabled>Apply / Publish — not available</button>
            <button onClick={() => setDetail(undefined)}>Close</button>
          </div>
        </Dialog>
      )}
      {review && (
        <Dialog
          title="Selected-week saved checks · Validation pending"
          onClose={() => setReview(false)}
        >
          <p>
            All saved records in this week, including filtered cards. These
            subchecks are observations, not full dispatch approval.
          </p>
          {shown?.records.map((r) => (
            <article key={savedKey(r)}>
              <h3>
                {r.job_number} · {r.record_kind} #{r.id} · {r.local_date}{" "}
                {r.slot}
              </h3>
              <Checks row={r} />
              <button onClick={() => void locate(r.record_kind, r.id)}>
                Locate {r.record_kind} #{r.id}
              </button>
            </article>
          ))}
          {!shown?.records.length && (
            <p>
              No complete loaded week / no saved records. Publication remains
              unavailable.
            </p>
          )}
          <button disabled>Publish — not available</button>
          <button onClick={() => setReview(false)}>Close</button>
        </Dialog>
      )}
      {recommend && (
        <DayRecommendationPreview
          key={recommend.id}
          projectId={recommend.project_id}
          workItemId={recommend.id}
          jobNumber={recommend.job_number}
          workType={recommend.type}
          onClose={() => setRecommend(undefined)}
        />
      )}
    </main>
  );
}
function Checks({ row }: { row: SavedVisit }) {
  return (
    <ul>
      {row.checks.map((c, i) => (
        <li key={`${c.check}-${i}`}>
          <strong>
            {reasonLabel(c.check)}: {c.state}
          </strong>{" "}
          — {[...new Set(c.reasons)].map(reasonLabel).join("; ")}
        </li>
      ))}
    </ul>
  );
}
