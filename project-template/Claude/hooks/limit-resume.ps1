# Claude/hooks/limit-resume.ps1 - StopFailure (rate_limit): records the usage limit and starts a watcher that opens a new Cod window after the reset
# (logic in limit_resume.py). Silent no-op without Python. Off switch: create Claude/relay/NO-RESUME.
$ErrorActionPreference = "SilentlyContinue"
$script = Join-Path $PSScriptRoot "limit_resume.py"
if (-not (Test-Path $script)) { exit 0 }
$in = [Console]::In.ReadToEnd()
foreach ($cand in @(@("py","-3"), @("python"), @("python3"))) {
    $exe = Get-Command $cand[0] -ErrorAction SilentlyContinue
    if (-not $exe) { continue }
    $pre = @(); if ($cand.Count -gt 1) { $pre = @($cand[1]) }
    $in | & $exe.Source @pre $script hook | Out-Null
    exit 0
}
exit 0
