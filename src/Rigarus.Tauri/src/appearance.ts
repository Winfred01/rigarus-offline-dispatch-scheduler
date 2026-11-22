export type Appearance = {
  accent: "Blue" | "Teal";
  font: "Segoe UI" | "Arial";
  size: "14" | "16";
  density: "Comfortable" | "Compact";
};
export const defaultAppearance: Appearance = {
  accent: "Blue",
  font: "Segoe UI",
  size: "14",
  density: "Comfortable",
};
export const appearanceKey = "rigarus.appearance.v1";
export function parseAppearance(raw: string | null): Appearance {
  try {
    const value = JSON.parse(raw ?? "null");
    if (
      !value ||
      !["Blue", "Teal"].includes(value.accent) ||
      !["Segoe UI", "Arial"].includes(value.font) ||
      !["14", "16"].includes(value.size) ||
      !["Comfortable", "Compact"].includes(value.density)
    )
      return { ...defaultAppearance };
    return {
      accent: value.accent,
      font: value.font,
      size: value.size,
      density: value.density,
    };
  } catch {
    return { ...defaultAppearance };
  }
}
export function applyAppearance(value: Appearance) {
  const root = document.documentElement;
  root.dataset.accent = value.accent;
  root.dataset.density = value.density;
  root.style.setProperty("--app-font", value.font);
  root.style.setProperty("--app-size", `${value.size}px`);
}
