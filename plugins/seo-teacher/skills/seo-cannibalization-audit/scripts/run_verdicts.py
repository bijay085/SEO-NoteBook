"""The decision cascade — one verdict per shortlisted pair.

Precedence (first tier that fires wins), exactly as the app ordered it:

    duplicate -> affected_handoff -> ongoing -> [differentiate guard]
      -> redundant_duplicate -> overlap_watch -> not_cannibal

The differentiate guard is the safety net that matters most: a page earning
>= distinct_page_unique_share of its clicks on queries the other page does not
rank for is a DISTINCT page. It blocks duplicate / ongoing / redundant from
auto-merging it, because a blanket 301 there destroys real traffic. The guard
runs on raw GSC demand, so it is independent of the topic judgment.

Run it twice:
  1st run — writes weekly/_fetch_list.json (which URLs need a date x query pull)
            and judgment/04_duplicates.task.json (boundary pairs for Claude).
  2nd run — with the weekly dumps (and optionally Claude's duplicate answers)
            in place, produces pair_verdicts.json.

Usage:
    python run_verdicts.py --work <dir> [--config config.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

import detectors as D
from cannib_config import load_cfg
from gsc_normalize import load_rows, normalize_brand_query, unique_click_share, url_twin
from judgment import intents_compatible


def weekly_filename(url):
    """Stable per-URL filename — URLs are too long and slash-heavy to use raw."""
    return hashlib.sha1(url.encode('utf-8')).hexdigest()[:16] + '.json'


def load_weekly(path, brand_tokens, q_to_topic):
    """One URL's (date, query) dump -> {topic_key: weekly DataFrame}.

    Queries are brand-normalised and topic-mapped with the SAME transform the
    universe used, or the keys would not line up with the shared-query set.
    """
    df = load_rows(path)
    if df.empty:
        return {}
    if 'date' not in df.columns or 'query' not in df.columns:
        return {}
    for c in ('clicks', 'impressions', 'position'):
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df[df['date'].notna()].copy()
    df['query'] = df['query'].map(lambda q: normalize_brand_query(q, brand_tokens))
    df = df[df['query'] != '']
    if q_to_topic:
        df['query'] = df['query'].map(lambda q: q_to_topic.get(q, q))
    return D.to_weekly_per_query(df)


def assess_duplicate(content_sim, twin, tsim, cfg):
    """Duplicate fast lane. Two pages are duplicates when either their page
    context is near-identical, or their URLs are near-twins on the same topic
    and the context does not actively say they are differentiated.

    The twin path needs that loose content corroboration because without it
    `/reading-practice-test/` and `/reading-practice-tests-3/` both scored
    duplicate-High — a Part 3 page with different content should never be
    auto-merged into Part 1 just because the slug differs by "-3".
    """
    c = content_sim if content_sim is not None else -1.0
    t = tsim if tsim is not None else -1.0
    content_hit = c >= cfg['dup_content_min']
    twin_hit = (bool(twin) and t >= cfg['dup_twin_topic_min']
                and (c < 0 or c >= cfg['dup_twin_content_min']))   # c < 0 = no signal, allowed
    if not (content_hit or twin_hit):
        return None
    reason = ((f'near-identical page context (similarity {c:.2f}) — the same page duplicated')
              if content_hit else
              (f'near-twin URLs on the same topic (topic-profile similarity {t:.2f}, '
               f'context similarity {c:.2f}) — a duplicate page'))
    return {'verdict': 'duplicate', 'reason': reason, 'confidence': 'High'}


def classify_pair(a, b, weekly_a, weekly_b, shared, appearance, intents, cfg, end_date,
                  content_sim, tsim, twin, ushare_a, ushare_b):
    base = {'url_a': a, 'url_b': b, 'shared_queries_count': len(shared),
            'content_sim': content_sim,
            'topic_profile_sim': round(tsim, 3) if tsim is not None else None,
            'url_twin': bool(twin),
            'unique_click_share_a': round(ushare_a, 3) if ushare_a is not None else None,
            'unique_click_share_b': round(ushare_b, 3) if ushare_b is not None else None}

    if not intents_compatible(intents.get(a, {}), intents.get(b, {})):
        return {**base, 'verdict': 'not_cannibal', 'confidence': '',
                'reason': f'intent mismatch: {intents.get(a, {}).get("intent")} vs '
                          f'{intents.get(b, {}).get("intent")}',
                'ongoing': None, 'handoff': None, 'serp_attribution': None, 'leakage': None}

    floor = cfg['distinct_page_unique_share']
    distinct = max(ushare_a or 0.0, ushare_b or 0.0) >= floor

    # --- tier 0: duplicate fast lane ---
    dup = assess_duplicate(content_sim, twin, tsim, cfg)
    if dup and not distinct:
        return {**base, **dup, 'ongoing': None, 'handoff': None,
                'serp_attribution': None, 'leakage': None}

    # SERP-feature attribution is COMPUTED here but only applied once parity or
    # handoff evidence exists. Applying it first killed real cannibals whose
    # shared queries were both plain organic but which happened to win a PAA or
    # video slot on unrelated terms.
    attr = None
    if cfg['serp_attribution_enabled'] and appearance:
        attr = D.serp_attribution_filter(a, b, appearance, cfg)

    ongoing = D.detect_ongoing(weekly_a, weekly_b, shared, cfg, end_date)
    handoff = D.detect_handoff(weekly_a, weekly_b, shared, cfg)
    base = {**base, 'ongoing': ongoing, 'handoff': handoff, 'serp_attribution': attr}

    if attr is not None and not attr['same_surface'] and (ongoing['verdict'] or handoff['verdict']):
        return {**base, 'verdict': 'not_cannibal', 'confidence': '',
                'reason': f'parity evidence present but {attr["reason"]}', 'leakage': None}

    handoff_winner = handoff_loser = None
    leakage = None
    if handoff['verdict']:
        if handoff['direction'] == 'a_to_b':
            handoff_loser, handoff_winner = a, b
            leakage = D.quantify_leakage(weekly_a, weekly_b, handoff['handoff_date'], end_date, cfg)
        else:
            handoff_loser, handoff_winner = b, a
            leakage = D.quantify_leakage(weekly_b, weekly_a, handoff['handoff_date'], end_date, cfg)
    base = {**base, 'handoff_winner': handoff_winner, 'handoff_loser': handoff_loser}

    def differentiate(tier):
        side = a if (ushare_a or 0) >= (ushare_b or 0) else b
        share = max(ushare_a or 0.0, ushare_b or 0.0)
        return {**base, 'verdict': 'differentiate', 'confidence': 'Medium', 'leakage': leakage,
                'distinct_page': side,
                'reason': (f'would have been "{tier}", but {side} earns {share * 100:.0f}% of its '
                           f'clicks on searches the other page does not rank for (floor '
                           f'{floor * 100:.0f}%) — a distinct page, not a duplicate. A blanket '
                           f'301 would destroy that traffic.')}

    if handoff['verdict']:
        # A completed handoff is history, not a merge decision — the guard does
        # not apply, because the loser has already lost the queries.
        return {**base, 'verdict': 'affected_handoff', 'confidence': 'High', 'leakage': leakage,
                'reason': f'handoff detected on {len(handoff["qualifying_queries"])} shared '
                          f'queries; direction={handoff["direction"]}'}

    if ongoing['verdict']:
        return differentiate('ongoing cannibal') if distinct else {
            **base, 'verdict': 'ongoing', 'confidence': 'High', 'leakage': None,
            'reason': f'{len(ongoing["qualifying_queries"])} shared queries pass all parity gates'}

    if dup and distinct:
        return differentiate('duplicate')

    redundant = D.assess_redundant(ongoing, cfg)
    if redundant['verdict']:
        return differentiate('redundant duplicate') if distinct else {
            **base, 'verdict': 'redundant_duplicate', 'confidence': 'Medium', 'leakage': None,
            'reason': redundant['reason'], 'redundant_side': redundant['weak_side'],
            'redundant_shared_count': redundant['shared_count'],
            'redundant_median_pos': redundant['median_pos']}

    ts = tsim if tsim is not None else -1.0
    cs = content_sim if content_sim is not None else -1.0
    if (len(shared) >= cfg['overlap_watch_min_shared']
            and (ts >= cfg['overlap_watch_topic_min'] or cs >= cfg['overlap_watch_content_min'])):
        return {**base, 'verdict': 'overlap_watch', 'confidence': 'Low', 'leakage': None,
                'reason': (f'pages cover the same topic (topic similarity {ts:.2f}, context '
                           f'{cs:.2f}, {len(shared)} shared topics) but no live click split or '
                           f'handoff yet — monitor')}

    return {**base, 'verdict': 'not_cannibal', 'confidence': '', 'leakage': None,
            'reason': 'no parity now and no handoff in history'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--config', default='')
    args = ap.parse_args()

    cfg, _raw = load_cfg(args.config or None)
    work = Path(args.work)
    weekly_dir = work / 'weekly'
    weekly_dir.mkdir(parents=True, exist_ok=True)
    jdir = work / 'judgment'
    jdir.mkdir(parents=True, exist_ok=True)

    cand = json.loads((work / 'candidates.json').read_text(encoding='utf-8'))
    universe = json.loads((work / 'universe.json').read_text(encoding='utf-8'))
    intents = json.loads((work / 'intents.json').read_text(encoding='utf-8'))
    appearance = json.loads((work / 'appearance.json').read_text(encoding='utf-8'))
    meta = json.loads((work / 'meta.json').read_text(encoding='utf-8'))
    q_to_topic = json.loads((work / 'topic_map.json').read_text(encoding='utf-8'))
    brand_tokens = universe['brand_tokens']
    end_date = pd.Timestamp(meta['end_date'])

    # --- fetch list ------------------------------------------------------
    fetch_list = {u: weekly_filename(u) for u in cand['shortlisted_urls']}
    (weekly_dir / '_fetch_list.json').write_text(json.dumps(fetch_list, indent=1), encoding='utf-8')
    have = {u: f for u, f in fetch_list.items() if (weekly_dir / f).exists()}
    missing = [u for u in fetch_list if u not in have]

    # --- duplicate-boundary judgment packet ------------------------------
    top_click_qs = universe['top_click_qs']
    boundary = []
    for p in cand['pairs']:
        a, b, tsim = p['a'], p['b'], p.get('tsim') or 0.0
        if url_twin(a, b) or tsim >= cfg['dup_twin_topic_min']:
            boundary.append({
                'pair_id': f'{a}||{b}',
                'a': {'url': a, 'slug': urlparse(a).path,
                      'top_queries': top_click_qs.get(a, [])[:8]},
                'b': {'url': b, 'slug': urlparse(b).path,
                      'top_queries': top_click_qs.get(b, [])[:8]},
                'url_twin': url_twin(a, b), 'topic_profile_sim': round(tsim, 3),
            })
    (jdir / '04_duplicates.task.json').write_text(json.dumps({
        'instruction': (
            'For each pair, judge how much the two pages are THE SAME PAGE, from slug and top '
            'queries (fetch the live pages for title/H1/meta if you can — state whether you '
            'did). Return content_sim 0.0-1.0: 0.95+ = the same page duplicated; 0.80-0.93 = '
            'same topic, genuinely different page; below 0.60 = clearly differentiated. '
            f'>= {cfg["dup_content_min"]} triggers an immediate 301 recommendation, so be '
            'strict — a wrong duplicate call destroys a real page.'),
        'answer_schema': {'pairs': [{'pair_id': 'a||b', 'content_sim': 0.0, 'why': '...'}]},
        'pairs': boundary,
    }, indent=1), encoding='utf-8')

    if missing:
        print(f'{len(missing)} of {len(fetch_list)} shortlisted URLs have no weekly dump yet.')
        print(f'Fetch (date, query) per URL and save each to {weekly_dir}/<filename> using the '
              f'url -> filename map in {weekly_dir}/_fetch_list.json, then re-run.')
        print(f'Also written: {jdir}/04_duplicates.task.json ({len(boundary)} boundary pairs).')
        if not have:
            return

    # --- duplicate answers (optional) ------------------------------------
    dup_sim = {}
    dup_answer = jdir / '04_duplicates.answer.json'
    if dup_answer.exists():
        for rec in json.loads(dup_answer.read_text(encoding='utf-8')).get('pairs', []):
            try:
                dup_sim[rec['pair_id']] = float(rec['content_sim'])
            except (KeyError, TypeError, ValueError):
                continue

    # --- weekly series ---------------------------------------------------
    weekly = {u: load_weekly(weekly_dir / f, brand_tokens, q_to_topic) for u, f in have.items()}
    page_query_clicks = universe['clicks_map']
    page_ranks_for = {u: set(qs) for u, qs in universe['top_queries'].items()}

    verdicts, skipped = [], []
    for p in cand['pairs']:
        a, b = p['a'], p['b']
        if a not in weekly or b not in weekly:
            skipped.append({'a': a, 'b': b, 'reason': 'weekly dump missing for one or both URLs'})
            continue
        shared = sorted(set(weekly[a]) & set(weekly[b]))
        if not shared:
            shared = sorted(page_ranks_for.get(a, set()) & page_ranks_for.get(b, set()))
        v = classify_pair(
            a, b, weekly[a], weekly[b], shared, appearance, intents, cfg, end_date,
            content_sim=dup_sim.get(f'{a}||{b}', dup_sim.get(f'{b}||{a}')),
            tsim=p.get('tsim'), twin=url_twin(a, b),
            ushare_a=unique_click_share(a, b, page_query_clicks, page_ranks_for),
            ushare_b=unique_click_share(b, a, page_query_clicks, page_ranks_for),
        )
        v['shortlist'] = {k: p[k] for k in ('score', 'tier', 'cos', 'icos', 'tsim', 'peer_group')
                          if k in p}
        verdicts.append(v)

    dist = {}
    for v in verdicts:
        dist[v['verdict']] = dist.get(v['verdict'], 0) + 1

    (work / 'pair_verdicts.json').write_text(json.dumps({
        'end_date': meta['end_date'],
        'distribution': dist,
        'pairs_judged': len(verdicts),
        # How many URLs actually had a weekly (date x query) series. This — not
        # the matrix's date column — is what decides whether the ongoing and
        # handoff detectors could run.
        'weekly_urls_loaded': len(have),
        'weekly_urls_expected': len(fetch_list),
        'pairs_skipped': skipped,
        'duplicate_judgments_used': len(dup_sim),
        'verdicts': verdicts,
    }, indent=1, default=str), encoding='utf-8')

    print(json.dumps(dist, indent=1))
    if skipped:
        print(f'WARNING: {len(skipped)} pairs skipped for missing weekly data.')
    if not dup_sim and boundary:
        print(f'NOTE: no 04_duplicates.answer.json — {len(boundary)} boundary pairs were judged '
              f'without a page-context signal (URL-twin path only).')


if __name__ == '__main__':
    main()
