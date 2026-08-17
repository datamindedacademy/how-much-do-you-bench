# Top challenges across organizations

`quant151.csv` is a survey export.
The challenges question is a **multi-select** spread across the columns
`Q20a_1`, `Q20a_2`, … `Q20a_23` ("Please select the challenges that are relevant
to your organization"). Each of those columns belongs to one challenge 
and a respondent selected it when the cell is non-empty.

In `challenges.py`, implement:

```python
def top_challenges(csv_path, n=5) -> list   # [(challenge_name, count), ...]
```

Count, per challenge, how many organizations selected it, and return the top `n`
as `(name, count)` pairs sorted by count descending, ties broken by challenge
name A to Z.

Then `plot_challenges(challenges, output_path)` — save a bar chart of those
challenges and their counts to `output_path` png.
