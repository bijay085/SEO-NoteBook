"""The detectors — every substantive numeric test in the cascade.

Ported from the Cannibalization Analysis app's `app/detectors.py`, with the one
dependency change the skill environment requires: `scipy.stats.spearmanr` is
replaced by a local rank-transform + Pearson, which is what Spearman *is*
(average ranks for ties). No scipy, no third-party AI.

Nothing here makes a judgment call — it measures. Every function returns the
measured values alongside the pass/fail, so the report quotes evidence rather
than asserting a conclusion.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Weekly resampling
# ---------------------------------------------------------------------------


def to_weekly_per_query(date_query_df):
    """Pivot (date, query, clicks, impressions, position) into per-query weekly
    series: {query: DataFrame[week, clicks, impressions, position]}.
    Position is impression-weighted within each week."""
    out = {}
    if date_query_df is None or date_query_df.empty:
        return out
    df = date_query_df.copy()
    df['week'] = df['date'].dt.to_period('W-SUN').dt.start_time
    df['pos_impr'] = df['position'] * df['impressions']
    grp = df.groupby(['query', 'week']).agg(
        clicks=('clicks', 'sum'),
        impressions=('impressions', 'sum'),
        pos_impr=('pos_impr', 'sum'),
    ).reset_index()
    grp['position'] = grp['pos_impr'] / grp['impressions'].replace(0, np.nan)
    grp = grp.drop(columns=['pos_impr'])
    for q, g in grp.groupby('query'):
        out[q] = g.sort_values('week').reset_index(drop=True)
    return out


def align_weekly(series_a, series_b, fill_value=0):
    """Outer-join two weekly frames on `week`. Missing weeks get 0
    clicks/impressions; position stays NaN (absent, not 'ranked at 0')."""
    a = series_a.rename(columns={'clicks': 'clicks_a', 'impressions': 'impressions_a',
                                 'position': 'position_a'})
    b = series_b.rename(columns={'clicks': 'clicks_b', 'impressions': 'impressions_b',
                                 'position': 'position_b'})
    m = a.merge(b, on='week', how='outer').sort_values('week').reset_index(drop=True)
    for c in ('clicks_a', 'clicks_b', 'impressions_a', 'impressions_b'):
        m[c] = m[c].fillna(fill_value).astype(float)
    return m


# ---------------------------------------------------------------------------
# Rank correlation (scipy-free Spearman)
# ---------------------------------------------------------------------------


def _rankdata(x):
    """Ranks with ties averaged — the transform that turns Pearson into
    Spearman. Matches scipy.stats.rankdata(method='average')."""
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind='mergesort')
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1, dtype=float)
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return ranks


def spearman(a, b):
    """Spearman rank correlation. Returns 0.0 when undefined (constant series or
    fewer than 3 points) — the neutral value the app used."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 3 or len(a) != len(b):
        return 0.0
    ra, rb = _rankdata(a), _rankdata(b)
    if ra.std() == 0 or rb.std() == 0:
        return 0.0
    r = float(np.corrcoef(ra, rb)[0, 1])
    return 0.0 if math.isnan(r) else r


# ---------------------------------------------------------------------------
# ONGOING detector — is traffic being split on this query right now?
# ---------------------------------------------------------------------------


def parity_test(merged, cfg, end_date, recent_days):
    """Parity gates on one shared query's aligned weekly series.

    Returns pass/fail plus every gate's measured value. A failing query drops
    out of the 'competing' set; the pair verdict needs >= N passing."""
    cutoff = pd.Timestamp(end_date) - pd.Timedelta(days=recent_days)
    recent = merged[merged['week'] >= cutoff].copy()
    if recent.empty:
        return {'qualifies': False, 'reason': 'no recent weeks', 'evidence': {}}

    weeks_total = len(recent)
    weeks_both_impr = int(((recent['impressions_a'] > 0) & (recent['impressions_b'] > 0)).sum())
    simultaneity = weeks_both_impr / max(weeks_total, 1)

    ca = float(recent['clicks_a'].sum())
    cb = float(recent['clicks_b'].sum())
    ia = float(recent['impressions_a'].sum())
    ib = float(recent['impressions_b'].sum())
    click_parity = min(ca, cb) / max(ca, cb) if max(ca, cb) > 0 else 0.0
    impr_parity = min(ia, ib) / max(ia, ib) if max(ia, ib) > 0 else 0.0

    def _wmean(df, pos_col, impr_col):
        valid = df[(df[impr_col] > 0) & df[pos_col].notna()]
        if valid.empty:
            return None
        return float((valid[pos_col] * valid[impr_col]).sum() / valid[impr_col].sum())

    pos_a = _wmean(recent, 'position_a', 'impressions_a')
    pos_b = _wmean(recent, 'position_b', 'impressions_b')
    if pos_a is None or pos_b is None:
        pos_delta = pos_max = None
    else:
        pos_delta = abs(pos_a - pos_b)
        pos_max = max(pos_a, pos_b)

    evidence = {
        'weeks_recent': weeks_total,
        'weeks_both_impr': weeks_both_impr,
        'simultaneity_pct': round(simultaneity, 3),
        'clicks_a': int(ca), 'clicks_b': int(cb),
        'click_parity': round(click_parity, 3),
        'impressions_a': int(ia), 'impressions_b': int(ib),
        'impr_parity': round(impr_parity, 3),
        'position_a': round(pos_a, 2) if pos_a is not None else None,
        'position_b': round(pos_b, 2) if pos_b is not None else None,
        'position_delta': round(pos_delta, 2) if pos_delta is not None else None,
    }

    gates = []
    # Materiality first — without it a query with 1 click each side scores
    # click_parity 1.0 and "qualifies" as an ongoing cannibal despite being pure
    # noise. That noise is what produces nonsensical clusters.
    min_total = cfg.get('ongoing_min_query_total_clicks', 15)
    min_each = cfg.get('ongoing_min_query_clicks_each_side', 3)
    if (ca + cb) < min_total:
        gates.append(f'clicks_total={int(ca + cb)}<{min_total} (noise — not material)')
    if min(ca, cb) < min_each:
        gates.append(f'clicks_min_side={int(min(ca, cb))}<{min_each} (one side has no real traffic)')
    if click_parity < cfg['ongoing_min_click_parity']:
        gates.append(f'click_parity={click_parity:.2f}<{cfg["ongoing_min_click_parity"]}')
    if impr_parity < cfg['ongoing_min_impr_parity']:
        gates.append(f'impr_parity={impr_parity:.2f}<{cfg["ongoing_min_impr_parity"]}')
    if pos_delta is None or pos_delta > cfg['ongoing_max_position_delta']:
        gates.append(f'pos_delta={pos_delta}>{cfg["ongoing_max_position_delta"]}')
    if pos_max is None or pos_max > cfg['ongoing_max_position_abs']:
        gates.append(f'pos_max={pos_max}>{cfg["ongoing_max_position_abs"]}')
    if simultaneity < cfg['ongoing_min_simultaneity_pct']:
        gates.append(f'simultaneity={simultaneity:.2f}<{cfg["ongoing_min_simultaneity_pct"]}')
    if weeks_total < cfg['ongoing_min_weeks_observed']:
        gates.append(f'weeks={weeks_total}<{cfg["ongoing_min_weeks_observed"]}')

    return {
        'qualifies': not gates,
        'reason': '; '.join(gates) if gates else 'all parity gates pass',
        'evidence': evidence,
    }


def detect_ongoing(weekly_a, weekly_b, shared_queries, cfg, end_date):
    """Parity test across every shared query."""
    qualifying, rejected = [], []
    for q in shared_queries:
        if q not in weekly_a or q not in weekly_b:
            continue
        merged = align_weekly(weekly_a[q], weekly_b[q])
        result = parity_test(merged, cfg, end_date, cfg['recent_window_days'])
        entry = {'query': q, 'evidence': result['evidence'], 'reason': result['reason']}
        (qualifying if result['qualifies'] else rejected).append(entry)
    return {
        'verdict': len(qualifying) >= cfg['ongoing_min_qualifying_queries'],
        'qualifying_queries': qualifying,
        'rejected_queries': rejected,
    }


# ---------------------------------------------------------------------------
# AFFECTED detector — did one URL already replace the other?
# ---------------------------------------------------------------------------


def _rolling(series, window):
    return series.rolling(window=window, min_periods=1, center=False).mean()


def detect_handoff_for_query(merged, cfg):
    """One shared query — find the crossover where A went silent and B took over.

    1. Smooth both click series (handoff_smoothing_weeks rolling mean).
    2. A's peak must clear handoff_min_pre_clicks.
    3. B's peak AFTER A's peak must clear handoff_min_post_clicks.
    4. Crossover = first week in that zone where smoothed B >= smoothed A.
    5. A must then stay near-silent for handoff_post_silence_weeks.
    6. Co-existence zone of >= handoff_min_coexistence_weeks where both had clicks.
    7. Anti-correlation across the zone: Spearman r <= handoff_min_anticorrelation.
    """
    if merged.empty or len(merged) < 8:
        return {'qualifies': False, 'reason': 'too few weeks', 'evidence': {}}

    sw = cfg['handoff_smoothing_weeks']
    a_smooth = _rolling(merged['clicks_a'], sw)
    b_smooth = _rolling(merged['clicks_b'], sw)

    peak_a_idx = int(a_smooth.idxmax())
    peak_a_val = float(a_smooth.iloc[peak_a_idx])
    if peak_a_val < cfg['handoff_min_pre_clicks']:
        return {'qualifies': False,
                'reason': f'A peak {peak_a_val:.1f} < {cfg["handoff_min_pre_clicks"]}',
                'evidence': {}}

    if len(merged.iloc[peak_a_idx:]) < cfg['handoff_post_silence_weeks']:
        return {'qualifies': False, 'reason': 'not enough weeks after A peak', 'evidence': {}}
    peak_b_idx = int(b_smooth.iloc[peak_a_idx:].idxmax())
    peak_b_val = float(b_smooth.iloc[peak_b_idx])
    if peak_b_val < cfg['handoff_min_post_clicks']:
        return {'qualifies': False,
                'reason': f'B post-A peak {peak_b_val:.1f} < {cfg["handoff_min_post_clicks"]}',
                'evidence': {}}

    zone_a = a_smooth.iloc[peak_a_idx:peak_b_idx + 1].values
    zone_b = b_smooth.iloc[peak_a_idx:peak_b_idx + 1].values
    if len(zone_a) == 0:
        return {'qualifies': False, 'reason': 'no transition zone', 'evidence': {}}
    crossover_offset = None
    for i in range(len(zone_a)):
        if zone_b[i] >= zone_a[i] and zone_b[i] >= cfg['handoff_min_post_clicks'] * 0.5:
            crossover_offset = i
            break
    if crossover_offset is None:
        return {'qualifies': False, 'reason': 'no crossover (B never overtook A)', 'evidence': {}}
    crossover_idx = peak_a_idx + crossover_offset
    crossover_week = merged.iloc[crossover_idx]['week']

    post = merged.iloc[crossover_idx + 1:crossover_idx + 1 + cfg['handoff_post_silence_weeks']]
    if len(post) < cfg['handoff_post_silence_weeks']:
        return {'qualifies': False, 'reason': 'not enough post-crossover weeks', 'evidence': {}}
    a_post_avg = float(_rolling(post['clicks_a'], sw).mean())
    if a_post_avg > peak_a_val * 0.20:
        # A is still alive — that is an ongoing split, not a completed handoff.
        return {'qualifies': False,
                'reason': f'A post-crossover avg {a_post_avg:.1f} > 20% of A peak {peak_a_val:.1f}',
                'evidence': {}}

    coexist = merged.iloc[peak_a_idx:crossover_idx + 1]
    coexist_weeks = int(((coexist['clicks_a'] > 0) & (coexist['clicks_b'] > 0)).sum())
    if coexist_weeks < cfg['handoff_min_coexistence_weeks']:
        return {'qualifies': False,
                'reason': f'coexistence_weeks={coexist_weeks}<{cfg["handoff_min_coexistence_weeks"]}',
                'evidence': {}}

    # Rank correlation, not Pearson — weekly click series are spiky and a single
    # spike swings Pearson. Spearman asks the real question: as A falls, does B rise?
    full_a = merged.iloc[peak_a_idx:peak_b_idx + 1]['clicks_a'].values
    full_b = merged.iloc[peak_a_idx:peak_b_idx + 1]['clicks_b'].values
    r = spearman(full_a, full_b) if len(full_a) >= 4 else 0.0
    if r > cfg['handoff_min_anticorrelation']:
        return {'qualifies': False,
                'reason': f'spearman_r={r:.2f}>{cfg["handoff_min_anticorrelation"]} '
                          f'(not anticorrelated enough)',
                'evidence': {'spearman_r': round(r, 3),
                             'crossover_week': str(crossover_week.date())}}

    # Residual evidence: the loser's clicks after the crossover. Near-zero
    # confirms the handoff completed.
    loser_residual = float(merged.iloc[crossover_idx + 1:]['clicks_a'].sum())
    return {
        'qualifies': True,
        'handoff_date': crossover_week,
        'reason': 'crossover confirmed with anti-correlation',
        'evidence': {
            'peak_a': round(peak_a_val, 1),
            'peak_b': round(peak_b_val, 1),
            'crossover_week': str(crossover_week.date()),
            'coexistence_weeks': coexist_weeks,
            'spearman_r': round(r, 3),
            'a_post_avg': round(a_post_avg, 1),
            'loser_residual_clicks': int(loser_residual),
        },
    }


def detect_handoff(weekly_a, weekly_b, shared_queries, cfg):
    """Run the per-query handoff detector in both directions. The direction with
    more qualifying queries wins."""
    def run_one(wa, wb):
        qual, rej = [], []
        for q in shared_queries:
            if q not in wa or q not in wb:
                continue
            r = detect_handoff_for_query(align_weekly(wa[q], wb[q]), cfg)
            entry = {'query': q, 'evidence': r['evidence'], 'reason': r['reason']}
            if r['qualifies']:
                entry['handoff_date'] = r['handoff_date']
                qual.append(entry)
            else:
                rej.append(entry)
        return qual, rej

    qa_to_b, rej_ab = run_one(weekly_a, weekly_b)
    qb_to_a, rej_ba = run_one(weekly_b, weekly_a)

    direction, qualifying = None, []
    min_q = cfg['handoff_min_qualifying_queries']
    if len(qa_to_b) >= min_q and len(qa_to_b) >= len(qb_to_a):
        direction, qualifying = 'a_to_b', qa_to_b
    elif len(qb_to_a) >= min_q:
        direction, qualifying = 'b_to_a', qb_to_a

    handoff_date = None
    if qualifying:
        dates = sorted(e['handoff_date'] for e in qualifying if e.get('handoff_date') is not None)
        if dates:
            handoff_date = dates[len(dates) // 2]        # median

    return {
        'verdict': direction is not None,
        'direction': direction,
        'handoff_date': handoff_date,
        'qualifying_queries': qualifying,
        'rejected_queries': rej_ab + rej_ba,
    }


# ---------------------------------------------------------------------------
# REDUNDANT DUPLICATE — no live split, but one page is dead weight
# ---------------------------------------------------------------------------


def assess_redundant(ongoing, cfg):
    """When a pair fails the ongoing parity test, is it instead a redundant
    duplicate — several shared queries where one page is consistently dominated?

    Dominated means consistently weaker AND either *buried* (median position
    worse than redundant_buried_position) or *out-clicked* (under
    redundant_max_weak_click_share of the pair's clicks). The second arm closes
    the gap the parity gate leaves: an 80/20 split with both pages on page 1
    fails parity yet is plainly not a contest.
    """
    min_shared = cfg.get('redundant_min_shared_queries', 3)
    dom_frac = cfg.get('redundant_dominance_frac', 0.70)
    buried_pos = cfg.get('redundant_buried_position', 15.0)
    max_weak_share = cfg.get('redundant_max_weak_click_share', 0.25)

    # Only queries where BOTH pages genuinely co-appeared count.
    considered = [e['evidence'] for e in ongoing.get('rejected_queries', [])
                  if (e.get('evidence') or {}).get('impressions_a', 0) > 0
                  and (e.get('evidence') or {}).get('impressions_b', 0) > 0]
    n = len(considered)
    if n < min_shared:
        return {'verdict': False, 'weak_side': None, 'shared_count': n,
                'median_pos': None, 'weak_click_share': None,
                'reason': f'only {n} co-appearing shared queries (<{min_shared})'}

    weak_count = {'a': 0, 'b': 0}
    weak_positions = {'a': [], 'b': []}
    total_clicks = {'a': 0.0, 'b': 0.0}
    for ev in considered:
        ca = ev.get('clicks_a', 0) or 0
        cb = ev.get('clicks_b', 0) or 0
        pa, pb = ev.get('position_a'), ev.get('position_b')
        total_clicks['a'] += ca
        total_clicks['b'] += cb
        if ca < cb:
            weak = 'a'
        elif cb < ca:
            weak = 'b'
        else:
            weak = 'a' if (pa or 999) > (pb or 999) else 'b'
        weak_count[weak] += 1
        pos = pa if weak == 'a' else pb
        if pos is not None:
            weak_positions[weak].append(pos)

    dom_weak = 'a' if weak_count['a'] >= weak_count['b'] else 'b'
    if weak_count[dom_weak] / n < dom_frac:
        return {'verdict': False, 'weak_side': None, 'shared_count': n,
                'median_pos': None, 'weak_click_share': None,
                'reason': 'no consistent weaker page across shared queries'}

    positions = sorted(weak_positions[dom_weak])
    median_pos = positions[len(positions) // 2] if positions else None
    pair_clicks = total_clicks['a'] + total_clicks['b']
    weak_share = (total_clicks[dom_weak] / pair_clicks) if pair_clicks > 0 else None

    is_buried = median_pos is not None and median_pos > buried_pos
    is_outclicked = weak_share is not None and weak_share < max_weak_share
    if not (is_buried or is_outclicked):
        bits = []
        if median_pos is not None:
            bits.append(f'median position {median_pos:.0f} not buried')
        if weak_share is not None:
            bits.append(f'click share {weak_share * 100:.0f}% not dominated')
        return {'verdict': False, 'weak_side': None, 'shared_count': n,
                'median_pos': median_pos, 'weak_click_share': weak_share,
                'reason': 'weaker page is not decisively dominated ('
                          + '; '.join(bits or ['insufficient signal']) + ')'}

    why = []
    if is_buried:
        why.append(f'median position {median_pos:.0f} (buried)')
    if is_outclicked:
        why.append(f"only {weak_share * 100:.0f}% of the pair's clicks")
    return {'verdict': True, 'weak_side': dom_weak, 'shared_count': n,
            'median_pos': median_pos, 'weak_click_share': weak_share,
            'reason': (f'redundant duplicate — across {n} shared queries the weaker page '
                       f'is decisively dominated (' + ' and '.join(why) + ') while the '
                       f'other owns them; not an even click split, but the weaker page '
                       f'is a redundant duplicate.')}


# ---------------------------------------------------------------------------
# SERP-feature attribution (GSC searchAppearance)
# ---------------------------------------------------------------------------


def serp_attribution_filter(url_a, url_b, appearance_share, cfg):
    """Are the two pages competing on the same SERP surface? If one lives mostly
    in Featured Snippet / Video / Rich Result while the other is plain organic,
    they are not competing."""
    a = appearance_share.get(url_a) or {}
    b = appearance_share.get(url_b) or {}
    a_nw = a.get('non_web_share', 0.0)
    b_nw = b.get('non_web_share', 0.0)
    delta = abs(a_nw - b_nw)

    def top_appearance(rec):
        mix = (rec or {}).get('mix', {})
        return max(mix.items(), key=lambda kv: kv[1])[0] if mix else ''

    a_top, b_top = top_appearance(a), top_appearance(b)
    a_dom = a_nw >= cfg['serp_non_web_appearance_dominance']
    b_dom = b_nw >= cfg['serp_non_web_appearance_dominance']

    base = {'delta': round(delta, 3),
            'a_non_web_share': round(a_nw, 3), 'b_non_web_share': round(b_nw, 3),
            'a_top_appearance': a_top, 'b_top_appearance': b_top}
    if a_dom != b_dom and delta >= cfg['serp_attribution_min_delta']:
        dom_url = url_a if a_dom else url_b
        dom_top = a_top if a_dom else b_top
        dom_share = a_nw if a_dom else b_nw
        return {**base, 'same_surface': False,
                'reason': (f'{dom_url} dominated by {dom_top} ({dom_share * 100:.0f}%) '
                           f'while the other is organic — different surface')}
    return {**base, 'same_surface': True,
            'reason': 'same organic surface (or both share non-WEB appearance)'}


# ---------------------------------------------------------------------------
# Leakage — what the loser held that the winner never picked up
# ---------------------------------------------------------------------------


def quantify_leakage(weekly_loser, weekly_winner, handoff_date, end_date, cfg):
    """Compare the loser's pre-handoff window against the winner's post-handoff
    window. This is what says whether a 301 is safe or needs a content migration
    first."""
    if handoff_date is None:
        return {'available': False, 'reason': 'no handoff date'}
    pre_start = handoff_date - pd.Timedelta(days=180)
    pre_end = handoff_date - pd.Timedelta(days=30)
    post_start = handoff_date + pd.Timedelta(days=30)
    post_end = pd.Timestamp(end_date)

    def window_stats(weekly_dict, ws, we):
        stats = {}
        for q, df in weekly_dict.items():
            sl = df[(df['week'] >= ws) & (df['week'] <= we)]
            if sl.empty:
                continue
            clicks = float(sl['clicks'].sum())
            impr = float(sl['impressions'].sum())
            valid = sl[(sl['impressions'] > 0) & sl['position'].notna()]
            pos = (float((valid['position'] * valid['impressions']).sum()
                         / valid['impressions'].sum()) if not valid.empty else None)
            if clicks > 0 or impr > 0:
                stats[q] = {'clicks': clicks, 'impressions': impr, 'position': pos}
        return stats

    loser_pre = window_stats(weekly_loser, pre_start, pre_end)
    winner_post = window_stats(weekly_winner, post_start, post_end)
    loser_pre_qs = {q for q, s in loser_pre.items() if s['clicks'] > 0}
    winner_post_qs = {q for q, s in winner_post.items() if s['clicks'] > 0}

    lost = sorted(loser_pre_qs - winner_post_qs, key=lambda q: -loser_pre[q]['clicks'])
    retained = sorted(loser_pre_qs & winner_post_qs, key=lambda q: -loser_pre[q]['clicks'])
    new = sorted(winner_post_qs - loser_pre_qs, key=lambda q: -winner_post[q]['clicks'])

    total_pre = sum(s['clicks'] for s in loser_pre.values())
    total_post = sum(s['clicks'] for s in winner_post.values())
    delta = total_post - total_pre
    delta_pct = (delta / total_pre) if total_pre > 0 else 0.0

    regressions = []
    for q in retained[:20]:
        pre_pos = loser_pre[q].get('position')
        post_pos = winner_post[q].get('position')
        if pre_pos and post_pos and post_pos > pre_pos + 2.0:
            regressions.append({'query': q, 'pre_position': round(pre_pos, 1),
                                'post_position': round(post_pos, 1),
                                'delta': round(post_pos - pre_pos, 1)})

    severity = 'none'
    if delta_pct <= -cfg['leakage_critical_pct']:
        severity = 'critical'
    elif delta_pct <= -cfg['leakage_warning_pct']:
        severity = 'warning'

    return {
        'available': True,
        'handoff_date': str(handoff_date.date()) if hasattr(handoff_date, 'date') else str(handoff_date),
        'pre_window': f'{pre_start.date()} → {pre_end.date()}',
        'post_window': f'{post_start.date()} → {post_end.date()}',
        'total_clicks_pre': int(total_pre), 'total_clicks_post': int(total_post),
        'clicks_delta': int(delta), 'clicks_delta_pct': round(delta_pct, 3),
        'lost_queries': [{'query': q, 'clicks_pre': int(loser_pre[q]['clicks'])} for q in lost[:25]],
        'retained_queries_count': len(retained),
        'new_queries_count': len(new),
        'top_lost_queries_count': len(lost),
        'position_regressions': regressions[:10],
        'severity': severity,
    }
