# GSC fetch playbook

Exact call recipes for the connected Search Console MCP, and the constraints that will silently
corrupt a run if you ignore them.

## Access

```
list_accounts        → every authenticated Google account and its sites
list_sites           → properties for one account
```

**If more than one account is connected you must pass `account` on every call** or it errors. Put
the label in the config's `inputs.gsc_account` and use it consistently.

Prefer the **domain property** (`sc-domain:example.com`) — it covers all subdomains and protocols.
Fall back to the URL-prefix property (`https://example.com/`) on "insufficient permission."

**Window.** GSC keeps 16 months and lags 2–3 days. End the window ~2 days before today; a shorter
window costs you the handoff detector, which needs history.

## The three constraints that matter

1. **No `startRow`.** The MCP exposes `rowLimit` but no pagination cursor, and the GSC API caps a
   single request at 25,000 rows. A site whose `page × query` matrix exceeds that is **silently
   truncated** — you get the top rows and no error. Split by date instead (below).
2. **No `dataState` / `type`.** You cannot request `final` only, or restrict to `web`. Fresh
   (incomplete) days are included; that is why the window ends 2 days back.
3. **`searchAppearance` cannot combine with any other dimension.** A per-page surface mix takes two
   steps.

## Phase 1 — the matrix

```
query_search_analytics(
  account:   "<label>",
  siteUrl:   "sc-domain:example.com",
  startDate: "2025-03-28",   endDate: "2026-07-26",
  dimensions: ["page","query"],
  rowLimit:  25000
)
```

Save the raw response to `<work>/data/matrix.json`. The normaliser sniffs the shape — raw
`{"rows":[{"keys":[...],...}]}`, a bare row list, flattened records, or CSV — so don't reshape it.

**If the response comes back at or near 25,000 rows, assume truncation.** Split the window into
quarters, save each to its own file, and pass them all:

```bash
python "$SCRIPTS/gsc_normalize.py" --work <work> --site sc-domain:example.com \
  --matrix <work>/data/matrix_q1.json <work>/data/matrix_q2.json <work>/data/matrix_q3.json
```

Rows are re-aggregated per `(page, query)`, so overlapping slices are safe as long as you don't
double-count the same date range.

`export_analytics(format:"csv", …)` is an alternative for big pulls — it writes a file rather than
returning rows inline, which avoids blowing the token limit. The normaliser reads CSV too.

## Phase 1b — searchAppearance (optional)

Enables SERP-surface attribution: if one page lives mostly in Featured Snippet / Video / Rich Result
while the other is plain organic, they are not competing.

```
# step 1 — which enriched surfaces this site has at all
query_search_analytics(dimensions:["searchAppearance"], …)

# step 2 — for EACH surface returned, the pages that appeared with it
query_search_analytics(
  dimensions: ["page"],
  filters: [{dimension:"searchAppearance", operator:"equals", expression:"FEATURED_SNIPPET"}], …)
```

Concatenate the step-2 responses into one file, adding a `searchAppearance` field per row, and pass
`--appearance`. Plain blue links carry **no** appearance label, so the WEB share is derived by
subtracting enriched impressions from each page's total — pass `--page-totals` (a
`dimensions:["page"]` pull) for that, or it falls back to the totals already in `pages.csv`.

Skip this entirely if the site has no enriched surfaces; the cascade runs fine without it.

## Phase 7 — the weekly per-URL pull

This is the data the whole skill exists for. One call per shortlisted URL:

```
query_search_analytics(
  account:   "<label>",
  siteUrl:   "sc-domain:example.com",
  startDate: "2025-03-28",  endDate: "2026-07-26",
  dimensions: ["date","query"],
  filters:   [{dimension:"page", operator:"equals", expression:"https://example.com/some-page/"}],
  rowLimit:  25000
)
```

Save each raw response to `<work>/weekly/<filename>`, taking `<filename>` from the `url → filename`
map in `<work>/weekly/_fetch_list.json`. Those names are content hashes because URLs are too long
and slash-heavy to use directly.

Notes:
- Use `operator:"equals"` with the **exact** URL string from the matrix. A trailing-slash mismatch
  returns zero rows, and a URL with no rows becomes a skipped pair — reported in the report's
  Coverage section, so it will not pass unnoticed.
- 25,000 rows for one URL over 16 months is generous; real pages are far sparser. If one does hit
  the cap, slice its date range.
- One call per URL means a 200-URL shortlist is 200 calls. That is the run's dominant cost — see
  SKILL.md §Scale.

## When a pull returns nothing

- Confirm the property has data for that window in the GSC UI first.
- On a URL-prefix property, URL filtering may be excluding everything — try the `sc-domain:` one.
- The default `exclude_url_patterns` drop `/tag/`, `/category/`, `/product-tag/`,
  `/product-category/`. Clear them in the config if the site uses those as real content paths.
