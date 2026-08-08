#!/usr/bin/env python3
"""Render the A-F findings report from findings.json (+ optional metrics.json),
reusing report_kit. Usage: python build_report.py findings.json [metrics.json] [out.html]
findings.json: {"client","period","summary","findings":[{rule_id,scope,element,
  verdict,severity,observed,expected,consequence,solution,execution,evidence_basis}]}"""
import sys, json, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from report_kit import render_html
from collections import Counter

def main():
    if len(sys.argv)<2: print(__doc__); return 2
    F=json.load(open(sys.argv[1])); 
    metrics=json.load(open(sys.argv[2])) if len(sys.argv)>2 and sys.argv[2].endswith(".json") else {}
    out=next((a for a in sys.argv[2:] if a.endswith(".html")), "Accessibility-Completeness-Report.html")
    fs=F.get("findings",[])
    vc=Counter((f.get("verdict") or "n/a").title() for f in fs)
    def card(f):
        sev=(f.get("severity") or "info").lower()
        return {"issue":f'{f.get("rule_id","")} — {f.get("observed") or f.get("expected","")}',
                "sev":sev,"evidence":f.get("observed",""),
                "solution":f.get("solution",""),
                "execution":f.get("execution") or f.get("expected",""),
                "priority":f.get("verdict","")}
    dom=""
    if metrics: dom=(f'DOM {metrics.get("dom_node_count","?")} nodes '
                     f'(depth {metrics.get("max_depth","?")}, verdict {metrics.get("dom_verdict","?")}).')
    REPORT={"title":"Accessibility & Completeness Audit","client":F.get("client","Client"),
      "period":F.get("period",""),"subtitle":F.get("summary",""),
      "output_dir":os.path.dirname(out) or ".",
      "sections":[
        {"id":"a","title":"A · Audit summary","intro":(F.get("summary","")+" "+dom).strip(),"findings":[]},
        {"id":"b","title":"B · Verdict counts","intro":"Rule outcomes.",
         "chart":{"type":"bars","title":"Findings by verdict","data":[[k,v] for k,v in vc.items()]},
         "findings":[]},
        {"id":"c","title":"C · Rule-level findings","intro":"Each rule with Issue · Evidence · Solution · Execution.",
         "findings":[card(f) for f in fs]},
        {"id":"d","title":"D · Prioritized repair plan","intro":"Fails and warnings first.",
         "table":{"cols":["Rule","Severity","Solution"],
                  "rows":[[f.get("rule_id"),f.get("severity"),f.get("solution","")[:80]]
                          for f in fs if (f.get("verdict") or "").lower() in ("fail","partial","warn")]}},
        {"id":"e","title":"E · Validation record","intro":"How each finding was verified.",
         "table":{"cols":["Rule","Evidence basis","Verdict"],
                  "rows":[[f.get("rule_id"),f.get("evidence_basis",""),f.get("verdict","")] for f in fs]}},
        {"id":"f","title":"F · Closing statement",
         "intro":"Every number measured or quoted; no unverified claim asserted as standard.","findings":[]},
      ]}
    html=render_html(REPORT); open(out,"w",encoding="utf-8").write(html)
    print(f"wrote {out} ({len(html):,} bytes, {len(fs)} findings)")
    return 0
if __name__=="__main__": raise SystemExit(main())
