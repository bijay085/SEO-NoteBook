---
name: seo-helper : accessibility-completeness-audit
description: >-
  Audit a live web page (or a page spec) on TWO dimensions at once and produce a
  branded SEO deliverable: (1) ACCESSIBILITY & SEMANTIC correctness : is the
  markup structured and exposed to the accessibility tree / machines correctly
  (semantic HTML5, landmarks, computed roles/names/states, allowed-ARIA per
  html-aria, keyboard/reading order, DOM size) : and (2) COMPLETENESS & TOPICAL/
  VISUAL SEMANTICS : does the page contain the semantic components its query-frame
  / page-type demands. Use whenever the user asks to "audit this page",
  "accessibility audit", "semantic HTML audit", "is this page complete / does it
  have the right sections", "page structure audit", "wireframe the correct
  structure", "convert this page to semantic HTML", or a per-page technical +
  structure + completeness review. Config-driven and industry-agnostic. Every
  finding carries Issue / Evidence / Solution / Execution and an evidence_basis.
  Deliverables: an A to F findings report AND a Miro-or-equivalent annotated
  wireframe. Merges the former "Accessibility Tree and Semantic HTML 5" and
  "Visual-Semantics-Research" engines.
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# Accessibility & Completeness Audit

One engine, two dimensions over the same page:

- **Accessibility & semantic correctness** : accessibility tree, semantic HTML5,
  landmarks, computed role/name/state, allowed-ARIA (html-aria), keyboard &
  reading order, DOM size.
- **Completeness & topical/visual semantics** : does the page carry the semantic
  components its query-frame / page-type requires (visual semantics, frame
  semantics, page-type coverage)?

## Core principle : sources are COMPILED, not CONSULTED
Every cited source was distilled **once** into concrete, machine-checkable rules in
`data/rules.csv`. At audit time the engine evaluates those frozen rules against the
page and makes **zero external calls** : it never re-reads an article or fetches a
URL. `source_id` is provenance; `evidence_basis` is the rule's authority. Any
measurement (DOM count, computed tree) comes from a local deterministic script, not
from eyeballing. This keeps every run cheap, deterministic, reproducible.

## How to run
1. Pick the **mode**: `AUDIT` (find issues) · `CONVERT` (emit corrected semantic
   markup) · `AUDIT_AND_REPAIR` (both).
2. Identify the **page type** (see `templates/`). Apply: **all global rules**
   (`templates/global_template.md`) + the **page-type's** rules + only the
   **triggered** component rules. A page-type may refine but never disables
   accessibility / truthfulness / evidence rules.
3. Evaluate each applicable rule in `data/rules.csv` against the page. Record a
   finding with the fields in `data/finding_fields.csv` : always Issue · Evidence ·
   Solution · Execution, plus `verification_level` and the rule's `evidence_basis`.
4. Emit **both** deliverables (see `templates/output_schema.md` and
   `templates/wireframe_output_schema.md`).

## Data (the engine)
- `data/rules.csv` : 80 rules, 14-col unified schema, `dimension` ∈
  {accessibility, completeness}. `data/rules_crosswalk.csv` maps every `ACC-####`
  back to its origin engine + original id.
- `data/allowed_aria.csv` : allowed/prohibited ARIA roles & attributes per element
  (html-aria). `data/accessibility_mappings.csv`, `data/elements.csv` : computed
  role/name/state and semantic-HTML tag reference.
- `data/sources.csv` : provenance registry. `data/finding_fields.csv` : finding
  schema.
- **Read `references/evidence-and-verification.md` before asserting anything** : it
  defines the two evidence vocabularies and the hard rule that keeps unverified
  visual-semantics claims from being stated as standards.

## Scripts (deterministic : no LLM, no live source calls)
- `scripts/measure.py <url|file> [out.json]` : DOM node count / depth / children
  (+ Lighthouse verdict), landmarks, headings, images (missing alt), forms. The
  measured evidence for the accessibility + DOM rules : no eyeballing.
- `scripts/build_report.py findings.json [metrics.json] [out.html]` : renders the
  A to F findings report (jump-nav, accordions, Issue·Evidence·Solution·Execution
  cards, verdict chart) via `report_kit.py`.
- `scripts/build_wireframe.py regions.json [out.svg]` : the REQUIRED annotated
  wireframe (Miro-or-equivalent): semantic tag per region + rule-linked QA
  checklist. Import the SVG into Miro or ship as-is.

## Guardrails
- Never assert an unverified visual-semantics claim as a requirement : those rules
  carry `evidence_basis ∈ {Interpretation, Hypothesis, Engineering interpretation}`
  and must be reported as such (see `references/master-claims.md`: only 8/37 of the
  source-4 claims were verified).
- Every number is measured (script) or quoted (verbatim) : never invented.
- See `BUILD_STATUS.md` for what is complete vs. the remaining normalization TODOs.
