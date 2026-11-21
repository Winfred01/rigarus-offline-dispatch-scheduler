import { invoke } from "@tauri-apps/api/core";
import { useRef, useState, type SubmitEvent } from "react";
import { PreviewResults, readWorkbook, type Preview } from "./import-preview";

type BulkPreview = {
  preview: Preview;
  preview_id: string;
  ready_count: number;
  skipped_count: number;
};
type Source = { kind: "text" | "xlsx"; content: string };
type Confirmation = {
  created_ids: number[];
  created_count: number;
  skipped_count: number;
};

const examples = [
  {
    id: "tsv",
    label: "Excel / TAB-separated",
    text: "Project Number\tSite ID\tSite Name\r\nVM-0001\t0001\tSynthetic VM Yard A\r\nVM-0002\t0002\tSynthetic VM Yard B\r\nVM-0003\t0003\tNorth Field Pad 1\r\n",
  },
  {
    id: "csv",
    label: "CSV / plain text",
    text: "Project Number,Site ID,Site Name\r\nVM-0001,0001,Synthetic VM Yard A\r\nVM-0002,0002,Synthetic VM Yard B\r\nVM-0003,0003,North Field Pad 1\r\n",
  },
] as const;

const help = [
  [
    "formats",
    "Accepted formats",
    "Copy the header and cells in Excel with Ctrl+C, then paste with Ctrl+V. TAB-separated text and CSV are accepted. In CSV, quote a site name containing a comma.",
  ],
  [
    "rows",
    "One project per row",
    "Include Project Number, Site ID and Site Name in that order. Keep identifiers as text to preserve leading zeroes.",
  ],
  [
    "preview",
    "Preview is read-only",
    "Preview and Cancel do not save projects. Changing text, file or tab removes the previous confirmation; preview again before saving.",
  ],
  [
    "overwrite",
    "No overwrite",
    "Only ready new projects are added after confirmation. Existing projects and work items stay unchanged. Duplicate rows are skipped; a failed transaction rolls back.",
  ],
  [
    "limits",
    "Limits",
    "Up to 2,000 data rows and 5 MiB. Excel files must be .xlsx. Formulas and external references are not evaluated; review source-cell diagnostics.",
  ],
] as const;

function CopyExample({ id, label, text }: (typeof examples)[number]) {
  const field = useRef<HTMLTextAreaElement>(null);
  const [message, setMessage] = useState("");

  async function copy() {
    setMessage("");
    try {
      if (!navigator.clipboard?.writeText)
        throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(text);
      setMessage(`${label} example copied.`);
    } catch {
      // Keep the exact example selectable when clipboard permissions are denied.
      field.current?.focus();
      field.current?.select();
      setMessage(
        "Copy unavailable. The example is selected; press Ctrl+C to copy it.",
      );
    }
  }

  return (
    <div className="bulk-example">
      <div className="page-heading">
        <label htmlFor={`bulk-example-${id}`}>{label} example</label>
        <button
          type="button"
          className="secondary-button"
          onClick={() => void copy()}
        >
          Copy {id.toUpperCase()} example
        </button>
      </div>
      <textarea
        id={`bulk-example-${id}`}
        ref={field}
        readOnly
        value={text}
        rows={5}
        spellCheck={false}
      />
      <p className="project-status" role="status">
        {message}
      </p>
    </div>
  );
}

export function BulkProjects({
  onCancel,
  onSaved,
}: {
  onCancel: () => void;
  onSaved: (message: string, firstId?: number) => void;
}) {
  const [kind, setKind] = useState<Source["kind"]>("text");
  const [text, setText] = useState("Project Number,Site ID,Site Name\n");
  const [file, setFile] = useState<File>();
  const [result, setResult] = useState<BulkPreview>();
  const [source, setSource] = useState<Source>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function invalidate() {
    setResult(undefined);
    setSource(undefined);
    setError("");
  }

  async function preview(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    invalidate();
    setBusy(true);
    try {
      let content = text;
      if (kind === "xlsx") {
        if (
          !file ||
          !file.name.toLowerCase().endsWith(".xlsx") ||
          file.size > 5 * 1024 * 1024
        ) {
          throw new Error("Choose an .xlsx workbook of at most 5 MiB.");
        }
        content = await readWorkbook(file);
      } else if (new Blob([text]).size > 5 * 1024 * 1024) {
        throw new Error("Paste Excel cells or CSV text of at most 5 MiB.");
      }
      const input = { kind, content };
      const checked = await invoke<BulkPreview>("bulk_projects", {
        action: "preview",
        input,
      });
      setSource(input);
      setResult(checked);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (busy || !result || !source) return;
    setBusy(true);
    setError("");
    try {
      const saved = await invoke<Confirmation>("bulk_projects", {
        action: "confirm",
        input: { ...source, preview_id: result.preview_id },
      });
      onSaved(
        `Bulk Add complete: ${saved.created_count} created, ${saved.skipped_count} skipped.`,
        saved.created_ids[0],
      );
    } catch (failure) {
      setResult(undefined);
      setSource(undefined);
      setError(
        String(failure) +
          " Preview again to check the current records before retrying.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function downloadTemplate() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await invoke<{ content: string }>("bulk_projects", {
        action: "template",
        input: {},
      });
      const bytes = Uint8Array.from(atob(response.content), (c) =>
        c.charCodeAt(0),
      );
      const url = URL.createObjectURL(
        new Blob([bytes], {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = "Rigarus-Projects-Template.xlsx";
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section aria-labelledby="bulk-title">
        <div className="page-heading">
          <h2 id="bulk-title">Bulk Add Projects</h2>
          <button
            type="button"
            className="secondary-button"
            disabled={busy}
            onClick={() => void downloadTemplate()}
          >
            Download Excel Template
          </button>
        </div>
        <p>
          Create new projects only. Existing records and work items stay
          unchanged. Preview first, then confirm the ready rows.
        </p>
        <div role="tablist" aria-label="Bulk project source">
          {(
            [
              ["text", "Paste from Excel or plain text"],
              ["xlsx", "Upload Excel"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={kind === value}
              tabIndex={kind === value ? 0 : -1}
              id={`bulk-tab-${value}`}
              aria-controls="bulk-input-panel"
              className="nav-button"
              disabled={busy}
              onClick={() => {
                if (kind !== value) {
                  setKind(value);
                  setFile(undefined);
                  invalidate();
                }
              }}
              onKeyDown={(event) => {
                if (
                  !["ArrowLeft", "ArrowRight", "Home", "End"].includes(
                    event.key,
                  )
                )
                  return;
                event.preventDefault();
                const next =
                  event.key === "Home"
                    ? "text"
                    : event.key === "End"
                      ? "xlsx"
                      : kind === "text"
                        ? "xlsx"
                        : "text";
                setKind(next);
                setFile(undefined);
                invalidate();
                document.getElementById(`bulk-tab-${next}`)?.focus();
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <form onSubmit={preview} className="project-search">
          <div
            id="bulk-input-panel"
            role="tabpanel"
            aria-labelledby={`bulk-tab-${kind}`}
          >
            <p id="bulk-input-help">
              Use Project Number, Site ID and Site Name, one project per row.
              Keep Excel identifiers as text. Up to 2000 rows and 5 MiB.
            </p>
            {kind === "text" ? (
              <>
                <label htmlFor="bulk-text">
                  Paste from Excel or plain text
                </label>
                <p id="bulk-paste-help" className="project-status">
                  In Excel, select the header and rows, press Ctrl+C, then paste
                  here with Ctrl+V. CSV with the same headers also works.
                </p>
                <textarea
                  id="bulk-text"
                  aria-describedby="bulk-input-help bulk-paste-help"
                  placeholder="Paste header and rows from Excel, or CSV text…"
                  disabled={busy}
                  value={text}
                  onChange={(event) => {
                    setText(event.target.value);
                    invalidate();
                  }}
                />
                <div
                  className="bulk-examples"
                  aria-label="Copyable project examples"
                >
                  {examples.map((example) => (
                    <CopyExample key={example.id} {...example} />
                  ))}
                </div>
              </>
            ) : (
              <>
                <label htmlFor="bulk-workbook">Excel workbook (.xlsx)</label>
                <input
                  id="bulk-workbook"
                  type="file"
                  accept=".xlsx"
                  aria-describedby="bulk-input-help"
                  disabled={busy}
                  onChange={(event) => {
                    setFile(event.target.files?.[0]);
                    invalidate();
                  }}
                />
              </>
            )}
          </div>
          <div className="bulk-help" aria-label="Bulk Add help">
            {help.map(([id, label, description]) => (
              <span key={id}>
                <button
                  type="button"
                  className="secondary-button"
                  aria-label={`Help: ${label}`}
                  popoverTarget={`bulk-help-${id}`}
                >
                  {label} <span aria-hidden="true">ⓘ</span>
                </button>
                <div
                  id={`bulk-help-${id}`}
                  popover="auto"
                  className="bulk-help-popover"
                  role="note"
                >
                  <strong>{label}</strong>
                  <p>{description}</p>
                  <button
                    type="button"
                    className="secondary-button"
                    popoverTarget={`bulk-help-${id}`}
                    popoverTargetAction="hide"
                  >
                    Close help
                  </button>
                </div>
              </span>
            ))}
          </div>
          <div className="actions">
            <button disabled={busy || (kind === "xlsx" && !file)}>
              Preview projects
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={onCancel}
            >
              Cancel Bulk Add
            </button>
          </div>
        </form>
        <p role="status">
          {busy
            ? "Checking local projects…"
            : result
              ? `Ready: ${result.ready_count} · Skipped: ${result.skipped_count}. No records changed by preview.`
              : "A fresh preview is required after input changes."}
        </p>
        {result && (
          <button
            type="button"
            disabled={
              busy ||
              !result.ready_count ||
              result.preview.diagnostics.length > 0
            }
            onClick={() => void confirm()}
          >
            Confirm {result.ready_count}{" "}
            {result.ready_count === 1 ? "project" : "projects"}
          </button>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </section>
      {result && <PreviewResults result={result.preview} />}
    </>
  );
}
