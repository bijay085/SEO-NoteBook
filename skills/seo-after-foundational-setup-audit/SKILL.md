---
name: seo-after-foundational-setup-audit
description: >-
  Run a comprehensive, per-page FORENSIC SEO + technical + content + performance
  audit of a live website after its foundational setup is complete, and produce a
  branded SEO deliverable (deep HTML report + master XLSX) with measured
  evidence and a prioritized fix plan. Use this whenever the user wants a "deep
  audit", "page-level audit", "technical + on-page audit", "money-page / service-
  page audit", "location-page audit", "content contamination / duplication check",
  "Core Web Vitals / Lighthouse audit", "authorship / E-E-A-T audit", "post-setup
  audit", "after foundational
  setup audit", or asks "what's still wrong / what's underperforming / what should
  we fix next" on a site that has already had its initial SEO foundation built.
  Every finding is measured (verbatim evidence + numbers) and carries Issue ·
  Evidence · Solution · Execution. Industry- and niche-agnostic; config-driven so
  it works for ANY client. Requests missing access (GSC, Clarity, page list,
  DataForSEO) before running. Reuse built-in report branding (brand_lib / report_kit) for styling.
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# After Foundational Setup Audit

A repeatable, config-driven **deep audit** that answers: *"The foundation is
built : now, page by page, what is actually wrong, what is underperforming, and
what do we fix first?"* It fetches every target page live, measures it, cross-
checks it against real Google Search Console + Lighthouse data, and produces the
SEO deliverable as one branded HTML document plus a master XLSX workbook.

It answers
"what is broken on the pages themselves" (technical, on-page, content, schema,
duplication, performance, CRO) : at per-page, per-section depth, with an
executable fix for every finding.

Every claim is **measured, not assumed** : verbatim quotes, exact byte/node
counts, real GSC clicks, real Lighthouse scores. If a number can't be measured,
it is flagged as a data gap, never invented.

## When to use
- A site has cleared its **foundational SEO setup** and needs a deep, page-level
  audit of what remains or what regressed.
- The user asks: *deep/page-level/technical/on-page audit*; *audit these money
  pages / location pages*; *find duplication or cloned content*; *run Lighthouse /
  Core Web Vitals*; *what's underperforming*; *what do we fix next*.
- The user drops a domain (and maybe a page list or prior deliverables) and wants
  it torn down page by page into a client-ready report.
- A prior deep audit needs re-running on the **current** live state to measure
  what got fixed.

## Required access : request it before running (do not guess)
This audit is only as good as its inputs. At intake, check what's available and
**ask the user for anything missing** via one structured question : then proceed
with what you have, degrading gracefully (a missing source drops its section and
is flagged, it never blocks the run). See `references/input-manifest.md`.

Ask for, at minimum:
1. **Site domain + the page inventory** : the exact money/service URLs and
   location URLs to audit (or permission to crawl the sitemap to discover them).
2. **Google Search Console access** : which connected account and the property
   (e.g. `sc-domain:<domain>`). GSC MCP calls often need an explicit `account`
   param or they error "Multiple accounts found" : confirm it. Without GSC the
   "Live Search Performance" section is dropped.
3. **Microsoft Clarity project** : and **verify it is THIS client's project**
   before using a single number (see Guardrails : the connected Clarity is often a
   *different* client). Without a verified client-owned project, behavioural data
   is marked "data gap", never faked.
4. **DataForSEO** (or equivalent) : for Lighthouse, backlinks, rankings,
   keyword/volume. Note its Lighthouse endpoint runs the **desktop** profile.
5. **Prior deliverables** (the foundational/setup docs) to diff against, if a
   before/after is wanted.
6. **Branding** : defaults to Bijay credit (see Branding); confirm client name +
   period for the cover.

Auth-gated connectors (Ahrefs, SimilarWeb, GBP, a client-owned Clarity) need an
interactive OAuth the automation session can't run : if one is needed and not
connected, tell the user to connect it and mark that dimension pending.

## The deliverable
1. **`<Client>_<Period>_Deep-Audit.html`** : one branded document: header, sticky
   grouped nav, a hub-card contents grid, then every analysis section, each with
   measured evidence, inline SVG charts, and collapsible per-page tear-downs.
2. **`<Client>_<Period>_Deep-Audit.xlsx`** : Overview (stat cards + tab index +
   exec summary) + one tab per analysis dimension + an Action-Items tab with
   Issue · Evidence · Solution · Executable step · Effort · Priority.
Both use SEO report branding. Keep the two formats at **parity** : a new measured
layer (e.g. Lighthouse) goes into *both*.

## How it works (the loop)
A **hybrid**: deterministic Python fetches + measures the pages and builds the
files; **you (Claude) author the findings** : the interpretation, the solution,
and the executable step : grounded in the measured numbers. A script crunches the
DOM/CSS/schema identically every time; only you can judge that a "Panel" heading
was cloned onto an Opener page.

```
1. INTAKE → load config.json; confirm inputs; REQUEST missing access (one question)
2. PULL → GSC (real clicks/impr/CTR/pos, sitemaps, cannibalization),
               Lighthouse (scores + CWV), Clarity (VERIFY project first),
               live page fetch → forensic metrics (scripts/fetch_pages.py)
3. ANALYZE → the 11 dimensions below, against measured data (never by eye)
4. AUTHOR → report_data.py: every finding = Issue · Evidence · Solution · Execution
5. BUILD → build_html.py + build_xlsx.py import report_data.py; render both, at parity
6. VALIDATE → balanced tags/tables, no unrendered placeholders, counts match, tab count
7. DELIVER → copy to the output folder, send both files, summarize honestly
8. MEMORY → save durable client facts (data-source routing, the lead finding)
```

### Step 1 : Intake & request
Load `config.json` (copy `config.template.json`). Resolve the page inventory and
each data source. Report what's present vs missing and **ask for missing access**
before pulling. `references/input-manifest.md` has the full spec + the intake
question to ask.

### Step 2 : Pull the measured data
- **Live page fetch (the forensic engine):** `python scripts/fetch_pages.py
  config.json` fetches every target URL and emits `pages_metrics.json` +
  `sections.json` : per page: raw/gzip bytes, inline-CSS/JS bytes, external
  css/js counts, DOM node count, inline-SVG count, JSON-LD @types, tracker-script
  hits (configurable), per-top-section node/byte breakdown, word count, and a
  cross-page **templated-ratio** for near-duplicate detection. Never re-derive
  these by eye.
- **GSC (real search performance):** pull 90-day clicks/impressions/CTR/position
  by page and by query; list sitemaps + errors; find duplicate URLs serving one
  intent (both live in GSC = true cannibalization); find brand-term leakage onto
  inner pages. Pass the `account` param. Exact values only : never estimate.
- **Lighthouse (measured performance):** run on the key pages via DataForSEO
  `on_page_lighthouse` (or MCP). Capture Performance/Accessibility/SEO/Best-
  Practices scores + LCP/CLS/Speed Index/TTFB/transfer. **State the profile**
  (DataForSEO = desktop); if mobile CWV are needed, get them from PageSpeed
  Insights and label them separately (mobile is Google's ranking basis).
- **Clarity (behavioural):** ONLY after verifying the connected project is this
  client's domain. If it returns another domain, record a data gap and move on.

Read every `*_data`/`*.json` output before authoring : the interpretation is
grounded in those exact numbers.

### Step 3 : Analyze the 11 dimensions
See `references/report-catalog.md` for how to build each. In short:

| # | Dimension | Source | Mode |
|---|---|---|---|
| 1 | Live Search Performance (GSC reality check) | GSC | script+author |
| 2 | Measured Performance (Lighthouse + CWV) | Lighthouse | script+author |
| 3 | Technical & Rendering (weight, CSS, DOM, trackers, form) | live fetch | script |
| 4 | Per-Section Forensic Deep-Dive (DOM/payload per section) | live fetch | script+author |
| 5 | On-Page & Schema (titles, meta, H1, JSON-LD stack) | live fetch | script+author |
| 6 | Content Contamination (cloned wrong-product blocks) | live fetch + read | **author** |
| 7 | Duplication / Templating (verbatim sentences, ratio) | live fetch | script+author |
| 8 | Location / Doorway-Page Uniqueness | live fetch | script+author |
| 9 | CRO / Conversion Path (CTAs, form mechanism, mobile) | live fetch + read | author |
| 10 | **Authorship & E-E-A-T** (author-box links, /author/ routes, Person/author schema, byline→bio) | live fetch + read | script+author |
| 11 | Action Items (prioritized P0 to P2, executable) | all of the above | author |

Scale to inputs: no GSC → drop 1; no Lighthouse → drop 2; no location pages → drop
8; no author/byline system → 10 goes light. Always include 3, 5, 6, 11 when the pages fetch.

### Step 4 : Author findings (the quality bar)
Every finding, in `report_data.py`, is a dict: **issue, sev, evidence, solution,
execution**. `evidence` is measured or verbatim (a quote in quotes, or exact
numbers). `execution` is the literal steps + how to verify. Contamination fixes
are verbatim **Find ▸ Replace** drafts. Severity: Critical/High/Medium/Low, plus
Good/Info for confirmed strengths. See `references/methodology.md`.

### Step 5 to 7 : Build, validate, deliver
- `report_data.py` holds all authored content (dicts/lists). `build_html.py` and
  `build_xlsx.py` both `import report_data as RD` and render : keep them at parity.
- Reuse built-in report branding for colors/fonts (or the bundled
  `scripts/brand_lib.py` if present).
- Validate: section/table/`<details>` tags balanced; no leftover `{RD.`/`{fn(`
  placeholders; headline counts match the arrays; XLSX tab count matches the index.
- Copy both files to the output folder, send them, and summarize **honestly** : 
  including what a measured result *corrected* (e.g. "the pages are heavy but not
  slow on desktop").

## Methodology (the non-obvious rules)
Read `references/methodology.md` before authoring. Load-bearing:
- **Measure, don't assume.** Payload size ≠ slow: a page can be 0.8 MB yet score
  94 on desktop Lighthouse because the CSS is inline (no round-trip). Report what
  you measured, and where it *contradicts* the assumption, say so.
- **Desktop ≠ mobile.** DataForSEO Lighthouse is desktop; Google ranks on mobile.
  Never present a desktop score as the mobile/ranking reality : label the profile.
- **Contamination is main-content-only.** Exclude nav/footer/review widgets or you
  get false positives; count each cloned block as one Find ▸ Replace fix.
- **Structural vs byte identity.** Near-identical template pages usually differ
  only by a city/product token : say "identical shell", not "byte-identical",
  unless a block genuinely has no varying token.
- **Cannibalization needs both URLs live in GSC.** Two paths for one intent, both
  drawing impressions = real; keep the higher-impression URL, 301 the other.
- **Prioritize by impression volume / commercial value**, and surface pages at
  position 11 to 20 first (smallest push to page 1).

## Data sources & tool routing
Read `references/input-manifest.md` for the exact MCP/API calls and the
gotchas: GSC `account` routing; verifying the Clarity project owner; the
DataForSEO desktop-Lighthouse caveat; live-fetch forensics with stdlib; and which
connectors are auth-gated.

## Branding
Use SEO report branding for every output (see built-in report branding):
Yellow #F5C518, Black #0A0A0A, Dark #1A1A1A, Green #2ECC71, Red #E74C3C, Orange
#E67E22, Blue #3498DB; Arial (XLSX) / Inter (HTML). Header + workbook read
**"<Client> · Deep Audit : <Period>"**. Text-only header (no logo)
(crop the black padding : see the branding skill).

## Guardrails
- **Never fabricate.** Every number comes from a fetch, GSC, or Lighthouse. No
  data → labelled placeholder + say so.
- **Never present another client's data as this client's.** Verify the Clarity
  (and any analytics) project domain first; on mismatch, flag a data gap.
- **Honesty over spin.** If the measured result softens a prior finding (heavy but
  fast on desktop), say it plainly : credibility is the product.
- **Degrade gracefully.** Missing source → drop its section, note it on the cover.
- **Parity.** Any new measured layer goes into both the HTML and the XLSX.
- **Re-run = compare.** Carry prior headline numbers as the baseline.

## Output location
Write everything to `<output_dir>/` from config (default `./Deep-Audit/`). Keep
intermediates (`*.json`, the builders) alongside; the two deliverables go in
`<output_dir>/`.
