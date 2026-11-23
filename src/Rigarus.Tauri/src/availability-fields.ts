export type AvailabilityState = "Available" | "Unavailable" | "Unknown";
export type AvailabilitySlot = "FullDay" | "AM" | "PM";
export type AvailabilitySnapshot = {
  employee_id: number;
  revision: number;
  start_date: string;
  end_date: string;
  entries: {
    local_date: string;
    slot: "AM" | "PM";
    state: AvailabilityState;
  }[];
};
export type SlotAvailability = {
  local_date: string;
  slot: "AM" | "PM";
  employees: { employee_id: number; state: AvailabilityState }[];
};
export function availabilityText(state: AvailabilityState): string {
  return state === "Unknown" ? "Not recorded" : state;
}
export function stateAt(
  snapshot: AvailabilitySnapshot,
  day: string,
  slot: "AM" | "PM",
): AvailabilityState {
  return (
    snapshot.entries.find((e) => e.local_date === day && e.slot === slot)
      ?.state ?? "Unknown"
  );
}
