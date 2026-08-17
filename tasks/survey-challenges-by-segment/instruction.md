# Top challenges, broken down by segment

Input data is survey: `quant151.csv`.
I want the top challenges *within* a segment of the respondents first by
organization size, then by industry.

The challenges are the multi-select columns `Q20a_1` … `Q20a_23`.

Segments:

- **`"size"`** — bucket **Q1** (annual revenue) into `"<10M"`, `"10-100M"`,
  `">100M"`:
- **`"industry"`** — group by **Q4** ("What industry is your organization
  primarily in?") using the raw industry value.

In `challenges_by_segment.py`, implement:

```python
def top_challenges_by_segment(csv_path, segment, k=3) -> dict
```

Return `{group: [(challenge_name, count), ...]}` — for each group, that group's
top `k` challenges as `(name, count)` pairs, **sorted by count descending, ties
broken by challenge name A to Z**. `segment` is `"size"` or `"industry"`.
