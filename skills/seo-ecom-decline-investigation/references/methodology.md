# Methodology : what each test proves and how to read it

Referenced from `SKILL.md` Phase 3. This is the interpretation layer : `scripts/period_decomposition.py`
computes the numbers; this document says what they mean and where the thresholds come from.

---

## 1. Shift-share cohort decomposition

**Question:** of the change in clicks/impressions between two periods, how much is from queries that
disappeared (lost cohort), queries that are new, or queries present in both periods but performing
differently (retained cohort)?

**Method:** for each query present in period A's top-N export, and each query present in period B's,
compute set membership: `retained = A ∩ B`, `lost = A - B`, `new = B - A`. Per-day normalize each
cohort's clicks/impressions (divide by period length). The total change decomposes as:

```
Δ(clicks/day) = (new cohort clicks/day) to (lost cohort clicks/day) + (retained cohort change)
```

**How to read it:** compute each term's share of the total change. In the source investigation, only
5.2% of the click loss came from queries that vanished from the top-1000 : 66.4% came from retained
queries simply declining. That is the opposite of "we lost keywords" : the keywords were still there,
ranking worse. Report the share breakdown explicitly; don't just say "some queries were lost."

**Caveat : censoring.** GSC UI exports commonly cap at 1,000 rows. If a query wasn't in either period's
top-1000, it's invisible to this test : say so. The live API can page further if the tail matters; note
in the report whether the tail was actually pulled or just inferred from aggregate deltas.

---

## 2. Impression-weighted position decomposition (the Simpson's-paradox check)

**Question:** when a site-wide average position metric moves, is the movement real (pages individually
ranking better/worse) or compositional (the mix of pages being averaged changed)?

**Method:** compute the impression-weighted average position four ways:
1. `P1_all` : period A, all queries
2. `P1_retained` : period A, only queries that also appear in period B (drop the "lost" cohort)
3. `P2_retained` : period B, the same retained-query set
4. `P2_all` : period B, all queries

Decompose the total change `P2_all to P1_all` into:
- **Compositional effect** = `(P1_retained to P1_all) + (P2_all to P2_retained)` : the part caused purely
  by which queries left/entered the average
- **Real effect** = `P2_retained to P1_retained` : the actual movement of the same queries

**How to read it:** if the compositional effect and the real effect have *opposite signs*, the headline
number is actively misleading : this is exactly what happened in the source investigation (headline
improved 23→9; real survivor movement was +1.03, i.e. worse). When this happens, **stop reporting
average position as a health metric for this site** and say so explicitly in the deliverable : recommend
impressions and indexed-page count instead.

---

## 3. Chi-square + Cramér's V (categorical effect size)

**Question:** is a decline concentrated in one segment (a country, a device type, a page category), or
distributed proportionally across all of them?

**Method:** build a contingency table (period × category, e.g. period × top-15-countries-plus-Other),
run `scipy.stats.chi2_contingency`. Chi-square alone is not enough : with GSC-scale data (often
millions of impressions) almost any real-world difference produces `p < 0.001` regardless of whether it
matters. Always compute Cramér's V alongside it:

```
V = sqrt(chi2 / (N × (min(rows, cols) to 1)))
```

**Threshold guide** (standard for a 2-sided categorical association, doesn't change by field):
- `V < 0.10` → negligible association. Report the hypothesis as **refuted** even if p is tiny.
- `0.10 ≤ V < 0.30` → weak/moderate : worth a closer look at which specific categories moved, but not
  a primary cause.
- `V ≥ 0.30` → the category genuinely matters; investigate further.

In the source investigation, country showed `V = 0.070` : the "we lost a country's SERP" hypothesis
was refuted by this number alone, despite a chi-square p-value of `3.3e-269`. Always report both
numbers together; a p-value without an effect size is not a finding.

**Also check share-of-total, not just the test.** A category whose *share* of the metric held stable or
rose (e.g. a market's share of total clicks going up) while its *absolute* numbers fell is additional,
intuitive evidence the decline wasn't targeted at that category.

---

## 4. Quandt-Andrews sup-F changepoint detection

**Question:** is there a single date where the daily metric structurally broke, or is the decline
gradual/noisy with no clear single event?

**Method:** fit `log(metric) ~ trend` (OLS) on the full daily series as the null (no break). Then, for
every candidate breakpoint `k` within a trimmed range (drop the first/last ~15% of points : breaks near
the edges are unreliable to detect), fit a model with a level shift and a slope shift at `k`:

```
y ~ const + t + I(t≥k) + I(t≥k)·(t to k)
```

Compute the F-statistic comparing the restricted (no-break) and unrestricted (break-at-k) residual sum
of squares for every candidate `k`. The **sup-F** is the maximum F-statistic across all candidates; the
`k` that achieves it is the most likely single breakpoint.

**How to read the magnitude:** there's no universal p-value table bundled here (the Quandt-Andrews test
statistic's distribution is non-standard and needs simulation/bootstrap for a formal p-value) : instead,
use it comparatively and combined with the visual/economic size of the break:
- A sup-F in the hundreds (as in the source investigation: 140.7) on a clean single-day level shift is
  overwhelming evidence of a real, singular break : especially when it coincides with a **one-day**
  jump in the raw series (e.g. position 25.4 → 11.4 literally the next day). A metric cannot move that
  fast through gradual ranking improvement; only a change in *what's being counted* explains a one-day
  jump of that size.
- A modest sup-F (tens) spread across the series with no sharp single-day jump in the raw data usually
  means "gradual decay," not a single event : report it that way, and don't force a single "this is the
  day" narrative onto a trend that's actually a slope change.

Always eyeball the raw daily values immediately around the detected `k` (a table of ±5 days) before
reporting it : the changepoint math can be right about the date and still be describing a multi-day
ramp rather than a true single-day cliff; say which one it actually is.

---

## 5. WLS regression: log(CTR) ~ Position × Period

**Question:** at a *given* rank, is a page earning the same click-through rate it used to : or has the
rank-to-click relationship itself degraded (a snippet, trust, or SERP-feature problem independent of
ranking)?

**Method:** pool query-level rows across periods (keep rows with `impressions ≥ 5` to avoid noise from
single-digit-impression queries), add a `period` dummy, fit weighted least squares (weight = impressions)
on `log(CTR) ~ Position + period + Position:period`, with HC1 robust standard errors.

**How to read it:**
- `Position` coefficient: the baseline CTR decay by rank (should be negative : CTR falls as rank
  worsens; this confirms the model is sane).
- `period` coefficient, **p-value is the headline number**: if insignificant (e.g. p > 0.1), CTR-at-a-
  given-rank is unchanged between periods : meaning **the lost volume is from lost impressions/ranks,
  not from users clicking less at the same rank.** This directly tells you whether "improve the
  snippet / rich results" is a relevant lever (it is not, if this test is insignificant) versus
  "recover the actual ranking / indexation" (it is, regardless).
- If the `period` coefficient *is* significant and negative, CTR-at-rank has genuinely degraded : worth
  investigating rich-result eligibility, title/meta relevance, or a SERP-feature (AI Overview, PAA)
  eating the click before the listing.

---

## 6. Counterfactual / elasticity check (clicks ~ impressions)

**Question:** how much of the click change is mechanically explained by the impression change alone?

**Method:** fit `Clicks ~ Impressions` (OLS) on period A's daily data. Predict what period B's clicks
*would have been* using period B's actual impressions and period A's fitted relationship. Compare to
period B's actual clicks.

**How to read it:** if actual ≈ predicted, the click story is fully explained by impressions : there's
no separate "clicks got worse independent of impressions" phenomenon to chase. If actual is *higher*
than predicted, something (better CTR execution, brand strength) is partially offsetting the impression
loss : worth naming as a genuine strength in the report, not just a footnote. Also report the log-log
elasticity (`d(log Clicks)/d(log Impressions)` from period A) as a sanity figure : apparel/ecommerce
SERPs typically show elasticity near or slightly above 1.0; a much lower or negative figure is itself
worth flagging as unusual.

---

## Tooling notes

All six tests are implemented with `pandas`, `numpy`, `scipy.stats`, and `statsmodels` : see
`scripts/period_decomposition.py`. None require an external AI/LLM call; they are closed-form or
iterative-fit statistical procedures. Claude's job is to run the script, read its printed output, and
write the interpretation using the rules above : not to eyeball a chart and guess.
