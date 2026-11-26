import test from "node:test";
import assert from "node:assert/strict";
import { ImpactFreshness, sameImpactScope } from "../src/impact-state.ts";

test("a stale observed proposal cannot become Current after source reversion or focus", () => {
  const session = new ImpactFreshness();
  assert.equal(session.observe("Current"), "Current");
  assert.equal(session.observe("Stale"), "Stale");
  assert.equal(session.observe("Current"), "Stale");
  session.recompute();
  assert.equal(session.observe("Current"), "Current");
});
test("scope edits retire results and errors never certify Current", () => {
  const session = new ImpactFreshness();
  session.invalidate();
  assert.equal(session.observe("Current"), "Stale");
  assert.throws(() => session.observe("Unavailable"));
  assert.equal(session.stale, true);
});
test("replacement scope binds typed identity and revision, independently of list order", () => {
  const a = { record_kind: "FullDayDraft", record_id: 1, expected_revision: 2 };
  const b = { ...a, record_id: 2 };
  const selected = [a, b],
    before = structuredClone(selected);
  assert.equal(sameImpactScope([b, a], selected), true);
  assert.deepEqual(selected, before);
  for (const changed of [
    [a],
    [a, a],
    [a, { ...b, expected_revision: 3 }],
    [a, { ...b, record_kind: "LegacyHalfDay" }],
    [a, { ...b, record_id: true }],
    [a, { ...b, expected_revision: 0 }],
  ])
    assert.equal(sameImpactScope(changed, selected), false);
});
test("empty replacement scope means no implicit saved-record release", () => {
  assert.equal(sameImpactScope([], []), true);
  assert.equal(
    sameImpactScope(
      [{ record_kind: "FullDayDraft", record_id: 1, expected_revision: 1 }],
      [],
    ),
    false,
  );
  assert.equal(sameImpactScope(null, []), false);
});
