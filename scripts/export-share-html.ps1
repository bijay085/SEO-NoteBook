param(
  [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot "plugins/seo-helper/knowledge/SEO_Action_Decision_System.html"
$export = Join-Path $repoRoot "SEO_Action_Decision_System.html"

if (-not (Test-Path -LiteralPath $source)) {
  throw "Canonical knowledgebase not found: $source"
}

if ($CheckOnly) {
  if (-not (Test-Path -LiteralPath $export)) {
    throw "Share export not found: $export"
  }
  $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
  $exportHash = (Get-FileHash -LiteralPath $export -Algorithm SHA256).Hash
  if ($sourceHash -ne $exportHash) {
    throw "Share export is out of sync. Run: .\scripts\export-share-html.ps1"
  }
  Write-Host "OK: share export matches canonical knowledgebase."
  exit 0
}

Copy-Item -LiteralPath $source -Destination $export -Force
$sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$exportHash = (Get-FileHash -LiteralPath $export -Algorithm SHA256).Hash
if ($sourceHash -ne $exportHash) {
  throw "Export failed: hashes do not match."
}

Write-Host "Exported share HTML: $export"