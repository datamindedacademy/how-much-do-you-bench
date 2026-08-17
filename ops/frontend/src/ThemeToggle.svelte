<script>
  import { apply, persist, resolve, stored, watchSystem } from "./lib/theme.js";

  let preference = $state(stored());
  const active = $derived(resolve(preference));

  function toggle() {
    // Two states, not three: a "system" item in a two-button control is a
    // setting, not a toggle. System remains the default until first use.
    preference = active === "dark" ? "light" : "dark";
    apply(preference);
    persist(preference);
  }

  $effect(() => watchSystem(() => apply(preference)));
</script>

<button
  type="button"
  class="toggle"
  onclick={toggle}
  aria-pressed={active === "dark"}
  title={active === "dark" ? "Switch to light mode" : "Switch to dark mode"}
>
  <span aria-hidden="true">{active === "dark" ? "☾" : "☀"}</span>
  <span class="sr-only">
    {active === "dark" ? "Switch to light mode" : "Switch to dark mode"}
  </span>
</button>

<style>
  .toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.5rem;
    font-size: 1.1rem;
    line-height: 1;
    color: var(--ink-muted);
    border: 1px solid var(--color-surface-300);
    background: transparent;
    cursor: pointer;
    transition:
      color 150ms ease-out,
      background-color 150ms ease-out;
  }

  :global(.dark) .toggle {
    border-color: var(--color-surface-700);
  }

  .toggle:hover {
    color: var(--ink);
    background-color: var(--color-surface-100);
  }

  :global(.dark) .toggle:hover {
    background-color: var(--color-surface-800);
  }

  .toggle:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }

  @media (prefers-reduced-motion: reduce) {
    .toggle {
      transition: none;
    }
  }
</style>
