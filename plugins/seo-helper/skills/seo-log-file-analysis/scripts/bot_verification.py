"""Verified search-bot identification by official IP range.

A User-Agent string is trivially spoofed; the only trustworthy way to say
"this really was Googlebot" is to check the client IP against the ranges the
search engine publishes. This module owns that check.

Enhancement over the Colab analyzer: that version fetched the range files on
every run and swallowed every network error, so an offline run silently
degraded to "no verified bots" with no trace in the report. Here the ranges are
CACHED ON DISK (7-day TTL) and the per-source outcome is RETURNED, so the
report can state which sources were live, which came from cache, and which
failed — a verified-bot claim is never made on quietly-missing data.

Public API:
  load_networks(offline=False, cache_dir=None) -> (networks, sources)
  verified_bot_from_ip(ip)  -> (class, 'Name (verified IP)') | None
  source_report()           -> [{source, status, prefixes}]
  coverage_summary()        -> one-line honesty statement
"""
import ipaddress
import json
import os
import time
import urllib.request

CACHE_TTL_SECONDS = 7 * 24 * 3600
DEFAULT_CACHE_DIR = os.path.expanduser("<workspace>/.cache/seo-log-file-analysis")
CACHE_FILE = "bot_ip_ranges.json"

# (traffic class, agent label, official range file)
VERIFIED_BOT_IP_SOURCES = [
    ("search_bot",  "Googlebot",              "https://developers.google.com/search/apis/ipranges/googlebot.json"),
    ("search_bot",  "Google Common Crawler",  "https://developers.google.com/static/crawling/ipranges/common-crawlers.json"),
    ("search_bot",  "Google Special Crawler", "https://developers.google.com/static/crawling/ipranges/special-crawlers.json"),
    ("search_bot",  "Google User Fetcher",    "https://developers.google.com/static/crawling/ipranges/user-triggered-fetchers.json"),
    ("search_bot",  "Bingbot",                "https://www.bing.com/toolbox/bingbot.json"),
    ("search_bot",  "DuckDuckBot",            "https://duckduckgo.com/duckduckbot.json"),
    ("search_bot",  "Applebot",               "https://search.developer.apple.com/applebot.json"),
    ("search_bot",  "OAI-SearchBot",          "https://openai.com/searchbot.json"),
    ("generic_bot", "OpenAI GPTBot",          "https://openai.com/gptbot.json"),
    ("generic_bot", "ChatGPT-User",           "https://openai.com/chatgpt-user.json"),
    ("seo_tool",    "Ahrefsbot",              "https://api.ahrefs.com/v3/public/crawler-ip-ranges"),
]

# Yandex publishes no machine-readable range file; these are the documented
# announced blocks. Static fallback only — labelled as such in the report.
YANDEX_FALLBACK_RANGES = [
    "5.45.192.0/18", "5.255.192.0/18", "37.9.64.0/18", "37.140.128.0/18",
    "77.88.0.0/18", "84.201.128.0/18", "87.250.224.0/19", "93.158.128.0/18",
    "95.108.128.0/17", "100.43.64.0/19", "130.193.32.0/19", "141.8.128.0/18",
    "178.154.128.0/17", "199.21.96.0/22", "199.36.240.0/22", "213.180.192.0/19",
]

_NETWORKS = None          # [(cls, agent, ip_network)]
_SOURCES = []             # [{source, status, prefixes}]
_IP_CACHE = {}


def _iter_ip_prefixes(data):
    """Yield CIDR strings from any of the published range-file shapes."""
    if isinstance(data, dict):
        for key in ("prefixes", "ips"):
            for item in data.get(key, []) or []:
                if not isinstance(item, dict):
                    continue
                cidr = item.get("ipv4Prefix") or item.get("ipv6Prefix")
                ip = item.get("ip") or item.get("ip_address")
                if cidr:
                    yield cidr
                elif ip:
                    try:
                        addr = ipaddress.ip_address(ip)
                        yield f"{ip}/{32 if addr.version == 4 else 128}"
                    except ValueError:
                        continue
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                yield item
            elif isinstance(item, dict):
                cidr = (item.get("ipv4Prefix") or item.get("ipv6Prefix")
                        or item.get("prefix"))
                ip = item.get("ip") or item.get("ip_address")
                if cidr:
                    yield cidr
                elif ip:
                    try:
                        addr = ipaddress.ip_address(ip)
                        yield f"{ip}/{32 if addr.version == 4 else 128}"
                    except ValueError:
                        continue


def _cache_path(cache_dir):
    return os.path.join(cache_dir or DEFAULT_CACHE_DIR, CACHE_FILE)


def _read_cache(cache_dir):
    try:
        with open(_cache_path(cache_dir), "r", encoding="utf-8") as fh:
            blob = json.load(fh)
        stale = time.time() - float(blob.get("fetched_at", 0)) > CACHE_TTL_SECONDS
        return blob, stale
    except Exception:
        return None, False


def _write_cache(cache_dir, payload):
    path = _cache_path(cache_dir)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
    except Exception:
        pass                            # a cache miss must never fail a run


def load_networks(offline=False, cache_dir=None, timeout=6):
    """Build the verified-bot network table.

    Per source: fresh cache -> live fetch -> stale cache -> unavailable.
    Returns (networks, sources); `sources` records what actually happened so
    the deliverable can disclose it."""
    global _NETWORKS, _SOURCES
    if _NETWORKS is not None:
        return _NETWORKS, _SOURCES

    cached, stale = _read_cache(cache_dir)
    fresh = cached["ranges"] if (cached and not stale) else {}
    stale_ranges = cached["ranges"] if cached else {}

    ranges, sources = {}, []
    for cls, agent, url in VERIFIED_BOT_IP_SOURCES:
        key = f"{cls}|{agent}"
        if key in fresh:
            ranges[key] = fresh[key]
            sources.append({"source": agent, "status": "cache",
                            "prefixes": len(fresh[key])})
            continue
        if offline:
            if key in stale_ranges:
                ranges[key] = stale_ranges[key]
                sources.append({"source": agent, "status": "stale-cache",
                                "prefixes": len(stale_ranges[key])})
            else:
                sources.append({"source": agent, "status": "unavailable (offline)",
                                "prefixes": 0})
            continue
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cidrs = list(_iter_ip_prefixes(data))
            if not cidrs:
                raise ValueError("no prefixes in payload")
            ranges[key] = cidrs
            sources.append({"source": agent, "status": "live", "prefixes": len(cidrs)})
        except Exception as exc:
            if key in stale_ranges:
                ranges[key] = stale_ranges[key]
                sources.append({"source": agent,
                                "status": f"stale-cache ({exc.__class__.__name__})",
                                "prefixes": len(stale_ranges[key])})
            else:
                sources.append({"source": agent,
                                "status": f"FAILED ({exc.__class__.__name__})",
                                "prefixes": 0})

    if any(s["status"] == "live" for s in sources):
        _write_cache(cache_dir, {"fetched_at": time.time(), "ranges": ranges})

    networks = []
    for key, cidrs in ranges.items():
        cls, agent = key.split("|", 1)
        for cidr in cidrs:
            try:
                networks.append((cls, agent, ipaddress.ip_network(cidr)))
            except ValueError:
                continue
    for cidr in YANDEX_FALLBACK_RANGES:
        try:
            networks.append(("search_bot", "Yandexbot", ipaddress.ip_network(cidr)))
        except ValueError:
            continue
    sources.append({"source": "Yandexbot", "status": "static fallback list",
                    "prefixes": len(YANDEX_FALLBACK_RANGES)})

    _NETWORKS, _SOURCES = networks, sources
    return networks, sources


def verified_bot_from_ip(ip):
    """(class, 'Agent (verified IP)') when the IP sits in an official range."""
    ip = str(ip or "").strip()
    if not ip or ip == "-":
        return None
    if ip in _IP_CACHE:
        return _IP_CACHE[ip]
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        _IP_CACHE[ip] = None
        return None
    networks, _ = load_networks()
    for cls, agent, network in networks:
        if addr in network:
            result = (cls, f"{agent} (verified IP)")
            _IP_CACHE[ip] = result
            return result
    _IP_CACHE[ip] = None
    return None


def source_report():
    """What the verified-bot table was actually built from, for disclosure."""
    load_networks()
    return list(_SOURCES)


def coverage_summary():
    """One-line honesty statement about verified-bot coverage this run."""
    srcs = source_report()
    live = sum(1 for s in srcs if s["status"] == "live")
    cached = sum(1 for s in srcs if s["status"].startswith(("cache", "stale-cache")))
    failed = [s["source"] for s in srcs
              if s["status"].startswith(("FAILED", "unavailable"))]
    total_prefixes = sum(s["prefixes"] for s in srcs)
    msg = (f"Verified-bot IP table: {total_prefixes:,} prefixes from "
           f"{live} live + {cached} cached source(s).")
    if failed:
        msg += (f" UNAVAILABLE: {', '.join(failed)} — bots from those engines can "
                f"only be identified by User-Agent in this run.")
    return msg
