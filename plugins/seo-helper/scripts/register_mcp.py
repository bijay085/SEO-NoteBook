#!/usr/bin/env python3
"""Safely merge seo-helper-router into Claude Desktop claude_desktop_config.json.

Usage:
    python register_mcp.py <server_script_path> <seo_helper_root> <config_path> [--python <python_exe>]

Exits 0 on success, 1 on error.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3:
        print("Usage: register_mcp.py <server_script> <seo_helper_root> <config_path> [--python <exe>]", file=sys.stderr)
        return 1

    server_script = args[0]
    seo_root = args[1]
    config_path = Path(args[2])

    python_exe = sys.executable
    if "--python" in args:
        idx = args.index("--python")
        if idx + 1 < len(args):
            python_exe = args[idx + 1]

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

    # Write with backup
    if config_path.is_file():
        shutil.copy2(config_path, config_path.with_suffix(".json.bak"))

    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registered seo-helper-router MCP in {config_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
