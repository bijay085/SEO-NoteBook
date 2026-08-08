# Methodology : the non-obvious rules

Load-bearing rules for the off-page audit. Each exists because the naive version gives a
wrong or harmful answer (a bad disavow removes real equity; a false toxic flag scares a
client). Apply them and explain the *why* in the report.

## 1. Disavow is a last resort : gate it on real evidence
Google discounts most spammy links automatically. Disavow only when there is (a) a
**manual action** for unnatural links, or (b) a clear pattern of **paid / negative-SEO**
links you have tried and failed to get removed. A speculative disavow can strip
legitimate equity and *drop* rankings. So P0 "disavow now" is conditional on
manual-action / clear-pattern evidence; otherwise the recommendation is **monitor**, and
the built `disavow.txt` is staged "ready if needed", not "upload today".

## 2. High-confidence toxic = multi-source agreement
A referring domain is disavow-grade only when **≥ `min_sources_to_disavow`** independent
sources flag it : DataForSEO `backlinks_spam_score` ≥ threshold, Ahrefs toxicity/DR
signal, Semrush toxic score. A single-source flag is a **"review"** candidate, not an
auto-disavow. Report the intersection explicitly (e.g. "75 domains flagged by BOTH
Ahrefs and Semrush"); it is far more defensible than any one tool's list.

## 3. Disavow at the domain level, not the URL
`domain:spam.example` disavows every current and future link from that host; a URL-level
entry misses `/page2`, the `www` variant, and tomorrow's link. Use domain entries for
spammy sites; reserve a bare-URL entry for a single bad link on an otherwise-legitimate
domain you want to keep.

## 4. Never re-disavow what's already disavowed
Parse the supplied `disavow.txt` first. Subtract those domains from the candidate set so
the report's **additions** are the true net-new, and the written file is the **merged
superset** (existing + new) : an upload replaces the whole file, so it must be complete.

## 5. You can't add rel to inbound links : disavow is the only inbound lever
Inbound anchors and rel are controlled by the linking site, not you. The only inbound
tools are outreach-for-removal and disavow. rel hygiene is an **outbound** concern.

## 6. Outbound dofollow to authorities is good : tag selectively
Do **not** blanket-nofollow outbound links. Editorial dofollow links to relevant,
authoritative sources are a positive relevance signal. Apply rel only where it belongs:
`rel="sponsored"` on monetized/affiliate links, `rel="ugc"` on user-generated links
(comments/forums), `rel="nofollow"` on genuinely low-trust or untrusted destinations.
Flag missing rel on **monetized** outbound (link-scheme risk) and excessive dofollow to
low-value/irrelevant sites (equity leak) : not healthy editorial links.

## 7. Referring domains beat raw backlink count
Authority scales with **unique referring domains**, not total links. 500 links from 300
domains is stronger and more natural than 10,000 links from 5 domains. Lead the profile
dimension with referring-domain count and its authority distribution; treat a huge
link:domain ratio from few domains as a footprint/PBN smell.

## 8. Exact-match anchor over-optimization is a Penguin-era risk
A natural inbound anchor profile is dominated by **branded**, **naked-URL**, and
**generic** ("click here", "this article") anchors. A high share of **exact-match
commercial** anchors from external sites (especially from low-authority domains) is the
manipulation signal to flag. Classify every anchor into branded / exact-match /
partial-match / naked-URL / generic and report the distribution vs a natural benchmark.

## 9. Prioritize by risk then opportunity
P0 = disavow the high-confidence toxic set **iff** §1 evidence exists (else monitor).
P1 = fix outbound rel hygiene (quick, in your control). P2 = the competitive link gap : 
referring domains competitors earn that you don't : as a link-building target list.

## 10. Measure, don't assume : and say when the profile is clean
Every number comes from DataForSEO, a client export, or a live crawl. If the profile is
natural and no disavow is warranted, **say so** as a `Good` finding : recommending a
disavow nobody needs is the classic way an off-page audit destroys trust. Unmeasurable
values are labelled data gaps, never invented.
