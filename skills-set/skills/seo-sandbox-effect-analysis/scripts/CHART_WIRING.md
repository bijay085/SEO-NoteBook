# Chart wiring — seo-sandbox-effect-analysis

`charts.py` is installed here. `report_helpers.py` builds the XLSX; the HTML is
authored at run time via `brand_lib.py`. Chart the suppression trajectory there:

```python
from charts import chart_html
# from your monthly series (sandbox_metrics.py output): one (label, value) per month,
# label = the month, value = organic clicks that month
block = chart_html("Monthly clicks — suppression trajectory", monthly_pairs, "bars")
# insert `block` into the "Suppression signature" section of the HTML
```
Map `monthly_pairs` to the actual field names your metrics dict uses — don't
assume keys; read the series you computed.
