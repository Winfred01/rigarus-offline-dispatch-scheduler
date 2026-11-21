export const projectLabels = {
  job_number: "Job #",
  site_id: "Site ID",
  site_name: "Site name",
} as const;

export type ProjectField = keyof typeof projectLabels;

export function projectFieldError(value: string, field: ProjectField) {
  // Match Python str.strip() whitespace, including U+001C..001F and U+0085.
  // FEFF is not stripped by the backend; do not add an identifier restriction.
  const blank =
    /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u;
  if (blank.test(value)) return `Enter ${projectLabels[field]}.`;
  if (value.includes("\0"))
    return `${projectLabels[field]} cannot contain a null character.`;
  return undefined;
}

export function projectFieldErrors(fields: Record<ProjectField, string>) {
  const errors: Partial<Record<ProjectField, string>> = {};
  for (const field of Object.keys(projectLabels) as ProjectField[]) {
    const message = projectFieldError(fields[field], field);
    if (message) errors[field] = message;
  }
  return errors;
}

export function projectServerFieldError(message: string) {
  if (message === "That Job # already belongs to another project.") {
    return { field: "job_number" as ProjectField, message };
  }
  for (const [field, backendLabel] of [
    ["job_number", "Job #"],
    ["site_id", "Site ID"],
    ["site_name", "site name"],
  ] as const) {
    if (message === `Enter a valid ${backendLabel}.`) return { field, message };
  }
  // Disk/service failures are not field errors. Keep their existing recovery hint.
  return undefined;
}
