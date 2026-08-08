# SEO Helper — remote installer for Windows
# Usage (no git clone needed):
#   irm https://raw.githubusercontent.com/bijay085/SEO-NoteBook/main/install.ps1 | iex
#
# Clones/updates the repo to %LOCALAPPDATA%\seo-helper, then runs the full
# skill installer so skills, commands, and MCP tools are available in
# Claude, Codex, and Cursor.

$repoUrl  = "https://github.com/bijay085/SEO-NoteBook"
$installDir = Join-Path $env:LOCALAPPDATA "seo-helper"
$pluginDir  = $installDir

Write-Host ""
Write-Host "SEO Helper Installer"
Write-Host "===================="
Write-Host ""

# --- 1. Git check -----------------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is required. Install Git for Windows from https://git-scm.com/download/win then re-run."
    exit 1
}

# --- 2. Clone or update -----------------------------------------------------
if (Test-Path (Join-Path $installDir ".git")) {
    Write-Host "Updating existing install at $installDir ..."
    git -C $installDir pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git pull had an issue. Continuing with existing files."
    }
} else {
    Write-Host "Cloning SEO Helper to $installDir ..."
    git clone --depth 1 $repoUrl $installDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Clone failed. Check your internet connection and try again."
        exit 1
    }
}

# --- 3. Python check --------------------------------------------------------
$pythonCmd = $null
foreach ($candidate in @("python", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $pythonCmd = $candidate
        break
    }
}

if (-not $pythonCmd) {
    Write-Host ""
    Write-Host "Python not found. Installing Python 3.12 via winget..."
    where.exe winget 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "winget not found. Install Python from https://www.python.org/downloads/ (check 'Add to PATH') then re-run."
        exit 1
    }
    winget install --id Python.Python.3.12 --source winget --scope user --accept-package-agreements --accept-source-agreements
    $env:PATH = "$env:LOCALAPPDATA\Programs\Python\Python312\;$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\;$env:PATH"
    $pythonCmd = "python"
}

Write-Host ""
Write-Host "Python: $($pythonCmd) $((& $pythonCmd --version 2>&1))"

# --- 4. Install Python packages ---------------------------------------------
Write-Host ""
Write-Host "Installing Python packages..."
& $pythonCmd -m pip install --upgrade pip --quiet
& $pythonCmd -m pip install -r (Join-Path $pluginDir "requirements.txt") --quiet
& $pythonCmd -m pip install -r (Join-Path $pluginDir "server\requirements.txt") --quiet

# --- 5. Run skill installer -------------------------------------------------
Write-Host ""
Write-Host "Installing skills, commands, and MCP tools..."
$installerScript = Join-Path $pluginDir "install-skills.ps1"
powershell -ExecutionPolicy Bypass -File $installerScript `
    -Targets claude,cursor,codex `
    -SkipPythonPackages `
    -RegisterPlugin

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Skill installer reported an error. Check output above."
} else {
    Write-Host ""
    Write-Host "Done. SEO Helper is installed from $installDir"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Restart Claude Desktop and Codex (ChatGPT) to activate MCP tools."
    Write-Host "  2. In Claude Code type /seo-helper to see all commands."
    Write-Host "  3. In Codex type /seo-helper to see all skills."
    Write-Host ""
    Write-Host "To update later, re-run this same command:"
    Write-Host "  irm https://raw.githubusercontent.com/bijay085/SEO-NoteBook/main/install.ps1 | iex"
}
