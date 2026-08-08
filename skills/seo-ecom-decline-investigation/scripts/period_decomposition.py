#!/usr/bin/env python
"""
period_decomposition.py : the 6-test statistical engine for seo-ecom-decline-investigation.

Implements the six tests documented in references/methodology.md:
  1. Shift-share cohort decomposition (query-level)
  2. Impression-weighted position decomposition (Simpson's-paradox check)
  3. Chi-square + Cramer's V (categorical effect size : country/device/any split)
  4. Quandt-Andrews sup-F changepoint detection (daily series)
  5. WLS regression log(CTR) ~ Position * Period
  6. Counterfactual / elasticity check (clicks ~ impressions)

Usage:
  <venv>/bin/python period_decomposition.py manifest.json

manifest.json shape (all *_csv paths optional : missing inputs skip the tests that need them):
{
  "out_dir": "out/",
  "periods": [
    {"name": "baseline", "start": "2025-03-01", "end": "2025-08-30",
     "date_csv": "p1_date.csv", "query_csv": "p1_query.csv", "page_csv": "p1_page.csv",
     "country_csv": "p1_country.csv", "device_csv": "p1_device.csv"},
    {"name": "current", "start": "2026-01-30", "end": "2026-07-03",
     "date_csv": "p3_date.csv", "query_csv": "p3_query.csv", "page_csv": "p3_page.csv",
     "country_csv": "p3_country.csv", "device_csv": "p3_device.csv"}
  ]
}

Each CSV is a standard GSC export shape: a first "key" column (Date / Top queries / Query /
Top pages / Page / Country / Device) followed by Clicks, Impressions, CTR, Position. Column
names are matched case-insensitively; CTR is always recomputed from Clicks/Impressions rather
than trusted as parsed (avoids string-percent parsing bugs).

No external AI/LLM API is called anywhere in this file : every number is a closed-form or
iterative-fit statistical computation (pandas/numpy/scipy/statsmodels only).
"""
import sys
import os
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf


KEY_CANDIDATES = [
    "date", "top queries", "query", "top pages", "page", "country", "device",
]


def hr(title):
    print("\n" + "=" * 78 + "\n" + title + "\n" + "=" * 78)


def load_export(path):
    """Load a standard GSC-shaped export CSV. Returns None if path is falsy/missing."""
    if not path:
        return None
    if not os.path.exists(path):
        print(f" [data gap] file not found, skipping: {path}")
        return None
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    key_col = None
    for cand in KEY_CANDIDATES:
        if cand in cols:
            key_col = cols[cand]
            break
    if key_col is None:
        key_col = df.columns[0] # fall back to first column, whatever it's named
    df = df.rename(columns={key_col: "key"})
    df["key"] = df["key"].astype(str).str.strip()
    for want in ["Clicks", "Impressions", "Position"]:
        match = next((c for c in df.columns if c.lower() == want.lower()), None)
        if match:
            df[want] = pd.to_numeric(df[match], errors="coerce")
        else:
            df[want] = np.nan
    df = df.dropna(subset=["key"])
    df = df[df["key"].str.lower() != "nan"]
    df["CTR"] = np.where(df["Impressions"] > 0, df["Clicks"] / df["Impressions"], np.nan)
    return df.reset_index(drop=True)


def period_days(period):
    d0 = pd.Timestamp(period["start"])
    d1 = pd.Timestamp(period["end"])
    return max(1, (d1 - d0).days)


# ---------------------------------------------------------------------------
# Test 1 : shift-share cohort decomposition
# ---------------------------------------------------------------------------
def test1_shift_share(qA, qB, days_a, days_b, out_dir, label_a, label_b):
    hr(f"TEST 1 : SHIFT-SHARE COHORT DECOMPOSITION ({label_a} -> {label_b})")
    if qA is None or qB is None:
        print(" [skipped] query-level export missing for one or both periods")
        return None

    qA = qA.copy(); qB = qB.copy()
    qA["k"] = qA["key"].str.lower()
    qB["k"] = qB["key"].str.lower()
    mA = qA.set_index("k"); mB = qB.set_index("k")
    sA, sB = set(mA.index), set(mB.index)
    retained, lost, new = sA & sB, sA - sB, sB - sA

    def per_day(df, keys, col, days):
        return df.loc[df.index.isin(keys), col].sum() / days

    lost_c = per_day(mA, lost, "Clicks", days_a)
    new_c = per_day(mB, new, "Clicks", days_b)
    ret_a_c = per_day(mA, retained, "Clicks", days_a)
    ret_b_c = per_day(mB, retained, "Clicks", days_b)
    total_delta = ret_b_c - ret_a_c + new_c - lost_c

    print(f" cohorts: retained={len(retained)} lost={len(lost)} new={len(new)}")
    print(f" lost cohort clicks/day (gone) : {lost_c:8.2f}")
    print(f" new cohort clicks/day (appeared) : {new_c:8.2f}")
    print(f" retained {label_a} clicks/day : {ret_a_c:8.2f}")
    print(f" retained {label_b} clicks/day : {ret_b_c:8.2f}")
    print(f" retained change : {ret_b_c - ret_a_c:+8.2f}")
    if total_delta != 0:
        print(f"\n share of change from LOST queries : {(-lost_c) / total_delta:6.1%}")
        print(f" share of change from RETAINED survivors: {(ret_b_c - ret_a_c) / total_delta:6.1%}")
        print(f" share of change from NEW queries : {new_c / total_delta:6.1%}")

    if out_dir:
        mA.loc[list(lost)].to_csv(os.path.join(out_dir, f"lost_queries_{label_a}_to_{label_b}.csv"))
        mB.loc[list(new)].to_csv(os.path.join(out_dir, f"new_queries_{label_a}_to_{label_b}.csv"))

    return {
        "retained": len(retained), "lost": len(lost), "new": len(new),
        "lost_clicks_per_day": lost_c, "new_clicks_per_day": new_c,
        "retained_change_per_day": ret_b_c - ret_a_c,
    }


# ---------------------------------------------------------------------------
# Test 2 : impression-weighted position decomposition (Simpson's-paradox check)
# ---------------------------------------------------------------------------
def test2_position_decomposition(qA, qB, label_a, label_b):
    hr(f"TEST 2 : POSITION DECOMPOSITION (real vs compositional) ({label_a} -> {label_b})")
    if qA is None or qB is None:
        print(" [skipped] query-level export missing for one or both periods")
        return None

    qA = qA.copy(); qB = qB.copy()
    qA["k"] = qA["key"].str.lower(); qB["k"] = qB["key"].str.lower()
    mA = qA.set_index("k"); mB = qB.set_index("k")
    retained = set(mA.index) & set(mB.index)

    def wpos(df, keys=None):
        d = df if keys is None else df.loc[df.index.isin(keys)]
        w = d["Impressions"]
        return np.average(d["Position"], weights=w) if w.sum() > 0 else np.nan

    p1_all = wpos(mA); p1_ret = wpos(mA, retained)
    p2_ret = wpos(mB, retained); p2_all = wpos(mB)
    comp = (p1_ret - p1_all) + (p2_all - p2_ret)
    real = p2_ret - p1_ret

    print(f" {label_a} all queries wpos = {p1_all:.2f}")
    print(f" {label_a} retained-only wpos = {p1_ret:.2f}")
    print(f" {label_b} retained-only wpos = {p2_ret:.2f} (REAL survivor movement {real:+.2f})")
    print(f" {label_b} all queries wpos = {p2_all:.2f}")
    print(f"\n total change = {p2_all - p1_all:+.2f}")
    print(f" compositional (mix effect) : {comp:+.2f}")
    print(f" real (survivor movement) : {real:+.2f}")
    if (comp > 0) != (real > 0) and abs(comp) > 0.05 and abs(real) > 0.05:
        print("\n *** SIGNS DISAGREE : the headline number is misleading. Do not report the ***")
        print(" *** all-queries average position as a recovery/decline signal on its own. ***")

    return {"p1_all": p1_all, "p1_retained": p1_ret, "p2_retained": p2_ret, "p2_all": p2_all,
            "compositional_effect": comp, "real_effect": real}


# ---------------------------------------------------------------------------
# Test 3 : chi-square + Cramer's V (categorical effect size)
# ---------------------------------------------------------------------------
def test3_categorical_effect_size(catA, catB, label_a, label_b, dim_name, top_n=15):
    hr(f"TEST 3 : {dim_name.upper()} EFFECT SIZE (chi2 + Cramer's V) ({label_a} -> {label_b})")
    if catA is None or catB is None:
        print(f" [skipped] {dim_name} export missing for one or both periods")
        return None

    top = catA.sort_values("Clicks", ascending=False).head(top_n)["key"].tolist()

    def bucket(df):
        d = df.copy()
        d["b"] = np.where(d["key"].isin(top), d["key"], "OTHER")
        return d.groupby("b")["Clicks"].sum()

    bA, bB = bucket(catA), bucket(catB)
    ct = pd.concat([bA, bB], axis=1).fillna(0)
    ct.columns = [label_a, label_b]
    chi2, p, dof, _ = stats.chi2_contingency(ct.values)
    n = ct.values.sum()
    v = np.sqrt(chi2 / (n * (min(ct.shape) - 1))) if n > 0 else np.nan

    print(f" chi2 = {chi2:,.1f} dof = {dof} p = {p:.3g}")
    print(f" Cramer's V = {v:.4f}", end=" ")
    if v < 0.10:
        print("-> NEGLIGIBLE effect size. Refute the '{}' hypothesis regardless of p-value.".format(dim_name))
    elif v < 0.30:
        print("-> weak/moderate : worth a closer per-category look, not a primary cause.")
    else:
        print("-> meaningful association : investigate further.")

    share = pd.DataFrame({f"{label_a}_share": bA / bA.sum(), f"{label_b}_share": bB / bB.sum()}) \
        .sort_values(f"{label_a}_share", ascending=False)
    print(f"\n Top {dim_name} share of clicks:")
    print((share * 100).round(2).to_string())

    return {"chi2": chi2, "p": p, "cramers_v": v, "dof": dof}


# ---------------------------------------------------------------------------
# Test 4 : Quandt-Andrews sup-F changepoint detection
# ---------------------------------------------------------------------------
def test4_changepoint(all_daily, metric_col="Impressions", trim=0.15):
    hr(f"TEST 4 : CHANGEPOINT DETECTION (Quandt-Andrews sup-F on log {metric_col})")
    if all_daily is None or len(all_daily) < 20:
        print(" [skipped] insufficient daily data (need a merged multi-period daily series)")
        return None

    d = all_daily.sort_values("Date").reset_index(drop=True)
    d["y"] = np.log(d[metric_col].clip(lower=1))
    n = len(d)
    t = np.arange(n)
    trim_n = int(trim * n)
    X0 = sm.add_constant(t)
    rss0 = sm.OLS(d["y"], X0).fit().ssr
    best = (-1, None)
    for k in range(trim_n, n - trim_n):
        dum = (t >= k).astype(float)
        X = np.column_stack([np.ones(n), t, dum, dum * (t - k)])
        res = sm.OLS(d["y"], X).fit()
        F = ((rss0 - res.ssr) / 2) / (res.ssr / (n - 4))
        if F > best[0]:
            best = (F, k)

    if best[1] is None:
        print(" [skipped] no valid breakpoint found within trim window")
        return None

    break_date = d["Date"].iloc[best[1]]
    pre = d[d["Date"] < break_date]
    post = d[d["Date"] >= break_date]
    print(f" strongest structural break: {break_date.date()} sup-F = {best[0]:.1f}")
    if pre[metric_col].mean():
        print(f" mean {metric_col}/day before: {pre[metric_col].mean():.1f} after: {post[metric_col].mean():.1f}"
              f" ({post[metric_col].mean() / pre[metric_col].mean() - 1:+.1%})")
    if "Clicks" in d.columns:
        print(f" mean Clicks/day before: {pre['Clicks'].mean():.1f} after: {post['Clicks'].mean():.1f}")
    if "Position" in d.columns:
        print(f" mean Position before: {pre['Position'].mean():.1f} after: {post['Position'].mean():.1f}")

    print("\n daily values +/-5 rows around the break (confirm cliff vs ramp):")
    lo, hi = max(0, best[1] - 5), min(n, best[1] + 6)
    cols = [c for c in ["Date", "Clicks", "Impressions", "Position"] if c in d.columns]
    print(d.iloc[lo:hi][cols].to_string(index=False))

    sup_f = best[0]
    if sup_f > 100:
        confidence = "overwhelming : very likely a genuine single-event break"
    elif sup_f > 30:
        confidence = "strong : likely real, corroborate against known events (Phase 4)"
    else:
        confidence = "modest : may be gradual decay rather than a single event; inspect the daily table above"
    print(f"\n confidence read: {confidence}")

    return {
        "break_date": str(break_date.date()), "sup_f": float(sup_f),
        "pre_mean": float(pre[metric_col].mean()), "post_mean": float(post[metric_col].mean()),
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Test 5 : WLS regression log(CTR) ~ Position * Period
# ---------------------------------------------------------------------------
def test5_ctr_at_rank(qA, qB, label_a, label_b):
    hr(f"TEST 5 : CTR-AT-RANK REGRESSION ({label_a} vs {label_b})")
    if qA is None or qB is None:
        print(" [skipped] query-level export missing for one or both periods")
        return None

    a = qA.assign(period=0); b = qB.assign(period=1)
    allq = pd.concat([a, b])
    allq = allq[(allq["CTR"] > 0) & (allq["Position"] > 0) & (allq["Impressions"] >= 5)].copy()
    if len(allq) < 30:
        print(" [skipped] too few qualifying rows (need Impressions>=5, CTR>0, Position>0)")
        return None
    allq["logctr"] = np.log(allq["CTR"])

    mod = smf.wls("logctr ~ Position + period + Position:period", data=allq,
                   weights=allq["Impressions"]).fit(cov_type="HC1")
    print(f" Position coef = {mod.params['Position']:.4f} (p={mod.pvalues['Position']:.3g})")
    print(f" period coef = {mod.params['period']:+.4f} (p={mod.pvalues['period']:.3g})"
          " <- headline: is CTR-at-rank different between periods?")
    print(f" Position:period = {mod.params['Position:period']:+.4f} (p={mod.pvalues['Position:period']:.3g})")
    p_period = mod.pvalues["period"]
    if p_period > 0.1:
        print(f"\n p={p_period:.2g} > 0.1 -> CTR-at-a-given-rank is statistically UNCHANGED.")
        print(" Recovering rank is the relevant lever; snippet/CTR-copy changes are not.")
    else:
        mult = np.exp(mod.params["period"])
        print(f"\n p={p_period:.2g} <= 0.1 -> CTR-at-rank genuinely shifted (x{mult:.3f}).")
        print(" Worth investigating rich-result eligibility / title-meta relevance / SERP features.")

    return {"position_coef": float(mod.params["Position"]), "period_coef": float(mod.params["period"]),
            "period_p": float(p_period)}


# ---------------------------------------------------------------------------
# Test 6 : counterfactual / elasticity (clicks ~ impressions)
# ---------------------------------------------------------------------------
def test6_counterfactual(dailyA, dailyB, label_a, label_b):
    hr("TEST 6 : COUNTERFACTUAL (is the click change fully explained by impressions?)")
    if dailyA is None or dailyB is None:
        print(" [skipped] daily export missing for one or both periods")
        return None

    a = dailyA.dropna(subset=["Clicks", "Impressions"])
    b = dailyB.dropna(subset=["Clicks", "Impressions"])
    if len(a) < 10 or len(b) < 10:
        print(" [skipped] insufficient daily rows")
        return None

    X1 = sm.add_constant(a["Impressions"])
    m = sm.OLS(a["Clicks"], X1).fit()
    pred_b = m.predict(sm.add_constant(b["Impressions"]))
    print(f" {label_a} daily model: Clicks = {m.params['const']:.1f} + {m.params['Impressions']:.4f}*Impr"
          f" R2={m.rsquared:.3f}")
    print(f" {label_b} actual clicks/day mean = {b['Clicks'].mean():.1f}")
    print(f" {label_b} predicted (via {label_a}'s CTR relationship & {label_b}'s impressions) = {pred_b.mean():.1f}")
    deficit = b["Clicks"].mean() / pred_b.mean() - 1 if pred_b.mean() else np.nan
    print(f" => deviation from counterfactual = {deficit:+.1%}")

    ll = np.log(a[["Clicks", "Impressions"]].replace(0, np.nan).dropna())
    if len(ll) > 5:
        me = sm.OLS(ll["Clicks"], sm.add_constant(ll["Impressions"])).fit()
        print(f" {label_a} click-impression elasticity (log-log) = {me.params['Impressions']:.3f}")

    return {"predicted_clicks_per_day": float(pred_b.mean()),
            "actual_clicks_per_day": float(b["Clicks"].mean()),
            "deviation_pct": float(deficit)}


def load_daily(period):
    df = load_export(period.get("date_csv"))
    if df is None:
        return None
    df = df.rename(columns={"key": "Date"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df.dropna(subset=["Date"])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    manifest = json.load(open(sys.argv[1]))
    periods = manifest["periods"]
    out_dir = manifest.get("out_dir", "out")
    os.makedirs(out_dir, exist_ok=True)

    if len(periods) < 2:
        print("Need at least 2 periods to decompose anything. Exiting.")
        sys.exit(1)

    hr("HEADLINE : per-day metrics by period")
    daily_frames = []
    headline = {}
    for p in periods:
        days = period_days(p)
        d = load_daily(p)
        if d is not None:
            daily_frames.append(d)
            clicks_pd = d["Clicks"].sum() / days
            impr_pd = d["Impressions"].sum() / days
            ctr = d["Clicks"].sum() / d["Impressions"].sum() if d["Impressions"].sum() else float("nan")
            print(f" {p['name']:15s} ({p['start']} -> {p['end']}, {days}d): "
                  f"clicks/day={clicks_pd:8.1f} impr/day={impr_pd:9.1f} CTR={ctr:.3%}")
            headline[p["name"]] = {"clicks_per_day": clicks_pd, "impr_per_day": impr_pd, "ctr": ctr, "days": days}
        else:
            print(f" {p['name']:15s}: [data gap] no date_csv provided")

    # Pairwise tests: baseline (periods[0]) vs every subsequent period
    base = periods[0]
    base_q = load_export(base.get("query_csv"))
    base_c = load_export(base.get("country_csv"))
    base_dv = load_export(base.get("device_csv"))
    base_daily = load_daily(base)

    results = {"headline": headline, "pairwise": {}}
    for p in periods[1:]:
        q = load_export(p.get("query_csv"))
        c = load_export(p.get("country_csv"))
        dv = load_export(p.get("device_csv"))
        d = load_daily(p)
        days_a, days_b = period_days(base), period_days(p)

        r = {}
        r["shift_share"] = test1_shift_share(base_q, q, days_a, days_b, out_dir, base["name"], p["name"])
        r["position_decomposition"] = test2_position_decomposition(base_q, q, base["name"], p["name"])
        r["country_effect"] = test3_categorical_effect_size(base_c, c, base["name"], p["name"], "country")
        r["device_effect"] = test3_categorical_effect_size(base_dv, dv, base["name"], p["name"], "device")
        r["ctr_at_rank"] = test5_ctr_at_rank(base_q, q, base["name"], p["name"])
        r["counterfactual"] = test6_counterfactual(base_daily, d, base["name"], p["name"])
        results["pairwise"][p["name"]] = r

    # Changepoint test needs the FULL merged daily series across all periods
    if daily_frames:
        merged = pd.concat(daily_frames).drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
        results["changepoint"] = test4_changepoint(merged, "Impressions")
    else:
        results["changepoint"] = None

    out_json = os.path.join(out_dir, "headline.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[saved {out_json} and per-period query CSVs in {out_dir}/]")


if __name__ == "__main__":
    main()
