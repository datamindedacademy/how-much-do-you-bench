<script>
  import Board from "./Board.svelte";
  import Scatter from "./Scatter.svelte";
  import Stat from "./Stat.svelte";
  import ThemeToggle from "./ThemeToggle.svelte";
  import { clockTime, duration, efficiencyFloor, isFinal, num } from "./lib/scoring.js";

  let submissions = $state([]);
  let frontier = $state([]);
  // Running submissions nobody has beaten yet. Computed server-side so the
  // dominance rule lives in one place rather than one per language.
  let contenders = $state([]);
  let error = $state(null);
  // Empty until /results says otherwise, so no trace links render when the
  // viewer is not deployed.
  let viewerUrl = $state("");
  let loaded = $state(false);

  // Sorting lives here so the chart caption can describe what the table is
  // ranked on without the two drifting apart.
  let sortKey = $state("passed");
  let sortDir = $state("desc");

  // Shared by the chart and the table: selecting a point opens its row.
  let openId = $state(null);
  const select = (id) => (openId = openId === id ? null : id);

  const finished = $derived(submissions.filter(isFinal));
  // Still in flight: shown but never ranked, since a partial score and a
  // partial token count would misplace them.
  const pending = $derived(submissions.filter((s) => !isFinal(s)));
  const teams = $derived(new Set(submissions.map((s) => s.team)).size);
  const best = $derived(finished.length ? Math.max(...finished.map((s) => s.passed)) : 0);
  const taskCount = $derived(finished[0]?.task_count ?? 0);

  const stats = $derived([
    { label: "Teams", value: teams },
    { label: "Submissions", value: submissions.length },
    { label: "Best score", value: finished.length ? `${best}/${taskCount}` : "—" },
    {
      label: "Running",
      value: pending.length,
      hint: pending.length ? "scores appear when they finish" : "all caught up",
      live: pending.length > 0,
    },
  ]);

  const floor = $derived(efficiencyFloor(finished));

  const columns = [
    {
      key: "team",
      label: "Team",
      get: (r) => r.team,
      sort: (r) => r.team.toLowerCase(),
      defaultDir: "asc",
    },
    { key: "commit", label: "Commit", get: (r) => r.commit },
    {
      key: "passed",
      label: "Passed",
      get: (r) => `${r.passed}/${r.task_count}`,
      sort: (r) => r.passed,
      num: true,
      defaultDir: "desc",
    },
    {
      key: "tokens",
      label: "Tokens",
      get: (r) => num(r.tokens),
      sort: (r) => r.tokens,
      num: true,
      defaultDir: "asc",
    },
    {
      key: "duration",
      label: "Duration",
      get: (r) => duration(r.duration_s),
      sort: (r) => r.duration_s ?? 0,
      num: true,
      defaultDir: "asc",
      title: "Agent time summed across the submission's tasks",
    },
    {
      key: "created_at",
      label: "Submitted",
      get: (r) => clockTime(r.created_at),
      // Sorted on the raw timestamp: the rendered value is local time to the
      // minute, so sorting it as a string would tie every submission in a
      // minute and break across midnight.
      sort: (r) => r.created_at ?? "",
      defaultDir: "desc",
    },
  ];

  async function refresh() {
    try {
      const response = await fetch("/results");
      if (!response.ok) throw new Error(`/results returned ${response.status}`);
      const data = await response.json();
      submissions = data.submissions;
      frontier = data.pareto;
      contenders = data.contenders ?? [];
      viewerUrl = data.viewer_url ?? "";
      error = null;
    } catch (e) {
      error = e.message;
    } finally {
      loaded = true;
    }
  }

  $effect(() => {
    refresh();
    const timer = setInterval(refresh, 10000);
    return () => clearInterval(timer);
  });
</script>

<main class="mx-auto max-w-5xl px-6 pt-10 pb-20">
  <header class="header">
    <div>
      <h1 class="display">
        <span class="emoji" aria-hidden="true">🏋️</span>
        How much do you bench?
      </h1>
      <p class="lede">
        A data engineering benchmark. Same model for everyone, so the only thing
        that separates you is the context you give it.
      </p>
    </div>
    <ThemeToggle />
  </header>

  {#if error}
    <aside class="card preset-tonal-warning mb-6 p-4 text-sm" role="alert">
      Could not load results: {error}
    </aside>
  {/if}

  <dl class="stats">
    {#each stats as stat (stat.label)}
      <Stat label={stat.label} value={stat.value} hint={stat.hint} live={stat.live} />
    {/each}
  </dl>

  <section class="mb-12">
    <h2 class="section">Accuracy against cost</h2>
    <p class="prose">
      Up and to the right is better. Click a point for its task breakdown.
    </p>
    <Scatter
      submissions={finished}
      {pending}
      {frontier}
      {contenders}
      selectedId={openId}
      onselect={select}
    />
    <div class="legend">
      <span class="inline-flex items-center gap-2">
        <i class="dot frontier"></i> On the frontier
      </span>
      <span class="inline-flex items-center gap-2">
        <i class="dot"></i> Beaten on both
      </span>
      {#if pending.length}
        <span class="inline-flex items-center gap-2">
          <i class="dot running"></i> Still running
        </span>
      {/if}
    </div>
    {#if loaded && !finished.length}
      <!-- Below the chart, not instead of it: the empty axes tell you what is
           being measured, which a sentence on its own does not. -->
      <p class="empty">
        Nothing plotted yet. The first completed submission draws the frontier.
      </p>
    {/if}
  </section>

  <section>
    <h2 class="section">Leaderboard</h2>
    <p class="prose">
      Sort by <strong class="font-medium">Passed</strong> or
      <strong class="font-medium">Tokens</strong>. The efficiency prize needs at least
      half the leader's score.
    </p>
    <Board
      rows={finished}
      {columns}
      {frontier}
      bind:sortKey
      bind:sortDir
      {floor}
      bind:openId
      {pending}
      {viewerUrl}
    />
  </section>
</main>

<style>
  /* El Messiri is the brand's title face, held to the page title. Product UI
     wants one family in labels, headers and data; a display face there reads
     as costume. */
  .header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 2rem;
    margin-bottom: 2.5rem;
  }

  .display {
    font-family: var(--heading-font-family);
    font-size: var(--text-title);
    font-weight: 700;
    line-height: var(--leading-tight);
    letter-spacing: -0.015em;
    text-wrap: balance;
    color: var(--ink);
  }

  /* Sized to the cap height rather than the em box, so it sits on the
     baseline instead of riding above the text. */
  .emoji {
    font-size: 0.85em;
    margin-right: 0.15em;
  }

  .lede {
    margin-top: 0.5rem;
    max-width: 60ch;
    font-size: var(--text-body);
    color: var(--ink-muted);
    text-wrap: pretty;
  }

  .section {
    font-family: var(--base-font-family);
    font-size: var(--text-subhead);
    font-weight: 600;
    line-height: var(--leading-tight);
    margin-bottom: 0.35rem;
    color: var(--ink);
  }

  /* Measure, not container width: the page is 64rem wide for the table, which
     would run prose well past 100 characters a line. */
  .prose {
    max-width: 68ch;
    margin-bottom: 1.25rem;
    font-size: var(--text-small);
    color: var(--ink-muted);
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
    gap: 0.75rem;
    margin: 0 0 3rem;
  }

  .legend {
    display: flex;
    gap: 1.5rem;
    margin-top: 1rem;
    font-size: var(--text-small);
    color: var(--ink-muted);
  }

  .empty {
    padding: 3rem 0;
    text-align: center;
    font-size: var(--text-small);
    color: var(--ink-muted);
  }

  .dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    display: inline-block;
    background: var(--dominated);
  }

  .dot.frontier {
    background: var(--series-1);
  }

  .dot.running {
    background: transparent;
    border: 2px solid var(--color-primary-500);
    animation: breathe 1.8s ease-in-out infinite;
  }

  :global(.dark) .dot.running {
    border-color: var(--color-primary-300);
  }

  @keyframes breathe {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.4;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .dot.running {
      animation: none;
    }
  }
</style>
