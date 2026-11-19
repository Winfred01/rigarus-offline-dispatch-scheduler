export type SortState<Key extends string> = {
  key: Key;
  direction: "ascending" | "descending";
};

export function nextSort<Key extends string>(
  current: SortState<Key> | undefined,
  key: Key,
): SortState<Key> {
  return {
    key,
    direction:
      current?.key === key && current.direction === "ascending"
        ? "descending"
        : "ascending",
  };
}

// Identifiers remain text (including leading zeroes); quantities remain numbers.
const textOrder = new Intl.Collator("en", { sensitivity: "base" });

export function sortRows<
  Row extends { id: number | null },
  Key extends keyof Row & string,
>(rows: readonly Row[], sort: SortState<Key> | undefined): Row[] {
  if (!sort) return [...rows];
  return [...rows].sort((left, right) => {
    const a = left[sort.key];
    const b = right[sort.key];
    const compared =
      typeof a === "number" && typeof b === "number"
        ? a - b
        : textOrder.compare(String(a), String(b));
    // Stable identity breaks ties in either direction without changing source data.
    return (
      compared * (sort.direction === "ascending" ? 1 : -1) ||
      (left.id ?? 0) - (right.id ?? 0)
    );
  });
}
