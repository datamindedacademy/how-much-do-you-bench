<script>
  let { x = 0, y = 0, visible = false, children } = $props();

  let node = $state(null);

  // Flip against the viewport edges so a mark near the right or top of the
  // plot does not push the tooltip off screen.
  const left = $derived(
    node ? Math.min(x + 14, window.innerWidth - node.offsetWidth - 8) : x + 14,
  );
  const top = $derived(node ? Math.max(y - node.offsetHeight - 12, 8) : y - 12);
</script>

<div
  bind:this={node}
  class="tip"
  role="tooltip"
  style:left="{left}px"
  style:top="{top}px"
  style:opacity={visible ? 1 : 0}
>
  {@render children?.()}
</div>

<style>
  .tip {
    position: fixed;
    pointer-events: none;
    background: var(--surface-1);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 12px;
    line-height: 1.45;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.16);
    transition: opacity 0.1s;
    z-index: 10;
  }
</style>
