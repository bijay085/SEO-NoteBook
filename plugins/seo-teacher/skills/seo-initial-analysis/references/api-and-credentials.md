# APIs & Credentials

Every data source is a **pre-configured MCP server** — no API keys, tokens, or
secrets live in this skill or in any client `config.json`. The `config.apis` block
only toggles which sources a run may use. If a server is disconnected or not
authorized, that source degrades gracefully and the run continues with a labelled gap.

## The engine — DataForSEO (`mcp__dataforseo__*`)
The keyword + SERP + competitor engine, plus the Baseline Snapshot's backlink /
Lighthouse / ranking / GBP pulls. Credential: the DataForSEO MCP server
(login / password configured once at the MCP layer). Tools used:
- `dataforseo_labs_google_keyword_ideas` / `google_keyword_suggestions` /
  `google_related_keywords` — expand each EAV seed into the long tail.
- `dataforseo_labs_google_keyword_overview` / `kw_data_google_ads_search_volume` —
  attach search volume + CPC.
- `dataforseo_labs_bulk_keyword_difficulty` — KD per keyword.
- `serp_organic_live_advanced` — the live SERP for intent + who ranks.
- `dataforseo_labs_google_competitors_domain` / `google_ranked_keywords` /
  `google_domain_rank_overview` — competitor teardown (Report 6).
- `dataforseo_labs_search_intent` — intent classification for clustering.
Save each raw response to `engine-run/raw/<seed>.json`; `cluster_keywords.py` reads them.

### Baseline Snapshot tools (Report 10, `scripts/baseline_metrics.py`)
- `backlinks_summary` (aggregate totals) + `backlinks_referring_domains` (per-domain
  list, paginate/limit as needed) + `backlinks_bulk_spam_score` (feed it the domain
  list from the previous call — it's a two-step sequential pull, not parallel).
  Categorization uses **DataForSEO's own 0–1000 domain-rank score**, not Ahrefs DR —
  don't relabel it as DR in a client-facing report. Spam threshold and "possible
  link farm" grouping are practitioner conventions (Interpretation-basis), not a
  DataForSEO-certified verdict — the script surfaces flagged domains, a human
  confirms the pattern before calling it a link farm.
- `on_page_lighthouse` on the homepage/primary URL — Lighthouse **lab** scores +
  Core Web Vitals (LCP, CLS, TBT, Speed Index). This is lab data only; it does not
  include INP, which is a field metric (needs real-user CrUX data this MCP
  connection has no source for) — recorded as "not available" rather than
  estimated or substituted with TBT.
- `dataforseo_labs_google_ranked_keywords` — full ranked-keyword list with
  position, bucketed by the script into top 3/5/10/50/100 tiers.
  `dataforseo_labs_google_domain_rank_overview` may return a pre-aggregated
  distribution too; cross-check against it if the tiers look off.
- `business_data_business_listings_search` — searched by business name +
  location (not a direct lookup by known listing ID); returns claimed status,
  rating, review count, category, address, phone for the matched listing.
Save each raw response to `engine-run/raw-baseline/<name>.json` — filenames are
fixed, see `baseline_metrics.py`'s own docstring.

## Google Search Console (`mcp__google-search-console__*`) — optional
Real first-party performance, when the client's property is connected. Credential:
the GSC MCP OAuth (per Google account). Set `config.apis.gsc_account`. Tools:
`list_sites`, `query_search_analytics`, `get_top_pages`, `find_keyword_opportunities`,
`query_by_search_type`, `inspect_url`. **Never estimate what GSC can give exactly** —
pull the real months. New sites (thin history) → note it and lean on DataForSEO demand.

For the Baseline Snapshot: `query_search_analytics` with `dimensions=["query"]` and
`dimensions=["page"]`, once for the ~16-month window (roughly GSC's own retention
ceiling — pull everything available, don't pick an arbitrary start date) and once
for the last ~3 months. Save all four responses (`gsc-16mo-query.json`,
`gsc-16mo-page.json`, `gsc-3mo-query.json`, `gsc-3mo-page.json`) —
`baseline_metrics.py` computes the deltas itself, no separate `compare_performance`
call needed.

## Wikipedia + Wikidata (WebFetch) — the KG anchor
No credential. Fetch the entity's Wikipedia article and Wikidata item (`Qxxxxx`) to
anchor Report 3's relationships (`instance of`, `subclass of`, `part of`, `practiced
by`). These are the *database* for the EAV — the user supplies the two URLs, or you
find them from the entity name.

## Web verification (`WebFetch` / `WebSearch`) — live truth
No credential. Used to fetch the live client site + sitemap, verify given claims (pages
live, review counts), and run the live competitor teardown. This is the "verify, don't
trust" layer — always run it before asserting a client-given figure.

## Microsoft Clarity (`mcp__clarity__*`) — optional behavior
Behavioral analytics (heatmaps, session stats) when connected. Credential: the Clarity
MCP. Off by default (`config.apis.clarity`); use it to ground UX / CRO notes in Report 8
if the client runs Clarity on their site.

## Desktop Commander (local filesystem tools) — file I/O
The file layer for everything under `~/Downloads`, where sandboxed Bash `cat`/`ls`/`head`
is TCC-blocked. Credential: Full Disk Access granted to the DC host app. Use `read_file`
(parses XLSX → JSON rows), `write_file` (chunk ≤30 lines; does **not** trip the GateGuard
fact-forcing hook, unlike native Write), `list_directory`, `move_file` (to Trash, never
hard-delete).

## Credential hygiene
- No secret is ever written into a report, a config, a log, or a commit.
- If a needed MCP server is unauthorized, tell the user to authorize it (host MCP /
  connectors → connector settings; other servers → `claude mcp` / `/mcp` in an
  interactive session) and mark the dependent report "pending <source>". Never ask the
  user to paste tokens or codes.
- Prohibited actions (entering credentials into sites, purchases, publishing) are never
  performed by the skill — it produces analysis; the human acts.
