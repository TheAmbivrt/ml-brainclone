# larry-startup.ps1
# Startar Larry-ekosystemet: 4 separata WT-foenstren (Larry, Barry, Harry, Parry) + Obsidian.
# - Oeppnar varje agent i sitt eget foenstret med ratt profil och faerg
# - Laesar positioner fraan window-positions.json (koer larry-save-positions.ps1 foerst)
# - Skippar agenter som redan koer (single instance per agent)

param(
    [int]$DelaySeconds = 5
)

Start-Sleep -Seconds $DelaySeconds

# --- Hjaelpfunktion: kontrollera om ett agent-foenstret redan aer oeppet ---
function Test-AgentRunning([string]$agentName) {
    $procs = Get-Process WindowsTerminal -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        if ($p.MainWindowTitle -like "*$agentName*") { return $true }
    }
    return $false
}

# --- Laas positionskonfig ---
$posFile = "$PSScriptRoot\window-positions.json"
$positions = $null
if (Test-Path $posFile) {
    $positions = Get-Content $posFile -Encoding UTF8 | ConvertFrom-Json
} else {
    Write-Host "[VARNING] window-positions.json saknas - oeppnar utan positionsdata." -ForegroundColor Yellow
    Write-Host "          Koer scripts\larry-save-positions.ps1 efter att ha positionerat foenstren." -ForegroundColor Yellow
}

# --- Obsidian ---
$obsidianExe = "$env:LOCALAPPDATA\Programs\Obsidian\Obsidian.exe"
if (Test-Path $obsidianExe) {
    $already = Get-Process Obsidian -ErrorAction SilentlyContinue
    if (-not $already) {
        Start-Process $obsidianExe -WindowStyle Minimized
        Write-Host "[OK] Obsidian startad"
    } else {
        Write-Host "[--] Obsidian koer redan"
    }
}

# --- Agenter ---
$agents = @(
    @{ Name = "Larry"; Profile = "Larry" },
    @{ Name = "Barry"; Profile = "Barry" },
    @{ Name = "Harry"; Profile = "Harry" },
    @{ Name = "Parry"; Profile = "Parry" }
)

foreach ($agent in $agents) {
    $name    = $agent.Name
    $profile = $agent.Profile

    if (Test-AgentRunning $name) {
        Write-Host "[--] $name koer redan, hoppar oever"
        continue
    }

    # Bygg argument
    $posArg = ""
    if ($positions -and $positions.$name) {
        $x = $positions.$name.X
        $y = $positions.$name.Y
        $posArg = "--pos $x,$y "
    }

    # -w new = foerced separat foenstret (inte ny flik i befintligt)
    # --title saetter foensternamnet sa att Test-AgentRunning kan hitta det
    $wtArgs = "$($posArg)-w new new-tab --profile `"$profile`" --title `"$name`""
    Start-Process "wt.exe" -ArgumentList $wtArgs

    Write-Host "[OK] $name startad$(if ($posArg) { `" (pos: $($positions.$name.X),$($positions.$name.Y))`" })"

    # Kort paus saa att WT hinner registrera foenstret innan naesta
    Start-Sleep -Milliseconds 600
}

Write-Host ""
Write-Host "Larry-ekosystemet aer igaang."
