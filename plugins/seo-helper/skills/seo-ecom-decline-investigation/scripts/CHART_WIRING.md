# Chart wiring — seo-ecom-decline-investigation

`charts.py` is installed here. `report_helpers.py` builds the XLSX; the HTML is
authored at run time. Chart the period decomposition (from `period_decomposition.py`):

```python
from charts import chart_html
# one (label, value) per driver: label = factor (e.g. "CTR", "coverage", "seasonality"),
# value = its click delta contribution
block = chart_html("Click decline by factor", factor_pairs, "hbars")
# insert `block` next to the decomposition table in the HTML
```
Use hbars — factor labels are long. Map `factor_pairs` to the real fields your
decomposition returns; read them, don't guess.
