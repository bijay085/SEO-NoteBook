"""Traffic classification — who made the request, and what they asked for.

The taxonomy and every gate below carry over unchanged from the Colab analyzer
`seo_log_file_analyzer.py`, because that conditioning is the value:

  * VERIFIED IP WINS. If the IP sits in an official published range, that
    identification beats anything the User-Agent claims.
  * URL PURPOSE GATES "SUSPICIOUS". Admin polling (admin-ajax, wp-cron,
    heartbeat), the WP REST API and service workers look exactly like
    high-volume scraping. An IP whose traffic is >50% admin-like is a
    logged-in admin or a PWA — never flagged, whatever its volume or UA.
  * CHROME 200+ IS THE SPOOF SIGNAL, not Chrome 130+. Real stable Chrome is
    ~v137 in 2026 and v200 will not ship until ~2032, so 200 is the safe
    lower bound; the older 130+ rule flagged every modern human visitor.

Enhancement: the named-crawler table gains the current AI/LLM fetchers
(PerplexityBot, ClaudeBot, Amazonbot, meta-externalagent, Bytespider). They
are classed generic_bot, NOT search_bot, so they never inflate the
search-crawl-budget numbers.

Public API:
  classify_traffic(ua, ip, ip_hits, total_hits, ip_admin_share)
      -> (traffic_class, agent_name, is_automated)
  classify_content(url)     -> 'HTML'|'CSS'|'Image'|...
  url_purpose(url)          -> 'content'|'admin_polling'|'scanner_probe'|...
  evaluate_ua_modernity(ua) -> {is_real_browser, chrome_version, is_future}
"""
import re
from urllib.parse import urlparse

from bot_verification import verified_bot_from_ip

# ── the bot taxonomy ────────────────────────────────────────────────────────
# Ordered: the FIRST entry whose keywords all appear in the UA wins, so
# "Googlebot + Mobile" must precede plain "Googlebot".
NAMED_CRAWLERS = [
    ("Googlebot Smartphone",   ["Googlebot", "Mobile"]),
    ("Googlebot Desktop",      ["Googlebot"]),
    ("Googlebot Image",        ["Googlebot-Image"]),
    ("Googlebot Video",        ["Googlebot-Video"]),
    ("GoogleOther Image",      ["GoogleOther-Image"]),
    ("GoogleOther Video",      ["GoogleOther-Video"]),
    ("GoogleOther",            ["GoogleOther"]),
    ("Google StoreBot",        ["Storebot-Google"]),
    ("AdsBot Google Mobile",   ["AdsBot-Google-Mobile"]),
    ("AdsBot Google",          ["AdsBot-Google"]),
    ("Google Inspectiontool",  ["Google-InspectionTool"]),
    ("APIs Google",            ["APIs-Google"]),
    ("Mediapartners Google",   ["Mediapartners-Google"]),
    ("Google Safety",          ["Google-Safety"]),
    ("Bingbot",                ["bingbot"]),
    ("Bingbot",                ["msnbot"]),
    ("Bingbot",                ["BingPreview"]),
    ("Yandexbot",              ["YandexBot"]),
    ("Baiduspider",            ["Baiduspider"]),
    ("DuckDuckBot",            ["DuckDuckBot"]),
    ("Applebot",               ["Applebot"]),
    ("OAI-SearchBot",          ["OAI-SearchBot"]),
    ("GPTBot",                 ["GPTBot"]),
    ("ChatGPT-User",           ["ChatGPT-User"]),
    ("PerplexityBot",          ["PerplexityBot"]),
    ("ClaudeBot",              ["ClaudeBot"]),
    ("Claude-User",            ["Claude-User"]),
    ("Amazonbot",              ["Amazonbot"]),
    ("Meta AI",                ["meta-externalagent"]),
    ("Bytespider",             ["Bytespider"]),
    ("Semrushbot",             ["SemrushBot"]),
    ("Ahrefsbot",              ["AhrefsBot"]),
    ("Moz",                    ["rogerbot"]),
    ("Screaming Frog",         ["Screaming Frog"]),
    ("Majestic",               ["MJ12bot"]),
    ("Deepcrawl",              ["DeepCrawl"]),
    ("Sitebulb",               ["Sitebulb"]),
]

INFRA_PATTERNS = [
    ("WordPress Self-Ping",   lambda ua: "WordPress/" in ua),
    ("WP Cache Preloader",    lambda ua: ("seraph-accel" in ua
                                          or "wp-rocket" in ua.lower()
                                          or "wp_rocket" in ua.lower())),
    ("Hotjar Analytics",      lambda ua: "Hotjar" in ua),
    ("Cleantalk",             lambda ua: "Cleantalk" in ua),
    ("StatusCake Monitor",    lambda ua: "StatusCake" in ua),
    ("Uptime Robot",          lambda ua: "UptimeRobot" in ua),
    ("Pingdom",               lambda ua: "Pingdom" in ua),
    ("GTmetrix",              lambda ua: "GTmetrix" in ua),
    ("Datadog Synthetics",    lambda ua: "Datadog" in ua),
    ("Generic Monitoring",    lambda ua: any(k in ua.lower() for k in
                                             ("monitor", "healthcheck",
                                              "health-check", "pingcheck"))),
]

GENERIC_BOT_SIGNALS = [
    "bot", "crawl", "spider", "scrape", "fetch", "check", "scan",
    "validator", "indexer", "harvest", "wget", "curl", "python-requests",
    "go-http-client", "axios", "libwww", "java/", "okhttp", "httpx",
]

# Real stable Chrome in 2026 is ~v137. A 130+ rule made every modern human look
# suspicious; Chrome 200 won't ship until ~2032, so this is the safe bound.
FUTURE_CHROME_RE = re.compile(r"Chrome/([2-9]\d{2}|\d{4,})\.")

# URL purpose taxonomy — drives the evidence gate. Admin / polling / service
# worker URLs look like high-volume scraping but are legitimate logged-in
# admin or PWA traffic and must never be flagged.
URL_PURPOSE_RULES = [
    ("admin_polling",   re.compile(r"/wp-admin/admin-ajax\.php|/wp-cron\.php|seraph_accel|wc-analytics/imports|wc-admin/options|heartbeat", re.I)),
    ("admin_ui",        re.compile(r"/wp-admin/(load-scripts|load-styles|edit\.php|post(-new|)\.php|admin\.php|options-|themes\.php|plugins\.php|users\.php|tools\.php|profile\.php|upload\.php|index\.php)", re.I)),
    ("rest_api",        re.compile(r"/wp-json/", re.I)),
    ("service_worker",  re.compile(r"(service-worker|[-/]sw[-.]|/sw\.js|superpwa-sw|onesignal)", re.I)),
    ("account_area",    re.compile(r"/(my-account|account|customer|checkout|cart|login|logout|signin|signup|register)/?", re.I)),
    ("scanner_probe",   re.compile(r"/\.env|/\.git|/wp-config|/phpinfo|/\.DS_Store|/backup|debug\.log|/\.svn|/wp-login\.php|/xmlrpc\.php|/(adminer|phpmyadmin|mysql)", re.I)),
    ("static_asset",    re.compile(r"\.(css|js|jpg|jpeg|png|gif|webp|svg|ico|woff2?|ttf|eot|map)(\?|$)", re.I)),
    ("feed_or_sitemap", re.compile(r"(/feed/?|/rss|sitemap[^/]*\.xml|sitemap_index)", re.I)),
    ("robots",          re.compile(r"/robots\.txt$", re.I)),
]

TRACKING_PARAM_RE = re.compile(
    r"(?:^|[?&])(utm_[a-z]+|fbclid|gclid|msclkid|mc_cid|mc_eid|yclid|_ga|_gl)=", re.I)
CACHEBUST_PARAM_RE = re.compile(r"(?:^|[?&])(_|v|ver|t|cb|r|nocache)=\d+", re.I)

ADMIN_LIKE_PURPOSES = {"admin_polling", "admin_ui", "rest_api", "service_worker"}
SEO_TOOL_NAMES = {"Semrushbot", "Ahrefsbot", "Moz", "Screaming Frog",
                  "Majestic", "Deepcrawl", "Sitebulb"}
# AI / LLM fetchers are automated but are NOT search-engine crawl budget.
GENERIC_TOOL_NAMES = {"GPTBot", "ChatGPT-User", "PerplexityBot", "ClaudeBot",
                      "Claude-User", "Amazonbot", "Meta AI", "Bytespider"}

CLASS_LABELS = {
    "search_bot":  "Search Bots",
    "seo_tool":    "SEO Crawlers",
    "infra":       "Infrastructure",
    "generic_bot": "Generic / AI Bots",
    "suspicious":  "Suspicious",
    "human":       "Human",
}

_EXT_MAP = {
    "html": "HTML", "htm": "HTML", "php": "HTML", "asp": "HTML", "aspx": "HTML",
    "css": "CSS", "js": "JavaScript",
    "jpg": "Image", "jpeg": "Image", "png": "Image", "gif": "Image",
    "webp": "Image", "ico": "Image", "svg": "SVG",
    "woff": "Font", "woff2": "Font", "ttf": "Font", "eot": "Font",
    "pdf": "PDF", "xml": "XML", "json": "JSON", "txt": "Text",
}


def classify_traffic(ua, ip, ip_hit_count, total_hits, ip_admin_url_share=0.0):
    """Classify one request.

    ip_admin_url_share = the fraction of THIS IP's requests that hit
    admin/polling/REST/service-worker URLs. A high share proves the IP is a
    logged-in admin or a PWA and must NEVER be flagged as suspicious,
    regardless of hit count or UA."""
    ip_agent = verified_bot_from_ip(ip)
    if ip_agent:
        return ip_agent[0], ip_agent[1], True
    if not ua or ua == "-":
        return "generic_bot", "No User-Agent", True
    ua_lower = ua.lower()
    for name, keywords in NAMED_CRAWLERS:
        if all(kw.lower() in ua_lower for kw in keywords):
            if name in SEO_TOOL_NAMES:
                cls = "seo_tool"
            elif name in GENERIC_TOOL_NAMES:
                cls = "generic_bot"
            else:
                cls = "search_bot"
            return cls, name, True
    for name, fn in INFRA_PATTERNS:
        if fn(ua):
            return "infra", name, True
    if any(sig in ua_lower for sig in GENERIC_BOT_SIGNALS):
        return "generic_bot", ua[:60], True

    # Verification gate: a dominant admin/polling URL pattern means a real
    # logged-in user — never suspicious, whatever the UA or the volume.
    if ip_admin_url_share > 0.5:
        return "human", "Logged-in Admin / Session", False

    if FUTURE_CHROME_RE.search(ua):
        share = ip_hit_count / max(total_hits, 1)
        label = ("Mass Scraper (impossible UA)" if share > 0.10
                 else "Suspicious UA (Chrome 200+, not yet released)")
        return "suspicious", label, True
    # High-volume rule retained, but requires content-page dominance so admin
    # polling can never trip it.
    if (ip_hit_count > 500 and ip_hit_count / max(total_hits, 1) > 0.10
            and ip_admin_url_share < 0.3):
        return "suspicious", f"High-volume IP, content-dominated ({ip_hit_count} hits)", True
    return "human", "Human", False


def classify_content(url):
    path = urlparse(url).path.lower()
    last = path.split("/")[-1]
    ext = last.rsplit(".", 1)[-1] if "." in last else ""
    if ext in _EXT_MAP:
        return _EXT_MAP[ext]
    if "sitemap" in path:
        return "XML"
    if path == "/robots.txt":
        return "Text"
    if path.endswith("/") or ext == "":
        return "HTML"
    return "Other"


def url_purpose(url):
    """Categorise a URL by functional purpose. Drives evidence-gated detection —
    admin/cron/service-worker polling looks like scraping but is normal."""
    if not url:
        return "unknown"
    u = str(url)
    for label, rx in URL_PURPOSE_RULES:
        if rx.search(u):
            return label
    if TRACKING_PARAM_RE.search(u):
        return "tracked_content"
    return "content"


def evaluate_ua_modernity(ua):
    """Inspect a UA. Real modern browsers are normal, NOT suspicious."""
    if not ua or ua == "-":
        return {"is_real_browser": False, "chrome_version": None, "is_future": False}
    m = re.search(r"Chrome/(\d+)\.", ua)
    chrome_v = int(m.group(1)) if m else None
    is_real = bool(re.search(r"Mozilla/5\.0.*AppleWebKit", ua, re.I))
    return {"is_real_browser": is_real, "chrome_version": chrome_v,
            "is_future": chrome_v is not None and chrome_v >= 200}


# Search-engine attribution for the bot-crawl detail tab.
SE_BOT_MAP = {
    "Googlebot Smartphone": "Google", "Googlebot Desktop": "Google",
    "Googlebot Image": "Google", "Googlebot Video": "Google",
    "GoogleOther": "Google", "GoogleOther Image": "Google",
    "GoogleOther Video": "Google", "Google StoreBot": "Google",
    "AdsBot Google": "Google", "AdsBot Google Mobile": "Google",
    "Google Inspectiontool": "Google", "APIs Google": "Google",
    "Mediapartners Google": "Google", "Google Safety": "Google",
    "Googlebot (verified IP)": "Google",
    "Google Common Crawler (verified IP)": "Google",
    "Google Special Crawler (verified IP)": "Google",
    "Google User Fetcher (verified IP)": "Google",
    "Bingbot": "Bing", "Bingbot (verified IP)": "Bing",
    "Yandexbot": "Yandex", "Yandexbot (verified IP)": "Yandex",
    "Baiduspider": "Baidu",
    "DuckDuckBot": "DuckDuckGo", "DuckDuckBot (verified IP)": "DuckDuckGo",
    "Applebot": "Apple", "Applebot (verified IP)": "Apple",
    "OAI-SearchBot": "OpenAI Search", "OAI-SearchBot (verified IP)": "OpenAI Search",
}
