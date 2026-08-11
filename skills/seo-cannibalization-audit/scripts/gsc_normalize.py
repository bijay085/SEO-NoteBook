"""Normalise raw GSC pulls into the tidy frames the rest of the pipeline reads.

Input : whatever the Search Console MCP wrote to disk (raw API JSON, flattened
         JSON, or CSV). Shapes are sniffed, not assumed.
Output : <work>/matrix.csv page, query, clicks, impressions, position [, date]
         <work>/pages.csv per-URL rollup + trend
         <work>/universe.json brand-normalised query universe + IDF
         <work>/appearance.json per-page SERP surface mix (when supplied)
         <work>/meta.json what was analysed, capped, excluded

Usage:
    python gsc_normalize.py --work <dir> --site sc-domain:example.com \
        --matrix data/matrix.json [--appearance data/appearance.json] \
        [--page-totals data/page_totals.json] [--config config.json]

Nothing here judges anything. It measures, normalises and rolls up.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import cast
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit

import numpy as np
import pandas as pd

from cannib_config import load_cfg

# ---------------------------------------------------------------------------
# Tolerant input loading
# ---------------------------------------------------------------------------

ALIASES = {
    'page': ['page', 'url', 'landing_page', 'top_pages', 'page_url', 'address'],
    'query': ['query', 'keyword', 'search_query', 'top_queries', 'search_term'],
    'clicks': ['clicks', 'total_clicks', 'url_clicks'],
    'impressions': ['impressions', 'total_impressions', 'impr', 'impression'],
    'position': ['position', 'avg_position', 'average_position', 'avg_pos', 'pos'],
    'date': ['date', 'day', 'week'],
    'ctr': ['ctr', 'click_through_rate'],
    'searchappearance': ['searchappearance', 'search_appearance', 'appearance'],
}


def _as_frame(obj) -> pd.DataFrame:
    return obj if isinstance(obj, pd.DataFrame) else pd.DataFrame(obj)


def _as_series(obj) -> pd.Series:
    return obj if isinstance(obj, pd.Series) else pd.Series(obj)


def _numeric_filled(obj, fill=0) -> pd.Series:
    s = _as_series(obj)
    raw = np.asarray(pd.to_numeric(s, errors='coerce'), dtype=float)
    raw = np.where(np.isnan(raw), float(fill), raw)
    return pd.Series(raw, index=s.index)


def _as_timestamp(val) -> pd.Timestamp:
    fallback = cast(pd.Timestamp, pd.Timestamp(datetime.now().date()))
    if isinstance(val, pd.Series):
        val = val.iloc[0] if not val.empty else None
    if val is None:
        return fallback
    try:
        if pd.isna(val):
            return fallback
    except (ValueError, TypeError):
        pass
    ts = pd.Timestamp(str(val))
    if not isinstance(ts, pd.Timestamp) or pd.isna(ts):
        return fallback
    return cast(pd.Timestamp, ts)


def _canon(col):
    key = re.sub(r'[^a-z0-9]+', '_', str(col).strip().lower()).strip('_')
    for canonical, names in ALIASES.items():
        if key in names:
            return canonical
    return key


def _parse_pipe_table(text):
    """Parse the pipe-delimited table the Search Console MCP actually returns
    when a result is too large to inline:

        Search Analytics Results (25000 rows)

        page | query | Clicks | Impressions | CTR | Position
        ----------------------------------------------------
        https://example.com/a/ | blue widgets | 12 | 340 | 3.53% | 6.2

    Returns None when the text is not that shape.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header_i = next((i for i, ln in enumerate(lines)
                     if '|' in ln and not set(ln.strip()) <= set('-| ')), None)
    if header_i is None:
        return None
    cols = [_canon(c) for c in lines[header_i].split('|')]
    if 'page' not in cols and 'query' not in cols:
        return None
    records = []
    for ln in lines[header_i + 1:]:
        if set(ln.strip()) <= set('-| '): # the ---- separator
            continue
        parts = [p.strip() for p in ln.split('|')]
        if len(parts) != len(cols):
            continue # a value containing '|' : skip, don't guess
        records.append(dict(zip(cols, parts)))
    if not records:
        return None
    df = pd.DataFrame(records)
    if 'ctr' in df.columns:
        df['ctr'] = df['ctr'].astype(str).str.rstrip('%')
    return df


def load_rows(path):
    """Read one GSC dump into a DataFrame. Handles raw API JSON
    ({"rows":[{"keys":[...], "clicks":..}]}), a bare list of raw rows,
    flattened records, CSV/TSV, or the MCP's pipe-delimited text table. Raw
    `keys` arrays are expanded using `dimensions` when echoed back, otherwise
    inferred from content."""
    p = Path(path)
    if p.suffix.lower() in ('.csv', '.tsv'):
        df = pd.read_csv(p, sep='\t' if p.suffix.lower() == '.tsv' else ',')
        df.columns = [_canon(c) for c in df.columns]
        return df

    text = p.read_text(encoding='utf-8', errors='replace')
    if text.lstrip()[:1] not in ('{', '['):
        table = _parse_pipe_table(text)
        if table is not None:
            return table
        raise SystemExit(f'{path}: not JSON, CSV, or a recognised MCP pipe table')

    payload = json.loads(text)
    dims = None
    if isinstance(payload, dict):
        dims = payload.get('dimensions')
        for key in ('rows', 'data', 'results', 'records'):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise SystemExit(f'{path}: cannot find a row list in this JSON')
    if not payload:
        return pd.DataFrame()

    if isinstance(payload[0], dict) and 'keys' in payload[0]:
        keys = [r.get('keys') or [] for r in payload]
        width = max(len(k) for k in keys)
        if not dims or len(dims) != width:
            dims = _infer_dimensions(keys, width)
        expanded = pd.DataFrame(
            [list(k) + [None] * (width - len(k)) for k in keys],
            columns=[_canon(d) for d in dims])
        metrics = pd.DataFrame([{k: r.get(k) for k in ('clicks', 'impressions', 'ctr', 'position')}
                                for r in payload])
        return pd.concat([expanded, metrics], axis=1)

    df = pd.DataFrame(payload)
    df.columns = [_canon(c) for c in df.columns]
    return df


_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _infer_dimensions(keys, width):
    """Name each key slot from its content : the MCP does not always echo back
    the `dimensions` it was called with."""
    names = []
    for i in range(width):
        sample = [k[i] for k in keys[:200] if len(k) > i and k[i]]
        head = sample[:20]
        if head and all(_DATE_RE.match(str(s)) for s in head):
            names.append('date')
        elif head and sum(str(s).startswith('http') for s in head) > len(head) * 0.5:
            names.append('page')
        else:
            names.append('query')
    return names


def _require(df, cols, label):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f'{label}: missing required column(s) {missing}. '
                         f'Got: {sorted(df.columns)}')


# ---------------------------------------------------------------------------
# URL + brand helpers (shared by shortlist / verdict / plan)
# ---------------------------------------------------------------------------

_BRAND_SUFFIX_WORDS = (
    'education', 'academy', 'institute', 'university', 'college', 'school',
    'classes', 'coaching', 'tutoring', 'learning', 'training', 'online',
    'official', 'digital', 'media', 'group', 'agency', 'studio', 'studios',
    'labs', 'solutions', 'services', 'consulting', 'marketing', 'design',
    'works', 'tech', 'software', 'apps', 'hub', 'shop', 'store', 'global',
    'world', 'hq',
)


def site_domain(site_url):
    if not site_url:
        return ''
    if site_url.startswith('sc-domain:'):
        return site_url.split(':', 1)[1]
    return urlparse(site_url).netloc or site_url


def detect_brand_tokens(site_url, configured=None):
    """Brand tokens used to brand-normalise the query universe. Explicit config
    wins. Otherwise derive from the domain: the full core ("acmeeducation"), the
    short prefix ("acme") and the spaced form ("acme education") : a brand gets
    searched all three ways."""
    if configured:
        return [t.strip().lower() for t in configured if t and t.strip()]
    host = site_domain(site_url).lower()
    if not host:
        return []
    core = re.sub(r'^www\.', '', host).split('.')[0]
    if len(core) < 3:
        return []
    tokens = [core]
    for suffix in _BRAND_SUFFIX_WORDS:
        if core.endswith(suffix):
            prefix = core[:-len(suffix)]
            if len(prefix) >= 3:
                if prefix not in tokens:
                    tokens.append(prefix)
                spaced = f'{prefix} {suffix}'
                if spaced not in tokens:
                    tokens.append(spaced)
            break
    return tokens


def normalize_brand_query(q, brand_tokens):
    """Strip brand tokens, leaving the topic remainder. A brand+topic query is
    not noise : it is a topic query with a brand modifier, and two of the site's
    own pages competing for it is real branded cannibalization. Only a query
    that is *nothing but* brand normalises to '' and gets dropped."""
    if not q:
        return ''
    ql = str(q).lower().strip()
    if not brand_tokens:
        return re.sub(r'\s+', ' ', ql).strip()
    for b in sorted((t for t in brand_tokens if t), key=len, reverse=True):
        ql = re.sub(r'\b' + re.escape(b) + r'\b', ' ', ql)
    return re.sub(r'\s+', ' ', ql).strip()


def norm_url(u):
    return (u or '').rstrip('/')


# Tracking parameters carry no page identity : GSC reports the tagged URL as a
# separate row, and without this the homepage "cannibalizes itself".
_TRACKING_PARAMS = ('utm_', 'gclid', 'fbclid', 'msclkid', 'gclsrc', 'dclid',
                    'mc_cid', 'mc_eid', '_ga', 'yclid', 'igshid', 'ref_src')


def canonical_url(u):
    """Strip the fragment and known tracking parameters. Other query params are
    KEPT : on many sites `?p=123` or a filter param is a genuinely distinct
    page, and silently merging those would fabricate duplicates."""
    if not u:
        return u
    parts = urlsplit(str(u))
    if not parts.query:
        return urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not any(k.lower().startswith(t) for t in _TRACKING_PARAMS)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       urlencode(kept, doseq=True), ''))


_NUM_TOKEN = re.compile(r'^(?:\d+|20\d{2})$')


def slug_parts(url):
    """Split a URL's last path segment into (content_tokens, number_tokens).
    Numbers are kept SEPARATE, not discarded : a number in a slug is often
    semantic (`-3` vs `-4` = Part 3 vs Part 4, distinct pages)."""
    path = urlparse(url).path.strip('/').lower()
    if not path:
        return [], []
    seg = path.split('/')[-1]
    content, nums = [], []
    for t in re.split(r'[-_]+', seg):
        if not t:
            continue
        if _NUM_TOKEN.match(t):
            nums.append(t)
        else:
            content.append(t[:-1] if len(t) > 3 and t.endswith('s') else t)
    return content, nums


def url_twin(url_a, url_b):
    """True when two URLs share the same slug *content* tokens : they LOOK like
    the same page modulo a numeric suffix. Only a HINT: whether that number is
    semantic is decided downstream by the query-demand guard, which sees the
    actual search demand."""
    if norm_url(url_a) == norm_url(url_b):
        return False
    a_tok, _ = slug_parts(url_a)
    b_tok, _ = slug_parts(url_b)
    if not a_tok or not b_tok:
        return False
    return sorted(a_tok) == sorted(b_tok)


def unique_click_share(page, other, page_query_clicks, page_ranks_for):
    """Fraction of `page`'s clicks earned on queries `other` does NOT rank for.
    High means `page` owns its own demand : a DISTINCT page, not a merge
    candidate, however twin-like the URL. None when there are too few clicks to
    judge."""
    qc = page_query_clicks.get(page) or {}
    total = sum(qc.values())
    if total < 10:
        return None
    other_q = set(page_ranks_for.get(other) or ())
    return sum(c for q, c in qc.items() if q not in other_q) / total


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------


def mann_kendall(values):
    """Non-parametric monotonic-trend test. Returns (direction, z) where 'flat'
    means not significant at p < 0.05. Scale-free : unlike a raw slope
    threshold, which means nothing without knowing the click scale."""
    x = np.asarray([float(v) for v in values], dtype=float)
    n = len(x)
    if n < 8:
        return ('flat', 0.0)
    s = 0.0
    for i in range(n - 1):
        s += float(np.sign(x[i + 1:] - x[i]).sum())
    _u, counts = np.unique(x, return_counts=True)
    tie = float(sum(c * (c - 1) * (2 * c + 5) for c in counts))
    var = (n * (n - 1) * (2 * n + 5) - tie) / 18.0
    if var <= 0:
        return ('flat', 0.0)
    z = (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var) if s < 0 else 0.0
    if abs(z) < 1.96:
        return ('flat', float(z))
    return ('up' if z > 0 else 'down', float(z))


def label_trend(weekly_clicks):
    w = np.asarray(weekly_clicks, dtype=float)
    if len(w) == 0 or w.sum() == 0:
        return 'Hits 0 Clicks'
    zero_ratio = 1 - ((w > 0).sum() / len(w))
    cv = w.std() / max(w.mean(), 1e-9)
    if zero_ratio > 0.4:
        return 'Unstable, Fluctuation and Hits 0 Clicks'
    direction, _z = mann_kendall(w)
    if direction == 'up' and cv < 0.8:
        return 'Positive, Growing & Stable Position'
    if direction == 'down':
        return 'Negative, Declining'
    if cv > 1.2:
        return 'Random, De-index time and again'
    return 'Stable, Flat'


# ---------------------------------------------------------------------------
# Query universe
# ---------------------------------------------------------------------------


def build_universe(matrix, brand_tokens, q_to_topic=None):
    """Brand-normalise (and optionally topic-canonicalise) every query, then roll
    up per page. Returns the maps the shortlister and cascade consume."""
    pq = matrix.groupby(['page', 'query']).agg(
        impressions=('impressions', 'sum'),
        clicks=('clicks', 'sum'),
        position=('position', 'mean'),
    ).reset_index()
    pq['nq'] = pq['query'].map(lambda q: normalize_brand_query(q, brand_tokens))
    brand_only = sorted(set(pq.loc[pq['nq'] == '', 'query']))
    kept = pq[pq['nq'] != ''].copy()
    if q_to_topic:
        kept['nq'] = kept['nq'].map(lambda n: q_to_topic.get(n, n))
    pqn = kept.groupby(['page', 'nq']).agg(
        impressions=('impressions', 'sum'),
        clicks=('clicks', 'sum'),
        position=('position', 'mean'),
    ).reset_index().rename(columns={'nq': 'query'})

    top_queries, impr_map, clicks_map, pos_map, top_click_qs = {}, {}, {}, {}, {}
    for page, g in pqn.groupby('page'):
        g_impr = g.sort_values('impressions', ascending=False)
        g_click = g.sort_values('clicks', ascending=False)
        top_queries[page] = sorted(g['query'])
        impr_map[page] = dict(zip(g_impr['query'], g_impr['impressions'].astype(float)))
        clicks_map[page] = dict(zip(g_impr['query'], g_impr['clicks'].astype(float)))
        pos_map[page] = dict(zip(g_impr['query'], g_impr['position'].astype(float)))
        top_click_qs[page] = list(g_click[g_click['clicks'] > 0].head(10)['query'])

    n_pages = max(len(top_queries), 1)
    df_count = {}
    for qs in top_queries.values():
        for q in qs:
            df_count[q] = df_count.get(q, 0) + 1
    idf = {q: math.log(n_pages / d) for q, d in df_count.items()}

    return {
        'top_queries': top_queries, 'clicks_map': clicks_map, 'impr_map': impr_map,
        'pos_map': pos_map, 'top_click_qs': top_click_qs, 'idf': idf,
        'df_count': df_count, 'n_pages': n_pages,
        'brand_only_queries': brand_only, 'brand_tokens': brand_tokens,
    }


# ---------------------------------------------------------------------------
# Per-page rollup
# ---------------------------------------------------------------------------


def build_pages(matrix, cfg, end_date):
    """Per-URL rollup: window totals, recent position, weekly trend."""
    agg = matrix.groupby('page').agg(
        clicks_window=('clicks', 'sum'),
        impressions_window=('impressions', 'sum'),
        queries=('query', 'nunique'),
    ).reset_index()

    has_date = ('date' in matrix.columns
                and bool(np.asarray(matrix['date'].notna(), dtype=bool).any()))
    recent_cut = pd.Timestamp(end_date) - pd.Timedelta(days=cfg['recent_window_days'])

    pos_90d, trend_label, trend_slope, first_click, last_click = {}, {}, {}, {}, {}
    for page, g in matrix.groupby('page'):
        window = g[g['date'] >= recent_cut] if has_date else g
        valid = window[(window['impressions'] > 0) & window['position'].notna()]
        pos_90d[page] = (float((valid['position'] * valid['impressions']).sum()
                               / valid['impressions'].sum()) if not valid.empty else None)
        if has_date:
            weekly = (g.assign(week=g['date'].dt.to_period('W-SUN').dt.start_time)
                       .groupby('week')['clicks'].sum().sort_index().tail(cfg['trend_weeks']))
            trend_label[page] = label_trend(weekly.values)
            trend_slope[page] = mann_kendall(weekly.values)[1]
            clicked = g[g['clicks'] > 0]
            first_click[page] = str(clicked['date'].min().date()) if not clicked.empty else ''
            last_click[page] = str(clicked['date'].max().date()) if not clicked.empty else ''
        else:
            trend_label[page], trend_slope[page] = 'unknown (no date dimension)', 0.0
            first_click[page] = last_click[page] = ''

    agg['avg_position_90d'] = agg['page'].map(pos_90d)
    agg['trend'] = agg['page'].map(trend_label)
    agg['trend_slope'] = agg['page'].map(trend_slope)
    agg['first_click'] = agg['page'].map(first_click)
    agg['last_click'] = agg['page'].map(last_click)
    return agg.sort_values('impressions_window', ascending=False).reset_index(drop=True)


def appearance_share_per_page(by_page_appearance, page_total_impressions=None):
    """GSC's searchAppearance dimension reports only ENRICHED surfaces : plain
    blue links carry no label. So the WEB share is a page's total impressions
    minus its enriched ones."""
    if by_page_appearance is None or by_page_appearance.empty:
        return {}
    page_total_impressions = page_total_impressions or {}
    web_like = {'', 'AMP_BLUE_LINK', 'AMP_TOP_STORIES', 'PAGE_EXPERIENCE'}
    out = {}
    for page, grp in by_page_appearance.groupby('page'):
        enriched = float(grp['impressions'].sum())
        total = max(float(page_total_impressions.get(page, enriched)) or 1.0, enriched)
        plain_web = total - enriched
        mix, web_impr, non_web = {}, plain_web, 0.0
        for _, r in grp.iterrows():
            appearance = r.get('searchappearance') or ''
            impr = float(r['impressions'])
            mix[appearance or 'WEB'] = impr / total
            if appearance in web_like:
                web_impr += impr
            else:
                non_web += impr
        if plain_web > 0:
            mix['WEB'] = mix.get('WEB', 0.0) + plain_web / total
        out[page] = {'web_share': web_impr / total, 'non_web_share': non_web / total,
                     'mix': mix, 'total_impressions': int(total)}
    return out


# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--site', default='')
    ap.add_argument('--matrix', required=True, nargs='+',
                    help='one or more GSC page x query [x date] dumps')
    ap.add_argument('--appearance', default='')
    ap.add_argument('--page-totals', default='')
    ap.add_argument('--config', default='')
    ap.add_argument('--end-date', default='')
    args = ap.parse_args()

    cfg, raw_cfg = load_cfg(args.config or None)
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    frames = [load_rows(m) for m in args.matrix]
    matrix = _as_frame(pd.concat([f for f in frames if not f.empty], ignore_index=True))
    _require(matrix, ['page', 'query', 'clicks', 'impressions'], 'matrix')
    if 'position' not in matrix.columns:
        matrix['position'] = np.nan
    for c in ('clicks', 'impressions', 'position'):
        matrix[c] = pd.to_numeric(matrix[c], errors='coerce')
    matrix = _as_frame(matrix.dropna(subset=['page', 'query']))
    raw_url_count = int(_as_series(matrix['page']).nunique())
    matrix['page'] = _as_series(matrix['page']).map(canonical_url)
    urls_merged_by_canonical = raw_url_count - int(_as_series(matrix['page']).nunique())
    matrix['clicks'] = _numeric_filled(matrix['clicks'])
    matrix['impressions'] = _numeric_filled(matrix['impressions'])
    if 'date' in matrix.columns:
        matrix['date'] = pd.to_datetime(matrix['date'], errors='coerce')
        date_ok = _as_series(matrix['date']).notna()
        if bool(np.asarray(date_ok, dtype=bool).any()):
            matrix = _as_frame(matrix.loc[date_ok])
        else:
            matrix = _as_frame(matrix.drop(columns=['date']))

    inputs = raw_cfg.get('inputs', {})
    patterns = inputs.get('exclude_url_patterns') or cfg['exclude_url_patterns']
    excluded_urls = []
    if patterns:
        hit = _as_series(matrix['page']).str.contains(
            '|'.join(re.escape(p) for p in patterns), case=False, na=False)
        excluded_urls = sorted(set(_as_series(matrix.loc[hit, 'page'])))
        matrix = _as_frame(matrix.loc[~np.asarray(hit, dtype=bool)])
    include = inputs.get('include_urls') or cfg['include_urls']
    if include:
        matrix = _as_frame(matrix.loc[np.isin(np.asarray(matrix['page']), list(include))])
    if matrix.empty:
        raise SystemExit('no rows left after URL filtering : check exclude_url_patterns')

    has_date = 'date' in matrix.columns
    if args.end_date:
        end_date = _as_timestamp(args.end_date)
    elif has_date:
        end_date = _as_timestamp(_as_series(matrix['date']).max())
    else:
        end_date = pd.Timestamp.today().normalize()

    pages = build_pages(matrix, cfg, end_date)
    max_urls = int(cfg.get('max_urls') or 0)
    dropped_for_scale = []
    if max_urls and len(pages) > max_urls:
        dropped_for_scale = list(pages['page'][max_urls:])
        pages = pages.iloc[:max_urls].reset_index(drop=True)
        matrix = _as_frame(matrix.loc[np.isin(np.asarray(matrix['page']), list(pages['page']))])

    site = args.site or inputs.get('gsc_property', '')
    brand_tokens = detect_brand_tokens(site, cfg.get('brand_tokens') or inputs.get('brand_tokens'))
    universe = build_universe(matrix, brand_tokens)

    matrix.to_csv(work / 'matrix.csv', index=False)
    pages.to_csv(work / 'pages.csv', index=False)
    (work / 'universe.json').write_text(json.dumps(universe, indent=1), encoding='utf-8')

    appearance = {}
    if args.appearance:
        ap_df = load_rows(args.appearance)
        if args.page_totals:
            tot = load_rows(args.page_totals)
            totals = (dict(zip(_as_series(tot['page']), _numeric_filled(tot['impressions'])))
                      if {'page', 'impressions'} <= set(tot.columns) else {})
        else:
            totals = dict(zip(_as_series(pages['page']), _as_series(pages['impressions_window'])))
        if not ap_df.empty and 'searchappearance' in ap_df.columns:
            ap_df['impressions'] = _numeric_filled(ap_df['impressions'])
            appearance = appearance_share_per_page(ap_df, totals)
    (work / 'appearance.json').write_text(json.dumps(appearance, indent=1), encoding='utf-8')

    meta = {
        'site': site, 'end_date': str(end_date.date()),
        'has_date_dimension': bool(has_date),
        'urls_analyzed': len(pages), 'rows': len(matrix),
        'queries_distinct': int(_as_series(matrix['query']).nunique()),
        'brand_tokens': brand_tokens,
        'brand_only_queries_dropped': len(universe['brand_only_queries']),
        'urls_merged_by_canonicalisation': int(urls_merged_by_canonical),
        'urls_pattern_excluded': excluded_urls,
        'urls_dropped_for_scale': dropped_for_scale,
        'appearance_pages': len(appearance),
    }
    (work / 'meta.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')

    print(f'urls={len(pages)} rows={len(matrix)} queries={meta["queries_distinct"]} '
          f'date_dim={has_date} brand={brand_tokens}')
    if dropped_for_scale:
        print(f'NOTE: capped at max_urls={max_urls}; {len(dropped_for_scale)} lower-impression '
              f'URLs excluded from this run (listed in meta.json).')
    if not has_date:
        print('WARNING: no `date` column : the handoff detector cannot run and ongoing parity '
              'falls back to aggregate-window comparison. Re-pull per URL with '
              'dimensions ["date","query"] for full power.')


if __name__ == '__main__':
    main()
