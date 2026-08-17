<script>
  import Tooltip from "./Tooltip.svelte";
  import { niceMax, num, short } from "./lib/scoring.js";

  let {
    submissions = [],
    pending = [],
    frontier = [],
    contenders = [],
    selectedId = null,
    onselect = () => {},
  } = $props();

  // Running submissions share the axes so you can watch one climb as tasks
  // land. They are excluded from the frontier: a partial score cannot dominate
  // a finished one.
  const plotted = $derived([...submissions, ...pending]);

  const W = 860;
  const H = 380;
  // The top margin carries a label, not just whitespace: a submission that
  // passes everything sits exactly on the top gridline, and its team label is
  // drawn 13px above that with a 13px glyph and a 3px halo. At 16 it was cut
  // off by the edge of the chart -- the perfect score being the one nobody
  // could read.
  const M = { top: 30, right: 24, bottom: 48, left: 52 };
  const plotW = W - M.left - M.right;
  const plotH = H - M.top - M.bottom;

  const maxTasks = $derived(Math.max(...plotted.map((s) => s.task_count), 1));
  const maxTokens = $derived(niceMax(Math.max(...plotted.map((s) => s.tokens), 1)));

  // Linear, reversed: cheap on the right, so up-and-right is better on both
  // axes. Linear keeps the distance between two teams proportional to the
  // tokens actually between them, which is what people compare.
  const x = $derived((t) => M.left + plotW - (t / maxTokens) * plotW);
  const y = $derived((p) => M.top + plotH - (p / maxTasks) * plotH);

  const yTicks = $derived.by(() => {
    const step = Math.max(1, Math.round(maxTasks / 5));
    const ticks = [];
    for (let v = 0; v <= maxTasks; v += step) ticks.push(v);
    return ticks;
  });
  const xTicks = $derived([0, 1, 2, 3, 4].map((i) => (maxTokens / 4) * i));

  /** The staircase separating what someone achieved from what nobody did.
   *
   * A step, not a diagonal: between two frontier points the best anyone
   * actually managed is the cheaper one's score, so the boundary holds that
   * score until the cost of the next one is reached. A straight line between
   * them would draw results nobody produced. */
  function staircase(points) {
    const sorted = [...points].sort((a, b) => b.tokens - a.tokens);
    if (!sorted.length) return null;

    const [first] = sorted;
    let line = `M ${M.left} ${y(first.passed)} L ${x(first.tokens)} ${y(first.passed)}`;
    for (let i = 1; i < sorted.length; i++) {
      line += ` L ${x(sorted[i - 1].tokens)} ${y(sorted[i].passed)}`;
      line += ` L ${x(sorted[i].tokens)} ${y(sorted[i].passed)}`;
    }
    return { line, last: sorted[sorted.length - 1] };
  }

  const settled = $derived(submissions.filter((s) => frontier.includes(s.submission_id)));

  const frontierPath = $derived.by(() => {
    const built = staircase(settled);
    if (!built) return null;
    const baseline = M.top + plotH;
    return {
      line: built.line,
      fill: built.line.replace("M", `M ${M.left} ${baseline} L`) +
        ` L ${x(built.last.tokens)} ${baseline} Z`,
    };
  });

  // Where the boundary would sit if the running submissions finished here.
  const provisionalPath = $derived.by(() => {
    if (!contenders.length) return null;
    return staircase([...settled, ...contenders])?.line ?? null;
  });

  // Dominated first, so frontier marks land on top where they overlap.
  const ordered = $derived(
    [...plotted].sort(
      (a, b) =>
        frontier.includes(a.submission_id) - frontier.includes(b.submission_id),
    ),
  );

  let hovered = $state(null);
  let pointer = $state({ x: 0, y: 0 });

  function hover(event, submission) {
    pointer = { x: event.clientX, y: event.clientY };
    hovered = submission;
  }
</script>

<div class="overflow-x-auto">
  <svg
    viewBox="0 0 {W} {H}"
    width={W}
    height={H}
    role="img"
    aria-label="Tasks passed against tokens consumed"
  >
    {#each yTicks as v (v)}
      <line x1={M.left} y1={y(v)} x2={M.left + plotW} y2={y(v)} class="grid" />
      <text x={M.left - 10} y={y(v) + 4} text-anchor="end">{v}</text>
    {/each}

    {#each xTicks as value (value)}
      <text x={x(value)} y={M.top + plotH + 20} text-anchor="middle">
        {short(Math.round(value))}
      </text>
    {/each}

    <line
      x1={M.left}
      y1={M.top + plotH}
      x2={M.left + plotW}
      y2={M.top + plotH}
      class="axis"
    />
    <text x={M.left + plotW / 2} y={H - 8} text-anchor="middle">
      tokens consumed &#183; &#8592; more &#183; cheaper &#8594;
    </text>
    <text transform="translate(14,{M.top + plotH / 2}) rotate(-90)" text-anchor="middle">
      tasks passed
    </text>

    {#if frontierPath}
      <path class="frontier-area" d={frontierPath.fill} />
      <path class="frontier-line" d={frontierPath.line} />
    {/if}
    {#if provisionalPath}
      <path class="provisional-line" d={provisionalPath} />
    {/if}

    {#each ordered as s (s.submission_id)}
      {@const onFrontier = frontier.includes(s.submission_id)}
      <!-- 2px surface ring keeps overlapping marks readable. -->
      {@const live = pending.includes(s)}
      <circle
        class="mark"
        class:frontier={onFrontier}
        class:running={live}
        class:selected={s.submission_id === selectedId}
        style:transform="translate({x(s.tokens)}px, {y(s.passed)}px)"
        r={live ? 6 : onFrontier ? 7 : 5.5}
        role="button"
        tabindex="0"
        aria-label={live
          ? `${s.team}, still running, ${s.completed} of ${s.task_count} tasks done.`
          : `${s.team}, ${s.passed} of ${s.task_count} passed, ${num(s.tokens)} tokens. Show task results.`}
        onclick={() => onselect(s.submission_id)}
        onkeydown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onselect(s.submission_id);
          }
        }}
        onmousemove={(e) => hover(e, s)}
        onmouseleave={() => (hovered = null)}
      />
      {#if onFrontier || contenders.includes(s.submission_id)}
        <!-- Anchor flips near the edges so a label on an extreme point is not
             clipped by the plot boundary. -->
        {@const px = x(s.tokens)}
        {@const anchor =
          px > M.left + plotW - 60 ? "end" : px < M.left + 60 ? "start" : "middle"}
        <text
          class="mark-label"
          x={anchor === "end" ? px + 8 : anchor === "start" ? px - 8 : px}
          y={y(s.passed) - 13}
          text-anchor={anchor}
        >
          {s.team}
        </text>
      {/if}
    {/each}
  </svg>
</div>

<Tooltip x={pointer.x} y={pointer.y} visible={!!hovered}>
  {#if hovered}
    <b>{hovered.team}</b> · {hovered.commit}<br />
    {hovered.passed} of {hovered.task_count} passed<br />
    {num(hovered.tokens)} tokens
  {/if}
</Tooltip>

<style>
  svg {
    display: block;
  }

  text {
    fill: var(--chart-tick);
    font-size: 13px;
  }

  .grid {
    stroke: var(--chart-grid);
    stroke-width: 1;
  }

  .axis {
    stroke: var(--chart-axis);
    stroke-width: 1;
  }

  .mark {
    fill: var(--dominated);
    stroke: var(--chart-surface);
    stroke-width: 2;
    cursor: pointer;
    /* Positioned by transform so a submission visibly travels when its score
       changes, instead of teleporting on each refresh. */
    transition: transform 700ms cubic-bezier(0.22, 1, 0.36, 1);
  }

  .mark.frontier {
    fill: var(--series-1);
  }

  /* The selected mark keeps its identity colour and gains a ring, so
     selection reads as state rather than as a different series. */
  .mark.selected {
    stroke: var(--color-primary-500);
    stroke-width: 3;
  }

  .mark:focus-visible {
    outline: none;
    stroke: var(--color-primary-500);
    stroke-width: 3;
  }

  .frontier-area {
    fill: var(--series-1);
    opacity: 0.07;
  }

  .frontier-line {
    fill: none;
    stroke: var(--series-1);
    stroke-width: 1.5;
    stroke-opacity: 0.45;
    stroke-linejoin: round;
  }

  /* Dashed because it has not happened yet: this is where the boundary moves
     if the running submission stops right now. */
  .provisional-line {
    fill: none;
    stroke: var(--color-primary-500);
    stroke-width: 1.5;
    stroke-dasharray: 5 4;
    stroke-linejoin: round;
  }

  :global(.dark) .provisional-line {
    stroke: var(--color-primary-300);
  }

  /* Still running: hollow and pulsing, so it reads as provisional next to
     finished work. */
  .mark.running {
    fill: var(--chart-surface);
    stroke: var(--color-primary-500);
    stroke-width: 2.5;
    animation: breathe 1.8s ease-in-out infinite;
  }

  :global(.dark) .mark.running {
    stroke: var(--color-primary-300);
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
    .mark {
      transition: none;
    }

    .mark.running {
      animation: none;
    }
  }

  /* Halo keeps a direct label legible where it crosses another mark. */
  .mark-label {
    font-size: 13px;
    font-weight: 500;
    fill: var(--chart-label);
    stroke: var(--chart-surface);
    stroke-width: 3px;
    paint-order: stroke fill;
    stroke-linejoin: round;
  }
</style>
