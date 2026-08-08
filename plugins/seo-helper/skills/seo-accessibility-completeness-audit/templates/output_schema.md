# Audit Output Schema

## A. Audit summary

| Field | Required content |
|---|---|
| Audit mode | Audit, Convert, or Audit and Repair |
| Input inspected | URL/files/representations supplied |
| Selected page type | Primary or hybrid template |
| Dominant activity | Learn, compare, calculate, buy, find, troubleshoot, contact, or contribute |
| Primary task | One testable task statement |
| Scope limits | Missing representations, data, or access |
| Audit date | ISO date |

## B. Verdict summary

Report counts for `Pass`, `Partial`, `Fail`, `Not Applicable`, and `Not Testable`. Group actionable findings by severity. Do not reduce the audit to a single score by default.

## C. Rule-level findings

Return one row per applicable or evaluated rule:

| Field | Requirement |
|---|---|
| Finding ID | Stable audit-instance identifier |
| Rule ID | ID from `AUDIT_RULES.csv` |
| Scope | Global, page type, component, or representation |
| Element/region | Exact affected element or region |
| Applicability | Why the rule applies |
| Verdict | Pass, Partial, Fail, Not Applicable, or Not Testable |
| Severity | Critical, High, Medium, Low, or Informational |
| Observed evidence | Verifiable page observation; selector/location where possible |
| Expected condition | Rule's pass condition |
| User consequence | Effect on comprehension, access, trust, or task completion |
| Machine consequence | Effect on structure, extraction, association, or state recovery |
| Evidence basis | Observed, official guidance, standard, research, interpretation, or hypothesis |
| Recommended solution | Smallest sufficient correction |
| Implementation example | Corrected HTML/content/pseudocode when useful |
| Validation method | Exact retest |
| Search-impact confidence | Confirmed input improvement, plausible hypothesis, or requires controlled test |
| Dependencies | Template, CMS, analytics, legal, content, or engineering dependency |

## D. Prioritized repair plan

Order repairs by dependency and consequence:

1. access, fetch, render, and indexing blockers;
2. deceptive or broken primary functions;
3. main-region, task, reading-order, and accessibility failures;
4. evidence and cross-representation contradictions;
5. page-type completeness and secondary-task issues;
6. low-consequence refinements and experiments.

## E. Validation record

For each repaired finding, record previous verdict, change made, representation retested, new verdict, remaining limitation, and tester/date.

## F. Required closing statement

State what the audit establishes from observable evidence and what remains an SEO hypothesis. Never present a corrected input as proof of a ranking outcome.
