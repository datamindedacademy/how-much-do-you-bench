<script>
  /** A metric card.
   *
   * One component so every figure shares a vocabulary: same label treatment,
   * same numeral size, same card. `live` marks a value that is still moving,
   * which is the difference between "1 running" as a fact and as a thing you
   * are waiting on.
   */
  let { label, value, hint = null, live = false } = $props();
</script>

<div class="card" class:live>
  <div class="head">
    <dt class="label">{label}</dt>
    {#if live}
      <span class="pulse" aria-hidden="true"></span>
    {/if}
  </div>
  <dd class="value">{value}</dd>
  {#if hint}
    <p class="hint">{hint}</p>
  {/if}
</div>

<style>
  /* A second surface, not a louder one: the brand's lavender reads as its own
     plane against white (1.23:1) without becoming an accent block. Measured on
     it: ink 15.7:1, muted 6.8:1. */
  .card {
    display: flex;
    flex-direction: column;
    padding: 1rem 1.15rem 1.1rem;
    border-radius: 0.75rem;
    background: var(--color-primary-100);
    border: 1px solid var(--color-primary-200);
  }

  /* surface-800 measured 1.20:1 against the navy page, which is why the
     panels vanished. primary-800 with a primary-500 edge separates and keeps
     the lavender relationship the light theme has. */
  :global(.dark) .card {
    background: var(--color-primary-800);
    border-color: var(--color-primary-500);
  }

  .head {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-height: 1.4rem;
  }

  .label {
    font-size: var(--text-small);
    color: var(--ink-muted);
    line-height: 1.3;
  }

  .value {
    margin: 0.35rem 0 0;
    font-size: var(--text-stat);
    line-height: var(--leading-tight);
    font-variant-numeric: tabular-nums;
    color: var(--ink);
  }

  /* Muted, not subtle: --ink-subtle measures 4.25:1 on lavender, which is
     large-text-only and this is 13px. */
  .hint {
    margin: 0.35rem 0 0;
    font-size: var(--text-caption);
    color: var(--ink-muted);
  }

  /* Work still in flight. The dot pulses rather than the number, so the
     figure stays readable while it changes. */
  .pulse {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background: var(--color-primary-500);
    animation: pulse 1.8s ease-in-out infinite;
  }

  :global(.dark) .pulse {
    background: var(--color-primary-300);
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.35;
      transform: scale(0.75);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .pulse {
      animation: none;
      opacity: 0.85;
    }
  }
</style>
