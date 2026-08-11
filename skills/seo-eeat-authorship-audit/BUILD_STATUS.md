# Build status

**Status: complete.** Built 2026-08-02.

- `data/rules.csv` : 42/42 rules, mechanically derived from the Checklist HTML +
  CSV (script: see git-free scratch build; counts asserted to match per section,
  one hand-mapped exception documented inline : the Helpful-content section,
  where the CSV folds 6 HTML checks into 4 broader rows).
- `data/sources.csv` : 8 sources, matches every `source_id` used in rules.csv.
- `data/finding_fields.csv` : 15-field finding schema.
- `scripts/measure.py` : self-tested against a synthetic fixture; caught and
  fixed one real bug pre-ship (Person schema nested in `article.author` wasn't
  being counted in `person_schema.present/count`, even though `sameAs_count`
  found it via a separate path : fixed by folding the author node into the
  persons list before counting).
- `scripts/build_report.py` + `shared/report_kit.py` : end-to-end self-test with 6 sample
  findings across 5 pillars produced valid, tag-balanced HTML with jump-nav,
  accordions, per-pillar SVG charts, and all four Issue/Evidence/Solution/
  Execution fields present.
- `SKILL.md`, `references/knowledge-base.md`, `templates/output_schema.md` : 
  written.
- Shipped to both `~/.claude/skills/` and the `seo-skills` plugin's
  `custom-skills/skills/`.

No remaining TODOs.
