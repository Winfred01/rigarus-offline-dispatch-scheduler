import { invoke } from "@tauri-apps/api/core";
import { useState, type SubmitEvent } from "react";
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
        throw new Error("Paste CSV text of at most 5 MiB.");
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
              ["text", "Paste Text"],
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
            <p>
              Use Project Number, Site ID and Site Name, one project per row.
              Keep Excel identifiers as text. Up to 2000 rows and 5 MiB.
            </p>
            {kind === "text" ? (
              <>
                <label htmlFor="bulk-text">
                  CSV text (include the header row; quote names containing
                  commas)
                </label>
                <textarea
                  id="bulk-text"
                  disabled={busy}
                  value={text}
                  onChange={(event) => {
                    setText(event.target.value);
                    invalidate();
                  }}
                />
              </>
            ) : (
              <>
                <label htmlFor="bulk-workbook">Excel workbook (.xlsx)</label>
                <input
                  id="bulk-workbook"
                  type="file"
                  accept=".xlsx"
                  disabled={busy}
                  onChange={(event) => {
                    setFile(event.target.files?.[0]);
                    invalidate();
                  }}
                />
              </>
            )}
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
