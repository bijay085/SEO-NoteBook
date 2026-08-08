#!/usr/bin/env python3
"""Extract conversion signals per domain and draft 0-10 scores.

Usage:
    python cro_signals.py <pages_dir> <out_dir> <site_url>

<pages_dir> holds saved ``view-source_<url>.html`` pages for the site AND each
competitor (grouped automatically by host). Writes ``<out_dir>/cro_signals.json``
and appends notable gaps to ``<out_dir>/findings.json``.

IMPORTANT — these scores are MECHANICAL DRAFTS, not the final verdict. They are
deliberately conservative starting points. The skill's Stage 3 (correction) is
where a human/Claude pass inspects the raw HTML, fixes false positives, and sets
the final /10. See references/methodology.md. Detectors here are written to
avoid the known false positives (dormant-CSS "sticky"/"badges", regex-missed
review stats, tag-stripped competitor HTML).
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from common import Finding, host_of, iter_pages, read_json, soup_of, visible_text, write_json

DIMENSIONS = ["UI/UX", "Coverage", "Page", "CTA", "Trust"]

_CTA_WORDS = re.compile(
    r"\b(get (a )?(free )?(quote|proposal|assessment|audit|consult\w*)|request|"
    r"book|schedule|contact us|call now|get started|start (now|today)|free trial|"
    r"talk to|speak (to|with)|claim|sign up)\b", re.I)
_SPECIFIC_CTA = re.compile(
    r"\b(free (quote|assessment|audit|consultation)|request (a )?(proposal|quote|consult)|"
    r"book (a )?(call|demo|meeting)|schedule (a )?(call|consult))\b", re.I)
_REVIEW_STAT = re.compile(
    r"(\d(?:\.\d)?)\s*/\s*5|\b(\d{1,4})\s*\+?\s*(?:google |local |b2b |verified )*reviews?\b|"
    r"\b(\d{1,4})\s*\+?\s*(?:five|5)[- ]star\b", re.I)
_GUARANTEE = re.compile(r"\b(guarantee\w*|money[- ]back|sla|100%\s+satisf)\b", re.I)
_PRICING = re.compile(r"\b(pricing|\$\s?\d+\s*/\s*(mo|month|user)|per (user|month)|our plans?)\b", re.I)
_LEAD_MAGNET = re.compile(r"\b(free (guide|ebook|checklist|template|download|assessment)|download (the|our)|whitepaper)\b", re.I)
_TESTIMONIAL = re.compile(r"\b(testimonial\w*|what our clients say|client stories|case stud\w+)\b", re.I)
_BADGE = re.compile(r"\b(clutch|gartner|g2|premier partner|gold partner|certified partner|msp 501|inc\.?\s?5000)\b", re.I)
_TRUST = re.compile(r"\b(review\w*|rating\w*|star\w*|testimonial\w*|certified|accredited|award\w*|trusted|clients?|years? (of|in)|guarantee)\b", re.I)
_SERVICE_HINT = re.compile(r"/(services?|it-|managed|support|cloud|security|consulting|voip|network|backup|helpdesk|help-desk)", re.I)


# --------------------------------------------------------------------------- #
def _has_real_sticky(soup) -> bool:
    """Real sticky element in the BODY — not a dormant CSS rule in <style>."""
    body = soup.body or soup
    for el in body.select('[class*="sticky"], [class*="fixed-"], [id*="sticky"]'):
        cls = " ".join(el.get("class", []))
        if re.search(r"\b(is-sticky|has-sticky|sticky-(nav|header|bar|top)|mysticky)\b", cls, re.I):
            return True
    for el in body.select('[style]'):
        if re.search(r"position\s*:\s*(fixed|sticky)", el.get("style", ""), re.I):
            return True
    return False


def _hero(soup) -> bool:
    """Does the first section/header carry a hero image (tag or inline bg)?"""
    head = soup.find(["header", "section"]) or soup.body
    if not head:
        return False
    if head.find("img"):
        return True
    scope = str(head)[:6000]
    return bool(re.search(r"background-image\s*:\s*url", scope, re.I))


def _real_form(soup) -> bool:
    if soup.find("form") and soup.select("form input, form textarea"):
        return True
    # Elementor / popup lead forms
    return bool(soup.select('[class*="elementor-form"], [class*="wpcf7"], [class*="gform"], '
                            '[data-settings*="form"], [class*="elementor-popup"]'))


def _profile(pages) -> dict:
    texts, words, ctas = [], [], Counter()
    has_sticky = has_form = phone = pricing = lead_magnet = testimonials = False
    hero_hits = 0
    reviews, guarantee, badges = [], False, False
    service_pages = 0
    for url, html in pages:
        soup = soup_of(html)
        txt = visible_text(html)
        texts.append(txt)
        words.append(len(txt.split()))
        has_sticky = has_sticky or _has_real_sticky(soup)
        has_form = has_form or _real_form(soup)
        hero_hits += 1 if _hero(soup) else 0
        if soup.select('a[href^="tel:"]') or re.search(r"\b\d{3}[.\-)\s]\d{3}[.\-\s]\d{4}\b", txt):
            phone = True
        pricing = pricing or bool(_PRICING.search(txt))
        lead_magnet = lead_magnet or bool(_LEAD_MAGNET.search(txt))
        testimonials = testimonials or bool(_TESTIMONIAL.search(txt)) or bool(soup.select('[class*="trustindex"], [class*="testimonial"]'))
        guarantee = guarantee or bool(_GUARANTEE.search(txt))
        badges = badges or bool(_BADGE.search(txt))
        if _SERVICE_HINT.search(url):
            service_pages += 1
        for m in _REVIEW_STAT.finditer(txt):
            reviews.append(m.group(0).strip())
        for a in soup.select('a, button'):
            t = re.sub(r"\s+", " ", a.get_text(" ")).strip()
            if t and _CTA_WORDS.search(t) and len(t) < 40:
                ctas[t] += 1
    n = max(1, len(pages))
    joined = " ".join(texts)
    return {
        "pages": len(pages),
        "service_pages": service_pages,
        "has_sticky": has_sticky,
        "phone_present": phone,
        "hero_frac": round(hero_hits / n, 2),
        "avg_words": int(sum(words) / n),
        "has_form": has_form,
        "trust_total": len(_TRUST.findall(joined)),
        "review_counts": sorted(set(reviews))[:6],
        "guarantee": guarantee,
        "badges": bool(badges),
        "testimonials": bool(testimonials),
        "lead_magnet": lead_magnet,
        "pricing": pricing,
        "top_ctas": [c for c, _ in ctas.most_common(8)],
        "specific_cta": bool(_SPECIFIC_CTA.search(joined)),
    }


def _clamp(x) -> int:
    return max(0, min(10, int(round(x))))


def _score(p: dict) -> dict:
    """Transparent DRAFT rubric (0-10). Documented in references/methodology.md."""
    cta = 5 + (2 if p["specific_cta"] else 0) + (1 if p["phone_present"] else 0)
    if len(p["top_ctas"]) > 6:              # CTA sprawl with no clear hierarchy
        cta -= 2
    trust = 2 + 2 * bool(p["review_counts"]) + 2 * p["testimonials"] + \
        2 * p["guarantee"] + 1 * p["badges"] + min(1, p["trust_total"] // 40)
    page = 3 + 2 * p["has_form"] + 2 * p["pricing"] + min(3, p["avg_words"] // 700)
    uiux = 4 + 2 * (p["hero_frac"] >= 0.5) + 1 * p["has_sticky"]
    cov = 2 + min(6, p["service_pages"] * 2) + (1 if p["pages"] > 1 else 0)
    scores = {"UI/UX": _clamp(uiux), "Coverage": _clamp(cov), "Page": _clamp(page),
              "CTA": _clamp(cta), "Trust": _clamp(trust)}
    scores["Overall"] = round(sum(scores[d] for d in DIMENSIONS) / len(DIMENSIONS), 1)
    return scores


def build(pages_dir, site_url):
    site_host = host_of(site_url)
    by_host: dict[str, list] = {}
    for url, html, _ in iter_pages(pages_dir):
        by_host.setdefault(host_of(url), []).append((url, html))
    domains = {}
    for host, pages in sorted(by_host.items()):
        prof = _profile(pages)
        domains[host] = {"is_site": host == site_host, "profile": prof, "scores": _score(prof)}
    return {"site_domain": site_host, "dimensions": DIMENSIONS, "domains": domains}


def _findings(data) -> list:
    out = []
    site = data["site_domain"]
    prof = data["domains"].get(site, {}).get("profile", {})
    if len(prof.get("top_ctas", [])) > 4 and not prof.get("specific_cta"):
        out.append(Finding("CRO-CTA-SPRAWL", "HIGH", "CTA",
                            "Multiple undifferentiated CTAs with no clear primary path",
                            f"{len(prof['top_ctas'])} CTA-like controls detected.",
                            evidence=str(prof["top_ctas"]),
                            recommended_actions=["Establish one primary CTA for new prospects; visually demote the rest."]))
    if not prof.get("review_counts"):
        out.append(Finding("CRO-TRUST-NOSTAT", "MEDIUM", "Trust",
                            "No quantified rating/review stat detected on crawled pages",
                            "No 'N reviews' or 'X/5' stat found in visible text.",
                            recommended_actions=["Surface an aggregate rating (e.g. '4.9/5 from N reviews') near the primary CTA."]))
    return [f.to_dict() for f in out]


def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    pages_dir, out_dir, site_url = argv[0], argv[1], argv[2]
    data = build(pages_dir, site_url)
    write_json(Path(out_dir) / "cro_signals.json", data)
    fpath = Path(out_dir) / "findings.json"
    existing = read_json(fpath) if fpath.exists() else []
    existing.extend(_findings(data))
    write_json(fpath, existing)
    site = data["domains"].get(data["site_domain"], {})
    print(f"cro_signals: {len(data['domains'])} domain(s); "
          f"site draft Overall={site.get('scores', {}).get('Overall')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
