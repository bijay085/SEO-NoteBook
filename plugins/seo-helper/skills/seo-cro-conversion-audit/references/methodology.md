# CRO Audit — Methodology

Why this beats a mechanical scan: the scan is only Stage 3. The confidence comes
from correcting it, corroborating it with real behavior, verifying it live, and
binding every claim to evidence.

## The six-part discipline

1. **Extract** — run the scripts to get per-domain signals, draft 0-10 scores, a
   form field/test model, and per-page Clarity behavior. Deterministic.
2. **Correct** — open the raw HTML and fix mechanical false positives (see the
   catalogue below). This is where most of the credibility is won or lost.
3. **Corroborate** — cross-check every architecture inference against real
   Microsoft Clarity click/scroll/attention data. An inference confirmed by
   behavior is a finding; one contradicted by behavior is dropped or reframed.
4. **Verify live** — resolve every ambiguous selector against the live page (what
   *is* `.vs-btn` / `#customteam-next`?). Never ship a guess about an element.
5. **Evidence-bind** — every score, gap and recommendation carries a concrete
   evidence line (a selector, a byte count, a decoded popup id, a click %).
6. **Report** — branded XLSX + HTML; recommendations span every area the data
   supports, ranked by priority.

## Scoring rubric (0-10)

Five dimensions, scored per domain. `cro_signals.py` emits **drafts**; Stage 4
(Correct) sets the finals by inspection.

| Dimension | What it measures | Raises it | Lowers it |
|---|---|---|---|
| **UI/UX** | Layout clarity, hero, visual hierarchy | Clear hero, real sticky nav | Heavy render-blocking payload, clutter |
| **Coverage** | Breadth of relevant service/landing pages | Many intent-matched service pages | Thin / single-page presence |
| **Page** | On-page conversion completeness | Real lead form, pricing, depth | No form, no pricing, thin copy |
| **CTA** | Clarity of the primary conversion path | One specific primary CTA, phone present | CTA sprawl with no hierarchy |
| **Trust** | Proof at the decision point | Quantified reviews, testimonials, guarantee, badges | No stat, proof absent from the conversion page |

`Overall` = mean of the five. Draft formulas live in `cro_signals.py::_score` and
are intentionally conservative — treat a draft as a hypothesis, not a verdict.

## Correction catalogue — false positives to re-check every time

The scripts already defend against these, but confirm on the raw HTML:

- **Tag-stripped competitor HTML.** A "save as" adds a `Mark of the Web` comment
  (`<!-- saved from url=(0014)about:internet -->`). A naive un-escaper can trip on
  it and strip every tag, zeroing competitor signals. `common.load_page` un-escapes
  only genuinely-escaped dumps and ignores the MOTW comment. If a competitor shows
  `avg_words≈0` or `has_form:false` implausibly, this is why — re-run on the raw file.
- **Review stats a regex misses.** Patterns like `4.9/5, 54+ local reviews` /
  `11 B2B reviews` sit between the number and the word "reviews." Confirm the
  `review_counts` list caught them; if a competitor visibly shows a rating you
  don't see in the JSON, add it.
- **"sticky" / "badges" from dormant CSS.** A match inside a `<style>` rule or a
  never-applied class is not a real element. Only count a sticky/badge you can see
  on a real body element.
- **Selector-path over-match (Clarity clicks).** A conversion keyword deep in a
  long CSS ancestor path is not a CTA click. `clarity_behavior` classifies on the
  **leaf** element; if a page shows an implausibly high conversion-click %, inspect
  its top rows.
- **Clarity folder/URL mismatch.** An export folder labeled one page may carry
  another page's data (Clarity's own URL regex is the truth). `integrity_issues`
  flags these — report the data under the URL Clarity actually recorded.

## Data models (the JSON contracts the report consumes)

**`cro_signals.json`**
```json
{"site_domain": "example.com", "dimensions": ["UI/UX","Coverage","Page","CTA","Trust"],
 "domains": {"example.com": {"is_site": true,
   "profile": {"pages": 2, "service_pages": 1, "has_sticky": false, "phone_present": true,
     "hero_frac": 0.5, "avg_words": 3055, "has_form": true, "trust_total": 40,
     "review_counts": ["4.9/5","54+ local reviews"], "guarantee": false, "badges": false,
     "testimonials": true, "lead_magnet": false, "pricing": true,
     "top_ctas": ["Get a Free Quote"], "specific_cta": true},
   "scores": {"UI/UX": 6, "Coverage": 3, "Page": 8, "CTA": 6, "Trust": 6, "Overall": 5.8}}}}
```

**`form_audit.json`**
```json
{"form_url": "https://example.com/contact-us/", "found": true, "field_count": 5,
 "fields": [{"tag": "input", "name": "email-564", "type": "email", "label": "Email Address",
   "required": true, "maxlength": "400", "pattern": "", "role": "email"}],
 "static_findings": 1,
 "test_plan": [{"id": "TC01", "category": "Happy Path", "scenario": "Valid full submission",
   "target_field": "form", "expected": "Submits.", "actual": "", "verdict": "", "severity": "", "fix": ""}]}
```

**`clarity_findings.json`**
```json
{"audit_date": "2026-07-16", "data_window": "07/17/2025 ... - 07/16/2026 ...",
 "methodology_note": {"classification": {"conversion": "...", "non_conversion": "...", "ambiguous": "..."},
   "reach_definition": "Scroll reach % per band = visitors / page_views."},
 "integrity_issues": [{"issue": "FOLDER/URL MISMATCH", "detail": "...", "handling": "..."}],
 "pages": {"Homepage": {"folder_label": "Homepage",
   "click": {"page_views": 4629, "conversion_click_pct": 0.45, "top_distractor": {"element": "#customteam-next", "clicks": 449},
     "ambiguous_for_review": [{"selector": "...", "clicks": 66}]},
   "scroll": {"biggest_single_band_drop": {"from_depth": 5, "to_depth": 10, "from_reach": 86.7, "to_reach": 46.7, "drop_pts": 40.0}},
   "attention": {"top_attention_band": {"depth_pct": 5, "pct_session": 28.83}}}}}
```

**`cro_verdict.json`** — authored in Stage 6 (headline, corrected scores, summary,
recommendations). Each recommendation is a COMPLETE unit —
`{priority, area, finding, evidence, impact, solution, steps[]}` — never a
one-liner; `steps` name the CMS/plugin, selector, and exact setting. Full schema
in `SKILL.md` Stage 6.

## Anti-patterns

- Reporting draft scores as final.
- A recommendation with no evidence line, or missing its Finding · Impact ·
  Solution · Executable steps (a one-line action is incomplete).
- Treating a missing input as a zero instead of requesting it.
- Using Clarity data flagged by an integrity issue without stating the caveat.
