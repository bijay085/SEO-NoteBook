#!/usr/bin/env python3
"""Safely register seo-helper-router MCP into AI desktop app configs.

Supports:
  - Claude Desktop  (%APPDATA%/Claude/claude_desktop_config.json)
  - OpenAI Codex    (~/.codex/config.toml)

Usage:
    # Claude Desktop
    python register_mcp.py claude <server_script> <seo_helper_root> <config_path> [--python <exe>]

    # OpenAI Codex
    python register_mcp.py codex <server_script> <seo_helper_root> <config_path> [--python <exe>]

Exits 0 on success, 1 on error.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Claude Desktop (JSON)
# ---------------------------------------------------------------------------

def register_claude(server_script: str, seo_root: str, config_path: Path, python_exe: str) -> int:
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.is_file():
        raw = config_path.read_text(encoding="utf-8")
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Warning: existing config is invalid JSON ({e}), starting fresh.", file=sys.stderr)
            config = {}
    else:
        config = {}

    if not isinstance(config.get("mcpServers"), dict):
        config["mcpServers"] = {}

    config["mcpServers"]["seo-helper-router"] = {
        "command": python_exe,
        "args": [server_script],
        "env": {"SEO_HELPER_ROOT": seo_root},
    }

    if config_path.is_file():
        shutil.copy2(config_path, config_path.with_suffix(".json.bak"))

    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registered seo-helper-router MCP in {config_path}")
    return 0


# ---------------------------------------------------------------------------
# OpenAI Codex (TOML append/replace)
# ---------------------------------------------------------------------------

def _toml_escape(s: str) -> str:
    """Return a TOML single-quoted string (no escapes needed inside '')."""
    if "'" not in s:
        return f"'{s}'"
    # Fall back to double-quoted with backslash escaping.
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def register_codex(server_script: str, seo_root: str, config_path: Path, python_exe: str) -> int:
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the TOML block we want to add/replace.
    block = (
        "\n[mcp_servers.seo-helper-router]\n"
        f"args = [{_toml_escape(server_script)}]\n"
        f"command = {_toml_escape(python_exe)}\n"
        "startup_timeout_sec = 30\n"
        "\n[mcp_servers.seo-helper-router.env]\n"
        f"SEO_HELPER_ROOT = {_toml_escape(seo_root)}\n"
    )

    if config_path.is_file():
        text = config_path.read_text(encoding="utf-8")
        shutil.copy2(config_path, config_path.with_suffix(".toml.bak"))
    else:
        text = ""

    # Remove any existing seo-helper-router section(s) using a regex that
    # captures from the section header up to (but not including) the next
    # top-level or same-level header, or end-of-file.
    pattern = re.compile(
        r"\n\[mcp_servers\.seo-helper-router\][^\[]*"
        r"(?:\[mcp_servers\.seo-helper-router\.env\][^\[]*)?",
        re.DOTALL,
    )
    text = pattern.sub("", text)

    text = text.rstrip("\n") + "\n" + block

    config_path.write_text(text, encoding="utf-8")
    print(f"Registered seo-helper-router MCP in {config_path}")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if len(args) < 4:
        print(
            "Usage: register_mcp.py <claude|codex> <server_script> <seo_helper_root> <config_path>"
            " [--python <exe>]",
            file=sys.stderr,
        )
        return 1

    mode, server_script, seo_root, config_path_str = args[0], args[1], args[2], args[3]

    python_exe = sys.executable
    if "--python" in args:
        idx = args.index("--python")
        if idx + 1 < len(args):
            python_exe = args[idx + 1]

    config_path = Path(config_path_str)

    if mode == "claude":
        return register_claude(server_script, seo_root, config_path, python_exe)
    elif mode == "codex":
        return register_codex(server_script, seo_root, config_path, python_exe)
    else:
        print(f"Unknown mode '{mode}'. Use 'claude' or 'codex'.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
