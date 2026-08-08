# Install seo-* Agent Skills into common host folders (Windows).
param(
    [string[]]$Targets = @("claude", "cursor", "codex"),
    [switch]$SkipPythonPackages,
    [switch]$RegisterPlugin
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsSrc = Join-Path $Root "skills"
$CommandsSrc = Join-Path $Root "commands"

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
$CommandsNsSrc = Join-Path $CommandsSrc "seo-helper"
if (Test-Path $CommandsNsSrc) {
    $commandTargets = @(
        (Join-Path $env:USERPROFILE ".claude\commands")
        (Join-Path $env:USERPROFILE ".cursor\commands")
        (Join-Path $env:USERPROFILE ".codex\commands")
        (Join-Path $env:USERPROFILE ".agents\commands")
    )

    foreach ($cmdRoot in $commandTargets) {
        $nsDir = Join-Path $cmdRoot "seo-helper"
        New-Item -ItemType Directory -Force -Path $nsDir | Out-Null
        # Remove old flat seo-*.md aliases from previous installs
        Get-ChildItem -Path $cmdRoot -Filter "seo-*.md" -File -ErrorAction SilentlyContinue | Remove-Item -Force
        Remove-Item -Force (Join-Path $cmdRoot "seo-helper.md") -ErrorAction SilentlyContinue

        Get-ChildItem -Path $CommandsNsSrc -Filter "*.md" | ForEach-Object {
            $dest = Join-Path $nsDir $_.Name
            Copy-Item -Force $_.FullName $dest
            Write-Host "Installed /seo-helper:$($_.BaseName) -> $dest"
        }
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

    # Register seo-helper-router MCP server in Claude Desktop config so the live
    # MCP tools (route_seo_situation, get_decision_section, etc.) are available
    # in both the Home and Code tabs of Claude Desktop.
    # Python does the JSON merge to avoid PowerShell 5.1 serialization issues.
    $serverScript = Join-Path $Root "server\seo_router_server.py"
    $registerScript = Join-Path $Root "scripts\register_mcp.py"
    if ((Test-Path $serverScript) -and (Test-Path $registerScript)) {
        $claudeConfigDir = Join-Path $env:APPDATA "Claude"
        $claudeConfigFile = Join-Path $claudeConfigDir "claude_desktop_config.json"

        $pythonExe = (Get-Command python -ErrorAction SilentlyContinue)
        $pythonPath = if ($pythonExe) { $pythonExe.Source } else { "python" }

        & $pythonPath $registerScript claude $serverScript $Root $claudeConfigFile --python $pythonPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Restart Claude Desktop to activate MCP tools in all tabs."
        } else {
            Write-Warning "MCP registration failed. Add seo-helper-router manually to $claudeConfigFile"
        }

        # Register in OpenAI Codex (ChatGPT desktop) if installed.
        $codexConfig = Join-Path $env:USERPROFILE ".codex\config.toml"
        if (Test-Path (Split-Path $codexConfig)) {
            & $pythonPath $registerScript codex $serverScript $Root $codexConfig --python $pythonPath
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Restart Codex (ChatGPT desktop) to activate MCP tools."
            } else {
                Write-Warning "Codex MCP registration failed. Add seo-helper-router manually to $codexConfig"
            }
        }
    }
}

Write-Host ""
Write-Host "Done. SEO Helper skills are installed."
