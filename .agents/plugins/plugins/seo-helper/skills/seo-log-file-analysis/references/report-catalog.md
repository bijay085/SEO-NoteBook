# Report catalog : the 8 dimensions, what fills them, and when to drop one

Section ids match `scripts/report_data.py`. The engine's `category` field routes each
finding to a section; the mapping is in that file's docstring.

## 0 · Crawl Summary (`summary`)
**Fills from** `analysis.json ▸ meta` + `segments`.
Volume, window and span, parse rate, unique URLs, the six-segment mix, and the
verified-bot coverage line. Chart: requests by segment (hbars).
**Always include.** This is where the caveats live : parse rate, CDN, missing UA field,
short window. Never drop it.

## 1 · HTTP Errors (`errors`)
**Fills from** findings with category `HTTP Errors`.
404s and 5xx per URL, each labelled by whether a verified Googlebot received it.
**Drop when** zero error findings : replace with a `good` finding quoting the 404 and
5xx rates from the health scorecard.

## 2 · Redirects & Chains (`redirects`)
**Fills from** category `Redirects`.
Persistent 301 crawling (stale internal links), 302s on content URLs, multi-hop chains.
**Drop the chain part** when referrer coverage was under 20% : and say why.

## 3 · Crawl Budget Waste (`budget`)
**Fills from** category `Crawl Budget`.
Backend/admin endpoints being crawled, URL parameter explosion, static-asset ratio,
low-value taxonomy pages, high internal (infra) traffic.
**Frame by site size** : see methodology §6. On a small site this is hygiene.

## 4 · Indexability & Discovery (`indexability`)
**Fills from** category `Indexability`.
robots.txt and sitemap status health, trailing-slash duplicates, the Googlebot
mobile-first split, overall Googlebot share.
**Always include** : even when clean, the robots.txt/sitemap status is worth stating.

## 5 · Performance (`performance`)
**Fills from** category `Performance` + `content_types`.
Average served response weight per HTML URL, from the bytes the server actually wrote.
**Drop when** the log format carries no byte size (Cloudways FPM, most CSV exports) : 
say that in one line rather than leaving an empty section.

## 6 · Security & Suspicious Traffic (`security`)
**Fills from** categories `Security` and `Security / Spam`.
Sensitive-file exposure (200 = active breach) or probing (403/404 = reconnaissance), and
high-volume IPs that survived the admin-URL gate.
**Never soften an exposure finding.** A `.env` served 200 means credentials are already
assumed stolen; the action is rotation, not just a block.

## 7 · Crawl Coverage (`coverage`)
**Fills from** `analysis.json ▸ crossref`.
Sitemap URLs never crawled in this window (discovery gap); GSC pages with impressions but
no crawl (stale-copy risk).
**Drop entirely** when neither `--sitemap` nor `--gsc-csv` was supplied. Ship the
`note` caveat with every claim here.

## 8 · Action Items (`actions`)
**Authored, not emitted.** One row per fix, ordered P0 → P2, each with an owner and the
verification step. P0 is reserved for crawl-halting and exposure (methodology §5).
Consolidate: fifteen 404 findings become one "restore or redirect the 15 URLs listed in
the URL Detail tab" action, not fifteen rows.

## XLSX-only tabs (measured, appended by `build_data_tabs.py`)
Health Scorecard · Traffic Breakdown (+ top agents) · URL Detail · Bot Crawl Detail ·
Crawl Trend · Log Sources · Crawl Coverage · Decision Guide.
They render only when the underlying data exists : an empty tab is never created.
