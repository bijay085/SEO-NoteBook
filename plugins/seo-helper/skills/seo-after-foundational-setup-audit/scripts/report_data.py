"""Authored content for the After-Foundational-Setup Deep Audit.

Claude fills REPORT at run time from the measured data (fetch_pages.py, GSC,
Lighthouse). Every finding MUST carry issue+evidence+solution+execution.
The examples below (issue starts with "‹EXAMPLE›") show the schema : replace them.
build_html.py and build_xlsx.py import this module and render at parity.
"""

REPORT = {
    "title": "Deep Audit",
    "client": "‹Client›",
    "period": "‹Period›",
    "subtitle": "Page-by-page forensic SEO, technical, content and performance "
                "audit : every finding measured, with an executable fix.",
    "output_dir": "./Deep-Audit",
    "sections": [
        {"id": "gsc", "title": "1 · Live Search Performance (GSC)",
         "intro": "Real 90-day clicks / impressions / CTR / position by page and query.",
         "findings": [
            {"issue": "‹EXAMPLE› Two URLs serve one intent and split impressions",
             "sev": "high",
             "evidence": "/services/ac-repair (1,240 impr, pos 8.2) and "
                         "/ac-repair (610 impr, pos 14.1) both rank for \"ac repair\".",
             "solution": "Consolidate to the higher-impression URL; 301 the weaker one.",
             "execution": "1. 301 /ac-repair -> /services/ac-repair\n"
                          "2. Update internal links to the canonical\n"
                          "3. GSC ▸ URL Inspection ▸ validate\n"
                          "Verify: impressions consolidate on one URL in 2-3 weeks.",
             "effort": "S", "priority": "P1"},
         ]},
        {"id": "perf", "title": "2 · Measured Performance (Lighthouse + CWV)",
         "intro": "Lab scores + Core Web Vitals. State the profile (DataForSEO = desktop).",
         "chart": {"type": "bars", "title": "‹EXAMPLE› Lighthouse (desktop) : homepage",
                   "data": [["Performance", 94], ["Accessibility", 88],
                            ["SEO", 92], ["Best Practices", 83]]},
         "findings": []},
        {"id": "tech", "title": "3 · Technical & Rendering",
         "intro": "Page weight, inline vs external CSS/JS, DOM node count, trackers, forms.",
         "findings": []},
        {"id": "forensic", "title": "4 · Per-Section Forensic Deep-Dive",
         "intro": "DOM / payload broken down per top-level page section.",
         "findings": []},
        {"id": "onpage", "title": "5 · On-Page & Schema",
         "intro": "Titles, meta, H1, and the JSON-LD stack.",
         "findings": []},
        {"id": "contamination", "title": "6 · Content Contamination",
         "intro": "Main-content-only blocks cloned from the wrong product/page.",
         "table": {"cols": ["Page", "Cloned block", "Source page"],
                   "rows": [["‹EXAMPLE› /heating", "\"Our AC tune-up panel\"", "/ac-repair"]]},
         "findings": []},
        {"id": "duplication", "title": "7 · Duplication / Templating",
         "intro": "Verbatim sentences and cross-page templated ratio.",
         "findings": []},
        {"id": "location", "title": "8 · Location / Doorway-Page Uniqueness",
         "intro": "Are city pages unique, or one shell with a swapped token?",
         "findings": []},
        {"id": "cro", "title": "9 · CRO / Conversion Path",
         "intro": "CTAs, form mechanism, mobile survivability.",
         "findings": []},
        {"id": "eeat", "title": "10 · Authorship & E-E-A-T",
         "intro": "Author-box links, /author/ routes, Person/author schema, byline→bio.",
         "findings": []},
        {"id": "actions", "title": "11 · Action Items",
         "intro": "Every finding, prioritised by impression volume × severity.",
         "findings": [
            {"issue": "‹EXAMPLE› Ship the cannibalization 301s",
             "sev": "high", "evidence": "See §1 : one duplicate intent confirmed live in GSC.",
             "solution": "Apply the consolidation 301 and re-point internal links.",
             "execution": "Owner: dev. Ship in the next release; validate in GSC.",
             "effort": "S", "priority": "P0"},
         ]},
    ],
}
