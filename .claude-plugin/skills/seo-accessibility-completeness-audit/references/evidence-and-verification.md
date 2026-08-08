# Evidence & verification policy

Two controlled vocabularies : they answer different questions. Both are recorded
per finding.

## verification_level : evidence strength of a FINDING at audit time
`source markup` · `rendered DOM` · `computed tree` · `interaction` · `keyboard` ·
`assistive technology`.

## evidence_basis : authority of the RULE itself
Unified target vocab: `Observed` · `Official guidance` · `Standard` · `Research` ·
`Interpretation` · `Hypothesis`.

**Engine B carried its own terms** (`Engineering interpretation`, `Methodology`,
`Page frame`, `Observed`, `Official guidance`). These are preserved verbatim in
`data/rules.csv` and must be **normalized** to the unified vocab (see BUILD_STATUS
TODO). Suggested map: `Engineering interpretation → Interpretation`,
`Methodology → Research`, `Page frame → Interpretation`.

## THE HARD RULE
Any rule derived from unverified visual-semantics claims (see `master-claims.md`:
only 8/37 verified) MUST carry `evidence_basis ∈ {Interpretation, Hypothesis}` and
be reported as an interpretation : **never `Standard` or `Official guidance`.** This
is what stops the engine asserting unproven SEO as a requirement.

## Source-3 (local-SEO 482980) policy
Distilled into rules but its citations were never primary-source verified → its
rules are labeled `Interpretation` until a verification pass runs (opt-in).
