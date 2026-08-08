---
name: cro-conversion-audit
description: >-
  Run a competitor-benchmarked, behavior-corroborated CRO (conversion rate
  optimization) audit for ANY website. Scores the site vs named competitors
  across UI/UX, Coverage, Page, CTA and Trust; audits the lead form and builds a
  ~20-case QA test plan; corroborates every claim with real Microsoft Clarity
  behavioral data (click / scroll / attention) and live-page verification; and
  delivers a branded HTML report + XLSX workbook with evidence-bound
  recommendations. Use when the user asks for a "CRO audit", "conversion audit",
  "conversion rate optimization", "why isn't my site / page converting", "improve
  conversions / leads", "lead form audit", "CTA audit", "compare my conversion vs
  competitors", or hands over Microsoft Clarity exports / GA4 exports / competitor
  pages for conversion analysis. Inputs are flexible (custom, similar, or
  additional) and mostly optional : the skill REQUESTS missing data or pulls it
  via the DataForSEO, Google Search Console, and Microsoft Clarity MCP connectors
  when needed. Claude-native: no OpenAI / Gemini key : Claude does the reasoning
  itself. Final brand polish via built-in report branding.
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# CRO / Conversion Audit

Score how well a site converts, **against named competitors**, then **prove it
with real user behavior**. The value is not the mechanical scan : it is the
reasoning layer: extract signals, **correct the false positives**, corroborate
with Microsoft Clarity behavioral data and live-page checks, bind every claim to
evidence, and ship a branded, executable report.

This skill was generalized from a real MSP engagement (site vs two competitors +
365-day Clarity data + Elementor lead form). It works for **any** site and adapts
to whatever inputs are supplied.

## What it produces

- **`cro_report.xlsx`** : Overview, Conversion Scores, Comparison Matrix, Form
  Audit, Form Test Plan, Behavioral (Clarity), and an **Action Plan** where every
  row carries Finding · Evidence · Impact · Solution · Executable steps.
- **A branded HTML report** : narrative verdict, scores, behavioral evidence, and
  a detailed action-plan card per fix (Finding · Evidence · Impact · Solution ·
  Executable steps), styled by the built-in report branding skill.

## Inputs : flexible, mostly optional

| Input | Needed? | Source |
|---|---|---|
| Site URL | **Required** | user |
| Competitor URLs (1-3) **or** saved competitor HTML | Strongly recommended | user; else discover via DataForSEO SERP |
| Lead-form page (URL or HTML) | Recommended | user; else the site's `/contact*` page |
| Microsoft Clarity exports (Click/Scroll/Attention CSV, folder per page) | Recommended | user export; else Clarity MCP dashboard |
| GA4 exports (engagement, acquisition + device) | Optional | user |
| Lead / conversion outcomes, form-submission export | Optional | user |
| Sitemap / page-type segmentation | Optional | user |

**Custom / similar / additional inputs are welcome.** Any extra dataset (call
logs, CRM export, session recordings) becomes supporting evidence. If a
recommended input is missing, **ask for it or fetch it** (see Stage 1) : never
silently proceed as if absent data were zero.

## Tools & credentials : call ONLY what exists (no hallucination)

Running inside the Claude interface, data comes from **MCP connectors** (each
manages its own auth) and the bundled **offline scripts** (no keys needed):

- **Page fetch** → browser/`navigate` (Playwright or agent browse) + `get_page_text` / `read_page`,
  or `WebFetch`, or `mcp__dataforseo__on_page_instant_pages` /
  `on_page_content_parsing`. Save each page as `view-source_<url>.html` whose
  first line is `<!-- crawled: <URL> -->`.
- **Behavioral** → `mcp__clarity__query-analytics-dashboard`,
  `mcp__clarity__list-session-recordings` : **or** client Clarity CSV exports
  (richer per-element click data; preferred when available).
- **Competitor discovery / market / Core Web Vitals / backlinks** →
  `mcp__dataforseo__*` (`serp_organic_live_advanced`,
  `dataforseo_labs_google_competitors_domain`, `on_page_lighthouse`,
  `backlinks_summary`).
- **Search Console context** (queries, CTR, top pages) →
  `mcp__google-search-console__*`.
- **Reasoning / synthesis** → Claude itself. No LLM API key is used.
- **Branded output** → built-in report branding skill (HTML) + `xlsx` skill.

If a connector is **not authorized**, say so and ask the user to connect it (via
their the host’s MCP / connector settings), or to supply the data as a file : 
then continue. Outside the Claude interface, the same data can instead come from
the keys in `project `.env` / host environment variables` (`DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD`,
`SCRAPINGBEE_KEY`, `PAGESPEED_API_KEY`, `AHREFS_API_KEY`, `SEMRUSH_API_KEY`,
`VALUESERP_API_KEY`); the bundled scripts themselves never call any API.

Full detail: **`references/inputs-and-tools.md`**.

## Workflow : seven stages

Set up a workspace with an `analysis/` and a `pages/` dir.

### Stage 1 : Intake & gap request
Confirm the site URL. List what you have vs. the input table above. For each
**missing but valuable** input, either fetch it (competitors via DataForSEO SERP;
lead form via the site's contact page; behavior via Clarity MCP) or **ask the
user** : one focused request, then proceed with what is available and state what
that limits.

### Stage 2 : Acquire pages
Fetch the site's key conversion pages (home, top service/landing pages, the lead
form) and each competitor page using the fetch tools above; write them to
`pages/` as `view-source_<url>.html` with the crawl marker. Or accept
client-saved HTML. (Two saved pages per domain minimum is ideal.)

### Stage 3 : Mechanical extraction (scripts)
```
python scripts/cro_signals.py pages/ analysis/ <site_url>
python scripts/form_audit.py pages/view-source_<contact>.html analysis/ <form_url>
python scripts/clarity_behavior.py "<clarity_dir>" analysis/
```
These write `cro_signals.json`, `form_audit.json`, `clarity_findings.json`,
`findings.json`. **The scores are DRAFTS.** Requires `beautifulsoup4`, `lxml`,
`openpyxl` (already present in this environment).

### Stage 4 : Correction pass (MANDATORY : the core value)
Open the raw HTML and **fix the mechanical false positives** before trusting any
number. Known traps (all handled defensively in the scripts, but re-verify):
review stats a regex can miss (`4.9/5, 54+ local reviews`), "sticky"/"badges"
that trace to dormant CSS, tag-stripped competitor HTML, generic selectors. Log
each correction as a `METHODOLOGY` note in the verdict. **Set the final /10 per
domain and dimension by inspection**, not the draft.

### Stage 5 : Behavioral corroboration & live verification
Use `clarity_findings.json` to confirm or challenge the architecture inferences
(conversion-click %, scroll collapse, top distractor). Resolve every
`ambiguous_for_review` selector by checking the **live page** (what element is
`.vs-btn` / `#customteam-next` really?). Honor the `integrity_issues` : never
report mislabeled data under the wrong page.

### Stage 6 : Verdict
Write `analysis/cro_verdict.json`:
```json
{
  "headline": "one-line conversion verdict",
  "scores": {"<domain>": {"UI/UX": 0, "Coverage": 0, "Page": 0, "CTA": 0, "Trust": 0, "Overall": 0.0}},
  "summary": [{"verdict": "GAP|STRENGTH|SCOPE|CONTEXT|METHODOLOGY", "text": "..."}],
  "recommendations": [{
    "priority": "HIGH|MEDIUM|LOW", "area": "CTA|Trust|Form|UI/UX|Page|Coverage",
    "finding": "the problem, precisely stated",
    "evidence": "measured proof : selectors, click counts, %, byte sizes",
    "impact": "what it costs in conversions",
    "solution": "the fix approach",
    "steps": ["concrete do-it-today step", "next step", "QA / verify step"]
  }]
}
```
**Every recommendation is a complete unit : Finding · Evidence · Impact ·
Solution · Executable steps.** Steps must be concrete enough to hand to a
developer without a follow-up: name the CMS/plugin, the selector or element, and
the exact setting to change (e.g. "In Elementor → Header, move the Create Ticket
button…", not "improve the CTAs"). No one-line recommendations. Every claim
carries evidence; every competitor strength/scope caveat appears; and
recommendations span **all** areas the data supports, not just one.

### Stage 7 : Report
```
python scripts/cro_report.py analysis/ <out>/cro_report.xlsx
```
Then invoke **built-in report branding** to produce the branded HTML narrative
from the verdict + evidence. Deliver both.

## Rules

- **Inspect, never guess.** Every score and claim traces to an observed signal on
  a real page or a real behavioral row.
- **Draft ≠ verdict.** Mechanical scores are starting points; Stage 4 sets finals.
- **Evidence or it doesn't ship.** No recommendation without its evidence line.
- **Complete items only.** Every action-plan entry carries Finding · Evidence ·
  Impact · Solution · Executable steps : concrete enough to execute without a
  follow-up. A one-line recommendation is not done.
- **Honesty about scope & gaps.** State what wasn't crawled, what a connector
  couldn't reach, and what that leaves unproven.
- **Data integrity first.** Surface Clarity folder/URL mismatches before using the
  data.
- **Request, don't assume.** Missing valuable input → ask or fetch; never treat
  absent data as zero.

## References & scripts

- `references/methodology.md` : the six-part discipline, scoring rubric, data
  models, and the known correction patterns.
- `references/inputs-and-tools.md` : every input spec + the grounded tool /
  credential map + connector-auth fallbacks.
- `scripts/` : `common.py`, `cro_signals.py`, `form_audit.py`,
  `clarity_behavior.py`, `cro_report.py`.
