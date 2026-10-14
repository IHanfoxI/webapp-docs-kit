# webapp-docs-kit installer for Windows.
#   powershell -ExecutionPolicy Bypass -File install.ps1                      -> for your user
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Project C:\path    -> copied into a project
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Uninstall          -> removes the links
# Uses junctions (no admin rights or developer mode needed) instead of symbolic links.
#
# Skill folders per agent (user scope):
#   %USERPROFILE%\.claude\skills   Claude Code
#   %USERPROFILE%\.agents\skills   Codex, Gemini CLI, GitHub Copilot, OpenCode and other Agent Skills clients
#   %USERPROFILE%\.cursor\skills   Cursor (only if .cursor exists)
param([string]$Project, [switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$Root = $PSScriptRoot
$Skills = @('visual-check', 'user-manual', 'video-tutorial')
$Scripts = Join-Path $Root 'skills\visual-check\scripts'

$Targets = @((Join-Path $HOME '.claude\skills'), (Join-Path $HOME '.agents\skills'))
if (Test-Path (Join-Path $HOME '.cursor')) { $Targets += (Join-Path $HOME '.cursor\skills') }

function Test-Link([string]$path) {
    (Test-Path $path) -and ((Get-Item $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)
}

if ($Uninstall) {
    foreach ($dir in $Targets) {
        foreach ($s in $Skills) {
            $link = Join-Path $dir $s
            if (Test-Link $link) { cmd /c rmdir "$link" | Out-Null; Write-Host "Removed $link" }
        }
    }
    exit 0
}

if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host 'Node.js 18+ is required: winget install OpenJS.NodeJS.LTS' -ForegroundColor Red
    exit 1
}
$missing = @()
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { $missing += 'ffmpeg (video-tutorial)' }
if (-not (Get-Command pdftoppm -ErrorAction SilentlyContinue)) { $missing += 'Poppler (user-manual)' }
if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command py -ErrorAction SilentlyContinue)) { $missing += 'Python (user-manual)' }
$lo = @('C:\Program Files', 'C:\Program Files (x86)') |
      ForEach-Object { Join-Path $_ 'LibreOffice\program\soffice.exe' } | Where-Object { Test-Path $_ }
$word = Test-Path 'Registry::HKEY_CLASSES_ROOT\Word.Application'
if (-not $lo -and -not $word) { $missing += 'LibreOffice or Microsoft Word (user-manual)' }
if ($missing.Count) { Write-Host "Optional tools not found: $($missing -join ', '). See docs\prerequisites.md." -ForegroundColor Yellow }

Push-Location $Scripts
try {
    npm install --silent
    if ($LASTEXITCODE) { throw 'npm install failed' }
    node node_modules\playwright-core\cli.js install chromium
    if ($LASTEXITCODE) { throw 'Chromium could not be installed' }
} finally { Pop-Location }

function Link-Into([string]$dest) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    foreach ($s in $Skills) {
        $link = Join-Path $dest $s
        if (Test-Path $link) {
            if (-not (Test-Link $link)) { Write-Host "Skipped $link`: it exists and is not a link"; continue }
            cmd /c rmdir "$link" | Out-Null   # removes only the link, not its contents
        }
        New-Item -ItemType Junction -Path $link -Target (Join-Path $Root "skills\$s") | Out-Null
        Write-Host "Linked $link"
    }
}

if ($Project) {
    # A copy (not a link) so it travels with the project's repository.
    foreach ($dest in @((Join-Path $Project '.claude\skills'), (Join-Path $Project '.agents\skills'))) {
        foreach ($s in $Skills) {
            robocopy (Join-Path $Root "skills\$s") (Join-Path $dest $s) /MIR /XD node_modules /NFL /NDL /NJH /NJS | Out-Null
            if ($LASTEXITCODE -ge 8) { throw "copying $s failed" }
            Write-Host "Copied $dest\$s"
        }
    }
    Write-Host "Run npm install in $Project\.claude\skills\visual-check\scripts (and .agents\...) before first use."
} else {
    foreach ($dir in $Targets) { Link-Into $dir }
}
Write-Host 'Done. Restart your agent and try /visual-check, /user-manual or /video-tutorial in a project.' -ForegroundColor Green
