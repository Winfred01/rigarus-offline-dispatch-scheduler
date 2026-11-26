import type { SavedVisit } from "./workbench-state";
import { validLocalDate } from "./assignment-fields";
export type DraftRecord = {
  id: number;
  revision: number;
  work_item_id: number;
  project_id: number;
  crew_id: number;
  local_date: string;
  notes: string;
  status: "Draft" | "Cancelled";
  employee_ids: number[] | null;
  record_kind: "FullDayDraft";
};
export type EditorRequest = {
  profile_id: string;
  request_id: string;
  action: "Create" | "Edit" | "Cancel";
  id?: number;
  expected_revision?: number;
  work_item_id?: number;
  expected_project_id?: number;
  crew_id?: number;
  local_date?: string;
  notes?: string;
  employee_ids?: number[] | null;
  staffing_confirmed?: boolean;
};
export type EditorResult = {
  outcome: "Committed" | "Rejected" | "NotFound";
  request_id: string;
  code?: string;
  message?: string;
  record?: DraftRecord;
  observation?: SavedVisit;
  validation_status?: "Pending";
  applyable?: false;
  publishable?: false;
};
export type Journal = Pick<Storage, "getItem" | "setItem" | "removeItem">;
export type Transport = (
  action: string,
  input: object,
) => Promise<EditorResult>;
export function editorDeadline<T>(
  operation: Promise<T>,
  milliseconds = 150000,
  clock = {
    schedule: (run: () => void, ms: number) => globalThis.setTimeout(run, ms),
    cancel: (id: number) => globalThis.clearTimeout(id),
  },
): Promise<T> {
  return new Promise((resolve, reject) => {
    let done = false;
    const timer = clock.schedule(() => {
      done = true;
      reject(
        Error(
          "Editor call timed out; the original operation may still complete.",
        ),
      );
    }, milliseconds);
    operation.then(
      (value) => {
        if (!done) {
          done = true;
          clock.cancel(timer);
          resolve(value);
        }
      },
      (error) => {
        if (!done) {
          done = true;
          clock.cancel(timer);
          reject(error);
        }
      },
    );
  });
}
const uuid = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(v);
const positive = (v: unknown) =>
  typeof v === "number" && Number.isSafeInteger(v) && v > 0;
export const journalKey = (profile: string) =>
  `rigarus.day-editor.pending.v1.${profile}`;
export function readJournal(
  storage: Journal,
  profile: string,
): EditorRequest | undefined {
  if (!uuid(profile)) throw Error("Invalid database identity");
  const text = storage.getItem(journalKey(profile));
  if (text === null) return;
  return parseJournal(text, profile);
}
function parseJournal(text: string, profile: string): EditorRequest {
  if (text.length > 64000) throw Error("Oversized recovery journal");
  const r = JSON.parse(text) as EditorRequest;
  if (
    !r ||
    r.profile_id !== profile ||
    !uuid(r.request_id) ||
    !["Create", "Edit", "Cancel"].includes(r.action)
  )
    throw Error("Invalid recovery journal");
  const allowed = [
    "profile_id",
    "request_id",
    "action",
    "id",
    "expected_revision",
    ...(r.action === "Cancel"
      ? []
      : [
          "work_item_id",
          "expected_project_id",
          "crew_id",
          "local_date",
          "notes",
          "employee_ids",
          "staffing_confirmed",
        ]),
  ];
  if (
    Object.keys(r).some((k) => !allowed.includes(k)) ||
    (r.action === "Create" &&
      (r.id !== undefined || r.expected_revision !== undefined))
  )
    throw Error("Unexpected recovery fields");
  if (
    r.action !== "Create" &&
    (!positive(r.id) || !positive(r.expected_revision))
  )
    throw Error("Invalid saved identity");
  if (
    r.action !== "Cancel" &&
    (!positive(r.work_item_id) ||
      !positive(r.expected_project_id) ||
      !positive(r.crew_id) ||
      typeof r.local_date !== "string" ||
      !validLocalDate(r.local_date) ||
      typeof r.notes !== "string" ||
      Array.from(r.notes).length > 2000 ||
      r.notes.includes("\0") ||
      typeof r.staffing_confirmed !== "boolean" ||
      (r.employee_ids !== null &&
        (!Array.isArray(r.employee_ids) ||
          r.employee_ids.length > 1000 ||
          r.employee_ids.some((e) => !positive(e)) ||
          new Set(r.employee_ids).size !== r.employee_ids.length)))
  )
    throw Error("Invalid recovery payload");
  return r;
}
export function remember(storage: Journal, r: EditorRequest) {
  const encoded = JSON.stringify(r);
  parseJournal(encoded, r.profile_id);
  if (readJournal(storage, r.profile_id))
    throw Error("Resolve the original request first");
  storage.setItem(journalKey(r.profile_id), encoded);
  const saved = readJournal(storage, r.profile_id);
  if (JSON.stringify(saved) !== JSON.stringify(r))
    throw Error("Recovery journal was not retained");
}
export function settle(
  storage: Journal,
  request: EditorRequest,
  value: EditorResult,
) {
  if (
    value.request_id !== request.request_id ||
    !["Committed", "Rejected", "NotFound"].includes(value.outcome)
  )
    throw Error("Unknown request response");
  if (
    value.outcome === "NotFound" ||
    ["REQUEST_REUSED", "WRONG_PROFILE"].includes(value.code ?? "")
  )
    return false;
  if (
    value.validation_status !== "Pending" ||
    value.applyable !== false ||
    value.publishable !== false
  )
    throw Error("Invalid receipt safety flags");
  if (
    value.outcome === "Committed" &&
    !matchesSavedRequest(request, value.record)
  )
    throw Error("Saved receipt does not match the original request");
  if (
    value.outcome === "Rejected" &&
    ![
      "STALE_REVISION",
      "STALE_PROJECT",
      "STAFFING_RECONFIRM",
      "NOT_FOUND",
      "OCCUPANCY_OR_REVISION",
      "INVALID_DRAFT",
      "SQL_GUARD",
    ].includes(value.code ?? "")
  )
    throw Error("Unrecognized rejection is not a definitive result");
  const current = readJournal(storage, request.profile_id);
  if (current && JSON.stringify(current) !== JSON.stringify(request))
    throw Error(
      "Recovery journal changed. Reopen and resolve its current request.",
    );
  try {
    storage.removeItem(journalKey(request.profile_id));
  } catch {
    /* receipt remains safely recoverable */
  }
  return true;
}

function matchesSavedRequest(
  request: EditorRequest,
  r: DraftRecord | undefined,
) {
  if (
    !r ||
    r.record_kind !== "FullDayDraft" ||
    !positive(r.id) ||
    !positive(r.revision) ||
    !positive(r.work_item_id) ||
    !positive(r.project_id) ||
    !positive(r.crew_id) ||
    typeof r.local_date !== "string" ||
    !validLocalDate(r.local_date) ||
    typeof r.notes !== "string" ||
    Array.from(r.notes).length > 2000 ||
    r.notes.includes("\0") ||
    !["Draft", "Cancelled"].includes(r.status) ||
    (r.employee_ids !== null &&
      (!Array.isArray(r.employee_ids) ||
        r.employee_ids.length > 1000 ||
        r.employee_ids.some((e) => !positive(e)) ||
        new Set(r.employee_ids).size !== r.employee_ids.length))
  )
    return false;
  if (request.action === "Create") {
    if (r.revision !== 1 || r.status !== "Draft") return false;
  } else if (
    r.id !== request.id ||
    !positive(request.expected_revision) ||
    (r.revision !== request.expected_revision &&
      r.revision !== request.expected_revision! + 1)
  )
    return false;
  if (request.action === "Cancel") return r.status === "Cancelled";
  return (
    r.status === "Draft" &&
    r.work_item_id === request.work_item_id &&
    r.project_id === request.expected_project_id &&
    r.crew_id === request.crew_id &&
    r.local_date === request.local_date &&
    r.notes === request.notes &&
    JSON.stringify(
      r.employee_ids === null
        ? null
        : [...r.employee_ids].sort((a, b) => a - b),
    ) ===
      JSON.stringify(
        request.employee_ids === null
          ? null
          : [...(request.employee_ids ?? [])].sort((a, b) => a - b),
      )
  );
}
export async function sendRemembered(
  storage: Journal,
  request: EditorRequest,
  transport: Transport,
) {
  const original = readJournal(storage, request.profile_id);
  if (JSON.stringify(original) !== JSON.stringify(request))
    throw Error("Original request must be retained unchanged");
  const value = await transport("submit", original!);
  return value;
}

export async function refreshCommitted(
  value: EditorResult,
  refresh: (row: DraftRecord) => Promise<boolean>,
) {
  if (value.outcome !== "Committed" || !value.record)
    throw Error("No committed receipt");
  try {
    return await editorDeadline(refresh(value.record));
  } catch {
    return false;
  }
}
