"""Process the Baseline Snapshot raw pulls (GSC, backlinks, Lighthouse, rankings, GBP)
into the initial-analysis baseline summary + detail tables.

Usage:
    python baseline_metrics.py <raw_baseline_dir> [out_dir]

<raw_baseline_dir> holds the saved MCP responses, one JSON per pull
(engine-run/raw-baseline/*.json), using these exact filenames -- any missing file
just drops that module from the output, never blocks the run:
  gsc-16mo-query.json / gsc-16mo-page.json query_search_analytics, dimensions=[query]/[page], ~16mo window
  gsc-3mo-query.json / gsc-3mo-page.json same, ~3mo window
  backlinks-summary.json backlinks_summary
  backlinks-domains.json backlinks_referring_domains
  backlinks-spam.json backlinks_bulk_spam_score, targets = the domains from backlinks-domains.json
  lighthouse.json on_page_lighthouse
  ranked-keywords.json dataforseo_labs_google_ranked_keywords
  gbp-listing.json business_data_business_listings_search

Outputs into out_dir:
  baseline-summary.json one JSON: every module's headline numbers
  baseline-gsc-queries.tsv query clicks_16mo impr_16mo pos_16mo clicks_3mo impr_3mo pos_3mo clicks_delta impr_delta pos_delta
  baseline-gsc-pages.tsv same, keyed by page
  baseline-backlink-domains.tsv domain rank spam_score spam_flag backlinks first_seen
  baseline-ranked-keywords.tsv keyword position search_volume url

NOTE ON FIELD-SHAPE CONFIDENCE: GSC extraction follows Google's public Search
Analytics API response shape (stable, high confidence). Lighthouse extraction
follows Google Lighthouse's public report schema (high confidence). DataForSEO
Backlinks / Labs ranked-keywords / Business Data extraction is written
defensively (recursive key search, tries multiple known field-name variants)
from DataForSEO's documented API shapes, but was only checked against a
hand-built synthetic fixture, not a live response -- verify against the first
real pull and adjust the `_first(...)` key variants below if a module comes
back empty.

Spam-score threshold (SPAM_FLAG_THRESHOLD) and the DR-equivalent rank bands
(RANK_BANDS) are practitioner conventions (Interpretation-basis), not
Google/DataForSEO-defined cutoffs -- adjust freely per client risk tolerance.
RANK_BANDS use DataForSEO's own 0-1000 domain rank score, which is NOT the
same metric as Ahrefs DR -- don't relabel it as DR in a client-facing report.

INP: a FIELD metric (needs real user interactions over time via Chrome UX
Report / CrUX) -- a single lab-mode page-load audit structurally cannot
produce a genuine one, and no CrUX/field-data tool is available through the
connected DataForSEO MCP server. The script still looks for it defensively in
case a fuller payload carries a CrUX passthrough, but defaults to an explicit
"not available" string rather than fabricating a number or silently
substituting TBT.
"""
import sys, os, json, glob

SPAM_FLAG_THRESHOLD = 30
RANK_BANDS = [(0, 199, "low"), (200, 499, "medium"), (500, 1000, "high")]
POSITION_TIERS = [3, 5, 10, 50, 100]


def _num(v, default=0.0):
    try:
        return default if v is None else float(v)
    except (TypeError, ValueError):
        return default


def _load(path):
    if not os.path.isfile(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"skip {path}: {e}")
        return None


def _find_all(obj, key):
    """Recursively collect every dict that has `key`, anywhere in obj."""
    out = []
    if isinstance(obj, dict):
        if key in obj:
            out.append(obj)
        for v in obj.values():
            out.extend(_find_all(v, key))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_find_all(v, key))
    return out


def _first(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None:
            return d[k]
    return None


def rank_band(rank):
    r = _num(rank)
    for lo, hi, label in RANK_BANDS:
        if lo <= r <= hi:
            return label
    return "unknown"


# ---------- GSC ----------

def gsc_rows(data):
    """rows = [{keys:[q_or_page], clicks, impressions, position}, ...] per the
    Search Console searchanalytics.query response shape."""
    if not data:
        return {}
    rows = data.get("rows") if isinstance(data, dict) else None
    if rows is None:
        hits = _find_all(data, "rows")
        rows = hits[0]["rows"] if hits else []
    out = {}
    for r in rows or []:
        keys = r.get("keys") or []
        if not keys:
            continue
        entity = keys[0]
        out[entity] = {
            "clicks": _num(r.get("clicks")),
            "impressions": _num(r.get("impressions")),
            "position": _num(r.get("position")),
        }
    return out


def process_gsc(raw_dir, out_dir, summary):
    pairs = [
        ("query", "gsc-16mo-query.json", "gsc-3mo-query.json", "baseline-gsc-queries.tsv"),
        ("page", "gsc-16mo-page.json", "gsc-3mo-page.json", "baseline-gsc-pages.tsv"),
    ]
    any_written = False
    for dim, longf, shortf, outfile in pairs:
        long_rows = gsc_rows(_load(os.path.join(raw_dir, longf)))
        short_rows = gsc_rows(_load(os.path.join(raw_dir, shortf)))
        if not long_rows and not short_rows:
            continue
        entities = sorted(set(long_rows) | set(short_rows),
                           key=lambda e: -(long_rows.get(e, {}).get("clicks", 0)))
        path = os.path.join(out_dir, outfile)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"{dim}\tclicks_16mo\timpr_16mo\tpos_16mo\tclicks_3mo\timpr_3mo\tpos_3mo\tclicks_delta\timpr_delta\tpos_delta\n")
            for e in entities:
                lo = long_rows.get(e, {"clicks": 0.0, "impressions": 0.0, "position": 0.0})
                sh = short_rows.get(e, {"clicks": 0.0, "impressions": 0.0, "position": 0.0})
                fh.write(f"{e}\t{int(lo['clicks'])}\t{int(lo['impressions'])}\t{lo['position']:.1f}\t"
                         f"{int(sh['clicks'])}\t{int(sh['impressions'])}\t{sh['position']:.1f}\t"
                         f"{int(sh['clicks'] - lo['clicks'])}\t{int(sh['impressions'] - lo['impressions'])}\t"
                         f"{(sh['position'] - lo['position']):.1f}\n")
        any_written = True
        summary[f"gsc_{dim}_16mo_total_clicks"] = int(sum(v["clicks"] for v in long_rows.values()))
        summary[f"gsc_{dim}_16mo_total_impressions"] = int(sum(v["impressions"] for v in long_rows.values()))
        summary[f"gsc_{dim}_3mo_total_clicks"] = int(sum(v["clicks"] for v in short_rows.values()))
        summary[f"gsc_{dim}_3mo_total_impressions"] = int(sum(v["impressions"] for v in short_rows.values()))
    if not any_written:
        summary["gsc"] = "not pulled"


# ---------- Backlinks ----------

def process_backlinks(raw_dir, out_dir, summary):
    summ = _load(os.path.join(raw_dir, "backlinks-summary.json"))
    if summ:
        hits = _find_all(summ, "referring_domains")
        row = hits[0] if hits else {}
        summary["backlinks_total"] = int(_num(_first(row, "backlinks")))
        summary["referring_domains_total"] = int(_num(_first(row, "referring_domains")))
        summary["referring_ips_total"] = int(_num(_first(row, "referring_ips")))

    domains = _load(os.path.join(raw_dir, "backlinks-domains.json"))
    spam = _load(os.path.join(raw_dir, "backlinks-spam.json"))
    spam_by_target = {}
    if spam:
        for hit in _find_all(spam, "spam_score"):
            t = _first(hit, "target", "domain")
            if t:
                spam_by_target[t] = _num(hit.get("spam_score"))

    if domains:
        items = _find_all(domains, "domain") or _find_all(domains, "target")
        path = os.path.join(out_dir, "baseline-backlink-domains.tsv")
        flagged = 0
        band_counts = {}
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("domain\trank\tspam_score\tspam_flag\tbacklinks\tfirst_seen\n")
            for it in items:
                d = _first(it, "domain", "target") or ""
                if not d:
                    continue
                rank = _num(_first(it, "rank", "domain_rank"))
                ss = spam_by_target.get(d, _num(_first(it, "spam_score")))
                flag = ss >= SPAM_FLAG_THRESHOLD
                flagged += 1 if flag else 0
                bl = _num(_first(it, "backlinks"))
                fs = _first(it, "first_seen") or ""
                fh.write(f"{d}\t{rank:g}\t{ss:g}\t{'yes' if flag else 'no'}\t{int(bl)}\t{fs}\n")
                band = rank_band(rank)
                band_counts[band] = band_counts.get(band, 0) + 1
        summary["backlink_domains_flagged_spam"] = flagged
        summary["backlink_domains_pulled"] = len(items)
        summary["backlink_domain_rank_bands"] = band_counts


# ---------- Lighthouse ----------

def process_lighthouse(raw_dir, out_dir, summary):
    data = _load(os.path.join(raw_dir, "lighthouse.json"))
    if not data:
        return
    cat_hits = _find_all(data, "categories")
    cat = cat_hits[0].get("categories") if cat_hits else {}
    if isinstance(cat, dict):
        for key in ("performance", "accessibility", "best-practices", "seo"):
            node = cat.get(key)
            score = _first(node, "score") if isinstance(node, dict) else None
            if score is not None:
                summary[f"lighthouse_{key.replace('-', '_')}"] = round(_num(score) * 100)

    audit_hits = _find_all(data, "audits")
    audit = audit_hits[0].get("audits") if audit_hits else {}
    metric_map = {
        "largest-contentful-paint": "lighthouse_lcp_ms",
        "cumulative-layout-shift": "lighthouse_cls",
        "total-blocking-time": "lighthouse_tbt_ms",
        "speed-index": "lighthouse_speed_index_ms",
    }
    if isinstance(audit, dict):
        for akey, out_key in metric_map.items():
            node = audit.get(akey)
            val = _first(node, "numericValue") if isinstance(node, dict) else None
            if val is not None:
                summary[out_key] = round(_num(val), 3 if "cls" in out_key else 0)

    # INP: field metric, not derivable from a lab-only page-load audit (see
    # module docstring). Look defensively, else record an explicit gap.
    inp_val = None
    if isinstance(audit, dict):
        for akey in ("interaction-to-next-paint", "experimental-interaction-to-next-paint"):
            node = audit.get(akey)
            v = _first(node, "numericValue") if isinstance(node, dict) else None
            if v is not None:
                inp_val = _num(v)
                break
    if inp_val is None:
        crux_hits = _find_all(data, "INP") or _find_all(data, "inp")
        if crux_hits:
            v = _first(crux_hits[0], "INP", "inp", "percentile", "numericValue")
            inp_val = _num(v) if v is not None else None
    summary["lighthouse_inp_ms"] = (
        round(inp_val) if inp_val is not None
        else "not available (lab-only Lighthouse run has no field/interaction data; needs a CrUX source)"
    )


# ---------- Rankings ----------

def process_rankings(raw_dir, out_dir, summary):
    data = _load(os.path.join(raw_dir, "ranked-keywords.json"))
    if not data:
        return
    # Anchor on the whole per-keyword item (has keyword_data + rank info as
    # siblings, arbitrarily nested below that) -- NOT on whichever inner dict
    # happens to hold rank_absolute directly, which is a different branch of
    # the same item and has no keyword/search_volume inside it.
    items = _find_all(data, "keyword_data")
    if not items:
        items = _find_all(data, "rank_absolute") + _find_all(data, "rank_group")
    rows = []
    for it in items:
        pos_hits = _find_all(it, "rank_absolute")
        pos = _first(pos_hits[0], "rank_absolute") if pos_hits else None
        if pos is None:
            pos_hits = _find_all(it, "rank_group")
            pos = _first(pos_hits[0], "rank_group") if pos_hits else None
        if pos is None:
            continue

        kd = it.get("keyword_data") if isinstance(it, dict) else None
        kw = _first(kd, "keyword") if isinstance(kd, dict) else None
        if not kw:
            kw_hits = _find_all(it, "keyword")
            kw = _first(kw_hits[0], "keyword") if kw_hits else ""

        sv = None
        ki = _first(kd, "keyword_info") if isinstance(kd, dict) else None
        if isinstance(ki, dict):
            sv = _first(ki, "search_volume")
        if sv is None:
            sv_hits = _find_all(it, "search_volume")
            sv = _first(sv_hits[0], "search_volume") if sv_hits else 0

        url_hits = _find_all(it, "url")
        url = _first(url_hits[0], "url") if url_hits else ""

        rows.append((kw or "", int(_num(pos)), int(_num(sv)), url))

    if not rows:
        return
    rows.sort(key=lambda r: r[1])
    path = os.path.join(out_dir, "baseline-ranked-keywords.tsv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("keyword\tposition\tsearch_volume\turl\n")
        for kw, pos, sv, url in rows:
            fh.write(f"{kw}\t{pos}\t{sv}\t{url}\n")

    tiers = {t: 0 for t in POSITION_TIERS}
    for _, pos, _, _ in rows:
        for t in POSITION_TIERS:
            if pos <= t:
                tiers[t] += 1
    summary["ranked_keywords_total"] = len(rows)
    for t in POSITION_TIERS:
        summary[f"ranked_top{t}"] = tiers[t]


# ---------- GBP ----------

def process_gbp(raw_dir, out_dir, summary):
    data = _load(os.path.join(raw_dir, "gbp-listing.json"))
    if not data:
        return
    items = _find_all(data, "title") or _find_all(data, "is_claimed")
    if not items:
        summary["gbp_matched"] = False
        return
    it = items[0]
    summary["gbp_matched"] = True
    summary["gbp_business_name"] = _first(it, "title", "name") or ""
    summary["gbp_is_claimed"] = bool(_first(it, "is_claimed"))
    rating = _first(it, "rating")
    if isinstance(rating, dict):
        summary["gbp_rating"] = _num(_first(rating, "value", "rating_value"))
        summary["gbp_review_count"] = int(_num(_first(rating, "votes_count", "rating_count")))
    else:
        summary["gbp_rating"] = _num(_first(it, "rating_value"))
        summary["gbp_review_count"] = int(_num(_first(it, "rating_count")))
    summary["gbp_category"] = _first(it, "category") or ""
    summary["gbp_address"] = _first(it, "address") or ""
    summary["gbp_phone"] = _first(it, "phone") or ""


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python baseline_metrics.py <raw_baseline_dir> [out_dir]")
    raw_dir = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else (os.path.dirname(raw_dir.rstrip("/")) or ".")
    os.makedirs(out_dir, exist_ok=True)

    summary = {}
    process_gsc(raw_dir, out_dir, summary)
    process_backlinks(raw_dir, out_dir, summary)
    process_lighthouse(raw_dir, out_dir, summary)
    process_rankings(raw_dir, out_dir, summary)
    process_gbp(raw_dir, out_dir, summary)

    spath = os.path.join(out_dir, "baseline-summary.json")
    with open(spath, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(f"baseline summary -> {spath} ({len(summary)} fields)")


if __name__ == "__main__":
    main()
