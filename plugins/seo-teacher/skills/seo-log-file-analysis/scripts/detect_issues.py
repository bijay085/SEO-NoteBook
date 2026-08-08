"""Issue detection — the evidence-gated rule engine.

Ported from `seo_log_file_analyzer.py` (detect_issues); thresholds and gate
logic unchanged. It runs over the aggregate built by analyze_logs.py rather
than a DataFrame, so the same rules apply to a 20 MB or a 20 GB log.

WHAT AN "EVIDENCE GATE" IS, and why every rule has one: raw log counts produce
enormous false-positive volume. A gate is the extra condition that must hold
before a pattern is reported, plus the `evidence` string stating WHY it
survived. The load-bearing gates:

  * A single VERIFIED-GOOGLEBOT 404 or 5xx is an SEO event at any volume; the
    same status with zero Googlebot hits is only link hygiene.
  * Scanner probes are excluded from the 404 rule (Security covers them).
  * 302s are reported only on CONTENT URLs — auth/checkout/account 302s are
    correct behaviour.
  * A 301 needs >=5 hits AND >=50% of that URL's requests before it counts as
    "still being crawled" — 2 hits is noise.
  * Trailing-slash duplicates are skipped when either variant already 301s in
    >80% of cases; that IS the canonical fix working.
  * Redirect-chain detection runs only when referrer data covers >=20% of rows.
  * Backend-URL crawl needs >=3 VERIFIED search-bot hits, not "any bot".
  * Low Googlebot share drops to Low confidence when the sample spans <48h,
    because crawl is bursty.

THREE DEFECTS in the source script are fixed here (deliberate behaviour change):
  1. "URL Parameter Explosion" `add()` sat OUTSIDE its `for` loop, so it fired
     once from the last iteration's variables and raised NameError when every
     iteration hit `continue`. Now inside the loop: one finding per base URL.
  2. The 404 rule computed `urg_404` from the Googlebot gate then discarded it,
     passing a hit-count expression instead — a Googlebot-hit 404 could be
     filed P2 while its own gate said P1. The gated value is now used.
  3. The 5xx rule had the same dead-variable bug (`urg_5xx` computed, then
     'P1 - Critical' hardcoded). The gated value is now used.

Public API:  detect_issues(agg) -> [finding dict]
"""
from traffic_classify import (CACHEBUST_PARAM_RE, TRACKING_PARAM_RE,
                              classify_content, evaluate_ua_modernity, url_purpose)

URGENCY_ORDER = {"P1 - Critical": 0, "P2 - High": 1, "P3 - Monitor": 2}

SEG_LABELS = {
    "search_bot": "Search Bots", "seo_tool": "SEO Tools",
    "infra": "Infrastructure", "generic_bot": "Generic Bots",
    "suspicious": "Suspicious", "human": "Human",
}

WP_BACKEND = [
    ("/wp-admin",       "WordPress admin panel"),
    ("/wp-login",       "WordPress login page"),
    ("admin-ajax.php",  "WordPress AJAX handler"),
    ("/wp-cron.php",    "WordPress pseudo-cron (replace with real server cron)"),
    ("/xmlrpc.php",     "WordPress XML-RPC — legacy remote API, usually safe to block"),
    ("/wp-json/oembed", "WordPress oEmbed endpoint"),
    ("/wp-json/wp/v2/", "WordPress REST API"),
    ("/administrator",  "Joomla admin panel"),
    ("?seraph_accel",   "Seraph Accel cache preloader parameter"),
]

LOW_VALUE_PATTERNS = ["/tag/", "/author/", "/page/", "/feed/", "/category/page/"]

SENSITIVE_FILES = [
    (".env",      "Environment config — may contain DB credentials, API keys, secret tokens"),
    (".bak",      "Backup file — may contain full codebase or database dump"),
    (".sql",      "SQL dump — may contain full database with user records"),
    ("wp-config", "WordPress config — contains DB username, password, secret keys"),
    ("/.git",     "Git repository directory — exposes full source code history"),
    ("phpinfo",   "PHP info page — exposes server config, modules, file paths"),
    (".config",   "Application config file — may contain service credentials"),
    ("/.svn",     "SVN repository directory — exposes source history"),
    ("/backup",   "Backup directory — may contain database or file archives"),
    ("debug.log", "Debug log — may contain internal paths, SQL queries, user data"),
]


def _sensitive_regexes():
    import re
    return {
        ".env":      re.compile(r"(/|^)\.env(\.|/|$)", re.I),
        ".bak":      re.compile(r"\.bak(\?|/|$)", re.I),
        ".sql":      re.compile(r"\.sql(\?|/|$|\.gz)", re.I),
        "wp-config": re.compile(r"/wp-config(\.php|-sample|\.bak|\.backup)", re.I),
        "/.git":     re.compile(r"/\.git(/|$)", re.I),
        "phpinfo":   re.compile(r"/phpinfo\.php|phpinfo\(\)", re.I),
        ".config":   re.compile(r"\.config(\?|/|$)", re.I),
        "/.svn":     re.compile(r"/\.svn(/|$)", re.I),
        "/backup":   re.compile(r"/backup(/|s/|\.|$)", re.I),
        "debug.log": re.compile(r"/debug\.log(\?|$)", re.I),
    }


def detect_issues(agg):
    """agg = the aggregate dict from analyze_logs.build_aggregate()."""
    findings = []
    total = agg["total"]
    if total == 0:
        return findings

    url_hits = agg["url_hits"]
    url_status = agg["url_status"]
    url_class = agg["url_class"]
    url_bytes = agg["url_bytes_sum"]
    url_last_status = agg["url_last_status"]
    gb_url_status = agg["gb_url_status"]
    class_counts = agg["class_counts"]
    automated_total = agg["automated_total"]
    bot_content = agg["bot_content_counts"]

    def add(category, issue, detail, url, segment, status_code, hits,
            urgency, root_cause, impact, action, effort, verify,
            confidence="High", evidence=""):
        findings.append({
            "category": category, "issue": issue, "detail": detail,
            "url": str(url)[:220], "segment": segment,
            "status_code": str(status_code), "hits": hits, "urgency": urgency,
            "root_cause": root_cause, "impact": impact, "action": action,
            "effort": effort, "verify": verify, "confidence": confidence,
            "evidence": evidence, "owner": "",
        })

    def gb_hits(u, code):
        return gb_url_status.get((u, code), 0)

    def seg_label(u):
        segs = url_class.get(u) or {}
        if not segs:
            return "All"
        return SEG_LABELS.get(max(segs, key=segs.get), max(segs, key=segs.get))

    # ── A: HTTP ERRORS ──────────────────────────────────────────────────────
    for u, hits in url_hits.items():
        sc = url_status.get(u, {})
        seg = seg_label(u)
        url_total = hits or 1

        n = sc.get(404, 0)
        purpose_404 = url_purpose(u)
        gb_404 = gb_hits(u, 404)
        # Gate: scanner probes belong to the Security rule; a handful of 404s is
        # usually a typo. BUT one Googlebot 404 is an SEO event at any volume.
        if (n >= 3 or gb_404 >= 1) and purpose_404 != "scanner_probe":
            if gb_404 >= 1:
                conf_404 = "High"
                urg_404 = "P1 - Critical" if gb_404 >= 5 else "P2 - High"
                ev_404 = (f"Verified: Googlebot received 404 on this URL {gb_404} "
                          f"time(s); {n} total 404s across all agents; URL purpose = "
                          f"{purpose_404}. Direct SEO impact.")
            else:
                conf_404 = "High" if n >= 10 else "Medium"
                urg_404 = "P2 - High" if n >= 10 else "P3 - Monitor"
                ev_404 = (f"Verified: {n} 404 responses but zero Googlebot hits — "
                          f"link-hygiene issue, not yet an indexing issue. URL purpose "
                          f"= {purpose_404}.")
            add("HTTP Errors", "404 Not Found",
                f"{n} requests hit a missing page. Each one wastes crawl budget and "
                f"signals poor link hygiene.",
                u, seg, 404, n, urg_404,
                "Page does not exist. Likely causes: deleted page with no redirect, "
                "renamed URL without updating internal links, or a stale sitemap entry.",
                "Wastes crawl budget — each 404 is a spent crawl slot. Persistent 404s on "
                "previously-indexed URLs trigger de-indexing. Users clicking internal "
                "links see error pages.",
                "1. Find all source links: Screaming Frog > Spider > filter Status Code = "
                "404 > select this URL > Inlinks tab lists every page linking here.\n"
                "2. Cross-check GSC > Coverage > Not Found for this URL.\n"
                "3. If the page moved: add a server-side 301 to the closest live page.\n"
                "4. If intentionally deleted: return 410 Gone (preferred over a 404).\n"
                "5. Remove the URL from the XML sitemap.\n"
                "6. Fix or remove every internal link pointing at it.",
                "30 min – 2 hrs depending on number of source links",
                "curl -I [URL] > must show 301 (to destination) or 410.\n"
                "GSC > Coverage > Not Found: URL disappears within 1-2 weeks.\n"
                "Screaming Frog re-crawl: 0 internal links pointing to this URL.",
                confidence=conf_404, evidence=ev_404)

        for code in (500, 502, 503, 504):
            n = sc.get(code, 0)
            if n <= 0:
                continue
            err_share = n / url_total
            gb_5xx = gb_hits(u, code)
            # Gate: a one-off 5xx rarely matters UNLESS Googlebot saw it — even a
            # single Googlebot 5xx can drop a URL from the index temporarily.
            if not (n >= 10 or err_share >= 0.05 or gb_5xx >= 1):
                continue
            if gb_5xx >= 1:
                conf_5xx = "High"
                urg_5xx = "P1 - Critical" if gb_5xx >= 3 else "P2 - High"
                ev_5xx = (f"Verified: Googlebot received {code} on this URL {gb_5xx} "
                          f"time(s); {n} total {code}s = {err_share*100:.1f}% of "
                          f"{url_total} requests. Direct SEO impact.")
            else:
                conf_5xx = "High" if (n >= 10 and err_share >= 0.05) else "Medium"
                urg_5xx = ("P1 - Critical" if (n >= 10 and err_share >= 0.10)
                           else "P2 - High")
                ev_5xx = (f"Verified: {n} {code} responses = {err_share*100:.1f}% of "
                          f"{url_total} requests; no Googlebot hits seen yet.")
            causes = {
                500: "Unhandled PHP/application exception. Check the hosting error_log for the stack trace.",
                502: "Upstream server or proxy returned an invalid response. Check whether PHP-FPM or Node is running.",
                503: "Server overloaded or in planned maintenance. Add Retry-After if it is a maintenance window.",
                504: "Upstream timed out. A PHP/DB query is too slow, or the load-balancer timeout is too short.",
            }
            log_paths = {
                500: "tail -100 /var/log/php/error.log OR hosting panel > Logs > error.log",
                502: "systemctl status php8.x-fpm  |  tail -100 /var/log/nginx/error.log",
                503: "check server CPU/memory in the hosting panel > review active processes",
                504: "tail -100 /var/log/nginx/error.log  |  check the DB slow query log",
            }
            extra = {
                500: "Increase PHP memory_limit (try 256M) and max_execution_time (try 120).",
                502: "Check PHP-FPM: systemctl status php8.2-fpm. Restart if stopped.",
                503: "For planned maintenance only: return 503 with Retry-After: 3600 so Google waits.",
                504: "Check DB performance: enable slow_query_log, find queries >2s.",
            }.get(code, "")
            add("HTTP Errors", f"{code} Server Error",
                f"{n} requests returned HTTP {code}. Google treats persistent {code}s as "
                f"soft 404s and may de-index the page.",
                u, seg, code, n, urg_5xx,
                causes.get(code, "Server-side failure."),
                f"Google de-indexes pages returning persistent {code}s within days. Users "
                f"cannot access the content. Every {code} inside a crawl window signals an "
                f"unhealthy server.",
                f"1. Check the server error log immediately: {log_paths.get(code)}.\n"
                f"2. Reproduce: curl -I \"{u}\" and confirm the response code.\n"
                f"3. {extra}\n"
                f"4. After the fix: GSC > URL Inspection > Test Live URL > must say "
                f"\"URL is available to Google\".\n"
                f"5. Request re-indexing: GSC > URL Inspection > Request Indexing.",
                "1-4 hrs depending on root cause",
                "curl -I [URL] > must return 200.\n"
                "GSC URL Inspection > Live Test > \"URL is available to Google\".\n"
                "GSC > Coverage > Server error (5xx) count trending down over 7 days.",
                confidence=conf_5xx, evidence=ev_5xx)

        n301 = sc.get(301, 0)
        redirect_share = n301 / url_total
        # Gate: 2 redirect hits is noise. Need persistent crawling AND dominance.
        if n301 >= 5 and redirect_share >= 0.50:
            conf_301 = "High" if n301 >= 20 else "Medium"
            urg_301 = ("P1 - Critical" if n301 >= 50
                       else ("P2 - High" if n301 >= 20 else "P3 - Monitor"))
            ev_301 = (f"Verified: {n301} of {url_total} ({redirect_share*100:.0f}%) "
                      f"requests to this URL got 301 — persistent, not one-off.")
            add("Redirects", "301 Redirect Still Being Crawled",
                f"{n301} requests hit this URL which sends a 301. Internal links or the "
                f"sitemap still point here instead of the final destination.",
                u, seg, 301, n301, urg_301,
                "Internal links and/or the XML sitemap still reference the old "
                "redirecting URL. Every crawl of a redirect consumes two request slots.",
                "PageRank diluted across both old and new URL. Crawl budget halved per "
                "redirect hop. GSC may report both URLs with divided impressions.",
                "1. Find every internal link to this URL: Screaming Frog > Spider > filter "
                "3xx > select this URL > Inlinks tab.\n"
                "2. Update each internal link to point directly at the final 200 URL.\n"
                "3. Bulk-update WP: Better Search Replace > old URL > final URL (include "
                "https:// variants).\n"
                "4. Regenerate the XML sitemap; confirm the old URL is excluded.\n"
                "5. Do NOT remove the 301 itself — external sites still link to it.",
                "1-3 hrs",
                "Screaming Frog re-crawl > 0 internal links to the old URL.\n"
                "GSC > Coverage > Redirect error count drops to 0 within 2 weeks.\n"
                "curl -I [old URL] > still shows 301 (external links still work).",
                confidence=conf_301, evidence=ev_301)

        n302 = sc.get(302, 0)
        purpose_302 = url_purpose(u)
        # Gate: 302s on account/checkout/login URLs are LEGITIMATE auth flow.
        if n302 >= 3 and purpose_302 in ("content", "tracked_content"):
            conf_302 = "High" if n302 >= 10 else "Medium"
            ev_302 = (f"Verified: {n302} 302 responses on a content URL "
                      f"(purpose={purpose_302}); auth/account redirects excluded.")
            add("Redirects", "302 Temporary Redirect",
                f"{n302} requests received a 302 (temporary) redirect. Google does not "
                f"pass PageRank through 302s.",
                u, seg, 302, n302, "P2 - High",
                "302 is a temporary signal — Google keeps the source URL indexed and "
                "withholds link equity from the destination.",
                "Link equity not transferred. The source URL stays indexed instead of the "
                "destination. In place more than a week, this should almost certainly be "
                "a 301.",
                "1. Confirm the redirect is permanent (not an A/B test or geo-redirect).\n"
                "2. Change 302 to 301:\n"
                "   .htaccess: change R=302 to R=301 in the RewriteRule.\n"
                "   nginx: change `redirect` 302 to `return 301`.\n"
                "   WP Redirection plugin: Edit > Type = \"301 Moved Permanently\".\n"
                "3. Clear CDN and server cache after the change.\n"
                "4. Update internal links to point straight at the destination.",
                "15-30 min",
                "curl -Iv [URL] > Location header must show 301 not 302.\n"
                "GSC URL Inspection on the source URL > \"URL is a redirect\", type 301.",
                confidence=conf_302, evidence=ev_302)

    # ── B: REDIRECT CHAINS ──────────────────────────────────────────────────
    # Gate: referrer data must cover >=20% of rows — many log formats omit it
    # for bot traffic, and a sparse referrer column produces phantom chains.
    ref_coverage = agg["ref_nonempty"] / max(total, 1)
    if ref_coverage >= 0.20 and agg["chain_candidates"]:
        redirect_urls = {u for u in url_hits if url_status.get(u, {}).get(301, 0) >= 1}
        chain_hits = {}
        for (ref, u), cnt in agg["chain_candidates"].items():
            if any(ru in ref for ru in redirect_urls):
                chain_hits[u] = chain_hits.get(u, 0) + cnt
        for u, cnt in sorted(chain_hits.items(), key=lambda kv: -kv[1])[:10]:
            ev_chain = (f"Verified: referrer present on {ref_coverage*100:.0f}% of rows; "
                        f"{cnt} hops whose referrer points at another redirecting URL.")
            add("Redirects", "Redirect Chain Detected",
                f"This URL appears to be a middle hop in a redirect chain (A > B > C). "
                f"{cnt} requests observed. Each extra hop loses ~15% of PageRank and "
                f"wastes an additional crawl slot.",
                u, seg_label(u), "301 > 301", cnt, "P2 - High",
                "Multiple 301s chained together — commonly an HTTP>HTTPS migration "
                "followed by URL restructures without cleaning up prior redirects.",
                "Each hop loses ~15% of PageRank. Googlebot may stop following after 5 "
                "hops. Double the crawl budget wasted vs a single redirect.",
                "1. Map the chain: curl -Iv [start URL] and follow each Location header.\n"
                "   OR Screaming Frog > Always Follow Redirects > Reports > Redirect Chains.\n"
                "2. Flatten to one hop: make A redirect directly to C.\n"
                "3. Update internal links pointing at A or B to point at C.\n"
                "4. Keep the A > C redirect for external links you cannot control.",
                "30 min - 2 hrs (mapping + flattening each chain)",
                "curl -Iv [A] > a single Location header pointing at C, which returns 200.\n"
                "Screaming Frog > Redirect Chains report > empty for the fixed URLs.",
                confidence="High" if cnt >= 10 else "Medium", evidence=ev_chain)

    # ── C: CRAWL BUDGET WASTE ───────────────────────────────────────────────
    for u, hits in url_hits.items():
        ul = u.lower()
        for kw, kw_label in WP_BACKEND:
            if kw.lower() not in ul:
                continue
            segs = url_class.get(u) or {}
            # Gate: only VERIFIED search-bot crawls count. Generic bots are noise.
            verified_bot_hits = segs.get("search_bot", 0)
            bot_hits = sum(segs.get(s, 0) for s in
                           ("search_bot", "seo_tool", "generic_bot", "suspicious"))
            if verified_bot_hits >= 3:
                ev_backend = (f"Verified: {verified_bot_hits} hits from search-bot-class "
                              f"IPs (Google/Bing ranges); total bot-class hits = {bot_hits}.")
                add("Crawl Budget", f"Backend URL Crawled: {kw_label}",
                    f"{bot_hits} bot requests to a backend/admin endpoint that must never "
                    f"be indexed. robots.txt is not blocking this path.",
                    u, "Bots", url_last_status.get(u, 0), hits, "P1 - Critical",
                    f"robots.txt is missing a Disallow rule for {kw}. Crawlers are freely "
                    f"reaching backend admin/API endpoints.",
                    "Direct crawl budget waste on non-indexable pages. Security exposure — "
                    "admin and API endpoints should not be publicly crawlable. Risk of "
                    "automated login attempts on /wp-login.",
                    f"1. Add to robots.txt:\n"
                    f"   User-agent: *\n"
                    f"   Disallow: {kw}\n"
                    f"2. For /wp-cron.php: define(\"DISABLE_WP_CRON\", true); in "
                    f"wp-config.php, then a real cron:\n"
                    f"   */5 * * * * curl -s https://DOMAIN/wp-cron.php > /dev/null\n"
                    f"3. For /xmlrpc.php (if unused), deny it in .htaccess or nginx.\n"
                    f"4. For /wp-json/: if unused by the theme/plugins, require auth via "
                    f"the rest_authentication_errors filter.\n"
                    f"5. Validate: GSC > Settings > robots.txt > this URL shows \"Blocked\".",
                    "15-45 min",
                    "curl https://DOMAIN/robots.txt > confirm the Disallow rule.\n"
                    "GSC robots.txt tester > the URL shows \"Blocked\".\n"
                    "Re-run log analysis in 2 weeks > URL absent from the bot segment.",
                    confidence="High", evidence=ev_backend)
            break

    # Infrastructure traffic share
    for agent, cnt in agg["infra_agent_counts"].items():
        pct = cnt / total * 100
        # Gate: ~5% is a normal baseline for caching plugins. Only >15% is real.
        if pct <= 15:
            continue
        is_wp_ping = "WordPress Self-Ping" in agent
        ev_infra = (f"Verified: {agent} = {pct:.1f}% of all traffic; the baseline for "
                    f"cache/monitor agents is <10%.")
        add("Crawl Budget", f"High Internal Traffic: {agent}",
            f"{cnt:,} requests ({pct:.1f}% of all traffic) from an internal platform "
            f"agent. Inflates server load and obscures real crawl patterns.",
            f"Site-wide ({cnt:,} requests)", "Infrastructure", "Mixed", cnt,
            "P2 - High" if pct > 20 else "P3 - Monitor",
            f"The {agent} is making high-volume automated requests. For WordPress "
            f"Self-Ping that is wp-cron firing on every page load instead of on a real "
            f"schedule. For cache preloaders it is the plugin re-warming every sitemap URL.",
            "Server resources consumed unnecessarily. Log data polluted — harder to see "
            "real search-bot patterns. Peak-hour preloading degrades Core Web Vitals.",
            ("1. Disable WP pseudo-cron: define(\"DISABLE_WP_CRON\", true); in wp-config.php.\n"
             "2. Add a real server cron:\n"
             "   */5 * * * * curl -s https://DOMAIN/wp-cron.php > /dev/null\n"
             "3. Self-ping traffic drops to a predictable 5-minute interval."
             if is_wp_ping else
             "1. Open the cache plugin settings (WP Rocket / seraph-accel / LiteSpeed).\n"
             "2. Reduce the preload crawl rate to the minimum interval.\n"
             "3. Schedule preloading for off-peak hours (2am-5am).\n"
             "4. Switch to \"preload only on cache expiry\" instead of a full re-crawl.\n"
             "5. Exclude already-fresh pages via the plugin's URL exclusion list."),
            "30-60 min",
            "Re-run log analysis on the next day's log > infra traffic % should drop.\n"
            "Hosting panel CPU/memory shows a lower baseline.",
            confidence="High", evidence=ev_infra)

    # Suspicious high-volume IPs
    for ip, info in sorted(agg["susp_ip"].items(), key=lambda kv: -kv[1]["hits"])[:10]:
        cnt = info["hits"]
        pct = cnt / total * 100
        ua_sample = (info.get("ua") or "")[:100]
        top_urls = [u for u, _ in sorted(info["urls"].items(), key=lambda kv: -kv[1])[:3]]
        url_preview = " | ".join(top_urls)
        # Only IPs that survived the URL-context check in classify_traffic reach
        # here, so admin polling is already excluded. Annotate WHY it looks bad.
        ua_eval = evaluate_ua_modernity(ua_sample)
        purposes = info.get("purposes", {})
        content_share = ((purposes.get("content", 0) + purposes.get("tracked_content", 0))
                         / max(cnt, 1))
        reasons = []
        if ua_eval["is_future"]:
            reasons.append(f"UA claims Chrome {ua_eval['chrome_version']} which has not "
                           f"been released yet")
        if cnt > 500 and pct > 10:
            reasons.append(f"{cnt:,} hits = {pct:.1f}% of total traffic from one IP")
        if content_share > 0.5:
            reasons.append(f"{content_share*100:.0f}% of requests target content pages "
                           f"(not admin/cron/SW)")
        ev_susp = ("Verified: " + "; ".join(reasons)) if reasons else "Pattern match (low signal)"
        conf_susp = ("High" if (ua_eval["is_future"] and content_share > 0.5)
                     else ("Medium" if content_share > 0.3 else "Low"))
        urg_susp = (("P1 - Critical" if pct > 20 else "P2 - High") if conf_susp == "High"
                    else ("P2 - High" if conf_susp == "Medium" else "P3 - Monitor"))
        add("Security / Spam", "Suspicious High-Volume IP",
            f"IP {ip} made {cnt:,} requests ({pct:.1f}% of all traffic). "
            f"UA: {ua_sample[:80]}. Top URLs: {url_preview[:100]}",
            f"IP: {ip}", "Suspicious", "Mixed", cnt, urg_susp,
            "A single IP generating abnormally high request volume behind a browser-like "
            "UA to evade basic detection. Likely a headless-browser scraper "
            "(Puppeteer/Playwright) or content harvester.",
            "Server bandwidth and CPU cost. Potential content or price-data theft. "
            "Pollutes analytics. Can trigger rate limiting that catches real users or "
            "Googlebot.",
            f"1. Block in Cloudflare: Security > IP Rules > IP = {ip} > Block.\n"
            f"   OR nginx: deny {ip};   OR .htaccess: Require not ip {ip}\n"
            f"2. Add rate limiting: same IP > 100 req/min > block for 1 hour.\n"
            f"3. Identify the owner at ipinfo.io/{ip} — if a cloud provider, consider "
            f"blocking the ASN should scraping persist.\n"
            f"4. Review the targeted URLs (URL Detail tab) — if product/pricing pages, "
            f"add JS-based access controls.\n"
            f"5. Enable Cloudflare Bot Fight Mode for ongoing protection.",
            "30-60 min",
            f"grep \"{ip}\" /var/log/nginx/access.log | wc -l > 0 after the block.\n"
            f"Cloudflare Analytics > Security Events > block events for this IP.\n"
            f"Confirm ipinfo.io/{ip} is a datacenter, not residential, before blocking.",
            confidence=conf_susp, evidence=ev_susp)

    # URL parameter explosion — FIXED: emitted inside the loop (see docstring).
    # Gate: only INDEXABLE URLs count. `/wp-cron.php?doing_wp_cron=<timestamp>`
    # mints a unique query string on every invocation, so on a real site it
    # produced "1,787 parameter variants" as a P2 crawl-budget finding — but
    # cron is internal, never indexed, and costs no crawl budget. Admin polling,
    # scanner probes and static assets are excluded for the same reason; the
    # infra-traffic rule is the one that legitimately covers wp-cron volume.
    param_urls = [u for u in url_hits
                  if "?" in u and url_purpose(u) not in
                  ("admin_polling", "admin_ui", "scanner_probe", "static_asset")]
    if len(param_urls) > 5:
        by_base = {}
        for u in param_urls:
            by_base.setdefault(u.split("?")[0], []).append(u)
        for base, variants in by_base.items():
            param_keys, tracking_keys, cachebust_keys = set(), set(), set()
            tracking_variant_count = 0
            for u in variants:
                qs = u.split("?", 1)[1] if "?" in u else ""
                if TRACKING_PARAM_RE.search("?" + qs):
                    tracking_variant_count += 1
                for part in qs.split("&"):
                    k = part.split("=")[0]
                    param_keys.add(k)
                    if TRACKING_PARAM_RE.search("?" + part):
                        tracking_keys.add(k)
                    if CACHEBUST_PARAM_RE.search("?" + part):
                        cachebust_keys.add(k)
            # Gate: >=20 total variants (filter explosion) OR >=5 tracking-param
            # variants (always-bad duplicates from analytics URLs).
            if not (len(variants) >= 20 or tracking_variant_count >= 5):
                continue
            trigger = ("tracking-param duplicates"
                       if tracking_variant_count >= 5 and len(variants) < 20
                       else "filter/parameter explosion")
            ev_param = (f"Verified: {len(variants)} parameter variants of {base} "
                        f"({trigger}); tracking params = {sorted(tracking_keys) or 'none'} "
                        f"({tracking_variant_count} URLs); cache-bust params = "
                        f"{sorted(cachebust_keys) or 'none'}.")
            conf_param = ("High" if len(variants) >= 50 or tracking_variant_count >= 20
                          else "Medium")
            add("Crawl Budget", "URL Parameter Explosion",
                f"{len(variants)} parameter variants of the same base URL are being "
                f"crawled. Parameter keys found: {', '.join(sorted(param_keys)[:8])}.",
                f"{base}?... ({len(variants)} variants)", "All", "Mixed",
                sum(url_hits[u] for u in variants), "P2 - High",
                "Crawlers treat every unique query string as a distinct indexable page. "
                "Common causes: session IDs in URLs, tracking parameters, filter/sort "
                "parameters on listing pages, pagination without canonicals.",
                "Near-duplicate pages dilute PageRank across hundreds of variants. Crawl "
                "budget wasted on low-value parameterised versions. Canonical signals "
                "fragmented; thin filtered pages may enter the index.",
                f"1. Add a canonical on every parameterised page pointing at the clean base:\n"
                f"   <link rel=\"canonical\" href=\"{base}\">\n"
                f"2. Use noindex,follow on tracking-parameter URLs rather than a robots.txt "
                f"Disallow. WHY: Disallow blocks crawling entirely, so you lose the log and "
                f"GSC visibility into those URLs; noindex,follow keeps them crawlable but "
                f"un-indexed, and link equity still flows through the follow directive.\n"
                f"   nginx: if ($args ~* \"utm_|sessionid=\") {{ add_header X-Robots-Tag "
                f"\"noindex, follow\"; }}\n"
                f"3. For pagination: rel=next/prev, OR canonical to the base page.\n"
                f"4. Confirm which parameters actually change content before excluding them.\n"
                f"5. Disable crawling of paginated archives that carry no unique content.",
                "2-4 hrs",
                "Screaming Frog re-crawl > Canonicals tab > all variants point at the base.\n"
                "GSC > Coverage > Excluded > \"Duplicate, Google chose different canonical\" "
                "rises (correct behaviour).\n"
                "GSC indexed URLs containing parameters decrease over 4-6 weeks.",
                confidence=conf_param, evidence=ev_param)

    # Static-asset crawl ratio
    if automated_total > 50:
        static_types = ("CSS", "JavaScript", "Font", "Image", "SVG")
        sh = sum(bot_content.get(t, 0) for t in static_types)
        sp = sh / automated_total * 100
        # Gate: 15-25% static is normal on CDN-fronted sites; >30% is a real
        # cache-header problem.
        if sp > 30:
            ev_static = (f"Verified: {sh:,} of {automated_total:,} bot requests "
                         f"({sp:.1f}%) target CSS/JS/images/fonts; healthy baseline <25%.")
            add("Crawl Budget", "High Static Asset Crawl Ratio",
                f"{sp:.1f}% of automated requests are for CSS/JS/images/fonts ({sh:,} "
                f"hits). Re-downloading identical files on every crawl is wasted bandwidth.",
                f"{sh:,} hits across static assets", "Bots", "Mixed", sh,
                "P2 - High" if sp > 35 else "P3 - Monitor",
                "Static assets are re-fetched on every crawl because Cache-Control headers "
                "are absent or too short, forcing crawlers to re-download identical files.",
                "Crawl budget wasted on non-indexable files. Bandwidth cost inflated. "
                "Fewer crawl slots left for actual HTML content.",
                "1. Set long-lived caching headers on static assets:\n"
                "   nginx: location ~* \\.(css|js|jpg|png|webp|svg|woff2)$ { expires 1y; "
                "add_header Cache-Control \"public, max-age=31536000, immutable\"; }\n"
                "   Apache: ExpiresActive On; ExpiresByType text/css \"access plus 1 year\";\n"
                "2. \"immutable\" tells the client the file will not change — zero "
                "re-validation requests.\n"
                "3. Version filenames (style.css?v=2.1) to bust cache on change.\n"
                "4. Do NOT disallow assets in robots.txt — Google needs CSS/JS to render.",
                "1-2 hrs (server config + cache invalidation)",
                "curl -I [CSS URL] > must include Cache-Control: public, max-age=31536000.\n"
                "DevTools > Network > reload > assets show \"(from disk cache)\".\n"
                "Re-run log analysis in 1 week > static % of bot traffic declines.",
                confidence="High" if sp > 40 else "Medium", evidence=ev_static)

    # ── D: INDEXABILITY ─────────────────────────────────────────────────────
    lv_urls = [u for u in url_hits if any(p in u.lower() for p in LOW_VALUE_PATTERNS)]
    if lv_urls:
        lv_total = sum(url_hits[u] for u in lv_urls)
        lv_pct = lv_total / max(automated_total, 1) * 100
        if lv_pct > 10 and len(lv_urls) > 5:
            # Medium confidence on purpose: some sites intentionally rank /tag/
            # and /author/ pages. Confirm in GSC before applying noindex.
            ev_lv = (f"Verified: {len(lv_urls)} URLs matching {LOW_VALUE_PATTERNS}; "
                     f"{lv_total:,} bot hits = {lv_pct:.1f}% of bot traffic. Confirm SEO "
                     f"value in GSC before applying noindex.")
            add("Crawl Budget", "Low-Value Taxonomy Pages Over-Crawled",
                f"{len(lv_urls)} taxonomy/pagination URLs received {lv_total:,} automated "
                f"hits ({lv_pct:.1f}% of bot traffic). Tag archives, author pages and deep "
                f"pagination are low-value crawl targets.",
                f"{len(lv_urls)} URLs: /tag/, /author/, /page/, /feed/", "Bots", "Mixed",
                lv_total, "P2 - High",
                "Tag archives, author pages and paginated archives are being crawled "
                "without noindex, consuming budget that should go to money pages.",
                "Crawl budget diverted from content that converts. Thin, near-duplicate "
                "archive pages may enter the index. Reduces crawl frequency of key pages.",
                "1. Yoast > Search Appearance > Taxonomies > Tags > \"Show in search "
                "results\" OFF (adds noindex).\n"
                "2. Yoast > Search Appearance > Archives > Author archives > No, unless "
                "authors have unique bios.\n"
                "3. For paginated archives beyond page 2, add noindex,follow.\n"
                "4. Check GSC > Performance > Pages filtered to /tag/ and /author/ — if "
                "zero impressions, safe to noindex.\n"
                "5. Regenerate the sitemap after adding noindex.",
                "1-2 hrs",
                "GSC > Coverage > Excluded > \"Excluded by noindex tag\" rises.\n"
                "Re-run log analysis in 2 weeks > /tag/ and /author/ bot hits drop.\n"
                "GSC indexed URL count stays stable (only thin pages removed).",
                confidence="Medium", evidence=ev_lv)

    for u in [x for x in url_hits if "/robots.txt" in x]:
        sc = url_status.get(u, {})
        bad_codes = [c for c in (404, 500, 502, 503) if sc.get(c, 0) > 0]
        if not bad_codes:
            continue
        url_total_rob = url_hits[u] or 1
        bad_hits = sum(sc.get(c, 0) for c in bad_codes)
        bad_share = bad_hits / url_total_rob
        # Gate: a single transient error isn't site-wide blocking. Persistent, or
        # any 5xx (Google's harshest case), qualifies.
        if not (bad_share >= 0.10 or any(c >= 500 for c in bad_codes)):
            continue
        conf_rob = ("High" if (bad_share >= 0.50 or any(c >= 500 for c in bad_codes))
                    else "Medium")
        urg_rob = "P1 - Critical" if any(c >= 500 for c in bad_codes) else "P2 - High"
        ev_rob = (f"Verified: robots.txt returned {bad_codes} on {bad_hits} of "
                  f"{url_total_rob} requests ({bad_share*100:.0f}%); a 5xx triggers a "
                  f"full-site crawl halt.")
        add("Indexability", "robots.txt Returning Error",
            f"robots.txt returned {bad_codes}. A 5xx on robots.txt makes Googlebot treat "
            f"the ENTIRE site as blocked and stop crawling immediately.",
            u, seg_label(u), str(bad_codes), url_hits[u], urg_rob,
            "The robots.txt at the domain root is missing or erroring. This is the most "
            "severe crawlability failure — it gates ALL search access to the site.",
            "If robots.txt returns 5xx, Googlebot assumes the whole site is disallowed and "
            "stops crawling. Pages drop from the index within days.",
            "1. Open https://DOMAIN/robots.txt right now and confirm whether it loads.\n"
            "2. If 404: create it at the web root with at minimum:\n"
            "   User-agent: *\n   Allow: /\n   Sitemap: https://DOMAIN/sitemap.xml\n"
            "3. If 500: check file permissions (644) and, if it is generated dynamically, "
            "the generating plugin.\n"
            "4. Validate in GSC > Settings > robots.txt > no errors.\n"
            "5. Test the key URLs in the tester.\n"
            "6. GSC > URL Inspection > homepage > Request Indexing.",
            "15-30 min",
            "curl -I https://DOMAIN/robots.txt > must return HTTP 200.\n"
            "GSC robots.txt report shows the file contents with no errors.\n"
            "GSC > Crawl Stats > requests/day resume within 3-5 days.",
            confidence=conf_rob, evidence=ev_rob)

    for u in [x for x in url_hits if "sitemap" in x.lower()]:
        sc = url_status.get(u, {})
        bad_codes = [c for c in (404, 500, 502, 503) if sc.get(c, 0) > 0]
        if not bad_codes:
            continue
        url_total_sit = url_hits[u] or 1
        bad_hits_sit = sum(sc.get(c, 0) for c in bad_codes)
        bad_share_sit = bad_hits_sit / url_total_sit
        if not (bad_share_sit >= 0.10 or any(c >= 500 for c in bad_codes)):
            continue
        conf_sit = ("High" if (bad_share_sit >= 0.50 or any(c >= 500 for c in bad_codes))
                    else "Medium")
        ev_sit = (f"Verified: {u} returned {bad_codes} on {bad_hits_sit} of "
                  f"{url_total_sit} requests ({bad_share_sit*100:.0f}%).")
        add("Indexability", "Sitemap Returning Error",
            f"Sitemap returned {bad_codes}. Crawlers cannot discover pages through it, so "
            f"new content will not be indexed promptly.",
            u, seg_label(u), str(bad_codes), url_hits[u], "P2 - High",
            "The XML sitemap is missing or the server errors on this path.",
            "New and updated pages take far longer to be discovered. Time-sensitive "
            "content may not rank for days or weeks after publication.",
            "1. Open the sitemap URL in a browser to see the exact error.\n"
            "2. WP + Yoast: SEO > General > Features > XML sitemaps > toggle off/on, then "
            "load /sitemap_index.xml.\n"
            "3. Validate the XML structure.\n"
            "4. Ensure the sitemap excludes noindexed, 404, redirecting and protected URLs.\n"
            "5. GSC > Sitemaps: remove the failing entry, submit the correct URL.\n"
            "6. Reference it in robots.txt: Sitemap: https://DOMAIN/sitemap.xml",
            "30-60 min",
            "curl -I [sitemap URL] > must return 200.\n"
            "GSC > Sitemaps > status \"Success\" with a non-zero URL count.\n"
            "GSC > Coverage > submitted-and-indexed trends up within 1-2 weeks.",
            confidence=conf_sit, evidence=ev_sit)

    # Trailing-slash duplicates
    url_set = set(url_hits)
    seen_dupes = set()
    for u in url_set:
        if not (u.endswith("/") and u[:-1] in url_set) or u in seen_dupes:
            continue
        seen_dupes.add(u)
        h1, h2 = url_hits[u], url_hits[u[:-1]]
        sc_u = url_status.get(u, {})
        sc_ns = url_status.get(u[:-1], {})
        redir_u = sc_u.get(301, 0) / max(h1, 1)
        redir_ns = sc_ns.get(301, 0) / max(h2, 1)
        # Gate: if either variant already 301s in >80% of cases, canonicalisation
        # is working — reporting it would be a false positive.
        if redir_u > 0.8 or redir_ns > 0.8:
            continue
        ev_dup = (f"Verified: both URLs serve non-redirect responses "
                  f"(slash:{int(redir_u*100)}% / no-slash:{int(redir_ns*100)}% 301 share); "
                  f"no canonical redirect in place.")
        add("Indexability", "Trailing Slash Duplicate URLs",
            f"Both \"{u}\" and \"{u[:-1]}\" are receiving traffic. The server returns "
            f"content on both without a canonical or redirect.",
            f"{u}  AND  {u[:-1]}", "All", "Mixed", h1 + h2, "P2 - High",
            "The server responds on both the trailing-slash and non-slash version without "
            "redirecting or canonicalising.",
            "Duplicate content in the index. PageRank split across two URL versions. GSC "
            "shows both with divided click and impression data.",
            "1. Choose one canonical form and apply it site-wide.\n"
            "2. 301 the non-canonical to the canonical:\n"
            "   nginx (strip slash): rewrite ^/(.*)/$ /$1 permanent;\n"
            "   .htaccess (add slash): RewriteRule ^(.*[^/])$ /$1/ [R=301,L]\n"
            "3. Add a canonical tag on both variants as a safety net.\n"
            "4. Update all internal links to the canonical form.",
            "30-90 min",
            "curl -Iv [non-canonical] > 301 to the canonical.\n"
            "curl -Iv [canonical] > 200.\n"
            "Screaming Frog > Canonicals > both URLs share one canonical href.",
            confidence="High", evidence=ev_dup)

    # ── E: PERFORMANCE ──────────────────────────────────────────────────────
    # Gate: 500KB is large but not SEO-critical, and Googlebot's cutoff is 15MB.
    # Flag where transfer cost genuinely hurts LCP/INP (>=750KB average HTML).
    big = []
    for u, hits in url_hits.items():
        if classify_content(u) != "HTML":
            continue
        avg = url_bytes.get(u, 0) / max(hits, 1)
        if avg > 750_000:
            big.append((u, avg, hits))
    for u, avg, hits in sorted(big, key=lambda x: -x[1])[:10]:
        size_kb = int(avg / 1024)
        add("Performance", "Oversized HTML Page",
            f"Average HTML response size is {size_kb}KB. Pages above ~750KB harm LCP/INP "
            f"on mobile. Googlebot truncates at 15MB so indexing still works, but ranking "
            f"suffers.",
            u, seg_label(u), url_last_status.get(u, 0), hits, "P3 - Monitor",
            "Page HTML is excessively large. Common causes: huge inline JSON-LD blocks, "
            "unminified HTML, thousands of DOM nodes, inline SVG, embedded data URIs.",
            "Googlebot may not parse content below the fold, leaving indexed content "
            "incomplete. Slower TTFB and LCP hurt Core Web Vitals. Higher bandwidth per crawl.",
            "1. Enable Brotli (preferred) or gzip — cuts transfer 70-80%:\n"
            "   nginx: brotli on; brotli_comp_level 6; brotli_types text/html;\n"
            "2. Measure real transfer: curl -H \"Accept-Encoding: br\" -o /dev/null -s "
            "-w \"%{size_download}\" [URL]\n"
            "3. Minify HTML output.\n"
            "4. Move large JSON-LD blocks to an external file.\n"
            "5. Audit DOM size in Lighthouse — target <1,500 nodes.\n"
            "6. Add loading=\"lazy\" to below-fold images and iframes.",
            "2-4 hrs",
            "curl -H \"Accept-Encoding: br\" ... > should be <100,000 bytes.\n"
            "DevTools > Network > document transferred size.\n"
            "GSC > Core Web Vitals > LCP improves after compression.",
            confidence="High" if size_kb > 1500 else "Medium",
            evidence=f"Verified: average response body for this URL is {size_kb}KB "
                     f"across {hits} hits.")

    # ── F: SECURITY ─────────────────────────────────────────────────────────
    sensitive_re = _sensitive_regexes()
    for u, hits in url_hits.items():
        for kw, kw_desc in SENSITIVE_FILES:
            rx = sensitive_re.get(kw)
            # Boundary-anchored so '.env' cannot match /environmental-impact.
            if rx is None or not rx.search(u):
                continue
            sc = url_status.get(u, {})
            is_exposed = any(sc.get(c, 0) > 0 for c in (200, 206))
            n_probe = sum(sc.get(c, 0) for c in (403, 404))
            ev_sens = (f"Verified: URL matches the strict pattern for {kw}; status mix = "
                       f"{dict(sc)}.")
            conf_sens = "High" if (is_exposed or n_probe >= 5) else "Medium"
            add("Security",
                f"Sensitive File {'EXPOSED (200)' if is_exposed else 'Probed'}: {kw}",
                (f"CRITICAL: the file is publicly accessible (HTTP 200). " if is_exposed
                 else f"File probing detected — currently returning "
                      f"{url_last_status.get(u, 0)}. ") + f"File type: {kw_desc}.",
                u, seg_label(u), url_last_status.get(u, 0), hits,
                "P1 - Critical" if is_exposed else "P2 - High",
                (f"A sensitive file is publicly accessible over HTTP. {kw_desc}."
                 if is_exposed else
                 f"Automated bots are probing for sensitive files — standard "
                 f"reconnaissance before a targeted attack. {kw_desc}."),
                ("ACTIVE DATA BREACH RISK. Credentials, source code or user data may "
                 "already be stolen. Immediate rotation of every secret in this file is "
                 "required." if is_exposed else
                 "Probing indicates active targeting. Ensure the block is robust at every "
                 "server path and CDN layer."),
                ("IMMEDIATE ACTIONS:\n"
                 "1. Move the file outside the web root.\n"
                 "2. Rotate ALL credentials it contained (DB password, API keys, salts).\n"
                 f"3. Audit access: grep \"{kw}\" /var/log/nginx/access.log | sort | "
                 f"uniq -c | sort -rn\n"
                 "4. Block the path at server level (nginx AND .htaccess):\n"
                 "   nginx: location ~ /\\.env { deny all; return 403; }\n"
                 "5. Enable the WAF's sensitive-file-access managed rules.\n"
                 "6. A robots.txt Disallow is an obscurity layer only, never the fix."
                 if is_exposed else
                 "1. Verify the block: curl -I [URL] > must return 403 or 404, never 200.\n"
                 "2. Add a server-level deny rule for this path (nginx and .htaccess).\n"
                 "3. Enable the WAF OWASP Core Rule Set sensitive-file rules.\n"
                 "4. Add a robots.txt Disallow as an additional signal.\n"
                 "5. If probing persists from specific IPs, block them at the CDN."),
                "Immediate (P1) / 30 min (P2)",
                "curl -I [URL] > must return 403 or 404.\n"
                + ("MANDATORY: request a full access-log export from the host to scope the "
                   "breach." if is_exposed else
                   "Re-run log analysis in 1 week > probe attempts return 403/404 only."),
                confidence=conf_sens, evidence=ev_sens)
            break

    # ── G0: MOBILE-FIRST INDEXING SPLIT ─────────────────────────────────────
    gb_total = agg["google_total"]
    gb_mobile = agg["google_mobile_total"]
    if gb_total >= 50 and agg["has_ua_data"]:
        gb_mobile_pct = gb_mobile / gb_total * 100
        if gb_mobile_pct < 50:
            ev_mfi = (f"Verified: Googlebot Smartphone = {gb_mobile} of {gb_total} "
                      f"({gb_mobile_pct:.0f}%); mobile-first indexing expects >80%.")
            add("Indexability", "Googlebot Mobile-First Imbalance",
                f"Only {gb_mobile_pct:.0f}% of Googlebot crawls came from the smartphone "
                f"agent. Mobile-first indexing expects >80%.",
                "Site-wide", "Search Bots", "Mixed", gb_mobile,
                "P2 - High" if gb_mobile_pct < 30 else "P3 - Monitor",
                "Possible causes: (1) the site is not on mobile-first indexing, (2) "
                "robots.txt blocks Googlebot Smartphone, (3) the server returns different "
                "content or status for the smartphone UA (cloaking risk), (4) responsive "
                "design is missing or broken on mobile.",
                "Desktop-only crawl signals miss the mobile rendering Google actually "
                "ranks. Pages may rank on desktop content while mobile content is ignored.",
                "1. GSC > Settings > About > Indexing crawler — confirm \"Googlebot "
                "smartphone\".\n"
                "2. GSC > robots.txt test with the smartphone UA on critical URLs.\n"
                "3. Fetch with the mobile Googlebot UA via curl -A and confirm 200 with "
                "the same HTML as desktop.\n"
                "4. GSC > URL Inspection > Test Live URL > rendered mobile HTML matches "
                "desktop content.\n"
                "5. If a separate m. subdomain exists, verify rel=alternate/canonical.\n"
                "6. A 10-20% desktop share is normal validation crawling.",
                "30-60 min investigation + variable fix time",
                "GSC > Crawl Stats > By Googlebot type > Smartphone >80% of total.\n"
                "GSC URL Inspection shows Googlebot smartphone as the indexing crawler.\n"
                "Re-run log analysis in 1-2 weeks > smartphone share trending up.",
                confidence="High" if gb_total >= 200 else "Medium", evidence=ev_mfi)

    # ── G: GOOGLEBOT PRESENCE ───────────────────────────────────────────────
    search_engine_total = class_counts.get("search_bot", 0)
    gb, denom, ctx = None, 0, ""
    if search_engine_total >= 20:
        gb, denom, ctx = gb_total, search_engine_total, "verified search-engine bot traffic"
    elif automated_total > 50 and agg["has_ua_data"]:
        gb, denom, ctx = gb_total, automated_total, "automated traffic"
    if gb is not None and denom and (gb / denom * 100) < 10:
        gb_pct = gb / denom * 100
        # Gate: a short sample can show an artificially low Googlebot share
        # because crawl is bursty — downgrade confidence, don't cry wolf.
        span_h = agg.get("span_hours")
        sample_caveat, conf_gb, urg_gb = "", "High", "P2 - High"
        if span_h is not None and span_h < 48:
            sample_caveat = (f" Sample period is only {span_h:.0f}h — Googlebot crawl is "
                             f"bursty so this may not reflect the steady-state rate.")
            conf_gb, urg_gb = "Low", "P3 - Monitor"
        ev_gb = (f"Verified: Googlebot = {gb} of {denom:,} {ctx} ({gb_pct:.1f}%); sample "
                 f"span = {f'{span_h:.0f}h' if span_h is not None else 'unknown'}."
                 f"{sample_caveat}")
        add("Indexability", "Low Googlebot Activity",
            f"Googlebot is only {gb_pct:.1f}% of {ctx} ({gb} hits out of {denom:,} "
            f"relevant requests). Expected: >20% on a healthy, actively-crawled site.",
            "Site-wide", "Search Bots", "N/A", gb,
            "P1 - Critical" if gb_pct < 2 else urg_gb,
            "Google has reduced its crawl rate. Common causes: robots.txt blocking "
            "Googlebot; persistent server errors during crawl windows; slow response times "
            "causing Googlebot to back off; low authority/freshness signals; a manual action.",
            "Fewer pages indexed. New and updated content takes days or weeks longer to "
            "appear. Ranking ability throttled — Google cannot re-evaluate improved pages "
            "promptly.",
            "1. Check robots.txt now: curl https://DOMAIN/robots.txt | grep -i disallow — "
            "look for Disallow: / which would block everything.\n"
            "2. GSC > Settings > Crawl Stats: average response time (<500ms), requests/day "
            "trend, crawl errors.\n"
            "3. GSC > Security & Manual Actions > confirm \"No issues detected\".\n"
            "4. GSC > URL Inspection > homepage > Test Live URL.\n"
            "5. Re-submit the sitemap.\n"
            "6. Request indexing on key pages.\n"
            "7. Fix every P1 in this report first — a faster, cleaner site earns more crawl.",
            "2-4 hrs investigation + ongoing improvements",
            "GSC > Crawl Stats > requests/day trending up over 4 weeks.\n"
            "Re-run log analysis in 2 weeks > Googlebot share increases.\n"
            "GSC > Coverage > indexed URL count trending up.",
            confidence=conf_gb, evidence=ev_gb)

    findings.sort(key=lambda f: (URGENCY_ORDER.get(f["urgency"], 3), -f["hits"]))
    return findings
