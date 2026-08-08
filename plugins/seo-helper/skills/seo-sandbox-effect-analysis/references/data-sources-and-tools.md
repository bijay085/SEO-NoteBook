# Data sources & tools : the no-hallucination contract

Every tool and credential below was **verified present in this environment** before being named.
If a future run lacks one, say so and ask : never invent a tool name to keep the workflow moving.
All *reasoning, interpretation, and report authoring is done by Claude itself* (Claude Max). No
third-party AI API is used (see "Forbidden" below).

## Credential truth (`project `.env` / host environment variables`) : checked, values never printed

| Key | State | Use it? | How |
|---|---|---|---|
| `GSC_CLIENT_ID` / `GSC_CLIENT_SECRET` | SET | : | Not needed directly; GSC goes through the MCP |
| `GSC_REFRESH_TOKEN` | **EMPTY** | **No direct OAuth** | There is NO working direct-GSC path from .env. Use the GSC **MCP**. |
| `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` | SET | Yes | Via the DataForSEO **MCP** (preferred) or Basic-Auth HTTP to `api.dataforseo.com` |
| `VALUESERP_API_KEY` | SET | Yes | Direct HTTP `https://api.valueserp.com/search` (live SERP snapshot) |
| `PAGESPEED_API_KEY` | SET | Yes | Direct HTTP PageSpeed Insights (mobile CWV) |
| `SCRAPINGBEE_KEY` | SET | Yes | Direct HTTP `https://app.scrapingbee.com/api/v1/` (render/anti-bot fetch) |
| `AHREFS_API_KEY` | **EMPTY** | **No** | Do NOT call Ahrefs directly. Backlinks come from DataForSEO MCP + client CSV. |
| `SEMRUSH_API_KEY` | **EMPTY** | **No** | Same : no direct Semrush call. |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | SET | **FORBIDDEN** | Present for unrelated tooling. This skill must NOT call them. Claude reasons. |

## GSC : Google Search Console MCP (`mcp__google-search-console__*`) : PRIMARY

The cheapest, highest-signal first-party data. Real tool names in this environment:
`list_accounts`, `list_sites`, `list_sitemaps`, `query_search_analytics`, `get_top_pages`,
`query_by_search_type`, `query_by_search_appearance`, `compare_performance`,
`find_keyword_opportunities`, `get_keyword_trend`, `analyze_brand_queries`, `inspect_url`,
`export_analytics`.

Gotchas baked into the skill:
- If `list_accounts` shows >1 account, pass `account` on **every** call or it errors. Set it in
  `config.gsc.account`. Prefer the **domain property** `sc-domain:...`.
- **Date-dimension totals are accurate; query-dimension totals UNDERCOUNT** (GSC anonymises rare
  queries). So: headline trend from `dimensions:["date"]`; brand split from `dimensions:["query"]`;
  never sum the two together. `sandbox_metrics.py` enforces this separation.
- GSC lags ~2 to 3 days : end any window ~2 days before today; the current month is partial and is
  auto-excluded from trend charts.
- To pull the daily series for `sandbox_metrics.py --daily`: `query_search_analytics` with
  `dimensions:["date"]` over `config.period`. For `--queries`: `dimensions:["query"]`, high
  `rowLimit`. For `--pages`: `dimensions:["page"]`.

## DataForSEO MCP (`mcp__dataforseo__*`) : ENHANCEMENT (config.enhancements.dataforseo)

Independent corroboration + the data GSC can't give:
- **Backlinks / off-page trust:** `backlinks_summary`, `backlinks_backlinks`, `backlinks_anchors`,
  `backlinks_referring_domains`, `backlinks_bulk_spam_score`, `backlinks_competitors`,
  `backlinks_domain_intersection` (link-gap vs `config.inputs.competitors`). Save an export and feed
  `backlink_trust.py`, or read the client's Ahrefs/Semrush CSV directly.
- **Ranking history (is it a demotion, not a sandbox?):**
  `dataforseo_labs_google_historical_rank_overview`, `dataforseo_labs_google_historical_serps` : 
  an independent ranking timeline to cross-check a suspected changepoint.
- **Live SERP (who actually holds the money terms):** `serp_organic_live_advanced`.
- **Authority-gap math:** `dataforseo_labs_google_domain_rank_overview`,
  `dataforseo_labs_google_competitors_domain`, `dataforseo_labs_bulk_traffic_estimation`.
- **Content duplication/thin-content:** `content_analysis_search` / `content_analysis_summary`.
- **Core Web Vitals / tech:** `on_page_lighthouse` (label it desktop/mobile), `on_page_instant_pages`.
- **Keyword demand for intent/tool pages:** `dataforseo_labs_google_keyword_ideas`,
  `keyword_overview`, `kw_data_google_ads_search_volume`.

## Microsoft Clarity MCP (`mcp__clarity__*`) : ENHANCEMENT (config.enhancements.clarity)

Only if the client's Clarity project is connected. `query-analytics-dashboard` (rage/dead clicks,
scroll depth, device split) and `list-session-recordings` corroborate a conversion/UX suppression
hypothesis with real behavior : never assert a UX cause without it.

## Direct HTTP (keys SET) : call from a script, key read from `os.environ`, never hardcoded

- **ValueSERP** live SERP: `GET https://api.valueserp.com/search?api_key=$VALUESERP_API_KEY&q=<kw>&location=<loc>&gl=uk&hl=en`
- **PageSpeed** mobile CWV: `GET https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<u>&strategy=mobile&key=$PAGESPEED_API_KEY`
- **ScrapingBee** (Cloudflare/anti-bot or JS render): `GET https://app.scrapingbee.com/api/v1/?api_key=$SCRAPINGBEE_KEY&url=<u>&render_js=true` : use for `entity_trust_audit.py --file` snapshots when a plain fetch is blocked.

## Browser MCP (`browser / Playwright / agent browse tools`) : rendered DOM

For render-gap checks (what a crawler sees pre-JS vs the rendered DOM) use the browser MCP, or
defer to the existing `seo-render-audit` skill. Relevant when content is client-side rendered and may
be invisible to Google : a real (and often missed) suppression cause.

## WebSearch / WebFetch : corroboration only

Use `WebSearch` to confirm a Google core/spam-update window around a detected changepoint
(Search Engine Land / Roundtable / Google Status Dashboard), and `WebFetch` for a specific
competitor page. Do NOT launch a broad research sweep for things GSC already answers or that are
common SEO knowledge.

## Forbidden

- No `GEMINI_API_KEY` / `OPENAI_API_KEY` calls anywhere in this workflow. Claude does the analysis.
- No direct Ahrefs/Semrush API calls (keys empty) : DataForSEO MCP + client CSV instead.
- No fabricated numbers. Every metric traces to a file, an MCP pull, or a script run. A value that
  can't be computed is a stated data gap, not an estimate.
