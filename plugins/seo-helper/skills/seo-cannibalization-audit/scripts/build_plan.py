"""Clusters, winners, and the per-URL action plan.

Verdict-positive pairs become cluster edges; connected components group a topic's
competing pages under one winner. Three verdicts deliberately do NOT cluster:
`redundant_duplicate` (the detector already named the buried page, so a
score-based winner-pick could override a correct direction), `overlap_watch`
(monitor-only) and `differentiate` (keep both). Those are flat post-passes.

Cluster-strength gate: an ongoing verdict on a SINGLE qualifying query with low
absolute volume is technically valid but noise-prone — usually a coincidence on
one ambiguous term. It stays visible in pair_verdicts but does not drag two pages
into the same cluster.

Usage:
    python build_plan.py --work <dir> [--config config.json]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd

from cannib_config import load_cfg

# Priority = the cascade order the client works top-down.
STATUS_ORDER = {
    'duplicate': 1, 'ongoing cannibal': 2, 'affected_handoff (loser)': 3,
    'redundant duplicate': 4, 'differentiate — keep both': 5, 'overlap watch': 6,
    'cluster winner': 7, 'affected_handoff (winner)': 7,
    'standalone': 8, 'standalone (0 clicks)': 9,
}


def _sigmoid(x):
    try:
        return 1.0 / (1.0 + math.exp(-float(x)))
    except OverflowError:
        return 0.0 if float(x) < 0 else 1.0


def strong_enough_for_cluster(v, cfg):
    if v['verdict'] in ('affected_handoff', 'duplicate'):
        return True
    if v['verdict'] != 'ongoing':
        return False
    qq = (v.get('ongoing') or {}).get('qualifying_queries') or []
    if len(qq) >= 2:
        return True          # the redundancy across queries is itself the signal
    if len(qq) == 1:
        ev = qq[0].get('evidence', {})
        floor = cfg['cluster_min_clicks_for_single_query_ongoing']
        return (int(ev.get('clicks_a') or 0) + int(ev.get('clicks_b') or 0)) >= floor
    return False


def score_cluster(urls_in_cluster, pages_idx, weights):
    present = [u for u in urls_in_cluster if u in pages_idx.index]
    if not present:
        return None
    sub = pages_idx.loc[present].copy()
    max_clicks = max(float(sub['clicks_window'].max()), 1.0)
    pos = sub['avg_position_90d'].fillna(100.0)
    max_pos = max(float(pos.max()), 1.0)
    sub['final_score'] = (weights['clicks'] * (sub['clicks_window'] / max_clicks)
                          + weights['trend'] * sub['trend_slope'].fillna(0.0).map(_sigmoid)
                          + weights['position'] * (1 - pos / max_pos))
    return sub.sort_values('final_score', ascending=False)


def redirect_plan(winner, loser, pages_idx, cfg):
    """Default is an immediate 301. But when the loser is a *rising challenger* —
    newer than the winner and gaining while the winner is flat or declining — an
    immediate redirect kills content that is winning on merit. Stage it."""
    if winner not in pages_idx.index or loser not in pages_idx.index:
        return f'Permanently (301) redirect {loser} → {winner}.'
    w, l = pages_idx.loc[winner], pages_idx.loc[loser]
    l_first, w_first = str(l.get('first_click') or ''), str(w.get('first_click') or '')
    rising = ('Positive' in str(l.get('trend', ''))
              and 'Positive' not in str(w.get('trend', ''))
              and l_first and w_first and l_first > w_first)
    if rising:
        return (f'STAGED — do NOT redirect yet. {loser} is newer and gaining while {winner} is '
                f'flat/declining. 1) Audit what {loser} does better. 2) Port that into {winner}. '
                f'3) rel=canonical on {loser} → {winner}. 4) Observe 4–6 weeks. '
                f'5) 301 only if {winner} re-takes the shared queries.')
    return (f'Permanently (301) redirect {loser} → {winner}, and update internal links pointing '
            f'at {loser}.')


def shared_str(v, limit=6):
    qq = ((v.get('ongoing') or {}).get('qualifying_queries')
          or (v.get('handoff') or {}).get('qualifying_queries') or [])
    return '; '.join(e['query'] for e in qq[:limit])


def evidence_rows(verdicts):
    """One row per qualifying shared query — the audit trail. Read this before
    acting on any large consolidation: one marginal query is far weaker evidence
    than ten in the green."""
    out = []
    for v in verdicts.values():
        if v['verdict'] == 'not_cannibal':
            continue
        for e in ((v.get('ongoing') or {}).get('qualifying_queries') or []):
            out.append({'url_a': v['url_a'], 'url_b': v['url_b'], 'verdict': v['verdict'],
                        'shared_query': e['query'], 'kind': 'ongoing', **e.get('evidence', {})})
        for e in ((v.get('handoff') or {}).get('qualifying_queries') or []):
            out.append({'url_a': v['url_a'], 'url_b': v['url_b'], 'verdict': v['verdict'],
                        'shared_query': e['query'], 'kind': 'handoff',
                        'handoff_winner': v.get('handoff_winner'),
                        'handoff_loser': v.get('handoff_loser'), **e.get('evidence', {})})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--config', default='')
    args = ap.parse_args()

    cfg, _raw = load_cfg(args.config or None)
    work = Path(args.work)
    pv = json.loads((work / 'pair_verdicts.json').read_text(encoding='utf-8'))
    pages = pd.read_csv(work / 'pages.csv')
    meta = json.loads((work / 'meta.json').read_text(encoding='utf-8'))
    universe = json.loads((work / 'universe.json').read_text(encoding='utf-8'))
    topic_map = json.loads((work / 'topic_map.json').read_text(encoding='utf-8'))
    pages_idx = pages.set_index('page')

    verdicts = {frozenset((v['url_a'], v['url_b'])): v for v in pv['verdicts']}
    edges = {k for k, v in verdicts.items() if strong_enough_for_cluster(v, cfg)}
    weak_ongoing = sum(1 for k, v in verdicts.items()
                       if v['verdict'] == 'ongoing' and k not in edges)

    # --- clusters: greedy connected components, strongest page first ------
    clicks_by_url = dict(zip(pages['page'], pages['clicks_window']))
    ordered = sorted(pages['page'], key=lambda u: -clicks_by_url.get(u, 0))
    claimed, clusters = set(), []
    for primary in ordered:
        if primary in claimed:
            continue
        members = [u for u in ordered
                   if u != primary and u not in claimed and frozenset((primary, u)) in edges]
        claimed.update(members)
        claimed.add(primary)
        clusters.append((primary, members))

    weights = cfg['score_weights']
    url_meta, cluster_rows = {}, []
    for cid, (primary, members) in enumerate(clusters, start=1):
        cluster_urls = [primary] + members
        scored = score_cluster(cluster_urls, pages_idx, weights)
        winner = scored.index[0] if scored is not None and len(scored) else primary
        for u in cluster_urls:
            # A single-page cluster has nothing to point at — leave `winner`
            # blank there, or every standalone row would name itself.
            url_meta[u] = {'cluster_id': cid if members else '',
                           'winner': winner if members else ''}
        if members:
            cluster_rows.append({
                'cluster_id': cid, 'winner': winner, 'pages': len(cluster_urls),
                'cannibals': len(members),
                'clicks_total': int(sum(clicks_by_url.get(u, 0) for u in cluster_urls)),
                'clicks_at_stake': int(sum(clicks_by_url.get(u, 0) for u in members)),
            })

    def make_row(url, **kw):
        r = pages_idx.loc[url] if url in pages_idx.index else None
        m = url_meta.get(url, {})
        pos = (round(float(r['avg_position_90d']), 1)
               if r is not None and pd.notna(r.get('avg_position_90d')) else '')
        return {'url': url, 'cluster_id': m.get('cluster_id', ''),
                'winner': m.get('winner', ''),
                'clicks_window': int(r['clicks_window']) if r is not None else 0,
                'impressions_window': int(r['impressions_window']) if r is not None else 0,
                'avg_position_90d': pos,
                'trend': (r.get('trend', '') if r is not None else ''), **kw}

    rows, handled = [], set()

    # --- clustered verdict rows -------------------------------------------
    for cid, (primary, members) in enumerate(clusters, start=1):
        if not members:
            continue
        winner = url_meta[primary]['winner']
        if winner not in handled:
            handled.add(winner)
            rows.append(make_row(winner, status='cluster winner', confidence='High',
                                 action=f'Keep — canonical for cluster #{cid}.',
                                 reason=f'Strongest page in cluster #{cid} by clicks, trend and '
                                        f'position.',
                                 shared_queries='', verdict='cluster_winner'))
        for u in [primary] + members:
            if u == winner or u in handled:
                continue
            v = verdicts.get(frozenset((winner, u))) or verdicts.get(frozenset((primary, u)))
            if v is None:
                continue
            handled.add(u)
            if v['verdict'] == 'affected_handoff':
                hwinner = v.get('handoff_winner') or winner
                leak = v.get('leakage') or {}
                sev, lost = leak.get('severity', 'none'), len(leak.get('lost_queries') or [])
                if u == hwinner:
                    rows.append(make_row(u, status='affected_handoff (winner)', confidence='High',
                                         winner=u,
                                         action='Keep — this page already won the handoff.',
                                         reason=v['reason'], shared_queries=shared_str(v),
                                         verdict=v['verdict']))
                    continue
                if sev == 'critical':
                    action = (f'MIGRATE THEN 301 → {hwinner}. {lost} queries this page held were '
                              f'never picked up — port that content across BEFORE redirecting.')
                elif sev == 'warning':
                    action = f'Review the {lost} lost queries, then 301 → {hwinner}.'
                else:
                    action = f'301 → {hwinner} — nothing valuable was left behind.'
                rows.append(make_row(u, status='affected_handoff (loser)', confidence='High',
                                     winner=hwinner, action=action,
                                     reason=(f'{v["reason"]}. Crossover '
                                             f'{leak.get("handoff_date", "n/a")}, click delta '
                                             f'{(leak.get("clicks_delta_pct") or 0) * 100:.0f}%.'),
                                     shared_queries=shared_str(v), verdict=v['verdict']))
            else:
                status = 'duplicate' if v['verdict'] == 'duplicate' else 'ongoing cannibal'
                rows.append(make_row(u, status=status, confidence='High', winner=winner,
                                     action=redirect_plan(winner, u, pages_idx, cfg),
                                     reason=v['reason'], shared_queries=shared_str(v),
                                     verdict=v['verdict']))

    # --- flat post-passes --------------------------------------------------
    for v in verdicts.values():
        kind = v['verdict']
        if kind not in ('redundant_duplicate', 'overlap_watch', 'differentiate'):
            continue
        a, b = v['url_a'], v['url_b']
        if kind == 'redundant_duplicate':
            weak = a if v.get('redundant_side') == 'a' else b
            keeper = b if weak == a else a
            if weak in handled:
                continue
            handled.add(weak)
            rows.append(make_row(weak, status='redundant duplicate', confidence='Medium',
                                 winner=keeper,
                                 action=(f'Audit {weak} for anything worth keeping, move it into '
                                         f'{keeper}, then 301 {weak} → {keeper}.'),
                                 reason=v['reason'], shared_queries=shared_str(v), verdict=kind))
        elif kind == 'differentiate':
            distinct = v.get('distinct_page') or a
            other = b if distinct == a else a
            if distinct in handled:
                continue
            handled.add(distinct)
            rows.append(make_row(distinct, status='differentiate — keep both', confidence='Medium',
                                 winner='',
                                 action=(f'Keep BOTH {distinct} and {other}. Consolidate only the '
                                         f'genuinely overlapping search terms (trim or canonical '
                                         f'the shared section) and let each page keep owning its '
                                         f'distinct queries. Do NOT 301.'),
                                 reason=v['reason'], shared_queries=shared_str(v), verdict=kind))
        else:
            weaker = a if clicks_by_url.get(a, 0) <= clicks_by_url.get(b, 0) else b
            stronger = b if weaker == a else a
            if weaker in handled:
                continue
            handled.add(weaker)
            rows.append(make_row(weaker, status='overlap watch', confidence='Low', winner=stronger,
                                 action=(f'No action now — monitor. Re-check next analysis; if a '
                                         f'click split appears, consolidate into {stronger}.'),
                                 reason=v['reason'], shared_queries=shared_str(v), verdict=kind))

    # --- everything else ---------------------------------------------------
    for _, r in pages.iterrows():
        u = r['page']
        if u in handled:
            continue
        handled.add(u)
        if int(r['clicks_window'] or 0) == 0:
            status = 'standalone (0 clicks)'
            action = ('Impressions but no clicks — check title, meta description, intent match '
                      'and position. Not cannibalization.')
        else:
            status, action = 'standalone', 'Keep — no other URL competes with it.'
        rows.append(make_row(u, status=status, confidence='', action=action,
                             reason='No verdict-positive pair.', shared_queries='',
                             verdict='standalone'))

    plan = pd.DataFrame(rows)
    plan['priority'] = plan['status'].map(lambda s: STATUS_ORDER.get(s, 10))
    plan = plan.sort_values(['priority', 'clicks_window'], ascending=[True, False])
    plan.to_csv(work / 'action_plan.csv', index=False)

    actionable = plan[plan['priority'] <= 6]
    summary = {
        'site': meta.get('site', ''), 'end_date': meta.get('end_date', ''),
        'urls_analyzed': int(meta.get('urls_analyzed', len(pages))),
        'pairs_judged': pv.get('pairs_judged', 0),
        'verdict_distribution': pv.get('distribution', {}),
        'clusters_with_cannibals': len(cluster_rows),
        'actionable_pages': int(len(actionable)),
        'clicks_at_stake': int(actionable['clicks_window'].sum()),
        'weak_ongoing_not_clustered': weak_ongoing,
        'topics': len(set(topic_map.values())),
        'queries_distinct': meta.get('queries_distinct', 0),
        'brand_tokens': universe.get('brand_tokens', []),
        # The weekly series is what the ongoing/handoff detectors run on. The
        # matrix's own date column is irrelevant to them — reporting that here
        # would understate a run whose per-URL pulls were fully dated.
        'weekly_series_urls': pv.get('weekly_urls_loaded', 0),
        'weekly_series_expected': pv.get('weekly_urls_expected', 0),
        'matrix_has_date_dimension': meta.get('has_date_dimension', False),
        'urls_dropped_for_scale': len(meta.get('urls_dropped_for_scale', [])),
        'pairs_skipped_missing_weekly': len(pv.get('pairs_skipped') or []),
    }
    (work / 'plan.json').write_text(json.dumps(
        {'summary': summary, 'clusters': cluster_rows,
         'action_plan': plan.to_dict('records'), 'evidence': evidence_rows(verdicts)},
        indent=1, default=str), encoding='utf-8')

    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
