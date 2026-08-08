# Chart wiring — seo-cro-conversion-audit

`charts.py` (shared `svg_bars` / `chart_html`) is installed in this folder.

`cro_report.py` builds the **XLSX only**; the client-facing narrative HTML is
authored at run time by built-in report branding. Put the chart in that HTML:

```python
from charts import chart_html
# scores are already computed in cro_signals.json (+ cro_verdict.json overrides)
site   = next(h for h, d in sig["domains"].items() if d.get("is_site"))
scores = _final(site, sig["domains"][site]["scores"], verdict)   # helper in cro_report.py
block  = chart_html("Conversion score by dimension",
                    [(dim, scores.get(dim)) for dim in sig["dimensions"]], "bars")
# insert `block` into the Overview/summary of the narrative HTML
```
Want a graph inside the workbook too? add a native `openpyxl.chart.BarChart`
on the "Conversion Scores" sheet.
