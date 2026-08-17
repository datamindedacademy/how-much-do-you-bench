# Analyze Harbor run results

I'm post-processing the output of our **Harbor** eval runs and need help to summarise the results.
Included tests with an error as failed tests.

Implement `analyze_run(job_dir)` (a path to the job directory). Return a dict shaped like:

```python
{
    "exercises": [
        {
            "name": ...,           # "python__<exercise>", random suffix removed
            "reward": ...,         # the value in reward.txt
            "passed": ..., "failed": ...,
            "passed_tests": [...], "failed_tests": [...],   # node ids
        },
        ...                        # one per exercise, sorted by "name"
    ],
    "total_passed": ..., "total_failed": ...,
    "n_exercises": ...,
    "reward_sum": ...,             # summed reward.txt values
}
```
Look at the sub-directories in the job folder for test results. A missing or empty `test-stdout.txt` just means nothing passed or failed there.

