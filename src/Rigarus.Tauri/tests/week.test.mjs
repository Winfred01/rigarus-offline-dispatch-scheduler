import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import { spawnSync } from "node:child_process";
import test from "node:test";

const source = stripTypeScriptTypes(
  readFileSync(new URL("../src/week.ts", import.meta.url), "utf8"),
);
const url = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const { weekDays, shiftDay, inWeek } = await import(url);

test("Sunday–Saturday includes weekends and crosses the calendar year", () => {
  const days = weekDays("2027-01-01");
  assert.deepEqual(days, [
    "2026-12-27",
    "2026-12-28",
    "2026-12-29",
    "2026-12-30",
    "2026-12-31",
    "2027-01-01",
    "2027-01-02",
  ]);
  assert.equal(inWeek("2027-01-02", days), true);
  assert.equal(inWeek("2027-01-03", days), false);
  assert.deepEqual(weekDays("2026-12-27"), days);
  assert.equal(shiftDay("2026-12-31", 1), "2027-01-01");
  assert.equal(shiftDay("2024-02-28", 1), "2024-02-29");
});

test("week navigation does not lose a day at DST or depend on host timezone", () => {
  for (const tz of ["America/Toronto", "Asia/Tokyo", "Pacific/Auckland"]) {
    const result = spawnSync(
      process.execPath,
      [
        "--input-type=module",
        "-e",
        `const {weekDays,shiftDay}=await import(${JSON.stringify(url)}); console.log(JSON.stringify([weekDays('2026-03-11'),shiftDay('2026-11-01',7)]))`,
      ],
      { env: { ...process.env, TZ: tz }, encoding: "utf8" },
    );
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(JSON.parse(result.stdout), [
      [
        "2026-03-08",
        "2026-03-09",
        "2026-03-10",
        "2026-03-11",
        "2026-03-12",
        "2026-03-13",
        "2026-03-14",
      ],
      "2026-11-08",
    ]);
  }
});

test("calendar counter retains low years and does not wrap at supported storage limits", () => {
  assert.equal(shiftDay("0001-01-01", 0), "0001-01-01");
  assert.equal(shiftDay("9999-12-31", 0), "9999-12-31");
  assert.equal(weekDays("0001-01-01").length, 7);
  assert.equal(weekDays("9999-12-31").length, 7);
  assert.equal(weekDays("9999-12-31")[6], "+010000-01-01");
});
