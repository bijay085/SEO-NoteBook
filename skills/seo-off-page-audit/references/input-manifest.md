# Input Manifest & Tool Routing

What the audit needs, what to **request**, what it can **pull itself**, and the exact
tool/credential routing : all **real**. Degrades gracefully: a missing source drops its
dimension and is noted on the cover.

## Inputs are flexible : custom / similar / additional all welcome
The one hard requirement is a **domain** (so DataForSEO can pull the profile). Everything
else is optional and enriches. Custom exports are never rejected : a different tool's
backlink CSV, a GA4 referral export, a manual toxic list all map to the nearest
dimension.

| Input | Feeds | If missing |
|---|---|---|
| **Domain** | everything (live DataForSEO pull) | Hard requirement : ask for it. |
| **Ahrefs export** (referring domains / backlinks / DR) | Dims 1,2,3 corroboration | DataForSEO-only; toxic set drops to single-source "review". |
| **Semrush toxic / backlink-audit export** | Dim 3 (toxic intersection) | Same : fewer corroborating sources. |
| **Existing `disavow.txt`** | Dim 3 (net-new vs merged file) | Assume empty; all candidates are "new". |
| **Outbound external-links export** (Screaming Frog) | Dim 5 (equity leak / rel) | Crawl a sample live, or drop Dim 5. |
| **Competitors** | Dim 6 (link gap) | Drop Dim 6, or discover via DataForSEO `backlinks_competitors`. |
| **GSC manual-action status** | Dim 3 disavow gating (Methodology §1) | Ask explicitly : it decides P0 vs monitor. |

Similar-but-different inputs (a Moz/Majestic export, a hand-built toxic list, a GA4
referral CSV) are read and mapped to the closest dimension : fold them in, don't discard.

## The intake question to ask (one AskUserQuestion)
1. **Domain** : "Confirm the target domain (and www/non-www, http/https)."
2. **Exports** : "Do you have Ahrefs and/or Semrush backlink or toxic exports, and the
   current `disavow.txt`? (If not, I'll pull the profile live from DataForSEO.)"
3. **Manual action** : "Has Search Console reported a manual action / unnatural links?
   (This decides whether a disavow is warranted at all.)"
4. **Outbound + competitors** : "Want the outbound-equity check (give a crawl export or
   let me crawl) and a competitor link-gap (name 2 to 4 competitors)?"
5. **Scope** : "Full 7-dimension audit or a subset (e.g. toxic + disavow only)?"

## Tool routing & credentials (all real, all pre-configured)
Credentials live in **`project `.env` / host environment variables`** and at the MCP layer. No secret is read into a
report or log. `scripts/backlink_toxicity.py` loads `project `.env` / host environment variables` with a stdlib parser
(no `python-dotenv` : it is not installed).

### DataForSEO backlinks : the live engine (`mcp__dataforseo__backlinks_*`)
Creds `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` (both populated). Pull and save each raw
response to `<output_dir>/` as JSON for the merge script:
- `backlinks_summary` : totals, referring domains, dofollow/nofollow split, rank.
- `backlinks_referring_domains` : per-domain backlinks + rank (save as
  `dataforseo_referring_domains.json`; the merge script reads it).
- `backlinks_anchors` : anchor-text distribution (Dim 2).
- `backlinks_bulk_spam_score` : spam score per domain (Dim 3 primary signal).
- `backlinks_competitors` / `backlinks_domain_intersection` : link gap (Dim 6).
- `backlinks_bulk_new_lost_referring_domains` : velocity (Dim 1).

### Client CSV exports (local filesystem tools `read_file`)
Read Ahrefs / Semrush exports (CSV or XLSX) from `~/Downloads` (TCC-blocked for Bash).
Column hints the merge script auto-detects (case-insensitive, substring):
- **domain**: a header containing `domain`, `referring`, or `source url`.
- **Ahrefs toxicity**: `domain rating`/`dr` (low = weak) or an explicit toxicity column.
- **Semrush toxic**: `toxic score` / `toxicity`.
The script is tolerant of column-name drift; if it can't find a domain column it skips
that file and logs it (never guesses).

### Google Search Console (`mcp__google-search-console__*`) : optional
For the **manual-action** check and links-report context. Auth is at the MCP layer;
`project `.env` / host environment variables` `GSC_REFRESH_TOKEN` is **empty**, so use the MCP (pass `account`), and
if unauthorized ask the user to connect : never paste tokens.

### Outbound crawl
`requests` + `bs4` (both installed), a Screaming-Frog "external outlinks" export, or
`browser / Playwright / agent browse tools` / Playwright for JS-rendered pages. Classify each external
outbound link's `rel` for Dim 5.

### NOT available : do not fake
- **`AHREFS_API_KEY` / `SEMRUSH_API_KEY` are EMPTY in `.env`.** Do NOT call the Ahrefs or
  Semrush REST APIs : there is no working key. All Ahrefs/Semrush signal comes from the
  **client CSV exports**; all live backlink data comes from **DataForSEO**. The OAuth
  Ahrefs/Semrush MCP connectors are interactive-auth and unavailable headless.

## Config mapping
Copy `config.template.json`: `client`, `domain`, `period`, `output_dir`;
`inputs.ahrefs_export` / `semrush_toxic_export` / `existing_disavow` / `outbound_export`
/ `dataforseo_referring_domains_json` (paths); `inputs.competitors`; `taxonomy.toxic_thresholds`
(`dataforseo_spam_score`, `ahrefs_toxicity`, `semrush_toxic_score`, `min_sources_to_disavow`);
`taxonomy.branded_anchor_terms`, `taxonomy.internal_domains`; `apis.*`; `brand`.
