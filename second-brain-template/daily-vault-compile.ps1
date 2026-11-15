<#
.SYNOPSIS
    Daily vault compile script for the second brain.
    Runs the daily free checks and logs to <vault>/output/upkeep/scheduler.log.

.DESCRIPTION
    This script is intended to be run via Windows Task Scheduler (schtasks) once per day.
    It calls brain_upkeep.py in "free" mode to run the daily free checks (links, dups, stats, status, Clippings count)
    and logs the result to the scheduler log.

    With the mailbox worker (point 3 in the upkeep design), this scheduled task is NO LONGER NEEDED
    because the mailbox worker will start the real pass when the inbox is empty.
    However, the daily free checks still run at session start via brain_brief.py start hook.

.PARAMETER Vault
    Path to the second brain vault. Defaults to $env:SECOND_BRAIN or the path in ~/.claude/CLAUDE.md.

.PARAMETER Python
    Path to python executable. Defaults to "python" (must be in PATH).

.EXAMPLE
    .\daily-vault-compile.ps1 -Vault "C:\SecondBrainOssidian"

.NOTES
    To register with schtasks (run once daily at 06:00):
    schtasks /create /tn "SecondBrainDailyCompile" /tr "powershell -ExecutionPolicy Bypass -File C:\SecondBrainOssidian\daily-vault-compile.ps1" /sc daily /st 06:00 /rl highest

    To remove:
    schtasks /delete /tn "SecondBrainDailyCompile" /f
#>

param(
    [string]$Vault = "",
    [string]$Python = "python"
)

# Determine vault path
if (-not $Vault) {
    $Vault = $env:SECOND_BRAIN
    if (-not $Vault) {
        $claudeMd = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"
        if (Test-Path $claudeMd) {
            $content = Get-Content $claudeMd -Raw
            if ($content -match '\*\*Second brain path\*\*:\s*`([^`]*)`') {
                $Vault = $matches[1]
            }
        }
    }
}

if (-not $Vault -or $Vault -eq "<SECOND_BRAIN_PATH>" -or -not (Test-Path $Vault)) {
    Write-Output "Vault not configured or not found. Skipping."
    exit 0
}

$Vault = Resolve-Path $Vault
$logDir = Join-Path $Vault "output\upkeep"
$logFile = Join-Path $logDir "scheduler.log"

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$hookPath = Join-Path $PSScriptRoot "..\project-template\Claude\hooks\brain_upkeep.py"

if (-not (Test-Path $hookPath)) {
    # Try to find it in the user's .claude folder
    $hookPath = Join-Path $env:USERPROFILE ".claude\project-template\Claude\hooks\brain_upkeep.py"
    if (-not (Test-Path $hookPath)) {
        $hookPath = Join-Path $env:USERPROFILE ".claude\skills\second-brain-query\scripts\..\..\project-template\Claude\hooks\brain_upkeep.py"
    }
}

if (-not (Test-Path $hookPath)) {
    $msg = "$timestamp | ERROR: brain_upkeep.py not found at $hookPath"
    Add-Content -Path $logFile -Value $msg
    Write-Error $msg
    exit 1
}

try {
    $result = & $Python $hookPath free --vault $Vault 2>&1
    $exitCode = $LASTEXITCODE

    if ($result) {
        $msg = "$timestamp | $result"
    } else {
        $msg = "$timestamp | OK: free checks passed"
    }

    Add-Content -Path $logFile -Value $msg
    Write-Output $msg

    if ($exitCode -ne 0) {
        exit $exitCode
    }
}
catch {
    $msg = "$timestamp | EXCEPTION: $($_.Exception.Message)"
    Add-Content -Path $logFile -Value $msg
    Write-Error $msg
    exit 1
}

exit 0