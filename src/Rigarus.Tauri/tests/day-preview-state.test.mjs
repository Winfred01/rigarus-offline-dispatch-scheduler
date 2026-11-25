import test from "node:test";
import assert from "node:assert/strict";
import {
  previewQuery,
  pendingFlags,
  PreviewEpoch,
  reasonLabel,
} from "../src/day-preview-state.ts";

const valid = {
  days: "2",
  confirmed: true,
  crews: [2, 1],
  start: "2026-11-23",
  end: "2026-11-27",
  limit: 3,
};
test("explicit whole-day query preserves stable context, confirmation and order", () => {
  const before = structuredClone(valid);
  const { query } = previewQuery(14, 6, valid, "EarliestFinish");
  assert.equal(query.remaining_days, 2);
  assert.equal(query.remaining_confirmed, true);
  assert.deepEqual(query.crew_ids, [1, 2]);
  assert.equal(query.work_item_id, 14);
  assert.equal(query.expected_project_id, 6);
  assert.equal(query.order, "EarliestFinish");
  assert.ok(!("slot" in query));
  assert.ok(!("estimated_half_days" in query));
  assert.deepEqual(valid, before);
});
test("no estimate, hidden progress deduction, decimal or unconfirmed remaining work", () => {
  for (const days of ["", "0", "-1", "1.5", "2e1", "9007199254740992"]) {
    assert.equal(
      previewQuery(14, 6, { ...valid, days }, "EarliestStart").error.field,
      "days",
    );
  }
  assert.equal(
    previewQuery(14, 6, { ...valid, confirmed: false }, "EarliestStart").error
      .field,
    "confirmed",
  );
  assert.equal(
    previewQuery(14, 6, { ...valid, days: "02" }, "EarliestStart").query
      .remaining_days,
    2,
  );
});
test("date boundaries are inclusive local dates, not timezone instants", () => {
  for (const [start, end] of [
    ["2026-12-31", "2027-01-01"],
    ["2028-02-28", "2028-02-29"],
    ["2027-03-13", "2027-03-15"],
    ["2027-11-06", "2027-11-08"],
    ["9999-12-31", "9999-12-31"],
    ["2028-01-01", "2028-12-31"],
  ]) {
    assert.ok(
      previewQuery(14, 6, { ...valid, start, end }, "EarliestFinish").query,
    );
  }
  for (const [start, end] of [
    ["0000-01-01", "0000-01-01"],
    ["2027-02-29", "2027-03-01"],
    ["2028-01-01", "2029-01-01"],
    ["2026-11-28", "2026-11-27"],
    ["2026-11-23T00:00:00Z", "2026-11-27"],
  ]) {
    assert.ok(
      previewQuery(14, 6, { ...valid, start, end }, "EarliestFinish").error,
    );
  }
});
test("candidate IDs and configurable limit are strict", () => {
  for (const crews of [
    [],
    [true],
    [1, 1],
    [0],
    Array.from({ length: 101 }, (_, i) => i + 1),
  ]) {
    assert.equal(
      previewQuery(14, 6, { ...valid, crews }, "EarliestFinish").error.field,
      "crews",
    );
  }
  for (const limit of [0, 11, 1.5])
    assert.equal(
      previewQuery(14, 6, { ...valid, limit }, "EarliestFinish").error.field,
      "limit",
    );
  assert.ok(previewQuery(0, 6, valid, "EarliestFinish").error);
});
test("positive or unknown safety flags fail closed instead of enabling a result", () => {
  const flags = {
    unit: "FullDay",
    validation_status: "Pending",
    applyable: false,
    publishable: false,
  };
  assert.equal(pendingFlags(flags), true);
  for (const x of [
    null,
    {},
    { ...flags, unit: "AM" },
    { ...flags, applyable: true },
    { ...flags, publishable: true },
    { ...flags, validation_status: "Confirmed" },
  ])
    assert.equal(pendingFlags(x), false);
});
test("late replies lose authority after input change, close or newer request", () => {
  const requests = new PreviewEpoch(),
    proofs = new PreviewEpoch();
  const old = requests.next();
  const newer = requests.next();
  assert.equal(requests.current(old), false);
  assert.equal(requests.current(newer), true);
  const proof = proofs.next();
  proofs.next();
  assert.equal(proofs.current(proof), false);
  assert.equal(requests.current(newer), true); // focus recheck cannot cancel a preview and leave it busy
  requests.next();
  assert.equal(requests.current(newer), false);
});
test("machine reasons have readable text without inventing a pass", () => {
  assert.equal(reasonLabel("CREW_CALENDAR_UNKNOWN"), "crew calendar unknown");
  assert.equal(reasonLabel("ApprovedDriver"), "approved driver");
  assert.equal(
    reasonLabel("CONSTRAINT_BLOCKED:RigConflicts"),
    "constraint blocked: rig conflicts",
  );
});
