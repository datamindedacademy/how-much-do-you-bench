# Normalize the survey into a SQLite database

`/app/quant151.csv` is the raw Qualtrics survey export. It's one very
wide table; I want it split into a small SQLite database so we can build a
dashboard / let people query it. Every response row has a unique `UID` — use it
as the `respondent_id` key in every table so they join.

In `/app/normalize.py`, implement:

```python
def build_database(csv_path, db_path) -> None
```

It reads `csv_path` and writes a single SQLite file at `db_path` with four tables:

1. `qualifications`: one row per respondent: plus the
   firmographic/role columns, question groups Q1–Q15.
2. `technology` — one row per respondent: Add the technology
   / tooling / vendor questions, groups Q16–Q19 and Q24–Q29.
3. `challenges_priorities` — a priority matrix: one row per respondent,
   one column per challenge. Add columns for each
   of the 23 challenges, named by the challenge text. Each cell is that respondent's priority
   allocation for the challenge — the integer from the matching `Q20b` column
   (`0` if blank).

Drop the bookkeeping columns (`StartDate`, `EndDate`, `PID`,
`Respondent_Status`).
The grader imports `build_database` from `/app/normalize.py` and calls it with the
CSV path and a database path of its choosing, so do not hard-code either.

Constraints:

- Do not edit `/app/quant151.csv`.
- Keep the function name and signature: `build_database(csv_path, db_path)`.
