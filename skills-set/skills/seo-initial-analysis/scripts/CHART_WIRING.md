# Chart wiring — seo-initial-analysis

`charts.py` is installed here. `combine.py` only *concatenates* the section
HTMLs you author (and builds the TOC), so the chart goes **inside a section**,
before combining:

```python
from charts import chart_html
# top keyword clusters from engine-run/master_by_sv.tsv:
# one (label, value) per cluster, label = cluster/bucket, value = aggregate SV
block = chart_html("Top keyword clusters by search volume", cluster_pairs, "bars")
# write `block` into the keyword-engine section body HTML;
# combine.py will include it and add its TOC anchor automatically
```
