import { invoke } from "@tauri-apps/api/core";
import { useRef, useState, type SubmitEvent } from "react";

type Diagnostic = {
  source: string;
  message: string;
  severity: "Error" | "Warning";
};
type PreviewRow = {
  source: string;
  values: Record<string, string>;
  action: "Create" | "Update" | "Skip";
  status: "Ready" | "Duplicate" | "Review" | "Invalid";
  diagnostics: Diagnostic[];
};
type Preview = {
  rows: PreviewRow[];
  diagnostics: Diagnostic[];
  counts: Record<string, number>;
};

function readWorkbook(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.onerror = () =>
      reject(new Error("Could not read the selected workbook."));
    reader.readAsDataURL(file);
  });
}

export function ImportPreview() {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File>();
  const [result, setResult] = useState<Preview>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  async function preview(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || busy) return;
    setBusy(true);
    setError("");
    setResult(undefined);
    setStatus("");
    try {
      if (
        !file.name.toLowerCase().endsWith(".xlsx") ||
        file.size > 5 * 1024 * 1024
      ) {
        throw new Error("Choose an .xlsx workbook of at most 5 MiB.");
      }
      const content = await readWorkbook(file);
      setResult(await invoke<Preview>("preview_import", { content }));
      setStatus("Preview complete. No records were changed.");
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  function cancel() {
    setFile(undefined);
    setResult(undefined);
    setError("");
    setStatus("Preview cancelled. No records were changed.");
    if (input.current) input.current.value = "";
  }

  return (
    <main className="frame project-master">
      <h1>Import preview</h1>
      <section aria-labelledby="workbook-preview-title">
        <h2 id="workbook-preview-title">Check an Excel workbook</h2>
        <p>
          Preview only. Review the proposed outcomes and source cells before
          planning an import. The workbook and project records stay on this
          computer.
        </p>
        <p>
          Use row 1 for Job #, Site ID and Site Name. Optional columns are
          Description, Customer, Crew Type, Crew Count and Estimated Half-days.
          Keep Job # and Site ID as text.
        </p>
        <form onSubmit={preview}>
          <label htmlFor="import-workbook">
            Excel workbook (.xlsx, up to 5 MiB)
          </label>
          <input
            id="import-workbook"
            ref={input}
            type="file"
            accept=".xlsx"
            disabled={busy}
            onChange={(event) => {
              setFile(event.target.files?.[0]);
              setResult(undefined);
              setError("");
              setStatus("");
            }}
          />
          <div className="actions">
            <button disabled={busy || !file}>Preview workbook</button>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={cancel}
            >
              Cancel preview
            </button>
          </div>
        </form>
        <p role="status">{busy ? "Checking workbook…" : status}</p>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </section>
      {result && (
        <section
          className="project-detail"
          aria-labelledby="import-result-title"
        >
          <h2 id="import-result-title">Proposed outcomes</h2>
          <p>
            {["Ready", "Duplicate", "Review", "Invalid"]
              .map((label) => label + ": " + (result.counts[label] ?? 0))
              .join(" · ")}
          </p>
          {result.diagnostics.length > 0 && (
            <ul>
              {result.diagnostics.map((issue, index) => (
                <li key={index}>
                  {issue.source} — {issue.message}
                </li>
              ))}
            </ul>
          )}
          {result.rows.length > 0 && (
            <div className="project-table">
              <table>
                <thead>
                  <tr>
                    {[
                      "Source",
                      "Job #",
                      "Site ID",
                      "Site Name",
                      "Proposed",
                      "Status",
                      "Fields and diagnostics",
                    ].map((label) => (
                      <th scope="col" key={label}>
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((row) => (
                    <tr key={row.source}>
                      <td>{row.source}</td>
                      <td>{row.values["Job #"]}</td>
                      <td>{row.values["Site ID"]}</td>
                      <td>{row.values["Site Name"]}</td>
                      <td>{row.action}</td>
                      <td>{row.status}</td>
                      <td>
                        <details>
                          <summary>
                            Review fields
                            {row.diagnostics.length ? " and issues" : ""}
                          </summary>
                          <dl>
                            {Object.entries(row.values).map(
                              ([label, value]) => (
                                <div key={label}>
                                  <dt>{label}</dt>
                                  <dd>{value || "Blank"}</dd>
                                </div>
                              ),
                            )}
                          </dl>
                          {row.diagnostics.length > 0 && (
                            <ul>
                              {row.diagnostics.map((issue, index) => (
                                <li key={index}>
                                  {issue.severity} · {issue.source} —{" "}
                                  {issue.message}
                                </li>
                              ))}
                            </ul>
                          )}
                        </details>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
