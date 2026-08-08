"""Authored content for the Log-File Analysis report.

Claude fills REPORT from `analysis.json` / `facts.md` produced by
analyze_logs.py. Every finding carries issue + evidence + solution + execution;
`evidence` must be a MEASURED number lifted from analysis.json (a hit count, a
status share, a percentage of traffic), never an impression.

Mapping from the engine to these sections:
  detect_issues category   ->  section id
  -----------------------------------------
  HTTP Errors              ->  errors
  Redirects                ->  redirects
  Crawl Budget             ->  budget
  Indexability             ->  indexability
  Performance              ->  performance
  Security, Security/Spam  ->  security
  (crossref block)         ->  coverage
  (authored)               ->  actions

Severity maps from urgency: P1 - Critical -> critical, P2 - High -> high,
P3 - Monitor -> medium. A dimension with nothing wrong gets ONE `good` finding
stating what was checked and what passed — silence is not a result.

Replace every ‹EXAMPLE› row.
"""

REPORT = {
    "title": "Log-File Analysis",
    "client": "‹Client›",
    "period": "‹Period›",
    "subtitle": "What crawlers and visitors actually did on the server — measured "
                "from raw access logs, with an executable fix for each finding.",
    "output_dir": "./Log-Analysis",
    "sections": [
        {"id": "summary", "title": "0 · Crawl Summary",
         "intro": "Volume, window, parse rate, traffic mix, and how much of the bot "
                  "identification was IP-verified rather than UA-trusted.",
         "chart": {"type": "hbars", "title": "‹EXAMPLE› Requests by traffic segment",
                   "data": [["Search Bots", 4820], ["Human", 3110],
                            ["Infrastructure", 1450], ["Generic / AI Bots", 610],
                            ["SEO Crawlers", 240], ["Suspicious", 90]]},
         "findings": []},

        {"id": "errors", "title": "1 · HTTP Errors (4xx / 5xx)",
         "intro": "Errors crawlers actually received. A status Googlebot saw is an "
                  "indexing event; the same status seen only by humans is link "
                  "hygiene — the evidence line says which.",
         "findings": [
            {"issue": "‹EXAMPLE› Googlebot received 404 on /old-service-page/",
             "sev": "high",
             "evidence": "Googlebot hit this URL 3 times and got 404 each time; 11 "
                         "total 404s across all agents; URL purpose = content.",
             "solution": "301 the URL to the closest live page, or return 410 if it "
                         "was retired deliberately.",
             "execution": "Add the 301 in .htaccess; remove the URL from sitemap.xml; "
                          "fix the 4 internal links listed in the URL Detail tab.\n"
                          "Verify: curl -I returns 301; GSC Not Found clears in 1-2 weeks.",
             "effort": "S", "priority": "P0"},
         ]},

        {"id": "redirects", "title": "2 · Redirects & Chains",
         "intro": "301s still being crawled (stale internal links), 302s on content "
                  "URLs, and multi-hop chains. Auth and checkout 302s are excluded — "
                  "those are correct behaviour.",
         "findings": []},

        {"id": "budget", "title": "3 · Crawl Budget Waste",
         "intro": "Where crawl was spent instead of on money pages: backend/admin "
                  "endpoints, parameter explosions, static assets, taxonomy archives, "
                  "and internal platform traffic.",
         "findings": []},

        {"id": "indexability", "title": "4 · Indexability & Discovery",
         "intro": "robots.txt and sitemap health, trailing-slash duplicates, the "
                  "mobile-first crawl split, and overall Googlebot presence.",
         "findings": []},

        {"id": "performance", "title": "5 · Performance",
         "intro": "Response weight as the server actually served it — bytes on the "
                  "wire, not a lab estimate.",
         "findings": []},

        {"id": "security", "title": "6 · Security & Suspicious Traffic",
         "intro": "Sensitive-file exposure and probing, plus high-volume IPs that "
                  "survived the admin/polling gate. Logged-in admin and PWA traffic is "
                  "deliberately excluded — it is not scraping.",
         "findings": []},

        {"id": "coverage", "title": "7 · Crawl Coverage (Sitemap / GSC)",
         "intro": "What the log does NOT contain: sitemap URLs never crawled in this "
                  "window, and pages earning impressions that Googlebot did not "
                  "revisit. Include only when a sitemap or GSC export was supplied.",
         "findings": []},

        {"id": "actions", "title": "8 · Action Items",
         "intro": "P0 crawl-blocking and security · P1 budget and redirects · P2 "
                  "monitoring. Owner and verification step on every line.",
         "findings": []},
    ],
}
