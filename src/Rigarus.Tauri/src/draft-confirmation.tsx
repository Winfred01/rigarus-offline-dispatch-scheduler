import { invoke } from "@tauri-apps/api/core";
import { useEffect, useRef, useState } from "react";
import { Dialog } from "./dialog";
import { editorDeadline } from "./day-editor-state";
import { reasonLabel } from "./day-preview-state";
import {
  prepared,
  envelope,
  confirmation,
  verifiedReceipt,
  historicalReceipt,
  inverse,
  displayRows,
  type PrepareInput,
  type Prepared,
  type Envelope,
  type DraftReceipt,
  type DraftValues,
  type ProposedValues,
  type Inverse,
} from "./draft-confirmation-state";
const call = <T,>(action: string, input: object = {}) =>
  editorDeadline(invoke<T>("draft_transactions", { action, input }));
export function DraftConfirmation({
  initial,
  onClose,
  onSaved,
}: {
  initial?: PrepareInput;
  onClose: (saved?: boolean) => void;
  onSaved?: (r: DraftReceipt) => Promise<boolean>;
}) {
  const [profile, setProfile] = useState(""),
    [enabled, setEnabled] = useState(false),
    [busy, setBusy] = useState(true),
    [broken, setBroken] = useState(false);
  const [input, setInput] = useState(initial),
    [proof, setProof] = useState<Prepared>(),
    [pending, setPending] = useState<Envelope>(),
    [receipt, setReceipt] = useState<DraftReceipt>();
  const [confirmed, setConfirmed] = useState(false),
    [warnings, setWarnings] = useState(false),
    [message, setMessage] = useState(
      "Reading database identity and native recovery journal…",
    );
  const [version, setVersion] = useState(""),
    [comparison, setComparison] = useState<Inverse>(),
    [refreshOK, setRefreshOK] = useState(false);
  const lock = useRef(false),
    alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    void (async () => {
      try {
        const s = await call<{
          database_identity: string;
          test_writes_enabled: boolean;
          production_writes_enabled: false;
          pending: Envelope | null;
        }>("status");
        if (!alive.current) return;
        setProfile(s.database_identity);
        setEnabled(
          s.test_writes_enabled === true &&
            s.production_writes_enabled === false,
        );
        if (s.pending) {
          setPending(envelope(s.pending, s.database_identity));
          setMessage(
            "An original request is retained. Resolve its receipt before another Save. No request was retried.",
          );
        } else if (initial) {
          const p = prepared(await call<Prepared>("prepare", initial), initial);
          if (p.database_identity !== s.database_identity)
            throw Error("Database identity changed during preparation");
          if (alive.current) {
            setProof(p);
            setMessage(
              "Exact preparation loaded. Review every date, employee change, cancellation and warning; this is not a reservation.",
            );
          }
        } else
          setMessage(
            "No unresolved native request. Enter an exact version ID to read its immutable changeset.",
          );
      } catch {
        if (alive.current) {
          setBroken(true);
          setMessage(
            "Cannot read complete preparation/recovery state. No Save is allowed. Reopen to retry; do not clear recovery files.",
          );
        }
      } finally {
        if (alive.current) setBusy(false);
      }
    })();
    return () => {
      alive.current = false;
    };
  }, []);
  async function run(operation: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      await operation();
    } catch {
      if (alive.current)
        setMessage(
          "The operation did not produce a verified result. The original request, if dispatched, remains in native recovery. Resolve it; do not create a replacement key.",
        );
    } finally {
      lock.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function refresh(r: DraftReceipt) {
    if (!onSaved) {
      setRefreshOK(false);
      setMessage(
        "Saved receipt confirmed. Reopen Schedule and reload the week to read the persisted changes. Do not Save again.",
      );
      return;
    }
    let ok = false;
    try {
      ok = await editorDeadline(onSaved(r));
    } catch {
      /* Committed is never downgraded by refresh failure. */
    }
    if (alive.current) {
      setRefreshOK(ok);
      setMessage(
        ok
          ? "Saved receipt confirmed; persisted weekly data refreshed. Still unconfirmed Draft / Validation pending."
          : "Saved successfully, but week refresh failed. Retry reads only; do not Save again.",
      );
    }
  }
  async function accept(original: Envelope, value: DraftReceipt) {
    const checked = verifiedReceipt(original, value);
    if (!alive.current) return;
    setPending(original);
    setReceipt(checked);
    setProof(original.reviewed);
    setInput(original.request.plan);
    if (checked.outcome === "Committed") {
      setVersion(String(checked.version_id));
      await refresh(checked);
    } else
      setMessage(
        `Rejected: ${reasonLabel(checked.code ?? "")}. No replacement write is allowed until this original attempt is explicitly retired.`,
      );
  }
  async function save() {
    if (
      !enabled ||
      !proof ||
      !input ||
      !confirmed ||
      !warnings ||
      pending ||
      broken
    )
      return;
    const original = confirmation(input, proof, crypto.randomUUID());
    setPending(original);
    setReceipt(undefined);
    setComparison(undefined);
    try {
      await accept(original, await call<DraftReceipt>("submit", original));
    } catch {
      setMessage(
        "Save result is UNKNOWN. The native journal must be re-read before another Save. Resolve original request; do not replace its key.",
      );
    }
  }
  async function resolve() {
    const s = await call<{
      database_identity: string;
      pending: Envelope | null;
    }>("status");
    if (!s.pending) {
      if (pending) {
        setBroken(true);
        setMessage(
          "The original request is no longer present in this journal. No new Save is allowed; investigate before continuing.",
        );
      }
      return;
    }
    const original = envelope(s.pending, profile);
    setPending(original);
    const result = await call<DraftReceipt | { outcome: "NotFound" }>(
      "receipt",
      { profile_id: profile, request_id: original.request.request_id },
    );
    if (result.outcome === "NotFound") {
      setReceipt(undefined);
      setMessage(
        "No committed receipt was observed. This is not rejection. Explicit replay must use the same retained request and key.",
      );
      return;
    }
    await accept(original, result);
  }
  async function retry() {
    if (!pending || !enabled) return;
    await accept(pending, await call<DraftReceipt>("submit", pending));
  }
  async function acknowledge() {
    if (!pending || !receipt) return;
    verifiedReceipt(pending, receipt);
    const result = await call<{ acknowledged: boolean }>("acknowledge", {
      request_id: pending.request.request_id,
      receipt,
    });
    if (result.acknowledged !== true) throw Error("No acknowledgement");
    if (!alive.current) return;
    setPending(undefined);
    setMessage(
      receipt.outcome === "Committed"
        ? "Verified receipt archived locally. Return to Schedule; this version is not published."
        : "Original rejection rechecked and archived. No changes were certified. Close and prepare a fresh exact plan before another Save.",
    );
  }
  async function loadVersion() {
    const id = Number(version);
    if (!Number.isSafeInteger(id) || id <= 0) {
      setMessage("Enter a positive exact version ID.");
      return;
    }
    const r = historicalReceipt(
      await call<DraftReceipt>("version", {
        profile_id: profile,
        version_id: id,
      }),
    );
    const c = inverse(
      await call<Inverse>("recovery", { profile_id: profile, version_id: id }),
      id,
    );
    if (alive.current) {
      if (!pending) {
        setReceipt(r);
        setProof(r.plan);
      }
      setComparison(c);
      setMessage(
        `Version #${id} read. ${c.status} compares touched records only; resources, locks and dependencies still need review. Restore is unavailable.`,
      );
    }
  }
  const frozen = busy || broken || !!pending || !!receipt;
  return (
    <Dialog
      title="Reviewed plan → unconfirmed Draft"
      className="draft-confirmation-dialog"
      onClose={() => onClose(receipt?.outcome === "Committed")}
      busy={busy}
    >
      <p className="preview-pending">
        <strong>Production writes closed · Validation pending</strong>.{" "}
        {enabled
          ? "Isolated synthetic engineering profile only."
          : "Read-only production preview; recording is disabled."}{" "}
        No dispatch approval, Publish or Restore.
      </p>
      <p
        role={
          broken || pending || receipt?.outcome === "Rejected"
            ? "alert"
            : "status"
        }
      >
        {message}
      </p>
      {pending && (
        <section className="editor-recovery">
          <h3>Original request retained</h3>
          <p className="impact-fingerprint">{pending.request.request_id}</p>
          <p>
            WorkItem #{String(pending.request.plan.query.work_item_id)} · Crew #
            {pending.request.plan.selected_crew_id}. Closing retains this exact
            request.
          </p>
          <div className="day-preview-toolbar">
            <button disabled={busy} onClick={() => void run(resolve)}>
              Resolve original request
            </button>
            <button disabled={busy || !enabled} onClick={() => void run(retry)}>
              Retry same unchanged request
            </button>
            {receipt && (
              <button disabled={busy} onClick={() => void run(acknowledge)}>
                {receipt.outcome === "Committed"
                  ? "Acknowledge verified saved receipt"
                  : "Recheck and retire original rejection"}
              </button>
            )}
          </div>
        </section>
      )}
      {proof && (
        <section aria-label="Exact changes to record">
          <h3>
            {proof.before.length} saved visit(s) → {proof.proposed.length}{" "}
            proposed date(s); {proof.cancel_ids.length} cancellation(s)
          </h3>
          <p>
            Remaining Days: {proof.confirmed_remaining_days} explicitly
            confirmed. Actual people are exactly as shown; unrecorded people do
            not inherit the saved roster. No actual Rig is allocated.
          </p>
          <Rows caption="Before · saved facts" rows={proof.before} />
          <Rows caption="After · exact proposed values" rows={proof.proposed} />
          <p>
            Cancel these FullDayDraft IDs:{" "}
            {proof.cancel_ids.join(", ") || "None"}. Legacy half-days and all
            unselected visits remain protected.
          </p>
          <details open>
            <summary>Exact Pending and unsupported warnings</summary>
            <div
              className="draft-warnings-scroll"
              tabIndex={0}
              aria-label="Complete Pending and unsupported warning evidence"
            >
              <Warnings value={proof.warnings} />
            </div>
          </details>
          <details>
            <summary>Preparation identity</summary>
            <p className="impact-fingerprint">{proof.plan_fingerprint}</p>
            <p>
              Current when prepared, not a resource reservation. Save
              revalidates the exact plan.
            </p>
          </details>
        </section>
      )}
      {proof && !receipt && !pending && (
        <section>
          <label className="day-preview-check">
            <input
              id="draft-confirm-plan"
              type="checkbox"
              disabled={frozen}
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            I confirm the exact dates, typed IDs, notes, employee changes and
            cancellations above.
          </label>
          <label className="day-preview-check">
            <input
              id="draft-confirm-warnings"
              type="checkbox"
              disabled={frozen}
              checked={warnings}
              onChange={(e) => setWarnings(e.target.checked)}
            />
            I acknowledge every Pending/unsupported warning. Record only an
            unconfirmed Draft, not safe dispatch.
          </label>
          <button
            id="record-unconfirmed-draft"
            disabled={frozen || !enabled || !confirmed || !warnings}
            onClick={() => void run(save)}
          >
            Record reviewed unconfirmed Draft
          </button>
        </section>
      )}
      {input && !pending && !receipt && (
        <button
          className="secondary-button"
          disabled={busy || broken}
          onClick={() =>
            void run(async () => {
              setProof(undefined);
              setConfirmed(false);
              setWarnings(false);
              const p = prepared(await call<Prepared>("prepare", input), input);
              if (p.database_identity !== profile)
                throw Error("Database identity changed during preparation");
              if (alive.current) {
                setProof(p);
                setMessage(
                  "New exact preparation. Review changes and explicitly confirm both statements again.",
                );
              }
            })
          }
        >
          Re-prepare exact plan — no writes
        </button>
      )}
      {receipt?.outcome === "Committed" && (
        <section className="editor-receipt">
          <h3>Committed · unconfirmed Draft version #{receipt.version_id}</h3>
          <p>
            Recorded {receipt.recorded_at}. This receipt is immutable; later
            saved edits may differ.
          </p>
          <Rows caption="Actual committed records" rows={receipt.after ?? []} />
          {onSaved && (
            <button
              disabled={busy}
              onClick={() => void run(() => refresh(receipt))}
            >
              Retry weekly refresh — reads only
            </button>
          )}
          <p>
            {refreshOK
              ? "Persisted week refreshed."
              : "Reload weekly views to inspect current persisted records."}
          </p>
        </section>
      )}
      <section>
        <h3>Read an exact Draft version</h3>
        <div className="day-preview-toolbar">
          <label>
            Version ID
            <input
              aria-label="Draft version ID"
              inputMode="numeric"
              value={version}
              disabled={busy}
              onChange={(e) => {
                setVersion(e.target.value);
                setComparison(undefined);
              }}
            />
          </label>
          <button
            disabled={busy || broken || !profile}
            onClick={() => void run(loadVersion)}
          >
            Read version and inverse comparison
          </button>
        </div>
        {comparison && (
          <>
            <p>
              <strong>{comparison.status}</strong> · read-only inverse for
              version #{comparison.version_id}. Current means touched values
              match, not that restoring is safe.
            </p>
            <Rows
              caption="Current records before a possible restore"
              rows={comparison.before_restore}
            />
            <Rows
              caption="Proposed inverse values — NOT executed"
              rows={comparison.proposed_restore}
            />
            <Warnings value={comparison.warnings} />
          </>
        )}
        <button disabled>Restore — not implemented</button>
      </section>
      <div className="day-preview-toolbar">
        <button
          disabled={busy}
          onClick={() => onClose(receipt?.outcome === "Committed")}
        >
          {pending
            ? "Close — retain original request"
            : receipt
              ? "Return to Schedule"
              : "Cancel without saving"}
        </button>
        <button disabled>Publish — unavailable</button>
      </div>
    </Dialog>
  );
}
function Rows({
  caption,
  rows,
}: {
  caption: string;
  rows: (ProposedValues | DraftValues | Inverse["proposed_restore"][number])[];
}) {
  return (
    <div className="draft-values-scroll">
      <table className="impact-comparison">
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th>FullDayDraft / revision</th>
            <th>Local date / Crew</th>
            <th>WorkItem / Project</th>
            <th>Actual employees / notes / status</th>
          </tr>
        </thead>
        <tbody>
          {displayRows(rows).map((r, i) => (
            <tr key={`${r.id ?? "new"}:${r.local_date}:${i}`}>
              <td>
                {r.id === null ? "New ID on commit" : `#${r.id}`} ·{" "}
                {"revision" in r
                  ? `rev ${r.revision}`
                  : "expected_current_revision" in r
                    ? `expected current ${r.expected_current_revision}`
                    : "Proposed"}
              </td>
              <td>
                {r.local_date}
                <br />
                Crew #{r.crew_id}
              </td>
              <td>
                #{r.work_item_id} / #{r.project_id}
              </td>
              <td>
                {r.employee_ids === null
                  ? "Not recorded"
                  : r.employee_ids.length
                    ? r.employee_ids.map((e) => `#${e}`).join(", ")
                    : "Explicitly empty"}
                <p>{r.notes || "No notes"}</p>
                <strong>{r.status}</strong>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p>No records in this set.</p>}
    </div>
  );
}
function Warnings({ value }: { value: unknown }) {
  if (Array.isArray(value))
    return (
      <ul>
        {value.map((v, i) => (
          <li key={i}>
            <Warnings value={v} />
          </li>
        ))}
      </ul>
    );
  if (value && typeof value === "object")
    return (
      <dl>
        {Object.entries(value).map(([k, v]) => (
          <div key={k}>
            <dt>{reasonLabel(k)}</dt>
            <dd>
              <Warnings value={v} />
            </dd>
          </div>
        ))}
      </dl>
    );
  return (
    <span>
      {typeof value === "string"
        ? reasonLabel(value)
        : String(value ?? "Not recorded")}
    </span>
  );
}
