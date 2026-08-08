#!/usr/bin/env python3
"""SEO Decision MCP — query the Action Decision System notebook by section.

Works with Claude Code plugins (CLAUDE_PLUGIN_ROOT), Cursor, Codex, or any MCP host.
Stdlib + beautifulsoup4. Optional: `mcp` package (FastMCP). Falls back to a tiny
stdio JSON-RPC loop if `mcp` is not installed.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    print("beautifulsoup4 required: pip install beautifulsoup4", file=sys.stderr)
    sys.exit(1)

ROOT = Path(
    os.environ.get("SEO_TEACHER_ROOT")
    or os.environ.get("CLAUDE_PLUGIN_ROOT")
    or Path(__file__).resolve().parents[1]
)
def _html_path() -> Path:
    candidates = [
        ROOT / "assets" / "SEO_Action_Decision_System.html",
        ROOT / "skills" / "seo-decision-teacher" / "assets" / "SEO_Action_Decision_System.html",
        Path(__file__).resolve().parents[1] / "assets" / "SEO_Action_Decision_System.html",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


HTML_PATH = _html_path()

# Situation keywords → notebook section id + suggested audit skill(s)
ROUTES = [
    (["traffic down", "ranking down", "clicks down", "decline", "drop", "lost traffic"],
     "decline-diagnosis", ["seo-gsc-diagnosis", "seo-ecom-decline-investigation"]),
    (["new site", "new domain", "new project", "what is this business", "entity"],
     "domain-understanding", ["seo-initial-analysis"]),
    (["topical map", "content cluster", "topic map", "keyword map"],
     "topical-map", ["seo-topical-map"]),
    (["money page", "service page", "conversion", "cro"],
     "money-pages", ["seo-cro-conversion-audit", "seo-after-foundational-setup-audit"]),
    (["location page", "local seo", "gbp", "google business"],
     "local-gbp", ["seo-after-foundational-setup-audit"]),
    (["eeat", "e-e-a-t", "authorship", "author"],
     "content-eeat", ["seo-eeat-authorship-audit"]),
    (["cannibal", "duplicate url", "same keyword two pages"],
     "decline-diagnosis", ["seo-cannibalization-audit"]),
    (["render", "javascript", "js seo", "raw html"],
     "technical-seo", ["seo-render-audit"]),
    (["log file", "crawl budget", "bot crawl"],
     "technical-seo", ["seo-log-file-analysis"]),
    (["backlink", "off page", "toxic link"],
     "technical-seo", ["seo-off-page-audit"]),
    (["affiliate", "review site", "disclosure"],
     "content-eeat", ["seo-affiliate-and-review-audit"]),
    (["sandbox", "indexed but not ranking", "not graduating"],
     "decline-diagnosis", ["seo-sandbox-effect-analysis"]),
    (["schema", "structured data", "rich result"],
     "structured-data", []),
    (["blog", "adsense", "informational"],
     "blog-adsense", []),
    (["forecast", "kpi", "projection"],
     "kpi-forecasting", []),
    (["weekly report", "reporting"],
     "weekly-reporting", []),
]


def _load_soup() -> BeautifulSoup:
    if not HTML_PATH.is_file():
        raise FileNotFoundError(f"Decision notebook not found: {HTML_PATH}")
    return BeautifulSoup(HTML_PATH.read_text(encoding="utf-8"), "lxml")


def list_sections() -> list[dict]:
    soup = _load_soup()
    out = []
    for sec in soup.select("section[id]"):
        h = sec.find(["h2", "h1"])
        out.append({
            "id": sec.get("id"),
            "title": h.get_text(" ", strip=True) if h else sec.get("id"),
        })
    return out


def get_section(section_id: str, max_chars: int = 12000) -> dict:
    soup = _load_soup()
    sec = soup.find("section", id=section_id)
    if sec is None:
        # fuzzy: match title substring
        needle = section_id.lower().strip()
        for candidate in soup.select("section[id]"):
            h = candidate.find(["h2", "h1"])
            title = h.get_text(" ", strip=True).lower() if h else ""
            if needle in candidate.get("id", "") or needle in title:
                sec = candidate
                section_id = candidate.get("id")
                break
    if sec is None:
        return {"error": f"Section not found: {section_id}", "available": [s["id"] for s in list_sections()]}
    h = sec.find(["h2", "h1"])
    text = sec.get_text("\n", strip=True)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[truncated — ask for a narrower subsection or raise max_chars]"
    return {
        "id": section_id,
        "title": h.get_text(" ", strip=True) if h else section_id,
        "path": str(HTML_PATH),
        "text": text,
    }


def route_situation(situation: str) -> dict:
    s = situation.lower()
    hits = []
    for keys, section_id, skills in ROUTES:
        score = sum(1 for k in keys if k in s)
        if score:
            hits.append((score, section_id, skills, keys))
    hits.sort(key=lambda x: (-x[0], x[1]))
    if not hits:
        return {
            "mode": "simple-or-clarify",
            "section_id": "decision-router",
            "reason": "No strong match — open the Action Decision Router and ask one clarifying question if needed.",
            "suggested_skills": [],
            "next_step": "Call get_section('decision-router') then answer with What/Why/How/Evidence/Priority.",
        }
    score, section_id, skills, keys = hits[0]
    return {
        "mode": "routed",
        "section_id": section_id,
        "matched_keywords": [k for k in keys if k in s],
        "suggested_skills": skills,
        "next_step": (
            f"Load section `{section_id}` via get_section, apply its rules, "
            f"then optionally run skills: {', '.join(skills) if skills else '(none — teach from notebook only)'}."
        ),
    }


def list_audit_skills() -> list[dict]:
    skills_dir = ROOT / "skills"
    out = []
    if not skills_dir.is_dir():
        return out
    for d in sorted(skills_dir.iterdir()):
        skill_md = d / "SKILL.md"
        if not d.is_dir() or not skill_md.is_file():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        desc = ""
        m = re.search(r"description:\s*>?-?\s*\n((?:  .*\n)+)", text)
        if m:
            desc = " ".join(line.strip() for line in m.group(1).splitlines())
        else:
            m2 = re.search(r"description:\s*[\"']?([^\"'\n]+)", text)
            desc = (m2.group(1) if m2 else "").strip()
        out.append({"name": d.name, "description": desc[:300]})
    return out


# --- MCP surface -----------------------------------------------------------

TOOLS = {
    "list_decision_sections": {
        "description": "List all section ids/titles in the SEO Action Decision System notebook.",
        "schema": {"type": "object", "properties": {}},
        "handler": lambda _a: list_sections(),
    },
    "get_decision_section": {
        "description": "Return the text of one notebook section by id (e.g. decline-diagnosis, money-pages).",
        "schema": {
            "type": "object",
            "properties": {
                "section_id": {"type": "string"},
                "max_chars": {"type": "integer", "default": 12000},
            },
            "required": ["section_id"],
        },
        "handler": lambda a: get_section(a["section_id"], int(a.get("max_chars") or 12000)),
    },
    "route_seo_situation": {
        "description": "Given a user SEO situation, recommend the notebook section and optional audit skill(s).",
        "schema": {
            "type": "object",
            "properties": {"situation": {"type": "string"}},
            "required": ["situation"],
        },
        "handler": lambda a: route_situation(a["situation"]),
    },
    "list_seo_audit_skills": {
        "description": "List bundled seo-* audit skills and short descriptions.",
        "schema": {"type": "object", "properties": {}},
        "handler": lambda _a: list_audit_skills(),
    },
}


def _run_fastmcp() -> bool:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return False

    mcp = FastMCP("seo-decision")

    @mcp.tool()
    def list_decision_sections() -> list:
        """List all section ids/titles in the SEO Action Decision System notebook."""
        return list_sections()

    @mcp.tool()
    def get_decision_section(section_id: str, max_chars: int = 12000) -> dict:
        """Return the text of one notebook section by id."""
        return get_section(section_id, max_chars)

    @mcp.tool()
    def route_seo_situation(situation: str) -> dict:
        """Recommend notebook section + audit skills for a situation."""
        return route_situation(situation)

    @mcp.tool()
    def list_seo_audit_skills() -> list:
        """List bundled seo-* audit skills."""
        return list_audit_skills()

    mcp.run()
    return True


def _run_minimal_stdio() -> None:
    """Tiny MCP stdio server (tools/list + tools/call) without the mcp package."""

    def reply(msg_id, result=None, error=None):
        out = {"jsonrpc": "2.0", "id": msg_id}
        if error is not None:
            out["error"] = error
        else:
            out["result"] = result
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method")
        msg_id = req.get("id")
        params = req.get("params") or {}

        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "seo-decision", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            tools = []
            for name, meta in TOOLS.items():
                tools.append({
                    "name": name,
                    "description": meta["description"],
                    "inputSchema": meta["schema"],
                })
            reply(msg_id, {"tools": tools})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            meta = TOOLS.get(name)
            if not meta:
                reply(msg_id, error={"code": -32601, "message": f"Unknown tool: {name}"})
                continue
            try:
                result = meta["handler"](args)
                reply(msg_id, {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                })
            except Exception as e:  # noqa: BLE001
                reply(msg_id, error={"code": -32000, "message": str(e)})
        elif method == "ping":
            reply(msg_id, {})
        elif msg_id is not None:
            reply(msg_id, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print(json.dumps({
            "root": str(ROOT),
            "html_exists": HTML_PATH.is_file(),
            "sections": len(list_sections()),
            "route": route_situation("organic traffic dropped on Shopify"),
        }, indent=2))
        sys.exit(0)
    if not _run_fastmcp():
        _run_minimal_stdio()
