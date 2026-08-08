#!/usr/bin/env python3
"""Render the branded XLSX deliverable from report_data.REPORT (parity with HTML).
Usage: python build_xlsx.py [output_dir]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_data as RD          # noqa: E402
from report_kit import render_xlsx  # noqa: E402
from build_html import _fname       # noqa: E402


def main():
    rep = RD.REPORT
    outdir = sys.argv[1] if len(sys.argv) > 1 else rep.get("output_dir", "./Deliverable")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, _fname(rep) + ".xlsx")
    saved = render_xlsx(rep, path)
    print(f"[build_xlsx] wrote {saved}  "
          f"({1 + len(rep.get('sections') or [])} tabs)")


if __name__ == "__main__":
    main()
