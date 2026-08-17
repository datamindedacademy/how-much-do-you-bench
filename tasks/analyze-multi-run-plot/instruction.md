# Compare multiple Harbor runs and plot them

I've run the same benchmark under a few increasingly capable agent configurations
(opencode alone, a tuned system prompt, system prompt **and** skills) and want to
compare them on a chart. Next to whether an exercise passed or failed, the number
of final hidden tests passed and total are valuable metrics for an agent's progress.

`analyze_runs(runs_dir)` parses every run and returns one dict per run, **sorted
by run name**:

```python
{
    "run": ...,            # run directory name
    "n_exercises": ...,
    "solved": ...,         # exercises with reward == 1
    "success_rate": ...,   # solved / n_exercises  (0..1)
    "tests_passed": ...,   # hidden tests passed for the run
    "tests_total": ...,    # hidden tests total for the run
}
```

`plot_runs(summaries, output_path)` takes that list and saves a PNG to
`output_path` showing, per run, **both** the overall success rate and the number
of passed hidden tests. Lay it out however you like (grouped bars, twin axis, …)
as long as both series render, one bar/point per run. Use a headless matplotlib
backend (e.g. `matplotlib.use("Agg")`).

Only count exercise sub-dirs whose name starts with `python__`.
