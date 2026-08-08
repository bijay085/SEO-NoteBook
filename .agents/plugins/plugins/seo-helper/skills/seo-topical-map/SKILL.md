---
name: seo-topical-map
description: >-
  Build a topical authority map AND a demand-gated page plan around ONE central
  entity : entity ontology with salience layers + a 13-bucket attribute map, then
  value-typed templates from real keyword clusters, a QDP (Query-Deserves-a-Page)
  4-rule decision per candidate, Koray-school semantic-SEO adjustments, a noise/QA
  pass, and a Blog/Landing split : exporting a branded XLSX (ontology + AMR page
  plan + review) / HTML / JSON that feeds the off-page workflow. Use when a user
  asks to "build a topical map", "topical authority map", "entity ontology", "topic
  cluster / content map", "content architecture for [brand/topic]", "how many blogs
  per value", "which queries deserve a page", "split blogs vs landing pages", "clean
  the noise", or "add keyword data / search volume to my topical map". CLAUDE-NATIVE:
  Claude does all reasoning in-context (no OpenAI/Gemini/Anthropic API) : the only
  external calls are DataForSEO via its MCP (real volumes + SERP) and WebFetch.
---

# Topical Map (Claude-native) : ontology → demand-gated page plan

Turns a central entity + controlled sources into (1) an **entity ontology** with
salience-based relevance layers and a 13-bucket attribute map, and (2) a **page-level
content plan** where every candidate page has passed a **QDP (Query Deserves a Page)**
decision backed by real demand. Exports `entity_ontology.xlsx` (ontology sheets **+**
the AMR page plan **+** a Review/noise sheet) + `.html` + `.json`.

**Merged skill:** the ontology engine (this skill) + the page-planning methodology
(value typing, anchor clustering, QDP, Koray-7, noise/QA, Blog/Landing, AMR
deliverable). Claude does every pass in-context; the sole external data is DataForSEO
via MCP (volumes + SERP) and WebFetch for approved source URLs.

## Inputs
- **Central entity** : name, type (LocalBusiness / Product / Concept / …), domain,
  one-sentence definition, aliases; plus every **sub-entity/segment** to cover.
- **Sources** : DOCX / approved URLs / pasted text. **INFERENCE mode:** `DATABASE_ONLY`
  (every fact traces to the corpus) or `INFERENCE_ALLOWED`. Default `DATABASE_ONLY`.
- **Existing content/keyword assets** : prior maps, competitor URLs → layer in, don't discard.
- **Geography** : local SEO triggers the location to service adjustment (Koray #4).
- **Workspace** `<ws>` : for `corpus.txt`, `ontology.json`, and the exports.

## The ontology model (unchanged)
**Entity record:** `relevance_layer, entity_name, entity_type, salience, ontology_layer,
relationship_type, short_definition, entity_definition, relational_definition, aliases[],
primary_bucket, secondary_bucket`. **Salience** 0 to 1 vs the central entity (central = 1.0).
**Relevance layers:** Core / Primary (~0.75+) / Secondary (~0.45 to 0.75) / Outer (<0.45).
Entities with salience > 0.45 get cross-entity relationships (Phase 5). **13-bucket
attribute taxonomy:** Types · Components/Parts · Methods · Services · Target Problems ·
Tools/Products · People/Roles · Providers · Regulators · Certifications · By Location ·
Concepts · Domain-Specific.

## Procedure : you run these phases (no subprocess LLM)
```
TM="${SKILL_DIR:-.}"; WS="<ws>"
```

**Phase 0 : Pre-flight.** Confirm central entity + sub-entities + sources + INFERENCE
mode + geography + output focus (ontology only, or full page plan). State the run plan.

**Phase 1 : Corpus (6-layer EAV).** Get source text : run
`python "$TM/scripts/topical_map.py" sources --docx a.docx --url https://… --out $WS/corpus.txt`
and/or WebFetch approved URLs. Build Entity→Attribute→Value triples from as many layers
as available: (1) authoritative docs, (2) commercial taxonomy, (3) competitor site
structure, (4) search-demand data, (5) SERP + People-Also-Ask, (6) voice-of-customer.
Cross-reference and dedupe. Don't extract the final entity list yet.

**Phase 2 : Entity extraction.** Extract every entity with a specific articulated
relationship to the central entity; set `entity_type`, `salience`, and the three
definitions. Under `DATABASE_ONLY`, every entity traces to the corpus.

**Phase 3 : Ontology mapping.** Set `ontology_layer` (parent chain: root/branch/child)
and `relationship_type` (HAS_TYPE, HAS_PART, USED_IN, PERFORMED_BY, REGULATED_BY, …).
**This parent chain is what QDP rules #2/#3 are tallied against : get it right.**

**Phase 4 : Relevance layers.** Assign each entity's `relevance_layer` from salience.

**Phase 5 : Cross-entity map.** For entities with salience > 0.45, map direct
relationships + note clusters + **similarity** to parents/siblings (feeds QDP #3).

**Phase 6 : Value typing.** Tag every Value with a **type** (FIXTURE, SERVICE, PROBLEM,
…) : this gates which templates it may take. Extend the type set per niche. See
[references/value-typing-noise-anchors.md](references/value-typing-noise-anchors.md).

**Phase 7 : Keyword enrichment (DataForSEO via MCP).** Per value/entity, pull real
volume/KD/CPC/intent : `mcp__dataforseo__dataforseo_labs_google_keyword_overview` or
`…_kw_data_google_ads_search_volume`, and `…_bulk_keyword_difficulty`. **Real metrics
only** : empty if DataForSEO has none; if the MCP isn't connected, say so and mark
volume `null` (QDP #1 stays undecided). Save large pulls to `$WS/kwfiles/<value>.json`;
for many values, fan out to subagents that write files + report paths.

**Phase 8 : Data-derived clustering.** Cluster each value's keywords by anchor pattern
(the library in the reference file); primary keyword = highest-SV in the cluster;
cluster SV = sum; title from value+anchor. A coherent anchor set = a **traceable
pattern** (QDP #4). Prefer an LLM clustering pass (you) over the raw regex; keep the
regex as the base layer.

**Phase 9 : QDP decision (the gate).** For every candidate page, run the **4-rule,
3-of-4** test and record `decision ∈ {page, heading, variant, dropped}`. Rules:
**#1 good volume** (DataForSEO; never assume), **#2 different entity vs PARENT**,
**#3 low similarity vs PARENT**, **#4 traceable pattern**. #2/#3 are always
parent-relative (fall back to the central entity if no parent). Break every borderline
(2 to 3/4) with the **SERP 60% arbiter** (`mcp__dataforseo__serp_organic_live_advanced`):
≥60% of page-1 results dedicated → own page; parent-query pages dominate → merge as a
heading. Full logic + worked example: [references/qdp.md](references/qdp.md). **Do not
call a candidate without real SV + the SERP check : QDP is a data-driven batch test.**

**Phase 10 : Koray-school semantic-SEO adjustments (apply all 7):**
1. **QDP gate** (Phase 9) : prune/merge thin pages.
2. **Macro/micro → Core/Outer** : dominant intents (Cost, How-to Fix, Install/Replace,
   Troubleshooting, Problem/Why) are `section: Core`; supporting ones `Outer`.
3. **E-A-V triples** : (Entity, attribute, Value) feeds schema markup + internal-link anchors.
4. **Location to service pairs** (local only) : canonical service page at root; city pages
   only where local demand clears the bar; neighborhoods fold into the parent city.
   No location page-spam.
5. **Anti-cannibalization** : merge near-duplicate targets into one canonical page (this
   is QDP #3 in action).
6. **Multi-tier internal links** : root → category hub → page; anchor = child's H1/title.
7. **Central-entity/intent anchor** : score each page's salience by proximity to the
   central entity's core intent, not in isolation.

**Phase 11 : Noise / QA pass.** Classify every generated row (dup-word artifact,
cross-product contamination, service/type mismatch); route flagged rows to `review[]`
with a reason : never silently delete. Recompute all counts from the kept set. See the
reference file §3. Pure local re-processing, no API cost.

**Phase 12 : Blog vs Landing split.** Classify each kept page: inherently informational
categories (How-to Fix, Symptoms, Problem/Why, Troubleshooting, Types/Comparison,
Maintenance, Cost, How-to Install) → **Blog**, unless the primary keyword is genuinely
transactional service-intent (near me / repair / install / emergency / contractor +
intent=transactional) → **Landing**. Buying/Best → Landing. Set `page_type`.

**Phase 13 : Assemble `ontology.json`** (see schema below): fill `entities[]`,
`attributes[]`, `keywords[]`, **`pages[]`** (the QDP page plan), and **`review[]`**
(noise removed). Merge duplicate entities to a canonical name; report thin/empty
buckets as gaps.

**Phase 14 : Export & deliver.**
```
python "$TM/scripts/topical_map.py" export --in $WS/ontology.json --out $WS/Deliverables
```

## ontology.json schema
```json
{
  "central_entity": {"name":"","type":"","domain":"","definition":"","aliases":[]},
  "summary": "phase-6 summary prose",
  "entities": [{"relevance_layer":"Primary","entity_name":"","entity_type":"","salience":0.8,
    "ontology_layer":"child","relationship_type":"HAS_TYPE","short_definition":"",
    "entity_definition":"","relational_definition":"","aliases":[],
    "primary_bucket":1,"secondary_bucket":null}],
  "attributes": [{"entity":"","attribute":"","business_attribute":"","value":"","entity_role":"",
    "buyer_context":"","commercial_relevance":"","template_assigned":"","template":"",
    "template_family":"","section":"","keyword":"","sv":null,"kd":null,"cpc":null,"slug":"",
    "title":"","kw_source":"","page_status":"","kw_fit":"","priority":"","kw_rejection_note":""}],
  "keywords": [{"entity_name":"","kind":"","relevance_layer":"","salience":0.8,"primary_kw":true,
    "keyword":"","volume":null,"kd":null,"cpc":null,"intent":"","trend":"","kw_type":""}],
  "pages": [{"entity":"","attribute":"","value":"","decision":"page|heading|variant|dropped",
    "merge_into":null,"section":"Core|Outer","page_type":"Blog|Landing","title":"","slug":"",
    "primary_keyword":"","sv":null,"kd":null,
    "qdp":{"volume":null,"different_entity":true,"low_similarity":false,"pattern":true,
      "score":3,"serp_verdict":"dedicated|parent|na"},"note":""}],
  "review": [{"entity":"","attribute":"","value":"","category":"","title":"","slug":"",
    "keyword":"","sv":null,"page_type":"","reason":""}]
}
```
`pages[]`/`review[]` are optional : omit them for an ontology-only run and the exporter
skips those sheets.

## Export deliverables
Writes `entity_ontology.xlsx` : sheets **Topical Map** (overview) · **Full Ontology** ·
**Attribute Map** · **Keyword Data** · **Page Plan (AMR+QDP)** · **Blog Count by Value**
· **Review (Noise Removed)** : plus `entity_ontology.html` and `entity_ontology.json`,
branded. The XLSX/JSON feed the off-page workflow.

## Setup
```
pip install -r "$TM/requirements.txt" # just openpyxl
```

## Rules
- **Source-grounded** (`DATABASE_ONLY` unless told otherwise) and **real metrics only**
  (volumes/SERP from DataForSEO; `null` if unavailable : QDP #1 stays undecided).
- **QDP is parent-relative and data-driven** : #2/#3 vs the parent, #1 from real SV,
  every borderline settled by the SERP 60% check. Never mint a page by assumption.
- **Review before delivering** : merge duplicates, run the noise pass, report gaps.
- **Honesty about scope** : state INFERENCE mode, any undecided QDP rows (no data), and
  any pass skipped (e.g. SERP check not run).

> v4.0.0 merges the `seo-topical-map` methodology into the Claude-native ontology skill.
> QDP is the corrected 4-rule (3-of-4) test with parent-relative #2/#3, volume strictly
> from DataForSEO, and the SERP 60% arbiter. References: [qdp.md](references/qdp.md),
> [value-typing-noise-anchors.md](references/value-typing-noise-anchors.md).
