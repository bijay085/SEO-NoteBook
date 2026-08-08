# Install seo-* Agent Skills into common host folders (Windows).
param(
    [string[]]$Targets = @("claude", "cursor", "codex"),
    [switch]$SkipPythonPackages,
    [switch]$RegisterPlugin
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsSrc = Join-Path $Root "skills"

# Support -Targets cursor,claude,codex as a single comma-separated arg.
$Targets = @(
    $Targets |
        ForEach-Object { $_ -split ',' } |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)

$map = @{
    "claude" = Join-Path $env:USERPROFILE ".claude\skills"
    "cursor" = Join-Path $env:USERPROFILE ".cursor\skills"
    "codex" = Join-Path $env:USERPROFILE ".codex\skills"
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

if (-not $SkipPythonPackages) {
    Write-Host ""
    Write-Host "Installing Python packages..."
    python -m pip install --upgrade pip
    python -m pip install -r (Join-Path $Root "requirements.txt")
    $serverReq = Join-Path $Root "server\requirements.txt"
    if (Test-Path $serverReq) {
        python -m pip install -r $serverReq
    }
}

if ($RegisterPlugin) {
    Write-Host ""
    Write-Host "Registering SEO Helper plugin for app/plugin pickers..."
    $marketRoot = Join-Path $env:USERPROFILE ".agents\plugins"
    $marketPlugins = Join-Path $marketRoot "plugins"
    $marketPlugin = Join-Path $marketPlugins "seo-helper"
    $marketFile = Join-Path $marketRoot "marketplace.json"

    New-Item -ItemType Directory -Force -Path $marketPlugin | Out-Null
    Copy-Item -Path (Join-Path $Root "*") -Destination $marketPlugin -Recurse -Force

    if (Test-Path $marketFile) {
        $market = Get-Content -Raw -Path $marketFile | ConvertFrom-Json
        if (-not $market.plugins) {
            $market | Add-Member -MemberType NoteProperty -Name plugins -Value @()
        }
    } else {
        New-Item -ItemType Directory -Force -Path $marketRoot | Out-Null
        $market = [pscustomobject]@{
            name = "personal"
            interface = [pscustomobject]@{ displayName = "Personal" }
            plugins = @()
        }
    }

    $entry = [pscustomobject]@{
        name = "seo-helper"
        source = [pscustomobject]@{
            source = "local"
            path = "./plugins/seo-helper"
        }
        policy = [pscustomobject]@{
            installation = "AVAILABLE"
            authentication = "ON_INSTALL"
        }
        category = "Productivity"
    }

    $kept = @($market.plugins | Where-Object { $_.name -ne "seo-helper" })
    $market.plugins = @($kept + $entry)
    $market | ConvertTo-Json -Depth 12 | Set-Content -Path $marketFile -Encoding UTF8
    Write-Host "Registered seo-helper in $marketFile"
}

Write-Host ""
Write-Host "Done. SEO Helper skills are installed."
