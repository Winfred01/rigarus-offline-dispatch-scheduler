import type { DraftAssignment } from "./assignment-fields";

// Defensive read projection: Home Crew never establishes dated attendance.
export function employeeVisits(
  rows: DraftAssignment[],
  employeeId: number,
  days: string[],
) {
  return rows
    .filter(
      (row) =>
        row.status === "Draft" &&
        days.includes(row.local_date) &&
        row.staffing?.configured &&
        row.staffing.workers.some(
          (worker) => worker.employee_id === employeeId,
        ),
    )
    .sort(
      (a, b) =>
        a.local_date.localeCompare(b.local_date) ||
        a.slot.localeCompare(b.slot) ||
        a.id - b.id,
    );
}
