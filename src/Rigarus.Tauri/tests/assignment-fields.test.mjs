import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import { spawnSync } from "node:child_process";
import test from "node:test";

const source = stripTypeScriptTypes(
  readFileSync(new URL("../src/assignment-fields.ts", import.meta.url), "utf8"),
);
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const { validLocalDate, assignmentFailureNeedsReload } = await import(
  moduleUrl
);

test("Gregorian local dates include leap years and cross-year boundaries without time parsing", () => {
  for (const value of [
    "0001-01-01",
    "2024-02-29",
    "2000-02-29",
    "2026-12-31",
    "2027-01-01",
    "9999-12-31",
  ])
    assert.equal(validLocalDate(value), true, value);
  for (const value of [
    "0000-01-01",
    "1900-02-29",
    "2026-02-29",
    "2026-04-31",
    "2026-13-01",
    "2026-01-00",
    "2026-1-01",
    "2026-01-01T00:00:00Z",
    " 2026-01-01",
    "２０２６-01-01",
  ])
    assert.equal(validLocalDate(value), false, value);
});

test("today follows the local calendar in Toronto and Tokyo around UTC midnight", () => {
  for (const [tz, expected] of [
    ["America/Toronto", "2025-12-31"],
    ["Asia/Tokyo", "2026-01-01"],
  ]) {
    const result = spawnSync(
      process.execPath,
      [
        "--input-type=module",
        "-e",
        `const {localToday}=await import(${JSON.stringify(moduleUrl)});process.stdout.write(localToday(new Date('2026-01-01T01:00:00Z')))`,
      ],
      { env: { ...process.env, TZ: tz }, encoding: "utf8" },
    );
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout, expected);
  }
});

test("only a definite crew-slot rejection permits an immediate corrected retry", () => {
  assert.equal(
    assignmentFailureNeedsReload(
      "Crew #12 already has Draft Assignment #3 on 2026-12-31 AM. Choose another Crew or half-day.",
    ),
    false,
  );
  for (const message of [
    "This assignment changed. Reload assignments before saving again.",
    "The local service is unavailable.",
    "Could not access draft assignments.",
    "Unknown failure",
  ])
    assert.equal(assignmentFailureNeedsReload(message), true);
});
