"""Shared inline-SVG chart helper for SEO skill reports (pure stdlib).

Self-styling: every <text>/<rect> carries inline style, so a chart drops into
ANY skill's existing HTML/CSS unchanged. No external deps, no host-CSS reliance.

Usage inside a builder:
    from charts import chart_html
    block = chart_html("Top clusters by search volume",
                       [("plumbing repair", 2400), ("water heater install", 1900)],
                       kind="bars", unit="")
    # ...insert `block` (an HTML <figure> string) where the chart belongs.

kind="bars"  -> vertical bars (comparisons, scores)
kind="hbars" -> horizontal bars (distributions / histograms, long labels)
"""
import html as _h

YL, BK, LN, MUT, INK = "#F5C518", "#0A0A0A", "#E7E7DF", "#6B6B63", "#14140F"
_LBL = f'font:11px system-ui,sans-serif;fill:{MUT}'
_VAL = f'font:600 11px system-ui,sans-serif;fill:{INK}'


def _esc(x):
    return _h.escape("" if x is None else str(x))


def _num(v):
    f = float(v)
    return str(int(f)) if f == int(f) else f"{f:.2f}".rstrip("0").rstrip(".")


def svg_bars(data, unit="", horizontal=False):
    data = [(str(l), float(v)) for l, v in (data or []) if v is not None]
    if not data:
        return ""
    mx = max(v for _, v in data) or 1.0
    if horizontal:
        rowh, labelw, w, pad = 26, 170, 600, 6
        barw = w - labelw - 80
        h = pad * 2 + rowh * len(data)
        p = []
        for i, (l, v) in enumerate(data):
            y = pad + i * rowh
            bw = max(2.0, (v / mx) * barw)
            p.append(f'<text x="0" y="{y+17}" style="{_LBL}">{_esc(l)}</text>')
            p.append(f'<rect x="{labelw}" y="{y+5}" width="{bw:.1f}" height="15" rx="3" '
                     f'fill="{YL}" stroke="{BK}" stroke-width="0.6"/>')
            p.append(f'<text x="{labelw+bw+6:.1f}" y="{y+17}" style="{_VAL}">{_num(v)}{_esc(unit)}</text>')
        inner = "".join(p)
    else:
        n, w, h, gap, top = len(data), 680, 240, 12, 16
        base = h - 28
        bw = (w - gap * (n + 1)) / n
        p = [f'<line x1="0" y1="{base}" x2="{w}" y2="{base}" stroke="{LN}"/>']
        for i, (l, v) in enumerate(data):
            x = gap + i * (bw + gap)
            bh = max(2.0, (v / mx) * (base - top))
            y = base - bh
            p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" '
                     f'fill="{YL}" stroke="{BK}" stroke-width="0.6"/>')
            p.append(f'<text x="{x+bw/2:.1f}" y="{y-4:.1f}" style="{_VAL}" text-anchor="middle">{_num(v)}{_esc(unit)}</text>')
            p.append(f'<text x="{x+bw/2:.1f}" y="{base+15:.1f}" style="{_LBL}" text-anchor="middle">{_esc(l)}</text>')
        inner = "".join(p)
    return (f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto" '
            f'preserveAspectRatio="xMinYMin meet" role="img">{inner}</svg>')


def chart_html(title, data, kind="bars", unit=""):
    svg = svg_bars(data, unit=unit, horizontal=(kind == "hbars"))
    if not svg:
        return ""
    return (f'<figure style="margin:14px 0;padding:12px;border:1px solid {LN};'
            f'border-radius:9px;background:#FCFCF9">'
            f'<figcaption style="font:700 13px system-ui,sans-serif;margin-bottom:6px;'
            f'color:{INK}">{_esc(title)}</figcaption>{svg}</figure>')
