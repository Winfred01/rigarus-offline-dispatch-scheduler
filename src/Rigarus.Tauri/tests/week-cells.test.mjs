import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";

async function sourceModule(name) {
  const source = stripTypeScriptTypes(
    readFileSync(new URL(`../src/${name}.ts`, import.meta.url), "utf8"),
  );
  return import(
    `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
  );
}
const { weekCells } = await sourceModule("week-cells");
const { weekDays } = await sourceModule("week");
const days = weekDays("2027-01-01");
function visit(id, date, slot, changes = {}) {
  return {
    id,
    local_date: date,
    slot,
    work_item_id: 10,
    project_id: 2,
    crew_id: 3,
    notes: "Synthetic same note",
    status: "Draft",
    revision: 1,
    job_number: "SYN-SPAN",
    site_id: "0002",
    site_name: "Synthetic spanning site",
    work_type: "Civil",
    required_crew_count: 1,
    estimated_half_days: 10,
    crew_name: "Synthetic Civil",
    crew_active: true,
    validation_status: "Pending",
    publishable: false,
    ...changes,
  };
}
function fullDay(date, firstId = 1, changes = {}) {
  return [
    visit(firstId, date, "AM", changes),
    visit(firstId + 1, date, "PM", changes),
  ];
}
const strips = (cells) => cells.filter((cell) => cell.dates.length > 1);
const ids = (cells) =>
  cells.flatMap((cell) => cell.assignments.map((row) => row.id));

test("a cross-year strip retains all four stored source records in date/slot order", () => {
  const rows = [...fullDay("2026-12-31"), ...fullDay("2027-01-01", 3)];
  const cells = weekCells(days, rows);
  assert.equal(strips(cells).length, 1);
  assert.deepEqual(strips(cells)[0].dates, ["2026-12-31", "2027-01-01"]);
  assert.equal(strips(cells)[0].start, 4);
  assert.deepEqual(ids(cells), [1, 2, 3, 4]);
  assert.equal(strips(cells)[0].assignments[2], rows[2]);
});

test("one full day and a missing PM remain independent instead of inventing occupancy", () => {
  const rows = [...fullDay("2026-12-31"), visit(3, "2027-01-01", "AM")];
  const cells = weekCells(days, rows);
  assert.equal(strips(cells).length, 0);
  assert.equal(cells.length, 7);
  assert.deepEqual(ids(cells), [1, 2, 3]);
  assert.equal(strips(weekCells(days, fullDay("2026-12-31"))).length, 0);
});

test("empty calendar days split visits; saved weekend pairs can span", () => {
  const separated = [...fullDay("2026-12-30"), ...fullDay("2027-01-01", 3)];
  assert.equal(strips(weekCells(days, separated)).length, 0);
  const weekend = weekCells(days, [
    ...fullDay("2027-01-01"),
    ...fullDay("2027-01-02", 3),
  ]);
  assert.deepEqual(strips(weekend)[0].dates, ["2027-01-01", "2027-01-02"]);
});

test("different WorkItems, Crews, Projects or exact notes are never combined", () => {
  for (const change of [
    { work_item_id: 11 },
    { crew_id: 4 },
    { project_id: 5 },
    { notes: "Different note" },
    { notes: "Synthetic same note " },
  ]) {
    const rows = [
      ...fullDay("2026-12-31"),
      ...fullDay("2027-01-01", 3, change),
    ];
    assert.equal(
      strips(weekCells(days, rows)).length,
      0,
      JSON.stringify(change),
    );
  }
  const mixedPair = [
    visit(1, "2026-12-31", "AM"),
    visit(2, "2026-12-31", "PM", { notes: "Changed" }),
    ...fullDay("2027-01-01", 3),
  ];
  assert.equal(strips(weekCells(days, mixedPair)).length, 0);
});

test("parallel project-row jobs remain separate cards without hiding either Crew", () => {
  const rows = [
    ...fullDay("2026-12-31"),
    ...fullDay("2027-01-01", 3),
    visit(5, "2027-01-01", "AM", { crew_id: 9 }),
  ];
  const cells = weekCells(days, rows);
  assert.equal(strips(cells).length, 0);
  assert.deepEqual(ids(cells), [1, 2, 3, 5, 4]);
});

test("editing or cancelling one visit splits presentation while retaining remaining IDs", () => {
  const rows = [...fullDay("2026-12-31"), ...fullDay("2027-01-01", 3)];
  const edited = rows.map((row) =>
    row.id === 4 ? { ...row, notes: "Edited only PM", revision: 2 } : row,
  );
  assert.equal(strips(weekCells(days, edited)).length, 0);
  assert.deepEqual(ids(weekCells(days, edited)), [1, 2, 3, 4]);
  const cancelled = rows.map((row) =>
    row.id === 3 ? { ...row, status: "Cancelled", revision: 2 } : row,
  );
  assert.equal(strips(weekCells(days, cancelled)).length, 0);
  assert.deepEqual(ids(weekCells(days, cancelled)), [1, 2, 4]);
  assert.equal(
    strips(
      weekCells(
        days,
        rows.map((row) => ({ ...row, revision: row.id })),
      ),
    ).length,
    1,
  );
});

test("week boundaries clip source dates without borrowing another week's records", () => {
  const rows = [...fullDay("2027-01-02"), ...fullDay("2027-01-03", 3)];
  assert.equal(strips(weekCells(days, rows)).length, 0);
  assert.deepEqual(ids(weekCells(days, rows)), [1, 2]);
  assert.equal(strips(weekCells(weekDays("2027-01-03"), rows)).length, 0);
  assert.deepEqual(ids(weekCells(weekDays("2027-01-03"), rows)), [3, 4]);
});

test("a full seven-date strip is stable for unordered input and does not mutate records", () => {
  const rows = days
    .flatMap((date, index) => fullDay(date, index * 2 + 1))
    .reverse();
  const before = structuredClone(rows);
  const cells = weekCells(days, rows);
  assert.equal(cells.length, 1);
  assert.equal(cells[0].dates.length, 7);
  assert.deepEqual(
    ids(cells),
    Array.from({ length: 14 }, (_, i) => i + 1),
  );
  assert.deepEqual(rows, before);
  assert.equal(
    rows.every(
      (row) => row.publishable === false && row.validation_status === "Pending",
    ),
    true,
  );
});
