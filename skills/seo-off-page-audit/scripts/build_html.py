#!/usr/bin/env python3
"""Render the branded HTML deliverable from report_data.REPORT.
Usage: python build_html.py [output_dir]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "shared"))
import report_data as RD # noqa: E402
from report_kit import render_html # noqa: E402


def _fname(rep):
    parts = [str(rep.get("client", "Report")), str(rep.get("period", "")),
             str(rep.get("title", "Audit"))]
    stem = "_".join(p.strip().replace(" ", "-") for p in parts if p.strip())
    return "".join(c for c in stem if c.isalnum() or c in "-_") or "Report"


def main():
    rep = RD.REPORT
    outdir = sys.argv[1] if len(sys.argv) > 1 else rep.get("output_dir", "./Deliverable")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, _fname(rep) + ".html")
    html = render_html(rep)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"[build_html] wrote {path} ({len(html):,} bytes, "
          f"{len(rep.get('sections') or [])} sections)")


if __name__ == "__main__":
    main()
