import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import { createHash } from "node:crypto";
const url = (text) =>
  `data:text/javascript;base64,${Buffer.from(stripTypeScriptTypes(text)).toString("base64")}`;
const applyUrl = url(
  readFileSync(
    new URL("../src/draft-confirmation-state.ts", import.meta.url),
    "utf8",
  ),
);
const apply = await import(applyUrl);
const api = await import(
  url(
    readFileSync(
      new URL("../src/draft-restore-state.ts", import.meta.url),
      "utf8",
    ).replaceAll('"./draft-confirmation-state"', JSON.stringify(applyUrl)),
  )
);
const flags = {
  validation_status: "Pending",
  applyable: false,
  publishable: false,
};
const profile = "11111111-1111-4111-8111-111111111111",
  key = "22222222-2222-4222-8222-222222222222",
  sha = "a".repeat(64);
const row = {
  record_kind: "FullDayDraft",
  id: 10,
  revision: 3,
  work_item_id: 1,
  project_id: 2,
  crew_id: 4,
  local_date: "2026-11-26",
  notes: "Synthetic café note",
  status: "Draft",
  employee_ids: [8],
};
const proposed = { ...row };
delete proposed.revision;
const input = apply.planInput(
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
const oldPlan = {
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
    checks: [],
    notes: [],
    missing_evidence: [],
    locks: "Unsupported",
    downstream: "Unsupported",
  },
  affected_crew_ids: [4],
  affected_work_item_ids: [1],
  confirmed_remaining_days: 1,
};
const observation = {
  ...row,
  ...flags,
  staffing_configured: true,
  workers: [{ id: 8 }],
  actual_rig_id: null,
  checks: [{ check: "Driver", state: "Pending", reasons: ["NotRecorded"] }],
};
delete observation.employee_ids;
delete observation.status;
const source = {
  outcome: "Committed",
  ...flags,
  request_id: key,
  database_identity: profile,
  confirmation: apply.confirmation(input, oldPlan, key).request,
  version_id: 6,
  recorded_at: "2026-11-26T12:00:00Z",
  plan: oldPlan,
  after: [row],
  observations: [observation],
};
const after = { ...row, revision: 4 };
const checks = [
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
].map((check) => ({ check, state: "Pending", reasons: ["NotRecorded"] }));
const digest = (v) =>
  createHash("sha256").update(apply.canonical(v)).digest("hex");
const warning = {
  record_kind: "FullDayDraft",
  record_id: 10,
  local_date: row.local_date,
  check: "ApprovedDriver",
  state: "Pending",
  reason: "NotRecorded",
};
const global = {
  record_kind: "DraftRestore",
  check: "LOCK_POLICY_UNSUPPORTED",
  state: "Pending",
  reason: "LOCK_POLICY_UNSUPPORTED",
};
const plan = {
  format: "rigarus-draft-restore-v1",
  ...flags,
  database_identity: profile,
  source_record_kind: "DraftVersion",
  source_version_id: 6,
  source_fingerprint: digest(source),
  before_restore: [row],
  proposed_restore: [after],
  observations: [{ ...observation, revision: 4, checks }],
  warnings: [warning, global].map((w) => ({ warning_id: digest(w), ...w })),
  blockers: [],
  status: "Current",
  production_writes_enabled: false,
};
plan.plan_fingerprint = digest(plan);
const bundle = { source, reviewed: plan };
const pending = api.confirmation(
  bundle,
  plan.warnings.map((w) => w.warning_id),
  key,
  true,
);
const committed = {
  outcome: "Committed",
  ...flags,
  record_kind: "DraftRestoreVersion",
  version_id: 1,
  database_identity: profile,
  request_id: key,
  source_record_kind: "DraftVersion",
  source_version_id: 6,
  plan,
  after: [after],
  observations: plan.observations,
  confirmation: pending.request,
  recorded_at: "2026-11-27T12:00:00Z",
};
const clone = (v) => structuredClone(v);

test("original/current/inverse values retain type, staff, notes and new revision", () => {
  assert.equal(api.prepared(bundle, profile, 6), bundle);
  assert.equal(api.receipt(pending, committed), committed);
  assert.equal(source.after[0].revision, 3);
  assert.equal(committed.after[0].revision, 4);
  assert.deepEqual(committed.after[0].employee_ids, [8]);
  assert.equal(committed.after[0].notes, row.notes);
});
test("each exact Pending item must be explicitly acknowledged, never a bulk substitute", () => {
  for (const ids of [
    [],
    [plan.warnings[0].warning_id],
    [...pending.request.acknowledged_warning_ids, sha],
    [plan.warnings[0].warning_id, plan.warnings[0].warning_id],
  ])
    assert.throws(() => api.confirmation(bundle, ids, key, true));
  assert.throws(() =>
    api.confirmation(
      bundle,
      pending.request.acknowledged_warning_ids,
      key,
      false,
    ),
  );
});
test("Blocked or changed source/proposal cannot create a submission envelope", () => {
  for (const mutate of [
    (b) => {
      b.reviewed.status = "Blocked";
      b.reviewed.blockers = [{ state: "Blocked" }];
    },
    (b) => (b.reviewed.before_restore[0].notes = "later edit"),
    (b) => (b.reviewed.proposed_restore[0].revision = 3),
    (b) => (b.reviewed.proposed_restore[0].record_kind = "LegacyHalfDay"),
    (b) => (b.reviewed.proposed_restore[0].employee_ids = []),
    (b) => (b.reviewed.source_version_id = 1),
    (b) => b.reviewed.before_restore.push(clone(row)),
  ]) {
    const b = clone(bundle);
    mutate(b);
    assert.throws(() =>
      api.confirmation(b, pending.request.acknowledged_warning_ids, key, true),
    );
  }
});
test("full receipt match rejects altered identity, source, plan, fields and safety flags", () => {
  for (const mutate of [
    (r) => (r.request_id = profile),
    (r) => (r.database_identity = key),
    (r) => (r.source_record_kind = "DraftRestoreVersion"),
    (r) => (r.source_version_id = 1),
    (r) => (r.record_kind = "DraftVersion"),
    (r) => (r.confirmation.acknowledged_warning_ids = []),
    (r) => (r.plan.warnings = []),
    (r) => (r.after[0].employee_ids = []),
    (r) => (r.after[0].notes = "wrong"),
    (r) => (r.after[0].revision = 3),
    (r) => (r.after[0].status = "Cancelled"),
    (r) => (r.publishable = true),
    (r) => (r.applyable = true),
    (r) => (r.validation_status = "Passed"),
    (r) => (r.recorded_at = "bad"),
    (r) => (r.version_id = 0),
    (r) => delete r.after,
    (r) => (r.observations = []),
  ]) {
    const r = clone(committed);
    mutate(r);
    assert.throws(() => api.receipt(pending, r));
  }
});
test("missing or malformed resources never become passed evidence", () => {
  for (const mutate of [
    (b) => (b.reviewed.observations[0].workers = []),
    (b) => (b.reviewed.observations[0].checks = []),
    (b) => (b.reviewed.observations[0].checks[0].state = "Unknown"),
    (b) => (b.reviewed.observations[0].publishable = true),
    (b) => (b.reviewed.warnings[0].record_id = 999),
    (b) => (b.reviewed.warnings[0].state = "Satisfied"),
  ]) {
    const b = clone(bundle);
    mutate(b);
    assert.throws(() => api.prepared(b, profile, 6));
  }
});
test("typed original version rejects equal integer recovery/legacy source identities", () => {
  for (const kind of [
    "LegacyHalfDay",
    "DraftRestoreVersion",
    "PublishedSnapshot",
  ]) {
    const p = clone(pending);
    p.request.source_record_kind = kind;
    assert.throws(() => api.envelope(p, profile));
  }
  for (const id of ["", "0", "-1", "1.5", "1e3", "9007199254740992", "../1"])
    assert.throws(() => api.versionId(id));
  assert.equal(api.versionId("6"), 6);
});
test("known sealed rejection is distinct from missing, bare or fabricated failure", () => {
  const rejected = { ...committed, outcome: "Rejected", code: "Stale" };
  delete rejected.after;
  delete rejected.plan;
  delete rejected.observations;
  delete rejected.version_id;
  assert.equal(api.receipt(pending, rejected), rejected);
  for (const r of [
    { outcome: "NotFound" },
    { detail: "Stale" },
    { ...rejected, code: "UNKNOWN_STORAGE" },
    { ...rejected, confirmation: {} },
  ])
    assert.throws(() => api.receipt(pending, r));
  assert.equal(api.notFound({ outcome: "NotFound", ...flags }), true);
  assert.equal(api.notFound({ outcome: "NotFound" }), false);
});
test("reopened original key/body is immutable and operation-isolated", () => {
  assert.equal(api.envelope(clone(pending), profile).request.request_id, key);
  for (const mutate of [
    (p) => (p.operation = "DraftApply"),
    (p) => (p.format = "old"),
    (p) => (p.request.profile_id = key),
    (p) => (p.request.confirmed = false),
    (p) => (p.request.plan_fingerprint = sha),
  ]) {
    const p = clone(pending);
    mutate(p);
    assert.throws(() => api.envelope(p, profile));
  }
});
test("closed gate and pending foreign operation are explicit rather than safety approval", () => {
  const s = {
    ...flags,
    database_identity: profile,
    test_writes_enabled: false,
    production_writes_enabled: false,
    pending: null,
    other_operation_pending: true,
  };
  assert.equal(api.status(s), s);
  for (const change of [
    { production_writes_enabled: true },
    { test_writes_enabled: "true" },
    { other_operation_pending: undefined },
    { pending: { operation: "Apply" } },
    { publishable: true },
  ])
    assert.throws(() => api.status({ ...s, ...change }));
});
test("close and newer operation invalidate late responses without replacing a request", () => {
  const epoch = new api.RestoreEpoch();
  const first = epoch.next();
  assert.equal(epoch.current(first), true);
  const reopened = epoch.next();
  assert.equal(epoch.current(first), false);
  assert.equal(epoch.current(reopened), true);
  epoch.next();
  assert.equal(epoch.current(reopened), false);
  assert.equal(pending.request.request_id, key);
});
test("Cancelled inverse additions remain visible as typed historical rows", () => {
  const b = clone(bundle);
  b.source.plan.before = [];
  b.reviewed.proposed_restore[0].status = "Cancelled";
  // A genuine source addition has no old row; original plan must also classify it as new.
  b.source.plan.proposed[0].id = null;
  b.source.after[0].id = 11;
  b.source.after[0].revision = 1;
  b.source.observations[0].id = 11;
  b.source.observations[0].revision = 1;
  b.source.confirmation.plan.query.replacements = [];
  b.source.confirmation.plan.notes = row.notes;
  b.source.plan.cancel_ids = [];
  b.reviewed.before_restore = clone(b.source.after);
  b.reviewed.proposed_restore = [
    { ...b.source.after[0], status: "Cancelled", revision: 2 },
  ];
  b.reviewed.observations = [];
  b.reviewed.warnings = [clone(plan.warnings[1])];
  assert.equal(api.prepared(b, profile, 6), b);
});

test("retained review shows original acknowledgements without claiming a live current read", () => {
  const fresh = api.reviewContext(bundle, undefined, undefined, [], false);
  assert.equal(fresh.title, "Current");
  assert.match(fresh.caption, /Current at preparation/);
  assert.deepEqual(fresh.acknowledged, []);
  const retained = api.reviewContext(bundle, pending, undefined, [], false);
  assert.equal(retained.title, "Retained review");
  assert.match(retained.caption, /not a current database read/);
  assert.deepEqual(
    retained.acknowledged,
    pending.request.acknowledged_warning_ids,
  );
  assert.equal(retained.confirmed, true);
  const archived = api.reviewContext(bundle, undefined, committed, [], false);
  assert.deepEqual(archived, retained);
  assert.equal(pending.request.request_id, key);
});

test("committed restore survives failed read refresh without a second write", async () => {
  const before = clone(committed);
  let reads = 0;
  assert.equal(
    await api.refreshRestored(committed, async (selected) => {
      ++reads;
      assert.deepEqual(selected, committed.after[0]);
      throw new Error("synthetic read timeout");
    }),
    false,
  );
  assert.deepEqual(committed, before);
  assert.equal(
    await api.refreshRestored(committed, async () => {
      ++reads;
      return true;
    }),
    true,
  );
  assert.equal(reads, 2);
  assert.deepEqual(committed, before);
  await assert.rejects(() =>
    api.refreshRestored({ outcome: "Rejected" }, async () => true),
  );
});
