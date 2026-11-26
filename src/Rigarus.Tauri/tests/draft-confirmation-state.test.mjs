import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
const source = stripTypeScriptTypes(
  readFileSync(
    new URL("../src/draft-confirmation-state.ts", import.meta.url),
    "utf8",
  ),
);
const api = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);
const profile = "11111111-1111-4111-8111-111111111111",
  requestId = "22222222-2222-4222-8222-222222222222",
  sha = "a".repeat(64);
const flags = {
  validation_status: "Pending",
  applyable: false,
  publishable: false,
};
const row = {
  record_kind: "FullDayDraft",
  id: 10,
  revision: 3,
  work_item_id: 1,
  project_id: 2,
  crew_id: 4,
  local_date: "2026-11-26",
  notes: "Synthetic retained note",
  status: "Draft",
  employee_ids: [8],
};
const proposed = { ...row };
delete proposed.revision;
const input = api.planInput(
  {
    work_item_id: 1,
    expected_project_id: 2,
    remaining_days: 1,
    remaining_confirmed: true,
    crew_ids: [4],
    replacements: [
      { record_kind: "FullDayDraft", record_id: 10, expected_revision: 3 },
    ],
    proposed_employee_ids: [8],
  },
  4,
);
const plan = {
  format: "rigarus-unconfirmed-draft-v1",
  ...flags,
  status: "Current",
  database_identity: profile,
  plan_fingerprint: sha,
  input_fingerprint: sha,
  proposal_fingerprint: sha,
  before: [row],
  proposed: [proposed],
  cancel_ids: [],
  warnings: {
    checks: [{ check: "Driver", state: "Pending", reasons: ["NotRecorded"] }],
    notes: ["UNCONFIRMED_DRAFT_ONLY"],
    missing_evidence: [],
    locks: "Unsupported",
    downstream: "Unsupported",
  },
  affected_crew_ids: [4],
  affected_work_item_ids: [1],
  confirmed_remaining_days: 1,
};
const pending = api.confirmation(input, plan, requestId);
const observation = {
  ...row,
  ...flags,
  workers: [{ id: 8 }],
  staffing_configured: true,
  checks: [{ state: "Pending" }],
};
delete observation.employee_ids;
delete observation.status;
const receipt = {
  outcome: "Committed",
  ...flags,
  request_id: requestId,
  database_identity: profile,
  confirmation: pending.request,
  version_id: 6,
  recorded_at: "2026-11-26T12:00:00Z",
  plan,
  after: [row],
  observations: [observation],
};
const clone = (v) => structuredClone(v);
test("display date order never mutates the exact reviewed selection order", () => {
  const rows = [{ ...row, id: 11, local_date: "2026-11-27" }, row];
  const before = clone(rows);
  assert.deepEqual(
    api.displayRows(rows).map((r) => r.id),
    [10, 11],
  );
  assert.deepEqual(rows, before);
});
test("actual calendar Matched is retained without promoting other safety checks", () => {
  const r = clone(receipt);
  r.observations[0].checks.push({ check: "DailyCalendars", state: "Matched" });
  assert.equal(api.verifiedReceipt(pending, r), r);
  r.observations[0].checks[1].check = "ApprovedDriver";
  assert.throws(() => api.verifiedReceipt(pending, r));
});
test("exact normalized preparation, no-op revision and historical receipt are accepted", () => {
  assert.equal(api.prepared(plan, input), plan);
  assert.equal(api.verifiedReceipt(pending, receipt), receipt);
  assert.equal(api.historicalReceipt(receipt), receipt);
  assert.equal(input.notes, null);
  assert.equal(input.query.proposed_rig_id, null);
});
test("missing receipt or NotFound cannot acknowledge an original request", () => {
  for (const r of [
    null,
    {},
    { outcome: "NotFound" },
    { ...receipt, after: undefined },
    { ...receipt, observations: undefined },
  ])
    assert.throws(() => api.verifiedReceipt(pending, r));
});
test("confirmation binds the unchanged key, complete query and exact warnings", () => {
  for (const mutate of [
    (r) => (r.request_id = requestId.replace("2", "3")),
    (r) => (r.database_identity = profile.replace("1", "3")),
    (r) => (r.confirmation.plan.query.remaining_days = 2),
    (r) => (r.confirmation.pending_acknowledged = false),
    (r) => (r.plan.warnings.checks = []),
    (r) => (r.plan.before[0].notes = "altered"),
  ]) {
    const r = clone(receipt);
    mutate(r);
    assert.throws(() => api.verifiedReceipt(pending, r));
  }
});
test("malformed or promoted root safety flags fail closed", () => {
  for (const mutate of [
    (r) => (r.publishable = true),
    (r) => (r.applyable = true),
    (r) => (r.validation_status = "Validated"),
    (r) => delete r.validation_status,
    (r) => (r.version_id = 0),
    (r) => (r.recorded_at = "unknown"),
  ]) {
    const r = clone(receipt);
    mutate(r);
    assert.throws(() => api.verifiedReceipt(pending, r));
  }
});
test("wrong saved ID, revision, note, Crew, date or employee cannot pass receipt settlement", () => {
  for (const mutate of [
    (r) => (r.after[0].id = 11),
    (r) => (r.after[0].revision = 4),
    (r) => (r.after[0].notes = "wrong"),
    (r) => (r.after[0].crew_id = 5),
    (r) => (r.after[0].local_date = "2026-11-27"),
    (r) => (r.after[0].employee_ids = []),
  ]) {
    const r = clone(receipt);
    mutate(r);
    assert.throws(() => api.verifiedReceipt(pending, r));
  }
});
test("observations must cover each actual active saved record with exact current staffing and no known blocker", () => {
  for (const mutate of [
    (r) => (r.observations = []),
    (r) => (r.observations[0].revision = 2),
    (r) => (r.observations[0].checks = [{ state: "Blocked" }]),
    (r) => (r.observations[0].workers = []),
    (r) => (r.observations[0].staffing_configured = false),
    (r) => (r.observations[0].publishable = true),
    (r) => (r.observations[0].checks = []),
  ]) {
    const r = clone(receipt);
    mutate(r);
    assert.throws(() => api.verifiedReceipt(pending, r));
  }
});
test("a deliberate notes edit requires one appended revision, not history rewind", () => {
  const p = clone(plan),
    i = clone(input);
  i.notes = "Synthetic edited";
  p.proposed[0].notes = i.notes;
  const e = api.confirmation(i, p, requestId),
    r = clone(receipt);
  r.confirmation = e.request;
  r.plan = p;
  r.after[0].notes = i.notes;
  r.after[0].revision = 4;
  r.observations[0].notes = i.notes;
  r.observations[0].revision = 4;
  assert.equal(api.verifiedReceipt(e, r), r);
  r.after[0].revision = 3;
  assert.throws(() => api.verifiedReceipt(e, r));
});
test("extension gets a new unique ID with revision1 and exact values", () => {
  const p = clone(plan),
    i = clone(input);
  i.query.remaining_days = 2;
  p.confirmed_remaining_days = 2;
  p.proposed.push({
    ...proposed,
    id: null,
    local_date: "2026-11-27",
    notes: "",
  });
  const e = api.confirmation(i, p, requestId),
    r = clone(receipt);
  r.confirmation = e.request;
  r.plan = p;
  r.after.push({
    ...row,
    id: 11,
    revision: 1,
    local_date: "2026-11-27",
    notes: "",
  });
  r.observations.push({
    ...observation,
    id: 11,
    revision: 1,
    local_date: "2026-11-27",
    notes: "",
  });
  assert.equal(api.verifiedReceipt(e, r), r);
  r.after[1].id = 10;
  assert.throws(() => api.verifiedReceipt(e, r));
});
test("early finish cancels only the exact selected ID and appends history revision", () => {
  const p = clone(plan),
    i = clone(input),
    old = { ...row, id: 11, revision: 8, local_date: "2026-11-27" };
  i.query.replacements.push({
    record_kind: "FullDayDraft",
    record_id: 11,
    expected_revision: 8,
  });
  p.before.push(old);
  p.cancel_ids = [11];
  const e = api.confirmation(i, p, requestId),
    r = clone(receipt);
  r.confirmation = e.request;
  r.plan = p;
  r.after.push({ ...old, status: "Cancelled", revision: 9 });
  assert.equal(api.verifiedReceipt(e, r), r);
  r.after[1].employee_ids = [];
  assert.throws(() => api.verifiedReceipt(e, r));
});
test("review cannot silently change scope, staffing, dates or notes", () => {
  for (const mutate of [
    (p) => (p.before[0].revision = 2),
    (p) => (p.proposed[0].employee_ids = null),
    (p) => (p.proposed[0].notes = "override"),
    (p) => (p.proposed[0].local_date = "2026-02-30"),
    (p) => (p.proposed[0].id = null),
    (p) => (p.cancel_ids = [10]),
  ]) {
    const p = clone(plan);
    mutate(p);
    assert.throws(() => api.prepared(p, input));
  }
});
test("untrusted native envelope binds its database, two explicit confirmations and original key", () => {
  for (const mutate of [
    (e) => (e.request.profile_id = "wrong"),
    (e) => (e.request.request_id = "../path"),
    (e) => (e.request.confirmed = false),
    (e) => (e.request.pending_acknowledged = false),
    (e) => (e.request.plan_fingerprint = "b".repeat(64)),
  ]) {
    const e = clone(pending);
    mutate(e);
    assert.throws(() => api.envelope(e, profile));
  }
});
test("only exact definite rejection codes can be acknowledged; unknown remains unresolved", () => {
  const rejected = {
    ...flags,
    outcome: "Rejected",
    code: "STALE_OR_CHANGED_EXACT_PLAN",
    request_id: requestId,
    database_identity: profile,
    confirmation: pending.request,
  };
  assert.equal(api.verifiedReceipt(pending, rejected), rejected);
  for (const code of [
    "UNKNOWN",
    "WRONG_DATABASE_IDENTITY",
    "IDEMPOTENCY_PAYLOAD_MISMATCH",
    undefined,
  ])
    assert.throws(() => api.verifiedReceipt(pending, { ...rejected, code }));
});
test("inverse is read-only, exact version-bound, and never enables Restore", () => {
  const v = {
    ...flags,
    readonly: true,
    status: "Current",
    version_id: 6,
    before_restore: [row],
    proposed_restore: [{ ...proposed, expected_current_revision: 3 }],
    restore_enabled: false,
    warnings: ["REVALIDATE_RESOURCES"],
  };
  assert.equal(api.inverse(v, 6), v);
  assert.equal(api.inverse({ ...v, status: "Stale" }, 6).status, "Stale");
  assert.throws(() => api.inverse({ ...v, restore_enabled: true }, 6));
  assert.throws(() => api.inverse(v, 7));
  assert.throws(() => api.inverse({ ...v, status: "Unknown" }, 6));
});
