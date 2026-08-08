# Input Manifest

What the initial analysis can ingest, what each input unlocks, and how to handle
**limited or custom** inputs. **Nothing here is required.** The analysis degrades
gracefully — a missing input drops or lightens its report(s); it never blocks the
run. At intake, tell the user exactly what's present, what that builds, and what is
skipped and why.

## The golden rule: no input is mandatory
The only thing the skill truly needs is a way to name the central **entity** — and
even that can be inferred from a domain or a one-line description. From there it
scales to whatever exists:

| You have… | You can still produce |
|---|---|
| Just an **entity brief** (entity + intent + ICP + dimensions) | Report 3 (EAV), keyword engine, topical map, starter go-to plan |
| Just a **domain** | + Business Understanding & Verification from the live site |
| Just a **questionnaire** (the Plate Photo case) | + richer Business Understanding, EAV seeds |
| A **full folder** (the Five Star case) | the complete suite |

Never wait for "complete" inputs. Run with what exists; label the gaps.

## Optional inputs — each deepens a specific report
| Input | Typical file | Feeds | If missing |
|---|---|---|---|
| Initial questionnaire (client Q&A) | `Initial Questionaires…csv` | Report 1, EAV seeds, differentiators, do-not-call | Build Report 1 from live site + entity only |
| Business overview | `Business Overview.csv` | Report 1, funnel | Infer from site / questionnaire |
| Competitors list | `Competitors.csv` | Report 6 teardown | Discover via live SERP, or skip Report 6 |
| Sitemap | `sitemap.xml` | Report 2, coverage, de-cannibalization | Live-crawl key URLs from the domain, or skip Report 2 |
| Live page / post list | `All Pages & Post…csv` | Report 2 verification | Use sitemap or a live crawl |
| Page plan | `Page Planned…csv` | Report 8, seo-topical-map reconciliation | Derive the plan from the topical map |
| Task logs | `All Task Logs.csv` | Report 2 (what was done), pace | Skip pace; note no work-history |
| Action items | `Top View of Action Items.csv` | Report 8 tracker | Generate items from the findings |
| Strategist / client concerns | `After Analysis Questions.csv` | Report 7 playbook | Skip Report 7 (nothing to answer) |
| Client pre-work dir | brand guide, CLV, deck, screenshots | Report 1, differentiators, proof | Skip; note a thinner proof layer |

## Custom / unexpected inputs — never rejected
Anything else the client hands over is in-scope. Read it, say what it is, and fold
it into the closest report (or an appendix). Examples seen in real runs:
- A **screenshot** of an Airbnb / GBP profile → verified review counts into Report 2
  (reconcile against the site's stated numbers; flag any overstatement).
- A **podcast / video / press URL** → an E-E-A-T / authorship signal into Report 1.
- A **prior audit** from another agency → reconciled in Report 2, gaps into Report 8.
- A **bespoke CSV / XLSX** of any shape → parse it, map the columns you recognize,
  list the rest, and place it where it fits.
List every custom input in `config.inputs.custom` with a one-line note on where it
landed, so the run is auditable.

## Intake checklist
1. Load `config.json`; resolve every `inputs.*` path relative to the client folder.
2. For each input: exists? → ✓ + what it unlocks; missing → which report(s) drop/lighten.
3. If a `domain` is set, fetch the live homepage + sitemap now (Report 1/2 grounding).
4. Confirm the `entity` block is filled (at least `central_entity`) — it's the spine
   of Report 3 and the seeds for the keyword engine.
5. Report the plan to the user: "These N reports will build; these M are skipped for
   missing inputs — here's what would unlock each." Then proceed.

## File-format notes
- **CSV / XLSX** — read with Desktop Commander (`read_file` parses XLSX → JSON rows)
  under `~/Downloads`, where Bash `cat`/`head` is TCC-blocked.
- **Sitemaps** — the `<loc>` list is the live URL inventory; split page vs post maps.
- **Screenshots / PDF** — read visually; extract the specific claim (count, name,
  date), not the whole document.
- **Odd headers / encodings** — read the first 2 rows, map columns, then process.
  Never assume a schema; confirm it against the actual file.
