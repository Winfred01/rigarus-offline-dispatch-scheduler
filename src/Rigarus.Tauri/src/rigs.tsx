import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState, type SubmitEvent } from "react";

type Crew = { id: number; name: string; type: string; active: boolean };
type RigDraft = {
  number: string;
  type: string;
  notes: string;
  default_crew_id: number | null;
  active: boolean;
};
type Rig = RigDraft & { id: number };
const emptyRig: RigDraft = {
  number: "",
  type: "",
  notes: "",
  default_crew_id: null,
  active: true,
};

function crewLabel(crew: Crew) {
  return (
    crew.name +
    " (" +
    crew.type +
    " #" +
    crew.id +
    (crew.active ? ")" : ", inactive)")
  );
}

export function RigInventory() {
  const [rigs, setRigs] = useState<Rig[]>([]);
  const [crews, setCrews] = useState<Crew[]>([]);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [editor, setEditor] = useState<{
    id: number | null;
    draft: RigDraft;
  }>();
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const crewsById = new Map(crews.map((crew) => [crew.id, crew]));

  async function load(term: string) {
    const [matches, defaults] = await Promise.all([
      invoke<Rig[]>("search_rigs", { term }),
      invoke<Crew[]>("search_crews", { term: "" }),
    ]);
    setRigs(matches);
    setCrews(defaults);
    setAppliedSearch(term);
  }

  async function refresh(term: string) {
    setBusy(true);
    setError("");
    setStatus("");
    try {
      await load(term);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh("");
  }, []);

  function edit(rig?: Rig) {
    setError("");
    setStatus("");
    if (rig) {
      const { number, type, notes, default_crew_id, active } = rig;
      setEditor({
        id: rig.id,
        draft: { number, type, notes, default_crew_id, active },
      });
    } else {
      setEditor({ id: null, draft: emptyRig });
    }
  }

  function update(changes: Partial<RigDraft>) {
    if (editor)
      setEditor({ ...editor, draft: { ...editor.draft, ...changes } });
  }

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || busy) return;
    setBusy(true);
    setError("");
    try {
      await invoke<Rig>("save_rig", { id: editor.id, rig: editor.draft });
      setEditor(undefined);
      setStatus("Rig saved.");
      await load(appliedSearch);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="frame project-master">
      <div className="page-heading">
        <h1>Rigs</h1>
        <button disabled={busy || !!editor} onClick={() => edit()}>
          New rig
        </button>
      </div>
      {editor ? (
        <section aria-labelledby="rig-editor-title">
          <h2 id="rig-editor-title">
            {editor.id === null ? "New rig" : "Edit rig"}
          </h2>
          <form className="project-editor" onSubmit={save}>
            <fieldset disabled={busy}>
              <div className="project-fields">
                <label>
                  Rig #
                  <input
                    id="rig-number"
                    value={editor.draft.number}
                    maxLength={50}
                    required
                    onChange={(event) => update({ number: event.target.value })}
                  />
                </label>
                <label>
                  Type
                  <input
                    id="rig-type"
                    value={editor.draft.type}
                    maxLength={100}
                    required
                    onChange={(event) => update({ type: event.target.value })}
                  />
                </label>
                <label>
                  Default crew
                  <select
                    id="rig-crew"
                    value={editor.draft.default_crew_id ?? ""}
                    onChange={(event) =>
                      update({
                        default_crew_id: event.target.value
                          ? Number(event.target.value)
                          : null,
                      })
                    }
                  >
                    <option value="">Unassigned</option>
                    {crews.map((crew) => (
                      <option key={crew.id} value={crew.id}>
                        {crewLabel(crew)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Status
                  <select
                    id="rig-active"
                    value={editor.draft.active ? "active" : "inactive"}
                    onChange={(event) =>
                      update({ active: event.target.value === "active" })
                    }
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </label>
              </div>
              <label htmlFor="rig-notes">Notes</label>
              <textarea
                id="rig-notes"
                value={editor.draft.notes}
                maxLength={2000}
                onChange={(event) => update({ notes: event.target.value })}
              />
              <div className="actions">
                <button>Save rig</button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setEditor(undefined);
                    setError("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </fieldset>
          </form>
        </section>
      ) : (
        <section aria-labelledby="rig-list-title">
          <h2 id="rig-list-title">Rig inventory</h2>
          <form
            className="project-search"
            onSubmit={(event) => {
              event.preventDefault();
              if (!busy) void refresh(search);
            }}
          >
            <label htmlFor="rig-search">Rig #, type or notes</label>
            <div className="search-controls">
              <input
                id="rig-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <button disabled={busy}>Search</button>
            </div>
          </form>
          <p className="project-status" role="status">
            {busy ? "Loading rigs…" : status}
          </p>
          {rigs.length ? (
            <div className="project-table">
              <table>
                <thead>
                  <tr>
                    {["Rig #", "Type", "Default crew", "Status", "Action"].map(
                      (label) => (
                        <th key={label} scope="col">
                          {label}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {rigs.map((rig) => {
                    const crew = crewsById.get(rig.default_crew_id ?? 0);
                    return (
                      <tr key={rig.id}>
                        <td>{rig.number}</td>
                        <td>{rig.type}</td>
                        <td>{crew ? crewLabel(crew) : "Unassigned"}</td>
                        <td>{rig.active ? "Active" : "Inactive"}</td>
                        <td>
                          <button
                            className="job-link"
                            aria-label={"Edit " + rig.number}
                            disabled={busy}
                            onClick={() => edit(rig)}
                          >
                            Edit
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : !busy && !error ? (
            <p>
              {appliedSearch ? "No rigs match your search." : "No rigs yet."}
            </p>
          ) : null}
        </section>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </main>
  );
}
