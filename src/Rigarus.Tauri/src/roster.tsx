import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState, type SubmitEvent } from "react";

type CrewDraft = {
  name: string;
  type: "Civil" | "Tower";
  active: boolean;
};
type Crew = CrewDraft & { id: number };

const emptyCrew: CrewDraft = { name: "", type: "Civil", active: true };

export function CrewRoster() {
  const [crews, setCrews] = useState<Crew[]>([]);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [editor, setEditor] = useState<{
    id: number | null;
    draft: CrewDraft;
  }>();
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  async function load(term: string) {
    setCrews(await invoke<Crew[]>("search_crews", { term }));
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

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || busy) return;
    setBusy(true);
    setError("");
    setStatus("");
    try {
      await invoke<Crew>("save_crew", { id: editor.id, crew: editor.draft });
      setEditor(undefined);
      setStatus("Crew saved.");
      await load(appliedSearch);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }

  function edit(id: number | null, draft: CrewDraft) {
    setError("");
    setStatus("");
    setEditor({ id, draft });
  }

  function update(changes: Partial<CrewDraft>) {
    if (editor)
      setEditor({ ...editor, draft: { ...editor.draft, ...changes } });
  }

  return (
    <main className="frame project-master">
      <div className="page-heading">
        <h1>Crews</h1>
        <button
          onClick={() => edit(null, emptyCrew)}
          disabled={busy || !!editor}
        >
          New crew
        </button>
      </div>
      {editor ? (
        <section aria-labelledby="crew-editor-title">
          <h2 id="crew-editor-title">
            {editor.id === null ? "New crew" : "Edit crew"}
          </h2>
          <form className="project-editor" onSubmit={submit}>
            <fieldset disabled={busy}>
              <div className="project-fields">
                <label>
                  Crew name
                  <input
                    id="crew-name"
                    value={editor.draft.name}
                    onChange={(event) => update({ name: event.target.value })}
                    maxLength={100}
                    required
                  />
                </label>
                <label>
                  Crew type
                  <select
                    id="crew-type"
                    value={editor.draft.type}
                    onChange={(event) =>
                      update({
                        type:
                          event.target.value === "Tower" ? "Tower" : "Civil",
                      })
                    }
                  >
                    <option>Civil</option>
                    <option>Tower</option>
                  </select>
                </label>
                <label>
                  Status
                  <select
                    id="crew-active"
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
              <div className="actions">
                <button>Save crew</button>
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
        <section aria-labelledby="crew-list-title">
          <h2 id="crew-list-title">Crew roster</h2>
          <form
            className="project-search"
            onSubmit={(event) => {
              event.preventDefault();
              if (!busy) void refresh(search);
            }}
          >
            <label htmlFor="crew-search">Crew name</label>
            <div className="search-controls">
              <input
                id="crew-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <button disabled={busy}>Search</button>
            </div>
          </form>
          <p className="project-status" role="status">
            {busy ? "Loading crews…" : status}
          </p>
          {crews.length ? (
            <div className="project-table">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Crew name</th>
                    <th scope="col">Type</th>
                    <th scope="col">Status</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {crews.map(({ id, name, type, active }) => (
                    <tr key={id}>
                      <td>{name}</td>
                      <td>{type}</td>
                      <td>{active ? "Active" : "Inactive"}</td>
                      <td>
                        <button
                          className="job-link"
                          aria-label={"Edit " + name}
                          onClick={() => edit(id, { name, type, active })}
                          disabled={busy}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : !busy && !error ? (
            <p>
              {appliedSearch ? "No crews match your search." : "No crews yet."}
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
