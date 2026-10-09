# Publishes the kit: checks, commit, push, tag and GitHub Release (title and notes come from CHANGELOG.md).
# Run from this folder on your PC with git and (for the Release) gh logged in: `gh auth login`.
# Before: raise project-template\Claude\KIT-VERSION, the 5 agent-console*.html versions, and add a "## vX.Y.Z - title" entry at the top of CHANGELOG.md.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$hasPy = [bool](Get-Command py -ErrorAction SilentlyContinue)

# 1. version consistency
$ver = (Get-Content "project-template\Claude\KIT-VERSION" -Raw).Trim()
if ($ver -notmatch '^\d+\.\d+\.\d+$') { throw "KIT-VERSION is not X.Y.Z: $ver" }
foreach ($f in Get-ChildItem "project-template\Claude\hooks\agent-console*.html") {
  if (-not (Select-String -Path $f.FullName -Pattern ([regex]::Escape($ver)) -Quiet)) { throw "$($f.Name) does not carry version $ver" }
}
$log = Get-Content "CHANGELOG.md" -Raw -Encoding UTF8
$m = [regex]::Match($log, '(?m)^## (v' + [regex]::Escape($ver) + '\b[^\r\n]*)\r?\n(.*?)(?=^## |\z)', 'Singleline')
if (-not $m.Success) { throw "CHANGELOG.md has no '## v$ver ...' entry" }
$title = $m.Groups[1].Value.Trim()
$notes = $m.Groups[2].Value.Trim()
$notesFile = Join-Path $env:TEMP "kit-release-notes.md"
Set-Content -Path $notesFile -Value $notes -Encoding UTF8

# 2. tests (tests, privacy scan, skill validator, token budget)
if ($hasPy) { py -3 tests/run_all.py } else { python tests/run_all.py }
if ($LASTEXITCODE -ne 0) { throw "Tests failed: nothing was published" }

# 3. commit + push (every git step is checked: a failed commit must stop the script BEFORE the tag)
function Git { & git -c core.pager=cat @args; if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') failed (exit $LASTEXITCODE)" } }
$tag = "v$ver"
if (Test-Path ".git\index.lock") { throw "Stale lock .git\index.lock: close other git programs, delete that file and run again" }
if (git tag --list $tag) {
  $tagCommit = (git rev-parse "$tag^{commit}").Trim()
  throw "Tag $tag already exists (on $($tagCommit.Substring(0,7))). If it points to an old commit: git tag -d $tag ; git push origin :refs/tags/$tag ; then run again. Otherwise raise the version."
}
Write-Host "[1/4] Tests passed. Staging files..."
Git add -A
git -c core.pager=cat diff --cached --quiet
if ($LASTEXITCODE -ne 0) { Write-Host "[2/4] Committing..."; Git commit -m ($title -replace [char]0x2014, "-") }
Write-Host "[3/4] Pushing to GitHub (if nothing happens for a minute, look for a GitHub sign-in window behind this one)..."
Git push origin HEAD

# 4. tag + Release
Write-Host "[4/4] Tag $tag and GitHub Release..."
Git tag $tag
Git push origin $tag
if (Get-Command gh -ErrorAction SilentlyContinue) {
  gh release create $tag --title $title --notes-file $notesFile --latest
  if ($LASTEXITCODE -ne 0) { Write-Host "Release not created: create it on GitHub with tag $tag (notes in $notesFile)." }
} else {
  Write-Host "gh not found: create the Release on GitHub with tag $tag. Title: $title. Notes: $notesFile"
}
Write-Host "Published $tag. Tests on GitHub: https://github.com/mimmo-the-root/UEFN-dream-bot-team/actions"
