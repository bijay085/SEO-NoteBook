# Input Manifest & Tool Routing

What the audit needs, what to request when it's missing, and the exact
tool/MCP routing (with the gotchas that cost real time). The audit **degrades
gracefully** — a missing source drops its section and is noted on the cover; it
never blocks the run.

## Required (need at least the page fetch)
| Input | Feeds | Notes |
|---|---|---|
| **Domain + page inventory** | everything | The exact money/service URLs + location URLs, OR permission to crawl the sitemap to discover them. This is the one hard requirement — the live fetch is the spine. |

## Strongly recommended (each adds a whole section)
| Input | Feeds | Notes |
|---|---|---|
| **GSC access** | Dimension 1 (Live Search Performance) | The connected account + property (`sc-domain:<domain>`). Turns the audit from inferred to proven. |
| **DataForSEO (or PSI)** | Dimension 2 (Lighthouse/CWV), rankings, backlinks | Lighthouse scores + CWV; keyword volume; SERP. |
| **Microsoft Clarity (client-owned)** | CRO behavioural layer | ONLY if verified as this client's project (see below). |
| **Prior deliverables** | before/after deltas | The foundational/setup docs to diff against. |

## The intake question to ask
When inputs are missing, ask ONE structured question (AskUserQuestion) covering:
1. **Page inventory** — "Paste the money/service + location URLs, or shall I crawl
   `<domain>/sitemap_index.xml`?"
2. **GSC** — "Which connected GSC account, and confirm the property is
   `sc-domain:<domain>`?"
3. **Clarity** — "Is there a Microsoft Clarity project for `<domain>`? (I will
   verify it returns `<domain>` data before using it.)"
4. **Scope** — "Full 10-dimension audit, or a subset (e.g. technical + Lighthouse
   only)?"
Then proceed with whatever is available; list which dimensions will build vs be
dropped.

## Tool routing & gotchas
### Google Search Console (`mcp__google-search-console__*`)
- Pass an explicit **`account`** param on every call, or you get
  "Multiple accounts found". (For this account family the value has been
  `"business"`; confirm per client.)
- Use the **domain** property `sc-domain:<domain>` over a URL-prefix duplicate.
- Pull: `query_search_analytics` (by page, by query, 90d), `get_top_pages`,
  `list_sitemaps` (status/errors), `inspect_url`. Use **exact** values, never
  estimate. Find duplicate URLs by scanning page rows for two paths, one intent.

### Lighthouse (`mcp__dataforseo__on_page_lighthouse`)
- Set `enable_javascript: true`. `full_data: false` returns the category scores +
  core metric numericValues (enough for the scorecard) without a huge payload.
- **It runs the DESKTOP profile** (`formFactor: desktop`, ~10 Mbps, 1x CPU). Label
  every score "desktop". For mobile CWV, run PageSpeed Insights separately.
- Capture per page: performance / accessibility / seo / best-practices scores, and
  first-contentful-paint, largest-contentful-paint, cumulative-layout-shift,
  speed-index, server-response-time, total-byte-weight.

### Microsoft Clarity (`mcp__clarity__*`)
- **VERIFY the project first.** Run a small query and check the returned URLs are
  `<domain>`. Connected Clarity projects are frequently a DIFFERENT client — if the
  data is another domain (or `about:blank`), record a data gap and do NOT use it.

### Live page fetch (the forensic engine — no external API)
- `scripts/fetch_pages.py` uses Python stdlib + `requests` to fetch each URL and
  compute the metrics. It is niche-agnostic; configure tracker patterns and the
  money/location URL patterns in `config.json` `taxonomy`.

### Auth-gated (interactive OAuth — often unavailable headless)
- Ahrefs, SimilarWeb, GBP/local-pack, a client-owned Clarity, GA4. If one is
  needed and not connected, tell the user to connect it (host MCP connectors or
  `claude mcp`) and mark that dimension pending — don't fake it.

## Config mapping
Copy `config.template.json` and fill:
- `client`, `domain`, `period`, `output_dir`.
- `inputs.money_pages` / `inputs.location_pages` (arrays of URLs) or
  `inputs.sitemap` (to crawl).
- `inputs.gsc_account`, `inputs.gsc_property`.
- `inputs.clarity_project` (+ the expected domain to verify against).
- `taxonomy.tracker_patterns` (regex/substrings to count, e.g. a CallRail swap.js),
  `taxonomy.money_url_pattern`, `taxonomy.location_url_pattern`.
- `brand` (defaults to Bijay credit).
