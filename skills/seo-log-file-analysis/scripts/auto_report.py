"""Build report sections straight from analysis.json : no authoring step.

WHY THIS EXISTS: the XLSX got its measured content from build_data_tabs.py while
the HTML rendered only `report_data.REPORT`, so an engine-only run produced a
complete workbook and an EMPTY html file. Same facts, one format silently
missing them. This module is the HTML's equivalent path, so both formats carry
the same content and differ only in presentation: the XLSX is a filterable
grid, the HTML a narrative of Issue · Evidence · Solution · Execution cards.

Every field the engine computes survives the mapping:
    detail, evidence, root_cause, impact -> the card's evidence block
    action -> solution (the literal fix)
    verify -> execution (how to prove it)
    effort, urgency -> effort, priority, severity

Authored sections from report_data.py are LAYERED ON TOP: anything Claude has
written for a section id replaces the auto-generated one, so the interpretation
upgrade never fights the measured baseline.

build_report(analysis, authored=None) -> report dict for report_kit.render_*
"""

MAX_PER_SECTION = 25 # findings rendered per section; the rest are counted,
                          # never silently dropped : the note says how many.

SEV_FROM_URGENCY = {
    "P1 - Critical": "critical",
    "P2 - High": "high",
    "P3 - Monitor": "medium",
}
PRIORITY_FROM_URGENCY = {
    "P1 - Critical": "P0",
    "P2 - High": "P1",
    "P3 - Monitor": "P2",
}

# engine category -> (section id, title, intro)
CATEGORY_SECTIONS = [
    ("HTTP Errors", "errors", "1 · HTTP Errors (4xx / 5xx)",
     "Errors crawlers actually received. A status Googlebot saw is an indexing "
     "event; the same status seen only by humans is link hygiene : each finding's "
     "evidence line says which."),
    ("Redirects", "redirects", "2 · Redirects & Chains",
     "301s still being crawled (stale internal links), 302s on content URLs, and "
     "multi-hop chains. Auth and checkout 302s are excluded : those are correct."),
    ("Crawl Budget", "budget", "3 · Crawl Budget Waste",
     "Where crawl was spent instead of on money pages: backend endpoints, "
     "parameter explosion, static assets, taxonomy archives, internal traffic."),
    ("Indexability", "indexability", "4 · Indexability & Discovery",
     "robots.txt and sitemap health, trailing-slash duplicates, the mobile-first "
     "crawl split, and overall Googlebot presence."),
    ("Performance", "performance", "5 · Performance",
     "Response weight as the server actually served it : bytes on the wire, not a "
     "lab estimate."),
    ("Security", "security", "6 · Security : File Exposure & Probing",
     "Sensitive files served (200 = active exposure, rotate credentials now) or "
     "probed (403/404 = reconnaissance)."),
    ("Security / Spam", "spam", "7 · Suspicious Traffic",
     "High-volume IPs that survived the admin/polling gate. Logged-in admin and "
     "PWA traffic is deliberately excluded : it is not scraping."),
]


def _finding(f):
    """Engine finding -> report_kit finding, losing nothing."""
    evidence = str(f.get("detail", "")).strip()
    if f.get("evidence"):
        evidence += f"\n\nVerified: {f['evidence']}"
    if f.get("root_cause"):
        evidence += f"\n\nRoot cause: {f['root_cause']}"
    if f.get("impact"):
        evidence += f"\n\nBusiness impact: {f['impact']}"
    scope = f.get("url") or ""
    head = (f"[{f.get('confidence', '?')} confidence · {f.get('hits', 0):,} hits · "
            f"status {f.get('status_code', '?')} · segment {f.get('segment', '?')}]")
    return {
        "issue": f"{f.get('issue', '')} : {scope}" if scope else f.get("issue", ""),
        "sev": SEV_FROM_URGENCY.get(f.get("urgency", ""), "medium"),
        "evidence": f"{head}\n\n{evidence}",
        "solution": f.get("action", ""),
        "execution": f.get("verify", ""),
        "effort": f.get("effort", ""),
        "priority": PRIORITY_FROM_URGENCY.get(f.get("urgency", ""), "P2"),
    }


def _summary_section(a):
    m = a.get("meta", {})
    dr = m.get("date_range", {})
    counts = {}
    for f in a.get("findings", []):
        counts[f["urgency"]] = counts.get(f["urgency"], 0) + 1
    intro = (
        f"{m.get('total_requests', 0):,} requests across "
        f"{m.get('unique_urls', 0):,} unique URLs, {dr.get('start', '?')} to "
        f"{dr.get('end', '?')} ({dr.get('span_hours', '?')}h). Parse rate "
        f"{m.get('parse_rate_pct', 0)}% of {m.get('lines_read', 0):,} lines read. "
        f"{len(a.get('findings', []))} findings: "
        f"P1 {counts.get('P1 - Critical', 0)} · P2 {counts.get('P2 - High', 0)} · "
        f"P3 {counts.get('P3 - Monitor', 0)}. "
        f"{m.get('verified_bot_coverage', '')} {dr.get('timezone_note', '')}"
    )
    return {
        "id": "summary", "title": "0 · Crawl Summary", "intro": intro,
        "chart": {"type": "hbars", "title": "Requests by traffic segment",
                  "data": [[s["segment"], s["requests"]] for s in a.get("segments", [])]},
        "table": {"cols": ["Metric", "Value", "Verdict", "Healthy", "Watch", "Urgent"],
                  "rows": [[h["metric"], h["value"], h["score"], h["healthy"],
                            h["watch"], h["urgent"]] for h in a.get("health", [])]},
        "findings": [],
    }


def _traffic_section(a):
    """Bot identification : who made the requests, and how we know."""
    agents = a.get("agents", [])
    if not agents:
        return None
    verified = sum(1 for x in agents if "(verified IP)" in x["agent"])
    return {
        "id": "traffic", "title": "A · Traffic & Bot Identification",
        "intro": (f"Top {len(agents)} agents by volume. {verified} of them identified "
                  f"by OFFICIAL IP RANGE rather than by User-Agent : a UA string is "
                  f"free text and proves nothing. "
                  f"{a.get('meta', {}).get('verified_bot_coverage', '')}"),
        "table": {"cols": ["Agent", "Class", "Requests", "% of Total",
                           "Unique URLs", "Top Status"],
                  "rows": [[x["agent"], x["class"], f'{x["requests"]:,}',
                            f'{x["pct"]}%', x["unique_urls"], x["top_status"]]
                           for x in agents]},
        "findings": [],
    }


def _crawl_section(a):
    """What search engines actually fetched."""
    rows = a.get("bot_crawl", [])[:40]
    if not rows:
        return None
    intro = "The URLs search-engine crawlers actually requested, by volume."
    trend = a.get("crawl_trend", [])
    if trend:
        intro += (" Daily totals: "
                  + ", ".join(f'{t["date"]} = {t["total"]:,}' for t in trend) + ".")
    return {
        "id": "crawl", "title": "B · Search-Engine Crawl Detail", "intro": intro,
        "table": {"cols": ["URL", "Engine", "Bot", "Hits", "Status", "Type",
                           "Avg Bytes", "Last Seen"],
                  "rows": [[r["url"], r["search_engine"], r["bot"], r["hits"],
                            r["status"], r["content_type"], f'{r["avg_bytes"]:,}',
                            r["last_seen"]] for r in rows]},
        "findings": [],
    }


def _urls_section(a):
    rows = a.get("url_detail", [])[:40]
    if not rows:
        return None
    return {
        "id": "urls", "title": "C · Most-Requested URLs",
        "intro": ("Top 40 by request volume, split by who asked. The full list is in "
                  "the URL Detail tab of the workbook."),
        "table": {"cols": ["URL", "Hits", "Search Bot", "Infra", "Suspicious",
                           "Human", "Status", "Avg Bytes"],
                  "rows": [[r["url"], r["total_hits"], r["search_bot"], r["infra"],
                            r["suspicious"], r["human"], r["status"],
                            f'{r["avg_bytes"]:,}'] for r in rows]},
        "findings": [],
    }


def _coverage_section(a):
    cross = a.get("crossref") or {}
    if not cross:
        return None
    rows = []
    if cross.get("sitemap"):
        c = cross["sitemap"]
        rows.append(["Sitemap", f'{c["never_crawled"]} of {c["sitemap_urls"]} URLs '
                                f'never crawled in this window', c["note"]])
        rows += [["Sitemap", "Never crawled", u] for u in c.get("sample", [])[:25]]
    if cross.get("gsc"):
        c = cross["gsc"]
        rows.append(["GSC", f'{c["impressions_but_no_crawl"]} of {c["gsc_pages"]} pages '
                            f'have impressions but no crawl', c["note"]])
        rows += [["GSC", f'{s["impressions"]} impressions, no crawl', s["url"]]
                 for s in c.get("sample", [])[:25]]
    return {
        "id": "coverage", "title": "D · Crawl Coverage (Sitemap / GSC)",
        "intro": ("What the log does NOT contain. A log proves presence, never "
                  "absence : every row here is true for this window only."),
        "table": {"cols": ["Source", "Finding", "Detail / URL"], "rows": rows},
        "findings": [],
    }


def _period_label(dr):
    start, end = (dr.get("start") or "")[:10], (dr.get("end") or "")[:10]
    if start and end:
        return start if start == end else f"{start} to {end}"
    return ""


def build_report(analysis, authored=None):
    """analysis.json (+ optional authored REPORT) -> a report_kit report dict."""
    m = analysis.get("meta", {})
    by_cat = {}
    for f in analysis.get("findings", []):
        by_cat.setdefault(f["category"], []).append(f)

    sections = [_summary_section(analysis)]
    for cat, sid, title, intro in CATEGORY_SECTIONS:
        items = by_cat.get(cat) or []
        if not items:
            continue
        note = ""
        if len(items) > MAX_PER_SECTION:
            # Never truncate silently : a capped section that does not say so
            # reads as "that is all of them".
            note = (f" Showing the {MAX_PER_SECTION} highest-volume of {len(items)} "
                    f"findings in this category; all {len(items)} are in the Issue "
                    f"Analysis tab of the workbook and in analysis.json.")
        sections.append({
            "id": sid, "title": title, "intro": intro + note,
            "findings": [_finding(f) for f in items[:MAX_PER_SECTION]],
        })

    for builder in (_traffic_section, _crawl_section, _urls_section, _coverage_section):
        sec = builder(analysis)
        if sec:
            sections.append(sec)

    # Authored content wins on any section id it defines, and appends new ones.
    if authored:
        by_id = {s["id"]: s for s in sections}
        order = [s["id"] for s in sections]
        for s in authored.get("sections") or []:
            if s["id"] in by_id:
                merged = dict(by_id[s["id"]])
                merged.update({k: v for k, v in s.items() if v})
                by_id[s["id"]] = merged
            else:
                by_id[s["id"]] = s
                order.append(s["id"])
        sections = [by_id[i] for i in order]

    def authored_val(key):
        """An unfilled ‹placeholder› is not a value : fall through to measured
        data, or the deliverable ships as `Client_Period_...`."""
        v = str((authored or {}).get(key) or "").strip()
        return "" if (not v or "‹" in v or "›" in v) else v

    base = dict(authored or {})
    base.update({
        "title": authored_val("title") or "Log-File Analysis",
        "client": authored_val("client") or m.get("site") or "Client",
        "period": authored_val("period") or _period_label(m.get("date_range", {})),
        "subtitle": (authored_val("subtitle")
                     or "What crawlers and visitors actually did on the server : "
                        "measured from raw access logs, with an executable fix for "
                        "each finding."),
        "sections": sections,
    })
    return base
