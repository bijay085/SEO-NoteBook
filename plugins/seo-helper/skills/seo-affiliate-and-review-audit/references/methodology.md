# Methodology : the non-obvious rules

Load-bearing analytical rules for the affiliate + review audit. Each exists because the
naive version gives a wrong or misleading answer. Apply them and explain the *why* in
the report so the client trusts the number.

## 1. `rel="sponsored"` is the correct tag for a monetized link
Google introduced `rel="sponsored"` in 2019 for paid/affiliate links; `nofollow` alone
is legacy-tolerated but `sponsored` is the preferred, unambiguous signal. `noopener`
(and `noreferrer`) guard any `target="_blank"` link from tab-nabbing. So the compliant
attribute on an affiliate link is `rel="sponsored nofollow noopener"`. A monetized link
carrying **no** `rel` is a **link-scheme risk** (passes PageRank for money) : report it
as a compliance/penalty issue, not a style nit. Quote the actual `rel=""` string as
evidence, per link.

## 2. An affiliate link is not every outbound link
Classify each outbound link by destination host + query signature against the network
map (`config.taxonomy.affiliate_networks`), then **auto-augment** the map from what the
crawl actually finds. Signatures: `?tag=<assoc-id>` or `amzn.to` = Amazon; a
practitioner-dispensary host (e.g. `*.fullscript.com`) = Fullscript; `shareasale.com/r.cfm`,
`impact`/`cj` redirectors = those networks. Do **not** tag an editorial citation
(a study, a Wikipedia link) as monetized : false positives destroy the report's
credibility. When unsure, mark "review manually", never guess.

## 3. Dead / legacy-network links are silent revenue leaks
Status-check **every** affiliate destination and follow redirects. A `404`/`410` earns
$0 and reads as untrustworthy. A `301`/`302` that lands on a **login page or a network
homepage** (not the intended product) is a **broken deep link** : the classic case is
`wellevate.me` URLs after Wellevate merged into Fullscript. Report `<status> → <final_url>`
as evidence; a 200 that redirected off-product is still a defect.

## 4. Attribution is off-domain : measure the click, reconcile the sale
The purchase happens on the affiliate's site, so first-party analytics can see the
**outbound click, not the revenue**. Verify (a) an outbound-click event fires
(GTM/GA `click`/`affiliate_click`), and (b) a **sub-ID / UTM** carries the source page so
the affiliate dashboard can attribute the sale back. Then reconcile clicks against the
dashboard export if supplied. **Duplicate tag-manager containers** (two GTM ids) double-
count events and can conflict : flag every extra container found in the markup.

## 5. Disclosure must be above the first affiliate link, same page (FTC 16 CFR 255)
An affiliate disclosure has to be **clear, conspicuous, and proximate** : before the
first monetized link, on the same page, not hidden in a footer or an "About" page. Check
placement, not mere presence. Evidence = the verbatim disclosure sentence + where it
sits relative to the first affiliate link. Fix = a verbatim disclosure line to paste
above the first link.

## 6. Voice is archetype-dependent : never one rubric for all
Classify each piece by archetype first : **product review, roundup/"best-of",
comparison/"X vs Y", how-to, personal-experience essay, informational** : then judge
voice against the rubric that archetype demands. A roundup is allowed to be brisk and
scannable; a personal-experience essay must be first-person and specific. The single
signal Google's product-review system rewards across all review archetypes is **genuine
first-hand experience**: original testing, sensory/measurement specifics, own photos,
pros *and* cons, who it's not for. Its **absence** on a page that claims to be a review
is the real defect : not word count, not keyword density.

## 7. A rating/score system belongs on genuine reviews only
If the site runs a score (a "Fuel Score", a 1 to 10, stars), verify it is (a) applied
**only** to pages that are real product reviews : not informational posts; (b) scored on
a consistent, stated rubric; and (c) backed by structured data that reflects reality.
A score slapped on a how-to, or an inconsistent scale, reads as arbitrary and dilutes
trust.

## 8. Self-serving `AggregateRating` is a structured-data violation
`AggregateRating` / `Review` markup on your **own** product or service that is **not**
from genuinely collected reviews is against Google's rating guidelines and risks a
manual action. Only mark up ratings you actually collected. On an affiliate review of a
**third-party** product, the `itemReviewed` is that product and the `Review.author` is
the site/author : mark that, not a fabricated aggregate. Flag any `AggregateRating` with
no visible underlying reviews as a **remove-or-substantiate** item.

## 9. Revenue-weight the priority
Rank findings by **revenue/traffic exposure × severity**, not by ease. A dead affiliate
link or a missing `rel` on the **top-earning** review page is P0; the same defect on a
zero-traffic post is P2. Use GSC clicks (or, absent GSC, a labelled traffic estimate) as
the weight. P0 = this week, P1 = 30 days, P2 = 60 to 90 days.

## 10. Measure, don't assume : and say when the data is clean
Every finding is a measured value or a verbatim quote: the `rel` string, the status
code + final URL, the disclosure sentence, the JSON-LD block. If the links are actually
correctly tagged and alive, **say so** as a `Good` finding : a review that only ever
finds problems is not credible. If a value can't be measured (a network with no public
status, a JS-gated link the fetch couldn't resolve), label it a **data gap** and name
the pull that would close it : never invent it.
