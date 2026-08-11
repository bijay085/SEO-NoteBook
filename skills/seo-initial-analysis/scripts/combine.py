"""Combine branded section HTMLs into one compiled Initial Analysis report.

Usage:
    python combine.py <sections_dir> <config.json> [out.html]

Reads every *.html in <sections_dir> (sorted by filename), pulls each one's inner
content + its <title>, and assembles a single branded document: cover, jump-link
TOC, then each section under an anchored bar. Reuses brand_lib for the shell/CSS so
the compiled report matches every standalone section. Name section files with a
numeric prefix (01-..., 02-...) to control order.
"""
import sys, os, re, glob
import brand_lib as B

def _inner(html):
    """Strip the per-section header/footer shell, keep the content block."""
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    body = m.group(1) if m else html
    starts = [body.find(s) for s in ("<div class='report-wrapper'", '<div class="report-wrapper"',
                                     "<div class='wrap'", '<div class="wrap"')]
    starts = [x for x in starts if x != -1]
    start = min(starts) if starts else 0
    ends = [body.find(s) for s in ("<div class='report-footer'", '<div class="report-footer"')]
    ends = [x for x in ends if x != -1]
    end = min(ends) if ends else len(body)
    return body[start:end].strip()

def _title(html, fallback):
    m = re.search(r"<title>.*?[: -]\s*(.*?)</title>", html, re.S | re.I)
    return m.group(1).strip() if m else fallback

def main():
    if len(sys.argv) < 3:
        sys.exit("usage: python combine.py <sections_dir> <config.json> [out.html]")
    sections_dir, cfg_path = sys.argv[1], sys.argv[2]
    cfg = B.load_config(cfg_path)
    client = cfg.get("client", {}).get("name", "")
    short = cfg.get("client", {}).get("short_name", client) or "Client"
    label = cfg.get("period", {}).get("label", "Initial Analysis")
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        os.path.dirname(cfg_path) or ".", f"00-{short}-Compiled-Analysis-Report.html")

    files = sorted(glob.glob(os.path.join(sections_dir, "*.html")))
    if not files:
        sys.exit(f"no *.html sections in {sections_dir}")
    secs = []
    for i, f in enumerate(files, 1):
        html = open(f, encoding="utf-8").read()
        title = _title(html, os.path.splitext(os.path.basename(f))[0])
        secs.append((f"sec{i}", title, _inner(html)))

    toc = "".join(f"<li><a href='#{sid}'>{t}</a></li>" for sid, t, _ in secs)
    parts = [f"<div class='report-wrapper'>",
             f"<div class='banner'><b>{client} &middot; Initial Analysis</b><p>{label}</p></div>",
             f"<h2>Contents</h2><ol>{toc}</ol></div>"]
    for sid, t, inner in secs:
        parts.append(f"<div class='report-wrapper' id='{sid}'>"
                     f"<div class='banner'><b>{t}</b></div>{inner}</div>")
    open(out, "w", encoding="utf-8").write(B.shell("Compiled Analysis", "".join(parts), cfg))
    print(f"Wrote {out} ({len(secs)} sections)")

if __name__ == "__main__":
    main()
