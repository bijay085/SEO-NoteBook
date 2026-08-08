# Input Manifest & Tool Routing

What the audit needs, what to **request** when it's missing, what it can **fetch/query
itself**, and the exact tool/MCP/credential routing : all **real**, nothing invented.
The audit **degrades gracefully**: a missing source drops its dimension and is noted on
the cover; it never blocks the run.

## Inputs are flexible : custom / similar / additional all welcome
There is **one** hard requirement: a way to reach the pages (a URL list, a sitemap to
crawl, OR an outbound-link export). Everything else is optional and each input just
unlocks more. Custom inputs are never rejected : read them, say what you found, map them
to the closest dimension or add an appendix.

| Input | Feeds | If missing |
|---|---|---|
| **Domain + review/money URL list** | everything | Crawl `sitemap` for the inventory (the skill does this itself). |
| **Outbound-link export** (Screaming Frog / Sitebulb `All Outlinks` xlsx/csv) | Dim 1 instantly, at full-site scale | Fall back to live per-page fetch (`fetch_affiliate_links.py`). |
| **Affiliate networks in play** | Dim 1 classification | Auto-detect from outbound hosts; augment the config map. |
| **GSC access** (`account` + `sc-domain:` property) | revenue-weighting (Dims 1,9), review-page performance | Weight by a labelled traffic estimate; say "no GSC". |
| **DataForSEO** | review-page rankings/SERP; optional page fetch/parse | Use stdlib live fetch only. |
| **Tag-manager / attribution facts** | Dim 2 | Measure what's in the markup; list the rest as a client question. |
| **Affiliate dashboard export** (Fullscript/Amazon CSV) | Dim 2 click→sale reconciliation | Report clicks only; note the reconciliation gap. |
| **Prior deliverable** | before/after deltas (re-run) | Single-point-in-time run. |

Similar-but-different inputs (a different crawler's export, a GA4 outbound-click CSV, a
brand style guide, a screenshot of the affiliate dashboard) map to the nearest dimension
: fold them in, don't discard.

## The intake question to ask (one AskUserQuestion)
When inputs are missing, ask ONE structured question covering:
1. **Pages** : "Paste the review/money URLs, hand me a Screaming-Frog outbound-link
   export, or shall I crawl `<domain>/sitemap_index.xml`?"
2. **Networks** : "Which affiliate networks are in play (Fullscript, Amazon, …), or
   should I auto-detect from the links?"
3. **GSC** : "Which connected GSC account, and confirm the property is
   `sc-domain:<domain>`?"
4. **Tracking** : "Do you know the GTM container id(s) and whether an outbound-click
   event + sub-ID is configured? (If not, I'll measure the markup and flag the rest.)"
5. **Scope** : "Full 8-dimension audit, or a subset (e.g. link integrity + disclosure
   only)?"
Then proceed with whatever is available; list which dimensions build vs are dropped.

## Tool routing & credentials (all real, all pre-configured)
Credentials live in **`project `.env` / host environment variables`** and at the MCP layer. **No secret is ever read
into a report, a config, or a log.** `scripts/fetch_affiliate_links.py` loads
`project `.env` / host environment variables` with a tiny stdlib parser (there is **no** `python-dotenv` installed : 
do not import it) and uses the values only inside HTTP requests.

### Live page fetch : the forensic engine (`scripts/fetch_affiliate_links.py`)
- Python **stdlib + `requests` + `bs4`** (all confirmed present; `lxml` parser
  available). Fetches each URL, extracts every `<a href>`, classifies the network,
  HEAD/GET-checks each affiliate destination (follows redirects → records `final_url`),
  reads the `rel` attribute, and parses JSON-LD for `Review`/`Product`/`AggregateRating`.
- **`SCRAPINGBEE_KEY`** (from `.env`) : the anti-block / JS-render fallback: when a plain
  `requests` fetch is 403/429 or the outbound links are injected by JS, re-fetch through
  ScrapingBee (`https://app.scrapingbee.com/api/v1/` with `render_js=true`). Toggle with
  `config.apis.scrapingbee_fallback`.
- **Playwright MCP** (`mcp__plugin_playwright_playwright__*`) : alternative render path
  for a handful of JS-gated pages when ScrapingBee isn't desired.

### Google Search Console (`mcp__google-search-console__*`)
- Auth is at the **MCP layer** (OAuth). NOTE: `project `.env` / host environment variables` has `GSC_CLIENT_ID` +
  `GSC_CLIENT_SECRET` but **`GSC_REFRESH_TOKEN` is currently empty**, so a direct
  refresh-token API path is NOT available : use the MCP; if it returns unauthorized,
  ask the user to connect the property (never paste tokens).
- Pass an explicit **`account`** on every call or it errors "Multiple accounts found"
  (this account family has used `"business"` : confirm per client).
- Prefer the **domain** property `sc-domain:<domain>`.
- Pull: `query_search_analytics` (by page, 90d : clicks/impr for revenue-weighting),
  `get_top_pages`, `inspect_url`. Exact values only; never estimate what GSC gives.

### DataForSEO (`mcp__dataforseo__*`) : creds `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`
- `on_page_instant_pages` / `on_page_content_parsing` : server-side fetch + parse of a
  page (links, headings, schema) when you want a second opinion vs the local fetch.
- `dataforseo_labs_google_ranked_keywords` / `serp_organic_live_advanced` : what each
  review page ranks for and who else ranks (review-SERP competitor read).

### Microsoft Clarity (`mcp__clarity__*`) : optional, off by default
- **VERIFY the project is THIS client's domain first** (run a small query, check the
  returned URLs). Connected Clarity is frequently a *different* client : on mismatch,
  record a data gap and do NOT use it.

### File I/O (local filesystem tools)
- For reading client exports and writing outputs under `~/Downloads`, where sandboxed
  Bash `cat`/`ls` is TCC-blocked. `read_file` parses XLSX→rows; `write_file` does not
  trip the fact-forcing gate; `move_file` sends to Trash (never hard-delete).

### Web verification (`WebFetch` / `WebSearch`) : no credential
- Live-verify a claim, fetch the FTC disclosure guidance for the fix wording, and sanity-
  check a network's current redirect behavior.

### Not used / auth-gated (do not fake)
- `AHREFS_API_KEY` / `SEMRUSH_API_KEY` exist in `.env` but are **currently empty** : so
  the separate `seo-off-page-audit` skill leans on **DataForSEO backlinks** + client-supplied
  Ahrefs/Semrush CSV exports, not a direct Ahrefs/Semrush API call, and not this skill. `VALUESERP_API_KEY` / `PAGESPEED_API_KEY` /
  `GEMINI_API_KEY` / `OPENAI_API_KEY` exist but this skill does not require them : review
  voice (Dim 4) is **Claude-native** (Claude reads and judges the copy directly). If a
  huge library needs batch pre-scoring, GEMINI/OPENAI may accelerate it, but the default
  path uses no external LLM API.

## Config mapping
Copy `config.template.json` and fill: `client`, `domain`, `period`, `output_dir`;
`inputs.review_pages` (or `inputs.sitemap`, or `inputs.outbound_link_export`);
`inputs.gsc_account` + `inputs.gsc_property`; `inputs.affiliate_dashboard_export`
(optional); `taxonomy.affiliate_networks` (seed map; auto-detect augments it),
`taxonomy.required_rel`, `taxonomy.review_url_pattern`, `taxonomy.disclosure_markers`;
`apis.*` toggles; `brand` (defaults to Bijay credit).
