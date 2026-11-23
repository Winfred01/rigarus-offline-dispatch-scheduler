import { invoke } from "@tauri-apps/api/core";
import { ImportPreview } from "./import-preview";
import { useEffect, useState, type SubmitEvent } from "react";
import { createRoot } from "react-dom/client";
import { EmployeeRoster } from "./employees";
import { AvailabilityCalendar } from "./availability";
import { CrewRoster } from "./roster";
import { RigInventory } from "./rigs";
import { ProjectMaster } from "./projects";
import { Schedule, publishBlockers, type ScheduleView } from "./schedule";
import {
  GlobalSearch,
  AppearanceSettings,
  Help,
  type SearchRecord,
} from "./system-tools";
import { applyAppearance, parseAppearance, appearanceKey } from "./appearance";
import { readWorkspace } from "./workspace-data";
import { Dialog } from "./dialog";
import { localToday, type AssignmentSeed } from "./assignment-fields";
import "./styles.css";
import "./desktop.css";

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

type Module =
  "Schedule" | "Project Management" | "People" | "Items" | "Reports" | "Data";
const modules: Module[] = [
  "Schedule",
  "Project Management",
  "People",
  "Items",
  "Reports",
  "Data",
];
const moduleIcons = [
  "calendar",
  "folder",
  "people",
  "box",
  "report",
  "database",
];
function NavIcon({ kind }: { kind: string }) {
  const paths: Record<string, string> = {
    calendar: "M4 5h16v15H4z M4 9h16 M8 3v4 M16 3v4 M8 12h3 M13 12h3 M8 16h3",
    folder: "M3 6h7l2 3h9v11H3z",
    people:
      "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M2 21v-3a7 7 0 0 1 14 0v3 M17 4a4 4 0 0 1 0 8 M19 15a6 6 0 0 1 3 6",
    box: "M3 7l9-4 9 4v10l-9 4-9-4z M3 7l9 4 9-4 M12 11v10",
    report: "M5 3h14v18H5z M8 17v-5 M12 17V7 M16 17v-8",
    database:
      "M3 6c0-5 18-5 18 0s-18 5-18 0v12c0 5 18 5 18 0V6 M3 12c0 5 18 5 18 0",
    settings:
      "M12 3v3 M12 18v3 M3 12h3 M18 12h3 M5 5l3 3 M16 16l3 3 M5 19l3-3 M16 8l3-3 M17 12a5 5 0 1 0-10 0 5 5 0 0 0 10 0",
    help: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20 M9 8a3 3 0 1 1 4 3v3 M12 17v1",
  };
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      aria-hidden="true"
    >
      <path d={paths[kind]} />
    </svg>
  );
}
function App() {
  const [module, setModule] = useState<Module>("Schedule");
  const [view, setView] = useState<ScheduleView>("Job Schedule");
  const [scheduleDay, setScheduleDay] = useState(localToday);
  const [employeeId, setEmployeeId] = useState(0);
  const [panel, setPanel] = useState("Employees");
  const [assignmentSeed, setAssignmentSeed] = useState<AssignmentSeed>();
  const [target, setTarget] = useState<{ id: number; date: string }>();
  const [tool, setTool] = useState<"settings" | "help">();
  const [status, setStatus] = useState("");
  const [record, setRecord] = useState<SearchRecord>();
  const [details, setDetails] = useState<[string, string][]>([]);
  const [recordError, setRecordError] = useState("");
  useEffect(() => {
    try {
      applyAppearance(parseAppearance(localStorage.getItem(appearanceKey)));
    } catch {
      applyAppearance(parseAppearance(null));
    }
  }, []);
  const currentView =
    module === "Schedule"
      ? view
      : module === "Project Management"
        ? "Projects"
        : module === "People"
          ? panel
          : module === "Items"
            ? "Equipment"
            : module === "Reports"
              ? "Weekly Export"
              : panel === "Demo note"
                ? "Demo note"
                : "Import preview";
  useEffect(() => {
    if (!record) return;
    let active = true;
    setDetails([]);
    setRecordError("");
    void readWorkspace()
      .then((data) => {
        let value: object | undefined;
        if (record.type === "Project")
          value = data.projects.find((p) => p.id === record.id);
        if (record.type === "Work Item")
          value = data.projects
            .flatMap((p) => p.work_items)
            .find((w) => w.id === record.id);
        if (record.type === "Person")
          value = data.people.find((p) => p.id === record.id);
        if (record.type === "Crew")
          value = data.crews.find((c) => c.id === record.id);
        if (record.type === "Equipment")
          value = data.rigs.find((r) => r.id === record.id);
        if (!value) throw Error("This record no longer exists. Search again.");
        if (active)
          setDetails(
            Object.entries(value)
              .filter(([, value]) => !Array.isArray(value))
              .map(([key, value]) => [
                key.replaceAll("_", " "),
                String(value ?? "Not configured"),
              ]),
          );
      })
      .catch((error) => {
        if (active) setRecordError(String(error));
      });
    return () => {
      active = false;
    };
  }, [record]);
  function openRecord(value: SearchRecord) {
    if (value.type === "Schedule" && value.date) {
      setModule("Schedule");
      setView("Job Schedule");
      setAssignmentSeed(undefined);
      setTarget({ id: value.id, date: value.date });
      return;
    }
    setModule(
      value.type === "Person" || value.type === "Crew"
        ? "People"
        : value.type === "Equipment"
          ? "Items"
          : "Project Management",
    );
    setPanel(value.type === "Crew" ? "Crews" : "Employees");
    setRecord(value);
  }
  function openEmployeeWeek(id: number) {
    setEmployeeId(id);
    setRecord(undefined);
    setAssignmentSeed(undefined);
    setTarget(undefined);
    setModule("Schedule");
    setView("Employee Week");
  }
  return (
    <div className="desktop-shell">
      <aside className="module-rail">
        <div className="brand">
          <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
            <path
              d="M6 26V4h11l7 6-7 7 8 9h-7l-8-10h6l3-5-4-2h-3v17z"
              fill="currentColor"
            />
          </svg>
          <strong>RIGARUS</strong>
        </div>
        <nav aria-label="Workspace">
          {modules.map((name, i) => (
            <button
              key={name}
              aria-current={module === name ? "page" : undefined}
              onClick={() => {
                setModule(name);
                setAssignmentSeed(undefined);
                setTarget(undefined);
                setStatus("");
                if (name === "People") setPanel("Employees");
                if (name === "Data") setPanel("Import preview");
              }}
            >
              <NavIcon kind={moduleIcons[i]} />
              <span>{name}</span>
            </button>
          ))}
        </nav>
        <div className="rail-tools">
          <button onClick={() => setTool("settings")}>
            <NavIcon kind="settings" />
            Settings
          </button>
          <button onClick={() => setTool("help")}>
            <NavIcon kind="help" />
            Help
          </button>
        </div>
      </aside>
      <div className="desktop-workspace">
        <header className="desktop-topbar">
          <strong>{module}</strong>
          <GlobalSearch onOpen={openRecord} />
        </header>
        <div className="desktop-content">
          {module === "Schedule" && (
            <Schedule
              seed={assignmentSeed}
              target={target}
              view={view}
              onView={setView}
              day={scheduleDay}
              onDay={setScheduleDay}
              employeeId={employeeId}
              onEmployee={setEmployeeId}
            />
          )}
          {module === "Project Management" && (
            <ProjectMaster
              onAssign={(projectId, workItemId) => {
                setAssignmentSeed({ projectId, workItemId });
                setTarget(undefined);
                setModule("Schedule");
                setView("Job Schedule");
              }}
            />
          )}
          {module === "People" && (
            <>
              <nav className="view-tabs section-tabs" aria-label="People views">
                {["Employees", "Crews", "Availability"].map((name) => (
                  <button
                    key={name}
                    aria-current={panel === name ? "page" : undefined}
                    onClick={() => setPanel(name)}
                  >
                    {name}
                  </button>
                ))}
              </nav>
              {panel === "Crews" ? (
                <CrewRoster />
              ) : panel === "Availability" ? (
                <AvailabilityCalendar />
              ) : (
                <EmployeeRoster onOpenWeek={openEmployeeWeek} />
              )}
            </>
          )}
          {module === "Items" && <RigInventory />}
          {module === "Reports" && (
            <main className="frame project-master">
              <p className="breadcrumb">Reports / Weekly Export</p>
              <h1>Weekly Export</h1>
              <section>
                <h2>Validated Published version required</h2>
                <ul>
                  {publishBlockers.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
                <div className="actions">
                  <button disabled>Company PDF unavailable</button>
                  <button disabled>Crew PDF unavailable</button>
                </div>
                <p>
                  Company weekly PDF: #17. Production Legal/Letter and Crew
                  layouts: #32. Employee weekly PDF/XLSX: #71.
                </p>
              </section>
            </main>
          )}
          {module === "Data" && (
            <>
              <nav className="view-tabs section-tabs" aria-label="Data tools">
                {["Import preview", "Demo note"].map((name) => (
                  <button
                    key={name}
                    aria-current={panel === name ? "page" : undefined}
                    onClick={() => setPanel(name)}
                  >
                    {name}
                  </button>
                ))}
              </nav>
              {panel === "Demo note" ? (
                <DemoDashboard active />
              ) : (
                <ImportPreview />
              )}
            </>
          )}
          {status && (
            <p className="device-status" role="status">
              {status}
            </p>
          )}
        </div>
      </div>
      {tool === "settings" && (
        <AppearanceSettings
          onClose={() => setTool(undefined)}
          onSaved={() => setStatus("Appearance saved on this device.")}
        />
      )}
      {tool === "help" && (
        <Help view={currentView} onClose={() => setTool(undefined)} />
      )}
      {record && (
        <Dialog
          title={`${record.title} · #${record.id}`}
          onClose={() => setRecord(undefined)}
        >
          <p>{record.destination}</p>
          {recordError ? (
            <p className="error" role="alert">
              {recordError}
            </p>
          ) : !details.length ? (
            <p role="status">Reading local record…</p>
          ) : (
            <dl className="record-detail">
              {details.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          )}
          <p>
            Home Crew, default Rig and driver status are master data. Actual
            staffing not assigned.
          </p>
          {record.type === "Person" && !recordError && !!details.length && (
            <button onClick={() => openEmployeeWeek(record.id)}>
              Open employee week
            </button>
          )}
          <button onClick={() => setRecord(undefined)}>Back to {module}</button>
        </Dialog>
      )}
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
