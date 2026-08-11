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

cmd_src="$ROOT/commands/seo-helper"

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

  # Flat seo-* layout for all targets. Namespacing via name: field in SKILL.md.
  # Remove stale seo-helper/ subfolder namespace from previous install attempt.
  if [[ -d "$dest_root/seo-helper" ]] && [[ ! -f "$dest_root/seo-helper/SKILL.md" ]]; then
    rm -rf "$dest_root/seo-helper"
  fi
  for d in "${dirs[@]}"; do
    name="$(basename "$d")"
    rm -rf "$dest_root/$name"
    cp -R "$d" "$dest_root/$name"
    echo "Installed $name -> $dest_root/$name"
  done

  if [[ -d "$ROOT/shared" ]]; then
    rm -rf "$(dirname "$dest_root")/shared" "$dest_root/shared"
    cp -R "$ROOT/shared" "$(dirname "$dest_root")/shared"
    cp -R "$ROOT/shared" "$dest_root/shared"
    echo "Installed shared/ for $t"
  fi

  if [[ -d "$cmd_src" ]]; then
    cmd_root="$(cmd_root_for "$t" || true)"
    if [[ -n "$cmd_root" ]]; then
      ns_dir="$cmd_root/seo-helper"
      mkdir -p "$ns_dir"
      # Remove old flat seo-*.md files from previous installs
      rm -f "$cmd_root"/seo-*.md "$cmd_root/seo-helper.md"
      for f in "$cmd_src"/*.md; do
        cp "$f" "$ns_dir/$(basename "$f")"
        echo "Installed /seo-helper:$(basename "$f" .md) -> $ns_dir/$(basename "$f")"
      done
    fi
  fi
done

echo
echo "Done. Also run: pip install -r \"$ROOT/requirements.txt\""
echo "To activate MCP tools in Claude Desktop, add seo-helper-router to"
echo "  ~/.config/Claude/claude_desktop_config.json (Linux)"
echo "  ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)"
echo "  command: python3, args: [\"$ROOT/server/seo_router_server.py\"]"
echo "  env: { SEO_HELPER_ROOT: \"$ROOT\" }"
