# Pitfalls — read before running

Numbered like `ecom-site-analysis`'s pitfalls list (same house convention). Every one of these is a
mistake actually made during the source investigation, caught either by a statistical test or by the
client's own correction. Update this file whenever a new run surfaces a new one.

1. **Same-window comparison, always.** Comparing a 3-week-old collection page's stats against a
   product page with 7+ months of history made the product page look artificially strong — it wasn't;
   the product page had simply had more time to accumulate. Fixed by re-pulling both in the identical,
   most-recent date window. **Before comparing any two pages/entities, confirm both have data over the
   same date range.** If one is younger, either wait, or explicitly caveat the comparison as
   apples-to-oranges.

2. **Average position is not a health metric on a site with a large long-tail.** It can improve purely
   because badly-ranking pages stopped being counted (Simpson's paradox — see
   `references/methodology.md` #2). Always run the impression-weighted decomposition before reporting
   a position trend as good or bad news. Recommend impressions + indexed-page-count as the tracked KPI
   instead, when this trap is confirmed present.

3. **A "significant" chi-square is not evidence of a targeted cause.** With GSC-scale sample sizes,
   almost any categorical difference is "significant." Always pair with Cramér's V (or equivalent
   effect size) before attributing a decline to a country, device, or segment. See
   `references/methodology.md` #3 for the threshold guide.

4. **A correlated date is not a proven cause.** A structural-break date landing inside a public Google
   update window is strong circumstantial evidence, not proof. State the confidence level explicitly;
   corroborate with a deploy log or an independent data source (DataForSEO historical rank) before
   calling it settled. See `references/methodology.md` #4 and `SKILL.md` Phase 4.

5. **JS-only filters with no URL parameters are often intentional, not a bug.** A filter architecture
   that keeps URL state out of parametric query strings can be a deliberate crawl-budget /
   index-bloat-prevention decision — confirmed as such in the source investigation. Flag it as a
   finding, but ask before recommending a fix; don't assume "no URL state" is automatically wrong. The
   real fix, if the client wants filter-combination queries to rank, is usually dedicated
   collection/sub-collection pages — not exposing every filter combination as its own indexable URL.

6. **A static/exported inventory data file that doesn't sync back to the CMS is a real but separate
   problem from a traffic decline.** It causes staleness (a product's status changes in the admin panel
   but never reaches the storefront) — this is a maintainability finding, not necessarily the cause of
   a ranking drop. Don't conflate the two; report the architecture finding on its own merits and only
   connect it to the traffic decline if there's actual evidence (e.g. a schema-generation bug traced to
   that same data source).

7. **Copy-pasted per-category templates multiply the cost of every future fix, but measure the
   duplication, don't estimate it.** `diff templateA templateB | grep -c '^[<>]'` against total line
   count gives a real percentage. An eyeballed "these look similar" is not a finding worth reporting a
   number for.

8. **Sequencing: never noindex a page whose replacement isn't confirmed ranking yet.** The validated
   order is collections-first, then prune the product tail beneath them (Phase 6) — reversing this
   order orphans demand with nothing yet catching it.

9. **Target the content-type, not the URL pattern, for indexation rules.** Blog posts and collection
   pages frequently share the same URL path depth as products on the same site. A path-based noindex
   rule will catch pages it shouldn't. Target the actual post-type/content-type in the CMS.

10. **Scripts written to a session's scratchpad/temp directory do not persist across sessions.** If a
    computation needs to be reproducible or reusable later, write it to a real project path (or, for a
    skill's own bundled logic, into the skill's own `scripts/` directory) — not a temp path that gets
    wiped. This exact mistake happened while building this skill: the original analysis scripts were
    written to an ephemeral scratchpad and were gone by the time this skill needed to reference them,
    requiring reconstruction from verified prior work rather than a direct copy.

11. **`pip install` at the system level may fail silently-ish with a clear but easy-to-miss error** on
    PEP-668-protected Python environments (`error: externally-managed-environment`). Always build an
    isolated venv for the statistical stack — see `scripts/setup_env.sh` — rather than fighting the
    system interpreter or reaching for `--break-system-packages` (which risks the host's own Python
    tooling).

12. **When building the branded XLSX, `openpyxl` merged cells only expose the top-left cell as
    writable.** Merging a full multi-row stat-card block into one cell and then trying to write to
    three different rows within it throws `AttributeError: 'MergedCell' object attribute 'value' is
    read-only`. Merge each *line* of a stat card separately (number / change / label as three separate
    merges), not the whole card as one merge. See `scripts/report_helpers.py` for the working pattern.

13. **Passing a color as a bare string like `"GREEN"` instead of the actual hex-color variable is a
    silent, easy-to-make typo** in a large table-building script — it throws a
    `ValueError: Colors must be aRGB hex values` deep in openpyxl's border-color setter, often far from
    the actual mistake. When authoring a large branded table with per-row severity colors, grep the
    finished script for stray quoted color-name strings (`"GREEN"`, `"RED"`, `"ORANGE"`) before running
    it — every one is a bug.

14. **Mixing table shapes (different column counts) on one spreadsheet tab breaks column widths**,
    because `openpyxl` column widths are a worksheet-level property, not per-table. If a sheet has a
    3-column table and a 5-column table, decide the shared column layout up front (pad the narrower
    table with empty cells in the extra columns, or restructure it to match) rather than setting
    per-table widths that silently overwrite each other.
