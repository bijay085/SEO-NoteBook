# Input manifest — what to ask for, what it unlocks, how it is read

Every input is optional except the logs themselves. Missing inputs drop a dimension;
they never block the run. Ask for everything in ONE structured question at intake.

## 1. The log files (REQUIRED)

| Format | Looks like | Detected as | Notes |
|---|---|---|---|
| Apache/nginx combined | `1.2.3.4 - - [01/Aug/2026:10:00:00 +0000] "GET /x HTTP/1.1" 200 5120 "-" "UA"` | `bracket` | The default. Full fidelity: IP, time, method, URL, status, bytes, referrer, UA. |
| IIS W3C | `#Fields:` header then space-delimited rows | `iis` | Reads the `#Fields:` line; falls back to the standard field order. UA has `+` for spaces. |
| JSON / Cloudflare Logpush | one JSON object per line | `json` | Accepts `uri`/`url`/`ClientRequestURI`, `status`/`EdgeResponseStatus`, etc. |
| Cloudways PHP-FPM | 3 lines per request: timestamp / IP / request | `cloudways_fpm` | **No User-Agent.** Bots identified by verified IP only — say so on the cover. |
| Aggregated CSV/TSV | a crawl/bot-hits export with URL + status + hits columns | `csv` / `tsv` | Each row expands to `hits` synthetic requests, capped at 1,000 per row. |

Compression: `.gz`, `.bz2`, `.xz` open transparently. `--logs` accepts files,
directories (walked recursively) and globs.

**Window**: 7 days minimum, 30 days ideal. Under 48h the engine automatically drops
crawl-rate findings to Low confidence — do not argue with it.

**File naming drives log-role routing** (`infer_log_role`):
`*error*` → error log, never traffic. `backend_*.access.log` → Cloudways backend
(primary). `php-app.access*` → Cloudways PHP (supplemental). `static_*.access.log` →
Cloudways static (supplemental). Anything else with `access` → standard access log.
If the client renamed their files, ask before trusting the routing.

## 2. Sitemap XML (optional, high value)
Unlocks dimension 7: which sitemap URLs were never crawled in this window.
Pass `--sitemap ./sitemap.xml`. A saved `sitemap_index.xml` works; if the sitemap is
split, concatenate the children or pass the file that actually contains `<loc>` entries.

## 3. GSC Pages export (optional, high value)
Unlocks the other half of dimension 7: pages earning impressions that Googlebot did not
revisit in this window — ranking on an increasingly stale copy.
Pass `--gsc-csv ./pages.csv`. Any column order; the reader finds the URL column
(`page`/`url`/`address`) and the impressions column by name.

## 4. Context questions (no file needed)
- **CDN in front?** Cloudflare/Fastly serving cache means the origin log shows only
  misses. Volume claims must be qualified.
- **Staging or production?** A staging log will show near-zero Googlebot and is not a
  crawl-health signal.
- **Any recent migration, block or robots.txt change?** It explains step changes in the
  Crawl Trend tab.

## Tool routing
- **No API keys are needed at runtime.**
- Network: only the public bot IP range files (Google, Bing, DuckDuckGo, Apple, OpenAI,
  Ahrefs), cached 7 days in `<workspace>/.cache/seo-log-file-analysis/`. `--offline` uses
  the cache alone; the report discloses per-source status either way.
- Reading client files under `~/Downloads` may be TCC-blocked for Bash — use
  local filesystem tools in that case.
- `mcp__google-search-console__*` is optional context for dimension 7 if no CSV export
  is supplied.
