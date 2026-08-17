# Data initiatives completed — bucketed bar chart

`quant151.csv` is a survey export. Question (Q2) is how many data initiatives each organization completed in
the last 12 months.

In `initiatives.py`, implement:

```python
def initiative_buckets(csv_path) -> dict
```

returning the number of organizations in each of three buckets (ignore None), keyed exactly:

```python
{"1-5": ..., "6-10": ..., "10+": ...}
```

Then `plot_buckets(buckets, output_path)`, save a bar chart (one bar per bucket,
in the order above) to `output_path` as a PNG.
