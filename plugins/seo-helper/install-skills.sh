#!/usr/bin/env bash
# Install seo-* Agent Skills into common host folders (macOS/Linux).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/skills"
TARGETS=("${@:-claude cursor codex}")

dest_for() {
  case "$1" in
    claude) echo "$HOME/.claude/skills" ;;
    cursor) echo "$HOME/.cursor/skills" ;;
    codex) echo "$HOME/.codex/skills" ;;
    *) echo ""; return 1 ;;
  esac
}

shopt -s nullglob
dirs=("$SRC"/seo-*/)
if ((${#dirs[@]} == 0)); then
  echo "No seo-* skill folders found under $SRC" >&2
  exit 1
fi

cmd_src="$ROOT/commands"

cmd_root_for() {
  case "$1" in
    claude) echo "$HOME/.claude/commands" ;;
    cursor) echo "$HOME/.cursor/commands" ;;
    codex)  echo "$HOME/.codex/commands"  ;;
    *)      echo ""; return 1             ;;
  esac
}

for t in $TARGETS; do
  dest_root="$(dest_for "$t" || true)"
  if [[ -z "${dest_root}" ]]; then
    echo "Unknown target '$t' (use claude, cursor, codex). Skipping." >&2
    continue
  fi
  mkdir -p "$dest_root"
  for d in "${dirs[@]}"; do
    name="$(basename "$d")"
    rm -rf "$dest_root/$name"
    cp -R "$d" "$dest_root/$name"
    echo "Installed $name -> $dest_root/$name"
  done

  if [[ -d "$cmd_src" ]]; then
    cmd_root="$(cmd_root_for "$t" || true)"
    if [[ -n "$cmd_root" ]]; then
      mkdir -p "$cmd_root"
      rm -f "$cmd_root/seo-helper.md"
      for f in "$cmd_src"/seo-*.md; do
        cp "$f" "$cmd_root/$(basename "$f")"
        echo "Installed /$(basename "$f" .md) command -> $cmd_root/$(basename "$f")"
      done
    fi
  fi
done

echo
echo "Done. Also run: pip install -r \"$ROOT/requirements.txt\""
echo "To activate MCP tools in Claude Desktop, add seo-helper-router to"
echo "  ~/.config/Claude/claude_desktop_config.json (Linux)"
echo "  ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)"
echo "  command: python, args: [\"$ROOT/server/seo_router_server.py\"]"
echo "  env: { SEO_HELPER_ROOT: \"$ROOT\" }"
