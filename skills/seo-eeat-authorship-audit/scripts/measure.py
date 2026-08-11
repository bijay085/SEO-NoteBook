#!/usr/bin/env python3
"""Deterministic E-E-A-T / Authorship signal measurement (stdlib only : no LLM).
Usage: python measure.py <url-or-file.html> [out.json] [--no-link-check]

Checks only what's objectively verifiable from markup, JSON-LD, and one optional
HTTP HEAD probe on the author link. This is NOT a judgment on quality or
genuineness (e.g. "is this review real") : that's the LLM's job for every rule in
data/rules.csv marked check_type=llm-judgment. This script only ever answers the
narrower, machine-checkable question: is the structural signal present at all.

Emits: article schema (author type), byline text + a crude suspicious-string flag,
Person schema + sameAs count, Review/AggregateRating schema presence (presence
only : not a fabrication check), published/modified dates, policy-page links,
HTTPS, and whether a discovered author link resolves.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

SUSPICIOUS_BYLINE = re.compile(r"^(admin|administrator|webmaster|staff|team|user\d+|[a-z]+\d{4,})$", re.I)
POLICY_KEYWORDS = {"privacy": ["privacy"], "terms": ["terms", "tos"],
                    "contact": ["contact"], "about": ["about", "our-story", "our story"]}


class M(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_ld = False
        self.ld_buf = []
        self.ld_blocks = []
        self.links = []
        self._open_href = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self.in_ld = True
            self.ld_buf = []
        if tag == "a" and a.get("href"):
            self._open_href = a["href"]
            self.links.append({"href": a["href"], "rel": (a.get("rel") or "").lower(), "text": ""})

    def handle_data(self, data):
        if self.in_ld:
            self.ld_buf.append(data)
        elif self._open_href is not None and self.links:
            self.links[-1]["text"] += data

    def handle_endtag(self, tag):
        if tag == "script" and self.in_ld:
            raw = "".join(self.ld_buf).strip()
            try:
                self.ld_blocks.append(json.loads(raw))
            except Exception:
                pass
            self.in_ld = False
        if tag == "a":
            self._open_href = None


def load(src):
    if src.startswith(("http://", "https://")):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 seo-audit"})
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    return open(src, encoding="utf-8", errors="replace").read()


def flatten_ld(blocks):
    out = []
    for b in blocks:
        items = b.get("@graph") if isinstance(b, dict) and "@graph" in b else b
        if isinstance(items, list):
            out.extend(x for x in items if isinstance(x, dict))
        elif isinstance(items, dict):
            out.append(items)
    return out


def type_of(node):
    if not node:
        return []
    t = node.get("@type")
    if isinstance(t, list):
        return [str(x) for x in t]
    return [str(t)] if t else []


def check_url(url, timeout=10):
    """Best-effort resolution check. Returns True/False, or None if we genuinely
    couldn't tell (network blocked, timeout) : None must never be reported as
    'broken', only as 'not checked'."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "Mozilla/5.0 seo-audit"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status < 400
        except urllib.error.HTTPError as e:
            return e.code < 400
        except Exception:
            continue
    return None


def measure(src, check_links=True):
    html = load(src)
    p = M()
    p.feed(html)
    nodes = flatten_ld(p.ld_blocks)

    article = next((n for n in nodes if any(t in ("Article", "BlogPosting", "NewsArticle") for t in type_of(n))), None)
    persons = [n for n in nodes if "Person" in type_of(n)]
    reviews = [n for n in nodes if "Review" in type_of(n)]
    agg = [n for n in nodes if "AggregateRating" in type_of(n)]

    author_node = None
    if article and isinstance(article.get("author"), dict):
        author_node = article["author"]
    elif persons:
        author_node = persons[0]

    # A Person nested inside article.author never appears in the flattened
    # top-level node list : fold it in (dedup by identity) so person_schema
    # counts stay consistent with the sameAs figure pulled from the same node.
    if author_node and "Person" in type_of(author_node) and not any(n is author_node for n in persons):
        persons = persons + [author_node]

    same_as = author_node.get("sameAs") if author_node else None
    if isinstance(same_as, str):
        same_as = [same_as]

    byline_text = None
    bm = (re.search(r'class="[^"]*\bauthor\b[^"]*"[^>]*>\s*([^<]{2,60})<', html, re.I)
          or re.search(r'rel=["\']author["\'][^>]*>\s*([^<]{2,60})<', html, re.I))
    if bm:
        byline_text = bm.group(1).strip()
    elif author_node and isinstance(author_node.get("name"), str):
        byline_text = author_node["name"]

    author_link = next((l for l in p.links if l.get("rel") == "author"
                         or re.search(r"/author/|/about/|/team/", l.get("href", ""), re.I)), None)
    resolves = None
    if check_links and author_link and author_link["href"].startswith(("http://", "https://")):
        resolves = check_url(author_link["href"])

    policy = {key: any(any(k in (l.get("href", "") + l.get("text", "")).lower() for k in kws) for l in p.links)
              for key, kws in POLICY_KEYWORDS.items()}

    dates: dict[str, str | None] = {"published": None, "modified": None}
    if article:
        dates["published"] = article.get("datePublished")
        dates["modified"] = article.get("dateModified")
    if not dates["published"]:
        pm = re.search(r'property=["\']article:published_time["\']\s+content=["\']([^"\']+)', html, re.I)
        dates["published"] = pm.group(1) if pm else None
    if not dates["modified"]:
        mm = re.search(r'property=["\']article:modified_time["\']\s+content=["\']([^"\']+)', html, re.I)
        dates["modified"] = mm.group(1) if mm else None

    return {
        "source": src,
        "https": src.startswith("https://") if src.startswith(("http://", "https://")) else None,
        "jsonld_blocks_found": len(p.ld_blocks),
        "article_schema": {
            "present": article is not None,
            "type": type_of(article)[0] if article else None,
            "author_type": type_of(author_node)[0] if author_node else None,
            "author_is_person": bool(author_node and "Person" in type_of(author_node)),
        },
        "byline": {
            "text": byline_text,
            "looks_suspicious": bool(byline_text and SUSPICIOUS_BYLINE.match(byline_text.strip())),
        },
        "person_schema": {
            "present": bool(persons), "count": len(persons),
            "sameAs_count": len(same_as) if same_as else 0,
        },
        "review_schema": {
            "aggregate_rating_present": bool(agg), "review_present": bool(reviews),
            "note": "Presence only. This is NOT a fabrication check : verify these numbers against the VISIBLE page by hand (rule EEAT-001).",
        },
        "dates": dates,
        "policy_links": policy,
        "author_link": {
            "found": author_link is not None,
            "href": author_link["href"] if author_link else None,
            "resolves": resolves,
        },
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_links = "--no-link-check" not in sys.argv
    if not args:
        print(__doc__)
        return 2
    m = measure(args[0], check_links=check_links)
    js = json.dumps(m, indent=2, default=str)
    if len(args) > 1:
        open(args[1], "w").write(js)
        print(f"wrote {args[1]}")
    else:
        print(js)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
