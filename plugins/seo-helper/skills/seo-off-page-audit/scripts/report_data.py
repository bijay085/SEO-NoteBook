"""Authored content for the Off-Page / Backlink Audit.

Claude fills REPORT from backlink_toxicity.py + DataForSEO/Ahrefs/Semrush.
Every finding carries issue+evidence+solution+execution. disavow.txt is a
third output produced by backlink_toxicity.py. Replace the ‹EXAMPLE› rows.
"""

REPORT = {
    "title": "Off-Page Audit",
    "client": "‹Client›",
    "period": "‹Period›",
    "subtitle": "Backlink profile, anchor distribution, toxicity/disavow and link "
                "gap : measured, with an executable action for each.",
    "output_dir": "./Off-Page-Audit",
    "sections": [
        {"id": "profile", "title": "1 · Inbound Backlink Profile",
         "intro": "Lead with referring domains, not raw links. Authority distribution below.",
         "chart": {"type": "hbars", "title": "‹EXAMPLE› Referring domains by authority (DR)",
                   "data": [["DR 0-20", 240], ["DR 20-40", 96], ["DR 40-60", 38],
                            ["DR 60-80", 11], ["DR 80+", 3]]},
         "findings": []},
        {"id": "anchors", "title": "2 · Anchor-Text Distribution",
         "intro": "Branded / exact / partial / naked / generic vs a natural benchmark.",
         "findings": []},
        {"id": "toxic", "title": "3 · Toxic Backlinks → Disavow",
         "intro": "Multi-source high-confidence set. Disavow only if evidence warrants.",
         "table": {"cols": ["Domain", "Flagged by", "Spam", "Verdict"],
                   "rows": [["‹EXAMPLE› spammy-pbn.ru", "DFS + Ahrefs", "78", "Disavow"],
                            ["‹EXAMPLE› niche-blog.com", "DFS only", "31", "Monitor"]]},
         "findings": [
            {"issue": "‹EXAMPLE› 12 domains flagged toxic by ≥2 sources",
             "sev": "high",
             "evidence": "12 referring domains flagged by ≥2 of {DFS, Ahrefs, Semrush}; "
                         "clear PBN footprint on 9.",
             "solution": "Disavow the multi-source set; monitor single-source flags.",
             "execution": "Search Console ▸ Disavow links ▸ upload disavow.txt (12 domains).\n"
                          "Verify: re-pull spam scores in 30 days.",
             "effort": "S", "priority": "P0"},
         ]},
        {"id": "quality", "title": "4 · Referring-Domain Quality & Relevance",
         "intro": "Sample the top referring domains: relevant? editorial vs directory vs PBN?",
         "findings": []},
        {"id": "outbound", "title": "5 · Outbound External-Link Equity",
         "intro": "Monetised outbound missing rel; dofollow equity leaks to low-value sites.",
         "findings": [
            {"issue": "‹EXAMPLE› Sponsored outbound links missing rel=\"sponsored\"",
             "sev": "medium",
             "evidence": "8 monetised outbound links carry dofollow with no rel.",
             "solution": "Add rel=\"sponsored\" to the monetised outbound set.",
             "execution": "Edit the 8 links (listed in the tab); add rel=\"sponsored\".\n"
                          "Verify: re-crawl shows 0 monetised dofollow.",
             "effort": "S", "priority": "P1"},
         ]},
        {"id": "gap", "title": "6 · Competitive Link Gap",
         "intro": "Referring domains ≥2 competitors have and the client doesn't.",
         "findings": []},
        {"id": "actions", "title": "7 · Action Items",
         "intro": "P0 disavow (iff warranted) · P1 outbound rel · P2 link-gap targets.",
         "findings": [
            {"issue": "‹EXAMPLE› Upload the disavow file",
             "sev": "high", "evidence": "See §3 : 12-domain high-confidence set.",
             "solution": "Upload disavow.txt; schedule a 30-day re-check.",
             "execution": "Owner: SEO. Today. Calendar the re-pull.",
             "effort": "S", "priority": "P0"},
         ]},
    ],
}
