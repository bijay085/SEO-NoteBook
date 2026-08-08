#!/usr/bin/env bash
# live_verify.sh : verify URLs against the LIVE site before making any claim about them.
# Prints: HTTP status | url | redirect target | rel=canonical | robots(meta+header) | in-sitemap?
# Sandbox rule: a page can be "live" yet noindex or 301'd to junk or missing from the sitemap =
# invisible to Google no matter how much work went into it. NEVER trust a spreadsheet URL list;
# verify. Browser UA + cache-bust defeat Cloudflare/edge caches. macOS bash 3.2 compatible.
#
# Usage: ./live_verify.sh https://site/a/ https://site/b/ (args)
# cat urls.txt | ./live_verify.sh (stdin)
# SITEMAP=https://site/sitemap.xml ./live_verify.sh ... (also checks sitemap membership)
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
SM_CACHE=""
if [ -n "$SITEMAP" ]; then SM_CACHE=$(curl -s -A "$UA" "$SITEMAP" 2>/dev/null); fi
check() {
  url="$1"; [ -z "$url" ] && return
  cb="${url}?nocache=$RANDOM"
  hdr=$(curl -s -A "$UA" -H 'Cache-Control: no-cache' -H 'Pragma: no-cache' -D - -o /tmp/_lv_body.$$ -m 25 "$cb")
  code=$(printf '%s' "$hdr" | awk 'toupper($1) ~ /^HTTP/ {c=$2} END{print c}')
  loc=$(printf '%s' "$hdr" | awk 'BEGIN{IGNORECASE=1}/^location:/{sub(/^[Ll]ocation:[ ]*/,"");print;exit}' | tr -d '\r')
  xrobots=$(printf '%s' "$hdr" | awk 'BEGIN{IGNORECASE=1}/^x-robots-tag:/{sub(/^[^:]*:[ ]*/,"");print;exit}' | tr -d '\r')
  canon=$(grep -io '<link[^>]*rel=["'"'"']canonical["'"'"'][^>]*>' /tmp/_lv_body.$$ 2>/dev/null | head -1 | grep -io 'href=["'"'"'][^"'"'"']*' | sed 's/href=["'"'"']//')
  mrobots=$(grep -io '<meta[^>]*name=["'"'"']robots["'"'"'][^>]*>' /tmp/_lv_body.$$ 2>/dev/null | head -1 | grep -io 'content=["'"'"'][^"'"'"']*' | sed 's/content=["'"'"']//')
  insm="-"
  if [ -n "$SM_CACHE" ]; then case "$SM_CACHE" in *"$url"*) insm="yes";; *) insm="NO";; esac; fi
  robots="${mrobots:-none}"; [ -n "$xrobots" ] && robots="$robots +xrt:$xrobots"
  printf '%s | %s | -> %s | canon:%s | robots:%s | sitemap:%s\n' "${code:-ERR}" "$url" "${loc:-none}" "${canon:-none}" "$robots" "$insm"
  rm -f /tmp/_lv_body.$$
}
if [ "$#" -gt 0 ]; then for u in "$@"; do check "$u"; done
else while IFS= read -r u; do check "$u"; done; fi
