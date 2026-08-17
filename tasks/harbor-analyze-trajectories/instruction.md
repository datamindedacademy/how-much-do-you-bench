# Analyze a Harbor agent trajectory

For a single exercise in a Harbor run, I want to see what the agent actually did:
did it solve the task, how many steps did it take, which tools did it use, and
did it ever call the `skill` tool.

In `analyze_trajectory.py`, implement `analyze_trajectory(task_dir)` returning:

```python
{
    "outcome": ...,        # "PASS" | "FAIL" | "AGENT_ERROR"
    "n_steps": ...,        # agent turns (exclude "user" steps)
    "n_tool_calls": ...,   # total tool calls across the agent turns
    "tools": ...,          # {function_name: count}
    "skill_invoked": ...,  # True if the "skill" tool was called
}
```

Outcome rules: `PASS` if `reward.txt` starts with `1`; `AGENT_ERROR` if there's
an `exception.txt` or no `reward.txt` to read; otherwise `FAIL`. If
`trajectory.json` is missing or unreadable, treat it as zero steps / tool calls
rather than crashing.
