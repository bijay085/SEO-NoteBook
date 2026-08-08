"""Thresholds for the cannibalization cascade.

Ported from the Cannibalization Analysis app's `app/config.py`. Every knob that
governed a verdict is kept at its calibrated value; the knobs that only existed
to bound third-party API cost (embedding batches, SerpAPI caps, Gemini models)
are gone : Claude does that reasoning in-session at no metered cost.

Override any value from the run config's `"thresholds"` block. Nothing here is
site-specific; the skill is industry-agnostic.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

DEFAULT_CFG = {
    # ---------- Data window ----------
    'months_back': 16, # GSC hard limit
    'recent_window_days': 90, # "right now" : the ongoing detector's window
    'long_window_months': 16, # full window : the handoff detector's window
    'trend_weeks': 26,

    # ---------- URL filtering ----------
    'include_urls': [],
    'exclude_url_patterns': ['/tag/', '/category/', '/product-tag/', '/product-category/'],
    'query_tail_min_impressions': 10,
    'max_urls': 400, # bound the run; top-N by impressions. See SKILL.md §Scale.

    # ---------- Brand handling ----------
    # Brand terms are NORMALISED, not dropped: "acme celpip mock test" -> "celpip
    # mock test" so branded and non-branded variants of one topic merge. Only a
    # query that is *nothing but* brand is dropped.
    'brand_tokens': [], # auto-detected from the domain when empty
    'idf_topic_max_df_fraction': 0.30, # a query on >30% of pages is not topic-bearing

    # ---------- Query-demand guard (the anti-destructive-301 safety net) ----------
    # A page earning >= this share of its clicks on queries the other page does
    # NOT rank for is a DISTINCT page. Gates duplicate / ongoing-redirect /
    # redundant verdicts -> `differentiate` instead. Runs on raw GSC demand, so
    # it is independent of topic clustering.
    'distinct_page_unique_share': 0.60,

    # ---------- Duplicate fast lane + overlap watch ----------
    # `content_sim` here is Claude's page-context similarity judgment (slug +
    # title + h1 + meta description) expressed 0-1, or the deterministic lexical
    # fallback when no judgment was supplied.
    'dup_content_min': 0.94, # near-identical context -> duplicate
    'dup_twin_topic_min': 0.88, # near-twin URL + this topic-profile cosine -> duplicate
    'dup_twin_content_min': 0.50, # twin path veto: below this, the pages are differentiated
    'overlap_watch_topic_min': 0.80,
    'overlap_watch_content_min': 0.78,
    'overlap_watch_min_shared': 2,

    # ---------- Shortlister (cheap candidate filter) ----------
    # Pairs that fail the shortlist are NEVER cannibalization.
    'shortlist_min_click_cosine': 0.30,
    'shortlist_min_impr_cosine': 0.40, # OR'd with clicks so a buried page still reaches the detector
    'shortlist_min_topic_profile_sim': 0.85,
    'shortlist_min_shared_topic_queries': 1, # applied only when ONLY the cosine path fires
    'shortlist_max_pairs_per_url': 12,
    'shortlist_require_same_intent': True,
    # Performance guard only. At 1.0 the cosine is exact. Lowering it skips
    # queries that appear on more than this fraction of pages when accumulating
    # dot products : cheaper on very large corpora, but it CHANGES the cosine,
    # so only lower it if a run is genuinely too slow.
    'cosine_max_posting_df_fraction': 1.0,

    # ---------- Topic judgment scope ----------
    # Only the top-N normalised queries by impressions go out for topic
    # grouping. The tail keeps its exact string, which is the safe fallback
    # (under-merging never causes a bad 301) and cannot produce a verdict
    # anyway : the ongoing materiality gates need >=15 combined clicks on a
    # query. Raise it when you can afford a longer judgment pass; the number
    # left unjudged is always reported.
    'topic_judgment_max_queries': 1000,

    # ---------- Entity peer-group gate (Claude-assigned, replaces the LLM family classifier) ----------
    'entity_grouping_enabled': True,
    'entity_batch_size': 30,
    'entity_min_confidence': 0.7,

    # ---------- ONGOING-CASE parity gates ----------
    'ongoing_min_click_parity': 0.40,
    'ongoing_min_impr_parity': 0.40,
    'ongoing_max_position_delta': 5.0,
    'ongoing_max_position_abs': 10.0,
    'ongoing_min_simultaneity_pct': 0.50,
    'ongoing_min_qualifying_queries': 1,
    'ongoing_min_query_total_clicks': 15, # materiality: combined clicks on a qualifying query
    'ongoing_min_query_clicks_each_side': 3, # materiality: stops 14-vs-1 passing the symmetric ratio
    'cluster_min_clicks_for_single_query_ongoing': 50,
    'ongoing_min_weeks_observed': 8,

    # ---------- REDUNDANT-DUPLICATE gates ----------
    'redundant_min_shared_queries': 3,
    'redundant_dominance_frac': 0.70,
    'redundant_buried_position': 15.0,
    'redundant_max_weak_click_share': 0.25,

    # ---------- AFFECTED-CASE handoff gates ----------
    'handoff_smoothing_weeks': 4,
    'handoff_min_pre_clicks': 5,
    'handoff_min_post_clicks': 5,
    'handoff_min_anticorrelation': -0.30, # Spearman rank correlation over the crossover zone
    'handoff_min_coexistence_weeks': 3,
    'handoff_min_qualifying_queries': 1,
    'handoff_post_silence_weeks': 6,

    # ---------- SERP-feature attribution (GSC searchAppearance) ----------
    'serp_attribution_enabled': True,
    'serp_non_web_appearance_dominance': 0.40,
    'serp_attribution_min_delta': 0.30,

    # ---------- Case classification ----------
    'high_click_threshold': 5000,
    'freshness_url_year_pattern': r'/(20\d{2})(?:/|-|$)',
    'freshness_min_age_days_for_winner': 365,
    'freshness_max_age_days_for_new': 365,

    # ---------- Action plan ----------
    'leakage_warning_pct': 0.10,
    'leakage_critical_pct': 0.25,

    # ---------- Cluster winner scoring ----------
    'score_weights': {'clicks': 0.5, 'trend': 0.3, 'position': 0.2},
}


def min_topic_idf(cfg):
    """IDF floor a query must clear to count as 'topic-bearing'."""
    frac = cfg.get('idf_topic_max_df_fraction', 0.30)
    return math.log(1.0 / frac) if frac and frac > 0 else 0.0


def load_cfg(config_path=None):
    """DEFAULT_CFG overlaid with the run config's `thresholds` block."""
    cfg = json.loads(json.dumps(DEFAULT_CFG)) # deep copy
    if not config_path:
        return cfg, {}
    raw = json.loads(Path(config_path).read_text(encoding='utf-8'))
    for k, v in (raw.get('thresholds') or {}).items():
        if k not in cfg:
            raise SystemExit(f'unknown threshold "{k}" in {config_path}')
        cfg[k] = v
    return cfg, raw
