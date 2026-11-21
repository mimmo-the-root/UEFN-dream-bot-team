# Claude/hooks/ensure-pipeline.ps1 (v1.0.0)
# Starts the Python pipeline guardian (tools/pipeline_guardian.py supervise) for THIS project: it runs the relay
# pipeline every pipeline.interval_min minutes, restarts a cycle that fails and replaces an older version after an
# update. Hidden window, never starts twice for the same project, respects STOP and pipeline.enabled false.
# Writes in Claude/logs/console-start.log and always exits 0. No Windows scheduler.
param([string]$ProjectDir = "")
try {
    if (-not $ProjectDir) { $ProjectDir = $env:CLAUDE_PROJECT_DIR }
    if (-not $ProjectDir) { exit 0 }
    $lab = Join-Path $ProjectDir "Claude"
    $log = Join-Path $lab "logs\console-start.log"
    function Log([string]$m) { if ($log) { try { Add-Content -LiteralPath $log -Value ("{0} pipeline: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m) } catch {} } }
    $settings = Join-Path $lab "config\kit-settings.json"
    if (Test-Path $settings) {
        $cfg = Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json
        if ($cfg -and $cfg.pipeline -and $cfg.pipeline.enabled -eq $false) { exit 0 }
    }
    if (Test-Path (Join-Path $lab "STOP")) { exit 0 }
    $guard = $env:PIPELINE_GUARDIAN
    if (-not $guard -or -not (Test-Path $guard)) {
        $candidates = @(
            (Join-Path $ProjectDir "Claude\tools\pipeline_guardian.py"),
            (Join-Path $env:USERPROFILE ".claude\hooks\pipeline_guardian.py"),
            (Join-Path $env:USERPROFILE ".claude\kit-template\tools\pipeline_guardian.py"),
            (Join-Path $PSScriptRoot "..\..\tools\pipeline_guardian.py"),
            (Join-Path $PSScriptRoot "..\..\..\tools\pipeline_guardian.py")
        )
        $guard = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    }
    if (-not $guard -or -not (Test-Path $guard)) { Log "guardian not installed (pipeline_guardian.py not found)"; exit 0 }
    $here = [regex]::Escape($ProjectDir)
    $guardians = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match 'pipeline_guardian\.py' -and $_.CommandLine -match 'supervise' -and $_.CommandLine -match $here
    })
    if ($guardians.Count -gt 0) { exit 0 }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { Start-Process -FilePath $py.Source -ArgumentList @("-3", "`"$guard`"", "supervise", "--lab", "`"$lab`"") -WindowStyle Hidden }
    else { Start-Process -FilePath "python" -ArgumentList @("`"$guard`"", "supervise", "--lab", "`"$lab`"") -WindowStyle Hidden }
    Log "guardian started (pipeline cycles every interval; restarts itself after an update)"
} catch { }
exit 0
