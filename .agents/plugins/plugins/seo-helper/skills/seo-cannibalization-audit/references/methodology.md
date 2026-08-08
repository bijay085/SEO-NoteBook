# Methodology : the decision cascade

Ported from a prior cannibalization-analysis app (`SOP.md` §1, §6, §7). Thresholds live in
`scripts/cannib_config.py`; override them from the run config's `thresholds` block.

## 1. There is no single score

Signals are evaluated as an ordered **cascade**. The first tier whose combination fires wins, so
when several could apply, the precedence is what decides:

```
shortlist → duplicate → affected_handoff → ongoing
           → [differentiate guard] → redundant_duplicate
           → overlap_watch → not_cannibal
```

**Cannibalization needs only ONE shared query that fully qualifies** : not a fixed count. A pair
sharing a single distinctive query, splitting clicks and impressions evenly at a similar position
over weeks, is a real verdict. What stops that being noise is the *materiality* floor, not a count.

## 2. Shortlist : who is even compared

A pair that fails the shortlist is never cannibalization.

**Tier 1 : entity peer-group gate (primary).** When both pages carry a Claude entity assignment they
are eligible only if they share a `peer_group_id` (`axis_1.axis_2`), or one is a hub whose `covers`
includes the other's `axis_1`. A cross-section pair is **structurally blocked** : it cannot be a
cannibal however much ambiguous-query overlap it shows. This is what stops a *writing* page being
"cannibalized" by a *speaking* page because both surface on one ambiguous term.

**Tier 2 : statistical OR-gate (when an entity assignment is missing).** Any one of:
- IDF-weighted **click** cosine ≥ `shortlist_min_click_cosine` (0.30)
- IDF-weighted **impression** cosine ≥ `shortlist_min_impr_cosine` (0.40) : OR'd with clicks so a
  buried page (impressions, ~no clicks) still reaches the detector
- **Topic-profile** cosine ≥ `shortlist_min_topic_profile_sim` (0.85) : semantic recall for
  same-intent pages whose query keys differ in surface form

`shortlist_min_shared_topic_queries` applies **only** when the cosine path alone rescued the pair.

The intent gate runs in both tiers. Different non-`unknown` intents never cannibalize, with two
deliberate exceptions: `news`↔`informational` (a stale evergreen article and a fresh news piece do
compete) and `commercial`↔`informational` ("best X" / "X review" straddle both).

**The per-URL cap keeps strong signal.** `shortlist_max_pairs_per_url` (12) trims the weak tail, but
any pair scoring ≥ the strong threshold is auto-kept. A plain top-N cap silently dropped
low-cosine-but-high-topic-similarity pairs because they ranked below high-cosine peers.

## 3. Duplicate fast lane

Settled *before* the time series, because a context-identical pair is a duplicate whatever the
traffic does. Fires when intents agree and either:
- page context similarity ≥ `dup_content_min` (0.94) : Claude's judgment on slug + title + H1 + meta; or
- URLs are near-twins (slug differs only by a number or year) **and** topic-profile ≥
  `dup_twin_topic_min` (0.88) **and** content ≥ `dup_twin_content_min` (0.50)

That last clause is a **veto, not a gate**. Without it `/reading-practice-test/` and
`/reading-practice-tests-3/` both scored `duplicate` High : a Part 3 page with different content
should never be auto-merged into Part 1 just because the slug differs by `-3`. A `content_sim` of
`None` (no signal) is allowed through; only an *actively low* score vetoes.

## 4. Ongoing : a live split

A shared query qualifies only if **all** gates hold over `recent_window_days` (90):

| Gate | Default | Why |
|---|---|---|
| combined clicks | ≥ 15 | materiality : below this, parity is noise |
| clicks each side | ≥ 3 | stops 14-vs-1 passing the symmetric ratio |
| click parity `min/max` | ≥ 0.40 | an even split, not a rout |
| impression parity | ≥ 0.40 | both genuinely being served |
| position delta | ≤ 5 | ranked comparably |
| max position | ≤ 10 | both in the real organic block |
| simultaneity | ≥ 50% of weeks | co-present, not alternating |
| weeks observed | ≥ 8 | sustained, not a blip |

## 5. Affected handoff : one already replaced the other

Per shared query, over the full window:
1. Smooth both click series (`handoff_smoothing_weeks`, 4-week rolling mean).
2. A's peak ≥ `handoff_min_pre_clicks` (5).
3. B's peak *after* A's peak ≥ `handoff_min_post_clicks` (5).
4. Crossover = first week in that zone where smoothed B ≥ smoothed A.
5. A then stays near-silent (≤20% of its peak) for `handoff_post_silence_weeks` (6). **If A is still
   alive it is an ongoing split, not a completed handoff.**
6. Co-existence zone ≥ `handoff_min_coexistence_weeks` (3) : the transition.
7. **Spearman** rank correlation ≤ `handoff_min_anticorrelation` ( to 0.30). Rank, not Pearson: weekly
   click series are spiky and a single spike swings Pearson.

Both directions are tested; the one with more qualifying queries wins.

**Leakage** then compares the loser's pre-handoff window against the winner's post-handoff window:
- < 10% lost → clean, just 301
- 10 to 25% → review the lost queries, then 301
- > 25% → **migrate then 301** : real value was left behind

## 6. Differentiate guard : the anti-destructive-301 net

A page earning ≥ `distinct_page_unique_share` (0.60) of its clicks on queries the other page does
**not** rank for is a DISTINCT page. It blocks `duplicate`, `ongoing` and `redundant` from
auto-merging, and the verdict becomes `differentiate` : keep both, consolidate only the genuinely
overlapping terms.

It runs on raw (brand-normalised) GSC demand, so it is independent of the topic judgment. It does
**not** apply to `affected_handoff`: that is history, and the loser has already lost the queries.

## 7. Redundant duplicate : no contest, still dead weight

When the ongoing test fails, check whether one page is consistently dominated across
≥ `redundant_min_shared_queries` (3) co-appearing queries, in ≥ `redundant_dominance_frac` (70%) of
them, and is either *buried* (median position > 15) **or** *out-clicked* (< 25% of the pair's
clicks). The out-clicked arm closes the gap parity leaves: an 80/20 split with both pages on page 1
fails parity yet is plainly not a contest.

## 8. SERP-feature attribution

Computed from GSC `searchAppearance`, but applied **only after** parity/handoff evidence exists : it
can downgrade, never short-circuit. Applying it first killed real cannibals whose shared queries were
both plain organic but which happened to win a PAA or video slot on unrelated terms.

## 9. Clusters, winners, actions

Cluster edges = `duplicate`, `ongoing`, `affected_handoff`. `redundant_duplicate`, `overlap_watch`
and `differentiate` are deliberately **not** clustered : the first has a direction the detector
already fixed, and the other two are keep-both / monitor.

**Cluster-strength gate:** a single-query `ongoing` needs
`cluster_min_clicks_for_single_query_ongoing` (50) combined clicks before becoming an edge. Two or
more qualifying queries always qualify : the redundancy is itself the signal. Weak pairs stay in
`pair_verdicts.json` for diagnostics.

Winner = `0.5·clicks + 0.3·sigmoid(trend) + 0.2·position-rank`, normalised within the cluster. Trend
direction comes from **Mann-Kendall** (significant at p<0.05), not a hardcoded slope : a slope of 0.5
means nothing without knowing the click scale.

**Staged redirects.** When the page you would redirect is *newer and gaining* while the keeper is
flat or declining, the action becomes STAGED: audit → port → canonical → observe 4 to 6 weeks → redirect
only if the keeper re-wins. Redirecting a rising page kills content winning on merit.

## Tuning

**Too few verdicts.** Loosen one gate at a time:
`ongoing_min_click_parity` 0.40→0.30, `ongoing_max_position_abs` 10→15,
`ongoing_min_simultaneity_pct` 0.50→0.40, `ongoing_min_weeks_observed` 8→4. For handoff:
`handoff_min_anticorrelation` to 0.30→ to 0.20, `handoff_min_pre_clicks` 5→3,
`handoff_post_silence_weeks` 6→4.

If pages targeting the same topic in **different phrasings** never pair up at all, no threshold fixes
it : that is a recall gap in the topic judgment. Redo Phase 4 and merge those phrasings, or lower
`shortlist_min_topic_profile_sim` toward 0.80.

**Too many verdicts.** Tighten `shortlist_min_click_cosine` 0.30→0.40,
`ongoing_min_click_parity` 0.40→0.50, `ongoing_max_position_delta` 5→3. You *can* raise
`shortlist_min_shared_topic_queries` to 2, but understand the cost: it rejects every pair that
cannibalizes on a single shared query, which is a genuine pattern. Prefer the parity gates first.

**Small site (<50 pages), nothing clusters.** The IDF threshold is too strict for a small corpus : 
most queries look ubiquitous, so few count as topic-bearing. Raise
`idf_topic_max_df_fraction` 0.30→0.60.

**Too many duplicates.** Raise `dup_content_min` toward 0.95 and `dup_twin_topic_min` toward 0.92.
**Real duplicates missed.** Lower them slightly : and check you actually answered
`04_duplicates.task.json`; without it only the URL-twin path can fire.

**Too many overlap-watch rows.** Raise `overlap_watch_topic_min`, `overlap_watch_content_min`, or
`overlap_watch_min_shared`.
