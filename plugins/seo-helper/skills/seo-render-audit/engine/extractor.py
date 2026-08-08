import json
from urllib.parse import urlparse
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from models import SignalResult


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _meta(soup: BeautifulSoup, name: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": name})
    if tag:
        return tag.get("content", "").strip() or None
    return None


def _og(soup: BeautifulSoup, prop: str) -> Optional[str]:
    tag = soup.find("meta", property=prop)
    return tag.get("content", "").strip() if tag else None


def _canonical(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("link", rel="canonical")
    return tag.get("href", "").strip() if tag else None


def _jsonld(soup: BeautifulSoup) -> List[dict]:
    blocks = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            blocks.append(json.loads(tag.string or "{}"))
        except Exception:
            pass
    return blocks


def _links(soup: BeautifulSoup, base_domain: str) -> List[str]:
    hrefs = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("/") or base_domain in href:
            hrefs.append(href)
    return list(set(hrefs))


def _images(soup: BeautifulSoup) -> List[dict]:
    imgs = []
    for img in soup.find_all("img"):
        imgs.append({
            "src": img.get("src", ""),
            "alt": img.get("alt", None),
            "loading": img.get("loading", ""),
        })
    return imgs


def _text_volume(soup: BeautifulSoup) -> int:
    return len(soup.get_text(separator=" ", strip=True))


def _headings(soup: BeautifulSoup, tag: str) -> List[str]:
    return [h.get_text(strip=True) for h in soup.find_all(tag)]


def _match(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return sorted(str(x) for x in a) == sorted(str(x) for x in b)
    return str(a or "").strip() == str(b or "").strip()


def extract_signals(
    raw_html: str,
    rendered_html: str,
    response_headers: Dict[str, str],
    base_url: str,
) -> List[SignalResult]:
    """
    Pure Python extraction. No AI.
    Returns a list of SignalResult for every tracked signal.
    """
    raw = _soup(raw_html)
    rend = _soup(rendered_html)
    domain = urlparse(base_url).netloc
    signals: List[SignalResult] = []

    def sig(signal_id, category, signal_name, raw_val, rend_val,
            match_override=None) -> SignalResult:
        matched = match_override if match_override is not None \
                  else _match(raw_val, rend_val)
        return SignalResult(
            signal_id=signal_id,
            category=category,
            signal_name=signal_name,
            raw_value=raw_val,
            rendered_value=rend_val,
            match=matched,
        )

    # ── META TAGS ─────────────────────────────────────────────────────────────
    signals.append(sig(
        "title", "Meta Tags", "Title Tag",
        raw.title.string.strip() if raw.title else None,
        rend.title.string.strip() if rend.title else None,
    ))
    signals.append(sig(
        "meta_description", "Meta Tags", "Meta Description",
        _meta(raw, "description"), _meta(rend, "description"),
    ))
    signals.append(sig(
        "meta_robots", "Indexability", "Meta Robots",
        _meta(raw, "robots"), _meta(rend, "robots"),
    ))
    signals.append(sig(
        "x_robots_header", "Indexability", "X-Robots-Tag Header",
        response_headers.get("X-Robots-Tag"), None,
        match_override=True, # header-only, no render comparison
    ))

    # ── CANONICAL ─────────────────────────────────────────────────────────────
    signals.append(sig(
        "canonical", "Indexability", "Canonical Tag",
        _canonical(raw), _canonical(rend),
    ))

    # ── HEADINGS ──────────────────────────────────────────────────────────────
    for lvl in ["h1", "h2", "h3"]:
        raw_h = _headings(raw, lvl)
        rend_h = _headings(rend, lvl)
        signals.append(sig(
            lvl, "Headings", f"{lvl.upper()} Tags",
            raw_h, rend_h,
        ))

    # ── BODY TEXT : with actual JS-gated text blocks ─────────────────────────
    raw_chars = _text_volume(raw)
    rend_chars = _text_volume(rend)
    gap_chars = rend_chars - raw_chars
    gap_pct = round((gap_chars / rend_chars * 100), 1) if rend_chars else 0

    # Collect actual text blocks present in rendered but absent from raw
    # Use broader capture: include non-leaf nodes up to 3 levels deep, min 30 chars
    def _text_blocks(soup):
        seen = set()
        blocks = set()
        for t in soup.find_all(["p","li","h1","h2","h3","h4","h5","span","td","div","section","article"]):
            txt = t.get_text(strip=True)
            if len(txt) > 30 and txt not in seen:
                seen.add(txt)
                blocks.add(txt)
        return blocks

    raw_blocks = _text_blocks(raw)
    rend_blocks = _text_blocks(rend)
    js_gated = sorted(rend_blocks - raw_blocks, key=len, reverse=True)[:15]

    signals.append(SignalResult(
        signal_id="body_text",
        category="Content",
        signal_name="Body Text Volume",
        raw_value={
            "char_count": raw_chars,
        },
        rendered_value={
            "char_count": rend_chars,
            "gap_chars": gap_chars,
            "gap_pct": gap_pct,
            "js_gated_text_samples": js_gated,
        },
        match=(gap_pct < 10),
        gap_significance=(
            "high" if gap_pct >= 60 else
            "medium" if gap_pct >= 30 else
            "low" if gap_pct >= 10 else
            "none"
        ),
    ))

    # ── LINKS : with actual JS-only hrefs ─────────────────────────────────────
    raw_links = _links(raw, domain)
    rend_links = _links(rend, domain)
    gap_links = [l for l in rend_links if l not in raw_links]
    signals.append(SignalResult(
        signal_id="internal_links",
        category="Links",
        signal_name="Internal Links",
        raw_value={"count": len(raw_links)},
        rendered_value={
            "count": len(rend_links),
            "js_only_hrefs": gap_links[:20],
            "js_only_hrefs_total": len(gap_links),
        },
        match=(len(gap_links) == 0),
        gap_significance=(
            "high" if len(gap_links) > 10 else
            "medium" if len(gap_links) > 3 else
            "low" if len(gap_links) > 0 else
            "none"
        ),
    ))

    # ── JSON-LD SCHEMA : with full blocks ─────────────────────────────────────
    raw_ld = _jsonld(raw)
    rend_ld = _jsonld(rend)
    raw_types = [b.get("@type", "") for b in raw_ld]
    rend_types = [b.get("@type", "") for b in rend_ld]
    signals.append(SignalResult(
        signal_id="json_ld",
        category="Schema",
        signal_name="JSON-LD Schema",
        raw_value={"types": raw_types or None, "blocks": raw_ld},
        rendered_value={"types": rend_types or None, "blocks": rend_ld},
        match=(_match(raw_types, rend_types)),
    ))

    # ── OG TAGS ───────────────────────────────────────────────────────────────
    signals.append(sig(
        "og_title", "Meta Tags", "OG Title",
        _og(raw, "og:title"), _og(rend, "og:title"),
    ))

    # ── IMAGES : with specific differing src/alt values ───────────────────────
    raw_imgs = _images(raw)
    rend_imgs = _images(rend)
    raw_srcs = {i["src"] for i in raw_imgs if i["src"]}
    rend_srcs = {i["src"] for i in rend_imgs if i["src"]}

    js_only_imgs_all = [i for i in rend_imgs
                        if i["src"] and i["src"] not in raw_srcs]
    missing_alt_all = [i for i in rend_imgs
                        if i.get("alt") is None or i.get("alt") == ""]
    js_only_imgs = js_only_imgs_all[:10]
    # NOT sample-capped: outputs/xlsx_builder.py's "Missing Alt Images" sheet
    # promises a full list, so this field must stay complete.
    missing_alt = missing_alt_all
    lazy_imgs = [i for i in raw_imgs
                     if "data-lazy" in str(i.get("src","")).lower()
                     or "data-src" in str(i).lower()][:5]

    n_js_only = len(js_only_imgs_all)
    n_missing_alt = len(missing_alt_all)
    signals.append(SignalResult(
        signal_id="images",
        category="Images",
        signal_name="Images",
        raw_value={
            "signal_type": "images",
            "count": len(raw_imgs),
            "lazy_load_detected": lazy_imgs,
        },
        rendered_value={
            "signal_type": "images",
            "count": len(rend_imgs),
            "js_only_images": js_only_imgs,
            "js_only_images_total": n_js_only,
            "missing_alt": missing_alt,
            "missing_alt_total": n_missing_alt,
        },
        match=(len(raw_imgs) == len(rend_imgs) and n_missing_alt == 0),
        gap_significance=(
            "high" if (n_missing_alt > 10 or n_js_only > 10) else
            "medium" if (n_missing_alt > 3 or n_js_only > 3) else
            "low" if (n_missing_alt > 0 or n_js_only > 0) else
            "none"
        ),
    ))

    return signals
