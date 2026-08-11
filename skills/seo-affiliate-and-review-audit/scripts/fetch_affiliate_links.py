"""
fetch_affiliate_links.py : deterministic engine for the seo-affiliate-and-review-audit skill.

For each target page it:
  1. fetches the HTML (requests; ScrapingBee render fallback when blocked / JS-rendered),
  2. extracts every outbound <a>, classifies the affiliate network, records the rel
     string and where the link sits (main content vs nav/footer/header chrome),
  3. HTTP-checks each affiliate destination (follows redirects -> final_url + status),
  4. parses JSON-LD and walks it RECURSIVELY for Review / Product / AggregateRating types
     (a flat top-level parse misses nested @graph nodes -- the FWD schema bug).

Outputs (to config.output_dir):
  affiliate_links.json one row per monetized link (page/anchor/destination/final_url/
                        network/http_status/rel/placement)
  review_schema.json per-page JSON-LD @type inventory
  fetch_summary.json counts + which pages used the render fallback / failed

Credentials: loaded from project `.env` / host environment variables at runtime with a stdlib parser. python-dotenv is
NOT installed and must not be imported. Only SCRAPINGBEE_KEY is used here, and only inside
a request -- no secret is written to any output.

Usage: python fetch_affiliate_links.py config.json
"""
import json
import os
import re
import sys
import time
from urllib.parse import urlparse, parse_qs, urljoin
import xml.etree.ElementTree as ET

try:
    import requests
except ImportError:
    sys.exit("requests is required: pip install requests")
try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("beautifulsoup4 is required: pip install beautifulsoup4")

UA = "Mozilla/5.0 (compatible; SEO-AffiliateAudit/1.0)"
FIELDS = ["page_url", "anchor", "destination", "final_url",
          "network", "http_status", "rel", "placement"]


def load_env(path="project `.env` / host environment variables"):
    """Minimal .env reader (no python-dotenv dependency)."""
    env = {}
    p = os.path.expanduser(path)
    if not os.path.isfile(p):
        return env
    with open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def read_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get(url, env, render=False, timeout=25):
    """Fetch a URL; when render=True route via ScrapingBee (SCRAPINGBEE_KEY)."""
    key = env.get("SCRAPINGBEE_KEY")
    if render and key:
        return requests.get(
            "https://app.scrapingbee.com/api/v1/",
            params={"api_key": key, "url": url, "render_js": "true"},
            timeout=timeout,
        )
    return requests.get(url, headers={"User-Agent": UA},
                        timeout=timeout, allow_redirects=True)


def fetch_html(url, env, use_bee):
    """Return (html, final_url, status, used_render); ScrapingBee fallback on block/error."""
    try:
        r = get(url, env, render=False)
        if r.status_code in (403, 429, 503) and use_bee and env.get("SCRAPINGBEE_KEY"):
            r = get(url, env, render=True)
            return r.text, str(r.url), r.status_code, True
        return r.text, str(r.url), r.status_code, False
    except requests.RequestException:
        if use_bee and env.get("SCRAPINGBEE_KEY"):
            try:
                r = get(url, env, render=True)
                return r.text, str(r.url), r.status_code, True
            except requests.RequestException:
                pass
        return "", url, None, False


def host_of(url):
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def classify_network(href, networks, amazon_tag_param):
    """Return the affiliate network name for a href, or None if it is not monetized."""
    host = host_of(href)
    if not host:
        return None
    for name, hosts in networks.items():
        for h in hosts:
            h = h.lower().lstrip("*.")
            if host == h or host.endswith("." + h):
                return name
    qs = parse_qs(urlparse(href).query)
    if amazon_tag_param and amazon_tag_param in qs and "amazon" in networks:
        return "amazon"
    return None


def placement_of(a):
    """Is the link in nav/header/footer chrome, or in the main content?"""
    for parent in a.parents:
        name = getattr(parent, "name", None)
        if name in ("nav", "header", "footer"):
            return name
        get_attr = getattr(parent, "get", None)
        cls = " ".join(parent.get("class", [])) if callable(get_attr) else ""
        if cls and re.search(r"\b(nav|header|footer|menu|sidebar|widget)\b", cls, re.I):
            return "chrome"
    return "main"


def check_destination(url, seen, timeout=20):
    """HEAD (GET fallback) an affiliate destination; follow redirects. Cache by URL."""
    if url in seen:
        return seen[url]
    status, final = None, url
    try:
        r = requests.head(url, headers={"User-Agent": UA},
                          timeout=timeout, allow_redirects=True)
        if r.status_code == 405 or r.status_code >= 400:
            r = requests.get(url, headers={"User-Agent": UA},
                             timeout=timeout, allow_redirects=True, stream=True)
        status, final = r.status_code, str(r.url)
    except requests.RequestException:
        status, final = None, url
    seen[url] = (status, final)
    return status, final


def walk_types(node, out):
    """Recursively collect @type values from a JSON-LD node (handles @graph nesting)."""
    if isinstance(node, dict):
        t = node.get("@type")
        if isinstance(t, str):
            out.add(t)
        elif isinstance(t, list):
            out.update(x for x in t if isinstance(x, str))
        for v in node.values():
            walk_types(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_types(v, out)


def parse_jsonld(soup):
    types = set()
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text() or ""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        walk_types(data, types)
    return sorted(types)


def discover_pages(cfg, env):
    """review_pages if given, else crawl the sitemap (one index level deep)."""
    pages = list(cfg.get("inputs", {}).get("review_pages") or [])
    if pages:
        return pages
    sm = cfg.get("inputs", {}).get("sitemap")
    if not sm:
        return []
    html, _, _, _ = fetch_html(sm, env, use_bee=False)
    try:
        root = ET.fromstring(html)
    except ET.ParseError:
        return []
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    for loc in root.findall(".//s:sitemap/s:loc", ns):
        if not loc.text:
            continue
        child, _, _, _ = fetch_html(loc.text.strip(), env, use_bee=False)
        try:
            croot = ET.fromstring(child)
        except ET.ParseError:
            continue
        urls += [u.text.strip() for u in croot.findall(".//s:url/s:loc", ns) if u.text]
    urls += [u.text.strip() for u in root.findall(".//s:url/s:loc", ns) if u.text]
    return urls


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python fetch_affiliate_links.py config.json")
    cfg = read_config(sys.argv[1])
    env = load_env(cfg.get("env_file", "project `.env` / host environment variables"))
    tax = cfg.get("taxonomy", {})
    networks = tax.get("affiliate_networks", {})
    amazon_tag = tax.get("amazon_tag_param", "tag")
    use_bee = bool(cfg.get("apis", {}).get("scrapingbee_fallback")) and bool(env.get("SCRAPINGBEE_KEY"))
    out_dir = os.path.expanduser(cfg.get("output_dir", "./Affiliate-Review-Audit/"))
    os.makedirs(out_dir, exist_ok=True)

    pages = discover_pages(cfg, env)
    rows, schema_rows = [], []
    summary = {"pages": 0, "rendered": 0, "failed": [], "affiliate_links": 0}
    dest_cache = {}

    for url in pages:
        html, final_url, status, rendered = fetch_html(url, env, use_bee)
        summary["pages"] += 1
        if rendered:
            summary["rendered"] += 1
        if not html or (status and status >= 400):
            summary["failed"].append({"page": url, "status": status})
            continue
        soup = BeautifulSoup(html, "lxml")
        schema_rows.append({"page_url": url, "types": parse_jsonld(soup)})
        for a in soup.find_all("a", href=True):
            raw_href = a.get("href")
            if not isinstance(raw_href, str):
                continue
            href = urljoin(final_url, raw_href.strip())
            net = classify_network(href, networks, amazon_tag)
            if not net:
                continue # only inventory monetized links
            st, fin = check_destination(href, dest_cache)
            rel_attr = a.get("rel")
            if isinstance(rel_attr, list):
                rel = " ".join(str(x) for x in rel_attr)
            elif isinstance(rel_attr, str):
                rel = rel_attr
            else:
                rel = ""
            rows.append({
                "page_url": url,
                "anchor": a.get_text(" ", strip=True)[:120],
                "destination": href,
                "final_url": fin,
                "network": net,
                "http_status": st,
                "rel": rel,
                "placement": placement_of(a),
            })
            time.sleep(0.15) # be gentle on destinations

    summary["affiliate_links"] = len(rows)
    for fname, payload in (
        ("affiliate_links.json", rows),
        ("review_schema.json", schema_rows),
        ("fetch_summary.json", summary),
    ):
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    print("[affiliate-audit] pages=%d rendered=%d affiliate_links=%d failed=%d"
          % (summary["pages"], summary["rendered"], summary["affiliate_links"], len(summary["failed"])))
    print("[affiliate-audit] wrote affiliate_links.json / review_schema.json / fetch_summary.json to %s" % out_dir)


if __name__ == "__main__":
    main()
