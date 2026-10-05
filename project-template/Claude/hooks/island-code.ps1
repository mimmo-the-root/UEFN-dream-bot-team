# Claude/hooks/island-code.ps1 - UserPromptSubmit: saves an island code from the prompt to Claude/docs/.island-code.
$ErrorActionPreference = "SilentlyContinue"
$script = Join-Path $PSScriptRoot "island_code_capture.py"
if (-not (Test-Path $script)) { exit 0 }
foreach ($cand in @(@("py","-3"), @("python"), @("python3"))) {
    $exe = Get-Command $cand[0] -ErrorAction SilentlyContinue
    if (-not $exe) { continue }
    $pre = @(); if ($cand.Count -gt 1) { $pre = @($cand[1]) }
    $in = [Console]::In.ReadToEnd(); $in | & $exe.Source @pre $script
    exit 0
}
exit 0
