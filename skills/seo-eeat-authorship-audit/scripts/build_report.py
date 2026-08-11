#!/usr/bin/env python3
"""Render the A-F E-E-A-T & Authorship findings report from findings.json (+ optional
metrics.json from measure.py), reusing report_kit.
Usage: python build_report.py findings.json [metrics.json] [out.html]
findings.json: {"client","period","summary","findings":[{rule_id,checklist_ref,pillar,
  scope,element,verdict,severity,observed,expected,consequence,solution,execution,
  evidence_basis,check_type}]}"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "shared"))
from report_kit import render_html
from collections import Counter

PILLAR_TITLES = {
    "trust": "Trust", "authorship": "Authorship", "experience": "Experience",
    "expertise": "Expertise", "authoritativeness": "Authoritativeness",
    "helpful-content": "Helpful / People-First", "schema": "Schema & Structured Data",
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    F = json.load(open(sys.argv[1]))
    metrics = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and sys.argv[2].endswith(".json") else {}
    out = next((a for a in sys.argv[2:] if a.endswith(".html")), "EEAT-Authorship-Report.html")
    fs = F.get("findings", [])
    vc = Counter((f.get("verdict") or "n/a").title() for f in fs)
    sev_fail = Counter((f.get("severity") or "info") for f in fs if (f.get("verdict") or "").lower() in ("fail", "partial"))

    def card(f):
        sev = (f.get("severity") or "info").lower()
        tag = f' [{f.get("evidence_basis")}]' if f.get("evidence_basis") == "Interpretation" else ""
        return {
            "issue": f'{f.get("rule_id", "")} ({f.get("checklist_ref", "")}) : {f.get("element") or f.get("expected", "")}{tag}',
            "sev": sev, "evidence": f.get("observed", ""),
            "solution": f.get("solution", ""),
            "execution": f.get("execution") or f.get("consequence", ""),
            "priority": f.get("verdict", ""),
        }

    det = ""
    if metrics:
        b = metrics.get("byline", {}); ps = metrics.get("person_schema", {})
        det = (f'Deterministic scan: byline {"found" if b.get("text") else "not found"}'
               f'{" (looks suspicious)" if b.get("looks_suspicious") else ""}, '
               f'Person schema {"present" if ps.get("present") else "absent"} '
               f'(sameAs x{ps.get("sameAs_count", 0)}), '
               f'HTTPS {"yes" if metrics.get("https") else "no/unknown"}.')

    by_pillar = {}
    for f in fs:
        by_pillar.setdefault(f.get("pillar", "other"), []).append(f)

    pillar_sections = []
    for slug, title in PILLAR_TITLES.items():
        items = by_pillar.get(slug, [])
        if not items:
            continue
        pv = Counter((f.get("verdict") or "n/a").title() for f in items)
        pillar_sections.append({
            "id": f"pillar-{slug}", "title": f"{title} ({len(items)} checks)",
            "intro": ", ".join(f"{v} {k}" for k, v in pv.items()),
            "chart": {"type": "bars", "title": f"{title} verdicts", "data": [[k, v] for k, v in pv.items()]},
            "findings": [card(f) for f in items],
        })

    REPORT = {
        "title": "E-E-A-T & Authorship Audit", "client": F.get("client", "Client"),
        "period": F.get("period", ""), "subtitle": F.get("summary", ""),
        "output_dir": os.path.dirname(out) or ".",
        "sections": [
            {"id": "a", "title": "A · Audit summary", "intro": (F.get("summary", "") + " " + det).strip(), "findings": []},
            {"id": "b", "title": "B · Verdict counts", "intro": "All rule outcomes across every pillar.",
             "chart": {"type": "bars", "title": "Findings by verdict", "data": [[k, v] for k, v in vc.items()]},
             "findings": []},
            *pillar_sections,
            {"id": "d", "title": "D · Prioritized repair plan", "intro": "Critical and High first.",
             "table": {"cols": ["Rule", "Checklist ref", "Severity", "Solution"],
                       "rows": [[f.get("rule_id"), f.get("checklist_ref"), f.get("severity"), f.get("solution", "")[:90]]
                                for f in sorted(fs, key=lambda x: {"Critical": 0, "High": 1, "Medium": 2, "Avoid": 3}.get(x.get("severity"), 9))
                                if (f.get("verdict") or "").lower() in ("fail", "partial")]}},
            {"id": "e", "title": "E · Validation record", "intro": "How each finding was checked, and its evidence basis.",
             "table": {"cols": ["Rule", "Check type", "Evidence basis", "Verdict"],
                       "rows": [[f.get("rule_id"), f.get("check_type"), f.get("evidence_basis"), f.get("verdict")] for f in fs]}},
            {"id": "f", "title": "F · Closing statement",
             "intro": ("Every number measured (scripts/measure.py) or read directly from the page; "
                       "no Interpretation-graded rule is reported as a Google requirement. "
                       f"Severity summary: {dict(sev_fail)}."), "findings": []},
        ],
    }
    html = render_html(REPORT)
    open(out, "w", encoding="utf-8").write(html)
    print(f"wrote {out} ({len(html):,} bytes, {len(fs)} findings, {len(pillar_sections)} pillars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
