"""Render the SEO deliverable: branded HTML + master XLSX.

Sections mirror the app's Google Sheet tabs, minus the Sheets dependency:
  Action Plan the client-facing summary : only the cases worth surfacing
  All URLs (detail) every analysed URL with its finding
  Evidence one row per qualifying shared query : the audit trail
  Cluster Summary one row per cluster
  Coverage & limits what this run did and did not cover

Usage:
    python build_report.py --work <dir> --out <dir> [--client "Acme"] [--config config.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "shared"))
from cannib_config import load_cfg
from report_kit import render_html, render_xlsx

# Verdict -> (plain-English explanation for the client, severity).
EXPLAIN = {
    'duplicate': ('Two pages are effectively the same page. Google has to pick one, and the '
                  'ranking signals you have earned are split across both.', 'critical'),
    'ongoing cannibal': ('Both pages are competing for the same searches right now : clicks, '
                         'impressions and positions split between them week after week.',
                         'critical'),
    'affected_handoff (loser)': ('This page already lost its searches to another page on your '
                                 'site. The traffic moved across; this URL is now dead weight : '
                                 'but check what it held before redirecting.', 'high'),
    'redundant duplicate': ('Both pages target the same searches, but this one is consistently '
                            'buried or out-clicked. Not a contest : dead weight diluting the '
                            'stronger page.', 'high'),
    'differentiate : keep both': ('These two pages overlap on some terms, but each earns most of '
                                  'its traffic on searches the other does not rank for. They are '
                                  'distinct pages : merging them would destroy real traffic.',
                                  'medium'),
    'overlap watch': ('Both pages cover the same topic, but nobody is losing traffic yet. Early '
                      'warning only : re-check next analysis.', 'low'),
    'cluster winner': ('The strongest page of its group : the one everything else should point '
                       'at.', 'good'),
    'affected_handoff (winner)': ('This page won a past handoff. Keep it.', 'good'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--client', default='')
    ap.add_argument('--period', default='')
    ap.add_argument('--config', default='')
    args = ap.parse_args()

    _cfg, raw_cfg = load_cfg(args.config or None)
    work, out = Path(args.work), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    plan = json.loads((work / 'plan.json').read_text(encoding='utf-8'))
    s = plan['summary']
    rows = plan['action_plan']
    client = args.client or raw_cfg.get('client') or s.get('site', 'Site')
    period = args.period or raw_cfg.get('period') or f'window ending {s.get("end_date", "")}'

    actionable = [r for r in rows if int(r.get('priority', 10)) <= 6]
    dist = s.get('verdict_distribution', {})

    # ---- Action Plan: the client deliverable ----------------------------
    if actionable:
        intro = (f'{len(actionable)} pages need attention out of {s["urls_analyzed"]} analysed, '
                 f'covering {s["clicks_at_stake"]:,} clicks. Work top-down: rows are ordered by '
                 f'how clear-cut the case is, then by traffic at stake. Every row is backed by the '
                 f'shared searches in the Evidence section : read those before acting on any large '
                 f'consolidation.')
    else:
        intro = (f'No cannibalization found across {s["urls_analyzed"]} analysed pages. Every page '
                 f'either owns its searches outright or shares none with a same-intent sibling.')

    findings = []
    for r in actionable[:60]:
        explain, sev = EXPLAIN.get(r['status'], (r.get('reason', ''), 'medium'))
        findings.append({
            'issue': f'{r["status"]}: {r["url"]}',
            'sev': sev,
            'evidence': (f'{r["clicks_window"]:,} clicks / {r["impressions_window"]:,} impressions '
                         f'in window; avg position {r.get("avg_position_90d") or ": "}; trend: '
                         f'{r.get("trend") or ": "}. Shared searches: '
                         f'{r.get("shared_queries") or "see Evidence section"}. '
                         f'Measured basis: {r.get("reason", "")}'),
            'solution': f'{explain} Page to keep: {r.get("winner") or ": "}.',
            'execution': r.get('action', ''),
            'priority': f'P{min(max(int(r.get("priority", 3)) - 1, 0), 2)}',
            'effort': 'S' if r['status'] in ('duplicate', 'overlap watch') else 'M',
        })

    sections = [{
        'id': 'action-plan', 'title': 'Action Plan', 'intro': intro,
        'chart': ({'type': 'hbars', 'title': 'Findings by type', 'unit': ' pairs',
                   'data': [[k, v] for k, v in sorted(dist.items(), key=lambda kv: -kv[1])
                            if k != 'not_cannibal']}
                  if dist else None),
        'table': {'cols': ['Priority', 'Confidence', 'Page to redirect / act on', 'Page to keep',
                           'Recommended action', 'Clicks at stake'],
                  'rows': [[r.get('priority', ''), r.get('confidence', ''), r['url'],
                            r.get('winner') or ': ', r.get('action', ''), r['clicks_window']]
                           for r in actionable]},
        'findings': findings,
    }]

    # ---- All URLs -------------------------------------------------------
    sections.append({
        'id': 'all-urls', 'title': 'All URLs (detail)',
        'intro': ('Every analysed URL and its finding : the analyst view. `standalone` means no '
                  'other URL competes with it.'),
        'table': {'cols': ['URL', 'Finding', 'Confidence', 'Cluster', 'Winner', 'Clicks',
                           'Impressions', 'Avg position', 'Trend', 'Reasoning'],
                  'rows': [[r['url'], r['status'], r.get('confidence', ''), r.get('cluster_id', ''),
                            r.get('winner', ''), r['clicks_window'], r['impressions_window'],
                            r.get('avg_position_90d', ''), r.get('trend', ''), r.get('reason', '')]
                           for r in rows]},
    })

    # ---- Evidence -------------------------------------------------------
    ev = plan.get('evidence', [])
    if ev:
        cols = ['url_a', 'url_b', 'verdict', 'shared_query', 'kind', 'clicks_a', 'clicks_b',
                'click_parity', 'impressions_a', 'impressions_b', 'impr_parity', 'position_a',
                'position_b', 'position_delta', 'simultaneity_pct', 'crossover_week',
                'coexistence_weeks', 'spearman_r', 'loser_residual_clicks']
        sections.append({
            'id': 'evidence', 'title': 'Cannibalization Evidence',
            'intro': ('One row per shared search that actually drove a verdict. Always read this '
                      'before an expensive consolidation: ten queries all in the green is a far '
                      'stronger case than one with marginal parity.'),
            'table': {'cols': cols, 'rows': [[e.get(c, '') for c in cols] for e in ev]},
        })

    # ---- Clusters -------------------------------------------------------
    if plan.get('clusters'):
        sections.append({
            'id': 'clusters', 'title': 'Cluster Summary',
            'intro': 'One row per group of competing pages.',
            'table': {'cols': ['Cluster', 'Winner (keep)', 'Pages', 'Cannibals', 'Clicks total',
                               'Clicks at stake'],
                      'rows': [[c['cluster_id'], c['winner'], c['pages'], c['cannibals'],
                                c['clicks_total'], c['clicks_at_stake']]
                               for c in plan['clusters']]},
        })

    # ---- Coverage & limits ---------------------------------------------
    coverage = [
        ['URLs analysed', s['urls_analyzed']],
        ['Distinct queries', s.get('queries_distinct', '')],
        ['Topics after semantic grouping', s.get('topics') or 'n/a (exact-string matching)'],
        ['Candidate pairs judged', s.get('pairs_judged', 0)],
        ['Clusters with cannibals', s.get('clusters_with_cannibals', 0)],
        ['Brand terms normalised', ', '.join(s.get('brand_tokens') or []) or 'none detected'],
        ['Weekly (date x query) series pulled',
         f'{s.get("weekly_series_urls", 0)} of {s.get("weekly_series_expected", 0)} shortlisted URLs'],
        ['Weak ongoing pairs kept out of clusters', s.get('weak_ongoing_not_clustered', 0)],
        ['URLs dropped for scale cap', s.get('urls_dropped_for_scale', 0)],
        ['Pairs skipped (missing weekly data)', s.get('pairs_skipped_missing_weekly', 0)],
    ]
    limits = []
    missing_weekly = s.get('weekly_series_expected', 0) - s.get('weekly_series_urls', 0)
    if missing_weekly > 0:
        limits.append({'issue': f'{missing_weekly} shortlisted URLs have no weekly series',
                       'sev': 'high',
                       'evidence': 'plan.json weekly_series_urls vs weekly_series_expected',
                       'solution': ('For those URLs the handoff detector cannot run and ongoing '
                                    'parity has no week-by-week evidence, so "sustained over '
                                    'weeks" is unverified.'),
                       'execution': 'Pull the missing URLs with dimensions ["date","query"] and '
                                    're-run run_verdicts.py.',
                       'priority': 'P0', 'effort': 'M'})
    if s.get('urls_dropped_for_scale'):
        limits.append({'issue': f'{s["urls_dropped_for_scale"]} URLs excluded by the scale cap',
                       'sev': 'medium', 'evidence': 'meta.json urls_dropped_for_scale',
                       'solution': ('Lower-impression URLs were not analysed, so a cannibal pair '
                                    'between two of them would be missed.'),
                       'execution': 'Raise `max_urls` in the config and re-run to widen coverage.',
                       'priority': 'P2', 'effort': 'S'})
    if s.get('pairs_skipped_missing_weekly'):
        limits.append({'issue': (f'{s["pairs_skipped_missing_weekly"]} pairs skipped : weekly data '
                                 f'missing'), 'sev': 'high',
                       'evidence': 'pair_verdicts.json pairs_skipped',
                       'solution': 'Those pairs carry no verdict : neither cleared nor flagged.',
                       'execution': ('Fetch the missing per-URL weekly dumps listed in '
                                     'weekly/_fetch_list.json and re-run run_verdicts.py.'),
                       'priority': 'P0', 'effort': 'S'})
    sections.append({
        'id': 'coverage', 'title': 'Coverage & limits',
        'intro': 'What this run did and did not cover. Read before quoting any number as complete.',
        'table': {'cols': ['Measure', 'Value'], 'rows': coverage},
        'findings': limits,
    })

    report = {
        'title': 'Keyword Cannibalization Audit', 'client': client, 'period': period,
        'subtitle': (f'Verdict-based analysis of {s["urls_analyzed"]} URLs from Google Search '
                     f'Console : every finding backed by the shared searches that produced it.'),
        'output_dir': str(out), 'sections': sections,
    }

    html_path = out / 'Cannibalization-Audit.html'
    html_path.write_text(render_html(report), encoding='utf-8')
    xlsx_path = out / 'Cannibalization-Audit.xlsx'
    try:
        render_xlsx(report, str(xlsx_path))
    except Exception as e: # noqa: BLE001
        xlsx_path = None
        print(f'XLSX skipped ({type(e).__name__}: {e}) : the HTML report is complete.')

    if rows:
        with (out / 'action-plan.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    print(f'wrote {html_path}')
    if xlsx_path:
        print(f'wrote {xlsx_path}')


if __name__ == '__main__':
    main()
