---
name: seo-sandbox-effect-analysis
description: >-
  Diagnose why a site that has ALREADY had SEO work done is indexed but NOT graduating : impressions
  accumulate while rankings, clicks, and leads stay flat : then produce a branded SEO deliverable (INTERNAL HTML + 3-format CLIENT report + master XLSX) with a measured graduation plan.
  Use whenever someone asks about the "sandbox effect", "why isn't my new/revamped site ranking",
  "we get impressions but no clicks / no leads", "traffic is flat after months of SEO", "stuck on
  page 2/3", "brand-only traffic / we only rank for our own name", "is Google holding my site back",
  "site isn't growing / not graduating", "trust/authority deficit", a "6-month SEO review that shows
  no movement", or drops a folder of an engagement's inputs + prior outputs and asks why it isn't
  working. Classifies the suppression into 5 modes (trust-hold/true-sandbox, core-update demotion,
  zero-click SERP interception, wrong-intent content, entity/link deficit) because the recovery
  differs, and computes a 0-100 Graduation Score from real Google Search Console data. Config-driven
  and niche-agnostic (local-service, ecom, YMYL). EVERY input is optional and extensible : the skill
  actively pulls from GSC / DataForSEO / Clarity and requests what's missing rather than assuming.
  CLAUDE-NATIVE: Claude does all reasoning and authoring itself : no Gemini/OpenAI/Anthropic API
  calls (Claude Max); the only external calls are real data-fetch tools verified present here.
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# Sandbox-Effect Analysis

Answers one question with evidence: **"We did the SEO work : why is the site still not
graduating (rankings / clicks / leads), and how do we fix it?"** : for any site whose foundation
is built but whose organic performance is stuck.

Built from three real client engagements : a local window installer (brand-only jail), a
pet-treats store (core-update demotion masquerading as a sandbox), and a YMYL kratom store
(dead-brand entity trap + spam-link suppression) : so the method generalizes across niches.

## Sibling skills : route correctly first

| Skill | Answers | Use instead when |
|---|---|---|
| `seo-gsc-diagnosis` | "Why isn't THIS page ranking/getting clicks" : single snapshot | The question is one page, right now |
| `seo-ecom-decline-investigation` | "What DROPPED, when, why" : before/after decline stats | There's a clear peak-then-fall to explain (a demotion) |
| `seo-after-foundational-setup-audit` | Per-page forensic technical audit | You need page-by-page defects, not a trend diagnosis |
| **`seo-sandbox-effect-analysis`** (this) | "Indexed but not graduating : why, and the graduation path" | Impressions up but rank/clicks/leads flat after months of work |

This skill overlaps `seo-ecom-decline-investigation` on purpose: mode 2 (core-update demotion) hands
the changepoint statistics to that sibling rather than re-deriving them. Everything else : the
trust-hold, zero-click, wrong-intent, and entity/link modes : lives here.

## Inputs : all optional, all extensible

Copy `config.template.json` → `config.json`. Nothing is mandatory except a way to see the site's
own search data (GSC access, live or exported). Fill what the engagement has; leave the rest : a
missing input drops its section and is flagged, it never blocks the run. `custom_inputs` is a
free-form bag for anything client-specific (an EAV/entity sheet, a CallRail leads export, a KG doc,
a schema file, a homepage-rebuild handoff) : reference it in the relevant phase.

| Category | Standard input | If missing |
|---|---|---|
| GSC access | property + account; live MCP or CSV/XLSX exports | Pull live via `mcp__google-search-console__*` (the .env GSC refresh token is EMPTY : MCP only) |
| Brand terms | `gsc.brand_regex` (name + misspellings) | Ask the user, or infer from the domain/brand and CONFIRM before splitting |
| Period + baseline | engagement window; optional baseline peak | Ask for the window. No baseline → treat as never-graduated (mode 1), not a demotion |
| Page inventory / sitemap | live URL list or sitemap | Pull the sitemap; derive top pages from GSC page-dim |
| Work log / plan | what the agency shipped | Report degrades to "delivered work not itemized"; still diagnose |
| Backlinks | Ahrefs/Semrush CSV | Pull via DataForSEO backlinks MCP (Ahrefs/Semrush direct keys are EMPTY) |
| Live site | URL (preferred) or saved HTML | `mode:none` skips live verification; anti-bot → ScrapingBee fetch |
| Competitors | domains for authority-gap math | Ask, or derive from live SERP for the money terms |
| `custom_inputs` | anything client-specific | Extend the config; don't rename a standard field |

### Filling gaps live : the "request/invoke as enhancement" behavior

Actively reduce data gaps with real tools instead of just reporting them (all verified present : 
see `references/data-sources-and-tools.md`): pull any missing GSC dimension live; corroborate a
suspected changepoint with `WebSearch` (update calendar) + `mcp__dataforseo__dataforseo_labs_google_historical_rank_overview`;
check a live SERP with `mcp__dataforseo__serp_organic_live_advanced` or the ValueSERP key; pull
backlinks via the DataForSEO backlinks MCP; get CWV via `on_page_lighthouse` / the PageSpeed key;
corroborate a UX/conversion cause with the Clarity MCP. **Never invent a tool** : if it isn't
connected, say so and ask.

## The workflow

```
0. INTAKE -> load config; report present vs missing; ask ONE structured question for the minimum gap
1. GSC PULL -> date-dim daily series + query-dim + page-dim (per config.period); save CSVs
2. SIGNATURE -> run scripts/sandbox_metrics.py -> brand/non-brand split, suppression signature,
                  position bands, zero-click candidates, Graduation Score -> sandbox_data.json
3. CLASSIFY -> you decide which of the 5 modes apply, each with its evidence (methodology.md).
                  If mode 2 (demotion) -> hand the changepoint stats to `seo-ecom-decline-investigation`
4. VERIFY LIVE -> scripts/live_verify.sh on the money/target URLs: live+indexed vs noindex / 301-to-junk
                  / missing-from-sitemap. NEVER claim from a spreadsheet : verify.
5. TRUST AUDIT -> scripts/entity_trust_audit.py (dead-brand entity trap, schema/NAP/aggregateRating)
                  + scripts/backlink_trust.py (anchors, toxic share, disavow candidates) when data exists
6. ARCHITECTURE-> intent mapping + duplication + money-page ranking gaps (DataForSEO content/SERP if on)
7. CREDIT WORK -> from the task log, credit what shipped; locate the gap between done and graduated
8. RECOVERY -> phased graduation plan (recovery-playbook.md), niche-weighted, honest expectations
9. BUILD -> INTERNAL html + 3-format CLIENT report + master XLSX (deliverable-structure.md)
10. VALIDATE -> numbers match sandbox_data.json; partial months excluded; tag balance; no stale claim
11. DELIVER -> save to output_dir; state findings vs data gaps vs corrected assumptions honestly
```

Phase notes that matter:
- **Phase 2 is pure stdlib** : no venv needed. `report_helpers.py` (XLSX, Phase 9) needs `openpyxl`
  (`scripts/setup_env.sh` if absent).
- **Phase 3 is Claude's call, not the script's.** The script flags candidates; you weigh the
  evidence and name the mode mix. A site usually has 2 to 3 modes at once.
- **Phase 4 is the anti-hallucination gate.** "The work" and "the visible work" diverge constantly
  (noindex money pages, hub slugs 301'ing to junk). Verify before you diagnose.

## Methodology & playbooks (read before authoring)

- `references/methodology.md` : the 5 modes + how to tell them apart, the exact GSC signals, the
  Graduation-Score rubric, the traps this prevents, the YMYL amplifier.
- `references/recovery-playbook.md` : the graduation levers, niche weighting, phased roadmap, the
  real monitoring KPI (non-brand clicks/position/score : not blended position, not impressions).
- `references/deliverable-structure.md` : INTERNAL + 3-format CLIENT + master XLSX skeletons.
- `references/data-sources-and-tools.md` : every real tool/key, exact call shapes, the credential
  truth, and the Forbidden list.

## Guardrails

- **Claude-native only.** All interpretation and authoring is Claude's. Do NOT call `GEMINI_API_KEY`
  or `OPENAI_API_KEY` (present for unrelated tooling) : this is Claude Max.
- **No tool that isn't real.** Every MCP/key named was verified present. GSC via MCP (refresh token
  empty); backlinks via DataForSEO+CSV (Ahrefs/Semrush keys empty). If a future env lacks one, say so.
- **Verify live before claiming.** Run `live_verify.sh`; re-verify (cache-busted) before repeating a
  prior finding : state can change ("we fixed that yesterday").
- **Never fabricate a number.** Every metric traces to a script run or an input file. Uncomputable =
  stated data gap.
- **Impressions ≠ progress; brand clicks ≠ discovery.** Lead with non-brand + position + score.
- **Classify before prescribing.** Sandbox vs demotion vs zero-click vs wrong-intent vs entity/link
  need different fixes; don't default to "just wait."
- **Sequence recovery.** Never prune/noindex before the replacement is confirmed ranking; don't bundle
  a site-wide template change into active recovery.
- **Honest expectations.** Separate non-gated wins from update-gated recovery; no over-promising.
- **Client report is AUTHORED, never a filtered internal copy** : forward-framed, no jargon, no blame.
- **Degrade gracefully.** Missing input drops its section, noted on the cover; the run continues.
- **Respect owner constraints** in `custom_inputs`/brief (no redesign, no public pricing, one CTA,
  human QA before publish, served-geography town list) : a plan that violates them won't be executed.

## Branding

SEO report branding on every output via `scripts/brand_lib.py` (HTML) and `scripts/report_helpers.py`
(XLSX), config-driven; consult the built-in report branding skill for the full spec (processed
text mark, yellow #F5C518 / black #0A0A0A, **Lexend** default). Cover/header read
**"<Client> · Sandbox-Effect Analysis"**.

## Output location

Everything to `<output_dir>/` (default `./Sandbox-Analysis/`). Keep the script outputs
(`data/sandbox_data.json`, any `*_analysis.json`, live_verify logs) alongside : the report must be
reproducible from them.

## Bundled files

| File | Purpose |
|---|---|
| `config.template.json` | Copy → `config.json`; every field optional except a way to reach GSC |
| `scripts/sandbox_metrics.py` | Phase 2 core (stdlib): brand split, suppression signature, bands, zero-click, Graduation Score |
| `scripts/live_verify.sh` | Phase 4 gate: HTTP status / redirect / canonical / robots / sitemap membership |
| `scripts/entity_trust_audit.py` | Phase 5: dead-brand entity trap : Org schema, NAP, sameAs, aggregateRating sanity |
| `scripts/backlink_trust.py` | Phase 5: anchor distribution, toxic share, domain-level disavow candidates |
| `scripts/report_helpers.py` | Phase 9: branded openpyxl XLSX primitives |
| `scripts/brand_lib.py` | Branded HTML primitives (shell/css/tbl), config-driven |
| `scripts/setup_env.sh` | Optional venv (only for openpyxl / .xlsx reads) |
| `references/methodology.md` | The diagnostic method (read before authoring) |
| `references/recovery-playbook.md` | Graduation levers, niche weighting, phased roadmap |
| `references/deliverable-structure.md` | INTERNAL + CLIENT + XLSX skeletons |
| `references/data-sources-and-tools.md` | Real tools/keys, exact shapes, credential truth, Forbidden list |

## Version

Built 2026-08-01, generalized from three client sandbox/suppression engagements (Bowalker : 
local window installer; The Doggie's Deli : pet-treats ecom; Urban Ice Botanicals : YMYL kratom
ecom). The GSC signal engine and 5-mode classification are niche-agnostic; the recovery weighting
is niche-tuned. Update whenever a new run surfaces a new suppression mode or trap.
