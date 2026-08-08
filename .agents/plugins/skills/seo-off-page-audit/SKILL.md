---
name: seo-helper : off-page-audit
description: >-
  Run a standalone, config-driven OFF-PAGE / link audit of a website : everything about
  the links between this domain and the rest of the web, in both directions: the INBOUND
  backlink profile (authority, referring domains, anchor-text distribution, toxic/spam
  links and a conservative domain-level disavow list) and the OUTBOUND external links
  (dofollow equity leak, rel hygiene). Produces a branded SEO deliverable (deep
  HTML report + master XLSX) with a prioritized disavow file and an outbound-rel fix
  plan, every claim backed by measured link data. Use whenever the user wants an
  "off-page audit", "backlink audit / profile", "link audit", "toxic backlink / spam
  link check", "disavow file / should I disavow", "anchor text distribution", "referring
  domains analysis", "link gap vs competitors", "am I leaking link equity", or drops
  Ahrefs / Semrush backlink or toxic exports + a disavow file. Industry-agnostic;
  config-driven so it works for ANY client. Backlink data comes from the DataForSEO
  backlinks MCP + client CSV exports (Ahrefs/Semrush) : NOT a direct Ahrefs/Semrush API
  (those keys are unset). Requests missing exports or pulls live via DataForSEO. Reuse
  built-in report branding (brand_lib / report_kit) for styling.
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# Off-Page / Link Audit

A repeatable, config-driven **off-page audit**: it looks only at links : the ones
pointing **in** (the backlink profile that is 50%+ of ranking) and the ones pointing
**out** (external links that leak equity or expose the site). It answers: *"Is the
inbound profile healthy or does it need a disavow, are the anchors natural, and are the
outbound links tagged so they neither leak PageRank nor invite a link-scheme flag?"* : 
and produces the SEO deliverable as one branded HTML document plus a master XLSX,
including a ready-to-upload `disavow.txt`.

It is the **off-site sibling** of the on-page skills (`seo-after-foundational-setup-audit`,
`seo-affiliate-and-review-audit`). Those audit the pages; **this** one audits the link graph
around them. Internal linking is deliberately **out of scope** here (it's an on-page
concern) unless the config opts it in.

Every claim is **measured, not assumed** : real referring-domain counts, real spam
scores, the actual anchor distribution, the verbatim rel on an outbound link. A domain
enters the disavow list only on **multi-source, high-confidence** evidence; nothing is
invented, and disavow is treated as a **last resort** (see Methodology).

## When to use
- A site needs its **backlink profile** assessed, a **toxic-link / disavow** decision
  made, or its **outbound links** checked for equity leak / rel hygiene.
- The user asks: *backlink/off-page/link audit*; *should I disavow / build a disavow
  file*; *are these links toxic*; *anchor-text distribution*; *referring domains*; *link
  gap vs competitors*; *am I leaking link equity*.
- The user drops **Ahrefs / Semrush** backlink or toxic exports (± an existing disavow
  file) and wants them merged into one verdict.
- A prior off-page audit needs re-running to measure new/lost links since the baseline.

## Required access : request it before running (do not guess)
At intake, check what's available and **ask for anything missing** via one structured
question : then proceed with what you have, degrading gracefully. The skill can also
**fill gaps itself** by pulling the profile live from DataForSEO. See
`references/input-manifest.md`.

Ask for, at minimum:
1. **Domain** : the target (root domain; confirm www/non-www + http/https handling).
2. **Backlink exports (optional but ideal)** : an **Ahrefs** backlink/referring-domains
   export and/or a **Semrush** backlink-audit / toxic export. These are the highest-
   value custom inputs: they corroborate DataForSEO for the high-confidence toxic set.
3. **Existing disavow file (optional)** : the current `disavow.txt` so already-disavowed
   domains are **not** re-listed and the output is the true net-new set + a merged file.
4. **Outbound-link export (optional)** : a Screaming-Frog / crawler "external outlinks"
   export (or permission to crawl) for the outbound-equity dimension.
5. **Competitors (optional)** : for the link-gap dimension.
6. **Manual-action status** : has GSC reported a manual action / "unnatural links"? This
   decides whether a disavow is even warranted (see Methodology §1).

## The deliverable
1. **`<Client>_<Period>_Off-Page-Audit.html`** : one branded document: header, sticky
   nav, contents grid, then every dimension with measured evidence, inline SVG charts
   (referring-domain authority histogram, anchor-type donut, new/lost velocity), and
   collapsible tables.
2. **`<Client>_<Period>_Off-Page-Audit.xlsx`** : Overview + one tab per dimension + a
   **Toxic-Domains** tab (domain · sources-that-flagged · spam score · verdict) + a
   **Disavow-Additions** tab + an Action-Items tab.
3. **`disavow.txt`** : Google-format (`domain:spam.example` lines + comment header),
   containing the existing entries plus the high-confidence net-new additions.
Both report formats use SEO report branding and stay at **parity**.

## How it works (the loop)
A **hybrid**: deterministic Python merges the link sources, scores toxicity, and writes
the disavow file; **you (Claude) author the findings** : the interpretation and the
executable step : grounded in the measured numbers, and you make the **disavow / no-
disavow judgement** (a script proposes candidates; only you decide it's warranted).

```
1. INTAKE → load config.json; confirm inputs; REQUEST exports / disavow (one question)
2. PULL → DataForSEO backlinks MCP (summary, referring_domains, anchors, spam_score,
             competitors); read client Ahrefs/Semrush CSVs + existing disavow.txt;
             (optional) crawl/read outbound external links
3. MERGE → scripts/backlink_toxicity.py unions the sources, computes the multi-source
             high-confidence toxic set, subtracts already-disavowed, writes disavow.txt
4. ANALYZE → the 7 dimensions below, against measured data (never by eye)
5. AUTHOR → report_data.py: every finding = Issue · Evidence · Solution · Execution
6. BUILD → build_html.py + build_xlsx.py import report_data.py; render both, at parity
7. VALIDATE→ balanced tags/tables, disavow format valid, counts match, tab count
8. DELIVER → copy to the output folder, send all files, summarize honestly
9. MEMORY → save durable client facts (RD count, the toxic set, disavow decision)
```

## The 7 dimensions
See `references/report-catalog.md`. In short:

| # | Dimension | Source | Mode |
|---|---|---|---|
| 1 | **Inbound Backlink Profile** : backlinks, referring domains, dofollow split, authority, new/lost velocity | DataForSEO + CSV | script+author |
| 2 | **Anchor-Text Distribution** : branded / exact-match / naked / generic; over-optimization | DataForSEO `backlinks_anchors` + CSV | script+author |
| 3 | **Toxic Backlinks → Disavow** : multi-source high-confidence set, domain-level, net of existing | spam_score + Ahrefs + Semrush CSV | **script+author** |
| 4 | **Referring-Domain Quality & Relevance** : topical relevance, link type (editorial/directory/PBN) | DataForSEO + read | author |
| 5 | **Outbound External-Link Equity** : dofollow leak, rel hygiene (sponsored/ugc/nofollow where apt) | crawl / outbound export | script+author |
| 6 | **Competitive Link Gap** : referring domains competitors have that you don't | DataForSEO `backlinks_domain_intersection` | script+author |
| 7 | **Action Items** : P0 disavow (if warranted) · P1 outbound rel · P2 link-building | all | author |

Scale to inputs: no competitors → drop 6; no outbound export/crawl → drop 5; no CSV →
run on DataForSEO alone and mark single-source toxic candidates "review" not "disavow".
Always include 1, 3, 7 when a domain is given.

## Author findings (the quality bar)
Every finding = **{issue, sev, evidence, solution, execution}**. `evidence` is a
measured number or verbatim value (referring-domain count, spam score, the anchor %, the
outbound `rel=""`). `execution` is literal (e.g. *"Search Console ▸ Disavow links ▸
upload `disavow.txt` (attached) : 75 domains"*, or *"add `rel=\"nofollow\"` to the 3
outbound links listed"*). Severity Critical/High/Medium/Low + Good/Info. See
`references/methodology.md`.

## Methodology (the non-obvious rules)
Read `references/methodology.md` before authoring. Load-bearing:
- **Disavow is a last resort.** Google ignores most spam automatically; disavow only on
  a **manual action** or a clear paid/negative-SEO pattern you can't get removed.
  Over-disavowing removes legitimate equity : say so, and gate the P0 on real evidence.
- **High-confidence = multi-source.** A domain is disavow-grade only when **≥2
  independent sources** flag it (DataForSEO high `backlinks_spam_score` + Ahrefs +
  Semrush). Single-source flags are "**review**", not auto-disavow (the FWD case: the
  Ahrefs∩Semrush intersection = 75 high-confidence).
- **Disavow at domain level.** `domain:spam.example` catches every page + future links;
  URL-level entries miss variants. Reserve URL entries for a single bad link on an
  otherwise-good domain.
- **Never re-disavow.** Subtract domains already in the supplied `disavow.txt`; the
  report's "additions" are the true net-new; the written file is the merged superset.
- **You can't rel inbound links : disavow is the only inbound lever.** rel hygiene
  applies to **outbound** links (you control those).
- **Outbound dofollow to authorities is GOOD.** Don't nofollow everything : editorial
  outbound dofollow to relevant sources is a positive relevance signal. Tag only
  **monetized** (`sponsored`), **user-generated** (`ugc`), or genuinely low-trust
  outbound. Over-nofollowing is a myth-driven anti-pattern.
- **Referring domains > raw backlink count.** 500 links from 300 domains beats 10,000
  from 5. Weight authority by unique referring domains.
- **Exact-match anchor over-optimization is a Penguin signal.** A natural inbound
  profile is dominated by branded / naked-URL / generic anchors; a high share of exact-
  match commercial anchors from external sites is the risk to flag.

## Data sources & tool routing
`references/input-manifest.md` has the exact calls + credential routing (all **real**):
**`mcp__dataforseo__backlinks_*`** is the live engine : `backlinks_summary`,
`backlinks_referring_domains`, `backlinks_anchors`, `backlinks_bulk_spam_score`,
`backlinks_competitors`, `backlinks_domain_intersection`,
`backlinks_bulk_new_lost_referring_domains` (creds `DATAFORSEO_LOGIN`/`_PASSWORD` from
`project `.env` / host environment variables`). Client **Ahrefs/Semrush CSVs** are read via local filesystem tools.
GSC (`mcp__google-search-console__*`) is optional context. **`AHREFS_API_KEY` /
`SEMRUSH_API_KEY` in `.env` are empty : do NOT call those APIs; use DataForSEO + the CSV
exports.** `browser / Playwright / agent browse tools`/Playwright/`requests` handle the outbound crawl.

## Branding
SEO report branding for every output (see built-in report branding): Yellow #F5C518,
Black #0A0A0A, Dark #1A1A1A, Green #2ECC71, Red #E74C3C, Orange #E67E22, Blue #3498DB;
Arial (XLSX) / Inter (HTML). Header + workbook read **"<Client> · Off-Page Audit : 
<Period>"**. Text-only header (no logo).

## Guardrails
- **Never fabricate.** Every count, score, and rel comes from DataForSEO, a client
  export, or a live crawl. No data → labelled placeholder + say so.
- **Disavow conservatively.** When evidence is thin, recommend "monitor", not "disavow".
  A wrong disavow is harder to undo than a missing one.
- **Honesty over spin.** A clean, natural profile is a `Good` finding : say it.
- **Degrade gracefully.** Missing source → drop its dimension, note it on the cover.
- **Parity.** Any new measured layer goes into both HTML and XLSX.
- **The skill produces analysis + the disavow file; the human uploads it.** It never
  submits to Search Console or contacts a webmaster on the user's behalf.

## Output location
Write everything to `<output_dir>/` from config (default `./Off-Page-Audit/`). Keep
intermediates (`*.json`, the merged sources, the builders) alongside; the two reports +
`disavow.txt` go in `<output_dir>/`.
