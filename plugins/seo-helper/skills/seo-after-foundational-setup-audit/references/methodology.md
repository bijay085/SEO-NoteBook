# Methodology : the non-obvious rules

These are the load-bearing analytical rules for the deep audit. Each exists
because the naive version gives a wrong or misleading answer. Apply them and
explain the *why* in the report so the client trusts the number.

## 1. Measure, don't assume
Every finding is backed by a measured number or a verbatim quote : never "this
looks heavy/slow/duplicated". Fetch the page, count the bytes/nodes, quote the
sentence. Where a measurement *contradicts* the intuitive read, say so out loud:
a page can be ~0.8 MB and still score 94 on desktop Lighthouse because its CSS is
inline (no extra round-trip), so "big payload" is NOT "slow page". Reporting that
honestly is more credible than a scary-but-wrong claim.

## 2. Desktop is not mobile (label the profile)
Google ranks mobile-first. But some tools default to desktop : DataForSEO's
Lighthouse endpoint runs the **desktop** profile (10 Mbps, 1x CPU). A desktop
score of 95 does NOT mean the mobile/ranking experience is fine. Always state the
profile next to the score. For the ranking-relevant view, get mobile CWV from
PageSpeed Insights (or a 4x-CPU + Slow-4G local trace) and label it "mobile".
There is often no CrUX field data for low-traffic sites : say "no field data"
rather than implying the lab number is the field reality.

## 3. Contamination is main-content-only
"Cloned wrong-product content" is measured on the MAIN CONTENT only : exclude
nav, footer, breadcrumb, and review/widget areas, or shared chrome creates false
positives. A finding is a *whole block* (a heading + its body, a Step accordion, a
Repair-or-Replace decision block) copied from a sibling page with the product noun
left wrong (e.g. an Opener page that still says "Schedule a Panel Diagnosis").
Count each wrong block as one **Find > Replace** fix. Treat recurring site
furniture (a dated "recent posts" card, a generic trust line) as a false positive,
not contamination : and say you excluded it.

## 4. Structural identity vs byte identity
Near-identical template pages (e.g. 28 city pages) usually differ only by a
city/product token. Say **"identical shell"** or "structurally identical", not
"byte-identical", for the whole page : the bytes differ by the city name. Reserve
"byte-identical" for blocks that genuinely contain no varying token (a shared
door-material blurb, a services grid). Also watch for the outlier: a page with a
different node/CSS fingerprint from its 27 siblings signals a non-deterministic
template regeneration or a per-page cache divergence : flag it as the canary.

## 5. Additivity of section counts
When you report per-section DOM/byte counts, note whether sections **nest**. On a
page where the whole body is wrapped in one mega-container, the child sections'
counts are inside that wrapper's count : they are NOT additive; the table caption
must say so. Where sections are siblings, the counts add up normally.

## 6. Cannibalization needs both URLs live in GSC
Only call it cannibalization when two (or more) URLs serve the same intent AND
both draw impressions in GSC. The fix: keep the higher-impression URL as
canonical, 301 the other(s) into it, and resubmit sitemaps. An un-cleaned
migration (legacy `-in-city-state` URLs, a `/location/` twin of a root URL, an
indexed raw `/*-template/`) is the usual root cause and is often a bigger lever
than any single on-page fix.

## 7. Brand-term leakage
If a brand query ("<brand> <service>") ranks an inner page (a city or a service
page) at position ~1 with ~0 clicks, those impressions are the brand searcher who
clicks the homepage/GBP instead : the inner page is absorbing brand impressions it
can't convert. Consolidate the brand query onto the homepage; this also explains
"page X has huge impressions at a great position but no clicks".

## 8. Templated-ratio (near-duplicate detection)
Compute each page's templated ratio = share of its main-content sentences that
recur across the majority of the peer set. Sentences appearing verbatim on nearly
all peers are the doorway pattern that caps how well any single page can rank. Add
250-400 words of genuinely local/unique content per page ABOVE the shared template.

## 9. Every finding = Issue . Evidence . Solution . Execution
- **Issue** : one line, specific.
- **Evidence** : measured number or verbatim quote (in quotes). No adjectives.
- **Solution** : the corrective principle.
- **Execution** : the literal steps a junior can follow + how to VERIFY (e.g.
  "DevTools > Network > filter swap.js must show 1"). For content, give the exact
  Find > Replace text.
Severity: Critical / High / Medium / Low, plus **Good** (a confirmed strength) and
**Info** (a neutral insight). Reporting strengths honestly builds trust.

## 10. Prioritize by impact, not by ease
Rank the action plan by impression volume and commercial value, and put pages at
**position 11-20** first : they need the smallest push to reach page 1. P0 = this
week (site-wide, high-leverage, often quick), P1 = 30 days, P2 = 60-90 days.

## 11. Honesty & data gaps
If a source is missing or wrong (e.g. the connected analytics project is a
different client), state it as an explicit **data gap** in the report : never fill
it with another client's numbers or an estimate. A named gap is a finding; a faked
number is a liability.


## 12. Authorship & E-E-A-T is an entity check, not a byline check
A visible byline is not E-E-A-T. Verify the author is a real, resolvable entity:
(a) the author-box link is a live URL, not `href=""` or a 404/301 `/author/` route;
(b) an author/`Person` JSON-LD node exists and links the article to a named person
with credentials + `sameAs`; (c) the byline reaches an on-site bio that establishes
experience/expertise. On **YMYL** pages (health, finance, legal) this is ranking-
load-bearing, not cosmetic. Evidence = the actual href (or its emptiness), the
`Person` block (or its absence), the `/author/` HTTP status : never "looks
authoritative". Fix = the exact author-box href + the `Person` schema FIND->REPLACE.
This dimension is **on-page authorship only**; off-site authority (backlinks,
mentions) belongs to the `seo-off-page-audit` skill : don't duplicate it here.
