---
name: cannibalization-audit
description: >-
  Full forensic keyword-cannibalization audit from Google Search Console data : the verdict engine,
  not a candidate list. For every same-intent page pair it runs a decision cascade (duplicate →
  affected handoff → ongoing split → differentiate guard → redundant duplicate → overlap watch) over
  per-query WEEKLY GSC time series, then emits a per-URL action plan (301 / migrate-then-301 /
  staged / keep both / monitor) with the shared searches that prove each call. Use whenever someone
  asks to "audit cannibalization", "keyword cannibalization analysis", "are these pages competing",
  "which pages are splitting traffic", "find duplicate pages eating each other", "should I redirect
  or merge these pages", "did one page replace another", or wants to know which URL to consolidate
  onto. Every semantic judgment (topic grouping, page taxonomy, intent, duplicate calls) is made by
  Claude in-session : NO Gemini/OpenAI/embedding API. GSC comes from the connected Search Console
  MCP. Ported from a prior cannibalization-analysis app. Industry-agnostic and config-driven.
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# Keyword Cannibalization Audit

## What this is, and what it is not

This is the **verdict engine**. `seo-gsc-diagnosis` has a `cannibalization_scan.py` that lists
queries served by 2+ URLs : that is a *candidate list*, deliberately "not a conclusion." This skill
turns candidates into defensible verdicts, because the two questions that actually decide a
consolidation can only be answered from the **weekly time series**:

- **Are these two URLs splitting traffic on the same search right now?** (the *ongoing* case : 
  clicks, impressions and positions in parity, sustained over weeks)
- **Did one URL already replace the other?** (the *affected* case : a crossover in the historical
  weekly series, anti-correlated, with the loser going silent afterwards)

A single aggregate export cannot answer either. That is why this skill pulls `(date, query)` per URL.

**The expensive failure this exists to prevent is a wrong 301.** Recommending a redirect between two
pages that each own their own search demand destroys real traffic and is hard to walk back. Several
gates below exist purely to stop that; they should not be loosened casually.

## Where the intelligence comes from

The original app called Gemini for four things. All four are semantic judgments, so **Claude makes
them directly** : no embedding model, no metered API, no per-corpus threshold auto-calibration:

| Judgment | Was | Now |
|---|---|---|
| Group query phrasings into topics | embeddings + cosine threshold + a second LLM pass to undo over-merging | deterministic rare-token blocking → **you** partition each block |
| Page taxonomy (peer groups) | Gemini batch classification | **you** assign two axes per page |
| Page intent | Gemini, rule fallback | **you**, with the rule classifier as the prior |
| "Are these the same page?" | context-embedding cosine | **you** judge only the boundary pairs |

Everything numeric : parity gates, crossover detection, Spearman anti-correlation, IDF cosines,
Mann-Kendall trend, clustering, winner scoring, leakage : stays deterministic Python. Only
`numpy` + `pandas` are required (`openpyxl` for the XLSX). **No scipy.**

If you skip a judgment step the pipeline still runs and says so in the report's Coverage section:
topics fall back to exact-string matching, the peer-group gate turns off, intent falls back to
rules. That degradation is real and costs recall : don't skip silently.

## The run route

Work in a scratch `<work>` dir. `SCRIPTS=` this skill's `scripts/`.

### Phase 0 : Scope & access
Run `list_accounts` / `list_sites`. **With multiple accounts you must pass `account` on every call**
or it errors. Prefer the domain property (`sc-domain:…`); fall back to the URL-prefix property on
"insufficient permission." GSC lags ~2 to 3 days, so end the window ~2 days before today. Copy
`config.template.json` and fill in client / domain / property.

### Phase 1 : Pull the matrix
`query_search_analytics` with `dimensions:["page","query"]` over the window (16 months max). Save
the raw response to `<work>/data/matrix.json`. See `references/gsc-fetch-playbook.md` for row-limit
and pagination workarounds : **the MCP exposes no `startRow`, so a large site must be pulled in date
slices or the tail is silently lost.** Optionally also pull `searchAppearance` for SERP-surface
attribution (recipe in the playbook).

### Phase 2 : Normalise
```bash
python "$SCRIPTS/gsc_normalize.py" --work <work> --site sc-domain:example.com --matrix <work>/data/matrix.json --config config.json
```
Reports URLs, rows, queries, detected brand tokens, and whether a date dimension is present.

### Phase 3 : Prepare judgments
```bash
python "$SCRIPTS/judgment.py" prepare --work <work> --config config.json
```

### Phase 4 : **Make the judgments** (the Claude step)
Read each `<work>/judgment/0N_*.task.json`, reason, write `0N_*.answer.json` beside it matching the
`answer_schema` in the file. Full protocol and worked examples:
`references/claude-judgment-protocol.md`. The rule that matters: **under-merging is safe,
over-merging causes destructive 301s.**

### Phase 5 : Apply judgments
```bash
python "$SCRIPTS/judgment.py" apply --work <work> --config config.json
```

### Phase 6 : Shortlist
```bash
python "$SCRIPTS/shortlist.py" --work <work> --config config.json
```
Prints how many pairs the entity gate blocked structurally vs let through. A pair that fails the
shortlist is never cannibalization.

### Phase 7 : Pull weekly data for shortlisted URLs
```bash
python "$SCRIPTS/run_verdicts.py" --work <work> --config config.json
```
The first run writes `<work>/weekly/_fetch_list.json` (url → filename) and
`judgment/04_duplicates.task.json`. For **each** URL in the fetch list, call
`query_search_analytics` with `dimensions:["date","query"]` and
`filters:[{dimension:"page",operator:"equals",expression:"<url>"}]`, saving the raw response to
`<work>/weekly/<filename>`. This is the slow phase : one call per shortlisted URL.

Also answer `04_duplicates.task.json` : only the boundary pairs. Fetch the live pages for
title/H1/meta if you can, and state whether you did.

### Phase 8 : Verdicts
```bash
python "$SCRIPTS/run_verdicts.py" --work <work> --config config.json
```

### Phase 9 : Clusters, winners, action plan
```bash
python "$SCRIPTS/build_plan.py" --work <work> --config config.json
```

### Phase 10 : Deliverable
```bash
python "$SCRIPTS/build_report.py" --work <work> --out <out> --client "Acme" --config config.json
```
Branded HTML + master XLSX + `action-plan.csv`.

## Scale : read before running on a big site

The weekly pull is one MCP call per shortlisted URL, so cost scales with the shortlist, not the
site. `max_urls` defaults to **400** (top by impressions). The app took 45 to 75 min on ~3,800 pages
with a threaded pool; here it is sequential, so **treat 400 URLs as the comfortable ceiling for one
session** and raise `max_urls` deliberately. Whatever is dropped is listed in `meta.json` and
surfaced in the report's Coverage section : never present a capped run as full coverage.

## Reading the verdicts

| Verdict | Means | Do |
|---|---|---|
| `duplicate` | Same page twice : settled on page context, no time series needed | 301 → winner. Act on these first |
| `ongoing` | Live click/impression/position split, sustained ≥8 weeks | 301 → winner (or STAGED, below) |
| `affected_handoff` | One URL already replaced the other in history | 301, or **migrate-then-301** when leakage > 25% |
| `differentiate` | Would have merged, but a page owns ≥60% unique demand | **Keep both.** Consolidate only the overlapping terms |
| `redundant_duplicate` | Same queries, one page buried or out-clicked. Not a contest | Fold into the keeper, then 301. Lower urgency |
| `overlap_watch` | Same topic, nobody losing yet | Monitor only |
| `not_cannibal` | No parity now, no handoff in history | Nothing |

**STAGED** on an `ongoing` action means the page you would redirect is *newer and gaining* while the
keeper is flat or declining. Redirecting a rising page kills content winning on merit : follow the
staged steps instead.

**Always read the Evidence section before an expensive consolidation.** One qualifying query with
marginal parity is far weaker than ten in the green. The verdict tells you what the data says; it
does not absolve you of looking.

## The safety gates (do not loosen these casually)

- **Materiality** : a query needs ≥15 combined clicks and ≥3 on *each* side. Without it,
  1-click-vs-1-click scores perfect parity and produces nonsense clusters.
- **Differentiate guard** : ≥60% unique click share means distinct page. The main defence against a
  destructive 301.
- **Cluster strength** : a single-query `ongoing` needs 50+ combined clicks before it drags two pages
  into one cluster. It stays visible in `pair_verdicts.json` either way.
- **Twin-path content veto** : a slug twin (`-2`, `-3`, a year) is only a *hint*. Whether that number
  is semantic is decided by real search demand, not by the URL.
- **SERP attribution runs late** : it can only downgrade existing parity evidence, never
  short-circuit the cascade. Running it first killed real cannibals.

## Verify before you act

Cannibalization verdicts assume both URLs are live, self-canonical 200s. Two "competing" URLs
already 301'd to one page are a *non-issue*. Before delivering, run `seo-gsc-diagnosis`'s
`scripts/check_urls.sh` over the action-plan URLs and drop any pair that is already consolidated. A
200-vs-301 check is ~50 cheap requests; a wrong report costs trust.

## References

- `references/methodology.md` : the full cascade, every verdict, and the tuning guide
- `references/gsc-fetch-playbook.md` : exact MCP call recipes, row limits, multi-account gotchas
- `references/claude-judgment-protocol.md` : how to answer each judgment task, with examples
