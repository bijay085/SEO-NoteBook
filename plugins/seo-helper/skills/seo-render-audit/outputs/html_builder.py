from pathlib import Path
from datetime import datetime
from typing import List
from jinja2 import Environment, FileSystemLoader
from models import URLAuditResult


def build_html(results: List[URLAuditResult], output_path: str):
    templates_dir = Path(__file__).parent.parent / "templates"
    env  = Environment(loader=FileSystemLoader(str(templates_dir)),
                       autoescape=True)
    tmpl = env.get_template("report.html.j2")

    # Pre-compute summary stats for the template
    all_criticals = []
    all_warnings  = []
    for res in results:
        for sol in res.solutions:
            if sol.severity == "critical":
                all_criticals.append((res.url, sol))
            elif sol.severity == "warning":
                all_warnings.append((res.url, sol))

    all_solutions = []
    for res in results:
        for sol in res.solutions:
            all_solutions.append((res.url, sol))
    all_solutions.sort(key=lambda x: x[1].priority_rank)

    avg_google    = _avg(results, "google_score")
    avg_ai        = _avg(results, "ai_bot_score")
    avg_gap       = _avg(results, "render_gap_score")
    total_crit    = len(all_criticals)
    total_warn    = len(all_warnings)
    total_pass    = sum(
        sum(1 for s in r.signals if s.severity == "pass") for r in results
    )

    html = tmpl.render(
        results       = results,
        all_criticals = all_criticals,
        all_warnings  = all_warnings,
        all_solutions = all_solutions,
        avg_google    = avg_google,
        avg_ai        = avg_ai,
        avg_gap       = avg_gap,
        total_crit    = total_crit,
        total_warn    = total_warn,
        total_pass    = total_pass,
        generated_at  = datetime.now().strftime("%B %d, %Y at %H:%M"),
        url_count     = len(results),
    )

    Path(output_path).write_text(html, encoding="utf-8")


def _avg(results, key):
    vals = [r.scores.get(key, 0) for r in results if r.scores]
    return round(sum(vals) / len(vals)) if vals else 0
