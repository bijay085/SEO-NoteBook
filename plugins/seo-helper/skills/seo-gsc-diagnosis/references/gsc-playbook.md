# GSC MCP Playbook

Exact call recipes and gotchas for the `google-search-console` MCP tools. Read this when running
Phase 0–1 of the run route.

## Multi-account / permission gotchas (these WILL bite)

- If more than one Google account is connected, **every** call errors unless you pass `account`.
  Run `list_accounts` first; pass e.g. `account: "business"` on every subsequent call.
- A property can be **listed but not permissioned**. The domain property `sc-domain:example.com`
  may return *"User does not have sufficient permission"* even though it shows in `list_sites`.
  When that happens, fall back to the URL-prefix property `https://example.com/`.
- Prefer the **domain property** when it works (it aggregates http/https + www/non-www + subdomains).
  Use URL-prefix only as the fallback.

## Date window

- GSC data lags ~2–3 days. Set `endDate` to ~2 days before today.
- Default to a 3–6 month window for a stable picture. Narrow it to spot recent changes
  (e.g. a traffic drop → compare two adjacent windows).

## Core calls (run in this order)

1. **Top pages** — see which URLs carry impressions/clicks and at what CTR/position:
   `get_top_pages { siteUrl, account, startDate, endDate, sortBy: "clicks", limit: 60 }`
   Also pull `sortBy: "impressions"` — the highest-impression pages are where zero-click problems hide.

2. **Top queries**:
   `query_search_analytics { siteUrl, account, startDate, endDate, dimensions: ["query"], rowLimit: 150 }`
   Scan for: brand vs non-brand, informational vs commercial/local, and CTR-by-position outliers.

3. **Cannibalization candidates (query × page)**:
   `query_search_analytics { ..., dimensions: ["query","page"], rowLimit: 25000 }`
   This is almost always too big to read inline and gets written to a file. Do **not** read it raw —
   run `scripts/cannibalization_scan.py <that_file>`. Then verify candidates with `check_urls.sh`.

4. **Page-2 opportunities**:
   `find_keyword_opportunities { ..., minImpressions: 300, maxPosition: 20, maxCtr: 0.02 }`
   High-impression, low-CTR, top-20 queries — the clearest optimization targets.

5. **Per-URL index/canonical truth (optional)**: `inspect_url` returns Google's *selected* canonical
   vs the *declared* canonical and coverage state. Useful to confirm whether Google has actually
   consolidated a redirected/canonicalized duplicate, beyond what `check_urls.sh` shows at the HTTP layer.

## Interpreting CTR vs position (the core read)

| Position | CTR | Reading | Action |
|---|---|---|---|
| > ~10 | any | genuine ranking gap | content / links / structure / consolidate |
| ≤ ~8 | < ~1% on big impressions | zero-click SERP (AI Overview / snippet / PAA) | SERP-feature capture, or pivot to click-earning query types |
| ≤ ~8 | ≳ 3% | working as intended | leave it; replicate the pattern |
| 11–20 | ≳ 1% | page-2 quick win | on-page + internal links to push to page 1 |

A page averaging position ~5 with 0.1–0.5% CTR across hundreds of thousands of impressions is the
signature of an informational query class being answered on the SERP. Ranking higher won't help —
you already rank. This is the finding that's easiest to miss if you look at clicks alone.

## Brand-query noise

Brand/navigational queries (the store's name and misspellings) legitimately surface many URLs at
once (sitelinks-style) and will top the `cannibalization_scan.py` output. That is **not**
cannibalization — recognise and discount these before reporting.
