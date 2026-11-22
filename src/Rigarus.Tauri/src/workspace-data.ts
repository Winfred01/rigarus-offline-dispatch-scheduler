import { invoke } from "@tauri-apps/api/core";
import type { DraftAssignment } from "./assignment-fields";

export type Crew = { id: number; name: string; type: string; active: boolean };
export type Person = {
  id: number;
  name: string;
  home_crew_id: number;
  active: boolean;
  foreman_eligible: boolean;
  driver_status: string;
};
export type Rig = {
  id: number;
  number: string;
  type: string;
  default_crew_id: number | null;
  active: boolean;
  notes: string;
};
export type WorkItem = {
  id: number;
  type: string;
  required_crew_count: number;
  estimated_half_days: number;
};
export type Project = {
  id: number;
  job_number: string;
  site_id: string;
  site_name: string;
  work_items: WorkItem[];
};
export type Foreman = {
  crew_id: number;
  employee_id: number | null;
  employee_name: string | null;
  employee_active: boolean | null;
  employee_eligible: boolean | null;
};
export type Workspace = {
  crews: Crew[];
  people: Person[];
  rigs: Rig[];
  projects: Project[];
  assignments: DraftAssignment[];
  foremen: Foreman[];
};

// Bound IPC fan-out when a backlog contains hundreds of Projects.
async function mapReads<T, R>(
  values: T[],
  read: (value: T) => Promise<R>,
): Promise<R[]> {
  const result: R[] = new Array(values.length);
  let index = 0;
  await Promise.all(
    Array.from({ length: Math.min(6, values.length) }, async () => {
      while (index < values.length) {
        const current = index++;
        result[current] = await read(values[current]);
      }
    }),
  );
  return result;
}

export async function readWorkspace(): Promise<Workspace> {
  const [crews, people, rigs, summaries, assignments] = await Promise.all([
    invoke<Crew[]>("search_crews", { term: "" }),
    invoke<Person[]>("search_employees", { term: "" }),
    invoke<Rig[]>("search_rigs", { term: "" }),
    invoke<{ id: number }[]>("search_projects", { term: "" }),
    invoke<DraftAssignment[]>("list_assignments", { query: {} }),
  ]);
  const [projects, foremen] = await Promise.all([
    mapReads(summaries, ({ id }) => invoke<Project>("read_project", { id })),
    mapReads(crews, ({ id }) =>
      invoke<Foreman>("read_foreman", { crewId: id }),
    ),
  ]);
  return { crews, people, rigs, projects, assignments, foremen };
}
