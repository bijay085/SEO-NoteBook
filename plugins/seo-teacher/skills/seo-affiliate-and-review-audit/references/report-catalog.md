# Report Catalog — how to build each dimension

Per-dimension authoring guidance. Every finding is a dict **{issue, sev, evidence,
solution, execution}** (see `methodology.md` §9–10). `evidence` is measured or verbatim;
`execution` is the literal steps + how to verify. Build only the dimensions the inputs
support; note the dropped ones on the cover.

## 1 · Affiliate-Link Integrity  — *script + author*
The spine. From `fetch_affiliate_links.py` (or the outbound-link export) you get, per
outbound link: `page_url, anchor, destination, final_url, network, http_status, rel,
placement`. Author:
- **Missing/weak `rel`** — count links where `rel` lacks `sponsored`/`nofollow`; group by
  page; quote the actual `rel=""`. This is usually the headline (the FWD case: 445 links
  still untagged after the tag task was marked "done" — a **regression**, so check any
  task log).
- **Dead / redirected-off-product** — list every affiliate `final_url` that is 4xx/5xx or
  a 301 into a login/homepage (legacy networks like `wellevate.me`).
- **Wrong-network remnants** — links to a sunset network that should be re-pointed.
- Output the full inventory as its own XLSX tab. Verdict per link: OK / Add-rel /
  Dead-fix / Re-point / Review-manually.

## 2 · Monetization Tracking & Attribution  — *script + author*
- From the page markup: which **GTM/GA containers** load (flag duplicates), whether an
  **outbound-click event** is wired, whether affiliate links carry a **sub-ID/UTM** so
  the dashboard can attribute the source page.
- If an affiliate-dashboard export is supplied, **reconcile** on-site outbound clicks
  vs dashboard sessions and call out the gap.
- Evidence = the container ids found, the event handler (or its absence), a sample
  affiliate URL with/without a sub-ID. Fix = the exact tag/dataLayer change + how to
  verify in DevTools ▸ Network.

## 3 · FTC / Affiliate Disclosure  — *author*
- Per money/review page: is there a disclosure, is it **above the first affiliate link**,
  is it on-page (not footer-only)? Quote the sentence + its position.
- Fix = a verbatim disclosure line to paste above the first link, with placement
  instruction. Severity High where money links exist with no proximate disclosure.

## 4 · Review Voice (archetype-aware)  — *author, Claude-native*
- **Classify** each reviewed page: product-review / roundup / comparison / how-to /
  personal-experience / informational. State the archetype per page.
- Judge voice against **that archetype's** rubric (not one global rubric). The universal
  test: **first-hand experience signals** — original testing, specific measurements,
  own photos, honest cons, "who it's not for". Quote a passage that shows presence or
  absence.
- Fix = the specific rewrite direction for that archetype (e.g. "add a tested-it-myself
  paragraph with a measured result + one original photo"), never "add words".

## 5 · Rating / Score-System Scope  — *author + schema*
- Is the site's score (Fuel Score / stars / 1–10) applied **only** to genuine reviews?
  List any informational post carrying a score (scope creep). Is the scale consistent
  and its rubric stated? Is it reflected in schema honestly?
- Fix = remove the score from non-reviews, publish the rubric, align schema.

## 6 · Review & Product Schema  — *script + author*
- From the JSON-LD parse: presence/validity of `Review`, `Product`, `itemReviewed`,
  `AggregateRating` on review pages. **Guard**: an `AggregateRating` on the site's own
  offering with no collected reviews = a violation (Methodology §8) → remove-or-
  substantiate. On third-party product reviews, `itemReviewed` = the product,
  `Review.author` = the site/author.
- Evidence = the JSON-LD block (quoted). Fix = corrected JSON-LD (Find ▸ Replace).

## 7 · Affiliate-CTA Conversion Path  — *author*
- The money moment: is the affiliate CTA present, above the fold, compelling, and does
  it survive on mobile? Is there a **global nav CTA** to the affiliate hub (e.g. a
  Fullscript store link) so every page can convert?
- Evidence = CTA copy + position (desktop/mobile). Fix = the CTA placement/copy change.

## 8 · Action Items  — *author, revenue-weighted*
- Consolidate every finding into a prioritized list, **weighted by revenue/traffic ×
  severity** (Methodology §9). Columns: Issue · Evidence · Solution · Execution · Effort
  · Priority (P0 week / P1 30d / P2 60–90d). If a **task log** was supplied, tag each
  item done / regressed / open and surface regressions first.

## Assembly
`report_data.py` holds all authored dicts/lists. `build_html.py` and `build_xlsx.py`
both `import report_data as RD` and render at **parity** (a new measured layer goes in
both). Reuse built-in report branding. Validate: balanced tags/tables, no leftover
`{RD.` placeholders, headline counts match arrays, XLSX tab count matches the index.
