export type DraftValues = {
  record_kind: "FullDayDraft";
  id: number;
  revision: number;
  work_item_id: number;
  project_id: number;
  crew_id: number;
  local_date: string;
  notes: string;
  status: "Draft" | "Cancelled";
  employee_ids: number[] | null;
};
export type ProposedValues = Omit<DraftValues, "id" | "revision"> & {
  id: number | null;
};
export function displayRows<
  T extends { local_date: string; crew_id: number; id: number | null },
>(rows: T[]): T[] {
  return [...rows].sort(
    (a, b) =>
      a.local_date.localeCompare(b.local_date) ||
      a.crew_id - b.crew_id ||
      (a.id ?? 0) - (b.id ?? 0),
  );
}
export type PrepareInput = {
  query: Record<string, unknown>;
  selected_crew_id: number;
  notes: string | null;
};
export type Prepared = {
  format: string;
  database_identity: string;
  status: string;
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  plan_fingerprint: string;
  input_fingerprint: string;
  proposal_fingerprint: string;
  before: DraftValues[];
  proposed: ProposedValues[];
  cancel_ids: number[];
  warnings: Record<string, unknown>;
  affected_crew_ids: number[];
  affected_work_item_ids: number[];
  confirmed_remaining_days: number;
};
export type Confirmation = {
  plan: PrepareInput;
  profile_id: string;
  request_id: string;
  plan_fingerprint: string;
  confirmed: true;
  pending_acknowledged: true;
};
export type Envelope = { request: Confirmation; reviewed: Prepared };
export type DraftReceipt = {
  outcome: "Committed" | "Rejected";
  request_id: string;
  database_identity: string;
  confirmation: Confirmation;
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  code?: string;
  version_id?: number;
  recorded_at?: string;
  plan?: Prepared;
  after?: DraftValues[];
  observations?: Observation[];
};
type Observation = {
  record_kind: string;
  id: number;
  revision: number;
  work_item_id: number;
  project_id: number;
  crew_id: number;
  local_date: string;
  notes: string;
  workers: { id: number }[];
  staffing_configured: boolean;
  checks: { check?: string; state: string }[];
  validation_status: string;
  applyable: boolean;
  publishable: boolean;
};
export type Inverse = {
  readonly: true;
  status: "Current" | "Stale";
  version_id: number;
  before_restore: DraftValues[];
  proposed_restore: (Omit<DraftValues, "revision"> & {
    expected_current_revision: number;
  })[];
  restore_enabled: false;
  warnings: string[];
  validation_status: string;
  applyable: boolean;
  publishable: boolean;
};
const positive = (v: unknown): v is number =>
  typeof v === "number" && Number.isSafeInteger(v) && v > 0;
const uuid = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(v);
const sha = (v: unknown) => typeof v === "string" && /^[a-f0-9]{64}$/.test(v);
const flags = (v: {
  validation_status?: unknown;
  applyable?: unknown;
  publishable?: unknown;
}) =>
  v?.validation_status === "Pending" &&
  v.applyable === false &&
  v.publishable === false;
export function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .filter(([, v]) => v !== undefined)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${JSON.stringify(k)}:${canonical(v)}`)
      .join(",")}}`;
  return JSON.stringify(value);
}
export const exact = (a: unknown, b: unknown) => canonical(a) === canonical(b);
function day(v: unknown) {
  if (typeof v !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
  const d = new Date(`${v}T00:00:00.000Z`);
  return (
    !Number.isNaN(d.valueOf()) &&
    d.toISOString().slice(0, 10) === v &&
    v.slice(0, 4) !== "0000"
  );
}
function values(v: ProposedValues | DraftValues, saved = false) {
  return (
    v?.record_kind === "FullDayDraft" &&
    ((v.id === null && !saved) || positive(v.id)) &&
    (!saved || positive((v as DraftValues).revision)) &&
    positive(v.work_item_id) &&
    positive(v.project_id) &&
    positive(v.crew_id) &&
    day(v.local_date) &&
    typeof v.notes === "string" &&
    Array.from(v.notes).length <= 2000 &&
    !v.notes.includes("\0") &&
    ["Draft", "Cancelled"].includes(v.status) &&
    (v.employee_ids === null ||
      (Array.isArray(v.employee_ids) &&
        v.employee_ids.length <= 100 &&
        v.employee_ids.every(positive) &&
        new Set(v.employee_ids).size === v.employee_ids.length))
  );
}
function assert(
  ok: unknown,
  message = "Incomplete or mismatched Draft proof; retain the original request.",
): asserts ok {
  if (!ok) throw Error(message);
}
export function planInput(
  query: Record<string, unknown>,
  crew: number,
): PrepareInput {
  return {
    query: {
      ...query,
      replacements: query.replacements ?? [],
      proposed_employee_ids: query.proposed_employee_ids ?? null,
      proposed_rig_id: query.proposed_rig_id ?? null,
    },
    selected_crew_id: crew,
    notes: null,
  };
}
export function prepared(value: Prepared, input: PrepareInput): Prepared {
  assert(
    value &&
      flags(value) &&
      value.format === "rigarus-unconfirmed-draft-v1" &&
      value.status === "Current" &&
      uuid(value.database_identity) &&
      sha(value.plan_fingerprint) &&
      sha(value.input_fingerprint) &&
      sha(value.proposal_fingerprint),
  );
  assert(
    positive(value.confirmed_remaining_days) &&
      value.confirmed_remaining_days === input.query.remaining_days &&
      input.query.remaining_confirmed === true &&
      positive(input.selected_crew_id),
  );
  assert(
    Array.isArray(value.before) &&
      value.before.length <= 366 &&
      value.before.every((r) => values(r, true)) &&
      new Set(value.before.map((r) => r.id)).size === value.before.length,
  );
  assert(
    Array.isArray(value.proposed) &&
      value.proposed.length === value.confirmed_remaining_days &&
      value.proposed.length <= 366 &&
      value.proposed.every(
        (r) =>
          values(r) &&
          r.status === "Draft" &&
          r.work_item_id === input.query.work_item_id &&
          r.project_id === input.query.expected_project_id &&
          r.crew_id === input.selected_crew_id &&
          exact(r.employee_ids, input.query.proposed_employee_ids),
      ),
  );
  assert(
    new Set(value.proposed.map((r) => r.local_date)).size ===
      value.proposed.length &&
      Array.isArray(value.cancel_ids) &&
      value.cancel_ids.every(positive) &&
      new Set(value.cancel_ids).size === value.cancel_ids.length &&
      value.warnings &&
      typeof value.warnings === "object" &&
      Array.isArray(value.warnings.checks) &&
      Array.isArray(value.warnings.notes) &&
      Array.isArray(value.warnings.missing_evidence) &&
      typeof value.warnings.locks === "string" &&
      typeof value.warnings.downstream === "string",
  );
  const scope = input.query.replacements as {
    record_kind: string;
    record_id: number;
    expected_revision: number;
  }[];
  assert(
    Array.isArray(scope) &&
      scope.length === value.before.length &&
      scope.every(
        (s) =>
          s.record_kind === "FullDayDraft" &&
          value.before.some(
            (r) => r.id === s.record_id && r.revision === s.expected_revision,
          ),
      ),
  );
  const used = new Set<number>();
  for (const p of value.proposed) {
    const old = value.before.find(
      (r) => r.crew_id === p.crew_id && r.local_date === p.local_date,
    );
    assert(p.id === (old?.id ?? null));
    if (old) {
      assert(!used.has(old.id));
      used.add(old.id);
    }
    assert(p.notes === (input.notes ?? old?.notes ?? ""));
  }
  assert(
    exact(
      [...value.cancel_ids].sort((a, b) => a - b),
      value.before
        .filter((r) => !used.has(r.id))
        .map((r) => r.id)
        .sort((a, b) => a - b),
    ),
  );
  return value;
}
export function envelope(value: Envelope, profile: string): Envelope {
  assert(
    value &&
      uuid(profile) &&
      value.request &&
      value.request.profile_id === profile &&
      uuid(value.request.request_id) &&
      sha(value.request.plan_fingerprint) &&
      value.request.confirmed === true &&
      value.request.pending_acknowledged === true,
  );
  prepared(value.reviewed, value.request.plan);
  assert(
    value.reviewed.database_identity === profile &&
      value.reviewed.plan_fingerprint === value.request.plan_fingerprint,
  );
  return value;
}
export function confirmation(
  plan: PrepareInput,
  reviewed: Prepared,
  requestId: string,
): Envelope {
  return envelope(
    {
      request: {
        plan,
        profile_id: reviewed.database_identity,
        request_id: requestId,
        plan_fingerprint: reviewed.plan_fingerprint,
        confirmed: true,
        pending_acknowledged: true,
      },
      reviewed,
    },
    reviewed.database_identity,
  );
}
const rejectionCodes = [
  "STALE_OR_CHANGED_EXACT_PLAN",
  "BLOCKED_OR_INCOMPLETE_PLAN",
  "FINAL_SAVED_RESOURCE_BLOCKED",
  "EXPLICIT_PLAN_AND_PENDING_CONFIRMATION_REQUIRED",
  "ACTUAL_RIG_WRITE_UNSUPPORTED",
];
export function verifiedReceipt(
  pending: Envelope,
  result: DraftReceipt,
): DraftReceipt {
  envelope(pending, pending.request.profile_id);
  assert(
    result &&
      flags(result) &&
      result.request_id === pending.request.request_id &&
      result.database_identity === pending.request.profile_id &&
      exact(result.confirmation, pending.request),
  );
  if (result.outcome === "Rejected") {
    assert(rejectionCodes.includes(result.code ?? ""));
    return result;
  }
  assert(
    result.outcome === "Committed" &&
      positive(result.version_id) &&
      typeof result.recorded_at === "string" &&
      !Number.isNaN(Date.parse(result.recorded_at)) &&
      exact(result.plan, pending.reviewed),
  );
  const plan = pending.reviewed;
  assert(
    Array.isArray(result.after) &&
      result.after.length === plan.cancel_ids.length + plan.proposed.length &&
      result.after.every((r) => values(r, true)) &&
      new Set(result.after.map((r) => r.id)).size === result.after.length,
  );
  const rows = result.after;
  for (const id of plan.cancel_ids) {
    const old = plan.before.find((r) => r.id === id)!;
    assert(
      exact(
        rows.find((r) => r.id === id),
        { ...old, status: "Cancelled", revision: old.revision + 1 },
      ),
    );
  }
  const created = new Set<number>();
  for (const p of plan.proposed) {
    const old = plan.before.find((r) => r.id === p.id);
    const r =
      p.id === null
        ? rows.find(
            (r) =>
              !plan.before.some((b) => b.id === r.id) &&
              r.local_date === p.local_date &&
              r.crew_id === p.crew_id,
          )
        : rows.find((r) => r.id === p.id);
    assert(r && !created.has(r.id));
    created.add(r.id);
    const oldValues = old ? { ...old, revision: undefined } : undefined;
    const expected = old ? old.revision + (exact(oldValues, p) ? 0 : 1) : 1;
    assert(exact(r, { ...p, id: r.id, revision: expected }));
  }
  assert(
    Array.isArray(result.observations) &&
      result.observations.length === plan.proposed.length &&
      new Set(result.observations.map((o) => o.id)).size ===
        plan.proposed.length,
  );
  for (const o of result.observations) {
    const r = rows.find((r) => r.id === o.id && r.status === "Draft");
    assert(
      r &&
        flags(o) &&
        o.record_kind === "FullDayDraft" &&
        o.revision === r.revision &&
        o.local_date === r.local_date &&
        o.crew_id === r.crew_id &&
        o.work_item_id === r.work_item_id &&
        o.project_id === r.project_id &&
        o.notes === r.notes &&
        o.staffing_configured === (r.employee_ids !== null) &&
        Array.isArray(o.workers) &&
        exact(
          o.workers.map((w) => w.id).sort((a, b) => a - b),
          [...(r.employee_ids ?? [])].sort((a, b) => a - b),
        ) &&
        Array.isArray(o.checks) &&
        o.checks.length > 0 &&
        o.checks.every(
          (c) =>
            ["Pending", "Satisfied"].includes(c.state) ||
            (c.check === "DailyCalendars" && c.state === "Matched"),
        ),
    );
  }
  return result;
}
export function historicalReceipt(result: DraftReceipt) {
  assert(result?.outcome === "Committed" && result.plan && result.confirmation);
  return verifiedReceipt(
    { request: result.confirmation, reviewed: result.plan },
    result,
  );
}
export function inverse(value: Inverse, id: number) {
  assert(
    value &&
      flags(value) &&
      value.readonly === true &&
      value.restore_enabled === false &&
      value.version_id === id &&
      ["Current", "Stale"].includes(value.status) &&
      Array.isArray(value.before_restore) &&
      value.before_restore.every((r) => values(r, true)) &&
      Array.isArray(value.proposed_restore) &&
      value.proposed_restore.every(
        (r) => values(r) && positive(r.expected_current_revision),
      ) &&
      Array.isArray(value.warnings),
  );
  return value;
}
