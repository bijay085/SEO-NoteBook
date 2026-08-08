#!/usr/bin/env python3
"""Render the branded XLSX deliverable from report_data.REPORT (parity with the
HTML), then append the measured data tabs from analysis.json.

Usage: python build_xlsx.py [output_dir]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import report_data as RD                          # noqa: E402
from build_data_tabs import append_data_tabs      # noqa: E402
from auto_report import build_report              # noqa: E402
from build_html import _fname, load_analysis      # noqa: E402
from report_kit import render_xlsx                # noqa: E402


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


def main():
    authored, dropped = _strip_examples(RD.REPORT)
    outdir = (sys.argv[1] if len(sys.argv) > 1
              else authored.get("output_dir", "./Log-Analysis"))
    os.makedirs(outdir, exist_ok=True)
    # Naming resolves from the same source as the HTML so the two files cannot
    # drift apart. The SECTIONS deliberately do not: in a spreadsheet the
    # measured findings belong in the filterable `Issue Analysis` grid, not
    # duplicated across nine narrative tabs. Parity is same facts, not same
    # shape — the HTML is the narrative view, the XLSX the working view.
    _a = load_analysis(outdir)
    if _a:
        named = build_report(_a, authored)
        rep = dict(authored, title=named["title"], client=named["client"],
                   period=named["period"], subtitle=named["subtitle"])
    else:
        rep = authored
    path = os.path.join(outdir, _fname(rep) + ".xlsx")
    saved = render_xlsx(rep, path)
    tabs = 1 + len(rep.get("sections") or [])
    if dropped:
        print(f"[build_xlsx] {dropped} authored section(s) were empty and omitted — "
              f"author report_data.py to include them.")

    # The measured half. A missing analysis.json is not fatal — the authored
    # report still stands — but it IS worth saying out loud, because a log
    # deliverable without the URL/bot tabs is a partial deliverable.
    ajson = os.path.join(outdir, "analysis.json")
    if os.path.exists(ajson):
        added = append_data_tabs(saved, ajson)
        tabs += len(added)
        print(f"[build_xlsx] appended data tabs: {', '.join(added)}")
    else:
        print(f"[build_xlsx] WARNING: {ajson} not found — findings tabs only, no "
              f"URL/bot/trend data tabs. Run analyze_logs.py --out {outdir} first.")

    print(f"[build_xlsx] wrote {saved}  ({tabs} tabs)")


if __name__ == "__main__":
    main()
