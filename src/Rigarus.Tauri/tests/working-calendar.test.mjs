import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";

const source = stripTypeScriptTypes(
  readFileSync(
    new URL("../src/working-calendar-fields.ts", import.meta.url),
    "utf8",
  ),
);
const { workingText, calendarMessage } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);
test("calendar feedback retains unknown, explicit closure and Project inheritance", () => {
  assert.equal(workingText("Unknown"), "Not recorded");
  assert.equal(workingText("NotWorking"), "Cannot work");
  const value = {
    project_id: 17,
    crew_state: "Working",
    work_item_state: "NotWorking",
    status: "Blocked",
  };
  assert.match(
    calendarMessage(value),
    /Calendar conflict: Crew Can work; Project Cannot work/,
  );
  assert.match(calendarMessage(value), /All WorkItems inherit Project #17/);
  assert.match(
    calendarMessage({
      ...value,
      work_item_state: "Unknown",
      status: "Pending",
    }),
    /Calendar pending.*Not recorded/,
  );
  assert.match(
    calendarMessage({
      ...value,
      work_item_state: "Working",
      status: "Matched",
    }),
    /Calendar matched/,
  );
  assert.doesNotMatch(
    calendarMessage({ ...value, status: "Matched" }),
    /eligible|approved|publishable/i,
  );
});
