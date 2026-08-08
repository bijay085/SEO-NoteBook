# Report Catalog

How to build each section. Author narrative reports as HTML section bodies wrapped
by `brand_lib.shell(title, inner, cfg)`; the scripted reports emit their own branded
HTML. Include a report only when its inputs exist (see `input-manifest.md`); otherwise
drop it and note it on the cover. Filenames use the client `short_name`.

## Report 1 : Business Understanding (`Report-1-Business-Understanding.html`)
The "who are we selling for" report. From questionnaire + business overview + live
site: business model, revenue mechanics, primary market, ICP (role / size / region /
income), the client's stated goal, the **do-not-call** terms (words they refuse to be
branded with), and the differentiators (the convincing dimensions in business terms).
End with the funnel thesis. If only a domain exists, build it from the live site + KG.

## Report 2 : Task / State Verification (`Report-2-Task-Verification.html`)
The "is what we were told actually true" report. Only when there are pages / claims to
check. For each given page: live? (200 + real content). For each stated metric (reviews,
ratings, "X+ done"): open the source, record the verified number, flag any overstatement.
Cross-check task logs vs the live site (was the work actually shipped?). Output a table:
claim | given | verified | delta | action.

## Report 3 : KG-Equivalent EAV (`Report-3-KG-Equivalent-EAV.html`)
The spine. Follow `methodology.md` §1. Sections: central entity + Wikidata / Wikipedia
anchors; L0 money terms; the EAV dimensions (one block each: attribute → values →
attract-query patterns); the bridge + a convincing-dimensions comparison table
(traditional vs the bridge, from the client's stated figures); the relationship graph;
the entity→page map. Always buildable from the entity brief alone.

## Report 4 : Keyword Engine (evidence) (`engine-run/`)
Scripted. Seed from the EAV → DataForSEO pulls saved as `raw/*.json` →
`cluster_keywords.py` → `master_by_sv.tsv` + `clusters.tsv`. This is evidence, not
prose; the topical map and go-to plan cite it. Skip only if DataForSEO is unavailable : 
then the EAV / topical map ship without volumes, clearly labelled "not yet measured".

## Report 5 : Topical Authority Map (`Topical-Map-<Client>.csv` + `.html`)
From the clusters. Columns: `cluster | page_type | salience_layer | intent |
aggregate_sv | variation_richness | canonical_url | notes`. Group into buckets (money,
category, informational, regulation/cost, location, brand). The HTML renders the buckets
with per-bucket SV totals. Reconcile against the client's page plan if one exists
(planned-but-missing / present-but-off-map). Can be delegated to
`seo-topical-map:build-topical-map`.

## Report 6 : Competitor Teardown
Only when competitors are named or discoverable. Per competitor: what they rank for
(DataForSEO ranked-keywords or live SERP), their page architecture, their proof / EAV,
and the specific **gap** the client can take. Fold into Report 1 or a standalone
section. Keep to copy/beat findings, not a feature list.

## Report 7 : Concern Playbook (`03-<Client>-Concern-Playbook.html`)
Only when strategist / client concerns were supplied. Each concern → one card: the
concern verbatim | verdict (confirmed / false / needs-data) | evidence | the action.
This is where the "verify, don't trust" work is surfaced concern-by-concern.

## Report 8 : Go-To SEO Plan (`05-<Client>-GoTo-SEO-Plan.html`)
The roadmap. Phase-wise (foundation → build → growth), each phase with objectives,
the pages / clusters it ships (from the topical map), owner, effort, and a "done-when"
check. Carry the funnel thesis (`methodology.md` §3) through it. Include team pace +
next steps. This is the report the client signs off on.

## Report 9 : Location-Page Template (`06-<Client>-Location-Page-Template.html`)
Only for location businesses. The reusable per-city page structure (Framenet-complete)
plus the per-city data table. Frame it as coverage / local-pack (`methodology.md` §4),
not an organic-traffic promise.

## Report 10 : Baseline Snapshot (`engine-run/raw-baseline/`)
Scripted, like Report 4. The "where they stood on day 1" record : captured once at
intake, not a recurring pull, so later engagement work (foundational audit, sandbox
analysis) has something to diff against. Five sources, each independently optional
(missing one drops it from the snapshot, never blocks the run):
- **GSC performance** : query + page tables for the ~16-month window and the last
  ~3 months (clicks, impressions, avg position), plus the delta between them.
- **Backlink profile** : referring domain / link counts, a DataForSEO-rank band per
  domain, spam-score-flagged domains.
- **PageSpeed** : Lighthouse category scores + Core Web Vitals (LCP, CLS, TBT,
  Speed Index). INP recorded as "not available" (lab data can't produce it), never
  estimated.
- **Ranking distribution** : ranked-keyword count in the top 3/5/10/50/100 position
  tiers.
- **GBP status** : claimed / rating / review count / category for the matched
  Google Business Profile listing.
Run `scripts/baseline_metrics.py <raw-baseline_dir> <out_dir>` on the saved raw
pulls → `baseline-summary.json` (headline numbers for the cover / workbook stat
cards) + `baseline-gsc-queries.tsv` / `baseline-gsc-pages.tsv` /
`baseline-backlink-domains.tsv` / `baseline-ranked-keywords.tsv` (detail tables).
Fold the summary numbers into Report 1 or Report 8 as the "starting point" the plan
is measured against; the detail TSVs back a Baseline tab in the Master Workbook
(use `workbook_lib.py`'s generic sheet helpers : no new workbook code needed).

## Compiled Report + Master Workbook
`combine.py <sections_dir> <config.json>` assembles the branded sections →
`00-<Client>-Compiled-Analysis-Report.html` (cover + jump-link TOC). The master XLSX
(`workbook_lib.py` helpers) is the execute-from hub: Overview, Business, Competitors,
EAV, Topical Map, Page Map, Action Items, Concern Ledger, Success Metrics : colored
tabs, frozen headers, gridlines off, status-color left-border accents.
