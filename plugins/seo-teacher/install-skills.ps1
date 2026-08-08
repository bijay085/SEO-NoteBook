# Install seo-* Agent Skills into common host folders (Windows).
param(
    [string[]]$Targets = @("claude", "cursor", "codex")
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsSrc = Join-Path $Root "skills"

# Support -Targets cursor,claude,codex (single comma-separated arg from -File)
$Targets = @(
    $Targets |
        ForEach-Object { $_ -split ',' } |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)

$map = @{
    "claude" = Join-Path $env:USERPROFILE ".claude\skills"
    "cursor" = Join-Path $env:USERPROFILE ".cursor\skills"
    "codex"  = Join-Path $env:USERPROFILE ".codex\skills"
}

$dirs = Get-ChildItem -Path $SkillsSrc -Directory | Where-Object { $_.Name -like "seo-*" }
if (-not $dirs) { throw "No seo-* skill folders found under $SkillsSrc" }

foreach ($t in $Targets) {
    $key = $t.Trim().ToLowerInvariant()
    if (-not $map.ContainsKey($key)) {
        Write-Warning "Unknown target '$t' (use claude, cursor, codex). Skipping."
        continue
    }
    $destRoot = $map[$key]
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
    foreach ($d in $dirs) {
        $dest = Join-Path $destRoot $d.Name
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Copy-Item -Recurse -Force $d.FullName $dest
        Write-Host "Installed $($d.Name) -> $dest"
    }
}

Write-Host ""
Write-Host "Done. Also run: pip install -r `"$Root\requirements.txt`""
Write-Host "Read INSTALL.md + AGENT_RUNTIME.md for MCP / chat-UI setup."
