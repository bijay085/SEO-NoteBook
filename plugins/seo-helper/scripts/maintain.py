#!/usr/bin/env python3
"""Maintenance helper for the SEO Helper plugin.

Commands:
  validate          Check manifest files, canonical HTML, MCP router, and section index.
  rebuild-index     Regenerate skills/seo-router/references/section-index.md from HTML.
  add-rule          Insert a compact HTML rule before a matching <h3> or </section> marker.

This script intentionally keeps the plugin simple: one canonical knowledgebase HTML,
one router skill, one optional MCP server, and focused audit skills.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1] if len(ROOT.parents) > 1 else ROOT
HTML = ROOT / "knowledge" / "SEO_Action_Decision_System.html"
INDEX = ROOT / "skills" / "seo-router" / "references" / "section-index.md"
CODEX_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
CLAUDE_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
MCP_CONFIG = ROOT / ".mcp.json"
SERVER = ROOT / "server" / "seo_router_server.py"


class SectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sections: list[dict[str, str]] = []
        self._current_id: str | None = None
        self._capture_heading = False
        self._heading_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "section" and attrs_dict.get("id"):
            self._current_id = attrs_dict["id"]
        elif self._current_id and tag == "h2":
            self._capture_heading = True
            self._heading_parts = []

    def handle_data(self, data: str) -> None:
        if self._capture_heading:
            self._heading_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self._capture_heading and self._current_id:
            title = " ".join(" ".join(self._heading_parts).split())
            self.sections.append({"id": self._current_id, "title": title})
            self._capture_heading = False
        elif tag == "section":
            self._current_id = None
            self._capture_heading = False


def load_sections() -> list[dict[str, str]]:
    parser = SectionParser()
    parser.feed(HTML.read_text(encoding="utf-8"))
    return parser.sections


def rebuild_index() -> None:
    sections = load_sections()
    lines = [
        "# Decision Notebook Section Index",
        "",
        "Source file in this plugin: `knowledge/SEO_Action_Decision_System.html`",
        "",
        "Prefer MCP tools `list_decision_sections`, `get_decision_section`, and `route_seo_situation` when available. Otherwise open the HTML and jump to the `id` below.",
        "",
        "| id | Section |",
        "|---|---|",
    ]
    lines.extend(f"| {s['id']} | {s['title']} |" for s in sections)
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Rebuilt section index with {len(sections)} sections: {INDEX}")


def require_file(path: Path, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"Missing file: {path}")


def validate_json(path: Path, errors: list[str]) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid JSON in {path}: {exc}")
        return {}


def run_self_test(errors: list[str]) -> None:
    try:
        result = subprocess.run(
            [sys.executable, str(SERVER), "--self-test"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"MCP self-test failed to start: {exc}")
        return
    if result.returncode != 0:
        errors.append(f"MCP self-test failed: {result.stderr.strip() or result.stdout.strip()}")
        return
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"MCP self-test returned non-JSON: {exc}")
        return
    if not data.get("html_exists"):
        errors.append("MCP self-test could not find canonical HTML")
    if int(data.get("sections") or 0) < 10:
        errors.append("MCP self-test found too few sections")


def validate() -> int:
    errors: list[str] = []
    for path in [HTML, INDEX, CODEX_MANIFEST, CLAUDE_MANIFEST, MCP_CONFIG, SERVER]:
        require_file(path, errors)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    codex = validate_json(CODEX_MANIFEST, errors)
    claude = validate_json(CLAUDE_MANIFEST, errors)
    mcp = validate_json(MCP_CONFIG, errors)

    for label, manifest in [("Codex", codex), ("Claude", claude)]:
        if manifest.get("name") != "seo-helper":
            errors.append(f"{label} manifest name must be seo-helper")
        if not manifest.get("version"):
            errors.append(f"{label} manifest missing version")
        if not manifest.get("description"):
            errors.append(f"{label} manifest missing description")

    if "mcpServers" not in mcp or "seo-helper-router" not in mcp.get("mcpServers", {}):
        errors.append(".mcp.json must define mcpServers.seo-helper-router")

    sections = load_sections()
    if len(sections) < 10:
        errors.append("Knowledgebase has too few <section id=...> blocks")

    index_text = INDEX.read_text(encoding="utf-8", errors="ignore")
    for section in sections:
        if f"| {section['id']} |" not in index_text:
            errors.append(f"Section index missing: {section['id']}")

    html_text = HTML.read_text(encoding="utf-8", errors="ignore")
    duplicate_root_html = REPO / "SEO_Action_Decision_System.html"
    if duplicate_root_html.exists():
        errors.append("Duplicate root SEO_Action_Decision_System.html exists. Keep only plugins/seo-helper/knowledge copy.")
    if "seo-teacher" in html_text.lower():
        errors.append("Knowledgebase still contains old seo-teacher naming")

    run_self_test(errors)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print("SEO Helper validation passed")
    print(f"Canonical knowledgebase: {HTML}")
    print(f"Sections: {len(sections)}")
    return 0


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def add_rule(args: argparse.Namespace) -> None:
    title = args.title.strip()
    body = args.body.strip()
    before = args.before.strip()
    if not title or not body or not before:
        raise SystemExit("add-rule requires --title, --body, and --before")
    text = HTML.read_text(encoding="utf-8")
    marker_options = [f"      <h3>{before}</h3>", f"    <section id=\"{before}\">", before]
    marker = next((candidate for candidate in marker_options if candidate in text), None)
    if not marker:
        raise SystemExit(f"Could not find insertion marker: {before}")
    block = (
        f"      <h3>{html_escape(title)}</h3>\n"
        f"      <p>{html_escape(body)}</p>\n"
        f"      <p><strong>Decision rule:</strong> {html_escape(args.decision.strip())}</p>\n"
    )
    text = text.replace(marker, block + marker, 1)
    HTML.write_text(text, encoding="utf-8")
    print(f"Added rule before marker: {before}")
    print("Run: python scripts/maintain.py rebuild-index")
    print("Run: python scripts/maintain.py validate")


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain the SEO Helper plugin")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("rebuild-index")
    add = sub.add_parser("add-rule")
    add.add_argument("--title", required=True)
    add.add_argument("--body", required=True)
    add.add_argument("--decision", required=True)
    add.add_argument("--before", required=True, help="Existing h3 title, section id, or exact marker text")
    args = parser.parse_args()
    if args.command == "validate":
        return validate()
    if args.command == "rebuild-index":
        rebuild_index()
        return 0
    if args.command == "add-rule":
        add_rule(args)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

