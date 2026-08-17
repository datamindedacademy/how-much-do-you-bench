# Extend the trajectory analyzer to multi-step runs

`analyze_trajectory.py` already has a working analyzer for *single-attempt*
Harbor runs (the exercise-02 helper). 

Extend the analyzer to handle both shapes without breaking the single-attempt path, and add an `n_attempts`
field to the result:

```python
{
    "outcome": ...,        # "PASS" | "FAIL" | "AGENT_ERROR"
    "n_attempts": ...,     # 1 for single-attempt runs; the attempt count otherwise
    "n_steps": ...,        # agent turns, summed across all attempts
    "n_tool_calls": ...,   # tool calls, summed across all attempts
    "tools": ...,          # {function_name: count}, summed across all attempts
    "skill_invoked": ...,  # True if "skill" was called in any attempt
}
```

For a multi-attempt run the **final** attempt decides the outcome (same rules as
before); steps, tool calls and tools are summed across every attempt. An
`exception.txt` at the task root still means `AGENT_ERROR`, and single-attempt
runs must keep working and report `n_attempts == 1`.
