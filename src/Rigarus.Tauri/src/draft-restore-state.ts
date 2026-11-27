import {
  exact,
  historicalReceipt,
  type DraftReceipt,
  type DraftValues,
} from "./draft-confirmation-state";

export type Warning = {
  warning_id: string;
  record_kind: string;
  record_id?: number;
  local_date?: string;
  check: string;
  reason: string;
  state: "Pending";
};
export type RestorePlan = {
  format: "rigarus-draft-restore-v1";
  database_identity: string;
  source_record_kind: "DraftVersion";
  source_version_id: number;
  source_fingerprint: string;
  plan_fingerprint: string;
  status: "Current" | "Blocked";
  before_restore: DraftValues[];
  proposed_restore: DraftValues[];
  warnings: Warning[];
  blockers: unknown[];
  observations: Observation[];
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  production_writes_enabled: false;
};
type Observation = {
  record_kind: string;
  id: number;
  revision: number;
  notes: string;
  work_item_id: number;
  project_id: number;
  crew_id: number;
  local_date: string;
  staffing_configured: boolean;
  workers: { id: number }[];
  actual_rig_id: number | null;
  checks: { check: string; state: string; reasons: string[] }[];
  validation_status: "Pending";
  applyable: false;
  publishable: false;
};
export type Bundle = { source: DraftReceipt; reviewed: RestorePlan };
export type RestoreRequest = {
  profile_id: string;
  source_record_kind: "DraftVersion";
  source_version_id: number;
  request_id: string;
  plan_fingerprint: string;
  confirmed: true;
  acknowledged_warning_ids: string[];
};
export type RestoreEnvelope = Bundle & {
  operation: "DraftRestore";
  format: "rigarus-restore-journal-v1";
  request: RestoreRequest;
};
export type RestoreReceipt = {
  outcome: "Committed" | "Rejected";
  database_identity: string;
  request_id: string;
  source_record_kind: "DraftVersion";
  source_version_id: number;
  confirmation: RestoreRequest;
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  recorded_at: string;
  version_id?: number;
  record_kind?: "DraftRestoreVersion";
  code?: string;
  plan?: RestorePlan;
  after?: DraftValues[];
  observations?: Observation[];
};
export type RestoreStatus = {
  database_identity: string;
  test_writes_enabled: boolean;
  production_writes_enabled: false;
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  pending: RestoreEnvelope | null;
  other_operation_pending: boolean;
};
const sha = (v: unknown): v is string =>
  typeof v === "string" && /^[a-f0-9]{64}$/.test(v);
export const uuid = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(v);
const positive = (v: unknown): v is number =>
  typeof v === "number" &&
  Number.isSafeInteger(v) &&
  v > 0 &&
  v < Number.MAX_SAFE_INTEGER;
const flags = (v: {
  validation_status?: unknown;
  applyable?: unknown;
  publishable?: unknown;
}) =>
  v?.validation_status === "Pending" &&
  v.applyable === false &&
  v.publishable === false;
function assert(ok: unknown): asserts ok {
  if (!ok)
    throw Error(
      "Incomplete or mismatched Restore evidence. Retain and resolve the original request.",
    );
}
export function versionId(text: string) {
  const v = Number(text);
  assert(/^[1-9]\d*$/.test(text) && positive(v));
  return v;
}
function rows(value: DraftValues[]) {
  assert(
    Array.isArray(value) &&
      value.length <= 366 &&
      new Set(value.map((r) => r?.id)).size === value.length,
  );
  for (const r of value) {
    assert(
      r?.record_kind === "FullDayDraft" &&
        [r.id, r.revision, r.work_item_id, r.project_id, r.crew_id].every(
          positive,
        ) &&
        typeof r.notes === "string" &&
        Array.from(r.notes).length <= 2000 &&
        !r.notes.includes("\0") &&
        ["Draft", "Cancelled"].includes(r.status),
    );
    assert(
      /^\d{4}-\d{2}-\d{2}$/.test(r.local_date) &&
        !Number.isNaN(Date.parse(r.local_date)) &&
        new Date(`${r.local_date}T00:00:00Z`).toISOString().slice(0, 10) ===
          r.local_date &&
        !r.local_date.startsWith("0000"),
    );
    assert(
      r.employee_ids === null ||
        (Array.isArray(r.employee_ids) &&
          r.employee_ids.length <= 100 &&
          r.employee_ids.every(positive) &&
          new Set(r.employee_ids).size === r.employee_ids.length),
    );
  }
}
export function original(value: DraftReceipt, profile: string, id: number) {
  historicalReceipt(value);
  assert(value.database_identity === profile && value.version_id === id);
  rows(value.after!);
  rows(value.plan!.before);
  return value;
}
function observations(value: Observation[], desired: DraftValues[]) {
  const active = desired.filter((r) => r.status === "Draft");
  assert(
    Array.isArray(value) &&
      value.length === active.length &&
      new Set(value.map((r) => r.id)).size === value.length,
  );
  for (const o of value) {
    const r = active.find((r) => r.id === o.id);
    assert(
      r &&
        flags(o) &&
        o.record_kind === "FullDayDraft" &&
        o.staffing_configured === (r.employee_ids !== null),
    );
    for (const k of [
      "revision",
      "notes",
      "work_item_id",
      "project_id",
      "crew_id",
      "local_date",
    ] as const)
      assert(o[k] === r[k]);
    assert(
      Array.isArray(o.workers) &&
        exact(
          o.workers.map((w) => w.id).sort((a, b) => a - b),
          [...(r.employee_ids ?? [])].sort((a, b) => a - b),
        ) &&
        Array.isArray(o.checks),
    );
    for (const name of [
      "DailyCalendars",
      "PersonnelConflicts",
      "ApprovedDriver",
      "CrewType",
      "MinimumStaffing",
      "SkillsLevel1",
      "SkillsLevel2",
      "SkillsLevel3",
      "Qualifications",
      "Foreman",
      "ActualRig",
      "VehicleCategory",
      "WeekendConsent",
    ])
      assert(o.checks.filter((c) => c.check === name).length === 1);
    assert(
      o.checks.every(
        (c) =>
          Array.isArray(c.reasons) &&
          (["Pending", "Satisfied"].includes(c.state) ||
            (c.check === "DailyCalendars" && c.state === "Matched")),
      ),
    );
  }
}
export function prepared(value: Bundle, profile: string, id: number): Bundle {
  assert(value && uuid(profile) && positive(id));
  original(value.source, profile, id);
  const p = value.reviewed;
  assert(
    p &&
      flags(p) &&
      p.format === "rigarus-draft-restore-v1" &&
      p.production_writes_enabled === false &&
      p.database_identity === profile &&
      p.source_record_kind === "DraftVersion" &&
      p.source_version_id === id &&
      sha(p.source_fingerprint) &&
      sha(p.plan_fingerprint),
  );
  rows(p.before_restore);
  rows(p.proposed_restore);
  assert(
    p.before_restore.length > 0 &&
      exact(p.before_restore, value.source.after) &&
      p.proposed_restore.length === p.before_restore.length,
  );
  p.before_restore.forEach((r, i) => {
    const prior = value.source.plan!.before.find((b) => b.id === r.id);
    assert(
      exact(p.proposed_restore[i], {
        ...(prior ?? { ...r, status: "Cancelled" }),
        revision: r.revision + 1,
      }),
    );
  });
  assert(
    Array.isArray(p.blockers) &&
      ((p.status === "Current" && p.blockers.length === 0) ||
        (p.status === "Blocked" && p.blockers.length > 0)) &&
      Array.isArray(p.warnings) &&
      p.warnings.length > 0 &&
      p.warnings.length <= 20000 &&
      new Set(p.warnings.map((w) => w.warning_id)).size === p.warnings.length,
  );
  assert(
    p.warnings.every(
      (w) =>
        w.state === "Pending" &&
        sha(w.warning_id) &&
        typeof w.reason === "string" &&
        !!w.reason &&
        typeof w.check === "string" &&
        !!w.check &&
        (w.record_kind === "DraftRestore" ||
          (w.record_kind === "FullDayDraft" &&
            p.proposed_restore.some(
              (r) => r.id === w.record_id && r.local_date === w.local_date,
            ))),
    ),
  );
  if (p.status === "Current") observations(p.observations, p.proposed_restore);
  return value;
}
export function envelope(value: RestoreEnvelope, profile: string) {
  assert(
    value?.operation === "DraftRestore" &&
      value.format === "rigarus-restore-journal-v1" &&
      uuid(profile),
  );
  const r = value.request;
  assert(
    r &&
      uuid(r.request_id) &&
      r.profile_id === profile &&
      r.confirmed === true &&
      r.source_record_kind === "DraftVersion",
  );
  prepared(value, profile, r.source_version_id);
  assert(
    value.reviewed.status === "Current" &&
      r.plan_fingerprint === value.reviewed.plan_fingerprint &&
      Array.isArray(r.acknowledged_warning_ids) &&
      exact(
        [...r.acknowledged_warning_ids].sort(),
        value.reviewed.warnings.map((w) => w.warning_id).sort(),
      ),
  );
  return value;
}
export function confirmation(
  value: Bundle,
  acknowledged: string[],
  requestId: string,
  confirmed: boolean,
): RestoreEnvelope {
  assert(confirmed);
  const p = value.reviewed;
  return envelope(
    {
      ...value,
      format: "rigarus-restore-journal-v1",
      operation: "DraftRestore",
      request: {
        profile_id: p.database_identity,
        source_record_kind: "DraftVersion",
        source_version_id: p.source_version_id,
        request_id: requestId,
        plan_fingerprint: p.plan_fingerprint,
        confirmed: true,
        acknowledged_warning_ids: [...acknowledged].sort(),
      },
    },
    p.database_identity,
  );
}
export function status(value: RestoreStatus) {
  assert(
    value &&
      flags(value) &&
      uuid(value.database_identity) &&
      value.production_writes_enabled === false &&
      typeof value.test_writes_enabled === "boolean" &&
      typeof value.other_operation_pending === "boolean" &&
      (value.pending === null || typeof value.pending === "object"),
  );
  if (value.pending) envelope(value.pending, value.database_identity);
  return value;
}
export function receipt(pending: RestoreEnvelope, value: RestoreReceipt) {
  envelope(pending, pending.request.profile_id);
  const r = pending.request;
  assert(
    value &&
      flags(value) &&
      value.database_identity === r.profile_id &&
      value.request_id === r.request_id &&
      value.source_record_kind === "DraftVersion" &&
      value.source_version_id === r.source_version_id &&
      exact(value.confirmation, r) &&
      typeof value.recorded_at === "string" &&
      !Number.isNaN(Date.parse(value.recorded_at)),
  );
  if (value.outcome === "Rejected") {
    assert(
      [
        "SOURCE_NOT_FOUND",
        "Stale",
        "Blocked",
        "STALE_RESTORE_PLAN",
        "EACH_PENDING_ITEM_REQUIRES_CONFIRMATION",
        "FINAL_RESOURCE_REVALIDATION_FAILED",
      ].includes(value.code ?? ""),
    );
    return value;
  }
  assert(
    value.outcome === "Committed" &&
      value.record_kind === "DraftRestoreVersion" &&
      positive(value.version_id) &&
      exact(value.plan, pending.reviewed) &&
      exact(value.after, pending.reviewed.proposed_restore) &&
      exact(value.observations, pending.reviewed.observations),
  );
  observations(value.observations!, value.after!);
  return value;
}
export function notFound(value: {
  outcome?: unknown;
  validation_status?: unknown;
  applyable?: unknown;
  publishable?: unknown;
}) {
  return value?.outcome === "NotFound" && flags(value);
}
export class RestoreEpoch {
  private value = 0;
  next() {
    return ++this.value;
  }
  current(ticket: number) {
    return ticket === this.value;
  }
}

export function reviewContext(
  bundle: Bundle,
  pending: RestoreEnvelope | undefined,
  result: RestoreReceipt | undefined,
  acknowledged: string[],
  confirmed: boolean,
) {
  const recorded = pending?.request ?? result?.confirmation;
  return {
    title: recorded ? "Retained review" : bundle.reviewed.status,
    caption: recorded
      ? "Retained reviewed snapshot — not a current database read"
      : "Current at preparation — revalidated on submit, not a reservation",
    acknowledged: recorded?.acknowledged_warning_ids ?? acknowledged,
    confirmed: recorded?.confirmed ?? confirmed,
    recorded: !!recorded,
  };
}

export async function refreshRestored(
  value: RestoreReceipt,
  refresh: (row: DraftValues) => Promise<boolean>,
) {
  assert(value.outcome === "Committed" && value.after?.length);
  const row = value.after.find((r) => r.status === "Draft") ?? value.after[0];
  try {
    return await refresh(row);
  } catch {
    return false;
  }
}
