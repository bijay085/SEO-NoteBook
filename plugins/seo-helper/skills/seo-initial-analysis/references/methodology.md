# Methodology

The non-obvious rules behind the initial analysis. Read before authoring Reports
3, 5 and 8 — they are where a run goes wrong if improvised. Everything here turns an
entity into a defensible page architecture grounded in **real** demand, without
fabricating a single number.

## 1. The KG-equivalent EAV (Report 3)
Build the client's own miniature knowledge graph around ONE central entity, the way
Google's Knowledge Graph models it. Four passes:

1. **Anchor the entity.** Pull the Wikipedia article + Wikidata item for the central
   entity. Record the real relationships: `instance of`, `subclass of`, `part of`,
   `practiced by`, `uses`. These are the spine — the parent classes and sibling
   entities Google already associates with the entity (e.g. Food Photography →
   `instance of` photography genre, `subclass of` still-life / commercial photography).
2. **Salience layers.** Place every related concept on a layer:
   - **L0 — core identity / money terms.** What a buyer types to buy the thing
     ("<entity> service", "hire <entity>", "<entity> pricing / cost").
   - **L1 — attributes / dimensions.** The facets that multiply the entity into many
     pages (the client's `entity.dimensions`): type, use-case, audience, platform,
     equipment, style, location. Each dimension is an **Attribute**.
   - **L2 — the bridge.** The client's angle onto the entity (`entity.bridge`, e.g.
     "…by AI"). Low current demand, high conversion — introduced *on* the page, not
     chased as a head term.
3. **EAV rows.** For each dimension: Entity → Attribute → **Values** (the child
   entities, from the KG + real keyword data) → the human-language **query patterns**
   that attract each value. Values are never invented; volumes come from the engine.
4. **Relationship graph + entity→page map.** Draw entity→dimension→value edges, then
   assign each cluster of values to exactly one page (the de-cannibalization spine).

## 2. Framenet roles (fill every page's frame)
A money page ranks and converts when it fills the semantic frame around the entity:
**Actor** (who provides it) · **Service** (the entity action) · **Location** (where) ·
**Value** (the dimension / child) · **Proof** (reviews, credentials, E-E-A-T) ·
**Action** (the CTA / how to buy). A page missing Proof or Action is an EAV table, not
a ranking asset. Audit every planned page against the six roles.

## 3. Salience-driven funnel (Report 8)
Demand is a pyramid: broad **L1 "Dimension + <entity>"** searches at the top, the
narrow **L2 bridge** at the bottom. So:
- **TOFU** — capture broad L1 dimension demand ("<food type> photography",
  "<platform> food photos") with informational + category pages.
- **MOFU** — the entity's commercial terms ("<entity> service / pricing / examples").
- **BOFU** — introduce the **bridge + convincing dimensions** on the page (cost, no
  equipment, no crew, minutes-not-days) to convert the L1 visitor to the L2 offer.
Never build a site that only targets the L2 conclusion — its demand is too thin.

## 4. Keyword engine → topical map (Reports 4–5)
- Seed the engine from the EAV dimensions + L0 money terms, not from guesswork.
- Enrich every keyword with **search volume + difficulty + SERP intent** (DataForSEO).
- Cluster by SERP overlap / head-term; per cluster record **aggregate SV**,
  **variation richness** (distinct queries), dominant **intent**, and the single
  **page type** it maps to.
- **Location pages are a coverage / local-pack play, not an organic-traffic play.**
  Bare "<service> <city>" terms are usually ~0 SV; the real geo organic demand is
  regulation / license / cost / "is it legal". Justify city pages as local-pack +
  internal-link coverage, and put the organic bet on the regulation/cost content.

## 5. De-cannibalization spine
One intent → one canonical page. Before planning, map every cluster to exactly one
page type; siblings link **up** to the category, they don't compete for the same term.
Two pages chasing one intent is the most common self-inflicted ranking loss.

## 6. Verify, don't trust (Report 2 + everywhere)
Every given claim is checked against the live source before it enters a report:
- "Live" pages → fetch them (HTTP 200 + real content, not a stub or redirect).
- Review counts / ratings → open the actual profile; reconcile against the site's
  stated number and **flag overstatement** (e.g. a site claiming "5,000+ / perfect
  5-star" against a verified 2,299 / 4.93★). Hold the trust-line copy until the client
  substantiates.
- Competitor stats → confirm on the live SERP, not from the client's deck.

## 7. Never fabricate
No search volume, review count, ranking, or "typical" figure is invented. If it is not
measured, write "not yet measured" and name the exact pull that would get it. A faithful
gap beats a confident fabrication — that is the line the whole deliverable is trusted on.
