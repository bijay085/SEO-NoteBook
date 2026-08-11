#!/usr/bin/env python3
"""sandbox_metrics.py : the quantitative core of the Sandbox-Effect analysis.

Turns Google Search Console exports into the "is this site graduating?" signal set:
the brand vs non-brand split, the impressions-up / clicks-flat suppression signature,
non-brand position bands, zero-click interception candidates, and a 0-100 Graduation
Score. Emits sandbox_data.json for the report + workbook, and prints a readable table.

PURE STDLIB : no pandas/scipy needed (so it runs without a venv). For the heavier
before/after stats that a CORE-UPDATE DEMOTION needs (changepoint, Simpson's-paradox
position decomposition), this script only *flags* the mode : defer the decomposition to
the sibling skill `seo-ecom-decline-investigation` rather than re-implementing it here.

INPUTS (all CSV; column names are matched case-insensitively and tolerate GSC UI export
headers like "Top queries"/"Clicks"/"Impressions"/"CTR"/"Position" and the lowercase
MCP forms). Feed whatever GSC gives you:

    --daily date,clicks,impressions[,ctr,position] (date dimension : the trend)
    --queries query,clicks,impressions,ctr,position (query dimension : brand split)
    --pages page,clicks,impressions,ctr,position (optional : top pages)
    --config config.json (default ./config.json; for brand_regex, period, domain)
    --out sandbox_data.json (default <output_dir>/data/sandbox_data.json)

Usage:
    python3 sandbox_metrics.py --daily daily.csv --queries queries.csv --config config.json

GSC gotcha baked in: date-dimension totals are accurate; query-dimension totals UNDERCOUNT
(GSC anonymises rare queries), so the headline trend uses --daily and the brand split uses
--queries, and the two are reported separately, never summed together.
"""
import argparse, csv, json, os, re, sys
from collections import defaultdict

# ---------- tolerant CSV reading ----------
def _norm(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())

_ALIASES = {
    'date': {'date','day'},
    'query': {'query','queries','topqueries','searchquery','keyword'},
    'page': {'page','pages','toppages','url','landingpage'},
    'clicks': {'clicks','click','urlclicks'},
    'impressions': {'impressions','impr','impressionscount'},
    'ctr': {'ctr','clickthroughrate'},
    'position': {'position','avgposition','averageposition','pos'},
}
def _colmap(header):
    m = {}
    for i, h in enumerate(header):
        n = _norm(h)
        for canon, al in _ALIASES.items():
            if n in al: m[canon] = i
    return m

def _num(x):
    if x is None: return 0.0
    x = str(x).strip().replace('%','').replace(',','')
    if x in ('', '-', 'n/a', 'na'): return 0.0
    try: return float(x)
    except ValueError: return 0.0

def read_csv(path):
    """Return (list-of-dicts with canonical keys, colmap)."""
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    if not rows: return [], {}
    # skip GSC UI preamble rows until a row that looks like a header
    hi = 0
    for i, r in enumerate(rows[:5]):
        if _colmap(r): hi = i; break
    cm = _colmap(rows[hi])
    out = []
    for r in rows[hi+1:]:
        if not any(c.strip() for c in r): continue
        d = {}
        for k, idx in cm.items():
            if idx < len(r): d[k] = r[idx]
        out.append(d)
    return out, cm

# ---------- month aggregation + partial flag ----------
_DAYS = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}
def _mdays(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    d = _DAYS[m]
    if m == 2 and (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)): d = 29
    return d

def monthly_from_daily(daily):
    mon = defaultdict(lambda: {'clicks':0.0,'impr':0.0,'days':0,'possum':0.0,'poswt':0.0})
    for d in daily:
        dt = (d.get('date') or '').strip()[:10]
        if len(dt) < 7: continue
        ym = dt[:7]; v = mon[ym]
        c, i = _num(d.get('clicks')), _num(d.get('impressions'))
        v['clicks'] += c; v['impr'] += i; v['days'] += 1
        if 'position' in d and _num(d.get('position')) > 0:
            v['possum'] += _num(d['position']) * max(i,1); v['poswt'] += max(i,1)
    rows = []
    for ym in sorted(mon):
        v = mon[ym]; ctr = 100*v['clicks']/v['impr'] if v['impr'] else 0.0
        pos = v['possum']/v['poswt'] if v['poswt'] else None
        rows.append({'month':ym,'days':v['days'],'expected_days':_mdays(ym),
                     'partial': v['days'] < _mdays(ym),
                     'clicks':int(v['clicks']),'impr':int(v['impr']),
                     'ctr':round(ctr,2),'position':round(pos,1) if pos else None})
    return rows

# ---------- brand / non-brand split ----------
def brand_split(queries, brand_rx):
    rx = re.compile(brand_rx, re.I) if brand_rx else None
    b = {'clicks':0.0,'impr':0.0,'poswt':0.0,'possum':0.0,'n':0}
    nb = {'clicks':0.0,'impr':0.0,'poswt':0.0,'possum':0.0,'n':0}
    nb_click_qs, zero_click = [], []
    for q in queries:
        term = (q.get('query') or '').strip()
        c, i = _num(q.get('clicks')), _num(q.get('impressions'))
        pos = _num(q.get('position')); ctr = _num(q.get('ctr'))
        bucket = b if (rx and term and rx.search(term)) else nb
        bucket['clicks'] += c; bucket['impr'] += i; bucket['n'] += 1
        if pos > 0: bucket['possum'] += pos*max(i,1); bucket['poswt'] += max(i,1)
        if bucket is nb:
            if c > 0: nb_click_qs.append((term, int(c), int(i), round(pos,1)))
            # zero-click interception candidate: ranks well, big impressions, ~0 CTR
            ctr_pct = ctr if ctr <= 1 else ctr # ctr may be fraction or percent; normalise below
            if pos and pos <= 10 and i >= 500:
                cpct = (c/i*100) if i else 0
                if cpct < 1.0: zero_click.append((term, int(i), round(cpct,3), round(pos,1)))
    def fin(x):
        x['ctr'] = round(100*x['clicks']/x['impr'],3) if x['impr'] else 0.0
        x['position'] = round(x['possum']/x['poswt'],1) if x['poswt'] else None
        x['clicks'] = int(x['clicks']); x['impr'] = int(x['impr'])
        for k in ('poswt','possum'): x.pop(k, None)
        return x
    b, nb = fin(b), fin(nb)
    tot_clicks = b['clicks'] + nb['clicks']
    brand_share = round(100*b['clicks']/tot_clicks,1) if tot_clicks else None
    nb_click_qs.sort(key=lambda t: -t[1]); zero_click.sort(key=lambda t: -t[1])
    return b, nb, brand_share, nb_click_qs[:25], zero_click[:25]

# ---------- non-brand position bands ----------
def position_bands(queries, brand_rx):
    rx = re.compile(brand_rx, re.I) if brand_rx else None
    bands = {'1-3':0.0,'4-10':0.0,'11-20':0.0,'21+':0.0}; tot = 0.0
    ctr_4_10 = []
    for q in queries:
        term = (q.get('query') or '').strip()
        if rx and term and rx.search(term): continue
        i = _num(q.get('impressions')); pos = _num(q.get('position'))
        if not pos: continue
        tot += i
        if pos <= 3: bands['1-3'] += i
        elif pos <= 10:
            bands['4-10'] += i
            c = _num(q.get('clicks')); ctr_4_10.append((c/i*100) if i else 0)
        elif pos <= 20: bands['11-20'] += i
        else: bands['21+'] += i
    share = {k: (round(100*v/tot,1) if tot else 0.0) for k,v in bands.items()}
    med_ctr = None
    if ctr_4_10:
        s = sorted(ctr_4_10); n = len(s)
        med_ctr = round((s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2), 2)
    return share, med_ctr

# ---------- graduation score ----------
def graduation_score(brand_share, nb_pos, bands, med_ctr_4_10):
    def clamp(x): return max(0.0, min(1.0, x))
    a = clamp((100 - (brand_share if brand_share is not None else 100)) / 50.0) # non-brand click share vs 50%
    b = clamp((30 - (nb_pos if nb_pos else 30)) / (30 - 8)) # non-brand avg position 8..30
    c = clamp((bands.get('1-3',0)+bands.get('4-10',0)) / 40.0) # page-1 non-brand impr share vs 40%
    d = clamp((med_ctr_4_10 if med_ctr_4_10 else 0) / 3.0) # CTR-at-rank health vs 3%
    score = round(100*(0.30*a + 0.30*b + 0.25*c + 0.15*d), 1)
    if score >= 70: stage = "Graduated / graduating : non-brand demand is being captured"
    elif score >= 45: stage = "Emerging : partial graduation; specific pillars still holding it back"
    elif score >= 25: stage = "Suppressed : indexed but not trusted; classic sandbox/brand-only pattern"
    else: stage = "Deep suppression : near brand-only; entity/E-E-A-T/link trust unresolved"
    return score, stage, {'nonbrand_share':round(a,2),'nonbrand_position':round(b,2),
                          'page1_share':round(c,2),'ctr_at_rank':round(d,2)}

# ---------- suppression-mode flags ----------
def mode_flags(months, brand_share, nb_pos, bands, med_ctr, has_baseline):
    flags = []
    real = [m for m in months if not m['partial']]
    if len(real) >= 4:
        n = len(real); k = max(1, n//3)
        early = real[:k]; late = real[-k:]
        ei = sum(m['impr'] for m in early)/len(early); li = sum(m['impr'] for m in late)/len(late)
        ec = sum(m['clicks'] for m in early)/len(early); lc = sum(m['clicks'] for m in late)/len(late)
        impr_chg = (li-ei)/ei*100 if ei else 0; click_chg = (lc-ec)/ec*100 if ec else 0
        if impr_chg > 20 and click_chg < 10 and (nb_pos or 99) > 12:
            flags.append(("SANDBOX / TRUST-HOLD",
              f"impressions {impr_chg:+.0f}% but clicks {click_chg:+.0f}% across the window; non-brand avg pos {nb_pos}. "
              "Visibility is accumulating without converting to rank/clicks : the never-graduated pattern."))
        if impr_chg < -25 and has_baseline:
            flags.append(("POSSIBLE CORE-UPDATE DEMOTION",
              f"impressions {impr_chg:+.0f}% with a baseline present : this may be a demotion, not a sandbox. "
              "Run the sibling skill `seo-ecom-decline-investigation` for the changepoint + position decomposition."))
    if bands.get('1-3',0)+bands.get('4-10',0) >= 25 and (med_ctr is not None and med_ctr < 1.0):
        flags.append(("ZERO-CLICK INTERCEPTION",
          f"{bands.get('1-3',0)+bands.get('4-10',0):.0f}% of non-brand impressions rank page-1 but median CTR@4-10 is {med_ctr}% "
          ": AI Overviews / PAA are answering on the SERP. Fix = SERP-feature capture + intent pivot, NOT 'rank higher'."))
    if brand_share is not None and brand_share >= 75:
        flags.append(("BRAND-ONLY JAIL",
          f"{brand_share}% of clicks are brand : the site earns clicks only when people already know the name. "
          "Non-brand discovery is the gap."))
    return flags

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--daily'); ap.add_argument('--queries'); ap.add_argument('--pages')
    ap.add_argument('--config', default='config.json'); ap.add_argument('--out')
    a = ap.parse_args()
    cfg = {}
    if os.path.exists(a.config):
        cfg = json.load(open(a.config, encoding='utf-8'))
    brand_rx = (cfg.get('gsc',{}) or {}).get('brand_regex') or ''
    out = a.out or os.path.join(cfg.get('output_dir','.'), 'data', 'sandbox_data.json')

    data = {'domain': (cfg.get('client',{}) or {}).get('domain'),
            'brand_regex': brand_rx, 'monthly': [], 'brand': None, 'nonbrand': None}

    months = []
    if a.daily and os.path.exists(a.daily):
        daily,_ = read_csv(a.daily); months = monthly_from_daily(daily); data['monthly'] = months
        print(f"{'Month':8}{'Days':>5}{'Clicks':>8}{'Impr':>9}{'CTR%':>7}{'Pos':>6} Partial")
        for m in months:
            print(f"{m['month']:8}{m['days']:>5}{m['clicks']:>8}{m['impr']:>9}{m['ctr']:>7}"
                  f"{(m['position'] if m['position'] else '-'):>6} {'YES (excluded from trend)' if m['partial'] else ''}")

    brand_share=nb_pos=med_ctr=None; bands={}
    if a.queries and os.path.exists(a.queries):
        queries,_ = read_csv(a.queries)
        b, nb, brand_share, nb_click_qs, zero_click = brand_split(queries, brand_rx)
        bands, med_ctr = position_bands(queries, brand_rx)
        nb_pos = nb['position']
        data.update({'brand':b,'nonbrand':nb,'brand_click_share':brand_share,
                     'nonbrand_click_queries':nb_click_qs,'zero_click_candidates':zero_click,
                     'nonbrand_position_bands':bands,'median_ctr_pos_4_10':med_ctr,
                     'query_dim_note':'Query-dimension totals UNDERCOUNT (GSC anonymises rare queries). '
                                      'Use --daily date totals for the headline trend.'})
        print(f"\nBrand vs non-brand (query dim): brand clicks={b['clicks']} nonbrand clicks={nb['clicks']} "
              f"brand_share={brand_share}% nonbrand_pos={nb_pos}")
        print(f"Non-brand impression bands: {bands} median CTR@4-10={med_ctr}%")
        if zero_click: print(f"Zero-click candidates (rank<=10, impr>=500, CTR<1%): {len(zero_click)}")

    if a.pages and os.path.exists(a.pages):
        pages,_ = read_csv(a.pages)
        tp = sorted(({'page':(p.get('page') or ''),'clicks':int(_num(p.get('clicks'))),
                      'impr':int(_num(p.get('impressions'))),'ctr':round(_num(p.get('ctr')),2),
                      'position':round(_num(p.get('position')),1)} for p in pages),
                    key=lambda x: -int(x['clicks']))[:30]
        data['top_pages'] = tp

    has_baseline = bool((cfg.get('period',{}) or {}).get('baseline_start'))
    if months or bands:
        score, stage, comps = graduation_score(brand_share, nb_pos, bands, med_ctr)
        flags = mode_flags(months, brand_share, nb_pos, bands, med_ctr, has_baseline)
        data.update({'graduation_score':score,'graduation_stage':stage,'score_components':comps,
                     'mode_flags':[{'mode':m,'evidence':e} for m,e in flags]})
        print(f"\n=== GRADUATION SCORE: {score}/100 : {stage} ===")
        print(f" components (0-1): {comps}")
        for m,e in flags: print(f" [{m}] {e}")

    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    json.dump(data, open(out,'w',encoding='utf-8'), indent=2)
    print(f"\nWROTE {out}")

if __name__ == '__main__':
    main()
