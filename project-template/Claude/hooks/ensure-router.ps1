# Claude/hooks/ensure-router.ps1 (v1.124.16)
# Makes sure the Dream Router (free models, Models page) is kept alive by its guardian:
# the guardian (dream_router.py supervise) starts the router, starts it again if it stops or crashes, and replaces an
# older version after an update. This script starts the guardian when none is running. Called at every session start,
# when the console starts and when the Models page is opened. Writes in Claude/logs/console-start.log. Always exits 0.
param([string]$ProjectDir = "")
try {
    $drPath = Join-Path $env:USERPROFILE ".claude\hooks\dream_router.py"
    if (-not (Test-Path $drPath)) { exit 0 }
    $log = $null
    if ($ProjectDir) { $log = Join-Path $ProjectDir "Claude\logs\console-start.log" }
    function Log([string]$m) { if ($log) { try { Add-Content -LiteralPath $log -Value ("{0} router: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m) } catch {} } }
    $guardians = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'dream_router\.py' -and $_.CommandLine -match 'supervise' })
    if ($guardians.Count -gt 0) { exit 0 }
    $stop = Join-Path $env:USERPROFILE ".dream-router\STOP"
    if (Test-Path $stop) { Remove-Item -LiteralPath $stop -Force -ErrorAction SilentlyContinue }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { Start-Process -FilePath $py.Source -ArgumentList @("-3", "`"$drPath`"", "supervise") -WindowStyle Hidden }
    else { Start-Process -FilePath "python" -ArgumentList @("`"$drPath`"", "supervise") -WindowStyle Hidden }
    Log "guardian started (it starts the router and restarts it if it stops)"
} catch { }
exit 0
