# Claude/hooks/docs-lint.ps1 - PostToolUse: format check of ROADMAP.md/BUGS.md right after an edit (exit 2 = Claude must fix).
$ErrorActionPreference = "SilentlyContinue"
$script = Join-Path $PSScriptRoot "docs_lint.py"
if (-not (Test-Path $script)) { exit 0 }
foreach ($cand in @(@("py","-3"), @("python"), @("python3"))) {
    $exe = Get-Command $cand[0] -ErrorAction SilentlyContinue
    if (-not $exe) { continue }
    $pre = @(); if ($cand.Count -gt 1) { $pre = @($cand[1]) }
    $in = [Console]::In.ReadToEnd(); $in | & $exe.Source @pre $script "--post-edit"
    exit $LASTEXITCODE
}
exit 0
