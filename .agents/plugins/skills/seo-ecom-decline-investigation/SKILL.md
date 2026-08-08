---
name: seo-ecom-decline-investigation
description: >-
  Rigorous, statistics-first investigation of an ecommerce/inventory-driven site's organic decline : 
  multi-period GSC decomposition, live technical + schema audit, backend/inventory architecture audit,
  and a validated indexation strategy for product vs. collection pages : assembled into a branded
  SEO XLSX + HTML deliverable. Use when a user says "why did our traffic/rankings drop", "organic
  decline investigation", "is this a Google update or something we broke", "should I noindex my product
  pages", "collection vs product page indexation", "did the [rollout/migration/redesign] cause this",
  "statistical SEO analysis", or drops GSC exports + asks what actually happened. Built from a real
  16-month mock-it.co investigation (Sept-2025 Google Spam Update devaluation + a June-2026 rollout
  regression). Every input is optional and can be extended with client-specific extras : the skill
  degrades gracefully and actively queries GSC/DataForSEO/WebSearch to fill gaps rather than assuming.
  CLAUDE-NATIVE: no OpenAI/Gemini/Anthropic API calls for reasoning : Claude does the analysis and
  authoring itself; the only external calls are real data-fetch tools (GSC, DataForSEO, WebSearch).
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# Ecommerce Decline Investigation

Answers one question with statistical rigor: **"Something changed : what actually happened, when,
and is it fixable?"** : for an ecommerce or inventory-driven site where organic clicks/impressions/
rankings moved and the cause is not obvious from a glance at the GSC dashboard.

## Sibling skills : read this first so you route correctly

| Skill | What it answers | Depth |
|---|---|---|
| `seo-gsc-diagnosis` | "Why isn't a page ranking / getting clicks" on a **single current snapshot** | Fact-first, HTTP/canonical verification, no multi-period stats |
| `ecom-site-analysis` | "How should the catalog be organized" : **forward** taxonomy/filter/page-plan building | Classification, not diagnosis |
| **`seo-ecom-decline-investigation`** (this skill) | "What changed, when, why, and what's the fix" across **multiple time periods**, with a live technical audit and an indexation-strategy verdict | Statistical decomposition + code-level audit |
| `seo-after-foundational-setup-audit` | Per-page forensic audit of a stable site (no decline being investigated) | Page-level, not trend-level |

Use this skill when there is a **before/after** to explain : a drop, a plateau that used to be growth,
a metric moving in a way "average position" alone can't explain. If the question is about ONE page
right now, or about ROI, route to the sibling instead.

## Why this exists : the trap it prevents

The cheap way to explain a traffic drop is to eyeball a GSC graph, notice average position "improved,"
and declare victory : or to blame a country, a competitor, or a Google update from a hunch. All three
failed in the source investigation this skill is built from:

- **Average position "improved" 23 → 9 while clicks fell 76%.** That was proven to be a pure
  measurement artifact (Simpson's paradox) : the impression-weighted decomposition showed the
  pages that *survived* actually ranked slightly worse; the metric only looked better because the
  worst-ranking pages stopped being counted.
- **"We lost a country's SERP" was the owner's live hypothesis.** A chi-square test was "significant"
  purely from sample size; the effect size (Cramér's V = 0.070) proved it negligible : the decline was
  broad and proportional across every market and device.
- **A same-window comparison mistake was made and corrected mid-investigation**: comparing a 3-week-old
  collection page's stats against a product page with 7+ months of accumulation made the product page
  look artificially strong. Fixed by re-pulling both in the identical date window.

Every phase below exists to catch one of these traps with a real statistical test, not a eyeball.

## Inputs : all optional, all extensible

Nothing here is mandatory. Fill in what the engagement has; leave the rest : the skill will query for
it live where a real tool can (see **Filling gaps live**, below) or mark it a data gap and proceed.

Copy `config.template.json`. The `custom_inputs` object is a free-form bag for **anything specific to
this client** that doesn't fit the standard shape : a CallRail export, a specific competitor tracker, a
migration changelog, a plugin/CMS quirk file. List whatever exists there; the workflow phases below
tell you where to fold it in.

| Category | Standard inputs | If missing |
|---|---|---|
| **Comparison periods** | 2+ named date ranges (e.g. "before", "after", "current") : GSC lags ~2-3 days | Ask the user to define at least a before/after split; without it, no decomposition is possible : this is the one true blocker |
| **GSC access** | Property URL, account (if multiple), export CSVs or live MCP access | Query live via `mcp__google-search-console__list_sites` / `query_search_analytics` : see references/data-sources-and-tools.md |
| **Site URLs under investigation** | The specific page(s)/collection(s) that moved | Derive from the GSC page-level export (top movers) if not given |
| **Live site access** | Ability to fetch the current rendered page (URL or saved HTML/snapshot) | Fetch live via WebFetch/Bash-curl if a URL is given; skip the technical-audit phase if neither exists |
| **Backend/source code** | Theme/app source (for the architecture audit phase) | Optional entirely : skip Phase 6 if not provided; never guess at backend behavior from the frontend alone |
| **Known events timeline** | Deploy dates, rollouts, migrations, redesigns the team already knows about | Ask for this explicitly : it is the fastest way to explain a changepoint once one is found |
| **`custom_inputs`** | Anything else specific to the engagement | N/A : extend the config, don't invent a field name that collides with the standard ones |

### Filling gaps live : the "invoke queries as enhancement" behavior

This skill should actively **use its real tools** to reduce data gaps instead of just reporting them:

- Missing a period's data → pull it live with `mcp__google-search-console__query_search_analytics`
  (dimensions: `date`, `query`, `page`, `country`, `device` as needed) rather than asking the user to export it.
- Need to confirm a changepoint date against an external cause → `WebSearch` for the Google algorithm
  update calendar around that date (see Phase 4).
- Need independent corroboration of a ranking trend → `mcp__dataforseo__dataforseo_labs_google_historical_rank_overview`
  or `dataforseo_labs_google_historical_serps` (DataForSEO's own historical tracking, independent of GSC).
- Need a live SERP position check instead of relying on a manual report → `mcp__dataforseo__serp_organic_live_advanced`.
- Need to quantify template/content duplication across pages → `mcp__dataforseo__content_analysis_search`
  / `content_analysis_summary`, or the bundled `scripts/live_page_audit.py --diff` mode.
- Need Core Web Vitals for a caching/performance hypothesis → `mcp__dataforseo__on_page_lighthouse`
  (desktop profile : label it as such) or the `PAGESPEED_API_KEY` direct call for mobile.

Never invent a tool name to fill a gap. If the environment doesn't have the tool connected, say so and
either ask the user or mark the gap explicit : see Guardrails.

## The workflow

```
0. INTAKE → load config; identify what's present vs missing; ask ONE structured question for gaps
1. PERIODIZE → define length-normalized comparison periods; never compare raw totals across
                different-length windows, and never compare a new page against an old one without
                matching the date window (see Pitfall #1)
2. PULL → first-party GSC facts per period, per dimension (date/query/page/country/device)
3. DECOMPOSE → the 6 statistical tests (Phase 3) : this is the core; run all that apply, cite exact
                numbers, never eyeball a trend
4. CORROBORATE→ cross-reference any detected changepoint against known events + external causes
                (Google update calendar via WebSearch, deploy log, DataForSEO historical rank)
5. AUDIT → live technical/schema audit of the affected page(s); backend/architecture audit if
                source is available
6. DECIDE → indexation/architecture verdict (product vs collection, noindex sequencing, etc.)
7. SYNTHESIZE → phased action plan (immediate / this sprint / sequenced / planned-refactor / ongoing)
8. BUILD → branded XLSX + HTML via built-in report branding (brand_lib / report_kit)
9. VALIDATE → tag balance, no placeholder text, numbers in the report match the script output
10. DELIVER → save to output_dir, summarize honestly, flag what's still a data gap
```

### Phase 0 : Intake

Load `config.json`. Report present vs missing in one structured message and ask for the minimum needed
(at least: the periods to compare, and GSC access). Proceed with whatever exists : a missing source
drops its section from the final report and gets flagged, it never blocks the run.

### Phase 1 : Periodize (length-normalize, always)

Define 2 or more named periods (baseline + however many "after" windows exist : the source
investigation used 3: pre-event baseline, post-event plateau, and a most-recent window that revealed
the decline hadn't stopped). For each period compute **per-day** metrics : never compare raw period
totals when period lengths differ. `days = (end - start)`; every headline metric is `total / days`.

**Pitfall to avoid (learned the hard way):** if a page/URL changed mid-investigation (a migration, a new
clean URL replacing an old one), a "same URL, different period" comparison is invalid for anything with
less than a full period of history. Pull the SAME date window for both the thing you're comparing FROM
and TO before drawing any conclusion. See `references/pitfalls.md` #1.

### Phase 2 : Pull first-party facts

For each period, pull via `mcp__google-search-console__query_search_analytics`:
- `dimensions: ["date"]` → the daily series (needed for changepoint detection in Phase 3)
- `dimensions: ["query"]` → query-level clicks/impressions/CTR/position (note: GSC UI exports cap at
  1,000 rows; the live API can page further : pull more if the query tail matters)
- `dimensions: ["page"]` → page-level equivalent
- `dimensions: ["country"]`, `dimensions: ["device"]` → for the geography/device hypothesis tests

Always pass the `account` param if `list_sites` shows multiple accounts : it errors without it.
See `references/data-sources-and-tools.md` for exact call shapes and gotchas.

### Phase 3 : Decompose (the statistical core)

Run `scripts/period_decomposition.py` against the pulled exports. It implements six tests : run
whichever apply to the question at hand, and report exact numbers (never "roughly" or "seems like"):

| # | Test | Question it answers | Kills the trap of |
|---|---|---|---|
| 1 | **Shift-share cohort decomposition** | Of the click/impression change, how much came from queries that disappeared vs. queries that survived-but-declined vs. new queries? | Assuming "keywords were lost" when survivors just declined |
| 2 | **Impression-weighted position decomposition** | Is an "average position improved" reading real, or an artifact of which pages left the average? | Simpson's paradox : the artifact that fooled the source investigation initially |
| 3 | **Chi-square + Cramér's V** (country, device, or any categorical split) | Is the decline concentrated in one segment, or broad and proportional? | Blaming geography/device from a "significant" p-value on a huge sample : always report the effect size, not just the p-value |
| 4 | **Quandt-Andrews sup-F changepoint** | Is there a single structural break date, or a gradual decline? | Guessing at "when it started" from a noisy daily chart |
| 5 | **WLS regression, log(CTR) ~ Position × Period** | Will recovering rank alone restore clicks, or is the lost volume from devalued impressions that rank-chasing can't reach? | "Just get the position back up" as a complete fix when CTR-at-rank hasn't actually degraded |
| 6 | **Counterfactual / elasticity** (OLS clicks~impressions, log-log) | How much of the click loss is explained by the impression loss alone? | Treating clicks and impressions as independent stories |

Full method notes and exact interpretation rules: `references/methodology.md`.

**Environment note:** this environment's system Python is externally-managed (PEP 668) : `pip install`
at the system level will fail. Use `scripts/setup_env.sh` to build an isolated venv with pandas, numpy,
scipy, and statsmodels before running the decomposition script.

### Phase 4 : Corroborate the changepoint

If Phase 3 test #4 finds a structural break date, corroborate it : do not report a correlation as a
cause without checking:
1. Ask/check the known-events timeline from config for a deploy, migration, or rollout on/near that date.
2. `WebSearch` for the Google algorithm/spam update calendar around that date : public update windows
   are documented (Search Engine Land, Search Engine Journal, Google's own status dashboard).
3. If DataForSEO is available, cross-check with `dataforseo_labs_google_historical_rank_overview` or
   `historical_serps` : an independent ranking data source corroborating the same date range raises
   confidence considerably.
State the confidence level plainly: a date match to a public update window is **correlational, not
proven** unless a site-side deploy log confirms nothing else changed that day.

### Phase 5 : Live technical + architecture audit

**Live page audit** (if a URL or saved HTML is available): run `scripts/live_page_audit.py` against
the page(s) most implicated by Phase 2-4. It checks, and reports severity-ranked:
- JSON-LD schema validity : flags identical/hardcoded `aggregateRating` values repeated across
  multiple entities (a real spam-policy violation pattern found in the source investigation)
- Pagination crawlability : JS-only `<button>` pagers with no `<a href>` are invisible to Googlebot
- Landmark/HTML validity : e.g. nested `<main>` elements
- Title/H1/meta alignment
- Filter/URL state : flags parametric filter URLs that would bloat the index (this is often
  **intentional** on a well-architected site; confirm with the owner before calling it a defect : 
  see `references/pitfalls.md` #5)

**Backend/architecture audit** (only if source code access is provided : never guess this from the
rendered frontend): grep/read the codebase for the patterns in `references/pitfalls.md` #6-7 : a
static/exported data file that doesn't sync back to the CMS, and copy-pasted per-category templates
that will each need the same fix applied N times. Diff two sibling templates
(`diff templateA.php templateB.php | grep -c '^[<>]'` against total line count) to get a real
duplication percentage : don't estimate it.

### Phase 6 : Indexation / inventory-architecture decision

This is the ecommerce-specific decision this skill exists to make correctly: **should individual
product pages stay indexed once collection pages exist for the same demand?**

The validated method (do not skip the same-window step : see Pitfall #1):
1. Pull collection-page and product-page performance for the **identical, most-recent settled date
   window** : never compare a new collection's lifetime stats against an old product page's lifetime
   stats.
2. If a collection page already out-earns its own flagship product pages for the same window, the
   product tail is redundant : recommend `noindex,follow` (not a hard noindex : `follow` preserves
   internal-link equity to the collections) for the low-performing tail, with a keep-list for any
   individually-earning outliers.
3. **Target the CPT/content-type, not a URL pattern.** Blog posts and the collections themselves often
   share the same URL path depth as products : a path-based noindex rule will catch the wrong pages.
4. **Sequence collections-first.** Never noindex the product tail before its replacement collection is
   confirmed indexed and holding position : that orphans the demand with nothing yet catching it.

### Phase 7 : Synthesize the action plan

Structure as phases, not a flat list : mirror what actually shipped in the source investigation:
**Immediate** (active policy-violation or crawlability risk, days) → **This sprint** (technical fixes)
→ **Sequenced** (indexation changes that depend on Phase 6 being confirmed first) → **Planned refactor**
(architecture cleanup that is real debt but not urgent : explicitly flag "do not bundle with active
recovery work," since a site-wide template change mid-recovery resets `last-modified` and can trigger
another recrawl/re-evaluation cycle) → **Ongoing monitoring** (name the actual health KPI : usually
impressions and indexed-page count, NOT average position, per the Phase 3 test #2 finding).

### Phase 8 : Build the deliverable

Reuse the built-in report branding skill for both outputs:
- `<Client>_Decline_Investigation_<Period>.xlsx` : Overview (stat cards + 3+-period headline) →
  Statistical Analysis (hypothesis verdicts + timeline + effect-size table) → Query & Page Data
  (money-query and page trajectories) → Technical & Architecture Audit → [Indexation Decision, if
  Phase 6 ran] → Action Plan. Use `scripts/report_helpers.py` for the branded openpyxl primitives
  (header band, section, table header/data rows, stat cards) : it has two real bugs from the source
  build already fixed and commented so they don't recur (merged-cell write errors, color-variable typos).
- `<Client>_Decline_Investigation_<Period>.html` : same content, single-scroll narrative, with a
  timeline visualization and simple CSS bar-chart trend comparisons (no chart library dependency needed).

Keep both at parity : a new finding goes in both formats.

### Phase 9 : Validate

Before delivering: tag balance in the HTML (div/table/tr/ul open==close counts), no leftover
placeholder text, every number quoted in the narrative matches what the decomposition script actually
printed, sheet count matches what's described.

### Phase 10 : Deliver

Save both files to `output_dir`. State plainly what was a genuine finding vs. a data gap vs. an
assumption that was corrected mid-investigation : an honest correction is worth more than a tidy
report that hides one (this happened twice in the source investigation and both corrections are
preserved as pitfalls below).

## Guardrails

- **Claude-native reasoning only.** All interpretation, hypothesis-testing judgment, and report
  authoring is done by Claude directly. Do **not** call the `GEMINI_API_KEY` or `OPENAI_API_KEY`
  entries present in `project `.env` / host environment variables` for any part of this workflow : they exist in this environment
  for unrelated tooling, not for this skill. The only external calls this skill makes are real
  data-fetch tools: GSC MCP, DataForSEO MCP, WebSearch, and direct HTTP calls to the other keys listed
  in `references/data-sources-and-tools.md`.
- **Never fabricate a statistical result.** Every p-value, effect size, changepoint date, and
  percentage in the report must come from an actual run of `scripts/period_decomposition.py` (or an
  equivalent real computation) against real pulled data : never estimated by eye, never invented to
  fill a gap. A number that can't be computed is a stated data gap.
- **A "significant" p-value is not a finding without an effect size.** Always pair chi-square with
  Cramér's V (or an equivalent) before attributing a change to a category. Large N makes almost
  anything "significant" : the effect size is what tells you if it matters.
- **An improving headline metric is not evidence of recovery** until decomposed. Check whether it's
  compositional (bad-ranking pages leaving the average) before reporting it as a win.
- **Same-window comparisons only.** Never compare two pages/periods of different ages or different
  date ranges and draw a conclusion from the raw numbers : pull the identical window for both sides
  first.
- **Correlation with an external event (a Google update) is not causation** until corroborated per
  Phase 4. State the confidence level explicitly.
- **Sequence indexation changes.** Never recommend noindexing a page whose replacement isn't confirmed
  ranking yet.
- **Degrade gracefully.** Missing source → drop its section, note it on the cover, keep going.
- **No tool that isn't real.** Every MCP tool and API key named in this skill and its references was
  verified present in this environment. If a future environment lacks one, say so and ask : never
  invent a plausible-sounding tool name to keep the workflow going.

## Branding

SEO report branding for every output : see built-in report branding for the full spec (colors,
text-only headers; XLSX/HTML patterns). Yellow #F5C518 / Black #0A0A0A / Dark #1A1A1A /
Green #2ECC71 / Red #E74C3C / Orange #E67E22; Arial (XLSX) / Inter (HTML).

## Output location

Write to `<output_dir>` from config (default `./Decline-Investigation/`). Keep the decomposition
script's raw output (`out/*.csv`, `out/headline.json`) alongside for auditability : the report should
be reproducible from them.

## Bundled files

| File | Purpose |
|---|---|
| `config.template.json` | Copy to `config.json`; every field optional except the comparison periods |
| `scripts/setup_env.sh` | Bootstraps an isolated venv (system Python is PEP-668-protected in this environment) |
| `scripts/period_decomposition.py` | The 6-test statistical engine (Phase 3) |
| `scripts/live_page_audit.py` | Schema/pagination/HTML validity checks on a live or saved page (Phase 5) |
| `scripts/report_helpers.py` | Reusable branded-openpyxl primitives for the XLSX build (Phase 8) |
| `references/methodology.md` | What each statistical test proves, exact interpretation rules, worked thresholds |
| `references/data-sources-and-tools.md` | Every real MCP/API call this skill uses, exact shapes, gotchas |
| `references/pitfalls.md` | The specific mistakes made and corrected while building this skill : read before running |

## Skill version

Built: 2026-08-01, generalized from a 16-month mock-it.co organic-decline investigation (apparel
ecommerce, WordPress). The statistical engine (Phase 3) is site-type-agnostic; the inventory/indexation
decision (Phase 6) and architecture-audit heuristics (Phase 5) are ecommerce/inventory-driven-site
specific. Update this skill whenever a new run surfaces a new pitfall or a genuinely new test is needed.
