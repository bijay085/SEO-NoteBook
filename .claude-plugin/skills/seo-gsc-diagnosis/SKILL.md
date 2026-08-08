---
name: seo-gsc-diagnosis
description: >-
  Fact-first SEO diagnosis for ecommerce stores (especially Shopify) that leads with first-party
  Google Search Console data plus HTTP/canonical verification BEFORE any web research. Use this
  whenever someone wants to audit or diagnose an ecommerce site's organic performance: "why isn't
  my site/blog ranking", "why do my pages get impressions but no clicks", keyword cannibalization
  or duplicate-URL audits, topical authority / content-gap analysis, "organic traffic dropped",
  interpreting Search Console data, or any Shopify/ecommerce SEO triage : even when the user never
  says the words "GSC" or "Search Console". The skill enforces checking real data and HTTP status
  codes before making any claim, which is the whole point: it prevents expensive false reports and
  stops you from burning tokens on broad research sweeps for things first-party data already answers.
---

# SEO GSC Diagnosis (fact-first)

## Why this skill exists

The expensive way to do an SEO audit is to reason from general SEO knowledge, spin up a broad
web-research sweep, and write a confident report. That fails twice: it burns enormous tokens
re-deriving best practices you already know, and it produces **plausible-but-false claims** because
it never looked at the site's actual data.

The specific trap this skill was built to kill: declaring "systemic keyword cannibalization" from a
list of duplicate-looking URLs in Search Console : when those duplicates were already 301-redirected
to a single canonical page and were a *non-issue*. The only thing that revealed the truth was
checking HTTP status codes. **A 200-vs-301 check is ~50 cheap requests; a wrong report costs the
client's trust.**

So the rule is simple: **first-party facts first, verify before you claim, and only reach for the
web when the site's own data genuinely can't answer the question.**

## The run route

Do these phases in order. Each phase gates the next : resist jumping to recommendations before the
facts and the verification are in.

### Phase 0 : Scope & access
- Identify the GSC property. Run `list_accounts` / `list_sites`. If multiple accounts exist, you
  **must** pass the `account` param on every call or it errors. Prefer the **domain property**
  (`sc-domain:…`) when permissioned; fall back to the URL-prefix property (`https://…/`) if the
  domain one returns "insufficient permission."
- Set a date window (default last ~3 to 6 months; GSC lags ~2 to 3 days, so end ~2 days before today).
- Pull the sitemap(s) for a page inventory: `list_sitemaps`, and/or fetch `/sitemap.xml`.

### Phase 1 : First-party facts (GSC)
This is the cheapest, highest-signal data, and most diagnoses live entirely here. Pull, in order:
- **Top pages** by clicks AND by impressions: `get_top_pages` (look at clicks, impressions, CTR,
  position together : never clicks alone).
- **Top queries**: `query_search_analytics` with `dimensions:["query"]`.
- **Cannibalization candidates**: `query_search_analytics` with `dimensions:["query","page"]`,
  high `rowLimit`. This export is large : it usually exceeds the token limit and gets saved to a
  file. Run `scripts/cannibalization_scan.py <file>` on it instead of reading it raw.
- **Page-2 opportunities**: `find_keyword_opportunities` (high impressions, low CTR, pos ≤ 20).

See `references/gsc-playbook.md` for exact call recipes and gotchas.

### Phase 2 : Verify before you claim (THE GATE)
Two specific claims are forbidden until verified, because both are easy to get wrong from GSC alone:

1. **"This is a ranking problem."** First separate the two failure modes (see *Reading the data*).
   A page at average position 4 to 6 is **not** a ranking failure : if its CTR is near-zero it's a
   *zero-click / SERP-feature* problem, and "write more / build links" is the wrong fix.

2. **"These duplicate URLs are cannibalizing."** Never assert this from the query×page export alone.
   The competing URLs may already be 301'd or canonical-tagged to one page. **Run
   `scripts/check_urls.sh`** on every suspected duplicate set and read the result:
   - clean slug **301 →** one `200` self-canonical twin = *already consolidated, not a problem.*
   - **two live `200`** pages that **self-canonical** = *real cannibalization,* worth fixing.
   - `404` = gone, ignore.

### Phase 3 : Targeted benchmark only if needed
If : and only if : a question genuinely can't be answered from first-party data (e.g. "what content
clusters do competitors X and Y cover that we don't"), fetch those **specific** pages with WebFetch,
or run a couple of narrow WebSearch queries. Do **not** launch a broad multi-agent research harness
for things that are common SEO knowledge or that GSC already answers. If you find yourself about to
research "what is keyword cannibalization" or "does E-E-A-T matter," stop : you already know it.

### Phase 4 : Synthesize (commercial-first, every claim cited)
- Map each finding to a **page-type / intent** action (see *Don't merge across intent*).
- Lead with structural fixes that need **no new content** (they're the cheapest wins).
- For a store, weight **commercial + local + product/collection** outcomes over informational
  traffic : content exists to move product, not to win zero-click trivia.
- Every problem statement cites the exact data point that proves it (a GSC row, an HTTP status, a
  fetched line). No claims from general knowledge.

## Reading the data (the heuristics that matter)

**Rank failure vs CTR/zero-click failure** : the distinction the whole audit hinges on:
- Position > ~10 with impressions → genuine **ranking** problem → content/links/structure.
- Position ≤ ~8 but CTR well under ~1% on big impressions → **zero-click SERP**: AI Overviews,
  featured snippets, and People-Also-Ask answer the query on the page. The fix is *SERP-feature
  capture* (tight 40 to 55-word answer blocks, FAQ schema) or *pivoting to query types that still get
  clicks* : not "rank higher," because you already rank.
- "Can dogs eat X" / "is X safe" / definitional informational queries are the classic zero-click
  class. A store ranking these wins impressions, not revenue.

**Where a store actually gets clicks** : scan top queries for healthy CTR (≳3%): these are usually
**commercial, local, and branded** ("treats near me", "<product> for dogs", "<city> <category>",
brand terms). If those rank poorly (page 2) they are the highest-value opportunity : a transactional
domain can win them, unlike informational head terms dominated by PetMD/AKC-type publishers.

**Quick wins**: tool/calculator/comparison pages and money pages sitting at position 11 to 20 with real
impressions. Page-1 push is cheap relative to net-new content.

**Cannibalization candidates ≠ cannibalization.** The scan finds queries served by 2+ of the site's
URLs. That's a *candidate list*. It only becomes a finding after Phase 2's status/canonical check.

## Don't merge across intent

Different search intents map to different page **types**, kept separate and **interlinked** : never
merged. Merging only ever applies to two pages of the *same* type/intent.

| Query | Intent | Page type |
|---|---|---|
| "can dogs eat chicken" | informational | **blog** post |
| "chicken dog treats" | commercial / category | **collection** |
| "chicken jerky for dogs" | transactional | **product** |

Wire them into a funnel (blog → collection → product, with in-content contextual links : sidebar/
footer boilerplate links are heavily discounted for passing topical signal). Consolidate only true
same-type duplicates, and only after verifying they're live 200s (Phase 2).

## Output structure

Lead with the single most important verified fact, then organize as:

```
## Headline finding (the one verified fact that reframes everything)
## What the data shows (facts, each with its GSC row / HTTP status / fetched evidence)
## Diagnosis (rank vs CTR vs structural : only verified claims)
## Priorities (sequenced; structural/no-content fixes first; commercial-weighted)
## What I did NOT verify / assumptions (be explicit about confidence)
```

If you walked back an earlier claim because verification contradicted it, **say so plainly** : an
honest correction builds more trust than a tidy report that hides the reversal.

## Bundled scripts

- `scripts/check_urls.sh` : the verification gate. Pass URLs as args or pipe a list on stdin;
  prints `HTTP status | url | redirect target | rel=canonical` per URL. Run this before ANY
  duplicate/cannibalization claim. Works on macOS bash 3.2 (no `mapfile`).
- `scripts/cannibalization_scan.py` : feed it the saved query×page GSC export; prints queries served
  by 2+ distinct normalized URLs (anchors/utm stripped), ranked by page-count then impressions.
  Output is a candidate list to feed into `check_urls.sh`, not a conclusion.

## References

- `references/gsc-playbook.md` : exact GSC MCP call recipes, multi-account/permission gotchas,
  date-window guidance, and how to handle the oversized query×page export.
