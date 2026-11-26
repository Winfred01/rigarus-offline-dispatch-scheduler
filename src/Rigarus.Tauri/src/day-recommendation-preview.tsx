import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState } from "react";
import { Dialog } from "./dialog";
import { ImpactFreshness, sameImpactScope } from "./impact-state";
import {
  ImpactComparison,
  ImpactScope,
  type Impact,
  type ImpactCandidate,
  type Replacement,
  type SavedImpactRecord,
} from "./impact-preview";
import { shiftDay } from "./week";
import {
  pendingFlags,
  previewQuery,
  PreviewEpoch,
  reasonLabel,
  type PreviewFields,
  type PreviewOrder,
  type PreviewQuery,
} from "./day-preview-state";

type Crew = { id: number; name: string; type: string; active: boolean };
type Candidate = ImpactCandidate & {
  crew_id: number;
  crew_name: string;
  status: string;
  proposed_start_date: string | null;
  proposed_finish_date: string | null;
  allocated_working_dates: string[];
  accumulated_days: number;
  unfilled_days: number | null;
  review_reasons: string[];
  skipped: { local_date: string; reasons: string[] }[];
  missing_evidence: { check: string; source: string; count: number }[];
  missing_evidence_count: number;
};
type Result = Partial<Impact> & {
  job_number: string;
  work_type: string;
  unit: "FullDay";
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  project_id: number;
  work_item_id: number;
  input_fingerprint: string;
  order: PreviewOrder;
  ranked_crew_ids: number[];
  omitted_by_limit: number;
  candidates: Candidate[];
  crew_reviews: { crew_id: number; crew_name: string; reasons: string[] }[];
};
type Freshness =
  "Current" | "Stale" | "Not checked" | "Checking" | "Unavailable";

export function DayRecommendationPreview({
  projectId,
  workItemId,
  jobNumber,
  workType,
  onClose,
}: {
  projectId: number;
  workItemId: number;
  jobNumber: string;
  workType: string;
  onClose: () => void;
}) {
  const [today] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  });
  const [fields, setFields] = useState<PreviewFields>({
    days: "",
    confirmed: false,
    crews: [],
    start: today,
    end: shiftDay(today, 120),
    limit: 3,
  });
  const [crews, setCrews] = useState<Crew[]>([]),
    [loading, setLoading] = useState(true),
    [catalogError, setCatalogError] = useState(false),
    [attempt, setAttempt] = useState(0);
  const [order, setOrder] = useState<PreviewOrder>("EarliestFinish");
  const [impactMode, setImpactMode] = useState(false);
  const [scope, setScope] = useState<SavedImpactRecord[]>([]);
  const [replacements, setReplacements] = useState<Replacement[]>([]);
  const [selectedCrew, setSelectedCrew] = useState<number>();
  const [result, setResult] = useState<{
    data: Result;
    query: PreviewQuery & {
      replacements?: Replacement[];
    };
  }>();
  const [freshness, setFreshness] = useState<Freshness>("Not checked");
  const [error, setError] = useState(""),
    [invalid, setInvalid] = useState("");
  const [busy, setBusy] = useState(false);
  const alive = useRef(true),
    epoch = useRef(new PreviewEpoch());
  const freshEpoch = useRef(new PreviewEpoch());
  const stale = useRef(new ImpactFreshness());
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      epoch.current.next();
    };
  }, []);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setCatalogError(false);
    setCrews([]);
    void invoke<Crew[]>("search_crews", { term: "" })
      .then((rows) => {
        if (active) setCrews(rows);
      })
      .catch(() => {
        if (active) setCatalogError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  function change(next: Partial<PreviewFields>) {
    epoch.current.next();
    freshEpoch.current.next();
    setBusy(false);
    setResult(undefined);
    setFreshness("Not checked");
    setError("");
    setInvalid("");
    setFields((old) => ({
      ...old,
      ...next,
      ...("days" in next ? { confirmed: false } : {}),
    }));
    setScope([]);
    setReplacements([]);
  }
  async function preview(
    nextOrder: PreviewOrder = order,
    useImpact = impactMode,
  ) {
    const parsed = previewQuery(workItemId, projectId, fields, nextOrder);
    if (parsed.error) {
      setError(parsed.error.message);
      setInvalid(parsed.error.field);
      document.getElementById(`day-preview-${parsed.error.field}`)?.focus();
      return;
    }
    const ticket = epoch.current.next();
    freshEpoch.current.next();
    setBusy(true);
    setError("");
    setInvalid("");
    setResult(undefined);
    stale.current.recompute();
    setImpactMode(useImpact);
    setOrder(nextOrder);
    setFreshness("Not checked");
    try {
      const query = useImpact
        ? { ...parsed.query, replacements }
        : parsed.query;
      const data = await invoke<Result>("day_recommendations", {
        action: useImpact ? "impact_preview" : "preview",
        input: query,
      });
      if (!alive.current || !epoch.current.current(ticket)) return;
      if (
        !pendingFlags(data) ||
        data.work_item_id !== workItemId ||
        data.project_id !== projectId ||
        !/^[a-f0-9]{64}$/.test(data.input_fingerprint)
      )
        throw new Error("Unexpected preview context");
      if (
        useImpact &&
        (!data.before ||
          !Array.isArray(data.before.records) ||
          !Array.isArray(data.protected_records) ||
          !sameImpactScope(data.replacement_scope ?? [], replacements) ||
          !/^[a-f0-9]{64}$/.test(data.proposal_fingerprint ?? ""))
      )
        throw new Error("Unexpected impact context");
      setResult({ data, query });
      if (useImpact) setScope(data.before!.records);
      setSelectedCrew(data.ranked_crew_ids[0] ?? data.candidates[0]?.crew_id);
      setFreshness("Current");
    } catch {
      if (alive.current && epoch.current.current(ticket)) {
        setResult(undefined);
        setError(
          "Unable to read this preview. Reload project data or retry; no alternative is certified.",
        );
      }
    } finally {
      if (alive.current && epoch.current.current(ticket)) setBusy(false);
    }
  }
  async function recheck() {
    if (!result || busy || stale.current.stale) return;
    const ticket = freshEpoch.current.next();
    setFreshness("Checking");
    setError("");
    try {
      const data = await invoke<{
        unit: string;
        validation_status: string;
        applyable: boolean;
        publishable: boolean;
        status: string;
      }>("day_recommendations", {
        action: impactMode ? "impact_freshness" : "freshness",
        input: {
          query: result.query,
          input_fingerprint: result.data.input_fingerprint,
        },
      });
      if (!alive.current || !freshEpoch.current.current(ticket)) return;
      if (!pendingFlags(data) || !["Current", "Stale"].includes(data.status))
        throw new Error("Unexpected freshness");
      setFreshness(stale.current.observe(data.status));
    } catch {
      if (alive.current && freshEpoch.current.current(ticket)) {
        setFreshness("Unavailable");
        setError(
          "Could not recheck current inputs. Preview again before further review.",
        );
      }
    }
  }
  useEffect(() => {
    if (!result) return;
    const focus = () => {
      void recheck();
    };
    const blur = () => {
      freshEpoch.current.next();
      if (!stale.current.stale) setFreshness("Not checked");
    };
    window.addEventListener("focus", focus);
    window.addEventListener("blur", blur);
    return () => {
      window.removeEventListener("focus", focus);
      window.removeEventListener("blur", blur);
    };
  }, [result, busy, impactMode]);
  const ranked =
    result?.data.ranked_crew_ids
      .map((id) => result.data.candidates.find((c) => c.crew_id === id))
      .filter((c): c is Candidate => Boolean(c)) ?? [];
  const diagnostic =
    result?.data.candidates.filter((c) => c.status === "Needs Review") ?? [];
  return (
    <Dialog
      title={`Auto-Recommend · ${result?.data.job_number ?? jobNumber} (${result?.data.work_type ?? workType}) · WorkItem #${workItemId}`}
      onClose={onClose}
      initialFocus="#day-preview-days"
    >
      <div className="day-recommendation-preview">
        <p className="preview-pending">
          <strong>Full Day · Validation pending</strong> — date-only
          alternatives. Actual workers and Rig are not selected; this preview
          does not reserve resources.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void preview();
          }}
        >
          <div className="day-preview-fields">
            <label>
              Remaining Days
              <input
                id="day-preview-days"
                inputMode="numeric"
                value={fields.days}
                aria-invalid={invalid === "days"}
                aria-describedby="day-preview-duration-help"
                onChange={(e) => change({ days: e.target.value })}
              />
            </label>
            <label>
              Show alternatives
              <select
                id="day-preview-limit"
                value={fields.limit}
                onChange={(e) => change({ limit: Number(e.target.value) })}
              >
                {Array.from({ length: 10 }, (_, i) => (
                  <option key={i + 1}>{i + 1}</option>
                ))}
              </select>
            </label>
            <label>
              Start on or after
              <input
                id="day-preview-start"
                type="date"
                value={fields.start}
                aria-invalid={invalid === "start"}
                onChange={(e) => change({ start: e.target.value })}
              />
            </label>
            <label>
              Planning horizon ends
              <input
                id="day-preview-end"
                type="date"
                value={fields.end}
                aria-invalid={invalid === "end"}
                onChange={(e) => change({ end: e.target.value })}
              />
            </label>
          </div>
          <p id="day-preview-duration-help">
            Enter remaining whole days explicitly. Estimated half-days and saved
            visits are not converted or deducted.
          </p>
          <label className="day-preview-check">
            <input
              id="day-preview-confirmed"
              type="checkbox"
              checked={fields.confirmed}
              aria-invalid={invalid === "confirmed"}
              onChange={(e) => change({ confirmed: e.target.checked })}
            />
            I confirm these Remaining Days for this preview.
          </label>
          <fieldset
            id="day-preview-crews"
            tabIndex={-1}
            aria-invalid={invalid === "crews"}
          >
            <legend>
              Candidate Crews — alternatives, not simultaneous allocations
            </legend>
            {loading ? (
              <p role="status">Loading Crews…</p>
            ) : catalogError ? (
              <p role="alert">
                Unable to load Crews.{" "}
                <button type="button" onClick={() => setAttempt((x) => x + 1)}>
                  Retry Crews
                </button>
              </p>
            ) : crews.length === 0 ? (
              <p>No Crews recorded. Add master data in People first.</p>
            ) : (
              <div className="day-preview-crews">
                {crews.map((c) => (
                  <label className="day-preview-check" key={c.id}>
                    <input
                      type="checkbox"
                      checked={fields.crews.includes(c.id)}
                      onChange={(e) =>
                        change({
                          crews: e.target.checked
                            ? [...fields.crews, c.id]
                            : fields.crews.filter((id) => id !== c.id),
                        })
                      }
                    />
                    {c.name} · {c.type}
                    {c.active ? "" : " · Inactive"}
                  </label>
                ))}
              </div>
            )}
          </fieldset>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <div className="day-preview-toolbar">
            <button
              id="day-preview-run"
              disabled={loading || catalogError || busy}
            >
              {busy
                ? "Reading current sources…"
                : impactMode
                  ? "Recompute impact"
                  : "Preview full-day dates"}
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={loading || catalogError || busy}
              onClick={() => void preview(order, true)}
            >
              Preview Impact
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
            >
              Cancel / close preview
            </button>
          </div>
        </form>
        {impactMode && scope.length > 0 && (
          <ImpactScope
            records={scope}
            replacements={replacements}
            onChange={(rows) => {
              epoch.current.next();
              freshEpoch.current.next();
              stale.current.invalidate();
              setFreshness("Stale");
              setBusy(false);
              setResult(undefined);
              setReplacements(rows);
              setError("Replacement scope changed. Recompute Preview Impact.");
            }}
          />
        )}
        {result && (
          <section aria-label="Full-day preview results">
            <div className="day-preview-toolbar">
              <button
                type="button"
                className={order === "EarliestFinish" ? "" : "secondary-button"}
                aria-pressed={order === "EarliestFinish"}
                onClick={() => void preview("EarliestFinish")}
              >
                Earliest Finish
              </button>
              <button
                type="button"
                className={order === "EarliestStart" ? "" : "secondary-button"}
                aria-pressed={order === "EarliestStart"}
                onClick={() => void preview("EarliestStart")}
              >
                Earliest Start
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={freshness === "Checking"}
                onClick={() => void recheck()}
              >
                Recheck inputs
              </button>
            </div>
            <p role="status">
              {freshness === "Current"
                ? "Current at last read — not a reservation."
                : freshness === "Stale"
                  ? "Stale — inputs changed. Preview again."
                  : `${freshness} — preview must be rechecked.`}
            </p>
            {impactMode && result.data.before && (
              <>
                <label>
                  Compare Proposed Crew
                  <select
                    aria-label="Compare Proposed Crew"
                    value={selectedCrew ?? ""}
                    onChange={(e) => {
                      setSelectedCrew(Number(e.target.value));
                      void recheck();
                    }}
                  >
                    {result.data.candidates.map((c) => (
                      <option key={c.crew_id} value={c.crew_id}>
                        {c.crew_name} · {c.resource_state ?? c.status}
                      </option>
                    ))}
                  </select>
                </label>
                <ImpactComparison
                  impact={result.data as Result & Impact}
                  candidate={result.data.candidates.find(
                    (c) => c.crew_id === selectedCrew,
                  )}
                  days={result.query.remaining_days}
                />
              </>
            )}
            {!ranked.length && (
              <p>
                No complete unblocked alternative in this horizon. Review the
                diagnostics below.
              </p>
            )}
            {ranked.map((c, i) => (
              <article className="day-preview-candidate" key={c.crew_id}>
                <h3>
                  Option {i + 1} · {c.crew_name}
                </h3>
                <p>
                  {c.proposed_start_date} → {c.proposed_finish_date} ·{" "}
                  {c.accumulated_days}/{fields.days.trim()} days accumulated
                </p>
                <p>Rig: Not assigned · Validation pending</p>
                <details>
                  <summary>Dates and missing checks</summary>
                  <CandidateDetails candidate={c} />
                </details>
                <button type="button" disabled>
                  Apply to Draft — not available
                </button>
              </article>
            ))}
            {result.data.omitted_by_limit > 0 && (
              <p>
                {result.data.omitted_by_limit} additional complete date
                alternatives omitted by your result limit.
              </p>
            )}
            {diagnostic.map((c) => (
              <article className="day-preview-candidate" key={c.crew_id}>
                <h3>{c.crew_name} · Needs Review</h3>
                <p>
                  {c.accumulated_days} accumulated ·{" "}
                  {c.unfilled_days ?? "Unconfirmed"} days unfilled. No certified
                  finish.
                </p>
                <details>
                  <summary>Review dates and reasons</summary>
                  <CandidateDetails candidate={c} />
                </details>
              </article>
            ))}
            {impactMode &&
              result.data.candidates
                .filter((c) => c.resource_state === "Blocked")
                .map((c) => (
                  <p role="status" key={c.crew_id}>
                    {c.crew_name} · Blocked. Select this Crew in the comparison
                    to review exact resource reasons; dates do not establish
                    eligibility.
                  </p>
                ))}
            {result.data.crew_reviews.map((c) => (
              <p key={c.crew_id}>
                {c.crew_name} · Needs Review:{" "}
                {c.reasons.map(reasonLabel).join("; ")}
              </p>
            ))}
            <p>
              Unknown availability, missing approval or a calendar match never
              proves safe dispatch. Missing-check counts cover scanned dates;
              complete safety and human Apply are separate.
            </p>
            <button type="button" disabled>
              Publish — not available
            </button>
          </section>
        )}
      </div>
    </Dialog>
  );
}

function CandidateDetails({ candidate: c }: { candidate: Candidate }) {
  return (
    <>
      <p>Accumulated: {c.allocated_working_dates.join(", ") || "None"}</p>
      {c.review_reasons.length > 0 && (
        <p>{c.review_reasons.map(reasonLabel).join("; ")}</p>
      )}
      <ul>
        {c.skipped.map((d) => (
          <li key={d.local_date}>
            {d.local_date}: {d.reasons.map(reasonLabel).join("; ")}
          </li>
        ))}
      </ul>
      <ul>
        {c.missing_evidence.map((m) => (
          <li key={`${m.check}:${m.source}`}>
            {reasonLabel(m.check)} · {m.source.toLowerCase()} / pending on{" "}
            {m.count} scanned date(s)
          </li>
        ))}
      </ul>
    </>
  );
}
