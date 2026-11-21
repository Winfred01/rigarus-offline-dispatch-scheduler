export type CountField = "crews" | "halfDays";
export type WorkItemErrors = Record<
  number,
  Partial<Record<CountField, string>>
>;

const labels: Record<CountField, string> = {
  crews: "Required crews",
  halfDays: "Estimated half-days",
};

export function workItemCountError(value: string, field: CountField) {
  const count = value.trim();
  if (!/^\+?\d+$/.test(count) || Number(count) < 1) {
    return `${labels[field]} must be a whole number of at least 1.`;
  }
  if (Number(count) > 2147483647) {
    return `${labels[field]} must be a whole number from 1 to 2147483647.`;
  }
  return undefined;
}

export function validateWorkItemCounts(
  items: { key: number; crews: string; halfDays: string }[],
) {
  const errors: WorkItemErrors = {};
  let first: { key: number; field: CountField } | undefined;
  for (const item of items) {
    for (const field of ["crews", "halfDays"] as const) {
      const message = workItemCountError(item[field], field);
      if (message) {
        (errors[item.key] ??= {})[field] = message;
        first ??= { key: item.key, field };
      }
    }
  }
  return { errors, first };
}
