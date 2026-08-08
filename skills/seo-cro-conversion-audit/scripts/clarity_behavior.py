#!/usr/bin/env python3
"""Turn Microsoft Clarity CSV exports into per-page behavioral evidence.

Usage:
    python clarity_behavior.py <clarity_dir> <out_dir> [site_url]

<clarity_dir> has one sub-folder per page, each holding the three Clarity
exports: *_Click_PC_*.csv, *_Scroll_PC_*.csv, *_Attention_PC_*.csv. Each CSV is
a key/value header block, then a ``"Metric","Click|Scroll|Attention"`` marker,
then a table. Writes ``<out_dir>/clarity_findings.json``.

Click rows are CSS selectors, so conversion vs non-conversion is a KEYWORD pass:
unambiguous rows are classified; anything generic is left ``ambiguous`` and
listed for the Stage-3 live-verification step (never silently guessed). Reach %
per scroll band = visitors / page_views (this reproduces Clarity's own curve).
An integrity check compares each folder's label against the page URL Clarity
actually recorded (catches mislabeled/mismatched exports).
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from common import write_json

_CONV = re.compile(
    r"(tel:|mailto:|contact|get[-_ ]?a[-_ ]?(free[-_ ]?)?(quote|proposal)|get[-_ ]?started|"
    r"getstarted|request|book[-_ ]|schedule|proposal|consult|vs-btn|elementor-popup|"
    r"popup-trigger|\bcta\b|sign[-_ ]?up|free[-_ ]?(quote|assessment|audit|consult)|"
    r"create[-_ ]?ticket|start[-_ ]?(now|today)|get[-_ ]?in[-_ ]?touch)", re.I)
_NONCONV = re.compile(
    r"(menu|nav-|navbar|sub-menu|breadcrumb|accordion|\bfaq\b|customteam|slider|swiper|"
    r"-prev|-next|carousel|footer|logo|read-?more|arrow|toggle|tab-|cookie|search)", re.I)


def _to_int(s):
    try:
        return int(re.sub(r"[^\d]", "", s or "0") or 0)
    except ValueError:
        return 0


def _to_pct(s):
    m = re.search(r"-?\d+(?:\.\d+)?", s or "")
    return float(m.group(0)) if m else 0.0


def _parse(path):
    """Return (header_dict, metric, columns, rows)."""
    header, metric, columns, rows = {}, "", [], []
    with open(path, newline="", encoding="utf-8", errors="ignore") as fh:
        reader = list(csv.reader(fh))
    i, n = 0, len(reader)
    while i < n:
        row = reader[i]
        if len(row) >= 2 and row[0] == "Metric":
            metric = row[1]
            i += 1
            break
        if len(row) == 2 and row[0]:
            header[row[0].strip()] = row[1].strip()
        i += 1
    while i < n and not (reader[i] and reader[i][0]):
        i += 1
    if i < n:
        columns = [c.strip() for c in reader[i]]
        i += 1
    while i < n:
        row = reader[i]
        if row and any(c.strip() for c in row):
            rows.append(row)
        i += 1
    return header, metric, columns, rows


def _click(path):
    header, _, _, rows = _parse(path)
    total = conv = nonconv = ambig = 0
    distractor = None
    ambiguous = []
    for r in rows:
        if len(r) < 3:
            continue
        sel, clicks = r[1], _to_int(r[2])
        leaf = sel.split(">")[-1] # the element actually clicked
        total += clicks
        if _NONCONV.search(sel): # nav / menu / footer / carousel are ancestors
            nonconv += clicks
            if distractor is None or clicks > distractor[1]:
                distractor = (sel[:60], clicks)
        elif _CONV.search(leaf): # conversion intent must sit on the leaf control
            conv += clicks
        else:
            ambig += clicks
            if len(ambiguous) < 8:
                ambiguous.append({"selector": sel[:120], "clicks": clicks})
    return {
        "page_views": _to_int(header.get("Page views", "0")),
        "total_clicks_reported": _to_int(header.get("Total clicks", "0")),
        "table_clicks": total,
        "conversion_clicks": conv,
        "conversion_click_pct": round(100 * conv / total, 2) if total else 0.0,
        "nonconversion_clicks": nonconv,
        "ambiguous_clicks": ambig,
        "top_distractor": ({"element": distractor[0], "clicks": distractor[1],
                            "pct_of_table": round(100 * distractor[1] / total, 2)}
                           if distractor and total else None),
        "ambiguous_for_review": ambiguous,
        "matched_url_regex": header.get("Visited URL matches regex", ""),
    }


def _scroll(path):
    header, _, _, rows = _parse(path)
    pv = _to_int(header.get("Page views", "0")) or 1
    bands = []
    for r in rows:
        if len(r) < 2:
            continue
        depth, visitors = _to_int(r[0]), _to_int(r[1])
        bands.append({"depth_pct": depth, "reach_pct": round(100 * visitors / pv, 1)})
    biggest = None
    for a, b in zip(bands, bands[1:]):
        drop = a["reach_pct"] - b["reach_pct"]
        if biggest is None or drop > biggest["drop_pts"]:
            biggest = {"from_depth": a["depth_pct"], "to_depth": b["depth_pct"],
                       "from_reach": a["reach_pct"], "to_reach": b["reach_pct"],
                       "drop_pts": round(drop, 1)}
    halfway = min(bands, key=lambda x: abs(x["depth_pct"] - 50), default=None)
    return {"bands": bands, "biggest_single_band_drop": biggest,
            "reach_at_halfway": halfway}


def _attention(path):
    header, _, _, rows = _parse(path)
    parsed = []
    for r in rows:
        if len(r) < 3:
            continue
        parsed.append({"depth_pct": _to_int(r[0]), "avg_time": r[1].strip(),
                       "pct_session": _to_pct(r[2])})
    top = max(parsed, key=lambda x: x["pct_session"], default=None)
    return {"bands": parsed, "top_attention_band": top}


def _find(folder, needle):
    for p in Path(folder).glob("*.csv"):
        if needle.lower() in p.name.lower():
            return p
    return None


def _audit_date(window):
    m = re.findall(r"(\d{2})/(\d{2})/(\d{4})", window or "")
    if m:
        mm, dd, yyyy = m[-1]
        return f"{yyyy}-{mm}-{dd}"
    return ""


def _label_url_mismatch(label, url_regex):
    """Flag when folder label topic words are absent from the recorded URL."""
    stop = {"page", "data", "clarity", "home", "homepage", "about", "team",
            "pricing", "contact", "blog", "service", "services", "the", "top", "best"}
    words = [w for w in re.split(r"[^a-z0-9]+", (label or "").lower())
             if len(w) > 3 and w not in stop]
    url = (url_regex or "").lower()
    if not words:
        return None
    missing = [w for w in words if w not in url]
    if missing: # a distinctive topic token is absent from the URL
        return f"Folder '{label}' token(s) {missing} absent from recorded URL ({url_regex})."
    return None


def build(clarity_dir, site_url=None):
    root = Path(clarity_dir)
    pages, integrity, window = {}, [], ""
    for sub in sorted(p for p in root.iterdir() if p.is_dir()):
        click_f, scroll_f, att_f = (_find(sub, "Click"), _find(sub, "Scroll"), _find(sub, "Attention"))
        if not any((click_f, scroll_f, att_f)):
            continue
        rec = {"folder_label": sub.name}
        url_regex = ""
        if click_f:
            c = _click(click_f); rec["click"] = c; url_regex = c["matched_url_regex"]
        if scroll_f:
            rec["scroll"] = _scroll(scroll_f)
        if att_f:
            rec["attention"] = _attention(att_f)
            h, _, _, _ = _parse(att_f); window = window or h.get("Date range", "")
        if click_f and not window:
            h, _, _, _ = _parse(click_f); window = h.get("Date range", "")
        mism = _label_url_mismatch(sub.name, url_regex)
        if mism:
            rec["data_mismatch_flag"] = True
            integrity.append({"issue": "FOLDER/URL MISMATCH", "detail": mism, "handling":
                              "Reported under the URL Clarity actually recorded; flag to client."})
        pages[sub.name] = rec
    return {
        "audit_date": _audit_date(window),
        "data_window": window,
        "methodology_note": {
            "source_folder": str(root),
            "classification": {
                "conversion": "CTA/contact/quote/get-started/tel: selectors (lead-capture intent).",
                "non_conversion": "Nav menus, breadcrumbs, accordions, sliders/carousels, footer, logo.",
                "ambiguous": "Generic selectors (e.g. bare .elementor-button) left for live verification.",
            },
            "reach_definition": "Scroll reach % per band = visitors / page_views.",
        },
        "integrity_issues": integrity,
        "pages": pages,
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    data = build(argv[0], argv[2] if len(argv) > 2 else None)
    write_json(Path(argv[1]) / "clarity_findings.json", data)
    print(f"clarity_behavior: {len(data['pages'])} page(s); "
          f"{len(data['integrity_issues'])} integrity issue(s); window={data['data_window'][:32]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
