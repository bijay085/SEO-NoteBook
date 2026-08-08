# Methodology — diagnosing the Sandbox Effect

## What "the Sandbox Effect" means here

A site that has had real SEO work done is **indexed but not graduating**: impressions accumulate,
yet rankings, clicks, and leads don't follow. The owner's question is always the same —
*"we did the work, months in, why is nothing moving?"* This skill answers it with measured
evidence and a graduation plan, for any niche.

The word "sandbox" is the client-facing frame for a family of suppression patterns. The analytic
job is to **classify which one(s) apply**, because the recovery differs. Do not assume "sandbox =
just wait." It almost never is.

## The five suppression modes (classify the mix, cite the evidence)

`sandbox_metrics.py` emits candidate flags; **you** make the final call from the evidence. A site
usually has 2–3 of these at once.

| Mode | Signature (what the data shows) | Primary recovery lever |
|---|---|---|
| **1. Trust-hold / true sandbox** | Impressions rising, clicks flat, non-brand avg pos >12, high brand-click share; **no prior peak** to fall from | Entity establishment + E-E-A-T + earned links (time-gated, but accelerable) |
| **2. Core-update / algorithmic demotion** | A **prior peak then a step-down** aligned to a known update date (needs a baseline) | Quality + E-E-A-T + authority; recovery often gated to the next update. **Run `seo-ecom-decline-investigation` for the changepoint + Simpson's-paradox position decomposition — don't re-derive it here.** |
| **3. Zero-click SERP interception** | Non-brand terms rank page-1 but CTR is ~0% on big impressions (AI Overviews / PAA / featured snippet answer on the SERP) | SERP-feature capture (40–55-word answer blocks, FAQ schema) + pivot effort to click-earning intents. **NOT "rank higher" — you already rank.** |
| **4. Wrong-intent content** | A large informational bank earns impressions but never converts; the **commercial/money** terms sit page 3–5 | Build/strengthen commercial (collection/service/location) pages; wire blog→collection→product funnels |
| **5. Entity/authority + link deficit** | "Dead-brand" entity (no KG anchor, thin/stuffed Organization schema), over-optimized/spammy backlink profile, large authority gap vs competitors | Entity cleanup + brand signals + anchor detox/disavow + competitive authority building |

Distinguishing **1 vs 2** is the load-bearing decision and it hinges on **whether a baseline
peak exists**. Set `config.period.baseline_*` only when there's a real "before"; if there isn't,
it's a never-graduated site (mode 1), not a demotion (mode 2).

## The GSC sandbox signals (exact recipes — `sandbox_metrics.py` computes all of these)

1. **Brand vs non-brand split** — *the* sandbox tell. Classify query-dim rows with
   `config.gsc.brand_regex` (brand name + common misspellings). Report brand-click-share,
   non-brand click count, non-brand impression-weighted position, non-brand CTR. A site clicking
   almost only on its own name (>75% brand share) is in **brand-only jail** — it earns clicks only
   from people who already know it; non-brand discovery is the gap.
2. **Suppression signature** — compare the first third vs last third of the (whole-month) window:
   *impressions up >20% while clicks up <10% and non-brand pos >12* = visibility accumulating
   without converting = the never-graduated pattern.
3. **Non-brand position bands** — share of non-brand impressions in pos 1–3 / 4–10 / 11–20 / 21+.
   A profile piled at 21+ is unranked; a profile at page-1 with no clicks is mode 3.
4. **Zero-click candidates** — non-brand queries at pos ≤10 with impressions ≥500 and CTR <1%.
5. **Graduation Score** (0–100) — a documented composite, below.

**Data-integrity rules (do not skip):** date-dim totals only for the trend; query-dim undercounts;
exclude partial months from every chart/table; GSC lags ~2–3 days.

## The Graduation Score (0–100) — a heuristic, stated as one

Composite of four clamped 0–1 components (weights in parentheses):
- **non-brand click share** vs a 50% target (0.30)
- **non-brand avg position** mapped 30→0 … 8→1 (0.30)
- **page-1 non-brand impression share** vs 40% (0.25)
- **CTR-at-rank health** = median CTR of non-brand pos-4–10 queries vs 3% (0.15)

Bands: **≥70** graduated/graduating · **45–69** emerging · **25–44** suppressed (classic
sandbox/brand-only) · **<25** deep suppression. It is a communication aid and a re-run baseline,
**not** a Google metric — always show the components and the underlying facts beside it.

## Traps this method exists to prevent (from the three source engagements)

- **Trusting the spreadsheet, not the live site.** Planned URLs 301'd to junk, "live" pages sitting
  `noindex` and absent from the sitemap — invisible no matter the work. **Verify every URL with
  `live_verify.sh` before any claim.** (Bowalker: 18 noindex pages + hub slugs 301'ing to wrong products.)
- **Reading "impressions doubled" as progress.** Impressions are visibility, not ranking. If clicks
  and non-brand position are flat, more impressions is the *symptom*, not the win.
- **Calling a demotion a sandbox (or vice-versa).** No baseline peak → not a demotion. A step-down on
  an update date → not a sandbox. (TDD: an actual March-2026 core-update demotion masquerading as
  "my blogs don't rank" — the recovery lever was E-E-A-T, but the *diagnosis* was a decline.)
- **"Rank higher" for a zero-click term.** If it already ranks page-1 at ~0% CTR, ranking is solved;
  the click is being eaten on the SERP. Different fix entirely.
- **Fabricated trust signals compound suppression.** Hardcoded sitewide `aggregateRating 5.0`, stuffed
  `alternateName`, "top-10 best (us #1)" link posts — spam-policy risk that actively holds a site
  down. `entity_trust_audit.py` flags the first; stop the last on sight. (UIB + Bowalker.)
- **Blaming topic choice.** Don't tell a client to drop informational content — it builds the topical
  authority that ranks money pages. Diagnose *execution* (intent mapping, E-E-A-T, funnel, geography),
  not the topics.
- **Over-promising.** Trust/entity/link recovery is measured in months and (for mode 2) may be
  update-gated. State realistic timelines; separate non-gated wins (technical, commercial pages,
  local, SERP-feature capture) from gated ones (broad ranking recovery).

## YMYL amplifier

Health / ingestible / money / safety niches (kratom, supplements, pet-consumables, finance, medical)
are held in suppression **longer and harder**. For a YMYL site, E-E-A-T is not one lever among many —
it is usually **the** unlock: credentialed/reviewed authorship, cited authoritative sources,
real organizational trust (verifiable NAP, licenses, compliance seals), and a clean link profile.
Weight the recovery accordingly and set expectations honestly.

## The mindset

First-party facts first; verify before you claim; reach for external tools only when GSC genuinely
can't answer; and if verification walks back an earlier finding, say so plainly — an honest
correction builds more trust than a tidy report that hides it.
