# SEO Helper — Windows installer
# Remote (no clone needed):
#   irm https://raw.githubusercontent.com/bijay085/SEO-NoteBook/main/install.ps1 | iex
# Local (after cloning):
#   powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [string[]]$Targets        = @("claude", "cursor", "codex"),
    [switch]$SkipPythonPackages,
    [switch]$RegisterPlugin
)

$ErrorActionPreference = "Stop"
$repoUrl    = "https://github.com/bijay085/SEO-NoteBook"
$installDir = Join-Path $env:LOCALAPPDATA "seo-helper"

# ---------------------------------------------------------------------------
# REMOTE MODE: piped via irm … | iex — $MyInvocation.MyCommand.Path is empty.
# Clone/update the repo, then re-run this same script from the local copy.
# ---------------------------------------------------------------------------
if (-not $MyInvocation.MyCommand.Path) {
    Write-Host ""
    Write-Host "SEO Helper Installer"
    Write-Host "===================="
    Write-Host ""

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "git is required. Install from https://git-scm.com/download/win then re-run."
        exit 1
    }

    if (Test-Path (Join-Path $installDir ".git")) {
        Write-Host "Updating existing install at $installDir ..."
        git -C $installDir pull --ff-only
        if ($LASTEXITCODE -ne 0) { Write-Warning "git pull had an issue. Continuing with existing files." }
    } else {
        Write-Host "Cloning SEO Helper to $installDir ..."
        git clone --depth 1 $repoUrl $installDir
        if ($LASTEXITCODE -ne 0) { Write-Error "Clone failed. Check internet and try again."; exit 1 }
    }

    $localScript = Join-Path $installDir "install.ps1"
    powershell -ExecutionPolicy Bypass -File $localScript -Targets ($Targets -join ",") -RegisterPlugin
    exit $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# LOCAL MODE: running from the cloned/local repo.
# ---------------------------------------------------------------------------
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "SEO Helper Installer"
Write-Host "===================="
Write-Host ""

# Normalize comma-joined targets (e.g. -Targets claude,cursor,codex)
$Targets = @($Targets | ForEach-Object { $_ -split "," } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

# --- Python ----------------------------------------------------------------
$pythonCmd = $null
foreach ($c in @("python", "py")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $pythonCmd = $c; break }
}
if (-not $pythonCmd) {
    Write-Host "Python not found. Installing Python 3.12 via winget..."
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Error "winget not found. Install Python from https://www.python.org/downloads/ (tick 'Add to PATH') then re-run."
        exit 1
    }
    winget install --id Python.Python.3.12 --source winget --scope user --accept-package-agreements --accept-source-agreements
    $env:PATH = "$env:LOCALAPPDATA\Programs\Python\Python312\;$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\;$env:PATH"
    $pythonCmd = "python"
}
Write-Host "Python: $((& $pythonCmd --version 2>&1))"

# --- Python packages -------------------------------------------------------
if (-not $SkipPythonPackages) {
    Write-Host ""
    Write-Host "Installing Python packages..."
    & $pythonCmd -m pip install --upgrade pip --quiet
    & $pythonCmd -m pip install -r (Join-Path $Root "requirements.txt") --quiet
    $srvReq = Join-Path $Root "server\requirements.txt"
    if (Test-Path $srvReq) { & $pythonCmd -m pip install -r $srvReq --quiet }
}

# --- Skills ----------------------------------------------------------------
$SkillsSrc = Join-Path $Root "skills"
$dirs = Get-ChildItem -Path $SkillsSrc -Directory | Where-Object { $_.Name -like "seo-*" }
if (-not $dirs) { throw "No seo-* skill folders found under $SkillsSrc" }

$skillMap = @{
    claude = Join-Path $env:USERPROFILE ".claude\skills"
    cursor = Join-Path $env:USERPROFILE ".cursor\skills"
    codex  = Join-Path $env:USERPROFILE ".codex\skills"
}

foreach ($t in $Targets) {
    $key = $t.ToLowerInvariant()
    if (-not $skillMap.ContainsKey($key)) { Write-Warning "Unknown target '$t'. Skipping."; continue }
    $destRoot = $skillMap[$key]
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null

    # Remove stale seo-helper/ subfolder namespace from old installs
    $stale = Join-Path $destRoot "seo-helper"
    if ((Test-Path $stale) -and -not (Test-Path (Join-Path $stale "SKILL.md"))) {
        Remove-Item -Recurse -Force $stale
    }

    foreach ($d in $dirs) {
        $dest = Join-Path $destRoot $d.Name
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Copy-Item -Recurse -Force $d.FullName $dest
        Write-Host "  skill $($d.Name) -> $destRoot"
    }
}

# --- Commands --------------------------------------------------------------
$CmdNsSrc = Join-Path $Root "commands\seo-helper"
if (Test-Path $CmdNsSrc) {
    $cmdRoots = @(
        Join-Path $env:USERPROFILE ".claude\commands"
        Join-Path $env:USERPROFILE ".cursor\commands"
        Join-Path $env:USERPROFILE ".codex\commands"
        Join-Path $env:USERPROFILE ".agents\commands"
    )
    foreach ($cmdRoot in $cmdRoots) {
        $nsDir = Join-Path $cmdRoot "seo-helper"
        New-Item -ItemType Directory -Force -Path $nsDir | Out-Null
        Get-ChildItem -Path $cmdRoot -Filter "seo-*.md" -File -ErrorAction SilentlyContinue | Remove-Item -Force
        Remove-Item -Force (Join-Path $cmdRoot "seo-helper.md") -ErrorAction SilentlyContinue
        Get-ChildItem -Path $CmdNsSrc -Filter "*.md" | ForEach-Object {
            Copy-Item -Force $_.FullName (Join-Path $nsDir $_.Name)
        }
        Write-Host "  commands -> $nsDir"
    }
}

# --- Plugin registry -------------------------------------------------------
if ($RegisterPlugin) {
    Write-Host ""
    Write-Host "Registering plugin..."

    $marketRoot   = Join-Path $env:USERPROFILE ".agents\plugins"
    $marketPlugin = Join-Path $marketRoot "plugins\seo-helper"
    $marketFile   = Join-Path $marketRoot "marketplace.json"

    New-Item -ItemType Directory -Force -Path $marketPlugin | Out-Null
    Copy-Item -Path (Join-Path $Root "*") -Destination $marketPlugin -Recurse -Force

    if (Test-Path $marketFile) {
        $market = Get-Content -Raw $marketFile | ConvertFrom-Json
        if (-not $market.plugins) { $market | Add-Member -MemberType NoteProperty -Name plugins -Value @() }
    } else {
        New-Item -ItemType Directory -Force -Path $marketRoot | Out-Null
        $market = [pscustomobject]@{
            name      = "personal"
            interface = [pscustomobject]@{ displayName = "Personal" }
            plugins   = @()
        }
    }
    $entry = [pscustomobject]@{
        name   = "seo-helper"
        source = [pscustomobject]@{ source = "local"; path = "./plugins/seo-helper" }
        policy = [pscustomobject]@{ installation = "AVAILABLE"; authentication = "ON_INSTALL" }
        category = "Productivity"
    }
    $market.plugins = @(@($market.plugins | Where-Object { $_.name -ne "seo-helper" }) + $entry)
    $market | ConvertTo-Json -Depth 12 | Set-Content -Path $marketFile -Encoding UTF8
    Write-Host "  plugin registry -> $marketFile"

    # MCP registration
    $serverScript   = Join-Path $Root "server\seo_router_server.py"
    $registerScript = Join-Path $Root "scripts\register_mcp.py"
    if ((Test-Path $serverScript) -and (Test-Path $registerScript)) {
        $py = (Get-Command $pythonCmd).Source
        $claudeCfg = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
        & $py $registerScript claude $serverScript $Root $claudeCfg --python $py
        if ($LASTEXITCODE -eq 0) { Write-Host "  MCP -> Claude Desktop (restart to activate)" }
        else { Write-Warning "  MCP registration failed for Claude Desktop" }

        $codexCfg = Join-Path $env:USERPROFILE ".codex\config.toml"
        if (Test-Path (Split-Path $codexCfg)) {
            & $py $registerScript codex $serverScript $Root $codexCfg --python $py
            if ($LASTEXITCODE -eq 0) { Write-Host "  MCP -> Codex (restart to activate)" }
            else { Write-Warning "  MCP registration failed for Codex" }
        }
    }
}

Write-Host ""
Write-Host "Done. SEO Helper installed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart Claude Desktop and Codex to activate MCP tools."
Write-Host "  2. In Claude Code: /seo-helper:<command>"
Write-Host "  3. In Codex:       /seo-helper to see skills"
Write-Host ""
Write-Host "To update: irm https://raw.githubusercontent.com/bijay085/SEO-NoteBook/main/install.ps1 | iex"
