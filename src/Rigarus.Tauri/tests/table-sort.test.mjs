import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";

const source = readFileSync(
  new URL("../src/table-sort.ts", import.meta.url),
  "utf8",
);
const outputText = stripTypeScriptTypes(source);
const { nextSort, sortRows } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);
const ids = (rows) => rows.map((row) => row.id);

test("new columns ascend, repeated clicks toggle, tables keep separate states", () => {
  let projects = nextSort(undefined, "job_number");
  const workItems = nextSort(undefined, "estimated_half_days");
  assert.equal(projects.direction, "ascending");
  projects = nextSort(projects, "job_number");
  assert.equal(projects.direction, "descending");
  assert.equal(workItems.direction, "ascending");
  assert.equal(nextSort(projects, "site_id").direction, "ascending");
  assert.equal(nextSort(projects, "job_number").direction, "ascending");
});

test("crews, half-days (2 versus 10 days) and item counts use numerical order", () => {
  const rows = [
    { id: 1, crews: 10, halfDays: 20, count: 10 },
    { id: 2, crews: 2, halfDays: 4, count: 2 },
    { id: 3, crews: 1, halfDays: 1, count: 1 },
  ];
  for (const key of ["crews", "halfDays", "count"]) {
    const ascending = nextSort(undefined, key);
    assert.deepEqual(ids(sortRows(rows, ascending)), [3, 2, 1]);
    assert.deepEqual(ids(sortRows(rows, nextSort(ascending, key))), [1, 2, 3]);
  }
});

test("identifiers retain leading zeroes and text order; all text columns toggle", () => {
  const rows = [
    { id: 1, job: "SYN-2", site: "02", name: "Zulu yard", type: "Tower" },
    { id: 2, job: "SYN-10", site: "10", name: "Alpha yard", type: "Civil" },
  ];
  for (const [key, expected] of [
    ["job", [2, 1]],
    ["site", [1, 2]],
    ["name", [2, 1]],
    ["type", [2, 1]],
  ]) {
    const ascending = nextSort(undefined, key);
    assert.deepEqual(ids(sortRows(rows, ascending)), expected);
    assert.deepEqual(
      ids(sortRows(rows, nextSort(ascending, key))),
      [...expected].reverse(),
    );
  }
  assert.equal(rows[0].site, "02");
});

test("equal values have deterministic ID order without mutating source or selection", () => {
  const rows = Object.freeze([
    Object.freeze({ id: 9, name: "same" }),
    Object.freeze({ id: 2, name: "Same" }),
  ]);
  const selected = rows[0];
  for (const direction of ["ascending", "descending"]) {
    const sorted = sortRows(rows, { key: "name", direction });
    assert.deepEqual(ids(sorted), [2, 9]);
    assert.equal(
      sorted.find((row) => row.id === selected.id),
      selected,
    );
  }
  assert.deepEqual(ids(rows), [9, 2]);
  assert.deepEqual(ids(sortRows(rows, undefined)), [9, 2]);
  assert.deepEqual(sortRows([], { key: "name", direction: "ascending" }), []);
});

test("sorting an already filtered subset neither restores excluded rows nor loses matches", () => {
  const all = [
    { id: 1, name: "Keep Z" },
    { id: 2, name: "Excluded" },
    { id: 3, name: "Keep A" },
  ];
  const filtered = all.filter((row) => row.name.startsWith("Keep"));
  const sort = nextSort(undefined, "name");
  assert.deepEqual(ids(sortRows(filtered, sort)), [3, 1]);
  assert.deepEqual(ids(sortRows(filtered, nextSort(sort, "name"))), [1, 3]);
});
