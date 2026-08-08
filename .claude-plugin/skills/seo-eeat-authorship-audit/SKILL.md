---
name: seo-eeat-authorship-audit
description: >-
  Audit a live page (or a page spec) for E-E-A-T and Authorship gaps and produce a
  branded SEO deliverable: every one of the 42 checks in the E-E-A-T/Authorship Checklist evaluated against the real page, each with a
  pass/fail/partial verdict, Issue · Evidence · Solution · Execution, a severity,
  and an evidence_basis (Standard = Google-sourced, Interpretation =
  practitioner-sourced, never conflated). Use whenever the user asks to "audit
  E-E-A-T", "authorship audit", "check this page's E-E-A-T", "find E-E-A-T gaps",
  "is this author credible enough", or a per-page trust/authorship/expertise
  review. Config-driven, industry-agnostic. Companion to (not a replacement for)
  the Checklist/Dos-and-Donts/CSV in `EEAT and Authorship/` and the
  research companion at `Authorship-Algorithm-EEAT-Research-Companion.html`.
---

# E-E-A-T & Authorship Audit

Turns the **E-E-A-T, Authorship & Helpful Content Checklist** (42 items,
client-tested) into a machine-checkable rule set, runs it against a real page, and
produces an Issue · Evidence · Solution · Execution findings report.

## Relationship to the other E-E-A-T assets
- `EEAT and Authorship/EEAT-Authorship-HelpfulContent-Checklist.html` +
  the companion CSV : the human-facing execution checklist. This skill's
  `data/rules.csv` is **derived directly from that checklist** (`checklist_ref`
  column carries the exact `c#i#` id) : never re-invented, never drifts from it.
- `EEAT and Authorship/EEAT-Authorship-HelpfulContent-Dos-and-Donts.html`
  : the same content as a Do/Don't playbook. Point clients here for the prose
  explanation of a finding; use this skill for the per-page pass/fail evidence.
- `EEAT and Authorship/Authorship-Algorithm-EEAT-Research-Companion.html` : 
  primary-source grounding (Google's own guidance, the real authorship-patent
  history, Koray Tugberk Gubur's framework evaluated with its evidence gaps
  named). Read this before asserting anything about *why* a rule exists.

## Core principle : sources are COMPILED, not CONSULTED
Every rule in `data/rules.csv` was distilled once from the checklist + the research
companion. At audit time, evaluate the frozen rules against the page : never
re-fetch a source article or re-derive a rule's rationale from scratch. Any
structural measurement (schema presence, byline text, HTTPS, dates, link
resolution) comes from `scripts/measure.py`, not eyeballing.

## How to run
1. **Measure what's deterministic first**: `python scripts/measure.py <url|file>
   metrics.json`. This covers 11 of the 42 rules directly (`check_type=
   deterministic` in `data/rules.csv`) : schema presence, byline text + a crude
   suspicious-string flag, `sameAs` count, HTTPS, dates, policy-page links,
   whether the author link resolves.
2. **Judge the rest**: for every rule with `check_type=llm-judgment`, read the
   actual page (and, where the rule's `scope=site`, the author's off-site
   footprint) and assess it against that rule's `pass_condition`/
   `fail_condition`. Never guess : if you can't verify something (e.g. off-site
   mentions with no search access), record `verdict=not-applicable` with a note,
   don't invent a pass or fail.
3. **Grade evidence honestly**: carry each rule's `evidence_basis` straight into
   the finding. Rules sourced `SRC-GUBUR` or `SRC-PRACTITIONER` are
   `Interpretation` : report them as "we recommend," never as "Google requires."
   See `references/knowledge-base.md` for why (the "500%" claim and the
   unsourced "statistical signature" mechanism in the research companion are the
   concrete cautionary example).
4. **Write `findings.json`** per `data/finding_fields.csv` : one entry per rule
   evaluated, every entry carrying Issue (`element`+`expected`) · Evidence
   (`observed`) · Solution (`solution`) · Execution (a **concrete draft**, not
   restated advice : an actual byline sentence, an actual Person-schema
   snippet, an actual reviewer-credential line).
5. **Render**: `python scripts/build_report.py findings.json metrics.json
   out.html` : an A to F report (jump-nav, accordions, per-pillar SVG verdict
   charts, prioritized repair plan, validation record) via `report_kit.py`.

## Data
- `data/rules.csv` : 42 rules, one per checklist item.
  `rule_id,pillar,checklist_ref,requirement,pass_condition,fail_condition,
  solution_pattern,default_severity,check_type,evidence_basis,source_id`.
  `pillar` ∈ {trust, authorship, experience, expertise, authoritativeness,
  helpful-content, schema} : matches the Checklist's own section structure, not
  the raw 4-letter E-E-A-T split (7 operational buckets are more actionable
  than 4 abstract pillars).
- `data/sources.csv` : provenance registry (`source_id → title, url,
  source_type, notes`). `SRC-GUBUR` is flagged evidence-thin by name; the two
  patent sources (`SRC-PATENT-*`) are flagged historical/not-confirmed-active.
- `data/finding_fields.csv` : the finding schema `build_report.py` expects.

## Scripts (deterministic where possible : no LLM, no live source re-fetches)
- `scripts/measure.py <url|file> [out.json] [--no-link-check]` : stdlib-only
  (json/re/urllib/html.parser). Parses JSON-LD for Article/Person/Review/
  AggregateRating, extracts the byline, checks policy-page links, HTTPS, dates,
  and optionally HEAD-checks the author link. Self-tested against a synthetic
  fixture before shipping.
- `scripts/build_report.py findings.json [metrics.json] [out.html]` : renders
  the A to F report, grouped by pillar, via `report_kit.py` (shared renderer,
  reused from `seo-accessibility-completeness-audit` rather than
  re-implemented).
- `scripts/report_kit.py` : shared HTML/XLSX renderer (jump-nav, `<details>`
  accordions : no custom JS, matches the workspace lesson that native
  `<details>` survives theme-JS interference better than scripted accordions : 
  inline SVG bar charts).

## Guardrails
- Never report an `Interpretation`-graded finding as a Google requirement : the
  research companion documents exactly why this matters (Gubur's "statistical
  signature" claim resolves to phrase-spotting, not a measurable feature set,
  when actually checked).
- Every number in a finding is either measured (`measure.py`) or quoted
  verbatim from the page : never invented.
- `checklist_ref` must always be populated : it's what lets a client trace a
  finding back to the row they can already tick off in the human checklist.
- If a rule's `check_type=llm-judgment` and the evidence genuinely isn't
  gatherable (e.g. off-site mention data with no search tool available),
  report `not-applicable` with the reason. Don't fabricate a verdict.
