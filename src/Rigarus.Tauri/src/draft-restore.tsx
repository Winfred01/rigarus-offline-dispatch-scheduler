import { useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Dialog } from "./dialog";
import { Rows, Warnings } from "./draft-confirmation";
import { editorDeadline } from "./day-editor-state";
import type { DraftValues, DraftReceipt } from "./draft-confirmation-state";
import {
  prepared,
  original,
  envelope,
  confirmation,
  status,
  receipt,
  notFound,
  versionId,
  RestoreEpoch,
  reviewContext,
  refreshRestored,
  type Bundle,
  type RestoreEnvelope,
  type RestoreReceipt,
  type RestoreStatus,
} from "./draft-restore-state";

const call = <T,>(action: string, input: object = {}) =>
  editorDeadline(invoke<T>("draft_restores", { action, input }));
export function DraftRestore({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: (row: DraftValues) => Promise<boolean>;
}) {
  const [gate, setGate] = useState<RestoreStatus>();
  const [busy, setBusy] = useState(true),
    [broken, setBroken] = useState(false),
    [version, setVersion] = useState("");
  const [source, setSource] = useState<DraftReceipt>(),
    [bundle, setBundle] = useState<Bundle>();
  const [pending, setPending] = useState<RestoreEnvelope>(),
    [result, setResult] = useState<RestoreReceipt>();
  const [ack, setAck] = useState<string[]>([]),
    [confirmed, setConfirmed] = useState(false),
    [refreshed, setRefreshed] = useState(false);
  const [message, setMessage] = useState(
    "Reading the database identity, gate and retained Restore request…",
  );
  const alive = useRef(true),
    focused = useRef(false),
    lock = useRef(false),
    epoch = useRef(new RestoreEpoch());
  useEffect(() => {
    alive.current = true;
    const ticket = epoch.current.next();
    void (async () => {
      try {
        const s = status(await call<RestoreStatus>("status"));
        if (!alive.current || !epoch.current.current(ticket)) return;
        setGate(s);
        if (s.pending) {
          const p = envelope(s.pending, s.database_identity);
          setPending(p);
          setBundle(p);
          setSource(p.source);
          setVersion(String(p.request.source_version_id));
          setMessage(
            "Original Restore retained. Resolve its receipt; nothing has been replayed.",
          );
        } else
          setMessage(
            s.other_operation_pending
              ? "Draft Apply has an unresolved request. Resolve it before Restore."
              : s.test_writes_enabled
                ? "Select one original DraftVersion. Preparation is a rolled-back synthetic dry run."
                : "Production Restore is closed. Original versions can be inspected; preparation and submission require a separate synthetic test opt-in.",
          );
      } catch {
        if (alive.current && epoch.current.current(ticket)) {
          setBroken(true);
          setMessage(
            "Cannot read complete native recovery state. Keep recovery files; no Restore is allowed.",
          );
        }
      } finally {
        if (alive.current && epoch.current.current(ticket)) setBusy(false);
      }
    })();
    return () => {
      alive.current = false;
      epoch.current.next();
    };
  }, []);
  useEffect(() => {
    if (gate && !busy && !focused.current) {
      document
        .getElementById(
          pending ? "resolve-draft-restore" : "restore-source-version",
        )
        ?.focus();
      focused.current = true;
    }
  }, [gate, busy, pending]);
  const current = () => alive.current;
  async function run(operation: (valid: () => boolean) => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    const ticket = epoch.current.next();
    const valid = () => current() && epoch.current.current(ticket);
    try {
      await operation(valid);
    } catch (e) {
      if (valid()) {
        setConfirmed(false);
        setAck([]);
        setMessage(
          String(e).startsWith("Stale")
            ? "Stale: the records or evidence changed. No new restore was confirmed. Prepare and review again."
            : "No complete verified result. If dispatched, retain the original request and resolve it; never create a replacement key.",
        );
      }
    } finally {
      lock.current = false;
      if (valid()) setBusy(false);
    }
  }
  async function refresh(value: RestoreReceipt, valid: () => boolean) {
    const ok = await refreshRestored(value, (row) =>
      editorDeadline(onSaved(row)),
    );
    if (valid()) {
      setRefreshed(ok);
      setMessage(
        ok
          ? "Restore committed; saved weekly data refreshed. It remains an unconfirmed Draft / Validation pending."
          : "Restore committed, but weekly refresh failed. Retry reads only; do not submit Restore again.",
      );
    }
  }
  async function accept(
    p: RestoreEnvelope,
    value: RestoreReceipt,
    valid: () => boolean,
  ) {
    const checked = receipt(p, value);
    if (!valid()) return;
    setPending(p);
    setResult(checked);
    setBundle(p);
    setSource(p.source);
    if (checked.outcome === "Committed") await refresh(checked, valid);
    else
      setMessage(
        `Restore rejected: ${checked.code}. A matching immutable rejection receipt is available; no recovery version was committed.`,
      );
  }
  async function readOriginal(valid: () => boolean) {
    if (!gate) return;
    const id = versionId(version);
    const value = original(
      await call<DraftReceipt>("original", {
        profile_id: gate.database_identity,
        source_version_id: id,
      }),
      gate.database_identity,
      id,
    );
    if (valid()) {
      setSource(value);
      setBundle(undefined);
      setAck([]);
      setConfirmed(false);
      setMessage(
        `Original DraftVersion #${id} loaded. It is not a Published snapshot or a recovery version.`,
      );
    }
  }
  async function prepare(valid: () => boolean) {
    if (!gate) return;
    setAck([]);
    setConfirmed(false);
    setBundle(undefined);
    const id = versionId(version);
    const value = prepared(
      await call<Bundle>("prepare", {
        profile_id: gate.database_identity,
        source_record_kind: "DraftVersion",
        source_version_id: id,
      }),
      gate.database_identity,
      id,
    );
    if (valid()) {
      setSource(value.source);
      setBundle(value);
      setMessage(
        value.reviewed.status === "Blocked"
          ? "Blocked: current constraints prohibit this inverse. Warning acknowledgement cannot override a blocker."
          : "Review original/current/inverse differences and independently acknowledge each Pending warning. This is not dispatch approval.",
      );
    }
  }
  async function submit(valid: () => boolean) {
    if (!bundle || !gate) return;
    const p = confirmation(bundle, ack, crypto.randomUUID(), confirmed);
    setPending(p);
    setMessage(
      "Submitting one original request. Closing keeps its native recovery journal and does not cancel a possible commit.",
    );
    await accept(p, await call<RestoreReceipt>("submit", p), valid);
  }
  async function resolve(valid: () => boolean) {
    if (!pending) return;
    const value = await call<RestoreReceipt | { outcome: "NotFound" }>(
      "resolve",
    );
    if (notFound(value)) {
      if (valid())
        setMessage(
          "Receipt NotFound is uncertain. The original request remains retained. You may explicitly replay only that unchanged request.",
        );
      return;
    }
    await accept(pending, value as RestoreReceipt, valid);
  }
  async function replay(valid: () => boolean) {
    if (!pending || !gate) return;
    await accept(
      pending,
      await call<RestoreReceipt>(
        "submit",
        envelope(pending, gate.database_identity),
      ),
      valid,
    );
  }
  async function acknowledge(valid: () => boolean) {
    if (!pending || !result) return;
    receipt(pending, result);
    const value = await call<{ acknowledged: boolean; request_id: string }>(
      "acknowledge",
      {
        profile_id: pending.request.profile_id,
        request_id: pending.request.request_id,
        outcome: result.outcome,
        version_id: result.version_id ?? null,
      },
    );
    if (
      value.acknowledged !== true ||
      value.request_id !== pending.request.request_id
    )
      throw Error("No exact acknowledgement");
    if (valid()) {
      setPending(undefined);
      setMessage(
        "Verified original receipt archived and flushed; its exact pending Restore journal was retired. No other operation was cleared.",
      );
    }
  }
  const enabled =
    !!gate?.test_writes_enabled && !gate.other_operation_pending && !broken;
  const frozen = busy || broken || !!pending || !!result;
  const canSubmit =
    enabled &&
    !frozen &&
    !!bundle &&
    bundle.reviewed.status === "Current" &&
    confirmed &&
    ack.length === bundle.reviewed.warnings.length;
  const context = bundle
    ? reviewContext(bundle, pending, result, ack, confirmed)
    : undefined;
  function reset() {
    setSource(undefined);
    setBundle(undefined);
    setResult(undefined);
    setAck([]);
    setConfirmed(false);
    setVersion("");
    setMessage(
      "Select another exact original version. No request has been sent.",
    );
  }
  return (
    <Dialog
      title="Single-version Draft Restore"
      className="draft-confirmation-dialog draft-restore-dialog"
      onClose={onClose}
      initialFocus="#restore-source-version"
    >
      <p className="preview-pending">
        <strong>Production Restore closed · Validation pending</strong>. A
        separate synthetic test opt-in can record a new unconfirmed Draft only.
        Apply=false · Publish=false. Old AM/PM records are protected.
      </p>
      <p role="status" aria-live="polite" id="restore-message">
        {message}
      </p>
      <div className="restore-controls">
        <label htmlFor="restore-source-version">
          Original DraftVersion ID
          <input
            id="restore-source-version"
            inputMode="numeric"
            value={version}
            disabled={frozen}
            onChange={(e) => {
              setVersion(e.target.value);
              setSource(undefined);
              setBundle(undefined);
              setAck([]);
              setConfirmed(false);
            }}
          />
        </label>
        <button
          id="read-restore-original"
          disabled={frozen || !gate || !version}
          onClick={() => void run(readOriginal)}
        >
          Inspect original version
        </button>
        <button
          id="prepare-draft-restore"
          disabled={frozen || !enabled || !version}
          onClick={() => void run(prepare)}
        >
          Prepare exact inverse
        </button>
      </div>
      {gate?.database_identity && (
        <p className="impact-fingerprint">Database {gate.database_identity}</p>
      )}
      {pending && (
        <section aria-label="Original Restore request">
          <h3>Retained Restore request</h3>
          <p className="impact-fingerprint" id="restore-request-id">
            {pending.request.request_id}
          </p>
          <p>
            Original DraftVersion #{pending.request.source_version_id}. Closing
            retains this request. Unknown / NotFound never permits a new key.
          </p>
          <button
            id="resolve-draft-restore"
            disabled={busy}
            onClick={() => void run(resolve)}
          >
            Resolve original receipt
          </button>
          {!result && (
            <button
              id="replay-draft-restore"
              disabled={busy || !enabled}
              onClick={() => void run(replay)}
            >
              Replay original request unchanged
            </button>
          )}
          {result && (
            <button
              id="acknowledge-draft-restore"
              disabled={busy}
              onClick={() => void run(acknowledge)}
            >
              Archive verified receipt and resolve request
            </button>
          )}
        </section>
      )}
      {bundle && (
        <section aria-label="Current and proposed inverse">
          <h3>
            {context!.title} · Original DraftVersion #
            {bundle.reviewed.source_version_id}
          </h3>
          <p className="impact-fingerprint">
            Plan {bundle.reviewed.plan_fingerprint}
          </p>
          <Rows
            caption={context!.caption}
            rows={bundle.reviewed.before_restore}
          />
          <Rows
            caption="Proposed inverse — new revisions, additions cancelled, stable IDs retained"
            rows={bundle.reviewed.proposed_restore}
          />
          {bundle.reviewed.blockers.length > 0 && (
            <div role="alert">
              <h3>Blocked — cannot submit</h3>
              <Warnings value={bundle.reviewed.blockers} />
            </div>
          )}
          <details>
            <summary>
              Complete current resource observations (including recorded actual
              Rig)
            </summary>
            <Warnings value={bundle.reviewed.observations} />
          </details>
          <fieldset disabled={frozen || bundle.reviewed.status !== "Current"}>
            <legend>
              {context!.recorded
                ? "Recorded Pending acknowledgements"
                : "Pending warnings — acknowledge each item"}{" "}
              ({context!.acknowledged.length}/{bundle.reviewed.warnings.length})
            </legend>
            <div
              className="draft-warnings-scroll"
              role="region"
              aria-label="Individual Pending warnings"
              tabIndex={0}
            >
              {bundle.reviewed.warnings.map((w) => (
                <label className="restore-warning" key={w.warning_id}>
                  <input
                    type="checkbox"
                    id={`restore-warning-${w.warning_id}`}
                    checked={context!.acknowledged.includes(w.warning_id)}
                    onChange={(e) =>
                      setAck((previous) =>
                        e.target.checked
                          ? [...previous, w.warning_id]
                          : previous.filter((id) => id !== w.warning_id),
                      )
                    }
                  />
                  <span>
                    {w.state} · {w.check} · {w.reason}
                    <br />
                    {w.record_kind}
                    {w.record_id ? ` #${w.record_id}` : ""} {w.local_date ?? ""}
                    <small className="impact-fingerprint">{w.warning_id}</small>
                  </span>
                </label>
              ))}
            </div>
            <label className="day-preview-check">
              <input
                id="confirm-restore-plan"
                type="checkbox"
                checked={context!.confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              I reviewed this exact inverse, including every cancellation,
              reactivation, employee and note. Record only a new unconfirmed
              Draft.
            </label>
          </fieldset>
          <button
            id="submit-draft-restore"
            disabled={!canSubmit}
            onClick={() => void run(submit)}
          >
            Confirm single-version Draft Restore
          </button>
        </section>
      )}
      {source && (
        <details open>
          <summary>
            Original immutable DraftVersion #{source.version_id} — source
            history, not current approval
          </summary>
          <Rows caption="Original Before" rows={source.plan!.before} />
          <Rows caption="Original After" rows={source.after!} />
        </details>
      )}
      {result && (
        <section aria-label="Verified Restore result">
          <h3 id="restore-outcome">
            {result.outcome}
            {result.version_id
              ? ` · DraftRestoreVersion #${result.version_id}`
              : ""}
          </h3>
          <p>
            {result.recorded_at} · Validation pending · Apply=false ·
            Publish=false
          </p>
          {result.after && (
            <Rows
              caption="Exact committed result — preserved stable identities"
              rows={result.after}
            />
          )}
          <p>
            Historical driver, Rig and weekend approval is not new
            certification.
          </p>
          {result.outcome === "Committed" && (
            <button
              id="refresh-restored-week"
              disabled={busy}
              onClick={() => void run((valid) => refresh(result, valid))}
            >
              {refreshed
                ? "Reload saved weekly data (reads only)"
                : "Retry weekly refresh (reads only)"}
            </button>
          )}
          {!pending && (
            <button disabled={busy} onClick={reset}>
              Inspect another original version
            </button>
          )}
        </section>
      )}
      <div className="restore-footer">
        <button id="close-draft-restore" onClick={onClose}>
          {pending ? "Close — keep recovery request" : "Cancel / Close"}
        </button>
        <span>Publish remains unavailable.</span>
      </div>
    </Dialog>
  );
}
