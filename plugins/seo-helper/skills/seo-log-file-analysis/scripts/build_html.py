#!/usr/bin/env python3
"""Render the branded HTML deliverable.

Content comes from `<output_dir>/analysis.json` — every measured finding with
its root cause, impact, literal fix and verification — with anything authored
in report_data.py layered on top. That ordering matters: this used to render
report_data.py ALONE, so an engine-only run produced a full workbook and an
EMPTY html file. Measured content is now the baseline in both formats;
authoring is an upgrade, never a prerequisite.

Usage: python build_html.py [output_dir]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_data as RD              # noqa: E402
from auto_report import build_report  # noqa: E402
from report_kit import render_html    # noqa: E402


def _fname(rep):
    parts = [str(rep.get("client", "Report")), str(rep.get("period", "")),
             str(rep.get("title", "Audit"))]
    stem = "_".join(p.strip().replace(" ", "-") for p in parts if p.strip())
    return "".join(c for c in stem if c.isalnum() or c in "-_") or "Report"


EXAMPLE_MARK = "\u2039EXAMPLE\u203a"


def _strip_examples(rep):
    """Remove template placeholder content, then drop anything left empty.

    report_data.py ships illustrative rows so the author can see the required
    shape. They must never reach a client: an un-authored run should produce
    NO authored tabs, not tabs full of invented findings. This is belt and
    braces on the never-fabricate rule."""
    def clean(sec):
        s = dict(sec)
        s["findings"] = [f for f in (sec.get("findings") or [])
                         if EXAMPLE_MARK not in repr(f)]
        for key in ("chart", "table"):
            if key in s and EXAMPLE_MARK in repr(s.get(key)):
                s.pop(key)
        return s
    keep = [c for c in (clean(x) for x in (rep.get("sections") or []))
            if c.get("findings") or c.get("table") or c.get("chart")]
    return dict(rep, sections=keep), len(rep.get("sections") or []) - len(keep)


def load_analysis(outdir):
    path = os.path.join(outdir, "analysis.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main():
    authored, _dropped = _strip_examples(RD.REPORT)
    outdir = (sys.argv[1] if len(sys.argv) > 1
              else authored.get("output_dir", "./Log-Analysis"))
    os.makedirs(outdir, exist_ok=True)

    analysis = load_analysis(outdir)
    if analysis:
        rep = build_report(analysis, authored)
        src = (f"{len(analysis.get('findings') or [])} measured findings"
               + (f" + {len(authored.get('sections') or [])} authored section(s)"
                  if authored.get("sections") else ""))
    else:
        # No measured data: the report can only be what was authored. Say so
        # rather than writing a near-empty page and calling it a deliverable.
        rep = authored
        print(f"[build_html] WARNING: {os.path.join(outdir, 'analysis.json')} not "
              f"found — rendering authored content only. Run analyze_logs.py "
              f"--out {outdir} first.")
        src = "authored content only"

    path = os.path.join(outdir, _fname(rep) + ".html")
    html = render_html(rep)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"[build_html] wrote {path}  ({len(html):,} bytes, "
          f"{len(rep.get('sections') or [])} sections, from {src})")


if __name__ == "__main__":
    main()
