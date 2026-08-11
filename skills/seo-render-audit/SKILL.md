---
name: seo-render-audit
description: >-
  Render audit for one or more URLs : diffs the raw HTML (what a crawler sees
  before JS) against the rendered DOM (after JS), checks robots.txt / llms.txt
  AI-bot access, then explains what Google and AI crawlers can and cannot see and
  how to fix it, exporting branded XLSX + HTML + JSON with a prioritised per-issue
  fix list. Use when a user asks for a "render audit", "JS rendering check", "what
  can crawlers / AI bots see", "is my content client-side rendered", "why can't
  Google/ChatGPT see my page", "AI bot visibility", or supplies URLs to audit for
  rendering. CLAUDE-NATIVE: Claude does the reading / analysis / solution / writing
  reasoning itself in-context (no Gemini/OpenAI key). The only external need is
  rendering the DOM, done via the browser / Playwright tool (Playwright optional).
---

# Render Audit (Claude-native)

For each URL: fetch the raw HTML, render the DOM, diff them, read robots.txt /
llms.txt bot access, extract signals : then **you (Claude) perform the reading →
analysis → solution passes yourself**, score the page, and write a branded
XLSX + HTML + JSON report with a prioritised, per-issue fix list.

**This is the Claude-native rebuild of the former `seo-render-audit` plugin.**
On a Claude Max subscription there is no reason to pay Gemini + GPT to reason in a
subprocess : you do every pass in-context. The paid transport (`router.py`,
`solution_builder.py`, `cli.py`) is gone; the deterministic engine (fetch, robots
parse, signal extraction, scoring, and the branded exporters incl. the 892-line
report template) is kept verbatim. The one thing you cannot synthesise is the
rendered DOM : so **render via the browser / Playwright tool** (Playwright is an optional local
fallback).

> Still distinct from `seo-forensics:seo-render-audit` (a mechanical, no-LLM
> raw-vs-rendered diff folded into the forensic XLSX). Use this one for the rich
> standalone report with explanations + fixes.

## Setup
```
pip install -r "${CLAUDE_PLUGIN_ROOT}/requirements.txt"
```
No API keys. No Chromium download unless you opt into the Playwright fallback.

## Inputs
- **URLs that matter** : the handful of important templates (homepage, a money
  page, a location page, a blog), not the whole site. Rendering is per-URL.
- **Workspace** `<ws>` : a folder for the per-URL artifacts and the report.

## Procedure

Set the path once:
```
RA="${SKILL_DIR:-.}"; WS="<ws>"
```

### Phase 0 : Pre-flight
Confirm the URL list and workspace. If the user just says "audit my site", ask for
the specific URLs (or pull the top templates from GSC/sitemap first).

### Phase 1 : Render the DOM (per URL, via the browser / Playwright tool)
For each URL, get the **fully-rendered DOM HTML** and save it to
`<ws>/rendered_<slug>.html`:
1. Navigate: Chrome DevTools MCP `navigate_page(url)` (preferred), or the in-app
   Browser `browser/navigate (Playwright or agent browse)({url})`.
2. Let late JS settle (wait for network idle / ~2s).
3. Grab the full DOM:
   - Chrome DevTools MCP: `evaluate_script(() => document.documentElement.outerHTML)`
   - in-app Browser: `javascript_tool` → `document.documentElement.outerHTML`
4. `Write` the returned HTML string to `<ws>/rendered_<slug>.html`.

Optional: emulate the Googlebot UA before navigating (Chrome DevTools MCP
`emulate`) to match what Googlebot receives : note it if you don't.
`<slug>` = the URL path slugified; root URL → `homepage` (matches `slug_of`).

### Phase 2 : Prep (deterministic script)
```
python "$RA/scripts/render_audit.py" prep --url "<URL>" --rendered-file "$WS/rendered_<slug>.html" --ws "$WS"
```
This raw-fetches the URL, reads robots.txt/llms.txt + per-bot access, extracts all
raw-vs-rendered signals, and writes `raw_<slug>.html`, `rendered_<slug>.html`
(echoed) and `prep_<slug>.json`. It prints a summary (char counts, body gap %,
blocked bots, signal count).

*No browser at all?* Omit `--rendered-file`; if Playwright is installed it renders
locally, otherwise it proceeds **raw-only** and flags it (the audit still runs).

### Phase 3 : Your three reasoning passes (in-context)
Read `prep_<slug>.json` (the extracted signals with raw/rendered values,
`gap_significance`, `match`, plus `bot_access`, robots, llms status) and the two
HTML files (grep for framework signatures; locate exact elements). Then write three
JSON files into `<ws>`. **Ground every judgement in what the signals and HTML
actually show : never generic advice.**

**(a) `reading_<slug>.json`** : page meta for the report header:
```json
{"js_framework_detected":"next.js|nuxt|react|vue|angular|unknown|none",
 "js_framework_evidence":"<short phrase, e.g. 'div#__next + _next/static'>",
 "js_heavy_page": true,
 "page_type_inferred":"homepage|article|product|service|landing|other"}
```

**(b) `analysis_<slug>.json`** : a JSON **array**; one object per signal that is
NOT a clean pass. Signals you omit stay `pass`. **`signal_id` must exactly match
the canonical IDs** or the scorer can't override the table:
```
title · meta_description · meta_robots · x_robots_header · canonical ·
h1 · h2 · h3 · body_text · internal_links · json_ld · og_title · images
```
```json
[{"signal_id":"h1","severity":"critical|warning|pass|info",
  "effort":"low|medium|high","impact":"high|medium|low",
  "priority_rank":1,"severity_reason":"<one sentence>"}]
```
Severity: **critical** = deindexation / invisibility / AI-bot block (JS injects
noindex, H1 only in rendered, GPTBot blocked). **warning** = degraded crawl/AI
readiness (schema or links only in rendered, content heavily JS-gated). **info** =
worth noting, no action. Rank critical+high impact first.

**(c) `solutions_<slug>.json`** : a JSON **array**; one object per critical/warning
signal, with the developer prose + formatted code already merged in:
```json
[{"signal_id":"h1","url":"<URL>","category":"Headings",
  "severity":"critical","effort":"medium","impact":"high","priority_rank":1,
  "observed_in_raw":"<what exists/absent in raw HTML>",
  "observed_in_rendered":"<what exists in rendered DOM>",
  "diagnosis":"<specific cause on THIS page>",
  "fix":"<specific action on THIS page>",
  "code_fix":"<copy-paste-ready HTML/JSON/config, or null>",
  "evidence_basis":"Observed: <what you saw>. Inferred: <what it means>.",
  "verify":"<exact command/step to confirm the fix>",
  "severity_reason":"<one sentence>",
  "prose":"<2-3 sentences on WHY it matters for Google/AI crawlers : add stakes, don't restate the fix>",
  "code_block":"<fenced code block string with a language tag, or null>"}]
```

**Hard rules (carried from the original prompts):**
- Every fix traces to something in the HTML you actually saw : reference the real
  tag / class / id / DOM path / framework signature. No advice that could apply to
  any site.
- If a JSON-LD block or an H1 exists only in the rendered DOM, output the **exact**
  block/text you saw : not a placeholder.
- **ALT TEXT RULE:** for any image missing `alt`, output the exact `src` and write
  `alt="[DESCRIBE: write your own alt text here]"`. **Never invent or infer alt
  text** from filename, URL, or context : a human must write it after seeing the
  image. Fabricated alt text is deployed as if real; do not do it.

Repeat Phases 1 to 3 for every URL.

### Phase 4 : Build the reports (deterministic script)
```
python "$RA/scripts/render_audit.py" build --ws "$WS" --out "$WS/report"
```
Globs every `prep_*.json`, applies the scorer (severity reconciliation +
google/ai/render-gap scores), and writes `audit_report.xlsx`, `audit_report.html`,
`audit_<ts>.json`. Deliver those to the user.

## Rules
- **Audit the pages that matter** : a few key templates, not the whole site.
- **Evidence-based** : severities follow the measured raw-vs-rendered gap and your
  grounded reading; report the fixes you derived, don't invent extra ones.
- **Honesty about gaps** : state the render method used; flag any URL that fell
  back to raw-only (render failed / no browser); note if you did NOT emulate the
  Googlebot UA (MCP uses the default UA), since some sites serve bots differently.

## Related skills
For a mechanical render diff inside a traffic-drop investigation, see
`seo-forensics:seo-render-audit`.

> Claude-native conversion of the `seo-render-audit` plugin. Reasoning is
> Claude's (no Gemini/OpenAI); rendering is via the browser / Playwright tool (Playwright
> optional); `scripts/render_audit.py` handles fetch + signal extraction + the
> deterministic scorer + the branded XLSX/HTML/JSON exporters (kept verbatim,
> incl. the original report template). The 4 original prompts are preserved in
> `prompts/` as the pass contracts.
