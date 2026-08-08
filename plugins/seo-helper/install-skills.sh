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
    codex)  echo "$HOME/.codex/skills" ;;
    *) echo ""; return 1 ;;
  esac
}

shopt -s nullglob
dirs=("$SRC"/seo-*/)
if ((${#dirs[@]} == 0)); then
  echo "No seo-* skill folders found under $SRC" >&2
  exit 1
fi

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
done

echo
echo "Done. Also run: pip install -r \"$ROOT/requirements.txt\""
echo "Read INSTALL.md + AGENT_RUNTIME.md for MCP / chat-UI setup."
