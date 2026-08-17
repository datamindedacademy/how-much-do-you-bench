/** Theme selection: system by default, overridable, remembered.
 *
 * Skeleton keys off a `.dark` class rather than a media query, so the class is
 * the single source of truth and the stored preference only decides what to
 * put there. */

const KEY = "benchmark-theme";
const media = () => window.matchMedia("(prefers-color-scheme: dark)");

export function stored() {
  try {
    const value = localStorage.getItem(KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    // Private browsing or a blocked origin: fall back to following the OS.
    return "system";
  }
}

export function resolve(preference) {
  if (preference === "system") return media().matches ? "dark" : "light";
  return preference;
}

export function apply(preference) {
  document.documentElement.classList.toggle("dark", resolve(preference) === "dark");
}

export function persist(preference) {
  try {
    if (preference === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, preference);
  } catch {
    // Nothing to do: the class is already applied for this session.
  }
}

/** Keep following the OS while no explicit choice is stored. */
export function watchSystem(onChange) {
  const listener = () => {
    if (stored() === "system") onChange();
  };
  media().addEventListener("change", listener);
  return () => media().removeEventListener("change", listener);
}
