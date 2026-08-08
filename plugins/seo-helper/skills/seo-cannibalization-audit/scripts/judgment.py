"""The Claude-judgment bridge — this is what replaces the third-party AI.

The original app sent four things to Gemini: query embeddings for topic
clustering, an LLM pass to split over-merged clusters, per-URL intent
classification, and a two-axis page taxonomy. All four are semantic judgments,
which is exactly what Claude is already in the room to do. So instead of an
embedding API plus a threshold that has to be auto-calibrated per corpus, this
module:

  `prepare` — does the deterministic, mechanical part (brand normalisation,
              rare-token blocking, rule-based intent priors, page context
              assembly) and writes small, reviewable judgment packets.
  `apply`   — validates Claude's answers, merges them with the deterministic
              fallbacks, and writes the maps the pipeline consumes.

Everything degrades: if a judgment file is absent, `apply` falls back to
exact-string query matching and rule-based intent, and records that in the
manifest. Same graceful-degradation contract the app had when GEMINI_API_KEY was
unset.

Usage:
    python judgment.py prepare --work <dir> [--config config.json]
    python judgment.py apply   --work <dir> [--config config.json]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from cannib_config import load_cfg

STOP = {
    'the', 'a', 'an', 'of', 'for', 'to', 'in', 'on', 'and', 'or', 'is', 'are',
    'with', 'my', 'your', 'best', 'top', 'free', 'online', 'near', 'me', 'how',
    'what', 'why', 'when', 'where', 'who', 'can', 'do', 'does', 'vs',
}

# ---------------------------------------------------------------------------
# Rule-based intent — the deterministic prior Claude confirms or overrides
# ---------------------------------------------------------------------------

URL_PATTERNS = [
    ('transactional', re.compile(r'/(shop|store|product|products|buy|checkout|cart|pricing|plans|order)(/|$)', re.I)),
    ('news',          re.compile(r'/(news|press|press-release)/', re.I)),
    ('informational', re.compile(r'/(blog|guide|guides|tutorial|tutorials|docs?|documentation|learn|resources?|knowledge-base|kb|wiki|glossary|how-to)(/|$)', re.I)),
    ('informational', re.compile(r'/(what-is|how-to)-', re.I)),
    ('commercial',    re.compile(r'/(best|top|review|reviews|compare|comparison|vs|versus)[-/]', re.I)),
    ('commercial',    re.compile(r'-(vs|versus|review|comparison)-', re.I)),
    ('navigational',  re.compile(r'/(about|contact|team|careers?|jobs?|privacy|terms|tos|legal|login|signin|signup|register)(/|$)', re.I)),
    # A /YYYY/MM/DD/ permalink is WordPress URL structure, not "news" — a blog
    # running date permalinks puts evergreen guides at these URLs too. Last, so
    # an explicit /shop/ or /best-… slug above still wins.
    ('informational', re.compile(r'/20\d{2}/\d{1,2}/\d{1,2}/[a-z0-9]', re.I)),
]

TOKEN_SETS = {
    'transactional': {'buy', 'price', 'pricing', 'cost', 'cheap', 'discount', 'deal',
                      'coupon', 'shop', 'order', 'subscribe', 'signup', 'plans', 'trial', 'demo'},
    'informational': {'how', 'what', 'why', 'when', 'where', 'who', 'guide', 'tutorial',
                      'explained', 'definition', 'meaning', 'examples', 'tips', 'steps',
                      'learn', 'introduction', 'beginners'},
    'commercial': {'best', 'top', 'review', 'reviews', 'vs', 'versus', 'comparison',
                   'alternative', 'alternatives', 'rating', 'ratings'},
    'news': {'news', 'today', 'latest', 'breaking', 'update', 'updates',
             'announcement', 'announces'},
}

VALID_INTENTS = {'transactional', 'commercial', 'informational', 'navigational',
                 'news', 'unknown'}


def rule_intent(url, queries=()):
    path = (urlparse(url).path or '/').lower()
    if path in ('/', ''):
        return {'intent': 'navigational', 'confidence': 'high', 'evidence': 'url-path:root'}
    for cls, pat in URL_PATTERNS:
        if pat.search(path):
            return {'intent': cls, 'confidence': 'high', 'evidence': f'url-path:{cls}'}
    scores = {k: 0 for k in TOKEN_SETS}
    n = 0
    for q in queries:
        toks = set(re.findall(r'[a-z0-9]+', str(q).lower()))
        if not toks:
            continue
        n += 1
        for cls, vocab in TOKEN_SETS.items():
            if toks & vocab:
                scores[cls] += 1
    if n:
        cls, top = max(scores.items(), key=lambda kv: kv[1])
        if top:
            share = top / n
            conf = 'high' if share >= 0.4 else 'med' if share >= 0.2 else 'low'
            if conf in ('high', 'med'):
                return {'intent': cls, 'confidence': conf, 'evidence': f'query-tokens:{cls}'}
    return {'intent': 'unknown', 'confidence': 'none', 'evidence': 'no-match'}


def intents_compatible(a, b):
    """Can these two intents cannibalize each other at all?
    Different non-unknown intents never can. `unknown` pairs with anything —
    dropping a real pair on a weak signal is the more expensive error."""
    a = a.get('intent') if isinstance(a, dict) else a
    b = b.get('intent') if isinstance(b, dict) else b
    if a == 'unknown' or b == 'unknown' or not a or not b:
        return True
    # A stale evergreen article and a fresh news piece on one topic DO compete.
    if {a, b} == {'news', 'informational'}:
        return True
    # "best X" / "X review" queries straddle these two.
    if {a, b} == {'commercial', 'informational'}:
        return True
    return a == b


# ---------------------------------------------------------------------------
# Query blocking — deterministic recall, Claude supplies the precision
# ---------------------------------------------------------------------------


def _content_tokens(q):
    return [t for t in re.findall(r'[a-z0-9]+', str(q).lower())
            if t not in STOP and len(t) > 1]


def block_queries(queries, max_block=60):
    """Union queries that share a *distinctive* token into candidate blocks.

    Pure recall: a block says "these might be phrasings of one search". Claude
    then partitions each block into actual topics — the step that previously
    needed an embedding model plus a second LLM pass to undo its over-merging.
    Ubiquitous tokens are skipped so one common word can't fuse the whole
    corpus into a single block.
    """
    parent = {q: q for q in queries}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    tok_index = {}
    for q in queries:
        for t in _content_tokens(q):
            tok_index.setdefault(t, []).append(q)

    # A token on more than 40% of the corpus's queries is a connector word for
    # this site, not a topic marker — skip it.
    ubiquitous = max(3, int(len(queries) * 0.40))
    for qs in tok_index.values():
        if len(qs) > ubiquitous:
            continue
        for other in qs[1:]:
            union(qs[0], other)

    blocks = {}
    for q in queries:
        blocks.setdefault(find(q), []).append(q)

    out = []
    for members in blocks.values():
        if len(members) <= 1:
            continue                      # a lone query needs no adjudication
        members = sorted(members)
        for i in range(0, len(members), max_block):
            out.append(members[i:i + max_block])
    return out


# ---------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------


def cmd_prepare(args):
    cfg, _raw = load_cfg(args.config or None)
    work = Path(args.work)
    jdir = work / 'judgment'
    jdir.mkdir(parents=True, exist_ok=True)

    universe = json.loads((work / 'universe.json').read_text(encoding='utf-8'))
    pages = pd.read_csv(work / 'pages.csv')
    top_click_qs = universe['top_click_qs']
    impr_map = universe['impr_map']
    df_count = universe['df_count']

    # --- 1. Topic blocks -------------------------------------------------
    q_impressions = {}
    for page_map in impr_map.values():
        for q, impr in page_map.items():
            q_impressions[q] = q_impressions.get(q, 0.0) + float(impr)
    ranked = sorted(q_impressions, key=lambda q: -q_impressions[q])
    # Bound the judgment to the head by impressions. The tail keeps its exact
    # string — the safe fallback — and cannot produce a verdict anyway, since
    # the ongoing gates need >=15 combined clicks on a qualifying query.
    cap = int(cfg.get('topic_judgment_max_queries') or 0)
    judged = ranked[:cap] if cap else ranked
    unjudged = len(ranked) - len(judged)
    blocks = block_queries(judged)
    topic_task = {
        'scope': {'queries_judged': len(judged), 'queries_unjudged': unjudged,
                  'basis': 'top by impressions; the rest keep exact-string matching'},
        'instruction': ('Partition each block into TOPICS. Two queries belong to the same '
                        'topic only when a searcher typing either one wants the SAME page. '
                        'Different phrasings of one search = same topic. Genuinely '
                        'different sub-topics ("part 1" vs "part 2", "reading" vs '
                        '"writing") = separate topics, even when the wording is close. '
                        'Under-merging is safe; over-merging causes destructive 301s. '
                        'Omit any query you are unsure about — it keeps its own string.'),
        'answer_schema': {'blocks': [{'block_id': 0,
                                      'topics': [{'topic': 'canonical label',
                                                  'queries': ['...']}]}]},
        'blocks': [{'block_id': i,
                    'queries': [{'q': q, 'pages': df_count.get(q, 0),
                                 'impressions': int(q_impressions.get(q, 0))} for q in b]}
                   for i, b in enumerate(blocks)],
    }
    (jdir / '01_topics.task.json').write_text(json.dumps(topic_task, indent=1), encoding='utf-8')

    # --- 2. Page entity taxonomy + 3. intent -----------------------------
    batch = int(cfg.get('entity_batch_size', 30))
    page_items = []
    for _, r in pages.iterrows():
        url = r['page']
        qs = list(top_click_qs.get(url, []))[:12]
        if not qs:
            qs = sorted(impr_map.get(url, {}), key=lambda q: -impr_map[url][q])[:12]
        page_items.append({
            'url': url,
            'slug': urlparse(url).path,
            'top_queries': qs,
            'clicks': int(r['clicks_window']),
            'impressions': int(r['impressions_window']),
            'rule_intent': rule_intent(url, qs),
        })
    batches = [page_items[i:i + batch] for i in range(0, len(page_items), batch)]

    (jdir / '02_entities.task.json').write_text(json.dumps({
        'instruction': (
            'Assign every page a TWO-AXIS taxonomy inferred from THIS corpus only — never '
            'category names from prior knowledge. axis_1 = the top-level section the page '
            'belongs to. axis_2 = the content angle within that section. Two pages are '
            'cannibalization-eligible IF AND ONLY IF they share BOTH axes. Set '
            'is_hub=true (and list the axis_1 values it covers) for a page that genuinely '
            'spans several sections, e.g. a top-level overview. Get the granularity right: '
            'too coarse merges unrelated pages, too fine lets real duplicates escape.'),
        'answer_schema': {'pages': [{'url': '...', 'axis_1': 'snake_case', 'axis_2': 'snake_case',
                                     'is_hub': False, 'covers': [], 'confidence': 0.0}]},
        'batches': batches,
    }, indent=1), encoding='utf-8')

    (jdir / '03_intent.task.json').write_text(json.dumps({
        'instruction': (
            'Classify each page by SEARCH INTENT. Two pages only cannibalize when they '
            'serve the SAME intent, so this decides which pairs are even compared. '
            'Classes: transactional (buy/pricing/sign-up/product), commercial ("best X", '
            '"X vs Y", reviews), informational (how-to, guide, explainer, practice '
            'material, templates), navigational (homepage/about/contact/login), news '
            '(time-sensitive), unknown (genuinely cannot tell). `rule_intent` is a '
            'URL-pattern prior — keep it unless the queries clearly contradict it.'),
        'answer_schema': {'pages': [{'url': '...', 'intent': 'one of the six',
                                     'confidence': 'high|med|low'}]},
        'batches': batches,
    }, indent=1), encoding='utf-8')

    print(f'topic blocks: {len(blocks)} (from {len(ranked)} normalised queries)')
    print(f'page batches: {len(batches)} x {batch} for entities and intent')
    print(f'wrote {jdir}/01_topics.task.json, 02_entities.task.json, 03_intent.task.json')
    print('Read each .task.json, reason, write the matching *.answer.json beside it, then:')
    print(f'  python judgment.py apply --work {work}')


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------


def _read_answer(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise SystemExit(f'{path}: invalid JSON ({e})')


def _snake(s):
    return re.sub(r'[^a-z0-9_]+', '_', str(s).strip().lower()).strip('_')


def cmd_apply(args):
    cfg, _raw = load_cfg(args.config or None)
    work = Path(args.work)
    jdir = work / 'judgment'
    universe = json.loads((work / 'universe.json').read_text(encoding='utf-8'))
    pages = pd.read_csv(work / 'pages.csv')
    all_urls = list(pages['page'])
    manifest = {}

    # --- topics ----------------------------------------------------------
    q_to_topic = {}
    ans = _read_answer(jdir / '01_topics.answer.json')
    if ans:
        known = set(universe['idf'])
        unknown = []
        for block in ans.get('blocks', []):
            for topic in block.get('topics', []):
                label = str(topic.get('topic', '')).strip().lower()
                members = [str(q).strip().lower() for q in topic.get('queries', [])]
                if not label or len(members) < 2:
                    continue          # a single-member topic changes nothing
                for q in members:
                    (q_to_topic.__setitem__(q, label) if q in known else unknown.append(q))
        manifest['topics'] = {'source': 'claude', 'queries_mapped': len(q_to_topic),
                              'topics': len(set(q_to_topic.values())),
                              'unrecognised_queries': len(unknown)}
        if unknown:
            print(f'WARNING: {len(unknown)} judged queries are not in the universe '
                  f'(paraphrased or re-cased?) — ignored. e.g. {unknown[:3]}')
    else:
        manifest['topics'] = {'source': 'fallback: exact-string matching',
                              'queries_mapped': 0, 'topics': 0}
        print('no 01_topics.answer.json — falling back to exact-string query matching '
              '(different phrasings of one search will not be paired)')
    (work / 'topic_map.json').write_text(json.dumps(q_to_topic, indent=1), encoding='utf-8')

    # Rebuild the universe on topic keys so the shortlister and detectors see
    # phrasings collapsed onto one key.
    if q_to_topic:
        from gsc_normalize import build_universe
        matrix = pd.read_csv(work / 'matrix.csv')
        universe = build_universe(matrix, universe['brand_tokens'], q_to_topic)
        (work / 'universe.json').write_text(json.dumps(universe, indent=1), encoding='utf-8')

    # --- entities --------------------------------------------------------
    entities = {}
    ans = _read_answer(jdir / '02_entities.answer.json')
    if ans:
        min_conf = float(cfg.get('entity_min_confidence', 0.7))
        low_conf = 0
        for rec in ans.get('pages', []):
            url = rec.get('url')
            a1, a2 = _snake(rec.get('axis_1', '')), _snake(rec.get('axis_2', ''))
            if not url or not a1 or not a2:
                continue
            conf = float(rec.get('confidence') or 0.0)
            if conf and conf < min_conf:
                low_conf += 1
            entities[url] = {
                'axis_1': a1, 'axis_2': a2, 'peer_group_id': f'{a1}.{a2}',
                'is_hub': bool(rec.get('is_hub')),
                'covers': [_snake(c) for c in (rec.get('covers') or [])],
                'confidence': conf,
            }
        missing = [u for u in all_urls if u not in entities]
        manifest['entities'] = {'source': 'claude', 'assigned': len(entities),
                                'unassigned': len(missing), 'below_confidence': low_conf}
        if missing:
            print(f'NOTE: {len(missing)} pages have no entity assignment — those pairs fall '
                  f'through to the statistical shortlist tier.')
    else:
        manifest['entities'] = {'source': 'absent — statistical shortlist tier only',
                                'assigned': 0, 'unassigned': len(all_urls)}
        print('no 02_entities.answer.json — the peer-group gate is off; the shortlist runs '
              'on the statistical tier alone (more candidate pairs, more noise)')
    (work / 'entities.json').write_text(json.dumps(entities, indent=1), encoding='utf-8')

    # --- intent ----------------------------------------------------------
    top_click_qs = universe['top_click_qs']
    intents = {u: rule_intent(u, top_click_qs.get(u, [])) for u in all_urls}
    overridden = 0
    ans = _read_answer(jdir / '03_intent.answer.json')
    if ans:
        for rec in ans.get('pages', []):
            url = rec.get('url')
            cls = str(rec.get('intent', '')).strip().lower()
            if url in intents and cls in VALID_INTENTS:
                if cls != intents[url]['intent']:
                    overridden += 1
                conf = str(rec.get('confidence', 'med')).lower()
                intents[url] = {'intent': cls,
                                'confidence': conf if conf in ('high', 'med', 'low') else 'med',
                                'evidence': 'claude'}
        manifest['intent'] = {'source': 'claude (rule-based prior)', 'pages': len(intents),
                              'overrode_rule': overridden}
    else:
        manifest['intent'] = {'source': 'rule-based only', 'pages': len(intents),
                              'overrode_rule': 0}
        print('no 03_intent.answer.json — using the rule-based classifier alone')
    (work / 'intents.json').write_text(json.dumps(intents, indent=1), encoding='utf-8')

    (work / 'judgment_manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    print(json.dumps(manifest, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('prepare', 'apply'):
        s = sub.add_parser(name)
        s.add_argument('--work', required=True)
        s.add_argument('--config', default='')
    args = ap.parse_args()
    (cmd_prepare if args.cmd == 'prepare' else cmd_apply)(args)


if __name__ == '__main__':
    main()
