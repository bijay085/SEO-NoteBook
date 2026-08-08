# Report Catalog : the 11 dimensions + build pattern

For each dimension: its question, source, mode, and how to build it. Scale to
inputs : drop a dimension whose source is absent and note it on the cover.
Dimensions **3, 5, 6, 11** are the spine whenever the pages fetch.

Section order in the combined doc: Contents (hub cards) -> Executive Summary ->
1 Live Search Performance -> 2 Measured Performance -> 3 Technical & Rendering ->
4 Deep-Dive -> 5 On-Page & Schema -> 6 Contamination (+ Corrected Drafts) ->
7 Duplication -> 8 Locations -> 9 CRO -> 10 Authorship & E-E-A-T -> 11 Action Items.

---
## 1 . Live Search Performance (GSC reality check) [script+author]
**Q:** What actually earns clicks, and what's cannibalizing? **In:** GSC 90d.
Stat cards (money-page clicks, biggest impr->clicks gap, duplicate-URL pairs,
brand-term leakage, sitemap errors); a top-pages-by-clicks table (kind = home /
blog / money / nav) showing the blog-vs-money gap; a cannibalization table (keep
green URL, 301 the red); a findings table. Methodology 6 & 7.

## 2 . Measured Performance (Lighthouse + CWV) [script+author]
**Q:** Are the pages actually fast, and accessible? **In:** Lighthouse on the key
pages. Stat cards + a scorecard table (Perf / LCP / CLS / Speed Index / TTFB /
transfer / A11y / SEO / Best-Pr). **Label the desktop profile** and add the
desktop-vs-mobile caveat note. Findings often include a *Good* (desktop is fast)
and a *Medium* (mobile unmeasured; accessibility below 90). Methodology 1 & 2.

## 3 . Technical & Rendering [script]
**Q:** Weight, CSS, DOM, trackers, native form per page. **In:** live fetch. A
per-page table (raw KB, gzip, inline CSS KB, inline JS KB, DOM nodes, ext CSS/JS,
tracker count, native form yes/no) with red flags over guideline (inline CSS <30
KB, DOM <1,400, one tracker, a native form in HTML). A weight bar chart.

## 4 . Per-Section Forensic Deep-Dive [script+author]
**Q:** Where is the DOM/payload concentrated? **In:** `sections.json`. A summary
table of ALL pages (nodes, payload, heaviest section, content context), then full
tear-downs for ~5 representative pages: heaviest sections (note nesting,
Methodology 5) + an Issue/Evidence/Solution/Execution table (CSS, DOM, SVG,
scripts). Because the template is shared, one fix repeats across all pages.

## 5 . On-Page & Schema [script+author]
**Q:** Titles, meta, H1, JSON-LD stack. **In:** live fetch. Table: title chars
(<=60), meta chars (~150-160), H1, schema present (LocalBusiness/Service/
AggregateRating/BreadcrumbList), flags (no schema / title long / generic H2).
Call out any page shipping zero structured data and any overlapping titles/H1s.

## 6 . Content Contamination (cloned wrong-product blocks) [author]
**Q:** Which pages carry another product's copy? **In:** live fetch + your read.
Main-content-only (Methodology 3). A per-page verdict + wrong-block count, and a
**Corrected Drafts** section: for each wrong block, verbatim FIND (current) ->
REPLACE (corrected). This is usually the highest-value content finding.

## 7 . Duplication / Templating [script+author]
**Q:** How templated is the site? **In:** templated-ratio + verbatim-sentence
detection. Cross-page duplication beyond single-product clones: the shared process
template, repeated trust/grid blocks, verbatim sentences on N/N pages.

## 8 . Location / Doorway-Page Uniqueness [script+author]
**Q:** Can any single city page rank? **In:** location fetch. Templated % per
city, unique-sentence count, verdict (near-duplicate / partly / unique). The fix:
unique local block per city ABOVE the shared template.

## 9 . CRO / Conversion Path [author]
**Q:** Does the page convert? **In:** live fetch + read. Tap-to-call count, first
CTA, lead-form mechanism (native vs JS/iframe : a JS form is invisible to crawlers
and blank on cold load), native form yes/no, mobile first-view call button. If
verified Clarity exists, add friction (rage/dead clicks, scroll, form drop-off);
else mark the behavioural gap.

## 10 . Authorship & E-E-A-T [script+author]
**Q:** Is the author a real, verifiable entity : not just a byline? **In:** live
fetch + read. Per author/article: the author-box link resolves (not `href=""` or a
404/301 `/author/` route), an author/`Person` JSON-LD node ties the piece to a named
person with credentials/`sameAs`, and the byline reaches an on-site bio. For **YMYL**
pages (health/finance/legal) this is ranking-load-bearing. Evidence = the actual
href (or its emptiness), the `Person` block (or its absence), the `/author/` HTTP
status. Fix = the exact author-box href + a `Person` schema FIND->REPLACE. On-page
authorship only : off-site authority (backlinks) is the `seo-off-page-audit` skill.
Methodology 12.

## 11 . Action Items (prioritized, executable) [author]
**Q:** What do we do, in order? **In:** all above. One row per fix: Issue . Scope .
Severity . Evidence (measured/quoted) . Solution . Executable step . Effort .
Priority (P0/P1/P2). Methodology 10. This is the team's working backlog : make
each step concrete and verifiable.

---
## Build pattern (report_data.py + two builders)
- **`report_data.py`** : ALL authored content as dicts/lists (findings, corrected
  drafts, stat tuples, Lighthouse rows). Both builders `import report_data as RD`.
  Keep measured numbers here or in the `*.json` the scripts emit; builders only
  render.
- **`build_html.py`** : renders each section via small functions returning HTML
  strings (f-strings); inline SVG charts; sticky grouped nav; hub-card contents
  grid; `<details>` collapsibles; a shared CSS block. Escape with `html.escape`.
- **`build_xlsx.py`** : openpyxl; one tab per dimension + Overview + Action-Items;
  helpers for newsheet / titleblk / header-row / cell; black-bg/yellow-text
  headers; set column widths + freeze panes explicitly; brand font on every cell.
- **Parity** : a new measured layer goes into BOTH builders and the Overview index.

## Validation checklist (run before delivery)
- HTML: `<section>`/`</section>`, `<table>`/`</table>`, `<details>`/`</details>`
  balanced; no leftover `{RD.` or `{fn(` placeholders; headline counts (e.g. "N
  prioritized fixes", "M P0") match the arrays; every chart/table populated.
- XLSX: tab count == index length; each tab's key cells populated; freeze panes set.
- Both: copy to `<output_dir>/`, send, and summarize honestly (incl. corrections).
