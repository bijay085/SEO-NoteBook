# Inputs & Tools

Everything the skill can consume, and the exact tools/credentials it may call.
**Nothing here is hypothetical** — each tool is a connector or skill that exists
in this environment; each credential is a key present in `project `.env` / host environment variables`
(names only, never values). If something is not present at run time, the skill
**asks for it or fetches it** — it never invents a source.

## Input catalogue

Inputs are **custom / similar / additional** friendly: the required core is tiny;
everything else strengthens the verdict and can be swapped or extended.

| # | Input | Required | Format | If missing |
|---|---|---|---|---|
| 1 | **Site URL** | Yes | a URL | ask |
| 2 | **Competitor pages** (1-3) | Strong | URLs, or saved `view-source_<url>.html` | discover the top organic rivals for the money query via DataForSEO SERP, confirm with user |
| 3 | **Lead-form page** | Recommended | URL or saved HTML | use the site's `/contact*`; if none, note the form audit is skipped |
| 4 | **Microsoft Clarity exports** | Recommended | one folder per page, each with `*_Click_PC_*.csv`, `*_Scroll_PC_*.csv`, `*_Attention_PC_*.csv` (Clarity's key/value header + a `"Metric",…` table) | pull top-line behavior from Clarity MCP; or ask the client to export |
| 5 | GA4 exports | Optional | CSV (engagement; acquisition + device category) | proceed without; note quantitative context is limited |
| 6 | Lead / conversion outcomes | Optional | CSV / form-submission export | proceed without |
| 7 | Sitemap / page-type segmentation | Optional | XLSX / CSV | derive page types from URLs |
| 8 | **Anything else** (call logs, CRM, recordings) | Optional | any | treat as supporting evidence |

Rule: a missing recommended input is a **request**, not a silent zero.

## Tool & credential map (grounded)

Inside the Claude interface the data comes from **MCP connectors** (they manage
their own OAuth) and the bundled **offline scripts** (no keys). Claude does all
reasoning — there is no OpenAI/Gemini/Anthropic API call in this skill.

### Page acquisition (Stage 2)
- browser/`navigate` (Playwright or agent browse) + browser/`get_page_text` (Playwright or agent browse) /
  browser/`read_page` (Playwright or agent browse)
- `WebFetch` (single page), `WebSearch` (find a URL)
- `mcp__dataforseo__on_page_instant_pages`, `mcp__dataforseo__on_page_content_parsing`

Save each fetched page to `pages/` as `view-source_<url>.html` with a first line
`<!-- crawled: <URL> -->` so `common.load_page` records the URL.

### Behavioral (Stage 3/5)
- Client Clarity CSV exports → `scripts/clarity_behavior.py` (richest — per-element
  clicks; **preferred**)
- `mcp__clarity__query-analytics-dashboard`, `mcp__clarity__list-session-recordings`
  (live dashboard behavior when no export is available)

### Competitor discovery, market sizing, Core Web Vitals, backlinks
- `mcp__dataforseo__serp_organic_live_advanced` — who ranks for the money query
- `mcp__dataforseo__dataforseo_labs_google_competitors_domain` — domain rivals
- `mcp__dataforseo__on_page_lighthouse` — Core Web Vitals (mobile conversion headwind)
- `mcp__dataforseo__backlinks_summary` — authority context
- `mcp__dataforseo__dataforseo_labs_google_ranked_keywords` — demand/opportunity

### Search Console context
- `mcp__google-search-console__query_search_analytics`, `…get_top_pages`,
  `…compare_performance`, `…inspect_url`, `…list_sites`

### Output
- `xlsx` skill (workbook) + `scripts/cro_report.py`
- **built-in report branding** skill (branded HTML narrative)

### Credentials (only if run OUTSIDE the interface)
The scripts never call an API. If you drive the same data from raw keys instead of
connectors, they live in `project `.env` / host environment variables` (names only):
`DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`, `SCRAPINGBEE_KEY`, `PAGESPEED_API_KEY`,
`AHREFS_API_KEY`, `SEMRUSH_API_KEY`, `VALUESERP_API_KEY`,
`GSC_CLIENT_ID` / `GSC_CLIENT_SECRET` / `GSC_REFRESH_TOKEN`,
`GEMINI_API_KEY`, `OPENAI_API_KEY`. Treat `.env` as read-only-sensitive; never
print or commit values.

## Connector-auth fallbacks

MCP connectors (DataForSEO, Google Search Console, Clarity, browser) may require
authorization. If a call fails for auth:

1. Tell the user which connector is unauthorized.
2. Ask them to connect it (host MCP / connector settings) **or** to supply the
   equivalent data as a file.
3. Continue with what is available, and state in the report what the gap left
   unproven.

Never ask the user for raw tokens, passwords, or callback URLs.
