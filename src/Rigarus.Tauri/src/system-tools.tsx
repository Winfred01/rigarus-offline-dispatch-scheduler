import { useEffect, useRef, useState } from "react";
import { Dialog } from "./dialog";
import { readWorkspace, type Workspace } from "./workspace-data";
import {
  appearanceKey,
  defaultAppearance,
  applyAppearance,
  parseAppearance,
  type Appearance,
} from "./appearance";

export type SearchRecord = {
  key: string;
  type: string;
  id: number;
  title: string;
  summary: string;
  destination: string;
  projectId?: number;
  date?: string;
};
export function searchRecords(data: Workspace): SearchRecord[] {
  return [
    ...data.projects.map((p) => ({
      key: `project-${p.id}`,
      type: "Project",
      id: p.id,
      title: p.job_number,
      summary: `${p.site_id} · ${p.site_name}`,
      destination: "Project Management / Projects",
    })),
    ...data.projects.flatMap((p) =>
      p.work_items.map((w) => ({
        key: `work-${w.id}`,
        type: "Work Item",
        id: w.id,
        title: `${p.job_number} · ${w.type} #${w.id}`,
        summary: `${p.site_id} · ${p.site_name} · ${w.estimated_half_days} half-days`,
        destination: "Project Management / Work Item",
        projectId: p.id,
      })),
    ),
    ...data.people.map((p) => ({
      key: `person-${p.id}`,
      type: "Person",
      id: p.id,
      title: p.name,
      summary: `Home Crew · ${data.crews.find((c) => c.id === p.home_crew_id)?.name ?? p.home_crew_id}${p.active ? "" : " · Inactive"}`,
      destination: "People / Employees",
    })),
    ...data.crews.map((c) => ({
      key: `crew-${c.id}`,
      type: "Crew",
      id: c.id,
      title: c.name,
      summary: `${c.type} · Foreman ${data.foremen.find((f) => f.crew_id === c.id)?.employee_name ?? "Unassigned"}`,
      destination: "People / Crews",
    })),
    ...data.rigs.map((r) => ({
      key: `rig-${r.id}`,
      type: "Equipment",
      id: r.id,
      title: `Rig ${r.number}`,
      summary: `${r.type}${r.active ? "" : " · Inactive"}`,
      destination: "Items / Equipment",
    })),
    ...data.assignments.map((a) => ({
      key: `assignment-${a.id}`,
      type: "Schedule",
      id: a.id,
      title: `${a.job_number} · ${a.work_type} · ${a.local_date} ${a.slot}`,
      summary: `${a.site_name} · ${a.crew_name} · Draft · Actual staffing not assigned`,
      destination: "Schedule / Job Schedule",
      date: a.local_date,
    })),
  ];
}

export function GlobalSearch({
  onOpen,
}: {
  onOpen: (record: SearchRecord) => void;
}) {
  const [open, setOpen] = useState(false);
  const [term, setTerm] = useState("");
  const [type, setType] = useState("All types");
  const [records, setRecords] = useState<SearchRecord[]>([]);
  const [index, setIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (!document.querySelector("dialog[open]")) {
          input.current?.focus();
          setOpen(true);
        }
      }
      if (event.key === "Escape") setOpen(false);
    };
    const outside = (event: PointerEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", key);
    document.addEventListener("pointerdown", outside);
    return () => {
      document.removeEventListener("keydown", key);
      document.removeEventListener("pointerdown", outside);
    };
  }, []);
  useEffect(() => {
    if (!open) return;
    let active = true;
    setBusy(true);
    setError("");
    setRecords([]);
    void readWorkspace()
      .then((data) => {
        if (active) setRecords(searchRecords(data));
      })
      .catch((failure) => {
        if (active) setError(String(failure));
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [open, attempt]);
  const matches = records.filter(
    (record) =>
      (type === "All types" || record.type === type) &&
      `${record.title} ${record.summary} ${record.id}`
        .toLocaleLowerCase()
        .includes(term.trim().toLocaleLowerCase()),
  );
  useEffect(() => {
    setIndex(0);
  }, [term, type]);
  useEffect(() => {
    document
      .getElementById(`search-result-${index}`)
      ?.scrollIntoView({ block: "nearest" });
  }, [index]);
  const choose = (record: SearchRecord) => {
    setOpen(false);
    onOpen(record);
  };
  return (
    <div
      className="global-search"
      ref={container}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node))
          setOpen(false);
      }}
    >
      <div className="global-search-input">
        <input
          ref={input}
          aria-label="Search across the workspace"
          role="combobox"
          aria-expanded={open}
          aria-controls="global-results"
          aria-autocomplete="list"
          aria-activedescendant={
            open && matches[index] ? `search-result-${index}` : undefined
          }
          placeholder="Search across the workspace"
          value={term}
          onFocus={() => setOpen(true)}
          onChange={(event) => {
            setTerm(event.target.value);
            setOpen(true);
          }}
          onKeyDown={(event) => {
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
              event.preventDefault();
              setOpen(true);
              setIndex((current) =>
                matches.length
                  ? (current +
                      (event.key === "ArrowDown" ? 1 : -1) +
                      matches.length) %
                    matches.length
                  : 0,
              );
            }
            if (event.key === "Enter" && open && matches[index] && !busy) {
              event.preventDefault();
              choose(matches[index]);
            }
          }}
        />
        <kbd>Ctrl K</kbd>
      </div>
      {open && (
        <div className="search-popover">
          <label>
            Record type
            <select
              aria-label="Record type"
              value={type}
              onChange={(event) => setType(event.target.value)}
            >
              {[
                "All types",
                "Project",
                "Work Item",
                "Person",
                "Crew",
                "Equipment",
                "Schedule",
              ].map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
          {busy && <p role="status">Searching local records…</p>}
          {error && (
            <p className="error" role="alert">
              {error}{" "}
              <button onClick={() => setAttempt(attempt + 1)}>
                Retry search
              </button>
            </p>
          )}
          <div
            id="global-results"
            role="listbox"
            aria-label="Local search results"
          >
            {!busy &&
              !error &&
              matches.map((record, i) => (
                <button
                  key={record.key}
                  id={`search-result-${i}`}
                  role="option"
                  aria-selected={i === index}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => choose(record)}
                >
                  <strong>
                    {record.title} <small>#{record.id}</small>
                  </strong>
                  <span>
                    {record.type} · {record.summary}
                  </span>
                  <small>{record.destination}</small>
                </button>
              ))}
          </div>
          {!busy && !error && (
            <p role="status">
              {matches.length
                ? `${matches.length} results · ↑ ↓ to select · Enter to open`
                : "No matches. Try a shorter query or choose All types."}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function AppearanceSettings({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => void;
}) {
  const [saved] = useState(() => {
    try {
      return parseAppearance(localStorage.getItem(appearanceKey));
    } catch {
      return { ...defaultAppearance };
    }
  });
  const [preview, setPreview] = useState<Appearance>(saved);
  const [error, setError] = useState("");
  const committed = useRef(false);
  useEffect(() => {
    applyAppearance(preview);
  }, [preview]);
  useEffect(
    () => () => {
      if (!committed.current) applyAppearance(saved);
    },
    [saved],
  );
  return (
    <Dialog title="Appearance" onClose={onClose}>
      <div className="settings-fields">
        {(
          [
            ["accent", "Accent colour", ["Blue", "Teal"]],
            ["font", "Font family", ["Segoe UI", "Arial"]],
            ["size", "Base font size", ["14", "16"]],
            ["density", "Table density", ["Comfortable", "Compact"]],
          ] as const
        ).map(([key, label, options]) => (
          <label key={key}>
            {label}
            <select
              value={preview[key]}
              onChange={(event) =>
                setPreview({ ...preview, [key]: event.target.value })
              }
            >
              {options.map((value) => (
                <option key={value} value={value}>
                  {value}
                  {key === "size" ? " px" : ""}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <button>Accent preview</button>
      <p>Changes preview immediately. Save to keep them on this device.</p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="actions">
        <button
          className="secondary-button"
          onClick={() => setPreview({ ...defaultAppearance })}
        >
          Reset preview
        </button>
        <button className="secondary-button" onClick={onClose}>
          Cancel
        </button>
        <button
          onClick={() => {
            try {
              localStorage.setItem(appearanceKey, JSON.stringify(preview));
              committed.current = true;
              onSaved();
              onClose();
            } catch {
              setError(
                "Appearance could not be saved on this device. Cancel restores the previous settings; retry Save to keep the preview.",
              );
            }
          }}
        >
          Save appearance
        </button>
      </div>
    </Dialog>
  );
}

export function Help({ view, onClose }: { view: string; onClose: () => void }) {
  return (
    <Dialog title={`Help · ${view}`} onClose={onClose}>
      <h3>Find a record</h3>
      <p>
        Ctrl+K focuses local search. Filter by record type. Use ↑/↓ to select
        and Enter to open the exact record. Escape closes search or the active
        panel. Tab and Shift+Tab move between controls.
      </p>
      {["Job Schedule", "Crew Board", "Overview"].includes(view) ? (
        <>
          <h3>Review a week</h3>
          <p>
            Previous week, Today, Next week and the date jump show
            Sunday–Saturday in local calendar dates. Crew filter limits both
            boards. Scroll inside the grid to reach every crew; date headings
            and the roster stay visible.
          </p>
          <h3>Plan a draft</h3>
          <p>
            Expand Unscheduled work items or choose Assign Work Item. Save
            places the visit in its week. Open a card to edit or cancel the
            saved draft. Form Cancel makes no write. Actual staffing is separate
            from Home roster. Review &amp; Publish explains the outstanding
            safety gates.
          </p>
        </>
      ) : (
        <>
          <h3>Work in {view}</h3>
          <p>
            Use this view’s labelled search and record actions. Edit forms
            preserve existing records until Save; Cancel returns without
            applying your input. Data imports require a reviewed preview and
            explicit confirmation.
          </p>
        </>
      )}
      <h3>Publication and exports</h3>
      <p>
        Formal export requires a validated immutable Published snapshot.
        Personnel, time off, driver and resource checks are tracked in
        #22/#15/#23; employee week/export follows #71 and company/Crew reports
        follow #17/#32.
      </p>
    </Dialog>
  );
}
