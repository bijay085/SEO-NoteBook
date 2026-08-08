# Recovery playbook : graduation levers

Recovery = graduating the site out of suppression. The levers are shared across niches; the
**weighting** changes with the diagnosed mode (methodology.md) and the niche. Sequence matters:
never noindex/prune before the replacement is confirmed ranking; never bundle a site-wide template
change into active recovery (it resets `last-modified` and can trigger another re-evaluation cycle).

## The levers (map each finding to one)

1. **Entity establishment (mode 1/5).** One correct Organization/LocalBusiness JSON-LD (name,
   logo, real `sameAs` to owned profiles, founder/person entity, verifiable NAP). Consistent NAP
   across GBP + site + citations. Remove stuffed `alternateName` and any fabricated `aggregateRating`.
   Goal: give Google a trustable entity to attach non-brand demand to.
2. **E-E-A-T (mode 1/2/5; the YMYL unlock).** Credentialed author bios; expert/medical reviewer
   byline where the niche warrants; cited authoritative sources (e.g. FDA/AAFCO/standards bodies);
   an About/《trust》surface with real people, licenses, guarantees. This is the single biggest lever
   on a YMYL site.
3. **Off-page trust (mode 5).** Detox: anchor-text distribution should be brand/URL/generic-heavy,
   not exact-match-money-heavy; disavow at **domain** level (conservative, human-reviewed : 
   `backlink_trust.py` proposes, a human approves). Earn a few genuinely authoritative links; stop
   any manufactured "we're #1" link posts.
4. **Commercial / money-page architecture (mode 3/4).** Strengthen collection/service/location pages
   for the terms that *convert*; separate intents into distinct interlinked page types
   (blog → collection → product, or informational → service → location) rather than merging;
   in-content contextual links, not boilerplate.
5. **SERP-feature capture (mode 3).** 40 to 55-word answer blocks, FAQ schema, tables/lists : to win
   the click back on zero-click terms, or pivot effort to intents that still get clicks.
6. **Technical graduation (all modes).** Kill the invisibility: fix noindex on pages that should
   rank, add them to the sitemap, resolve 301-to-junk, consolidate duplicate hubs, fix render-gaps
   (client-side-rendered content Google can't see), Core Web Vitals where they gate.
7. **Local layer (local-service niche).** GBP optimization + genuine location pages for the served
   geography (the client's own town list, not invented ones); reconcile GBP Insights vs
   CallRail/attributed leads.

## Niche weighting

- **YMYL ecom (e.g. kratom/supplements):** E-E-A-T (2) + entity (1) + off-page detox (3) first;
  compliance/trust seals are load-bearing. Expect a longer graduation window.
- **Pet / consumable ecom:** intent architecture (4) + E-E-A-T-lite (2, vet/expert review) + SERP
  capture (3) for the "can X eat Y" zero-click bank; commercial pages are the revenue path.
- **Local service (installer/contractor):** entity+NAP (1) + local layer (7) + commercial/service
  pages (4) + premium repositioning if moving upmarket; one clear CTA.
- **Honor owner constraints** captured in `config.custom_inputs` / client_brief (e.g. no redesign,
  no public pricing, one CTA, human QA before publish). A recovery plan that violates the owner's
  hard constraints won't be executed.

## Phased roadmap template (structure the plan as phases, not a flat list)

- **Immediate (days):** active policy/trust risks + invisibility bugs : fabricated schema, noindex on
  money pages, 301-to-junk, stop manipulative link posts.
- **This sprint (2 to 4 wks):** entity schema fix, E-E-A-T surfaces on top money/YMYL pages, technical
  crawlability, sitemap hygiene.
- **Sequenced (dependency-gated):** commercial-page build/strengthen, intent funnels, then any
  prune/noindex of the redundant tail **after** replacements are confirmed indexed and holding.
- **Ongoing:** earned links + anchor health, content depth on money clusters, monitoring.
- **Watch, don't chase:** for mode 2, broad ranking recovery may be gated to the next core update : 
  say so; deliver the non-gated wins meanwhile.

## Monitoring KPI (name the real one)

Track **non-brand clicks, non-brand position, and the Graduation Score** re-run each period : NOT
blended average position (compositional artifact) and NOT impressions alone (visibility ≠ ranking).
Carry the prior period's numbers as the baseline on every re-run.
