#!/usr/bin/env python3
"""Claude-native SEO Render Audit : deterministic prep + build.

The AI reasoning passes (reading / analysis / solutions) are performed by Claude
in-context between the two subcommands (see SKILL.md), NOT by any external LLM API.

  prep fetch raw HTML + robots/llms + extract raw-vs-rendered signals. The
         rendered DOM comes from --rendered-file (produced via the browser / Playwright tool)
         or, if installed, an optional local Playwright fallback. Writes
         raw_<slug>.html, rendered_<slug>.html and prep_<slug>.json.

  build read prep_<slug>.json plus Claude's analysis_<slug>.json /
         solutions_<slug>.json / reading_<slug>.json, run the deterministic
         scorer, and write the branded XLSX + HTML + JSON reports.

Usage:
  python render_audit.py prep --url URL [--rendered-file R.html] --ws WS [--slug S]
  python render_audit.py build --ws WS [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config # noqa: E402
from models import ( # noqa: E402
    URLAuditResult, FetchResult, SignalResult, SolutionRecord,
)
from fetcher.raw_fetch import fetch_raw # noqa: E402
from fetcher.aux_fetch import ( # noqa: E402
    fetch_robots, fetch_llms_txt, parse_bot_access,
)
from engine.extractor import extract_signals # noqa: E402
from engine.scorer import ( # noqa: E402
    apply_scores, reconcile_severity_from_solutions, compute_scores,
)
from outputs import build_xlsx, build_json # noqa: E402


def slug_of(url: str) -> str:
    """Stable, filesystem-safe slug. Root URL -> 'homepage'."""
    path = urlparse(url).path.strip("/")
    s = re.sub(r"[^a-z0-9]+", "-", (path or "homepage").lower()).strip("-")
    return s or "homepage"


# ── HTML report (ported from the app's build_html_report : registers the
# format_number filter and passes `meta`, which the template requires) ──────
def build_html_report(results, output_path: str) -> None:
    from jinja2 import Environment, FileSystemLoader
    from outputs.html_builder import _avg

    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")),
                      autoescape=True)
    env.filters["format_number"] = lambda v: f"{int(v):,}"
    tmpl = env.get_template("report.html.j2")

    all_criticals, all_warnings = [], []
    for res in results:
        for sol in res.solutions:
            if sol.severity == "critical":
                all_criticals.append((res.url, sol))
            elif sol.severity == "warning":
                all_warnings.append((res.url, sol))
    all_solutions = sorted(
        [(res.url, sol) for res in results for sol in res.solutions],
        key=lambda x: x[1].priority_rank,
    )
    html = tmpl.render(
        results=results, all_criticals=all_criticals, all_warnings=all_warnings,
        all_solutions=all_solutions,
        avg_google=_avg(results, "google_score"),
        avg_ai=_avg(results, "ai_bot_score"),
        avg_gap=_avg(results, "render_gap_score"),
        total_crit=len(all_criticals), total_warn=len(all_warnings),
        total_pass=sum(sum(1 for s in r.signals if s.severity == "pass")
                       for r in results),
        generated_at=datetime.now().strftime("%B %d, %Y at %H:%M"),
        url_count=len(results),
        meta=getattr(results[0], "meta", {}) if results else {},
    )
    Path(output_path).write_text(html, encoding="utf-8")


# ── PREP ──────────────────────────────────────────────────────────────────────
def cmd_prep(a) -> int:
    ws = Path(a.ws).resolve()
    ws.mkdir(parents=True, exist_ok=True)
    url = a.url
    slug = a.slug or slug_of(url)

    raw = fetch_raw(url)
    raw_html = raw.raw_html or ""
    if raw.fetch_error:
        print(f"WARN: raw fetch error for {url}: {raw.fetch_error}", file=sys.stderr)

    render_error = None
    render_time_ms = 0
    console_errors: list = []
    if a.rendered_file:
        rf = Path(a.rendered_file)
        if rf.exists():
            rendered_html = rf.read_text(encoding="utf-8", errors="replace")
            rmode = "file(MCP)"
        else:
            rendered_html = raw_html
            render_error = f"--rendered-file not found: {rf}"
            rmode = "RAW-ONLY"
    else:
        try:
            from fetcher.render_fetch import fetch_rendered
            rend = fetch_rendered(url)
            if rend.get("error"):
                rendered_html = raw_html
                render_error = rend["error"]
                rmode = "RAW-ONLY"
            else:
                rendered_html = rend["html"]
                render_time_ms = rend["render_time_ms"]
                console_errors = rend["console_errors"]
                rmode = "playwright"
        except Exception as e: # pragma: no cover
            rendered_html = raw_html
            render_error = f"no renderer: {e}"
            rmode = "RAW-ONLY"

    path = urlparse(url).path or "/"
    robots_txt = fetch_robots(url)
    llms_txt = fetch_llms_txt(url)
    bot_access = parse_bot_access(robots_txt, path, config.AI_BOTS)
    llms_status = "present" if llms_txt else "missing"

    signals = extract_signals(
        raw_html=raw_html, rendered_html=rendered_html,
        response_headers=raw.headers, base_url=url,
    )

    raw_path = ws / f"raw_{slug}.html"
    rend_path = ws / f"rendered_{slug}.html"
    raw_path.write_text(raw_html, encoding="utf-8")
    rend_path.write_text(rendered_html, encoding="utf-8")

    bt = next((s for s in signals if s.signal_id == "body_text"), None)
    raw_chars = (bt.raw_value or {}).get("char_count", 0) if bt else 0
    rend_chars = (bt.rendered_value or {}).get("char_count", 0) if bt else 0
    gap_pct = (bt.rendered_value or {}).get("gap_pct", 0) if bt else 0

    prep = {
        "url": url, "slug": slug, "path": path,
        "status_code": raw.status_code, "headers": dict(raw.headers),
        "fetch_time_ms": raw.fetch_time_ms, "final_url": raw.final_url,
        "redirect_chain": raw.redirect_chain,
        "render_time_ms": render_time_ms, "console_errors": console_errors,
        "render_error": render_error, "fetch_error": raw.fetch_error,
        "robots_txt": robots_txt, "llms_txt": llms_txt,
        "llms_txt_status": llms_status, "bot_access": bot_access,
        "raw_html_path": str(raw_path), "rendered_html_path": str(rend_path),
        "raw_chars": raw_chars, "rend_chars": rend_chars, "gap_pct": gap_pct,
        "signals": [s.model_dump() for s in signals],
    }
    prep_path = ws / f"prep_{slug}.json"
    prep_path.write_text(json.dumps(prep, indent=2, ensure_ascii=False),
                         encoding="utf-8")

    gapped = [s for s in signals
              if s.gap_significance in ("medium", "high") or not s.match]
    blocked = ",".join(b for b, v in bot_access.items() if v == "block") or "none"
    print(f"PREP OK {url}")
    print(f" slug={slug} status={raw.status_code} "
          f"raw_chars={raw_chars} rend_chars={rend_chars} body_gap={gap_pct}%")
    print(f" render={rmode}" + (f" render_error={render_error}" if render_error else ""))
    print(f" robots={'yes' if robots_txt else 'no'} "
          f"llms.txt={llms_status} bots_blocked={blocked}")
    print(f" signals={len(signals)} with_gap_or_mismatch={len(gapped)}")
    print(f" raw_html -> {raw_path}")
    print(f" rendered -> {rend_path}")
    print(f" prep -> {prep_path}")
    print(f"NEXT (Claude): read prep_{slug}.json + the two HTML files, then write "
          f"analysis_{slug}.json, solutions_{slug}.json, reading_{slug}.json "
          f"(schemas in SKILL.md). Then: build --ws {ws}")
    return 0


# ── BUILD ───────────────────────────────────────────────────────────────────
def _load(ws: Path, name: str, default):
    p = ws / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f" warn: {name} unreadable ({e}) : using default", file=sys.stderr)
    return default


def _coerce_solution(s: dict, url: str) -> dict:
    return {
        "signal_id": s.get("signal_id", ""), "url": s.get("url", url),
        "category": s.get("category", ""), "severity": s.get("severity", ""),
        "effort": s.get("effort", ""), "impact": s.get("impact", ""),
        "priority_rank": int(s.get("priority_rank", 999) or 999),
        "observed_in_raw": s.get("observed_in_raw", ""),
        "observed_in_rendered": s.get("observed_in_rendered", ""),
        "diagnosis": s.get("diagnosis", ""), "fix": s.get("fix", ""),
        "code_fix": s.get("code_fix"),
        "evidence_basis": s.get("evidence_basis", ""),
        "verify": s.get("verify", ""),
        "severity_reason": s.get("severity_reason", ""),
        "prose": s.get("prose", ""), "code_block": s.get("code_block"),
    }


def cmd_build(a) -> int:
    ws = Path(a.ws).resolve()
    out_dir = Path(a.out).resolve() if a.out else (ws / "report")
    out_dir.mkdir(parents=True, exist_ok=True)

    preps = sorted(ws.glob("prep_*.json"))
    if not preps:
        sys.exit(f"error: no prep_*.json in {ws} : run `prep` first")

    results = []
    for pp in preps:
        prep = json.loads(pp.read_text(encoding="utf-8"))
        slug, url = prep["slug"], prep["url"]
        signals = [SignalResult(**s) for s in prep.get("signals", [])]

        analysis = _load(ws, f"analysis_{slug}.json", [])
        if analysis:
            signals = apply_scores(signals, analysis)
        else:
            print(f" warn: analysis_{slug}.json missing : signals stay 'pass'",
                  file=sys.stderr)

        sols_raw = _load(ws, f"solutions_{slug}.json", [])
        solutions = [SolutionRecord(**_coerce_solution(s, url)) for s in sols_raw]
        signals = reconcile_severity_from_solutions(signals, solutions)
        solutions = sorted(solutions, key=lambda r: r.priority_rank)

        reading = _load(ws, f"reading_{slug}.json", {})
        scores = compute_scores(signals, prep.get("bot_access", {}),
                                prep.get("llms_txt_status", "missing"))

        fetch = FetchResult(
            url=url, status_code=prep.get("status_code"),
            headers=prep.get("headers", {}),
            fetch_time_ms=prep.get("fetch_time_ms", 0),
            render_time_ms=prep.get("render_time_ms", 0),
            redirect_chain=prep.get("redirect_chain", []),
            console_errors=prep.get("console_errors", []),
            final_url=prep.get("final_url", ""),
            robots_txt=prep.get("robots_txt"), llms_txt=prep.get("llms_txt"),
            fetch_error=prep.get("fetch_error"),
            render_error=prep.get("render_error"),
        )
        results.append(URLAuditResult(
            url=url, fetch=fetch, signals=signals, solutions=solutions,
            bot_access=prep.get("bot_access", {}),
            llms_txt_status=prep.get("llms_txt_status", "missing"),
            scores=scores,
            audit_status="failed" if prep.get("fetch_error") else "complete",
            meta={
                "js_framework_detected": reading.get("js_framework_detected", ""),
                "js_framework_evidence": reading.get("js_framework_evidence", ""),
                "js_heavy_page": reading.get("js_heavy_page", False),
                "page_type_inferred": reading.get("page_type_inferred", ""),
            },
        ))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx = str(out_dir / "audit_report.xlsx")
    html = str(out_dir / "audit_report.html")
    js = str(out_dir / f"audit_{ts}.json")
    for label, fn in [("XLSX", lambda: build_xlsx(results, xlsx)),
                      ("HTML", lambda: build_html_report(results, html)),
                      ("JSON", lambda: build_json(results, js))]:
        try:
            fn()
            print(f" {label}: ok")
        except Exception as e:
            print(f" {label} FAILED: {e}", file=sys.stderr)

    print(f"report dir: {out_dir}")
    for r in results:
        sc = r.scores or {}
        nc = sum(1 for s in r.signals if s.severity == "critical")
        nw = sum(1 for s in r.signals if s.severity == "warning")
        print(f" {r.url} : {r.audit_status} : "
              f"google={sc.get('google_score','n/a')} "
              f"ai={sc.get('ai_bot_score','n/a')} "
              f"gap={sc.get('render_gap_score','n/a')} crit={nc} warn={nw}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="render_audit.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prep", help="fetch + extract signals for one URL")
    p.add_argument("--url", required=True)
    p.add_argument("--rendered-file", dest="rendered_file",
                   help="rendered DOM HTML saved from the browser MCP")
    p.add_argument("--ws", required=True, help="workspace dir")
    p.add_argument("--slug", help="override the auto slug")
    p.set_defaults(func=cmd_prep)

    b = sub.add_parser("build", help="assemble reports from prep_ + Claude JSON")
    b.add_argument("--ws", required=True)
    b.add_argument("--out", help="output dir (default: <ws>/report)")
    b.set_defaults(func=cmd_build)

    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
