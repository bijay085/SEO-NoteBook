# Output schema : the A to F report

Rendered by `scripts/build_report.py` via `report_kit.py`. Six blocks, matching the
Issue · Evidence · Solution · Execution pattern used across every SEO audit
skill in this workspace:

- **A · Audit summary** : client, period, one-line summary, deterministic-scan
  headline (byline/schema/HTTPS at a glance from `measure.py`).
- **B · Verdict counts** : pass/fail/partial across all 42 rules, one bar chart.
- **One section per pillar** (trust / authorship / experience / expertise /
  authoritativeness / helpful-content / schema) : a verdict chart plus a card per
  finding: `rule_id (checklist_ref) : element [Interpretation if applicable]` /
  Evidence (`observed`) / Solution / Execution. The `[Interpretation]` tag is the
  reader's signal that a finding is practitioner-sourced, not a Google requirement.
- **D · Prioritized repair plan** : every fail/partial, Critical → High → Medium →
  Avoid, each with its `checklist_ref` so a client can find the matching row in
  the human Checklist.
- **E · Validation record** : rule, check_type, evidence_basis, verdict for every
  rule evaluated : the audit trail.
- **F · Closing statement** : the no-fabrication guarantee + a severity-count
  summary.

A page not yet auditable for a given rule (no search-access for off-site mentions,
no crawl for a site-wide check) gets `verdict=not-applicable` with the reason in
`observed` : it still appears in block E so the gap is visible, never silently
dropped.
