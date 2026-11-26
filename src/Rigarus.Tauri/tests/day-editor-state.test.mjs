import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
const moduleUrl = (source) =>
  `data:text/javascript;base64,${Buffer.from(stripTypeScriptTypes(source)).toString("base64")}`;
const fieldsUrl = moduleUrl(
  readFileSync(new URL("../src/assignment-fields.ts", import.meta.url), "utf8"),
);
const stateUrl = moduleUrl(
  readFileSync(
    new URL("../src/day-editor-state.ts", import.meta.url),
    "utf8",
  ).replace('from "./assignment-fields"', `from "${fieldsUrl}"`),
);
const {
  readJournal,
  remember,
  sendRemembered,
  settle,
  journalKey,
  refreshCommitted,
  editorDeadline,
} = await import(stateUrl);

test("bounded desktop timeout keeps the original journal even if a commit reply arrives late", async () => {
  const s = storage();
  remember(s, request);
  let complete, expire;
  const original = new Promise((resolve) => {
    complete = resolve;
  });
  const send = sendRemembered(s, request, () =>
    editorDeadline(original, 150000, {
      schedule: (f, ms) => {
        assert.equal(ms, 150000);
        expire = f;
        return 1;
      },
      cancel: () => {},
    }),
  );
  expire();
  await assert.rejects(send);
  complete(receipt);
  await Promise.resolve();
  assert.deepEqual(readJournal(s, profile), request);
  assert.equal(settle(s, request, receipt), true);
});
const profile = "11111111-1111-4111-8111-111111111111";
const request = {
  profile_id: profile,
  request_id: "22222222-2222-4222-8222-222222222222",
  action: "Create",
  work_item_id: 1,
  expected_project_id: 2,
  crew_id: 3,
  local_date: "2026-11-25",
  notes: "Synthetic journal",
  employee_ids: [5],
  staffing_confirmed: true,
};
function storage() {
  const values = new Map();
  return {
    getItem: (k) => values.get(k) ?? null,
    setItem: (k, v) => values.set(k, v),
    removeItem: (k) => values.delete(k),
  };
}
const receipt = {
  outcome: "Committed",
  request_id: request.request_id,
  validation_status: "Pending",
  applyable: false,
  publishable: false,
  record: {
    record_kind: "FullDayDraft",
    id: 7,
    revision: 1,
    status: "Draft",
    work_item_id: request.work_item_id,
    project_id: request.expected_project_id,
    crew_id: request.crew_id,
    local_date: request.local_date,
    notes: request.notes,
    employee_ids: request.employee_ids,
  },
};
test("journal persists exact payload across reopen and database scopes", () => {
  const s = storage();
  remember(s, request);
  assert.deepEqual(readJournal(s, profile), request);
  assert.equal(
    readJournal(s, "33333333-3333-4333-8333-333333333333"),
    undefined,
  );
  assert.throws(() => remember(s, request));
});
test("lost successful response retains request; receipt resolution does not submit again", async () => {
  const s = storage();
  remember(s, request);
  let sends = 0;
  await assert.rejects(
    sendRemembered(s, request, async () => {
      sends++;
      throw Error("Synthetic lost reply after commit");
    }),
  );
  assert.deepEqual(readJournal(s, profile), request);
  assert.equal(settle(s, request, receipt), true);
  assert.equal(readJournal(s, profile), undefined);
  assert.equal(sends, 1);
});
test("not observed receipt remains uncertain and manual replay uses exact original key/payload", async () => {
  const s = storage();
  remember(s, request);
  assert.equal(
    settle(s, request, { outcome: "NotFound", request_id: request.request_id }),
    false,
  );
  const seen = [];
  await sendRemembered(s, request, async (a, r) => {
    seen.push([a, r]);
    return receipt;
  });
  assert.deepEqual(seen, [["submit", request]]);
  assert.deepEqual(readJournal(s, profile), request);
  assert.equal(settle(s, request, receipt), true);
  assert.equal(readJournal(s, profile), undefined);
});

test("incomplete or mismatched committed data never clears recovery or claims success", () => {
  const s = storage();
  remember(s, request);
  for (const record of [
    { record_kind: "FullDayDraft", id: 7, revision: 1, status: "Draft" },
    { ...receipt.record, project_id: 99 },
    { ...receipt.record, work_item_id: 99 },
    { ...receipt.record, crew_id: 99 },
    { ...receipt.record, local_date: "2026-11-26" },
    { ...receipt.record, notes: "Different saved payload" },
    { ...receipt.record, employee_ids: [] },
    { ...receipt.record, status: "Cancelled" },
    { ...receipt.record, revision: 3 },
  ]) {
    assert.throws(() => settle(s, request, { ...receipt, record }));
    assert.deepEqual(readJournal(s, profile), request);
  }
});

test("an older settled receipt cannot erase a different pending request", () => {
  const s = storage();
  const other = {
    ...request,
    request_id: "33333333-3333-4333-8333-333333333333",
  };
  remember(s, other);
  assert.throws(() => settle(s, request, receipt));
  assert.deepEqual(readJournal(s, profile), other);
});

test("saved edit and cancellation receipts bind exact identity and allowed revision", () => {
  const s = storage(),
    edit = { ...request, action: "Edit", id: 7, expected_revision: 1 };
  remember(s, edit);
  for (const record of [
    { ...receipt.record, id: 8 },
    { ...receipt.record, revision: 3 },
  ])
    assert.throws(() => settle(s, edit, { ...receipt, record }));
  assert.equal(
    settle(s, edit, { ...receipt, record: { ...receipt.record, revision: 2 } }),
    true,
  );
  const cancel = {
    profile_id: profile,
    request_id: "44444444-4444-4444-8444-444444444444",
    action: "Cancel",
    id: 7,
    expected_revision: 2,
  };
  remember(s, cancel);
  assert.throws(() =>
    settle(s, cancel, {
      ...receipt,
      request_id: cancel.request_id,
      record: { ...receipt.record, revision: 3 },
    }),
  );
  assert.equal(
    settle(s, cancel, {
      ...receipt,
      request_id: cancel.request_id,
      record: { ...receipt.record, revision: 3, status: "Cancelled" },
    }),
    true,
  );
});
test("payload alteration after unknown cannot dispatch another request", async () => {
  const s = storage();
  remember(s, request);
  let sends = 0;
  await assert.rejects(
    sendRemembered(s, { ...request, notes: "Synthetic changed" }, async () => {
      sends++;
      return receipt;
    }),
  );
  assert.equal(sends, 0);
  assert.deepEqual(readJournal(s, profile), request);
});
test("stale revision rejection preserves caller fields and permits explicit corrected request", async () => {
  const s = storage(),
    before = structuredClone(request);
  remember(s, request);
  const rejected = {
    validation_status: "Pending",
    applyable: false,
    publishable: false,
    outcome: "Rejected",
    request_id: request.request_id,
    code: "STALE_REVISION",
  };
  assert.deepEqual(
    await sendRemembered(s, request, async () => rejected),
    rejected,
  );
  assert.deepEqual(request, before);
  assert.equal(settle(s, request, rejected), true);
  assert.equal(readJournal(s, profile), undefined);
});

test("unknown or malformed rejection is uncertain and retains the exact journal", () => {
  const s = storage();
  remember(s, request);
  for (const value of [
    {
      outcome: "Rejected",
      request_id: request.request_id,
      code: "STALE_REVISION",
    },
    { ...receipt, outcome: "Rejected", code: "UNKNOWN_STORAGE_FAILURE" },
    { ...receipt, outcome: "Rejected", code: "SQL_GUARD", publishable: true },
  ]) {
    assert.throws(() => settle(s, request, value));
    assert.deepEqual(readJournal(s, profile), request);
  }
});
test("wrong-profile/reused-request/unknown identities never clear the original journal", () => {
  const s = storage();
  remember(s, request);
  for (const code of ["WRONG_PROFILE", "REQUEST_REUSED"])
    assert.equal(
      settle(s, request, {
        outcome: "Rejected",
        request_id: request.request_id,
        code,
      }),
      false,
    );
  assert.throws(() => settle(s, request, { ...receipt, request_id: "other" }));
  assert.throws(() => settle(s, request, { ...receipt, applyable: true }));
  assert.deepEqual(readJournal(s, profile), request);
});
test("corrupt, oversized and foreign journal fails closed", () => {
  const s = storage();
  for (const value of [
    "bad json",
    "x".repeat(64001),
    JSON.stringify({ ...request, profile_id: "other" }),
    JSON.stringify({ ...request, employee_ids: [5, 5] }),
    JSON.stringify({ ...request, local_date: "2026-02-30" }),
  ]) {
    s.setItem(journalKey(profile), value);
    assert.throws(() => readJournal(s, profile));
  }
});
test("unwritable pre-dispatch journal prevents sending and unreadable storage is not ignored", () => {
  const s = {
    getItem: () => null,
    setItem: () => {
      throw Error("Synthetic disk");
    },
    removeItem: () => {},
  };
  assert.throws(() => remember(s, request));
  assert.throws(() =>
    readJournal(
      {
        ...s,
        getItem: () => {
          throw Error("Synthetic denied");
        },
      },
      profile,
    ),
  );
});
test("committed save with failed refresh remains committed; retry refresh performs no save", async () => {
  let reads = 0;
  const copy = structuredClone(receipt);
  assert.equal(
    await refreshCommitted(receipt, async () => {
      reads++;
      throw Error("Synthetic refresh failure");
    }),
    false,
  );
  assert.equal(
    await refreshCommitted(receipt, async () => {
      reads++;
      return true;
    }),
    true,
  );
  assert.equal(reads, 2);
  assert.deepEqual(receipt, copy);
});
