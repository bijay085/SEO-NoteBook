"""Authored content for the Affiliate & Review Audit.

Claude fills REPORT from fetch_affiliate_links.py + live reads. Every finding
carries issue+evidence+solution+execution. Replace the ‹EXAMPLE› rows.
The full outbound-link inventory is emitted as its own section/tab.
"""

REPORT = {
    "title": "Affiliate & Review Audit",
    "client": "‹Client›",
    "period": "‹Period›",
    "subtitle": "Affiliate-link integrity, disclosure, review voice and schema — "
                "each finding measured, with an executable fix.",
    "output_dir": "./Affiliate-Audit",
    "sections": [
        {"id": "links", "title": "1 · Affiliate-Link Integrity",
         "intro": "Per outbound link: rel, destination health, network. Full inventory below.",
         "chart": {"type": "bars", "title": "‹EXAMPLE› rel coverage across affiliate links",
                   "data": [["Tagged (sponsored/nofollow)", 128], ["Untagged", 445]]},
         "table": {"cols": ["Page", "Anchor", "Destination", "rel", "Verdict"],
                   "rows": [["‹EXAMPLE› /best-blenders", "\"check price\"",
                             "amazon.com/…", "(none)", "Add-rel"]]},
         "findings": [
            {"issue": "‹EXAMPLE› 445 affiliate links still lack rel=\"sponsored\" after the tag task",
             "sev": "critical",
             "evidence": "445 outbound affiliate <a> carry rel=\"\" (task log marked "
                         "\"tagging done\" — this is a regression).",
             "solution": "Add rel=\"sponsored nofollow\" to every monetised outbound link.",
             "execution": "1. Filter inventory tab -> Verdict = Add-rel\n"
                          "2. Bulk-update via the link plugin / template partial\n"
                          "3. Re-crawl; confirm 0 untagged\n"
                          "Verify: rel coverage chart reads 100%.",
             "effort": "M", "priority": "P0"},
         ]},
        {"id": "tracking", "title": "2 · Monetization Tracking & Attribution",
         "intro": "GTM/GA containers, outbound-click event, sub-ID/UTM on affiliate URLs.",
         "findings": []},
        {"id": "disclosure", "title": "3 · FTC / Affiliate Disclosure",
         "intro": "Is a disclosure present, on-page, above the first affiliate link?",
         "findings": [
            {"issue": "‹EXAMPLE› Review pages disclose in the footer only",
             "sev": "high",
             "evidence": "/best-blenders places disclosure in the footer, below 6 affiliate links.",
             "solution": "Add an on-page disclosure line directly above the first affiliate link.",
             "execution": "Paste above first link: \"We earn a commission if you buy "
                          "through our links, at no cost to you.\"\nVerify: line renders "
                          "above the fold on mobile.",
             "effort": "S", "priority": "P1"},
         ]},
        {"id": "voice", "title": "4 · Review Voice (archetype-aware)",
         "intro": "Classify each page, judge first-hand-experience signals per archetype.",
         "findings": []},
        {"id": "scoring", "title": "5 · Rating / Score-System Scope",
         "intro": "Is the score applied only to genuine reviews, with a stated rubric?",
         "findings": []},
        {"id": "schema", "title": "6 · Review & Product Schema",
         "intro": "Review / Product / itemReviewed / AggregateRating validity + honesty.",
         "findings": []},
        {"id": "cta", "title": "7 · Affiliate-CTA Conversion Path",
         "intro": "Is the money CTA present, above the fold, and mobile-surviving?",
         "findings": []},
        {"id": "actions", "title": "8 · Action Items",
         "intro": "Consolidated, weighted by revenue/traffic × severity; regressions first.",
         "findings": [
            {"issue": "‹EXAMPLE› Fix the 445-link rel regression",
             "sev": "critical", "evidence": "See §1.",
             "solution": "Bulk re-tag; add a lint check so it can't regress again.",
             "execution": "Owner: dev. This week. Add CI check for untagged affiliate links.",
             "effort": "M", "priority": "P0"},
         ]},
    ],
}
