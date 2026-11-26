export class ImpactFreshness {
  stale = false;
  recompute() {
    this.stale = false;
  }
  invalidate() {
    this.stale = true;
  }
  observe(status: string): "Stale" | "Current" {
    if (status !== "Current" && status !== "Stale")
      throw new Error("Unknown freshness is not Current");
    if (status === "Stale") this.stale = true;
    return this.stale ? "Stale" : "Current";
  }
}

type ScopeRow = {
  record_kind: string;
  record_id: number;
  expected_revision: number;
};
export function sameImpactScope(
  saved: ScopeRow[],
  requested: ScopeRow[],
): boolean {
  if (
    !Array.isArray(saved) ||
    !Array.isArray(requested) ||
    saved.length !== requested.length
  )
    return false;
  const key = (r: ScopeRow) =>
    `${r.record_kind}:${r.record_id}:${r.expected_revision}`;
  const valid = (r: ScopeRow) =>
    r?.record_kind === "FullDayDraft" &&
    Number.isSafeInteger(r.record_id) &&
    r.record_id > 0 &&
    Number.isSafeInteger(r.expected_revision) &&
    r.expected_revision > 0;
  return (
    saved.every(valid) &&
    requested.every(valid) &&
    new Set(saved.map(key)).size === saved.length &&
    [...saved].map(key).sort().join("|") ===
      [...requested].map(key).sort().join("|")
  );
}
