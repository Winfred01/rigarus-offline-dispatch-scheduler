import { reasonLabel } from "./day-preview-state";

export type Replacement = {
  record_kind: "FullDayDraft";
  record_id: number;
  expected_revision: number;
};
type Check = {
  check: string;
  state: string;
  reasons: string[];
  local_date: string;
  record_kind: string;
  record_id: number;
};
export type SavedImpactRecord = {
  record_kind: "FullDayDraft" | "LegacyHalfDay";
  record_id: number;
  revision: number;
  work_item_id: number;
  crew_id: number;
  local_date: string;
  slot: string | null;
  employee_ids: number[];
  actual_rig_id: number | null;
  checks: Check[];
};
export type Impact = {
  proposal_id: string;
  proposal_fingerprint: string;
  before: {
    records: SavedImpactRecord[];
    start_date: string | null;
    finish_date: string | null;
    selected_start_date: string | null;
    selected_finish_date: string | null;
  };
  protected_records: SavedImpactRecord[];
  affected_crew_ids: number[];
  affected_work_item_ids: number[];
  outside_horizon_count: number;
  lock_status: string;
  downstream_status: string;
  replacement_scope: Replacement[];
};
export type ImpactCandidate = {
  crew_id: number;
  proposed_start_date: string | null;
  proposed_finish_date: string | null;
  resource_state?: string;
  checks?: Check[];
};

export function ImpactScope({
  records,
  replacements,
  onChange,
}: {
  records: SavedImpactRecord[];
  replacements: Replacement[];
  onChange: (rows: Replacement[]) => void;
}) {
  return (
    <fieldset>
      <legend>Exact saved visits to replace in this preview</legend>
      <p>
        No selection means additional work. Saved visits are never cancelled.
      </p>
      {records.length === 0 && <p>No active saved visits in this horizon.</p>}
      {records.map((r) => (
        <label
          className="day-preview-check"
          key={`${r.record_kind}:${r.record_id}`}
        >
          {r.record_kind === "FullDayDraft" && (
            <input
              type="checkbox"
              checked={replacements.some((x) => x.record_id === r.record_id)}
              onChange={(e) =>
                onChange(
                  e.target.checked
                    ? [
                        ...replacements,
                        {
                          record_kind: "FullDayDraft",
                          record_id: r.record_id,
                          expected_revision: r.revision,
                        },
                      ]
                    : replacements.filter((x) => x.record_id !== r.record_id),
                )
              }
            />
          )}
          {r.record_kind} #{r.record_id} · revision {r.revision} ·{" "}
          {r.local_date}
          {r.slot ? ` ${r.slot} · Legacy / Needs Review — retained` : ""}
          {" · "}Crew #{r.crew_id}
        </label>
      ))}
    </fieldset>
  );
}

export function ImpactComparison({
  impact,
  candidate,
  days,
}: {
  impact: Impact;
  candidate?: ImpactCandidate;
  days: number;
}) {
  const records = impact.before.records;
  const crews = [...new Set(records.map((r) => r.crew_id))];
  const employees = [...new Set(records.flatMap((r) => r.employee_ids))];
  const rigs = [
    ...new Set(
      records.flatMap((r) =>
        r.actual_rig_id === null ? [] : [r.actual_rig_id],
      ),
    ),
  ];
  return (
    <section aria-label="Before and After impact">
      <h3>Before / After · read-only</h3>
      <p>
        Saved span covers active visits in this horizon; it is not actual
        progress.
      </p>
      <table className="impact-comparison">
        <caption>
          Saved facts compared with the selected Proposed alternative
        </caption>
        <thead>
          <tr>
            <th>Field</th>
            <th>Before · Saved</th>
            <th>After · Proposed</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th>WorkItem</th>
            <td>
              {[...new Set(records.map((r) => r.work_item_id))].join(", ") ||
                "No saved visits"}
            </td>
            <td>Same selected WorkItem</td>
          </tr>
          <tr>
            <th>Crew</th>
            <td>{crews.map((id) => `#${id}`).join(", ") || "Not recorded"}</td>
            <td>
              {candidate ? `#${candidate.crew_id}` : "No complete alternative"}
            </td>
          </tr>
          <tr>
            <th>Start date</th>
            <td>{impact.before.start_date ?? "Not recorded"}</td>
            <td>{candidate?.proposed_start_date ?? "Not available"}</td>
          </tr>
          <tr>
            <th>Finish date</th>
            <td>{impact.before.finish_date ?? "Not recorded"}</td>
            <td>{candidate?.proposed_finish_date ?? "Not available"}</td>
          </tr>
          <tr>
            <th>Remaining Days</th>
            <td>Not recorded — no saved confirmation</td>
            <td>{days} · operator confirmed for this preview</td>
          </tr>
          <tr>
            <th>Employees</th>
            <td>
              {employees.map((id) => `#${id}`).join(", ") ||
                "Pending / not recorded"}
            </td>
            <td>Pending — no proposed workers selected</td>
          </tr>
          <tr>
            <th>Actual Rig</th>
            <td>
              {rigs.map((id) => `#${id}`).join(", ") ||
                "Pending / not recorded"}
            </td>
            <td>Pending — no actual Rig selected</td>
          </tr>
          <tr>
            <th>Resource checks</th>
            <td>Saved checks below; not dispatch approval</td>
            <td>
              {candidate?.resource_state ?? "Pending"} · overall validation
              Pending
            </td>
          </tr>
          <tr>
            <th>Locks</th>
            <td colSpan={2}>{impact.lock_status}</td>
          </tr>
          <tr>
            <th>Downstream impact</th>
            <td>Protected visits retained</td>
            <td>{impact.downstream_status}</td>
          </tr>
        </tbody>
      </table>
      <p>
        {impact.replacement_scope.length} exact FullDayDraft visit(s) released
        only in memory. Selected saved span:{" "}
        {impact.before.selected_start_date ?? "None"} →{" "}
        {impact.before.selected_finish_date ?? "None"}.{" "}
        {impact.outside_horizon_count} target visit(s) outside this horizon are
        not evaluated.
      </p>
      <p>
        Affected / protected Crew IDs: {impact.affected_crew_ids.join(", ")}.{" "}
        WorkItem IDs: {impact.affected_work_item_ids.join(", ")}. No successor
        is moved.
      </p>
      <details>
        <summary>Saved resource checks ({records.length} visits)</summary>
        {records.map((r) => (
          <div key={`${r.record_kind}:${r.record_id}`}>
            <h4>
              {r.record_kind} #{r.record_id} · {r.local_date} · Crew #
              {r.crew_id}
            </h4>
            <ImpactChecks checks={r.checks} />
          </div>
        ))}
      </details>
      <details>
        <summary>
          Protected daily / legacy occupancy ({impact.protected_records.length})
        </summary>
        <ul>
          {impact.protected_records.map((r) => (
            <li key={`${r.record_kind}:${r.record_id}`}>
              {r.record_kind} #{r.record_id} · WorkItem #{r.work_item_id} · Crew
              #{r.crew_id} · {r.local_date} {r.slot}
            </li>
          ))}
        </ul>
      </details>
      <ImpactChecks checks={candidate?.checks ?? []} />
      <details>
        <summary>Proposal identity — read-only, not Apply authority</summary>
        <p className="impact-fingerprint">{impact.proposal_fingerprint}</p>
      </details>
    </section>
  );
}

function ImpactChecks({ checks }: { checks: Check[] }) {
  return (
    <ul>
      {checks.map((c, i) => (
        <li key={i}>
          {c.local_date} · {c.record_kind} #{c.record_id} ·{" "}
          {reasonLabel(c.check)}: <strong>{c.state}</strong> —{" "}
          {c.reasons.map(reasonLabel).join("; ")}
        </li>
      ))}
    </ul>
  );
}
