import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";

const source = readFileSync(
  new URL("../src/work-item-validation.ts", import.meta.url),
  "utf8",
);
const { validateWorkItemCounts, workItemCountError } = await import(
  `data:text/javascript;base64,${Buffer.from(stripTypeScriptTypes(source)).toString("base64")}`
);

test("zero crews marks only Required crews and chooses that input", () => {
  const checked = validateWorkItemCounts([
    { key: 4, crews: "0", halfDays: "2" },
  ]);
  assert.deepEqual(checked, {
    errors: {
      4: { crews: "Required crews must be a whole number of at least 1." },
    },
    first: { key: 4, field: "crews" },
  });
});

test("fractional half-days marks only Estimated half-days", () => {
  const checked = validateWorkItemCounts([
    { key: 4, crews: "2", halfDays: "1.5" },
  ]);
  assert.deepEqual(checked, {
    errors: {
      4: {
        halfDays: "Estimated half-days must be a whole number of at least 1.",
      },
    },
    first: { key: 4, field: "halfDays" },
  });
});

test("both errors remain distinct; first error follows visible row/field order", () => {
  const draft = Object.freeze([
    Object.freeze({ key: 9, crews: "2", halfDays: "" }),
    Object.freeze({ key: 2, crews: "0", halfDays: "1.5" }),
  ]);
  const checked = validateWorkItemCounts(draft);
  assert.deepEqual(checked.first, { key: 9, field: "halfDays" });
  assert.deepEqual(Object.keys(checked.errors[2]), ["crews", "halfDays"]);
  assert.match(checked.errors[2].crews, /^Required crews/);
  assert.match(checked.errors[2].halfDays, /^Estimated half-days/);
  assert.equal(draft[1].crews, "0");
});

test("correction clears only that field; other draft values and stable keys remain", () => {
  const checked = validateWorkItemCounts([
    { key: 9, crews: "2", halfDays: "1.5" },
    { key: 12, crews: "3", halfDays: "4" },
  ]);
  assert.equal(checked.errors[9].crews, undefined);
  assert.ok(checked.errors[9].halfDays);
  assert.equal(checked.errors[12], undefined);
  assert.deepEqual(
    validateWorkItemCounts([{ key: 9, crews: "2", halfDays: "4" }]),
    { errors: {}, first: undefined },
  );
});

test("whole-number syntax and existing Int32 limit are preserved", () => {
  for (const value of ["", "-1", "1.5", "1e2", "Infinity", "abc", "0"])
    assert.ok(workItemCountError(value, "crews"));
  for (const value of ["1", " +2 ", "0002", "2147483647"])
    assert.equal(workItemCountError(value, "crews"), undefined);
  assert.match(workItemCountError("2147483648", "halfDays"), /2147483647/);
  assert.match(workItemCountError("9".repeat(400), "crews"), /2147483647/);
  assert.deepEqual(validateWorkItemCounts([]), {
    errors: {},
    first: undefined,
  });
});
