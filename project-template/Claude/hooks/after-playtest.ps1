# Claude/hooks/after-playtest.ps1
#
# The matcher in .claude/settings.json fires on EVERY call to mcp__unreal-mcp__call_tool
# (the unreal-mcp server uses a single dispatcher for all of its actions, not one tool per
# action). The real filter is here: we read the hook's JSON payload from stdin and proceed
# ONLY if this specific call is actually a play-session/game stop - otherwise we exit
# immediately, doing nothing (so as not to run qa-regression/planner-docs on every single
# MCP call, which would waste tokens).
#
# If this script never fires (or always fires), check the exact shape of the payload:
# uncomment the two $debug lines below to log the raw payload once, look at
# Claude/logs/raw-hook-payloads.log, and adjust the $isStopSession regex accordingly.

$ErrorActionPreference = "Stop"
$projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
Set-Location $projectDir

$stdin = [Console]::In.ReadToEnd()

# $debugLog = Join-Path $projectDir "Claude\logs\raw-hook-payloads.log"
# New-Item -ItemType Directory -Force -Path (Split-Path $debugLog) | Out-Null
# $stdin | Out-File -Append $debugLog

# Filter: we treat "play-session ended" as any call whose payload explicitly mentions a
# session/game stop, wherever that field is nested in the JSON.
$isStopSession = $stdin -match '(?i)stopgame|stopsession|stop_session|stop_game'

if (-not $isStopSession) {
    exit 0
}

$logsDir = Join-Path $projectDir "Claude\logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $logsDir "auto-postplaytest-$timestamp.log"

"=== qa-regression (started $(Get-Date)) ===" | Out-File -Append -FilePath $log
try {
    claude -p "A test play-session in this project just ended. Analyze logs and project state to find regressions and bugs not yet reported, compared to what's documented as working in Claude/docs/STATUS.md. Add whatever you find to Claude/docs/BUGS.md, under the Newly reported section." --agent qa-regression 2>&1 | Out-File -Append -FilePath $log
} catch {
    "qa-regression returned an error, check the log." | Out-File -Append -FilePath $log
}

"=== planner-docs (started $(Get-Date)) ===" | Out-File -Append -FilePath $log
try {
    claude -p "qa-regression just analyzed the last play-session (see $log and Claude/docs/BUGS.md, Newly reported section). Update Claude/docs/STATUS.md with a new entry and reprioritize Claude/docs/BUGS.md." --agent planner-docs 2>&1 | Out-File -Append -FilePath $log
} catch {
    "planner-docs returned an error, check the log." | Out-File -Append -FilePath $log
}

Write-Output "Automatic post-playtest check complete. Details in $log"
