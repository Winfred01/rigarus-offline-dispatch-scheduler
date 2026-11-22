import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";

const source = stripTypeScriptTypes(
  readFileSync(new URL("../src/appearance.ts", import.meta.url), "utf8"),
);
const { parseAppearance, defaultAppearance } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);
test("corrupt, obsolete or untrusted device preferences safely use defaults", () => {
  for (const raw of [
    null,
    "{",
    "null",
    "3",
    "[]",
    '{"accent":"url(remote)"}',
    JSON.stringify({ ...defaultAppearance, font: "https://remote/font" }),
    JSON.stringify({ ...defaultAppearance, size: "500" }),
  ])
    assert.deepEqual(parseAppearance(raw), defaultAppearance);
});
test("saved appearance retains only supported values across reload", () => {
  const saved = {
    accent: "Teal",
    font: "Arial",
    size: "16",
    density: "Compact",
  };
  assert.deepEqual(
    parseAppearance(JSON.stringify({ ...saved, unrelated: "ignored" })),
    saved,
  );
});
