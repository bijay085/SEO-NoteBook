#!/usr/bin/env bash
# check_urls.sh — the verification gate.
# Prints HTTP status, redirect target, and rel=canonical for each URL so you can tell a
# real duplicate (two live 200s, each self-canonical) from an already-consolidated one
# (clean slug 301 -> single 200 twin). NEVER claim cannibalization without running this.
#
# Usage:
#   check_urls.sh https://site/a https://site/b ...
#   printf '%s\n' url1 url2 | check_urls.sh
#
# macOS bash 3.2 safe (no mapfile). Requires curl.

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

check_one() {
  u="$1"
  [ -z "$u" ] && return
  tmp=$(mktemp)
  hdr=$(curl -sS -m 15 -A "$UA" -D - -o "$tmp" "$u" 2>/dev/null)
  code=$(printf '%s' "$hdr" | awk 'toupper($1) ~ /^HTTP/{c=$2} END{print c}')
  loc=$(printf '%s' "$hdr" | awk -F': ' 'tolower($1)=="location"{print $2}' | tr -d '\r' | head -1)
  canon=$(grep -oiE '<link[^>]*rel=["'"'"']canonical["'"'"'][^>]*>' "$tmp" \
          | grep -oiE 'href=["'"'"'][^"'"'"']*' | sed -E 's/^href=.//' | head -1)
  printf '%-4s | %-60s | loc=%-45s | canon=%s\n' "${code:-ERR}" "$u" "${loc:--}" "${canon:--}"
  rm -f "$tmp"
}

printf '%-4s | %-60s | %-49s | %s\n' CODE URL REDIRECT CANONICAL
printf -- '----------------------------------------------------------------------------------------------------------------------\n'

if [ "$#" -gt 0 ]; then
  for u in "$@"; do check_one "$u"; done
else
  while IFS= read -r u; do check_one "$u"; done
fi
