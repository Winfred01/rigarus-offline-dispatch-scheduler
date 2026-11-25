import { validLocalDate } from "./assignment-fields";
import { weekDays } from "./week";
export type SavedKind = "FullDayDraft" | "LegacyHalfDay";
export type SavedTarget = {
  id: number;
  date?: string;
  record_kind?: SavedKind;
};
export type SavedVisit = {
  record_kind: SavedKind;
  id: number;
  revision: number;
  work_item_id: number;
  project_id: number;
  crew_id: number;
  crew_name: string;
  local_date: string;
  slot: "AM" | "PM" | null;
  notes: string;
  job_number: string;
  site_id: string;
  site_name: string;
  work_type: string;
  staffing_configured: boolean;
  workers: {
    id: number;
    name: string;
    home_crew_id: number;
    active: boolean;
  }[];
  actual_rig_id: number | null;
  rig_context_stale: boolean;
  compatibility_status: string;
  validation_status: "Pending";
  applyable: false;
  publishable: false;
  checks: { check: string; state: string; reasons: string[] }[];
};
export const savedKey = (r: Pick<SavedVisit, "record_kind" | "id">) =>
  `${r.record_kind}-${r.id}`;
export function savedKind(value: unknown): value is SavedKind {
  return value === "FullDayDraft" || value === "LegacyHalfDay";
}
export function weekRange(day: string) {
  const days = weekDays(day),
    supported = days.filter(validLocalDate);
  return { days, start: supported[0], end: supported.at(-1)! };
}
export function revealTypedFilters(
  filters: { crew: string; project: string },
  row: SavedVisit,
) {
  return {
    crew:
      !filters.crew || Number(filters.crew) === row.crew_id ? filters.crew : "",
    project:
      !filters.project || Number(filters.project) === row.project_id
        ? filters.project
        : "",
  };
}
export function visitsForCell(rows: SavedVisit[], date: string) {
  return rows
    .filter((r) => r.local_date === date)
    .sort(
      (a, b) =>
        a.record_kind.localeCompare(b.record_kind) ||
        (a.slot ?? "").localeCompare(b.slot ?? "") ||
        a.crew_id - b.crew_id ||
        a.id - b.id,
    );
}
export function activeProblems(row: SavedVisit) {
  return row.checks.filter(
    (c) => !["Satisfied", "Matched", "Not applicable"].includes(c.state),
  );
}
