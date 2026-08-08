#!/usr/bin/env python3
"""Shared SEO report branding for the Periodic Audit skill.

Config-driven: colors / logo / font come from config.json's `brand` block (defaults
to yellow/black + Lexend; text mark only (no logo)). Import this from the report scripts and from
combine.py so every section shares one look.

    import brand_lib as B
    cfg = B.load_config("config.json")
    html = B.shell("Leads & Channel ROI", inner_html, cfg)   # standalone report
    B.tbl(["A","B"], [["1","2"]])                             # table helper
"""
import json, os

def load_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _b(cfg):
    b = dict(cfg.get("brand", {}))
    d = {"yellow":"#F5C518","black":"#0A0A0A","dark":"#1A1A1A","text":"#1C1C1C",
         "muted":"#888888","green":"#2ECC71","red":"#E74C3C","orange":"#E67E22",
         "font":"Lexend","agency":"Bijay","logo_url":""}
    d.update({k:v for k,v in b.items() if v})
    d["logo"] = b.get("logo_local") or b.get("logo_url") or ""
    return d

def css(cfg):
    b = _b(cfg)
    return f"""@import url('https://fonts.googleapis.com/css2?family={b['font']}:wght@400;500;600;700;800&display=swap');
:root{{--yellow:{b['yellow']};--black:{b['black']};--dark:{b['dark']};--bg:#F7F7F7;--text:{b['text']};--muted:{b['muted']};--white:#fff;--green:{b['green']};--red:{b['red']};--orange:{b['orange']};--radius:8px;--shadow:0 2px 12px rgba(0,0,0,.08)}}
*{{box-sizing:border-box}}body{{margin:0;font-family:{b['font']},system-ui,Arial;background:var(--bg);color:var(--text);font-size:14px;line-height:1.7}}
.report-header{{background:var(--black);padding:22px 40px;border-bottom:3px solid var(--yellow);display:flex;align-items:center;justify-content:space-between;gap:20px}}
.report-header .brand-mark{{color:var(--yellow);font-size:22px;font-weight:800;letter-spacing:.04em}}
.report-header .ht{{color:#fff;font-size:19px;font-weight:800;text-align:right;line-height:1.2}}.report-header .ht span{{color:var(--yellow)}}
.report-header .hm{{color:var(--muted);font-size:11px;text-align:right;margin-top:3px}}
.report-wrapper,.wrap{{max-width:1000px;margin:0 auto;padding:26px 40px 8px}}
h1{{display:none}}.sub{{color:var(--muted);font-size:12.5px;margin-bottom:14px}}
h2{{font-size:17px;font-weight:700;border-left:4px solid var(--yellow);padding-left:13px;margin:26px 0 10px;line-height:1.3}}h3{{font-size:14px;font-weight:600;margin:10px 0 4px}}
.card{{background:var(--white);border:1px solid #e6e8eb;border-radius:var(--radius);padding:18px;margin-top:12px;box-shadow:var(--shadow)}}
.card svg{{width:100%;height:auto;display:block}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:14px 0}}
.kpi{{background:var(--dark);border-radius:var(--radius);padding:18px 16px;border-top:3px solid var(--yellow);text-align:center}}
.kpi .v{{font-size:25px;font-weight:800;color:var(--yellow)}}.kpi .l{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em;margin-top:5px}}
.banner{{background:var(--black);color:#fff;border-left:5px solid var(--yellow);border-radius:var(--radius);padding:20px 22px;margin:14px 0}}.banner b{{color:var(--yellow);font-size:15px}}.banner p{{margin-top:8px;opacity:.95;font-size:13.5px}}
.flag{{background:#fff;border:1px solid #f0c9c9;border-left:4px solid var(--red);border-radius:var(--radius);padding:13px 15px;margin:12px 0}}
.good{{background:#fff;border:1px solid #cdebd6;border-left:4px solid var(--green);border-radius:var(--radius);padding:13px 15px;margin:12px 0}}
table{{border-collapse:collapse;width:100%;font-size:12.5px;box-shadow:var(--shadow);border-radius:var(--radius);overflow:hidden;margin-top:6px}}
th{{background:var(--black);color:var(--yellow);text-transform:uppercase;font-size:11px;letter-spacing:.05em;padding:10px 12px;text-align:left}}
td{{padding:9px 12px;border-bottom:1px solid #ebebeb;vertical-align:top}}tr:nth-child(even) td{{background:#F2F2F2}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.win{{background:#fbecec;border:1px solid #f0c9c9;border-radius:var(--radius);padding:14px}}.need{{background:#e9f6ee;border:1px solid #c8e8d3;border-radius:var(--radius);padding:14px}}.win h3{{color:var(--red)}}.need h3{{color:#1f7a44}}
ul{{padding-left:18px}}li{{margin:4px 0}}small{{color:#888}}
.report-footer{{background:var(--black);border-top:2px solid var(--yellow);padding:16px 40px;display:flex;justify-content:space-between;align-items:center;margin-top:36px}}
.report-footer span{{color:var(--muted);font-size:12px}}"""

def header(title, cfg):
    b = _b(cfg); client = cfg.get("client", {}).get("name", "")
    brand = b.get('mark') or 'SEO'
    return (f"<div class='report-header'>"
            f"<div class='brand-mark'>{brand}</div>"
            f"<div><div class='ht'>{client} <span>&middot;</span> {title}</div>"
            f"<div class='hm'>Prepared by {b['agency']}</div></div></div>")

def footer(cfg):
    b = _b(cfg)
    return (f"<div class='report-footer'><span>&copy; {b['agency']}</span>"
            f"<span>{cfg.get('client',{}).get('name','')} &middot; Periodic Audit</span></div>")

def shell(title, inner, cfg):
    """Full standalone HTML for one report section."""
    if "report-wrapper" not in inner and "class='wrap'" not in inner:
        inner = f"<div class='report-wrapper'>{inner}</div>"
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{cfg.get('brand',{}).get('agency','Bijay')} — {title}</title>"
            f"<style>{css(cfg)}</style></head><body>{header(title,cfg)}{inner}{footer(cfg)}</body></html>")

def tbl(headers, rows):
    h = "<tr>" + "".join(f"<th>{x}</th>" for x in headers) + "</tr>"
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table>{h}{body}</table>"
