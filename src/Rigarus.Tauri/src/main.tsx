import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState, type SubmitEvent } from "react";
import { createRoot } from "react-dom/client";
import { ProjectMaster } from "./projects";
import "./styles.css";

type DemoProject = {
  job_number: string;
  site_name: string;
  note: string;
};

const maximumLength = 200;

function DemoDashboard({ active }: { active: boolean }) {
  const [project, setProject] = useState<DemoProject>();
  const [note, setNote] = useState("");
  const [working, setWorking] = useState(true);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setWorking(true);
    setError("");
    try {
      const result = await invoke<DemoProject>("read_demo");
      setProject(result);
      setNote(result.note);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setWorking(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setWorking(true);
    setStatus("");
    setError("");
    try {
      const saved = await invoke<DemoProject>("save_demo_note", { note });
      setProject(saved);
      setNote(saved.note);
      setStatus("Note saved.");
    } catch (failure) {
      setError(String(failure));
    } finally {
      setWorking(false);
    }
  }

  return (
    <>
      <main className="frame">
        {active && <h1>Dispatch dashboard</h1>}
        <section aria-labelledby="project-title">
          <div className="project">
            <h2 id="project-title">Synthetic project</h2>
            {project && (
              <dl>
                <div>
                  <dt>Job #</dt>
                  <dd>{project.job_number}</dd>
                </div>
                <div>
                  <dt>Site</dt>
                  <dd>{project.site_name}</dd>
                </div>
              </dl>
            )}
          </div>
          {project ? (
            <form onSubmit={save}>
              <div className="field-label">
                <label htmlFor="demo-note">Demo note</label>
                <span id="note-limit">
                  {note.length} / {maximumLength}
                </span>
              </div>
              <textarea
                id="demo-note"
                aria-describedby="note-limit"
                maxLength={maximumLength}
                value={note}
                readOnly={working}
                onChange={(event) => {
                  setNote(event.target.value);
                  setStatus("");
                  setError("");
                }}
              />
              <div className="actions">
                <button disabled={working || note === project.note}>
                  Save note
                </button>
                <span role="status">{working ? "Saving note…" : status}</span>
              </div>
            </form>
          ) : working ? (
            <p role="status">Opening the local database…</p>
          ) : (
            <button onClick={() => void load()}>Retry</button>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </section>
      </main>
    </>
  );
}

function App() {
  const [page, setPage] = useState<"dashboard" | "projects">("dashboard");
  return (
    <>
      <header className="app-header">
        <div className="frame header-content">
          <strong>Rigarus Dispatch</strong>
          <nav aria-label="Workspace">
            <button
              className="nav-button"
              aria-current={page === "dashboard" ? "page" : undefined}
              onClick={() => setPage("dashboard")}
            >
              Dashboard
            </button>
            <button
              className="nav-button"
              aria-current={page === "projects" ? "page" : undefined}
              onClick={() => setPage("projects")}
            >
              Projects
            </button>
          </nav>
          <span className="mode">Demo mode</span>
        </div>
      </header>
      <div hidden={page !== "dashboard"}>
        <DemoDashboard active={page === "dashboard"} />
      </div>
      <div hidden={page !== "projects"}>
        {page === "projects" && <ProjectMaster />}
      </div>
    </>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
