from typing import List, Dict
from models import SignalResult


def apply_scores(signals: List[SignalResult],
                 scored: List[dict]) -> List[SignalResult]:
    """
    Merge AI-assigned severity/effort/impact/priority/severity_reason back into
    the python-extracted SignalResult list.
    """
    score_map = {s["signal_id"]: s for s in scored}

    for sig in signals:
        s = score_map.get(sig.signal_id)
        if s:
            sig.severity = s.get("severity", sig.severity)
            sig.effort = s.get("effort", sig.effort)
            sig.impact = s.get("impact", sig.impact)
            sig.priority_rank = s.get("priority_rank", sig.priority_rank)
            sig.severity_reason = s.get("severity_reason", "")

    return sorted(signals, key=lambda x: x.priority_rank)


def reconcile_severity_from_solutions(signals: List[SignalResult],
                                       solutions) -> List[SignalResult]:
    """
    After solutions are generated, override signal severity from the solution
    record. This ensures All Signals table is consistent with Warnings/Criticals.
    A signal that has a warning-level solution must never show PASS in the table.
    """
    sol_map = {}
    for sol in solutions:
        # solutions may cover sub-signals (images_missing_alt) : map to base id
        base_id = sol.signal_id.replace("_missing_alt", "").replace("_js_gated", "")
        if base_id not in sol_map or sol.severity in ("critical", "warning"):
            sol_map[base_id] = sol.severity

    for sig in signals:
        if sig.signal_id in sol_map:
            sol_sev = sol_map[sig.signal_id]
            # Only escalate, never downgrade
            rank = {"critical": 3, "warning": 2, "info": 1, "pass": 0}
            if rank.get(sol_sev, 0) > rank.get(sig.severity, 0):
                sig.severity = sol_sev

    return signals


def compute_scores(signals: List[SignalResult],
                   bot_access: Dict[str, str],
                   llms_txt_status: str) -> Dict[str, int]:
    """
    Compute three headline scores (0-100) from signal list.
    """
    total = len(signals)
    if total == 0:
        return {"google_score": 0, "ai_bot_score": 0, "render_gap_score": 0}

    critical_count = sum(1 for s in signals if s.severity == "critical")
    warning_count = sum(1 for s in signals if s.severity == "warning")
    pass_count = sum(1 for s in signals if s.severity == "pass")

    # Google score : penalise criticals heavily, warnings lightly
    google_score = max(0, 100
                       - (critical_count * 15)
                       - (warning_count * 5))

    # AI bot score : based on bot access + llms.txt + schema signals
    blocked_bots = sum(1 for v in bot_access.values() if v == "block")
    schema_pass = any(s.signal_id == "json_ld" and s.severity == "pass"
                       for s in signals)
    ai_score = max(0, 100
                   - (blocked_bots * 20)
                   - (0 if llms_txt_status == "present" else 10)
                   - (0 if schema_pass else 10))

    # Render gap score : based on body text gap and signal mismatches
    # body_text signal raw_value/rendered_value are now dicts : use char_count key
    gap_signal = next((s for s in signals if s.signal_id == "body_text"), None)
    mismatch_count = sum(1 for s in signals if not s.match)
    gap_pct = 0
    if gap_signal:
        rv = gap_signal.rendered_value
        raw_v = gap_signal.raw_value
        # Support both old int format and new dict format
        rend_chars = rv.get("char_count", 0) if isinstance(rv, dict) else (rv or 0)
        raw_chars = raw_v.get("char_count", 0) if isinstance(raw_v, dict) else (raw_v or 0)
        # Also use pre-computed gap_pct from dict if available
        if isinstance(rv, dict) and "gap_pct" in rv:
            gap_pct = rv["gap_pct"]
        elif rend_chars > 0:
            gap_pct = max(0, (rend_chars - raw_chars) / rend_chars * 100)

    render_gap_score = max(0, 100
                           - int(gap_pct * 0.5)
                           - (mismatch_count * 5))

    return {
        "google_score": min(100, google_score),
        "ai_bot_score": min(100, ai_score),
        "render_gap_score": min(100, render_gap_score),
    }
