"""Health scorecard — the ten Green/Yellow/Red gauges.

Thresholds carried over unchanged from `seo_log_file_analyzer.py` (calc_health).
They are the "is this normal?" reference the findings are read against: a 4%
404 rate is Yellow, not a crisis; ANY sustained 5xx above 0.5% is Red.

calc_health(agg, findings) -> [(metric, value, score, healthy, watch, urgent)]
"""

METRIC_NOTES = {
    "404 Error Rate": "Share of all requests answered 404.",
    "301 Redirect Rate": "Share answered 301 — every one is a doubled crawl slot.",
    "5xx Error Rate": "Any sustained 5xx is a crawl-halt risk, so the bar is 0%.",
    "Robots.txt": "robots.txt should answer 200/304; a 3xx is reachable but misconfigured, a 4xx/5xx halts crawling.",
    "Sitemap": "Sitemap should answer 200/304 — it is the discovery path.",
    "Googlebot Share": "Googlebot as a share of SEARCH-ENGINE traffic (not of all bots).",
    "Static Crawl Ratio": "Bot requests spent on CSS/JS/images instead of HTML.",
    "Suspicious Traffic": "Share classified suspicious after the URL-purpose gate.",
    "Infra Traffic": "Self-pings, cache preloaders and uptime monitors.",
    "P1 Issues": "Count of P1 - Critical findings.",
}


def _score(value, green_max, yellow_max, higher_is_better=False):
    if higher_is_better:
        return ("Green" if value >= green_max
                else ("Yellow" if value >= yellow_max else "Red"))
    return ("Green" if value <= green_max
            else ("Yellow" if value <= yellow_max else "Red"))


def calc_health(agg, findings):
    total = agg["total"]
    if total == 0:
        return []
    automated = max(agg["automated_total"], 1)
    status_counts = agg["status_counts"]
    class_counts = agg["class_counts"]

    r404 = status_counts.get(404, 0) / total * 100
    r301 = status_counts.get(301, 0) / total * 100
    r5xx = sum(n for s, n in status_counts.items() if s >= 500) / total * 100
    static = sum(agg["bot_content_counts"].get(t, 0)
                 for t in ("CSS", "JavaScript", "Font", "Image", "SVG")) / automated * 100
    scrape_pct = class_counts.get("suspicious", 0) / total * 100
    infra_pct = class_counts.get("infra", 0) / total * 100

    # Googlebot share is measured against SEARCH-ENGINE traffic, not against all
    # automated traffic. Dividing by "everything automated" folds in uptime
    # monitors, WP self-pings, curl and Go clients, so a site with a chatty
    # monitor scores Red however healthily Google crawls it. Measured on real
    # logs this read 3.8% (Red) while the same site's Googlebot share of search
    # traffic was 34% (healthy) — the scorecard was contradicting the findings.
    # This is the denominator detect_issues already uses.
    search_total = class_counts.get("search_bot", 0)
    gb_denom = search_total if search_total >= 20 else automated
    gb = agg["google_total"] / max(gb_denom, 1) * 100

    # A file that was never requested cannot be broken — absent means OK, and
    # the findings report that absence separately rather than scoring an
    # untested file Red. Three states, because they mean different things: a
    # 4xx/5xx breaks crawling (Red); a 3xx is reachable but misconfigured,
    # usually an http->https or www redirect (Yellow, not a crawl halt).
    def _file_state(statuses):
        if not statuses:
            return "OK", "Green"
        if any(s >= 400 for s in statuses):
            return "ERROR", "Red"
        if any(300 <= s < 400 for s in statuses):
            return "REDIRECT", "Yellow"
        return "OK", "Green"

    rob_val, rob_score = _file_state(agg["robots_statuses"])
    sit_val, sit_score = _file_state(agg["sitemap_statuses"])

    p1c = sum(1 for f in findings if f["urgency"] == "P1 - Critical")

    return [
        ("404 Error Rate",     f"{r404:.1f}%",       _score(r404, 1, 5),        "<1%",  "1-5%",   ">5%"),
        ("301 Redirect Rate",  f"{r301:.1f}%",       _score(r301, 3, 10),       "<3%",  "3-10%",  ">10%"),
        ("5xx Error Rate",     f"{r5xx:.1f}%",       _score(r5xx, 0, 0.5),      "0%",   "<0.5%",  ">0.5%"),
        ("Robots.txt",         rob_val, rob_score, "200/304", "3xx redirect", "Any 4xx/5xx"),
        ("Sitemap",            sit_val, sit_score, "200/304", "3xx redirect", "Any 4xx/5xx"),
        ("Googlebot Share",    f"{gb:.1f}%",         _score(gb, 50, 20, True),  ">50%", "20-50%", "<20%"),
        ("Static Crawl Ratio", f"{static:.1f}%",     _score(static, 20, 35),    "<20%", "20-35%", ">35%"),
        ("Suspicious Traffic", f"{scrape_pct:.1f}%", _score(scrape_pct, 1, 10), "<1%",  "1-10%",  ">10%"),
        ("Infra Traffic",      f"{infra_pct:.1f}%",  _score(infra_pct, 10, 30), "<10%", "10-30%", ">30%"),
        ("P1 Issues",          str(p1c),             _score(p1c, 0, 2),         "0",    "1-2",    ">2"),
    ]
