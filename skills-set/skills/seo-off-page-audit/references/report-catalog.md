# Report Catalog — how to build each dimension

Every finding is a dict **{issue, sev, evidence, solution, execution}** (see
`methodology.md` §10). Build only the dimensions the inputs support; note dropped ones on
the cover.

## 1 · Inbound Backlink Profile  — *script + author*
From `backlinks_summary` + `backlinks_referring_domains` (+ CSV): total backlinks,
**referring domains**, dofollow/nofollow split, authority distribution (rank buckets),
new/lost velocity. Lead with referring domains, not raw links (Methodology §7). Evidence
= the counts + a histogram of referring-domain authority. Flag a high link:domain ratio
from few domains as a footprint smell.

## 2 · Anchor-Text Distribution  — *script + author*
From `backlinks_anchors` (+ CSV): classify every anchor into branded / exact-match /
partial-match / naked-URL / generic (using `config.taxonomy.branded_anchor_terms`).
Report the % distribution vs a natural benchmark (branded + naked + generic should
dominate). Evidence = the distribution table + the top exact-match anchors and their
source domains. Over-optimized exact-match from low-authority domains = the risk
(Methodology §8).

## 3 · Toxic Backlinks → Disavow  — *script + author (the core)*
`scripts/backlink_toxicity.py` merges DataForSEO `backlinks_bulk_spam_score` + Ahrefs +
Semrush exports, computes the **multi-source high-confidence** set (flagged by ≥
`min_sources_to_disavow`), subtracts the existing `disavow.txt`, and writes the merged
`disavow.txt`. Author:
- The **intersection** count + a per-domain table (domain · sources-that-flagged · spam
  score · verdict).
- The **disavow / monitor** decision, gated on manual-action / clear-pattern evidence
  (Methodology §1). Say plainly when the answer is "don't disavow — the profile is
  normal."
- Evidence = the domains + which tools flagged each. Execution = "Search Console ▸
  Disavow links ▸ upload `disavow.txt` (N domains)" **only if** warranted; else "stage
  and monitor".

## 4 · Referring-Domain Quality & Relevance  — *author*
Read a sample of the top referring domains: topically relevant? editorial vs directory
vs comment vs PBN-pattern? Evidence = named examples per bucket. This contextualizes Dim
1 (a small but relevant/authoritative profile can beat a large junk one).

## 5 · Outbound External-Link Equity  — *script + author*
From the outbound export / crawl: external outbound links, their `rel`, and destination
authority. Flag: monetized outbound missing `rel="sponsored"` (link-scheme risk); heavy
dofollow to low-value/irrelevant sites (equity leak). Do NOT flag healthy editorial
dofollow to authorities (Methodology §6). Evidence = the links + their `rel`. Execution =
the exact `rel` to add, per link/group.

## 6 · Competitive Link Gap  — *script + author*
From `backlinks_domain_intersection` / `backlinks_competitors`: referring domains that ≥2
competitors have and the client doesn't. Evidence = the gap domains + their authority.
Output a prioritized **link-building target list** (relevant, reachable domains first).

## 7 · Action Items  — *author, risk-then-opportunity*
Consolidate: **P0** disavow the high-confidence toxic set *iff* evidence warrants (else
monitor); **P1** outbound rel fixes (in your control, quick); **P2** the link-gap target
list. Columns: Issue · Evidence · Solution · Execution · Effort · Priority.

## Assembly
`report_data.py` holds authored dicts/lists. `build_html.py` + `build_xlsx.py` import it
and render at **parity**; the `disavow.txt` is a third output. Reuse
built-in report branding. Validate: balanced tags/tables, `disavow.txt` lines all
`domain:` or bare-URL + a comment header, headline counts match arrays, XLSX tab count
matches the index.
