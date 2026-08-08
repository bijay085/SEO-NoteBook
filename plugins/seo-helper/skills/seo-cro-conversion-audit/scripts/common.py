"""Shared helpers for the seo-cro-conversion-audit skill.

Pure standard library + BeautifulSoup (bs4/lxml). No paid APIs, no network,
fully deterministic. Every other script in this skill imports from here.

Design notes
------------
* Saved pages are named ``view-source_<url>.html`` and normally begin with a
  ``<!-- crawled: URL -->`` marker followed by RAW html. Some browser "save as"
  dumps are HTML-escaped instead (a view-source-of-view-source). ``load_page``
  un-escapes ONLY when the body is genuinely escaped, and it strips the standard
  "Mark of the Web" comment first so that comment can never trigger un-escaping
  (that false-positive once corrupted competitor signal extraction).
"""
from __future__ import annotations

import html as _html
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - dependency is documented in SKILL.md
    BeautifulSoup = None

__all__ = [
    "Finding", "load_page", "iter_pages", "host_of", "soup_of",
    "visible_text", "read_json", "write_json", "slugify",
]

_CRAWL_MARKER = re.compile(r"<!--\s*crawled:\s*(\S+)\s*-->", re.I)
_MOTW = re.compile(r"<!--\s*saved from url=\(\d+\).*?-->", re.I)


# --------------------------------------------------------------------------- #
# Page loading
# --------------------------------------------------------------------------- #
def load_page(path) -> tuple[str, str]:
    """Return ``(url, html)`` for a saved page file.

    The URL comes from the ``<!-- crawled: URL -->`` marker when present
    (reliable), else it is reconstructed from the filename.
    """
    raw = Path(path).read_text(encoding="utf-8", errors="ignore")
    m = _CRAWL_MARKER.search(raw[:4000])
    if m:
        url = m.group(1).strip()
        body = raw[m.end():]
    else:
        url = _url_from_filename(path)
        body = raw
    probe = _MOTW.sub("", body)            # MOTW comment must not skew the test
    if _looks_escaped(probe):
        body = _html.unescape(body)
    return url, body


def _looks_escaped(s: str) -> bool:
    """True only for a genuinely HTML-escaped view-source dump."""
    sample = s[:20000]
    lt = sample.count("<")
    esc = sample.count("&lt;")
    return esc > 20 and esc > lt * 5


def _url_from_filename(path) -> str:
    name = Path(path).stem
    name = re.sub(r"^view-source[_-]?", "", name, flags=re.I)
    name = re.sub(r"^https?[_:]+/*", "", name)
    parts = name.split("_")
    host = parts[0]
    rest = "/".join(p for p in parts[1:] if p)
    return f"https://{host}/{rest}".rstrip("/") + "/"


def iter_pages(pages_dir):
    """Yield ``(url, html, path)`` for every ``*.html`` in a directory."""
    for p in sorted(Path(pages_dir).glob("*.html")):
        url, body = load_page(p)
        yield url, body, p


# --------------------------------------------------------------------------- #
# HTML helpers
# --------------------------------------------------------------------------- #
def soup_of(html_text: str):
    if BeautifulSoup is None:
        raise RuntimeError(
            "BeautifulSoup (bs4) + lxml are required. Install: pip install beautifulsoup4 lxml"
        )
    return BeautifulSoup(html_text, "lxml")


def visible_text(html_text: str) -> str:
    soup = soup_of(html_text)
    for t in soup(["script", "style", "noscript", "template"]):
        t.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def host_of(url: str) -> str:
    try:
        netloc = urlparse(url if "://" in url else "http://" + url).netloc.lower()
    except Exception:
        netloc = ""
    netloc = netloc.split(":")[0]
    return netloc[4:] if netloc.startswith("www.") else netloc


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


# --------------------------------------------------------------------------- #
# JSON IO
# --------------------------------------------------------------------------- #
def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)


# --------------------------------------------------------------------------- #
# Finding model  (mirrors the findings.json rows the report consumes)
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    id: str
    severity: str = "INFO"      # CRITICAL | HIGH | MEDIUM | LOW | INFO
    area: str = ""              # CTA | Trust | Form | UI/UX | Coverage | Page | Behavioral
    title: str = ""
    detail: str = ""
    evidence: str = ""
    recommended_actions: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
