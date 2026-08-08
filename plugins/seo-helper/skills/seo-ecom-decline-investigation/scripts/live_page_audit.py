#!/usr/bin/env python
"""
live_page_audit.py — severity-ranked technical/schema audit of a single saved HTML page.

Generalizes the live-page checks used in the source investigation (a hoodie collection page
that had a hardcoded/duplicated review-rating schema, JS-only uncrawlable pagination, and a
nested <main> landmark). Read-only: parses a saved HTML file, never modifies it.

Usage:
  <venv>/bin/python live_page_audit.py page.html [page2.html ...]
  <venv>/bin/python live_page_audit.py --diff templateA.html templateB.html   # duplication %

Fetching the live page first (not this script's job — use WebFetch or `curl` in the workflow,
then run this against the saved file so the audit is reproducible):
  curl -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15" \\
       -s "https://example.com/collection/" -o page.html

No external AI/LLM API is called — this is deterministic parsing (BeautifulSoup + stdlib re/json).
"""
import sys
import re
import json
import difflib

from bs4 import BeautifulSoup


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "OK": 4}


def finding(severity, title, detail):
    return {"severity": severity, "title": title, "detail": detail}


def check_schema_ratings(soup):
    """Flag identical aggregateRating values repeated verbatim across multiple JSON-LD entities —
    the exact pattern found live in the source investigation (4.8 / 1247 hardcoded on every
    Product + SoftwareApplication entity). A real per-product distribution should vary."""
    out = []
    ratings = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "{}")
        except (json.JSONDecodeError, TypeError):
            out.append(finding("MEDIUM", "Unparseable JSON-LD block",
                                "A <script type='application/ld+json'> block did not parse as valid JSON."))
            continue
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        for node in nodes if isinstance(nodes, list) else [nodes]:
            if not isinstance(node, dict):
                continue
            ar = node.get("aggregateRating")
            if isinstance(ar, dict) and "ratingValue" in ar:
                ratings.append((node.get("@type"), node.get("name"), ar.get("ratingValue"), ar.get("reviewCount")))

    if len(ratings) >= 2:
        signatures = {(rv, rc) for _, _, rv, rc in ratings}
        if len(signatures) == 1 and len(ratings) >= 3:
            rv, rc = next(iter(signatures))
            out.append(finding(
                "CRITICAL", "Identical aggregateRating hardcoded across multiple entities",
                f"{len(ratings)} entities all carry ratingValue={rv}, reviewCount={rc}. "
                "Google's structured-data policy prohibits fabricated/copy-pasted ratings — this is "
                "a real spam-signal pattern, not a cosmetic issue. Verify against actual review data "
                "per product/page, or remove the aggregateRating block entirely if none exists."
            ))
        elif len(ratings) >= 3:
            out.append(finding("OK", "aggregateRating values vary across entities",
                                f"{len(ratings)} entities, {len(signatures)} distinct rating signatures — looks like real per-product data."))
    return out


def check_pagination(soup):
    """Flag JS-only pager controls (<button> with no matching <a href>) — Googlebot cannot follow
    a button click, so paginated content beyond page 1 is invisible to the crawler."""
    out = []
    pager_candidates = soup.select("[class*=pager], [class*=pagination], [id*=pager], [id*=pagination]")
    for pager in pager_candidates:
        buttons = pager.find_all("button")
        links = pager.find_all("a", href=True)
        page_buttons = [b for b in buttons if b.get("data-page") or re.search(r"\bpage\b", str(b.get("class", [])), re.I)]
        if page_buttons and not links:
            out.append(finding(
                "CRITICAL", "Pagination is JS-only, not crawlable",
                f"Found {len(page_buttons)} page-control <button> elements with no matching <a href> "
                "in the same pager container. Googlebot cannot click buttons — pages beyond the first "
                "are invisible to the crawler. Fix: add real <a href> links (can still be intercepted "
                "by JS for a smooth AJAX experience via history.pushState), or ensure server-rendered "
                "paginated URLs exist and are linked."
            ))
        elif links:
            out.append(finding("OK", "Pagination has crawlable links",
                                f"Found {len(links)} <a href> pagination links."))
    if not pager_candidates:
        out.append(finding("LOW", "No pagination container detected",
                            "No element matched common pager/pagination class or id patterns — "
                            "confirm manually if this page is expected to paginate."))
    return out


def check_landmarks(soup):
    """Flag nested <main> elements — HTML5 permits only one per document."""
    out = []
    mains = soup.find_all("main")
    if len(mains) > 1:
        nested = any(m.find("main") for m in mains)
        if nested:
            out.append(finding(
                "HIGH", "Nested <main> element(s)",
                f"Found {len(mains)} <main> elements on the page, at least one nested inside "
                "another. HTML5 permits only one <main> landmark per document — this is invalid "
                "markup and an accessibility/parsing risk. Rename the inner element(s) to <div> or "
                "<section>."
            ))
        else:
            out.append(finding(
                "MEDIUM", "Multiple <main> elements (not nested)",
                f"Found {len(mains)} <main> elements, not nested inside each other, but still more "
                "than the one permitted per document."
            ))
    elif len(mains) == 1:
        out.append(finding("OK", "Single <main> landmark", "Exactly one <main> element found."))
    else:
        out.append(finding("MEDIUM", "No <main> landmark found",
                            "No <main> element — a missing primary-content landmark hurts accessibility."))
    return out


def check_title_h1_alignment(soup):
    """Flag a thin H1 relative to the title tag's differentiator."""
    out = []
    title_tag = soup.find("title")
    h1 = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None
    h1_text = h1.get_text(strip=True) if h1 else None
    if not title:
        out.append(finding("MEDIUM", "Missing <title> tag", "No <title> element found."))
    if not h1_text:
        out.append(finding("HIGH", "Missing <h1>", "No <h1> element found on the page."))
        return out
    if title and h1_text:
        title_words = set(re.findall(r"[a-z]+", title.lower()))
        h1_words = set(re.findall(r"[a-z]+", h1_text.lower()))
        title_only = title_words - h1_words
        if len(h1_text) < 25 and len(title_only) >= 2:
            out.append(finding(
                "MEDIUM", "H1 is thinner than the title tag",
                f"Title: \"{title}\" (differentiating words not in H1: {sorted(title_only)[:6]}). "
                f"H1: \"{h1_text}\". Consider aligning the H1 with the title tag's intent — it is "
                "read first by both users and Google."
            ))
        else:
            out.append(finding("OK", "Title/H1 reasonably aligned", f"Title: \"{title}\" · H1: \"{h1_text}\""))
    return out


def check_filter_url_state(soup):
    """Informational only — flag whether filter controls appear to write URL parameters. This is
    NOT automatically a defect (see references/pitfalls.md #5) — confirm intent with the owner."""
    out = []
    filter_inputs = soup.select("input[type=checkbox][data-tax], input[type=checkbox][data-group], "
                                 "[class*=filter] input[type=checkbox]")
    if filter_inputs:
        out.append(finding(
            "LOW", "Filter UI detected — confirm URL-state intent",
            f"Found {len(filter_inputs)} filter checkbox inputs. This audit cannot determine from "
            "static HTML alone whether filtering writes URL parameters (JS-driven). If it doesn't, "
            "confirm with the site owner whether that is a deliberate crawl-budget/index-bloat "
            "decision (common and often correct) before recommending a change — see pitfalls.md #5."
        ))
    return out


def audit_page(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    findings = []
    findings += check_schema_ratings(soup)
    findings += check_pagination(soup)
    findings += check_landmarks(soup)
    findings += check_title_h1_alignment(soup)
    findings += check_filter_url_state(soup)
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 9))

    print(f"\n{'=' * 78}\nLIVE PAGE AUDIT — {path}\n{'=' * 78}")
    print(f"  {len(html):,} bytes  ·  {len(html.splitlines()):,} lines")
    for f in findings:
        print(f"\n  [{f['severity']}] {f['title']}")
        print(f"    {f['detail']}")
    if not findings:
        print("\n  No findings from the automated checks (does not replace a manual review).")
    return findings


def diff_templates(path_a, path_b):
    """Duplication-percentage check for two candidate near-duplicate templates (pitfalls.md #7).
    Measures line-level diff, not byte-identity — near-identical pages often differ only by a
    varying token (a city, a product name), which this correctly still counts as "identical shell"."""
    a = open(path_a, encoding="utf-8", errors="replace").read().splitlines()
    b = open(path_b, encoding="utf-8", errors="replace").read().splitlines()
    sm = difflib.SequenceMatcher(None, a, b)
    ratio = sm.ratio()
    print(f"\n{'=' * 78}\nTEMPLATE DUPLICATION CHECK\n{'=' * 78}")
    print(f"  {path_a}: {len(a)} lines")
    print(f"  {path_b}: {len(b)} lines")
    print(f"  SequenceMatcher line-level similarity ratio: {ratio:.1%}")
    if ratio > 0.85:
        print("  -> Very high duplication. Strong candidate for consolidation into one dynamic "
              "template with per-instance content fields, rather than N copy-pasted files.")
    elif ratio > 0.5:
        print("  -> Substantial shared structure. Worth reviewing for consolidation opportunities.")
    else:
        print("  -> Limited overlap — likely genuinely distinct templates, not copy-paste duplicates.")
    return ratio


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == "--diff":
        if len(args) != 3:
            print("Usage: live_page_audit.py --diff templateA.html templateB.html")
            sys.exit(1)
        diff_templates(args[1], args[2])
        return
    for path in args:
        audit_page(path)


if __name__ == "__main__":
    main()
