---
name: seo-parallel-audit
description: >
  Run MULTIPLE SEO audits in PARALLEL on any target (a page or a whole site),
  for any client, in any session. Auto-selects the right audit bundle by page type, or
  takes an explicit list. Fans out one worker per audit concurrently, dedupes findings
  across audits, and emits ONE branded HTML+XLSX. Use when the user says: "run
  all audits", "parallel audit", "run multiple audits", "full audit on <url>", "audit
  everything for <client>", "run render + a11y + cro on X", or invokes /seo-parallel-audit.
---

# SEO Parallel Audit Orchestrator

One trigger that runs several `seo-*` audits at once and returns a single merged, branded
deliverable. This is a **personal skill** : it loads in every session and works for any
client. It orchestrates; the real work is done by the individual audit skills, run as
**parallel workers**.

---

## Invocation

```
/seo-parallel-audit <target> [audits] [--out DIR]
```

- **target** : a URL (page), several URLs, or a client + site root ("AMR homepage",
  `https://amrgaragedoors.com/`, or a `sitemap.xml`).
- **audits** (optional) : explicit comma list (`render,a11y,cro`). **If omitted → auto-select
  by page type** (Phase 1). Aliases: `render`=seo-render-audit · `a11y`=seo-accessibility-completeness-audit ·
  `foundational`=seo-after-foundational-setup-audit · `cro`=seo-cro-conversion-audit ·
  `offpage`=seo-off-page-audit · `topical`=seo-topical-map · `gsc`=seo-gsc-diagnosis ·
  `initial`=seo-initial-analysis · `affiliate`=seo-affiliate-and-review-audit ·
  `ecom`=seo-ecom-decline-investigation · `sandbox`=seo-sandbox-effect-analysis · `links`=internal-links.

If the target is only a client name with no URL, ask for the URL(s) / GSC property before proceeding.

---

## Phase 1 : Classify the target & choose the bundle (auto mode)

Determine what the target is (URL pattern + a quick fetch/render of the page), then map to a bundle.
Always honor an explicit `audits` list over auto-selection.

| Target type | Signals | Default parallel bundle |
|---|---|---|
| **Homepage** | root `/`, brand H1, mixed intents | render · a11y · foundational · cro |
| **Money / service page** | `/service`, `/repair`, single-intent, CTA-heavy | render · foundational · cro · a11y |
| **Location page** | `/city`, `/areas-served`, near-duplicate template | foundational · cro · a11y (flag duplication) |
| **Blog / content** | `/blog`, article schema, informational | foundational · a11y · topical (fit only) |
| **Ecom PDP / category** | price, add-to-cart, product schema | cro · render · a11y (+ ecom if a decline is described) |
| **Affiliate / review** | comparison tables, outbound affiliate links | affiliate · cro · a11y |
| **Whole site / many URLs / sitemap** | multiple targets, "audit the site" | topical · offpage · gsc · initial (site-level, not per-page) |

State the detected type and the chosen bundle before firing, so the user can correct it.

---

## Phase 2 : Connector preflight (do this before fanning out)

Some audits need live connectors. Check availability in THIS session:

- **DataForSEO** → offpage, topical, gsc, initial, ecom, sandbox
- **Google Search Console** → gsc, initial, foundational (indexing checks)
- **Microsoft Clarity** → cro (behavioral), ecom
- **Browser / Playwright** (in-app, Chrome DevTools, or agent browse) → render, a11y (DOM/accessibility tree)

If a selected audit's connector is not authenticated, tell the user, then either **skip** that
audit or run its connector-free portion. Never fabricate data an unauthenticated connector
would have supplied. (render / a11y / cro-heuristic run anywhere with a browser / Playwright tool.)

---

## Phase 3 : Fan out (the actual parallelism)

Launch **one worker per selected audit** so they can run concurrently when the host
supports parallel agents (Cursor Task/workers, Claude workers, Codex workers, etc.).
If the host cannot parallelize, run audits **sequentially** with the same contract, then merge.
Give each worker the SAME structured-output contract so results merge without parsing.
Prompt template per worker:

> Run the SEO **`seo-<audit>`** audit against **`<target>`**. Load and follow
> that audit’s `SKILL.md` in this pack (sibling under `skills/`) exactly (use its scripts + the session's MCP data
> tools; render DOM via the browser / Playwright tool where the skill calls for it). Do NOT write any client
> files or reports : instead RETURN your findings as JSON matching this schema:
> `{ "audit": "<audit>", "page_scope": "<url-or-template>", "summary": "<=40 words",
> "findings": [ { "id": "", "area": "", "severity": "High|Medium|Low|Info",
> "confidence": "Confirmed|Strong|Moderate", "evidence": "", "consequence": "", "fix": "" } ],
> "metrics": { } }`. Keep evidence concrete (selectors, numbers, URLs). If a required connector
> is unavailable, return `findings: []` and set `summary` to the limitation.

Notes:
- Worker final reports are NOT shown to the user : YOU collect the JSON and merge it. Relay a
  one-line status per audit as they land.
- Respect the host’s concurrency limits; queue extras if needed : still schedule them all.
- For **many pages × many audits** (site-wide at scale), don't hand-fan hundreds of agents : say so
  and offer the saved **Workflow** path (pipeline over pages with auto-dedupe) instead.

---

## Phase 4 : Merge & dedupe (you do this, in-context)

1. Pool all findings from every worker.
2. **Dedupe** by `(page_scope + normalized issue)`. Exact same defect from two audits → keep one,
   list both audits in `source_audit`.
3. **Cross-lens link, don't delete**: when two audits describe the same element from different
   angles (e.g. SEO "images missing alt" ↔ a11y "unnamed control", or CRO "iframe form renders
   blank" ↔ a11y "iframe title wrong"), keep BOTH and tag them `↔` as related : they're
   complementary, not duplicates.
4. Rank: High → Medium → Low → Info; Confirmed above lower-confidence within a tier.
5. Produce a master findings table + per-audit sections.

---

## Phase 5 : One branded deliverable

Emit a single output using **built-in report branding** (colors, text mark, Inter/Arial,
section order). Default: **HTML + XLSX** to the target's project folder (or `--out DIR`):

- **HTML**: cover + KPI cards (total findings, High count, audits run, page scope) → a **Master
  Findings** table (all audits, deduped, filterable) → one section per audit → cross-lens links called out.
- **XLSX**: `Overview` tab + one tab per audit + a `Master Findings` tab. Brand tab colors.
- Reuse the enhancement layer pattern (sticky nav, severity filter, dark/light, print) if the
  client wants an interactive report.

Report which audits ran, which were skipped (and why : usually a missing connector), and the
deduped finding count.

---

## Guarantees & caveats

- **Portable**: personal skill → available in every session, every client. Inputs (URLs, GSC
  property) are per-client and passed in or asked for.
- **Honest coverage**: an audit skipped for a missing connector is reported as skipped, never
  silently dropped or faked.
- **No client writes from workers**: only the orchestrator writes the final merged files, so
  parallel agents never collide on disk.
