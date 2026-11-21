import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";

const source = readFileSync(
  new URL("../src/project-validation.ts", import.meta.url),
  "utf8",
);
const { projectFieldError, projectFieldErrors, projectServerFieldError } =
  await import(
    `data:text/javascript;base64,${Buffer.from(stripTypeScriptTypes(source)).toString("base64")}`
  );

test("all current required text fields are identified without mutating drafts", () => {
  const draft = Object.freeze({
    job_number: " ",
    site_id: "\t",
    site_name: "\n",
  });
  assert.deepEqual(projectFieldErrors(draft), {
    job_number: "Enter Job #.",
    site_id: "Enter Site ID.",
    site_name: "Enter Site name.",
  });
  assert.equal(draft.site_id, "\t");
  assert.deepEqual(projectFieldErrors({ ...draft, site_id: "0001" }), {
    job_number: "Enter Job #.",
    site_name: "Enter Site name.",
  });
});

test("blank and null handling matches backend without a new character policy", () => {
  for (const field of ["job_number", "site_id", "site_name"]) {
    for (const value of ["", "\u001c", "\u0085", "\u3000", " \t\n"])
      assert.ok(projectFieldError(value, field));
    assert.match(projectFieldError("A\0B", field), /null character/);
    // FEFF is not Python whitespace; format and non-ASCII decisions stay open.
    for (const value of ["\ufeff", "项目 Ω/?", "0001", "S-104", "1"])
      assert.equal(projectFieldError(value, field), undefined);
  }
});

test("canonical duplicate and field responses target only their actual input", () => {
  assert.deepEqual(
    projectServerFieldError("That Job # already belongs to another project."),
    {
      field: "job_number",
      message: "That Job # already belongs to another project.",
    },
  );
  assert.equal(
    projectServerFieldError("Enter a valid Site ID.").field,
    "site_id",
  );
  assert.equal(
    projectServerFieldError("Enter a valid site name.").field,
    "site_name",
  );
});

test("disk, service, ownership and unknown failures are not mislabeled as bad fields", () => {
  for (const message of [
    "Could not save the project. Check disk access, then try again.",
    "The local service is unavailable.",
    "A work item is repeated or does not belong to this project.",
    "",
    "Duplicate",
    "Unexpected failure",
  ]) {
    assert.equal(projectServerFieldError(message), undefined);
  }
});
