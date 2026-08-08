---
name: seo-affiliate-and-review-audit
description: >-
  Run a standalone, config-driven audit of an AFFILIATE + REVIEW-content site : the
  two things that actually make a review site money: the outbound affiliate money-path
  (are the links alive, correctly tagged, tracked, and disclosed?) and the review
  content itself (is the voice right for each archetype, is the scoring scoped to real
  reviews, is Review/Product schema valid and not self-serving?). Produces a branded
  SEO deliverable (deep HTML report + master XLSX) with measured evidence and a
  prioritized fix plan. Use whenever the user wants an "affiliate audit", "affiliate
  link audit / check my affiliate links", "rel=sponsored / nofollow compliance",
  "affiliate revenue leak", "FTC affiliate disclosure audit", "review site audit",
  "product review audit", "review schema / AggregateRating check", "is my Fuel-Score /
  rating system set up right", or a "monetization audit" of a site that earns from
  Fullscript / Amazon / ShareASale / Impact / CJ / practitioner-dispensary or similar
  affiliate links. Industry- and network-agnostic; config-driven so it works for ANY
  affiliate/review client. Requests missing access (page list, outbound-link export,
  GSC, DataForSEO) before running, and can crawl/query live to fill gaps. Reuse
  built-in report branding (brand_lib / report_kit) for styling.
---

# Affiliate & Review-Site Audit

A repeatable, config-driven **deep audit** for the business model where the revenue is
an **outbound affiliate link** and the asset is **review content**. It answers the two
questions that decide whether such a site earns: *"Is the money path intact : every
affiliate link alive, correctly tagged, tracked, and disclosed?"* and *"Is the review
content trustworthy : the right voice per archetype, a rating system scoped to genuine
reviews, and Review/Product schema that helps rather than triggers a manual action?"*
It produces the SEO deliverable as one branded HTML document plus a master XLSX.

It is the **monetization sibling** of `seo-after-foundational-setup-audit`. That skill
tears a page down technically (weight, DOM, duplication, CWV, on-page/schema); **this**
one follows the dollar : the affiliate link out and the review that earns the click : 
and audits FTC/E-E-A-T compliance a page-forensic pass never looks at. Run either
alone, or this one for the revenue path and the forensic one for the page mechanics.

Every claim is **measured, not assumed** : the actual `rel` string on the link, the
real HTTP status of the destination, the verbatim disclosure sentence (or its absence),
the JSON-LD `@type` stack. If a number can't be measured, it's a labelled data gap,
never invented.

## When to use
- A site earns from **outbound affiliate links** and/or **product-review content** and
  needs the money path + review quality audited.
- The user asks: *audit my affiliate links / are they tagged `sponsored nofollow` /
  which are dead*; *is my FTC disclosure compliant*; *review-site / product-review
  audit*; *is my rating (Fuel-Score) system / Review schema set up correctly*;
  *monetization audit*; *why isn't the affiliate revenue growing*.
- The user drops a domain, a page list, or a Screaming-Frog **outbound-link export**
  and wants the revenue path torn down link by link into a client-ready report.
- A prior affiliate/review audit needs re-running on the **current** live state to
  measure what got fixed (e.g. did the missing `rel` tags actually get applied?).

## Required access : request it before running (do not guess)
This audit is only as good as its inputs. At intake, check what's available and **ask
the user for anything missing** via one structured question : then proceed with what
you have, degrading gracefully (a missing source drops its dimension and is flagged; it
never blocks the run). The skill can also **fill gaps itself**: crawl the sitemap for
the page list, pull GSC for which review pages earn, fetch each page live to inventory
links. See `references/input-manifest.md` for the full intake spec and the exact
question to ask.

Ask for, at minimum:
1. **Domain + the page inventory** : the money/review URLs (or permission to crawl the
   sitemap), OR a Screaming-Frog / crawler **outbound-link export** (unlocks the link
   inventory instantly : this is the highest-value custom input).
2. **Affiliate networks in play** : Fullscript, Amazon Associates, ShareASale, Impact,
   CJ, Wellevate (legacy), iHerb, etc. : or let the skill **auto-detect** them from the
   outbound-link hosts.
3. **Google Search Console** : which connected account + property (`sc-domain:<domain>`)
   so revenue-weighting uses real clicks/impressions on the review pages. Pass the
   `account` param or GSC errors "Multiple accounts found."
4. **DataForSEO** : for review-page rankings/SERP and (optional) live page fetch/parse.
5. **Tracking/attribution facts** : the tag-manager container id(s) and whether an
   outbound-click event + sub-ID/UTM is configured (attribution is off-domain : see
   Methodology). If unknown, the skill measures what's in the page markup and flags the
   rest as a client question.
6. **Branding** : defaults to Bijay credit; confirm client name + period for the cover.

Auth-gated connectors (a client-owned Clarity, GA4, GBP) need interactive OAuth an
automation session can't run : if one is needed and not connected, tell the user to
connect it and mark that dimension pending. **Never** ask the user to paste tokens.

## The deliverable
1. **`<Client>_<Period>_Affiliate-Review-Audit.html`** : one branded document: header,
   sticky grouped nav, a hub-card contents grid, then every dimension, each with
   measured evidence, inline SVG charts, and collapsible per-page / per-link tear-downs.
2. **`<Client>_<Period>_Affiliate-Review-Audit.xlsx`** : Overview (stat cards + tab
   index + exec summary) + one tab per dimension + a full **Affiliate-Link Inventory**
   tab (every outbound money link: page, anchor, destination, network, HTTP status,
   `rel`, verdict) + an Action-Items tab (Issue · Evidence · Solution · Execution ·
   Effort · Priority).
Both use SEO report branding. Keep the two formats at **parity** : a new measured layer
goes into both.

## How it works (the loop)
A **hybrid**: deterministic Python fetches the pages, inventories every outbound link,
classifies the network, checks each destination's HTTP status + `rel`, and parses the
review schema; **you (Claude) author the findings** : the interpretation, the fix, and
the executable step : grounded in those measured numbers. A script crawls links
identically every time; only you can judge that a "review" reads like an AI-flat
summary with no first-hand testing.

```
1. INTAKE → load config.json; confirm inputs; REQUEST missing access (one question);
              offer to crawl/query for anything the user can't hand over
2. PULL → live page fetch → outbound-link inventory + status + rel + review schema
              (scripts/fetch_affiliate_links.py); GSC (real clicks/impr on review pages);
              DataForSEO (review-page rankings); read the review copy itself
3. ANALYZE → the 8 dimensions below, against measured data (never by eye)
4. AUTHOR → report_data.py: every finding = Issue · Evidence · Solution · Execution
5. BUILD → build_html.py + build_xlsx.py import report_data.py; render both, at parity
6. VALIDATE → balanced tags/tables, no unrendered placeholders, counts match, tab count
7. DELIVER → copy to the output folder, send both files, summarize honestly
8. MEMORY → save durable client facts (networks in play, the lead revenue leak)
```

## The 8 dimensions
See `references/report-catalog.md` for how to build each. In short:

| # | Dimension | Source | Mode |
|---|---|---|---|
| 1 | **Affiliate-Link Integrity** : inventory, network, HTTP status, `rel` tag | live fetch / outbound export | script+author |
| 2 | **Monetization Tracking & Attribution** : outbound-click event, tag-manager, sub-ID/UTM, duplicate GTM | live fetch + GSC/client | script+author |
| 3 | **FTC / Affiliate Disclosure** : presence, placement, proximity to first link | live fetch + read | author |
| 4 | **Review Voice (archetype-aware)** : classify archetype, audit voice against the RIGHT rubric; first-hand E-E-A-T signals | read (Claude-native) | **author** |
| 5 | **Rating / Score-System Scope** : is the score (e.g. Fuel Score) scoped to real reviews only, consistent, schema-backed | read + schema | author |
| 6 | **Review & Product Schema** : Review/Product/AggregateRating validity; self-serving-rating guard | live fetch | script+author |
| 7 | **Affiliate-CTA Conversion Path** : the money moment: CTA presence/position/mobile, global affiliate nav CTA | live fetch + read | author |
| 8 | **Action Items** : prioritized P0 to P2, executable, revenue-weighted | all of the above | author |

Scale to inputs: no outbound links found → 1 to 2 drop or go light; no review content →
4 to 6 drop; no GSC → revenue-weighting falls back to traffic estimate and says so. Always
include 1, 3, 6, 8 when the pages fetch.

## Author findings (the quality bar)
Every finding, in `report_data.py`, is a dict: **issue, sev, evidence, solution,
execution**. `evidence` is measured or verbatim (the actual `rel=""` string, the exact
HTTP status + final URL, a quoted disclosure sentence, the JSON-LD block). `execution`
is the literal steps + how to verify (e.g. *"View-Source the page; the link to
`fullscript.com/...` must read `rel=\"sponsored nofollow noopener\"`"*). Disclosure and
schema fixes are verbatim **Find ▸ Replace** drafts. Severity: Critical/High/Medium/Low,
plus Good/Info for confirmed strengths. See `references/methodology.md`.

## Methodology (the non-obvious rules)
Read `references/methodology.md` before authoring. Load-bearing:
- **`rel="sponsored"` is the correct tag for a monetized link** (Google, since 2019);
  `nofollow` alone is legacy-tolerated, `sponsored` is preferred, and `noopener` guards
  `target="_blank"`. A monetized link with no `rel` is a **link-scheme risk**, not a
  style nit.
- **An affiliate link is not every outbound link.** Classify by destination host +
  query-signature against the network map (`?tag=` = Amazon, dispensary subdomains =
  Fullscript, `shareasale.com/r.cfm`, `impact`/`cj` redirectors). Don't tag an
  editorial citation as monetized.
- **Dead / legacy-network links are silent revenue leaks.** Status-check every
  destination and follow redirects : a 301 into a login or a network's homepage is a
  **broken deep link earning $0** (e.g. Wellevate URLs after the Fullscript merger).
- **Attribution is off-domain** : the sale happens on the affiliate's site, so on-site
  analytics see the **click, not the sale**. Verify the outbound-click event fires and
  a sub-ID/UTM carries the source page, then reconcile against the affiliate dashboard.
  Duplicate tag-manager containers double-count : flag them.
- **Disclosure must sit above the first affiliate link, on the same page** (FTC 16 CFR
  255) : a footer-only disclosure is insufficient.
- **Voice is archetype-dependent** : a product review, a roundup, a how-to, and a
  personal-experience essay each have a different *correct* voice; never score them all
  on one rubric. The E-E-A-T signal Google's product-review system rewards is **genuine
  first-hand experience** (original testing, specific detail, own photos); its absence
  on a "review" is the real defect.
- **A rating system belongs on genuine reviews only** : applying a score to an
  informational post, or a self-assigned `AggregateRating` with no collected reviews,
  is a structured-data violation. Scope it; back it with real `Review` nodes.
- **Prioritize by revenue exposure** : a dead link or missing `rel` on the top-earning
  review page is P0; the same on a zero-traffic post is P2. Rank by traffic/revenue ×
  severity.

## Data sources & tool routing
`references/input-manifest.md` has the exact MCP/API calls and credential routing (all
**real**, all pre-configured): `mcp__dataforseo__*` (login/password from `project `.env` / host environment variables`
`DATAFORSEO_LOGIN`/`_PASSWORD`), `mcp__google-search-console__*` (GSC OAuth from the same
`.env`), `SCRAPINGBEE_KEY` for a rendered/anti-block fetch fallback, Playwright MCP for
JS-rendered outbound links, local filesystem tools for file I/O under `~/Downloads`,
WebFetch/WebSearch for live verification + the FTC reference. No secret is read into a
report or a config : the script loads project `.env` / host environment variables at runtime and uses the values in
requests only.

## Branding
Use SEO report branding for every output (see built-in report branding): Yellow
#F5C518, Black #0A0A0A, Dark #1A1A1A, Green #2ECC71, Red #E74C3C, Orange #E67E22, Blue
#3498DB; Arial (XLSX) / Inter (HTML). Header + workbook read **"<Client> · Affiliate &
Review Audit : <Period>"**. Text-only header (no logo).

## Guardrails
- **Never fabricate.** Every `rel`, status code, disclosure quote, and schema `@type`
  comes from a real fetch or parse. No data → labelled placeholder + say so.
- **Never present another client's data as this client's.** Verify any analytics
  project (Clarity/GA) domain first; on mismatch, flag a data gap.
- **Honesty over spin.** If the links are actually clean, say so (a "Good" finding) : 
  credibility is the product.
- **Degrade gracefully.** Missing source → drop its dimension, note it on the cover.
- **Parity.** Any new measured layer goes into both the HTML and the XLSX.
- **The skill produces analysis; the human acts.** It never enters credentials into a
  site, publishes, or edits the live site : it hands the client the exact fix.

## Output location
Write everything to `<output_dir>/` from config (default `./Affiliate-Review-Audit/`).
Keep intermediates (`*.json`, the builders) alongside; the two deliverables go in
`<output_dir>/`.
