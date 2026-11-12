# Claude/hooks/limit-resume.ps1 - StopFailure (rate_limit): records the usage limit and starts a watcher that, after the reset, types "continue" into this
# same Claude Code session (logic in limit_resume.py and limit-wake.ps1). Silent no-op without Python. Off switch: create Claude/relay/NO-RESUME.
$ErrorActionPreference = "SilentlyContinue"
$script = Join-Path $PSScriptRoot "limit_resume.py"
if (-not (Test-Path $script)) { exit 0 }
$in = [Console]::In.ReadToEnd()
# the Claude Code process is the nearest ancestor of this hook that is claude.exe, or node.exe running claude
$claudePid = 0
try {
    $id = $PID
    for ($i = 0; $i -lt 14 -and $id; $i++) {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$id"
        if (-not $p) { break }
        if ($i -gt 0 -and $p.Name -match '^(claude|node)(\.exe)?$' -and ($p.Name -match '^claude' -or $p.CommandLine -match 'claude')) { $claudePid = [int]$p.ProcessId; break }
        $id = $p.ParentProcessId
    }
} catch {}
foreach ($cand in @(@("py","-3"), @("python"), @("python3"))) {
    $exe = Get-Command $cand[0] -ErrorAction SilentlyContinue
    if (-not $exe) { continue }
    $pre = @(); if ($cand.Count -gt 1) { $pre = @($cand[1]) }
    $extra = @(); if ($claudePid -gt 0) { $extra = @("--pid", "$claudePid") }
    $in | & $exe.Source @pre $script hook @extra | Out-Null
    exit 0
}
exit 0
