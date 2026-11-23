import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";
const code = stripTypeScriptTypes(
  readFileSync(
    new URL("../src/employee-week-data.ts", import.meta.url),
    "utf8",
  ),
);
const { employeeVisits } = await import(
  `data:text/javascript;base64,${Buffer.from(code).toString("base64")}`
);
const days = ["2026-12-31", "2027-01-01"];
const visit = (
  id,
  date = "2026-12-31",
  slot = "AM",
  workers = [1],
  status = "Draft",
  configured = true,
) => ({
  id,
  local_date: date,
  slot,
  status,
  crew_id: 99,
  staffing: {
    configured,
    workers: workers.map((employee_id) => ({ employee_id, home_crew_id: 2 })),
  },
});
test("membership is explicit: shared Home Crew, unknown/empty/reconfirmation never imply jobs", () => {
  const rows = [
    visit(1),
    visit(2, undefined, undefined, [2]),
    visit(3, undefined, undefined, []),
    visit(4, undefined, undefined, [1], "Draft", false),
    { ...visit(5), staffing: undefined },
  ];
  assert.deepEqual(
    employeeVisits(rows, 1, days).map((r) => r.id),
    [1],
  );
  assert.deepEqual(
    employeeVisits(rows, 2, days).map((r) => r.id),
    [2],
  );
  assert.deepEqual(employeeVisits(rows, 3, days), []);
  assert.equal(employeeVisits(rows, 1, days)[0].crew_id, 99);
});
test("cross-year/weekend AM/PM and repeated visits remain independent; cancelled/outside excluded", () => {
  const rows = [
    visit(4, "2027-01-01", "PM"),
    visit(2, "2026-12-31", "PM"),
    visit(1),
    visit(3, "2027-01-01"),
    visit(5, "2027-01-02"),
    visit(6, undefined, undefined, [1], "Cancelled"),
  ];
  assert.deepEqual(
    employeeVisits(rows, 1, days).map((r) => r.id),
    [1, 2, 3, 4],
  );
});
test("stable date/slot/ID order leaves source records and saved worker IDs unchanged", () => {
  const rows = [visit(9), visit(2), visit(3, undefined, "PM")];
  const before = structuredClone(rows);
  assert.deepEqual(
    employeeVisits(rows, 1, days).map((r) => r.id),
    [2, 9, 3],
  );
  assert.deepEqual(rows, before);
});
test("defensive projection never exposes another employee from a stale/wrong server result", () => {
  const rows = [visit(1), visit(2, "2027-01-01", "PM", [2])];
  assert.deepEqual(
    employeeVisits(rows, 2, ["2027-01-01"]).map((r) => r.id),
    [2],
  );
  assert.deepEqual(employeeVisits(rows, 2, ["2026-12-31"]), []);
});
