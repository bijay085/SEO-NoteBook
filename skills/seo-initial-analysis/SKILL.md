---
name: seo-helper : initial-analysis
description: >-
  Run the first-engagement SEO analysis for a new client and produce the branded
  SEO "initial analysis" deliverable set : Business-Understanding, live
  Task/State Verification, a Knowledge-Graph-equivalent EAV (central entity →
  salience layers → attributes → entity→page map), a DataForSEO keyword engine
  run, a topical authority map (CSV + HTML), a concern-by-concern playbook, and a
  phase-wise Go-To SEO plan : assembled into one compiled HTML report plus a
  master XLSX the team executes from. Use this whenever a NEW client is being
  onboarded/analyzed for the first time, the user drops a folder of client
  materials (questionnaire, business overview, competitors, sitemap, page plan,
  strategist concerns) and asks to "analyze this client", "do the initial
  analysis", "do what we did for Five Star / for <client>", asks for an "EAV /
  Entity-Attribute-Value", a "KG-equivalent", a "topical map", a "go-to SEO
  plan", or a "domain-wide analysis" for a site that has NOT yet had a foundation
  phase. It is config-driven so it works for ANY client, and EVERY input is
  optional : it runs on whatever is provided, from a full folder down to just a
  domain or an entity brief, and degrades gracefully.
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# Initial Analysis (New-Client First Engagement)

The repeatable, config-driven analysis we run **at the start** of an SEO
engagement : before any foundation work exists to audit. It answers: *who is this
client, what entity do they own, what does the search demand around that entity
look like, which pages should exist, and what is the phase-wise plan to rank the
money pages?* It produces the seo-initial-analysis suite as one branded HTML
document plus a master XLSX the team executes from.

It is **config-driven**: one `config.json` per client supplies the name, domain,
brand, the entity/EAV brief, and whatever input files exist, so the same skill
analyzes any client. It **starts** an engagement : the first-phase analysis, run before any foundation work exists to audit.

## When to use
- A **new client** is being onboarded and needs the first strategic analysis.
- The user drops a folder of client artifacts (questionnaire, business overview,
  competitors, sitemap, page plan, task logs, strategist concerns) and says
  "analyze this / do the initial analysis / do what we did for Five Star".
- The user asks for any of the core artifacts by name: **EAV / Entity-Attribute-
  Value**, **KG-equivalent**, **topical map**, **domain-wide analysis**,
  **go-to SEO plan**, **concern playbook**, **business-understanding report**.
- The user gives only an **entity brief** (entity + buying intent + ICP +
  dimensions + bridge + convincing dimensions + conclusion) and wants the EAV +
  topical map built from it.

Do **not** use this for a running engagement's ongoing performance/value review.
For a live Search-Console traffic-drop triage use `seo-gsc-diagnosis`. This skill can *hand off* the seo-topical-map step to
`seo-topical-map:build-topical-map` and branding to
built-in report branding when those are available (see "Related skills").

## Inputs are OPTIONAL : limited or custom is fine
**There is no required input.** The skill runs on whatever exists and tells the
user what each present input unlocks and what each missing one drops. Three real
shapes it must handle:

1. **Full folder** (the Five Star case): questionnaire + business overview +
   competitors + sitemap + page plan + task logs + action items + strategist
   concerns → the complete suite.
2. **Limited** (the Plate Photo case): just an initial questionnaire, or just a
   domain → still produce Business-Understanding + EAV + keyword engine + topical
   map + go-to plan; drop Task-Verification and Concern-Playbook, note why.
3. **Entity-only**: just the entity brief (no files, maybe no live site yet) →
   produce the EAV + a keyword-driven topical map + a starter go-to plan from the
   KG + DataForSEO alone.

**Custom inputs never get rejected.** Anything extra a client provides (brand
guide, CLV/customer data, sales deck, prior audit, screenshots, a bespoke CSV) is
mapped to the closest report or added as an appendix. When an input's shape is
unexpected, read it, say what you found, and fold it in : don't discard it.

The full spec (what each input feeds, formats, column hints, the "minimum viable"
sets) is in `references/input-manifest.md`. Read it at intake.

## The deliverable
1. **`00-<Client>-Compiled-Analysis-Report.html`** : one branded document: cover,
   jump-link table of contents, every report section, footer. (`scripts/combine.py`.)
2. **`00-<Client>-Master-Workbook.xlsx`** : the execute-from hub: Overview +
   per-report data tabs + Topical Map + Page Map + Action Items + Concern Ledger +
   Success Metrics. (`scripts/workbook_lib.py` helpers.)
3. Standalone section HTMLs: `Report-1-Business-Understanding.html`,
   `Report-2-Task-Verification.html`, `Report-3-KG-Equivalent-EAV.html`,
   `03-<Client>-Concern-Playbook.html`, `05-<Client>-GoTo-SEO-Plan.html`, and
   (for location businesses) `06-<Client>-Location-Page-Template.html`.
4. **`Topical-Map-<Client>.csv` + `.html`** : the topical authority map.
5. **`engine-run/`** : `master_by_sv.tsv`, `clusters.tsv`, `raw/*.json` (the
   DataForSEO pulls, kept as evidence).
6. **`engine-run/raw-baseline/`** : the initial Baseline Snapshot: raw GSC /
   backlinks / Lighthouse / rankings / GBP pulls, plus `baseline-summary.json`
   and detail TSVs (`scripts/baseline_metrics.py`). One-time "where they stood
   on day 1" record : later engagement audits diff against it.
7. **`config.json`** (the run's frozen config) and a **session log**.

Every HTML/XLSX uses SEO report branding (see "Branding"). Scale the set to the
inputs : a section with no data is dropped and noted on the cover, never faked.

## How it works (the phases)
A **hybrid**: deterministic Python for the keyword engine + branding/assembly,
and **you (Claude) author** the narrative/strategy reports by reading the inputs
and applying `references/methodology.md`. A script can't write the synthesis; a
script *should* cluster keywords identically every time.

```
0. INTAKE → read config.json; inventory which inputs exist (all optional);
                  tell the user what builds vs what's dropped. Fetch the live site
                  + sitemap if a domain is given. VERIFY given claims, don't trust.
1. BUSINESS → Report 1: who they are, model, ICP, market, goal, do-not-call
                  terms, differentiators : from inputs + live site.
2. VERIFY → Report 2: check given claims vs live reality (pages live? review
                  counts? competitor claims?). Only when there's prior work/pages.
3. EAV / KG → Report 3: anchor the entity in Wikipedia/Wikidata; salience
                  layers L0/L1/L2; EAV per dimension; relationship graph; bridge +
                  convincing dimensions; entity→page map. Always doable.
4. ENGINE → DataForSEO: expand seeds from the EAV dimensions → SV/KD/SERP →
                  scripts/cluster_keywords.py → master_by_sv.tsv + clusters.tsv.
5. TOPICAL MAP → clusters → buckets w/ salience + aggregate SV + intent + page
                  type + de-cannibalization → Topical-Map.csv + .html.
6. COMPETITORS → live SERP + content teardown of named/discovered competitors →
                  gaps → folds into Report 1 / a competitor section.
7. CONCERNS → Concern Playbook: each strategist/client concern answered with
                  evidence + action. Only when concerns were supplied.
8. GO-TO PLAN → phase-wise roadmap (foundation → build → growth), team pace,
                  page plan, next steps.
9. BASELINE (opt) → the initial Baseline Snapshot, captured once at intake so later
                  engagement work has a "day 1" to diff against:
                  - GSC (if connected): query_search_analytics, dimensions=[query]
                    and [page], for the ~16mo max-history window AND the last ~3mo,
                    saved separately (don't call GSC data "estimated" : pull the
                    real months).
                  - Backlinks: backlinks_summary (totals) + backlinks_referring_domains
                    (per-domain list) + backlinks_bulk_spam_score (score each of
                    those domains) → domain/link counts, a DataForSEO-rank-based
                    band per domain, spam-flagged domains.
                  - PageSpeed: on_page_lighthouse on the homepage/primary URL →
                    category scores + Core Web Vitals (LCP, CLS, TBT, Speed Index).
                    INP is a field metric a lab run can't produce : record it as
                    "not available" rather than estimate it.
                  - Rankings: dataforseo_labs_google_ranked_keywords → bucket into
                    top 3/5/10/50/100 position tiers.
                  - GBP: business_data_business_listings_search, matched by business
                    name + location → claimed status, rating, review count, category.
                  Save every raw response to `engine-run/raw-baseline/<name>.json`
                  (exact filenames + processing in `scripts/baseline_metrics.py`,
                  which writes `baseline-summary.json` + detail TSVs). Any source
                  that's unavailable (no GSC property, DataForSEO off) drops from
                  the snapshot and is noted : never blocks the run.
10. ASSEMBLE → brand every section (brand_lib) → combine.py → compiled HTML;
                  build the master XLSX (workbook_lib); write the session log.
```

Every phase degrades gracefully: no inputs for it → drop or lighten it, note it,
move on. Read the `engine-run` outputs before writing synthesis : interpretation
is grounded in those exact numbers, never re-derived by eye.

## Report catalog
Full per-report authoring guidance is in `references/report-catalog.md`. In short:

| # | Report | Built from | Mode |
|---|---|---|---|
| 1 | Business Understanding | questionnaire + overview + live site | author |
| 2 | Task / State Verification | given pages/claims vs live site + sitemap | author |
| 3 | KG-Equivalent EAV | entity brief + Wikipedia/Wikidata | author |
| 4 | Keyword Engine (evidence) | DataForSEO pulls | **script** |
| 5 | Topical Authority Map | engine clusters + EAV | script/author |
| 6 | Competitor Teardown | competitors list + live SERP | author |
| 7 | Concern Playbook | strategist/client concerns | author |
| 8 | Go-To SEO Plan (phase-wise) | all of the above | author |
| 9 | Location-Page Template | client locations (if local) | author |
| 10 | Baseline Snapshot | GSC + DataForSEO pulls (baseline_metrics.py) | **script** |
| : | Compiled Report + Master Workbook | all sections | script/author |

Always include 3, 5, 8 (doable from an entity + APIs alone). Include 1 when any
client material exists; 2 when there are pages/claims to verify; 6 when
competitors are named; 7 when concerns are supplied; 9 for location businesses.

## Methodology (the non-obvious rules)
Read `references/methodology.md` before authoring. Load-bearing methods:
- **Salience layers** : L0 core-identity/money terms, L1 attributes/dimensions,
  L2 the bridge (e.g. "…by AI"). Every entity gets placed on a layer; the funnel
  targets the broad L1 "Dimension + <service>" demand, then introduces the L2
  bridge and the convincing dimensions on the page.
- **EAV** : Entity → Attribute (dimension) → Value (child entities), each with the
  human-language query patterns that attract it. Values come from the KG + real
  keyword data, **never invented volumes**.
- **Location pages are a coverage / local-pack play, not an organic-traffic play**
  : geo "<service> <city>" terms are often ~0 SV; the real geo organic demand is
  regulation/license/cost. Don't promise organic traffic from bare city pages.
- **De-cannibalization spine** : one intent → one canonical page; siblings link up,
  not compete. Map every cluster to exactly one page type before planning.
- **Right content, wrong execution** : informational content builds the topical
  authority that ranks money pages; keep it, fix its geography/E-E-A-T/funnel.
- **Verify, don't trust** : every given claim (review counts, "live" pages,
  competitor stats) is checked against the live source before it enters a report.

## APIs & credentials
Data sources, the exact MCP tools, and what each is for are in
`references/api-and-credentials.md`. Summary: **DataForSEO** MCP (keyword volume /
ideas / SERP / competitor for the engine; backlinks / Lighthouse / rankings /
Business Data for the Baseline Snapshot), **Google Search Console** MCP (real
performance when connected, including the baseline's 16mo/3mo pull), **Wikipedia +
Wikidata** via WebFetch (entity anchoring), **WebSearch/WebFetch** (live
verification + competitor teardown), **Microsoft Clarity** MCP (optional behavior),
**Desktop Commander** MCP (file I/O under `~/Downloads`, where Bash cat/ls is
TCC-blocked). **No secrets live in the skill** : every credential is a
pre-configured MCP server; if one isn't connected or authorized, that data source
degrades gracefully and the run continues.

## Branding
Use SEO report branding for every output. If built-in report branding is
available, consult it; otherwise the spec is baked into `scripts/brand_lib.py`,
driven by `config.json`'s `brand` block (yellow #F5C518 / black #0A0A0A + Lexend
for HTML; Arial for XLSX). Cover + workbook header read
**"<Client> · Initial Analysis"**.

## Guardrails
- **Never fabricate.** Every number comes from a file or an MCP pull. No search
  volume, review count, or ranking is invented : if it isn't measured, label it
  "not yet measured" and list the pull that would get it.
- **Verify live before asserting.** Findings decay; re-check the live site/SERP at
  run time. Reconcile client-stated figures against the source and flag gaps.
- **Degrade gracefully.** Missing input → drop/lighten that report, note it on the
  cover. Never block the run for a missing file.
- **Nothing is lost.** When consolidating or cleaning, verify the new set ⊇ the old
  before removing anything; move to Trash, never hard-delete.
- Keep the client's own goal and **do-not-call** terms as constraints every report
  respects.

## Related skills (compose, don't duplicate)
- `seo-topical-map:build-topical-map` + `:keyword-enrichment` : can own the
  seo-topical-map + keyword steps if you prefer their engine to `cluster_keywords.py`.
- built-in report branding : the canonical brand spec.
- `seo-gsc-diagnosis` : GSC traffic-drop triage (post-launch).
- `seo-forensics:*` : drop / CRO / coverage-gap forensics, later.

## Output location
Write everything to `<output_dir>/` from the config (default `./Output/`). Keep
intermediate section HTML in `<output_dir>/sections/` and the keyword pulls in
`<output_dir>/engine-run/`; the compiled HTML, standalone reports, topical map,
and master XLSX go in `<output_dir>/`.
