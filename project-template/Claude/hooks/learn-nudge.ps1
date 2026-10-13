# Claude/hooks/learn-nudge.ps1 - Stop: in a long session, asks Claude to keep learning the map when the code, the documents
# or the devices changed (logic in learn_nudge.py, no AI tokens when nothing changed). Silent no-op without Python.
$ErrorActionPreference = "SilentlyContinue"
$script = Join-Path $PSScriptRoot "learn_nudge.py"
if (-not (Test-Path $script)) { exit 0 }
$in = [Console]::In.ReadToEnd()
foreach ($cand in @(@("py","-3"), @("python"), @("python3"))) {
    $exe = Get-Command $cand[0] -ErrorAction SilentlyContinue
    if (-not $exe) { continue }
    $pre = @(); if ($cand.Count -gt 1) { $pre = @($cand[1]) }
    $in | & $exe.Source @pre $script
    exit 0
}
exit 0
