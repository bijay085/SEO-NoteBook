# QDP — Query Deserves a Page (the page-decision gate)

QDP decides, for every candidate query/topic in the map, whether it earns its **own
page** — or **merges** into a parent page as a heading, becomes a **keyword variant**
of an existing page, or is **dropped**. Run it as a **BATCH** over the whole extracted
keyword set for the site (or a segment), never one query in isolation — the decision
is relative to the other entities and, above all, to the **parent**.

## The test: 4 rules — a query deserves a page if ≥ 3 of 4 pass
1. **Has good search volume** — real demand exists. **DATA rule:** the number comes
   only from DataForSEO; if none has been pulled yet it is `null` (undecided) —
   **never assumed**.
2. **Different entity in query** — is the candidate a genuinely different entity
   **from its parent**? (Its own node, not the parent restated or a thin facet of it.)
3. **Low similarity** — is the candidate's overlap **with its parent** low? A shared
   head term / subset relationship = HIGH similarity = this rule **FAILS**.
4. **Traceable search pattern** — a consistent, repeatable query shape exists around
   the entity (e.g. `{service} cost`, `how much does {service} cost`).

### Comparison basis (critical — this is where it usually goes wrong)
- Rules **#2 and #3 are ALWAYS tallied against the PARENT entity** when a parent
  exists — **never sibling-vs-sibling**. No parent → compare to the central entity /
  nearest ancestor.
- Rules **#1 and #4** are data / pattern facts (not relative).
- **#2 is categorical** (is it its own node at all?); **#3 is degree** (how far from
  the parent does that node sit?). Different questions, both parent-anchored.

### Evaluation order (entity-first, volume-last)
1. mark **different entity** → 2. resolve **parent–child** → 3. **similarity** →
4. **search pattern** → 5. **search volume**. Doing entity work first stops a
high-volume query from getting its own page when it is really the parent restated
(pure cannibalization).

## Outcomes
- **≥ 3/4 → own page** (then classify Core/Outer + Blog/Landing).
- **2/4 (typically because #3 fails on parent overlap) → merge as a dedicated H2
  heading** under the parent page.
- **#2 AND #3 both fail** (same entity, only phrasing differs — e.g. "seo cost" vs
  "how much does seo cost") **→ keyword variant** of the parent page (same target,
  not even a heading).
- **< 2/4 or noise → drop** (record in the Review sheet with the reason).

## SERP arbiter (breaks every borderline; confirms the rest)
Google the query — or pull `mcp__dataforseo__serp_organic_live_advanced` — and read
page 1:
- **≥ 60% of page-1 results are pages DEDICATED to that exact query/entity → it
  deserves its own page** (Google is already ranking dedicated pages for it).
- **page 1 surfaces PARENT-query (broad) pages instead → it does NOT → merge as a
  heading** under the parent.

This is the strongest signal available — Google itself reveals whether the query
warrants a dedicated page. Use it on every 2–3/4 candidate.

## How this skill computes each rule
| Rule | Source in this skill |
|---|---|
| #1 volume | DataForSEO (`dataforseo_labs_google_keyword_overview` / `kw_data_google_ads_search_volume`) |
| #2 different entity (vs parent) | the entity ontology — is the candidate a distinct node from its parent (`ontology_layer` chain), or the parent restated? |
| #3 low similarity (vs parent) | ontology parent–child + similarity: shared head term, subset relation, salience proximity to the parent |
| #4 traceable pattern | the anchor-pattern library (see [value-typing-noise-anchors.md](value-typing-noise-anchors.md)) |
| SERP arbiter | `mcp__dataforseo__serp_organic_live_advanced` / `dataforseo_labs_google_serp_competitors` — classify page-1 results dedicated vs parent |

## Worked example — SEO agency, "cost + service" segment, parent = "SEO (cost)"
Every candidate is tested **against the parent**, not against each other:

| Candidate | #2 diff from parent | #3 low sim to parent | #4 pattern | #1 volume | Verdict |
|---|---|---|---|---|---|
| seo cost / how much does seo cost | — (this IS the parent) | — | ✓ | need data | **Parent hub page**; the two phrasings are keyword variants of it |
| on page seo cost | weak (sub-facet, shares "seo") | ✗ high overlap | ✓ | ? data | 2/4 firm → **heading**, unless SV strong + SERP shows dedicated → page |
| off page seo cost | weak | ✗ | ✓ | ? data | same |
| local seo cost | weak–moderate (geo shifts intent) | ✗ | ✓ | ? data | same; local is often promoted by the SERP test |
| seo audit cost | moderate (audit is a distinct deliverable) | ✗–~ | ✓ | ? data | borderline → SERP decides |

Because #3 fails on parent overlap, each child sits low on the count and the verdict
**cannot be called without real SV + the SERP check.** QDP is a data-driven batch
test, not a paper exercise. Default lean for a 2/4 child: heading under the hub.

## Record in ontology.json (per candidate, inside `pages[]`)
```
"qdp": {"volume": true|false|null, "different_entity": bool, "low_similarity": bool,
        "pattern": bool, "score": 0-4, "serp_verdict": "dedicated|parent|na"},
"decision": "page|heading|variant|dropped",
"merge_into": "<parent page slug/title, or null>"
```
`score` = count of the 4 rules that passed (a `null` volume counts as not-passed for
the score but is shown as `?`, signalling "pull the data to finalise").
