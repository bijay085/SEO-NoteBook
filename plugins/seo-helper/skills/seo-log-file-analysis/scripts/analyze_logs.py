#!/usr/bin/env python3
"""Log-file analysis orchestrator — parse, classify, detect, emit the facts.

This is the deterministic half of the skill. It never writes prose: it produces
`analysis.json` (every measured number) and `facts.md` (the same numbers, human
readable), and Claude authors the findings narrative from those. Nothing in the
report may cite a number this script did not measure.

WHY TWO PASSES: classification depends on per-IP context that is only knowable
after seeing the whole log — how many hits that IP made, and what share of them
were admin/polling URLs. Pass 1 accumulates just those two counters; pass 2
re-streams and classifies. Memory stays O(unique URLs + unique IPs) rather than
O(requests), so a large rotated log set runs on a laptop.

Usage:
  python analyze_logs.py --logs LOG [LOG ...] --site example.com --out ./Log-Analysis
Options:
  --offline            skip live bot-IP fetches; use the on-disk cache only
  --sitemap FILE       cross-reference: sitemap URLs never crawled (discovery gap)
  --gsc-csv FILE       cross-reference: GSC pages with impressions but no crawl
  --top-urls N         rows in the URL Detail tab (default 1000)
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bot_verification                                           # noqa: E402
import log_parser as LP                                           # noqa: E402
from detect_issues import detect_issues                           # noqa: E402
from health_score import calc_health                              # noqa: E402
from traffic_classify import (ADMIN_LIKE_PURPOSES, CLASS_LABELS,   # noqa: E402
                              SE_BOT_MAP, classify_content,
                              classify_traffic, url_purpose)

MAX_CHAIN_KEYS = 50_000          # bound the redirect-chain candidate table
MAX_URLS_PER_SUSPECT = 50        # bound per-suspicious-IP URL detail
DETAIL_LIMIT = 60                # findings expanded in full in facts.md
                                 # (all of them are always in analysis.json + XLSX)


def _new_agg():
    return {
        "total": 0,
        "url_hits": Counter(),
        "url_status": defaultdict(Counter),
        "url_class": defaultdict(Counter),
        "url_bytes_sum": Counter(),
        "url_last_status": {},
        "url_ctype": {},
        "url_last_seen": {},
        "gb_url_status": Counter(),
        "class_counts": Counter(),
        "agent_counts": Counter(),
        "agent_class": {},
        "agent_urls": defaultdict(set),
        "agent_status": defaultdict(Counter),
        "status_counts": Counter(),
        "content_counts": Counter(),
        "bot_content_counts": Counter(),
        "infra_agent_counts": Counter(),
        "automated_total": 0,
        "google_total": 0,
        "google_mobile_total": 0,
        "has_ua_data": False,
        "susp_ip": {},
        "ref_nonempty": 0,
        "chain_candidates": Counter(),
        "robots_statuses": set(),
        "sitemap_statuses": set(),
        "se_detail": defaultdict(lambda: {"hits": 0, "last_status": 0, "ctype": "",
                                          "bytes": 0, "last_seen": ""}),
        "daily": defaultdict(Counter),
        "ts_min": None,
        "ts_max": None,
        "span_hours": None,
        "tz_aware_seen": False,
        "tz_naive_seen": False,
    }


def _quiet(*_a, **_k):
    pass


def _norm_ts(ts):
    """Normalise a timestamp to naive UTC so stamps from different formats compare.

    Bracket logs carry an offset (`+0000`); IIS and Cloudways FPM do not. Mixing
    those in one run makes every min/max comparison raise. Anything tz-aware is
    converted to UTC and stripped; anything naive is taken as already-UTC, which
    is what IIS writes by definition and what a server log means in practice.
    Returns (normalised_ts, was_aware) so the run can disclose a mixed set."""
    if ts is None:
        return None, False
    if ts.tzinfo is not None:
        return ts.astimezone(timezone.utc).replace(tzinfo=None), True
    return ts, False


def pass_one(files, log):
    """Per-IP hit counts and admin-URL share — the inputs classification needs."""
    ip_counts, admin_by_ip, total = Counter(), Counter(), 0
    for path in files:
        for rec in LP.iter_records(path, log=_quiet):
            if rec is None:
                continue
            total += 1
            ip = rec.get("ip", "-")
            ip_counts[ip] += 1
            if url_purpose(rec.get("url", "")) in ADMIN_LIKE_PURPOSES:
                admin_by_ip[ip] += 1
    log(f"   Pass 1: {total:,} records, {len(ip_counts):,} distinct IPs")
    return ip_counts, admin_by_ip, total


def pass_two(files, ip_counts, admin_by_ip, grand_total, log):
    """Classify every record and build the aggregate the detectors consume."""
    agg = _new_agg()
    ip_admin_share = {ip: admin_by_ip.get(ip, 0) / max(n, 1)
                      for ip, n in ip_counts.items()}

    for path in files:
        for rec in LP.iter_records(path, log=_quiet):
            if rec is None:
                continue
            url = rec.get("url", "-")
            ip = rec.get("ip", "-")
            ua = rec.get("user_agent", "") or ""
            status = int(rec.get("status", 0) or 0)
            nbytes = int(rec.get("bytes", 0) or 0)
            ts, was_aware = _norm_ts(rec.get("timestamp"))
            if ts is not None:
                agg["tz_aware_seen" if was_aware else "tz_naive_seen"] = True

            cls, agent, is_auto = classify_traffic(
                ua, ip, ip_counts.get(ip, 0), grand_total,
                ip_admin_share.get(ip, 0.0))
            ctype = classify_content(url)
            purpose = url_purpose(url)

            agg["total"] += 1
            agg["url_hits"][url] += 1
            agg["url_status"][url][status] += 1
            agg["url_class"][url][cls] += 1
            agg["url_bytes_sum"][url] += nbytes
            agg["url_last_status"][url] = status
            agg["url_ctype"][url] = ctype
            agg["class_counts"][cls] += 1
            agg["agent_counts"][agent] += 1
            agg["agent_class"][agent] = cls
            agg["agent_urls"][agent].add(url)
            agg["agent_status"][agent][status] += 1
            agg["status_counts"][status] += 1
            agg["content_counts"][ctype] += 1
            if ua.strip():
                agg["has_ua_data"] = True
            if is_auto:
                agg["automated_total"] += 1
                agg["bot_content_counts"][ctype] += 1
            if cls == "infra":
                agg["infra_agent_counts"][agent] += 1
            if "googlebot" in agent.lower():
                agg["google_total"] += 1
                agg["gb_url_status"][(url, status)] += 1
                if any(k in ua for k in ("Mobile", "Android", "Smartphone")):
                    agg["google_mobile_total"] += 1
            if cls == "suspicious":
                slot = agg["susp_ip"].setdefault(
                    ip, {"hits": 0, "ua": ua, "urls": Counter(), "purposes": Counter()})
                slot["hits"] += 1
                if len(slot["urls"]) < MAX_URLS_PER_SUSPECT or url in slot["urls"]:
                    slot["urls"][url] += 1
                slot["purposes"][purpose] += 1

            ref = (rec.get("referrer") or "").strip()
            if ref and ref != "-":
                agg["ref_nonempty"] += 1
                if status == 301 and len(agg["chain_candidates"]) < MAX_CHAIN_KEYS:
                    agg["chain_candidates"][(ref, url)] += 1

            if "/robots.txt" in url:
                agg["robots_statuses"].add(status)
            if "sitemap" in url.lower():
                agg["sitemap_statuses"].add(status)

            engine = SE_BOT_MAP.get(agent)
            if engine:
                d = agg["se_detail"][(url, engine, agent)]
                d["hits"] += 1
                d["last_status"] = status
                d["ctype"] = ctype
                d["bytes"] += nbytes
                if ts:
                    d["last_seen"] = ts.isoformat()

            if ts:
                agg["url_last_seen"][url] = ts.isoformat()
                agg["daily"][ts.date().isoformat()][cls] += 1
                if agg["ts_min"] is None or ts < agg["ts_min"]:
                    agg["ts_min"] = ts
                if agg["ts_max"] is None or ts > agg["ts_max"]:
                    agg["ts_max"] = ts

    if agg["ts_min"] and agg["ts_max"]:
        agg["span_hours"] = (agg["ts_max"] - agg["ts_min"]).total_seconds() / 3600
    log(f"   Pass 2: {agg['total']:,} classified, {len(agg['url_hits']):,} unique URLs")
    return agg


def summarise_sources(files, roles, primary_roles, log):
    """Row counts and provenance per log role — primary vs supplemental."""
    out = []
    by_role = defaultdict(list)
    for p in files:
        by_role[roles[p]].append(p)
    purpose = {
        "access": "Standard access log; used as primary traffic.",
        "cloudways_backend": "Cloudways backend access; primary SEO/crawl source with User-Agent.",
        "cloudways_php": "Cloudways PHP runtime; fallback or performance supplement, not mixed into backend totals.",
        "cloudways_static": "Cloudways static assets; supplemental asset-crawl context.",
        "error": "Error log; not a traffic-analysis input.",
    }
    for role, paths in sorted(by_role.items()):
        rows, urls = 0, set()
        if role != "error":
            for p in paths:
                for rec in LP.iter_records(p, log=_quiet):
                    if rec is None:
                        continue
                    rows += 1
                    urls.add(rec.get("url", "-"))
        out.append({
            "role": role, "files": len(paths), "rows": rows,
            "unique_urls": len(urls),
            "used_in_main_totals": role in primary_roles,
            "purpose": purpose.get(role, "Parsed traffic source."),
            "filenames": [os.path.basename(p) for p in paths][:20],
        })
        log(f"   {role:<18} {rows:>9,} rows  "
            f"({'primary' if role in primary_roles else 'supplemental/skipped'})")
    return out


def read_sitemap_urls(source):
    """Extract <loc> values from a sitemap XML file."""
    import re
    try:
        with LP.open_text(source) as fh:
            text = fh.read()
    except Exception:
        return []
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text, re.I)


def read_gsc_csv(path):
    """GSC 'Pages' export -> {url: impressions}. Accepts any column order."""
    import csv
    out = {}
    try:
        with LP.open_text(path) as fh:
            reader = csv.DictReader(fh)
            cols = {c: (c or "").lower() for c in (reader.fieldnames or [])}
            url_col = next((o for o, l in cols.items()
                            if "page" in l or "url" in l or "address" in l), None)
            imp_col = next((o for o, l in cols.items() if "impress" in l), None)
            if not url_col:
                return {}
            for row in reader:
                u = (row.get(url_col) or "").strip()
                if not u:
                    continue
                try:
                    imp = int(float(str(row.get(imp_col, 0) or 0).replace(",", "")))
                except (ValueError, TypeError):
                    imp = 0
                out[u] = imp
    except Exception:
        return {}
    return out


def crossref(agg, sitemap_urls, gsc_pages):
    """Two crawl-coverage checks the log alone cannot answer.

    A log says what WAS crawled. It cannot say what SHOULD have been. Comparing
    against the sitemap and against GSC turns absence into a finding:
      * in the sitemap, never crawled          -> a discovery gap
      * earning impressions, never crawled     -> ranking on a stale copy
    Both are reported as counts + samples, never as certainty: a short log
    window legitimately misses low-frequency crawls, and the note says so."""
    if not sitemap_urls and not gsc_pages:
        return {}
    from urllib.parse import urlparse

    def _path(u):
        p = urlparse(u)
        return (p.path or "/").rstrip("/") or "/"

    crawled = {(_path(u.split("?")[0])) for u in agg["url_hits"]}

    res = {}
    if sitemap_urls:
        missing = [u for u in sitemap_urls if _path(u) not in crawled]
        res["sitemap"] = {
            "sitemap_urls": len(sitemap_urls),
            "never_crawled": len(missing),
            "sample": missing[:50],
            "note": ("A URL absent from this log window is not proof it is never "
                     "crawled — widen the window before acting on a long list."),
        }
    if gsc_pages:
        missing = [(u, i) for u, i in sorted(gsc_pages.items(), key=lambda kv: -kv[1])
                   if _path(u) not in crawled and i > 0]
        res["gsc"] = {
            "gsc_pages": len(gsc_pages),
            "impressions_but_no_crawl": len(missing),
            "sample": [{"url": u, "impressions": i} for u, i in missing[:50]],
            "note": ("These pages earn impressions but were not crawled in this "
                     "window — they rank on an increasingly stale copy."),
        }
    return res


def summarise_findings(findings):
    """Group findings by (category, issue) for authoring.

    The detectors are deliberately per-URL — the XLSX fix list needs one row per
    broken URL. But a real site produces 131 separate "404 Not Found" findings,
    and authoring 131 report cards is neither possible nor useful. This groups
    them so the author writes ONE finding per pattern ("131 URLs returned 404,
    43,xxx hits, worst offenders listed") and links to the URL Detail tab for
    the full list. Nothing is discarded — `findings` still holds every row."""
    order = {"P1 - Critical": 0, "P2 - High": 1, "P3 - Monitor": 2}
    groups = {}
    for f in findings:
        key = (f["category"], f["issue"])
        g = groups.setdefault(key, {
            "category": f["category"], "issue": f["issue"], "count": 0,
            "total_hits": 0, "worst_urgency": f["urgency"],
            "confidence": Counter(), "top": [],
        })
        g["count"] += 1
        g["total_hits"] += f["hits"]
        g["confidence"][f["confidence"]] += 1
        if order.get(f["urgency"], 3) < order.get(g["worst_urgency"], 3):
            g["worst_urgency"] = f["urgency"]
        g["top"].append((f["hits"], f["url"], f["evidence"]))
    out = []
    for g in groups.values():
        g["top"] = [{"url": u, "hits": h, "evidence": e}
                    for h, u, e in sorted(g["top"], key=lambda t: -t[0])[:10]]
        g["confidence"] = dict(g["confidence"])
        out.append(g)
    out.sort(key=lambda g: (order.get(g["worst_urgency"], 3), -g["total_hits"]))
    return out


def build_payload(agg, findings, health, sources, args, parse_stats, crossref_data):
    total = max(agg["total"], 1)
    segments = [{"segment": CLASS_LABELS.get(c, c), "key": c, "requests": n,
                 "pct": round(n / total * 100, 2)}
                for c, n in agg["class_counts"].most_common()]
    agents = [{"agent": a,
               "class": CLASS_LABELS.get(agg["agent_class"].get(a, ""),
                                         agg["agent_class"].get(a, "")),
               "requests": n, "pct": round(n / total * 100, 2),
               "unique_urls": len(agg["agent_urls"][a]),
               "top_status": (agg["agent_status"][a].most_common(1) or [(0, 0)])[0][0]}
              for a, n in agg["agent_counts"].most_common(30)]
    url_detail = []
    for u, hits in agg["url_hits"].most_common(args.top_urls):
        cl = agg["url_class"][u]
        url_detail.append({
            "url": u[:220], "total_hits": hits,
            "search_bot": cl.get("search_bot", 0), "infra": cl.get("infra", 0),
            "suspicious": cl.get("suspicious", 0), "human": cl.get("human", 0),
            "status": agg["url_last_status"].get(u, 0),
            "avg_bytes": int(agg["url_bytes_sum"].get(u, 0) / max(hits, 1)),
            "content_type": agg["url_ctype"].get(u, ""),
            "last_seen": agg["url_last_seen"].get(u, ""),
        })
    bot_crawl = [{"url": k[0][:220], "search_engine": k[1], "bot": k[2],
                  "hits": v["hits"], "status": v["last_status"],
                  "content_type": v["ctype"],
                  "avg_bytes": int(v["bytes"] / max(v["hits"], 1)),
                  "last_seen": v["last_seen"]}
                 for k, v in sorted(agg["se_detail"].items(),
                                    key=lambda kv: -kv[1]["hits"])[:args.top_urls]]
    trend = [{"date": d, "total": sum(counts.values()),
              **{CLASS_LABELS.get(c, c): n for c, n in counts.items()}}
             for d, counts in sorted(agg["daily"].items())]
    return {
        "meta": {
            "site": args.site,
            "generated_from": [os.path.basename(p) for p in parse_stats["files"]],
            "date_range": {
                "start": agg["ts_min"].isoformat() if agg["ts_min"] else None,
                "end": agg["ts_max"].isoformat() if agg["ts_max"] else None,
                "span_hours": round(agg["span_hours"], 1) if agg["span_hours"] else None,
                "timezone_note": (
                    "Mixed offset-aware and naive timestamps across the supplied logs; "
                    "all normalised to UTC (naive stamps taken as already-UTC). Verify "
                    "the server's log timezone before quoting exact hours."
                    if (agg["tz_aware_seen"] and agg["tz_naive_seen"]) else
                    "All timestamps normalised to UTC."),
            },
            "total_requests": agg["total"],
            "unique_urls": len(agg["url_hits"]),
            "lines_read": parse_stats["lines"],
            "lines_failed": parse_stats["failed"],
            "parse_rate_pct": round(
                (parse_stats["lines"] - parse_stats["failed"])
                / max(parse_stats["lines"], 1) * 100, 2),
            "primary_roles": parse_stats["primary_roles"],
            "routing_reason": parse_stats["routing_reason"],
            "verified_bot_sources": bot_verification.source_report(),
            "verified_bot_coverage": bot_verification.coverage_summary(),
            "has_user_agent_data": agg["has_ua_data"],
        },
        "segments": segments,
        "agents": agents,
        "statuses": [{"status": s, "count": n, "pct": round(n / total * 100, 2)}
                     for s, n in sorted(agg["status_counts"].items())],
        "content_types": [{"type": t, "total": n,
                           "bot_crawls": agg["bot_content_counts"].get(t, 0)}
                          for t, n in agg["content_counts"].most_common()],
        "findings": findings,
        "findings_summary": summarise_findings(findings),
        "health": [{"metric": m, "value": v, "score": s,
                    "healthy": g, "watch": y, "urgent": r}
                   for m, v, s, g, y, r in health],
        "url_detail": url_detail,
        "bot_crawl": bot_crawl,
        "log_sources": sources,
        "crawl_trend": trend,
        "crossref": crossref_data,
    }


def write_facts_md(payload, path):
    m = payload["meta"]
    p1 = sum(1 for f in payload["findings"] if f["urgency"] == "P1 - Critical")
    p2 = sum(1 for f in payload["findings"] if f["urgency"] == "P2 - High")
    p3 = sum(1 for f in payload["findings"] if f["urgency"] == "P3 - Monitor")
    lines = [
        f"# Log-file facts — {m['site']}", "",
        f"- Requests analysed: **{m['total_requests']:,}** across "
        f"**{m['unique_urls']:,}** unique URLs",
        f"- Window: {m['date_range']['start'] or 'unknown'} -> "
        f"{m['date_range']['end'] or 'unknown'} "
        f"({m['date_range']['span_hours'] or '?'}h)",
        f"- Lines read {m['lines_read']:,}, failed {m['lines_failed']:,} "
        f"(parse rate {m['parse_rate_pct']}%)",
        f"- Primary log roles: {', '.join(m['primary_roles']) or 'none'} — "
        f"{m['routing_reason']}",
        f"- {m['verified_bot_coverage']}",
        f"- User-Agent data present: {m['has_user_agent_data']}",
        "", f"## Findings: {len(payload['findings'])} (P1 {p1} · P2 {p2} · P3 {p3})", "",
        "### Grouped — author ONE report finding per row here, not one per URL", "",
        "| Worst | Category | Issue | URLs | Total hits | Confidence |",
        "|---|---|---|---|---|---|",
    ]
    for g in payload["findings_summary"]:
        conf = ", ".join(f"{k}×{v}" for k, v in g["confidence"].items())
        lines.append(f"| {g['worst_urgency']} | {g['category']} | {g['issue']} | "
                     f"{g['count']} | {g['total_hits']:,} | {conf} |")
    # Full detail per finding. The whole point of the rule engine is the
    # root cause / impact / literal fix / verification chain — printing only a
    # summary table throws away everything that makes a finding actionable.
    lines += ["", "---", "", "## Findings in full", ""]
    for i, f in enumerate(payload["findings"][:DETAIL_LIMIT], 1):
        lines += [
            f"### {i}. [{f['urgency']}] {f['issue']} — {f['category']}", "",
            f"- **Scope:** `{f['url']}`  ·  **Segment:** {f['segment']}  ·  "
            f"**Status:** {f['status_code']}  ·  **Hits:** {f['hits']:,}",
            f"- **Confidence:** {f['confidence']}  ·  **Effort:** {f['effort']}",
            f"- **What:** {f['detail']}",
            f"- **Evidence:** {f['evidence']}",
            f"- **Root cause:** {f['root_cause']}",
            f"- **Business impact:** {f['impact']}", "",
            "**Step-by-step action**", "", "```text", f["action"].rstrip(), "```", "",
            "**Verify the fix**", "", "```text", f["verify"].rstrip(), "```", "",
        ]
    if len(payload["findings"]) > DETAIL_LIMIT:
        lines += [f"_{len(payload['findings']) - DETAIL_LIMIT} further findings are not "
                  f"expanded here — every one is in `analysis.json` and in the "
                  f"**Issue Analysis** tab of the XLSX with the same 16 fields._", ""]
    lines += ["", "## Traffic segments", "", "| Segment | Requests | % |", "|---|---|---|"]
    for s in payload["segments"]:
        lines.append(f"| {s['segment']} | {s['requests']:,} | {s['pct']}% |")
    lines += ["", "## Health scorecard", "",
              "| Metric | Value | Score | Healthy | Watch | Urgent |",
              "|---|---|---|---|---|---|"]
    for h in payload["health"]:
        lines.append(f"| {h['metric']} | {h['value']} | {h['score']} | "
                     f"{h['healthy']} | {h['watch']} | {h['urgent']} |")
    if payload.get("crossref"):
        cr = payload["crossref"]
        lines += ["", "## Crawl-coverage cross-reference", ""]
        if "sitemap" in cr:
            lines.append(f"- Sitemap: {cr['sitemap']['never_crawled']} of "
                         f"{cr['sitemap']['sitemap_urls']} URLs never crawled in this "
                         f"window. {cr['sitemap']['note']}")
        if "gsc" in cr:
            lines.append(f"- GSC: {cr['gsc']['impressions_but_no_crawl']} pages earn "
                         f"impressions but were not crawled. {cr['gsc']['note']}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description="SEO log-file analysis engine")
    ap.add_argument("--logs", nargs="+", required=True,
                    help="log files, directories or globs (.gz/.bz2/.xz supported)")
    ap.add_argument("--site", default="site", help="site/client label for the report")
    ap.add_argument("--out", default="./Log-Analysis", help="output directory")
    ap.add_argument("--offline", action="store_true",
                    help="do not fetch bot IP ranges; use the on-disk cache only")
    ap.add_argument("--sitemap", default="", help="sitemap XML file for cross-reference")
    ap.add_argument("--gsc-csv", dest="gsc_csv", default="",
                    help="GSC Pages export for cross-reference")
    ap.add_argument("--top-urls", type=int, default=1000,
                    help="rows in the URL Detail tab (default 1000)")
    args = ap.parse_args()

    def log(msg=""):
        print(msg, flush=True)

    files, skipped = LP.discover_logs(args.logs)
    if not files:
        log("No log files found. Check --logs.")
        if skipped:
            log(f"  {len(skipped)} file(s) present but not recognised as logs: "
                f"{', '.join(os.path.basename(p) for p in skipped[:10])}")
        return 2
    log(f"Discovered {len(files)} log file(s).")
    for p in files:
        log(f"    + {os.path.basename(p)} ({os.path.getsize(p):,} bytes)")
    if skipped:
        # Never drop input silently: a sweep that matched 1 of 5 rotated files
        # would still render a confident-looking report on a fraction of the data.
        log(f"  SKIPPED {len(skipped)} non-log file(s): "
            f"{', '.join(os.path.basename(p) for p in skipped[:10])}"
            f"{' ...' if len(skipped) > 10 else ''}")

    roles = {p: LP.infer_log_role(p) for p in files}
    primary_roles, reason = LP.route_log_roles(Counter(roles.values()))
    log(f"Log source routing: primary = {primary_roles or 'none'} — {reason}")

    primary_files = [p for p in files if roles[p] in primary_roles]
    if not primary_files:
        log("No primary traffic logs after routing (were all inputs error logs?).")
        return 2

    log("\nParsing (format detection per file):")
    lines_total, failed_total = 0, 0
    for p in primary_files:
        log(f"  {os.path.basename(p)}")
        _recs, ln, fl = LP.parse_file(p, log=log, collect=False)
        lines_total += ln
        failed_total += fl

    log("\nLoading verified search-bot IP ranges...")
    bot_verification.load_networks(offline=args.offline)
    log("  " + bot_verification.coverage_summary())

    log("\nClassifying:")
    ip_counts, admin_by_ip, grand_total = pass_one(primary_files, log)
    agg = pass_two(primary_files, ip_counts, admin_by_ip, grand_total, log)
    if agg["total"] == 0:
        log("Parsed zero records — check the log format.")
        return 2

    log("\nLog sources:")
    sources = summarise_sources(files, roles, primary_roles, log)

    log("\nDetecting issues...")
    findings = detect_issues(agg)
    health = calc_health(agg, findings)
    p1 = sum(1 for f in findings if f["urgency"] == "P1 - Critical")
    p2 = sum(1 for f in findings if f["urgency"] == "P2 - High")
    p3 = sum(1 for f in findings if f["urgency"] == "P3 - Monitor")
    log(f"  {len(findings)} findings — P1 {p1} · P2 {p2} · P3 {p3}")
    for cat, n in Counter(f["category"] for f in findings).most_common():
        log(f"    {cat}: {n}")

    cross = crossref(
        agg,
        read_sitemap_urls(args.sitemap) if args.sitemap else [],
        read_gsc_csv(args.gsc_csv) if args.gsc_csv else {},
    )
    if cross:
        log("\nCross-reference:")
        if "sitemap" in cross:
            log(f"  sitemap: {cross['sitemap']['never_crawled']} of "
                f"{cross['sitemap']['sitemap_urls']} URLs never crawled in this window")
        if "gsc" in cross:
            log(f"  GSC: {cross['gsc']['impressions_but_no_crawl']} pages have "
                f"impressions but no crawl in this window")

    payload = build_payload(
        agg, findings, health, sources, args,
        {"files": primary_files, "lines": lines_total, "failed": failed_total,
         "primary_roles": primary_roles, "routing_reason": reason},
        cross)

    os.makedirs(args.out, exist_ok=True)
    jpath = os.path.join(args.out, "analysis.json")
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    fpath = os.path.join(args.out, "facts.md")
    write_facts_md(payload, fpath)
    log(f"\nWrote {jpath}")
    log(f"Wrote {fpath}")
    log("\nNext: author report_data.py from these facts, then run "
        "build_html.py and build_xlsx.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
