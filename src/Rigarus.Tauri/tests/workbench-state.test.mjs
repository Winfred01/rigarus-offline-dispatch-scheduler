import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
function sourceUrl(name, imports = {}) {
  let source = stripTypeScriptTypes(
    readFileSync(new URL(`../src/${name}.ts`, import.meta.url), "utf8"),
  );
  for (const [key, url] of Object.entries(imports))
    source = source.replaceAll(`"./${key}"`, JSON.stringify(url));
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}
const {
  savedKey,
  savedKind,
  weekRange,
  revealTypedFilters,
  visitsForCell,
  activeProblems,
} = await import(
  sourceUrl("workbench-state", {
    "assignment-fields": sourceUrl("assignment-fields"),
    week: sourceUrl("week"),
  })
);
const { createLocateCue } = await import(
  sourceUrl("schedule-locate", {
    "assignment-fields": sourceUrl("assignment-fields"),
    week: sourceUrl("week"),
    "working-calendar-fields": sourceUrl("working-calendar-fields"),
  })
);
import { PreviewEpoch } from "../src/day-preview-state.ts";
const day = {
  record_kind: "FullDayDraft",
  id: 1,
  crew_id: 2,
  project_id: 3,
  local_date: "2026-12-31",
  slot: null,
  checks: [
    { check: "Personnel", state: "Blocked" },
    { check: "Driver", state: "Pending" },
    { check: "Calendar", state: "Matched" },
  ],
};
const old = { ...day, record_kind: "LegacyHalfDay", slot: "PM" };
test("equal integers remain distinct saved kinds, never proposal or generic IDs", () => {
  assert.notEqual(savedKey(day), savedKey(old));
  assert.ok(savedKind("FullDayDraft"));
  assert.ok(savedKind("LegacyHalfDay"));
  for (const v of ["Proposal", "Day", null, 1])
    assert.equal(savedKind(v), false);
});
test("week dates cross year, leap and UTC daylight boundaries without slot conversion", () => {
  for (const d of ["2026-12-31", "2028-02-29", "2027-03-14", "2027-11-07"]) {
    const r = weekRange(d);
    assert.equal(r.days.length, 7);
    assert.ok(r.start <= d && d <= r.end);
  }
  assert.equal(weekRange("2026-12-31").start, "2026-12-27");
  assert.equal(weekRange("0001-01-01").start, "0001-01-01");
  assert.equal(weekRange("9999-12-31").end, "9999-12-31");
});
test("cell projection preserves mixed records and exact notes/id metadata, excludes other dates", () => {
  const rows = [old, { ...day, id: 2, local_date: "2027-01-01" }, day];
  const before = structuredClone(rows);
  assert.deepEqual(visitsForCell(rows, "2026-12-31").map(savedKey), [
    savedKey(day),
    savedKey(old),
  ]);
  assert.deepEqual(rows, before);
});
test("typed Locate retains matching filters and clears only hidden target filters", () => {
  assert.deepEqual(revealTypedFilters({ crew: "2", project: "8" }, day), {
    crew: "2",
    project: "",
  });
  assert.deepEqual(revealTypedFilters({ crew: "9", project: "3" }, day), {
    crew: "",
    project: "3",
  });
});
test("matched calendar cannot hide Blocked and missing independent checks", () => {
  assert.deepEqual(
    activeProblems(day).map((c) => c.state),
    ["Blocked", "Pending"],
  );
});
test("same numeric target kinds have independent two-second cue identity", () => {
  let task,
    cancelled = [],
    seen = [];
  const cue = createLocateCue((x) => seen.push(x), {
    schedule: (f, ms) => {
      assert.equal(ms, 2000);
      task = f;
      return seen.length;
    },
    cancel: (i) => cancelled.push(i),
  });
  cue.start(savedKey(day));
  const late = task;
  cue.start(savedKey(old));
  late();
  assert.equal(seen.at(-1), savedKey(old));
  task();
  assert.equal(seen.at(-1), undefined);
  assert.ok(cancelled.length);
});
test("late week or Locate response cannot replace a newer request", () => {
  const e = new PreviewEpoch(),
    week = e.next(),
    locate = e.next();
  assert.equal(e.current(week), false);
  assert.equal(e.current(locate), true);
  e.next();
  assert.equal(e.current(locate), false);
});
