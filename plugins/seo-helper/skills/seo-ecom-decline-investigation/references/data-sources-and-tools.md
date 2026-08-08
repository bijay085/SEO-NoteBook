# Data sources & tool routing : verified, not assumed

Referenced from `SKILL.md`. Every tool and credential named below was confirmed present in the
environment this skill was built in (2026-08-01) : either by direct successful use during the source
investigation, or by confirming its presence in `project `.env` / host environment variables` / the connected MCP server list.
**Re-verify at the start of a new run** : a future environment may have different tools connected;
if something below isn't available, say so and ask rather than assuming it still works.

---

## Tier 1 : verified by direct use in the source investigation

These were called successfully and repeatedly during the investigation this skill generalizes from.
Use these first; they are the backbone of Phases 2 to 4.

### Google Search Console (`mcp__google-search-console__*`)
- `list_sites` : lists every property across every connected account. **Run this first** if unsure of
  the property URL or whether multiple accounts exist.
- `query_search_analytics` : the core data-pull. Params: `siteUrl`, `account` (**required** the moment
  `list_sites` shows more than one account : omitting it errors "Multiple accounts found"),
  `startDate`/`endDate` (ISO `YYYY-MM-DD`), `dimensions` (array: `date`, `query`, `page`, `country`,
  `device`, or combinations), `rowLimit` (the live API can page well past the ~1,000-row cap of a
  UI-exported CSV : use this when the query/page tail matters for Phase 3 test #1).
- `inspect_url` : live index-coverage + rich-result status for a single URL. Useful in Phase 5/6 to
  confirm a page is actually indexed (not just ranking in a stale export) before making an indexation
  recommendation.
- Also available on this server: `list_accounts`, `compare_performance`, `export_analytics`,
  `find_keyword_opportunities`, `get_keyword_trend`, `get_top_pages`, `list_sitemaps`,
  `query_by_search_appearance`, `query_by_search_type`, `analyze_brand_queries`. Load schemas via
  `ToolSearch` if deferred before calling.

### WebSearch
Used in Phase 4 to cross-reference a detected changepoint date against the public Google algorithm
update calendar (Search Engine Land, Search Engine Journal, Google's own status dashboard all index
update rollout windows with start/end dates). A working search with a date-scoped query
(`"Google [month] [year] update rollout dates"`) is sufficient : no special API needed beyond the
standard `WebSearch` tool.

### Bash + Python (pandas, numpy, scipy, statsmodels, openpyxl, Pillow, requests)
The statistical engine (`scripts/period_decomposition.py`) and the branded report builder
(`scripts/report_helpers.py`) both depend on this stack.

**Environment gotcha, confirmed real:** the system Python in this environment is externally-managed
(PEP 668) : `pip install <pkg>` at the system level fails with
`error: externally-managed-environment`. `scipy` and `statsmodels` in particular are not preinstalled.
**Fix:** build an isolated venv first : see `scripts/setup_env.sh`. It uses `--only-binary=:all:` to
avoid slow/failing source compiles, and installs into a project-local `.venv` rather than touching the
system interpreter.

### Read / Grep / Glob / Bash (source-code + live-page audit)
Used for the live HTML page audit (Phase 5) and the backend/architecture audit (Phase 5, if source is
provided). Standard file tools : no special credential needed. For a *live* page fetch (not saved
HTML), use `WebFetch` or `curl` via Bash; save the raw HTML locally before running
`scripts/live_page_audit.py` against it so the audit is reproducible.

### Agent tool (general-purpose subagent)
Dispatch a subagent for large-file reads that would otherwise consume excessive context : e.g. a
5,000-line rendered HTML page, or comparing two large template files line-by-line. Give it the specific
file path(s) and the exact checks to run (see `scripts/live_page_audit.py`'s check list for what to ask
for); it should return findings, not the raw file content.

---

## Tier 2 : confirmed connected, not directly exercised in the source investigation

These MCP servers/tools were confirmed present (listed in this environment's tool inventory) but were
not the ones actually called during the source run. Treat them as a real, available **enhancement path**
per `SKILL.md`'s "Filling gaps live" section : not a first resort, and verify the specific tool schema
via `ToolSearch` before calling (`mcp__dataforseo__*` tools are deferred by default).

### DataForSEO (`mcp__dataforseo__*`)
Configured via `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` in `project `.env` / host environment variables`. Relevant tools for this
skill, by phase:
- **Phase 4 (changepoint corroboration):** `dataforseo_labs_google_historical_rank_overview`,
  `dataforseo_labs_google_historical_serps` : an independent ranking-history source to corroborate a
  GSC-derived changepoint date.
- **Phase 5 (live SERP check):** `serp_organic_live_advanced` : automates what was done manually in
  the source investigation (a human live-checking Google SERP position for a specific query). Prefer
  this over asking the user to manually check when the tool is available.
- **Phase 5 (duplication measurement):** `content_analysis_search`, `content_analysis_summary` : can
  quantify near-duplicate content across a set of URLs, as an alternative/supplement to a manual
  `diff` on source templates.
- **Phase 5 (performance):** `on_page_lighthouse` : runs on the **desktop** profile; label it as such
  in any report, since Google's ranking basis is mobile. For mobile Core Web Vitals, use
  `PAGESPEED_API_KEY` directly (Tier 3).
- **Phase 6/backlink cross-check (optional):** `backlinks_summary`,
  `backlinks_timeseries_new_lost_summary` : if a link-loss hypothesis needs testing, a timeseries dip
  in referring domains around the changepoint date is corroborating evidence.
- The server also exposes SERP, keyword-volume, Amazon/merchant, and YouTube endpoints not relevant to
  this skill : do not reach for them here.

---

## Tier 3 : configured credentials, direct API call (not MCP-wrapped in this environment)

These keys exist in `project `.env` / host environment variables` but were **not verified via a wrapping MCP tool** in the source
investigation. If needed, call them directly over HTTP (e.g. via Bash + `curl`/Python `requests`) using
the exact key name below : never invent an MCP tool name for these.

| Key | Use case in this skill |
|---|---|
| `PAGESPEED_API_KEY` | Mobile Core Web Vitals, as a complement to DataForSEO's desktop-only Lighthouse (Phase 5) |
| `VALUESERP_API_KEY` | Alternative live-SERP-position check if DataForSEO's `serp_organic_live_advanced` isn't enabled for this engagement |
| `SCRAPINGBEE_KEY` | Rendering a JS-heavy page that a plain fetch can't capture (Phase 5 live-page audit, if the site is React/Vue-rendered) |
| `AHREFS_API_KEY` | Independent backlink/authority cross-check, alternative to DataForSEO's backlinks endpoints |
| `SEMRUSH_API_KEY` | Independent traffic/ranking estimate cross-check |

Before using any of these, confirm the key is actually present and non-empty in `project `.env` / host environment variables` for
**this** environment : do not assume it carries over from the source build.

---

## Explicitly NOT used for reasoning : present but out of scope

`GEMINI_API_KEY` and `OPENAI_API_KEY` are present in `project `.env` / host environment variables` for unrelated tooling in this
environment. **Do not call either for any part of this skill's analysis, decomposition, or authoring.**
Per the user requirement this skill was built under: the session runs on a Claude subscription plan,
and Claude's own native reasoning does all interpretation : there is no reason to pay for or route
through a second LLM API mid-workflow. If a future variant of this skill is tempted to add an "LLM
judge" or "AI summarizer" sub-step using one of these keys, that is a scope violation : flag it and
ask before adding it.

---

## Multi-account GSC gotcha (repeats every run)

If `list_sites` returns more than one account block, **every** subsequent `query_search_analytics` /
`inspect_url` call on that property needs the `account` parameter set to match, or it throws
`"Multiple accounts found : specify an account"`. This is not a one-time setup step; it applies to
every call for the life of the investigation.
