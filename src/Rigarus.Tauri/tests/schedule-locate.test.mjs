import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";

function sourceUrl(name, imports = {}) {
  let source = stripTypeScriptTypes(
    readFileSync(new URL(`../src/${name}.ts`, import.meta.url), "utf8"),
  );
  for (const [name, url] of Object.entries(imports))
    source = source.replaceAll(`"./${name}"`, JSON.stringify(url));
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}
const helper = await import(
  sourceUrl("schedule-locate", {
    "assignment-fields": sourceUrl("assignment-fields"),
    week: sourceUrl("week"),
    "working-calendar-fields": sourceUrl("working-calendar-fields"),
  })
);
const {
  locateProblem,
  locateWeek,
  revealFilters,
  reviewFeedback,
  locateScroll,
  createLocateCue,
} = helper;
const row = {
  id: 81,
  status: "Draft",
  local_date: "2027-01-01",
  slot: "PM",
  crew_id: 4,
  project_id: 12,
  crew_active: true,
  staffing: { configured: true, workers: [{ employee_id: 2 }] },
  calendar_assessment: {
    status: "Matched",
    crew_state: "Working",
    work_item_state: "Working",
    project_id: 12,
  },
};

test("Locate uses the exact saved ID and current local Sunday week across year/leap/DST", () => {
  assert.equal(locateProblem(81, row), "");
  assert.notEqual(locateProblem(82, row), "");
  assert.equal(locateWeek(row.local_date), "2026-12-27");
  assert.equal(locateWeek("2028-02-29"), "2028-02-27");
  assert.equal(locateWeek("2027-03-14"), "2027-03-14");
  assert.equal(locateWeek("0001-01-01"), "0001-01-01");
  assert.equal(locateWeek("9999-12-31"), "9999-12-26");
  const am = { ...row, id: 80, slot: "AM" };
  assert.equal(locateProblem(80, am), "");
  assert.notEqual(locateProblem(81, am), "");
});

test("unavailable, cancelled, paused, malformed or wrong records never produce a valid Locate", () => {
  for (const value of [
    undefined,
    { ...row, status: "Cancelled" },
    { ...row, status: "Paused" },
    { ...row, status: "Published" },
    { ...row, local_date: "2027-02-29" },
  ])
    assert.notEqual(locateProblem(81, value), "");
  for (const id of [0, -1, 1.5, NaN, Number.MAX_SAFE_INTEGER + 1])
    assert.notEqual(locateProblem(id, row), "");
});

test("only filters blocking the target are reset", () => {
  assert.deepEqual(revealFilters({ crew: "4", project: "12" }, row), {
    crew: "4",
    project: "12",
  });
  assert.deepEqual(revealFilters({ crew: "5", project: "12" }, row), {
    crew: "",
    project: "12",
  });
  assert.deepEqual(revealFilters({ crew: "4", project: "13" }, row), {
    crew: "4",
    project: "",
  });
  assert.deepEqual(revealFilters({ crew: "", project: "" }, row), {
    crew: "",
    project: "",
  });
});

test("review feedback comes only from recorded calendar/staffing/Crew observations", () => {
  assert.deepEqual(reviewFeedback(row), []);
  assert.match(
    reviewFeedback({ ...row, staffing: undefined })[0],
    /not assigned/,
  );
  assert.match(
    reviewFeedback({ ...row, staffing: { configured: true, workers: [] } })[0],
    /explicitly empty/,
  );
  assert.match(
    reviewFeedback({ ...row, calendar_assessment: undefined })[0],
    /not loaded/,
  );
  const conflict = reviewFeedback({
    ...row,
    calendar_assessment: {
      ...row.calendar_assessment,
      status: "Blocked",
      crew_state: "NotWorking",
    },
  });
  assert.match(conflict[0], /Calendar conflict.*Cannot work/);
  assert.equal(
    conflict.some((value) => /driver|maintenance|qualification/i.test(value)),
    false,
  );
  assert.deepEqual(reviewFeedback({ ...row, crew_active: false }), [
    "Crew is inactive.",
  ]);
  assert.equal(row.calendar_assessment.status, "Matched");
});

test("centering scrolls the inner viewport around sticky header and roster with bounds", () => {
  const viewport = { top: 100, left: 20, width: 500, height: 300 };
  const card = { top: 800, left: 900, width: 100, height: 50 };
  const scroll = { top: 0, left: 0, width: 2000, height: 2000 };
  const sticky = { top: 60, left: 100 };
  assert.deepEqual(locateScroll(viewport, card, scroll, sticky), {
    top: 545,
    left: 630,
  });
  assert.deepEqual(
    locateScroll(viewport, { ...card, top: -900, left: -900 }, scroll, sticky),
    { top: 0, left: 0 },
  );
  assert.deepEqual(
    locateScroll(viewport, { ...card, top: 5000, left: 5000 }, scroll, sticky),
    { top: 1700, left: 1500 },
  );
  assert.deepEqual(
    locateScroll(
      viewport,
      { ...card, width: 600, height: 400 },
      scroll,
      sticky,
    ),
    { top: 640, left: 780 },
  );
});

function fakeCue() {
  let id = 0;
  const callbacks = new Map();
  const cancelled = [];
  const changes = [];
  const delays = [];
  const cue = createLocateCue((value) => changes.push(value), {
    schedule(run, ms) {
      callbacks.set(++id, run);
      delays.push(ms);
      return id;
    },
    cancel(value) {
      cancelled.push(value);
    },
  });
  return { cue, callbacks, cancelled, changes, delays };
}
test("the highlight expires after 2000ms and a previous callback cannot clear the next target", () => {
  const { cue, callbacks, cancelled, changes, delays } = fakeCue();
  cue.start(80);
  cue.start(81);
  assert.deepEqual(delays, [2000, 2000]);
  assert.deepEqual(cancelled, [1]);
  callbacks.get(1)();
  assert.deepEqual(changes, [80, 81]);
  callbacks.get(2)();
  assert.deepEqual(changes, [80, 81, undefined]);
});
test("repeat Locate of the same card restarts its cue; cleanup prevents late writes", () => {
  const { cue, callbacks, changes, cancelled } = fakeCue();
  cue.start(80);
  cue.clear();
  cue.start(80);
  cue.dispose();
  callbacks.get(1)();
  callbacks.get(2)();
  assert.deepEqual(changes, [80, undefined, 80]);
  assert.deepEqual(cancelled, [1, 2]);
});
