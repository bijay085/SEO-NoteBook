"""The shortlister : the cheap filter that decides which pairs are even worth
pulling weekly GSC data for. A pair that fails the shortlist is never
cannibalization.

Two tiers, exactly as the app had them:

  Tier 1 : ENTITY PEER-GROUP GATE (primary, when both pages carry a Claude
    entity assignment). Eligible iff they share a peer_group_id, or one is a hub
    covering the other's section. A cross-section pair is STRUCTURALLY blocked : 
    it cannot be a cannibal however much ambiguous-query overlap it shows. This
    is what stops a writing page being "cannibalized" by a speaking page just
    because both surface on one ambiguous term.

  Tier 2 : STATISTICAL OR-GATE (when an entity assignment is missing). Any of:
    IDF click cosine, IDF impression cosine, or topic-profile cosine clearing
    its threshold. The shared-topic-query gate applies only when the cosine path
    alone rescued the pair.

The intent gate runs in BOTH tiers : same intent is always required.

The app used a scipy sparse matrix multiply for the cosines. This uses an
inverted-index accumulation instead: identical arithmetic, no scipy, and it only
touches queries two pages actually share.

Usage:
    python shortlist.py --work <dir> [--config config.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from cannib_config import load_cfg, min_topic_idf
from judgment import intents_compatible


def cosine_pairs(urls, value_map, idf=None, max_df_fraction=1.0):
    """IDF-weighted cosine for every page pair sharing at least one query.

    Equivalent to the app's `W_norm @ W_norm.T`: with w[page][q] = idf[q]*v[q],
    the dot product over shared queries equals the dot product over all queries
    (absent queries contribute 0), so accumulating per shared query through an
    inverted index gives the same numbers without materialising the matrix.

    Returns {(i, j): cosine} for i < j. Pairs sharing no query are absent
    (cosine 0), matching the app's `dot=0 -> cos=0`.
    """
    index = {u: i for i, u in enumerate(urls)}
    postings = {}
    norms = [0.0] * len(urls)
    for u in urls:
        i = index[u]
        for q, v in (value_map.get(u) or {}).items():
            w = (idf.get(q, 0.0) if idf is not None else 1.0) * float(v)
            if w == 0.0:
                continue
            norms[i] += w * w
            postings.setdefault(q, []).append((i, w))
    norms = [math.sqrt(n) for n in norms]

    cutoff = len(urls) * max_df_fraction if max_df_fraction < 1.0 else float('inf')
    dots = {}
    for posting in postings.values():
        if len(posting) < 2 or len(posting) > cutoff:
            continue
        for a in range(len(posting)):
            ia, wa = posting[a]
            for b in range(a + 1, len(posting)):
                ib, wb = posting[b]
                key = (ia, ib) if ia < ib else (ib, ia)
                dots[key] = dots.get(key, 0.0) + wa * wb

    return {k: d / (norms[k[0]] * norms[k[1]])
            for k, d in dots.items()
            if norms[k[0]] > 0 and norms[k[1]] > 0}


def peers_eligible(a, b):
    """Cannibalization-eligible iff the two pages share a peer group, or one is a
    hub whose `covers` includes the other's section."""
    if not a or not b:
        return False
    if a.get('peer_group_id') == b.get('peer_group_id'):
        return not str(a.get('peer_group_id', '')).startswith('unresolved')
    if a.get('is_hub') and b.get('axis_1') in (a.get('covers') or []):
        return True
    if b.get('is_hub') and a.get('axis_1') in (b.get('covers') or []):
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--config', default='')
    args = ap.parse_args()

    cfg, _raw = load_cfg(args.config or None)
    work = Path(args.work)
    universe = json.loads((work / 'universe.json').read_text(encoding='utf-8'))
    entities = json.loads((work / 'entities.json').read_text(encoding='utf-8'))
    intents = json.loads((work / 'intents.json').read_text(encoding='utf-8'))

    top_queries = {u: set(qs) for u, qs in universe['top_queries'].items()}
    urls = sorted(top_queries, key=lambda u: -sum((universe['impr_map'].get(u) or {}).values()))
    idf = universe['idf']
    max_df = cfg['cosine_max_posting_df_fraction']

    click_cos = cosine_pairs(urls, universe['clicks_map'], idf, max_df)
    impr_cos = cosine_pairs(urls, universe['impr_map'], idf, max_df)
    # Topic-profile similarity: once Claude has collapsed phrasings onto topic
    # keys, a page's profile IS its distribution over topics. An unweighted
    # cosine of the impression profile answers "do these two pages cover the
    # same topic mix?" : the recall path the app bought with page embeddings.
    topic_sim = cosine_pairs(urls, universe['impr_map'], None, max_df)

    tsim_min = float(cfg['shortlist_min_topic_profile_sim'])
    cos_min = float(cfg['shortlist_min_click_cosine'])
    icos_min = float(cfg['shortlist_min_impr_cosine'])
    min_shared_topic = int(cfg['shortlist_min_shared_topic_queries'])
    idf_floor = min_topic_idf(cfg)
    require_intent = bool(cfg['shortlist_require_same_intent'])

    candidates, rejects = {}, []
    n_entity_ok = n_entity_blocked = n_legacy = 0

    for i in range(len(urls)):
        a = urls[i]
        a_ent = entities.get(a)
        for j in range(i + 1, len(urls)):
            b = urls[j]
            b_ent = entities.get(b)
            key = (i, j)
            cos = click_cos.get(key, 0.0)
            icos = impr_cos.get(key, 0.0)
            tsim = topic_sim.get(key, 0.0)
            shared = top_queries[a] & top_queries[b]

            both_have_entities = bool(a_ent and b_ent)
            if both_have_entities and not peers_eligible(a_ent, b_ent):
                # Structurally blocked: different sections, no hub coverage.
                # Not logged individually : it would flood the diagnostics.
                n_entity_blocked += 1
                continue

            if require_intent and not intents_compatible(intents.get(a, {}), intents.get(b, {})):
                rejects.append((a, b, f'intent mismatch: {intents.get(a, {}).get("intent")} '
                                      f'vs {intents.get(b, {}).get("intent")}'))
                continue

            if both_have_entities:
                # The entity grouping IS the signal. Statistical overlap gets
                # measured downstream, and the materiality / cluster-strength
                # gates filter the noise there.
                candidates[(a, b)] = {'score': max(cos, icos, tsim, 0.5), 'tier': 'entity',
                                      'cos': round(cos, 4), 'icos': round(icos, 4),
                                      'tsim': round(tsim, 4), 'shared': len(shared),
                                      'peer_group': a_ent.get('peer_group_id')}
                n_entity_ok += 1
                continue

            n_legacy += 1
            cosine_passes = cos >= cos_min or icos >= icos_min
            tsim_passes = tsim >= tsim_min
            if not (cosine_passes or tsim_passes):
                if shared:
                    rejects.append((a, b, f'statistical tier: cos={cos:.2f}<{cos_min} & '
                                          f'impr_cos={icos:.2f}<{icos_min} & '
                                          f'tsim={tsim:.2f}<{tsim_min}'))
                continue
            if cosine_passes and not tsim_passes:
                topic_bearing = [q for q in shared if idf.get(q, 0.0) >= idf_floor]
                if len(topic_bearing) < min_shared_topic:
                    rejects.append((a, b, f'shared_topic_queries={len(topic_bearing)}'
                                          f'<{min_shared_topic}'))
                    continue
            candidates[(a, b)] = {'score': max(cos, icos, tsim), 'tier': 'statistical',
                                  'cos': round(cos, 4), 'icos': round(icos, 4),
                                  'tsim': round(tsim, 4), 'shared': len(shared),
                                  'peer_group': ''}

    # Cap pairs per URL to bound the weekly-pull cost : but ALWAYS keep a pair
    # whose signal cleared the strong threshold. The app learned this the hard
    # way: a plain top-N cap silently dropped low-cosine-but-high-tsim pairs
    # because they ranked below high-cosine peers on a niche site.
    cap = int(cfg.get('shortlist_max_pairs_per_url') or 0)
    capped = 0
    if cap > 0:
        keep = {p for p, m in candidates.items() if m['score'] >= tsim_min}
        by_url = {}
        for pair, m in candidates.items():
            if m['score'] >= tsim_min:
                continue
            for u in pair:
                by_url.setdefault(u, []).append((pair, m['score']))
        for pairs in by_url.values():
            pairs.sort(key=lambda x: -x[1])
            keep.update(p for p, _ in pairs[:cap])
        before = len(candidates)
        candidates = {p: m for p, m in candidates.items() if p in keep}
        capped = before - len(candidates)

    shortlisted_urls = sorted({u for pair in candidates for u in pair})
    out = {
        'pairs': [{'a': a, 'b': b, **m} for (a, b), m in
                  sorted(candidates.items(), key=lambda kv: -kv[1]['score'])],
        'shortlisted_urls': shortlisted_urls,
        'stats': {
            'urls': len(urls),
            'possible_pairs': len(urls) * (len(urls) - 1) // 2,
            'candidates': len(candidates),
            'entity_eligible': n_entity_ok,
            'entity_cross_section_blocked': n_entity_blocked,
            'statistical_tier': n_legacy,
            'rejected_logged': len(rejects),
            'dropped_by_cap': capped,
        },
    }
    (work / 'candidates.json').write_text(json.dumps(out, indent=1), encoding='utf-8')

    with (work / 'rejects.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['url_a', 'url_b', 'reason'])
        w.writerows(rejects)

    print(json.dumps(out['stats'], indent=1))
    print(f'{len(shortlisted_urls)} URLs need a weekly (date x query) GSC pull.')


if __name__ == '__main__':
    main()
