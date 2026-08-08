# Deliverable structure

Two audiences, authored separately (never a filtered copy of one into the other). All outputs use
SEO report branding via `brand_lib.py` (HTML) and `report_helpers.py` (XLSX); font defaults to
**Lexend**; exclude partial months from every chart/table; every claim carries its evidence.

## 1. INTERNAL report — `00-<Client>-Sandbox-Analysis-INTERNAL.html`

Blunt, complete, evidence-first. Suggested sections (drop any whose data is absent):
1. **Headline finding** — the one verified fact that reframes everything (e.g. "97% brand-only jail
   at non-brand pos 38 — indexed, not graduating").
2. **Suppression signature** — the GSC trend (whole months), brand vs non-brand split, position
   bands, Graduation Score + components. Charts from `sandbox_data.json`.
3. **Mode classification** — which of the 5 modes apply, each with its evidence; the 1-vs-2 call.
4. **Live inventory & verification** — `live_verify.sh` results: what's actually live+indexed vs
   noindex/301-to-junk/missing-from-sitemap. (This is where "the work" and "the visible work" diverge.)
5. **Entity & trust audit** — `entity_trust_audit.py` output; schema/NAP/aggregateRating findings.
6. **Off-page trust** — `backlink_trust.py`: anchor distribution, toxic share, disavow candidates.
7. **Content & intent architecture** — duplication, intent-mapping, money-page ranking gaps.
8. **What the agency already shipped** — credit done work from the task log; find the gap between
   done and graduated (avoids blame; frames the plan).
9. **Prioritized findings ledger** — every issue: Issue · Evidence · Solution · Execution · Priority.
10. **Recovery roadmap** — phased (immediate/sprint/sequenced/ongoing/watch), per recovery-playbook.

## 2. CLIENT report — `<Client>-Sandbox-Report.{html,docx,xlsx}` (3 formats)

**Authored for the client, not filtered from internal.** Reporting sense, forward-framed, no internal
jargon (no "noindex/LIVE-BUG/Report N"), no self-blame — accountability stated as workflow
commitments. Suggested flow:
1. **Where you stand** — plain-language read of the sandbox situation + the one headline number.
2. **What we've delivered** — the foundation work done (credit it honestly).
3. **What the data shows** — the graduation picture: brand vs non-brand, visibility vs clicks,
   partial months excluded; explain *why* impressions rose but leads didn't, without blame.
4. **Why the site isn't graduating yet** — the diagnosed causes in client language.
5. **The graduation plan** — phased, with what changes for them and realistic timelines
   (separate quick wins from update-gated recovery).
6. **Tools / local / trust** — niche-appropriate (configurator/calculator, GBP+location, E-E-A-T).
7. **How we'll measure it** — non-brand clicks + position + Graduation Score, re-run each period.

Build the 3 formats with the built-in report branding skill's patterns (processed logo,
black/yellow, Lexend). Keep all three at content parity.

## 3. Master workbook — `00-<Client>-Sandbox-Master.xlsx`

Built with `report_helpers.py`. Tabs: **Overview** (stat cards: Graduation Score, brand share,
non-brand pos, non-brand clicks) · **GSC Signals** (monthly trend, brand/non-brand, bands) ·
**URL Status** (live_verify results) · **Entity & Trust** · **Backlinks & Disavow** ·
**Findings Ledger** (Issue·Evidence·Solution·Execution·Priority·Owner·Done-when) ·
**Recovery Roadmap** (phased, executable steps). Never fabricate a cell — every value from a
script output or an input file.

## Validation before delivery

Tag balance in HTML (open==close for div/table/tr/ul); no placeholder text; every number in the
narrative matches `sandbox_data.json` / script output; partial months excluded everywhere; no stale
or contradicted claim survives a state change (re-verify live before repeating a prior finding).
