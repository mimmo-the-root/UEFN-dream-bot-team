# Claude/hooks/kit-sync.ps1 - SessionStart: updates this project's kit files from the reference copy in
# your user profile (~/.claude/kit-template), creates the genre skill, ingests community packs.
# Logic lives in kit_sync.py (needs Python 3, same as the Skills page). Silent no-op without Python.
$ErrorActionPreference = "SilentlyContinue"
$script = Join-Path $PSScriptRoot "kit_sync.py"
if (-not (Test-Path $script)) { exit 0 }
foreach ($cand in @(@("py","-3"), @("python"), @("python3"))) {
    $exe = Get-Command $cand[0] -ErrorAction SilentlyContinue
    if (-not $exe) { continue }
    $pre = @(); if ($cand.Count -gt 1) { $pre = @($cand[1]) }
    & $exe.Source @pre $script
    exit 0
}
exit 0
