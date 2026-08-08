import json
from datetime import datetime
from typing import List
from models import URLAuditResult


def build_json(results: List[URLAuditResult], output_path: str):
    payload = {
        "audit_meta": {
            "tool":      "SEO Render Audit",
            "version":   "2.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reasoning": "claude-native (in-context; no external LLM API)",
        },
        "urls": [],
    }

    for res in results:
        payload["urls"].append({
            "url":    res.url,
            "status": res.audit_status,
            "fetch": {
                "status_code":    res.fetch.status_code,
                "fetch_time_ms":  res.fetch.fetch_time_ms,
                "render_time_ms": res.fetch.render_time_ms,
                "redirect_chain": res.fetch.redirect_chain,
                "console_errors": res.fetch.console_errors,
                "final_url":      res.fetch.final_url,
                "render_error":   res.fetch.render_error,
            },
            "scores":     res.scores,
            "bot_access": res.bot_access,
            "llms_txt":   res.llms_txt_status,
            "meta":       res.meta,
            "signals":    [s.model_dump() for s in res.signals],
            "solutions":  [s.model_dump() for s in res.solutions],
            "errors":     res.errors,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
