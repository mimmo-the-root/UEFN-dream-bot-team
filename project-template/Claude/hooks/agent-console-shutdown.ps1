# Claude/hooks/agent-console-shutdown.ps1
#
# SessionEnd hook: when the owner ends the session (types exit or /exit, logs out, or the session just ends),
# stop the Agent Console server so it does not stay alive in the background.
# It does NOT stop on /clear or a resume (the session continues), and it only stops a server that
# answers /whoami with THIS project's folder, so a console serving another project is left alone.
#
# MUST NEVER fail loudly: every error is swallowed, script always exits 0.

$ErrorActionPreference = "Stop"
try {
    $projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
    $payload = $null
    try { $payload = [Console]::In.ReadToEnd() | ConvertFrom-Json -ErrorAction Stop } catch {}
    $reason = if ($payload -and $payload.reason) { [string]$payload.reason } else { "other" }
    if ($reason -in @("clear", "resume", "compact")) { exit 0 }

    $port = 8765
    $thisProject = $projectDir.TrimEnd('\', '/')
    $mine = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$port/whoami" -TimeoutSec 2 -UseBasicParsing
        $served = ([string](($resp.Content | ConvertFrom-Json).project)).TrimEnd('\', '/')
        $mine = ($served -eq $thisProject)
    } catch { exit 0 }   # nothing answers: nothing to stop
    if (-not $mine) { exit 0 }

    $lines = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    foreach ($line in $lines) {
        $procId = ($line -split '\s+')[-1]
        if ($procId -match '^\d+$') {
            $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
            if ($procName -match 'powershell|pwsh|python') {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    # Swallow everything - see the header comment above.
}
exit 0
