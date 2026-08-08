#!/usr/bin/env python3
"""Build the REQUIRED annotated wireframe (Miro-or-equivalent SVG) from a region list.
Usage: python build_wireframe.py regions.json [out.svg]
regions.json: {"page_type":"Service","regions":[{"name","tag","rule","instruction"},...]}
Emits an SVG wireframe with the semantic tag on each region + a QA checklist tied to rule IDs."""
import sys, json, os, html as H

def esc(x): return H.escape(str(x if x is not None else ""))
def main():
    if len(sys.argv)<2: print(__doc__); return 2
    d=json.load(open(sys.argv[1])); out=sys.argv[2] if len(sys.argv)>2 else "wireframe.svg"
    regs=d.get("regions",[]); pt=d.get("page_type","Page")
    W,rh,gap,top=760,54,10,88; H_=top+len(regs)*(rh+gap)+40+len(regs)*16
    y=top; boxes=[f'<rect x="0" y="0" width="{W}" height="{H_}" fill="#FFFFFF"/>',
        f'<rect x="0" y="0" width="{W}" height="56" fill="#0A0A0A"/>',
        f'<rect x="0" y="56" width="{W}" height="4" fill="#F5C518"/>',
        f'<text x="20" y="26" fill="#F5C518" font-family="system-ui" font-weight="800" font-size="15">SEO</text>',
        f'<text x="20" y="46" fill="#fff" font-family="system-ui" font-size="12">Wireframe : {esc(pt)} page (annotated semantic structure)</text>']
    for r in regs:
        boxes.append(f'<rect x="20" y="{y}" width="{W-40}" height="{rh}" rx="6" fill="#FCFCF9" stroke="#0A0A0A" stroke-width="1.2"/>')
        boxes.append(f'<text x="34" y="{y+22}" font-family="system-ui" font-weight="700" font-size="13">{esc(r.get("name"))}</text>')
        boxes.append(f'<text x="34" y="{y+40}" font-family="ui-monospace,monospace" font-size="12" fill="#B8890A">&lt;{esc(r.get("tag","div"))}&gt;</text>')
        if r.get("rule"): boxes.append(f'<text x="{W-40}" y="{y+22}" text-anchor="end" font-family="system-ui" font-size="11" fill="#6B6B63">{esc(r.get("rule"))}</text>')
        if r.get("instruction"): boxes.append(f'<text x="{W-40}" y="{y+40}" text-anchor="end" font-family="system-ui" font-size="11" fill="#6B6B63">{esc(r.get("instruction"))[:70]}</text>')
        y+=rh+gap
    y+=8; boxes.append(f'<text x="20" y="{y}" font-family="system-ui" font-weight="800" font-size="13">QA checklist (rule-linked)</text>'); y+=20
    for r in regs:
        boxes.append(f'<text x="24" y="{y}" font-family="system-ui" font-size="12">&#9744; {esc(r.get("rule",""))} : {esc(r.get("name"))} uses &lt;{esc(r.get("tag","div"))}&gt;</text>'); y+=16
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {y+10}" width="{W}">{"".join(boxes)}</svg>'
    open(out,"w",encoding="utf-8").write(svg); print(f"wrote {out} ({len(regs)} regions, {len(svg):,} bytes)")
    return 0
if __name__=="__main__": raise SystemExit(main())
