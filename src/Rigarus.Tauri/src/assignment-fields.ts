export type AssignmentSeed = { projectId: number; workItemId: number };
export type DraftAssignment = {
  id: number;
  work_item_id: number;
  crew_id: number;
  local_date: string;
  slot: "AM" | "PM";
  notes: string;
  status: "Draft" | "Cancelled";
  revision: number;
  project_id: number;
  job_number: string;
  site_id: string;
  site_name: string;
  work_type: string;
  required_crew_count: number;
  estimated_half_days: number;
  crew_name: string;
  crew_active: boolean;
  validation_status: "Pending";
  publishable: false;
  staffing?: {
    configured: boolean;
    change_id: number;
    workers: {
      employee_id: number;
      name: string;
      home_crew_id: number;
      active: boolean;
      driver_status: string;
    }[];
  };
};

export function localToday(now = new Date()): string {
  return `${now.getFullYear().toString().padStart(4, "0")}-${(now.getMonth() + 1).toString().padStart(2, "0")}-${now.getDate().toString().padStart(2, "0")}`;
}

export function validLocalDate(value: string): boolean {
  if (!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return (
    year >= 1 && month >= 1 && month <= 12 && day >= 1 && day <= days[month - 1]
  );
}

export function assignmentFailureNeedsReload(message: string): boolean {
  // This canonical collision is a definite rejection, so the operator can correct the slot.
  return !/^Crew #[0-9]+ already has Draft Assignment #[0-9]+ on [0-9]{4}-[0-9]{2}-[0-9]{2} (AM|PM)\./.test(
    message,
  );
}
