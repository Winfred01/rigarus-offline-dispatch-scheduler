export type PreviewOrder = "EarliestFinish" | "EarliestStart";
export type PreviewQuery = {
  work_item_id: number;
  expected_project_id: number;
  crew_ids: number[];
  remaining_days: number;
  remaining_confirmed: true;
  earliest_start_date: string;
  horizon_end_date: string;
  order: PreviewOrder;
  max_options: number;
};
export type PreviewFields = {
  days: string;
  confirmed: boolean;
  crews: number[];
  start: string;
  end: string;
  limit: number;
};

function validDay(value: string): number | undefined {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return;
  const [y, m, d] = value.split("-").map(Number);
  if (y < 1 || y > 9999) return;
  const date = new Date(0);
  date.setUTCFullYear(y, m - 1, d);
  date.setUTCHours(0, 0, 0, 0);
  if (
    date.getUTCFullYear() !== y ||
    date.getUTCMonth() !== m - 1 ||
    date.getUTCDate() !== d
  )
    return;
  return date.getTime() / 86400000;
}

export function previewQuery(
  workItem: number,
  project: number,
  fields: PreviewFields,
  order: PreviewOrder,
):
  | { query: PreviewQuery; error?: never }
  | { query?: never; error: { field: string; message: string } } {
  const fail = (field: string, message: string) => ({
    error: { field, message },
  });
  const positive = (n: number) => Number.isSafeInteger(n) && n > 0;
  if (!positive(workItem) || !positive(project))
    return fail("days", "Reload the saved WorkItem before previewing.");
  const days = Number(fields.days.trim());
  if (!/^\d+$/.test(fields.days.trim()) || !positive(days))
    return fail("days", "Enter a positive whole number of Remaining Days.");
  if (!fields.confirmed)
    return fail(
      "confirmed",
      "Explicitly confirm Remaining Days; estimates and old visits are not converted.",
    );
  if (
    !fields.crews.length ||
    fields.crews.length > 100 ||
    fields.crews.some((id) => !positive(id)) ||
    new Set(fields.crews).size !== fields.crews.length
  )
    return fail("crews", "Choose 1 to 100 distinct candidate Crews.");
  const first = validDay(fields.start),
    last = validDay(fields.end);
  if (first === undefined)
    return fail("start", "Choose a valid local start date.");
  if (last === undefined || last < first || last - first >= 366)
    return fail("end", "Choose an ordered horizon of at most 366 local dates.");
  if (!Number.isInteger(fields.limit) || fields.limit < 1 || fields.limit > 10)
    return fail("limit", "Choose 1 to 10 alternatives.");
  return {
    query: {
      work_item_id: workItem,
      expected_project_id: project,
      crew_ids: [...fields.crews].sort((a, b) => a - b),
      remaining_days: days,
      remaining_confirmed: true,
      earliest_start_date: fields.start,
      horizon_end_date: fields.end,
      order,
      max_options: fields.limit,
    },
  };
}

export function pendingFlags(
  value:
    | {
        unit?: unknown;
        validation_status?: unknown;
        applyable?: unknown;
        publishable?: unknown;
      }
    | null
    | undefined,
): boolean {
  return (
    value?.unit === "FullDay" &&
    value.validation_status === "Pending" &&
    value.applyable === false &&
    value.publishable === false
  );
}

export function reasonLabel(code: string): string {
  return code
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replaceAll("_", " ")
    .replaceAll(":", ": ")
    .toLowerCase();
}

export class PreviewEpoch {
  private value = 0;
  next(): number {
    return ++this.value;
  }
  current(ticket: number): boolean {
    return ticket === this.value;
  }
}
