<#
 reset-lab.ps1 - maintainer tool: puts the clean demo Lab back and installs the current kit into your profile.
 One command:  reset-lab.cmd            (or: powershell -ExecutionPolicy Bypass -File reset-lab.ps1)
 Close UEFN, Cod and any terminal or Explorer window open inside the Lab first.
 Switches:  -Yes (no questions)   -DryRun (checks only, changes nothing)   -OpenUefn (opens the project at the end)
 Paths:     -Projects (default C:\UEFN_Progetti)  -LabName (default root_ai_lab)  -Zip (default: newest _spike\<LabName>-clean-*.zip)
 What it does: stops the kit console, keeps the built farm as a ZIP outside the projects folder (UEFN lists every .uefnproject it
 finds under the projects folder, so a second project folder there shows up as a duplicate), restores the clean Lab from the
 zip in place (no rename needed), runs update-my-profile.cmd, and reads back the second brain.
#>
param(
    [string]$Projects = "C:\UEFN_Progetti",
    [string]$LabName = "root_ai_lab",
    [string]$Zip = "",
    [switch]$Yes,
    [switch]$DryRun,
    [switch]$OpenUefn
)
$ErrorActionPreference = "Stop"
$Kit = Split-Path -Parent $MyInvocation.MyCommand.Path
$Lab = Join-Path $Projects $LabName
$Stamp = Get-Date -Format "yyyyMMdd-HHmm"
$FarmZip = Join-Path $Kit ("_private\lab-backup\" + $LabName + "-farm-" + $Stamp + ".zip")
if (-not $Zip) {
    $z = Get-ChildItem (Join-Path $Kit "_spike") -Filter ($LabName + "-clean-*.zip") -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($z) { $Zip = $z.FullName }
}

function Step($t) { Write-Host ("`n== " + $t) -ForegroundColor Cyan }
function Fail($m) { Write-Host ("STOP: " + $m) -ForegroundColor Red; exit 1 }
function CountFiles($p) { (Get-ChildItem $p -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object).Count }
function ZipFileCount($z) {
    $zf = [System.IO.Compression.ZipFile]::OpenRead($z)
    $n = @($zf.Entries | Where-Object { $_.Name -ne "" }).Count
    $zf.Dispose()
    return $n
}
function Robo($src, $dst, $flags) {
    & robocopy $src $dst @flags /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw ("robocopy failed with code " + $LASTEXITCODE) }
}
Add-Type -AssemblyName System.IO.Compression.FileSystem

Step "Checks"
if (-not $Zip -or -not (Test-Path $Zip)) { Fail ("no clean zip found (looked for _spike\" + $LabName + "-clean-*.zip). Pass -Zip <path>.") }
if (-not (Test-Path $Lab)) { Fail ("Lab not found: " + $Lab) }
if (Get-Process -Name "UnrealEditorFortnite*" -ErrorAction SilentlyContinue) { Fail "UEFN is open: close it and run again." }
$console = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'agent-console-server' })
$projects = @(Get-ChildItem $Projects -Recurse -Filter "*.uefnproject" -Depth 3 -ErrorAction SilentlyContinue)
Write-Host ("zip:       " + $Zip)
Write-Host ("lab:       " + $Lab + "   (" + (CountFiles $Lab) + " files)")
Write-Host ("farm zip:  " + $FarmZip)
Write-Host ("kit console processes running: " + $console.Count)
Write-Host ("projects UEFN will list under " + $Projects + ": " + $projects.Count)
foreach ($p in $projects) { Write-Host ("   " + $p.FullName) }
if ($projects.Count -gt 1) { Write-Host "More than one: the extra ones show up in UEFN as duplicates. This script keeps only the Lab; zip and remove the others (see the end)." -ForegroundColor Yellow }
if ($DryRun) { Write-Host "`nDry run: nothing changed." -ForegroundColor Yellow; exit 0 }
if (-not $Yes) {
    $r = Read-Host "Cod, UEFN and every terminal or Explorer window inside the Lab are closed? (y/n)"
    if ($r -ne "y") { Fail "close them and run again." }
}

Step "Stop the kit console"
# The console is a PowerShell server: Windows shows its port as held by System (PID 4), so stop the process by its command line.
foreach ($p in $console) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

Step "Keep the built farm as a zip (never as a second project folder)"
New-Item -ItemType Directory -Force (Split-Path $FarmZip) | Out-Null
[System.IO.Compression.ZipFile]::CreateFromDirectory($Lab, $FarmZip, [System.IO.Compression.CompressionLevel]::Optimal, $true)
$have = CountFiles $Lab
$inZip = ZipFileCount $FarmZip
if ($have -ne $inZip) {
    Remove-Item $FarmZip -Force -ErrorAction SilentlyContinue
    Fail ("the zip has " + $inZip + " files, the Lab has " + $have + ". Nothing was changed in the Lab.")
}
Write-Host ("farm saved: " + $FarmZip + " (" + $inZip + " files)")

Step "Restore the clean Lab from the zip, in place"
$tmp = Join-Path $env:TEMP ("lab-clean-" + $Stamp)
$failed = $false
try {
    Expand-Archive $Zip -DestinationPath $tmp -Force
    $src = Join-Path $tmp $LabName
    if (-not (Test-Path (Join-Path $src ($LabName + ".uefnproject")))) { throw ("the zip does not look right (no " + $LabName + ".uefnproject)") }
    Robo $src $Lab @("/MIR")
}
catch {
    $failed = $true
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host ("The farm is safe in " + $FarmZip + ". The Lab may be half cleaned: fix the cause and run again.")
}
finally { if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue } }
if ($failed) { exit 1 }

Step "Check the clean Lab"
if (-not (Test-Path (Join-Path $Lab ($LabName + ".uefnproject")))) { Fail "the project file is missing." }
foreach ($x in @("Content\Claude", "Content\CLAUDE.md")) {
    if (Test-Path (Join-Path $Lab $x)) { Fail ($x + " still exists: the Lab is not clean.") }
}
$expected = ZipFileCount $Zip
$have = CountFiles $Lab
if ($have -ne $expected) { Fail ("the Lab has " + $have + " files, the zip has " + $expected + ".") }
Write-Host ("clean: " + $have + " files, no Claude folder, no CLAUDE.md")
$left = @(Get-ChildItem $Projects -Recurse -Filter "*.uefnproject" -Depth 3 -ErrorAction SilentlyContinue)
if ($left.Count -gt 1) {
    Write-Host ("WARNING: UEFN will list " + $left.Count + " projects:") -ForegroundColor Yellow
    foreach ($p in $left) { Write-Host ("   " + $p.FullName) }
    Write-Host "Zip each extra folder outside the projects folder and remove it. See reset-lab.ps1 header."
}

Step "Kit into your profile (update-my-profile.cmd)"
Push-Location $Kit
try { & ".\update-my-profile.cmd" } finally { Pop-Location }

Step "Second brain (read only)"
$cm = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"
if (Test-Path $cm) {
    $t = Get-Content $cm -Raw
    $n = ([regex]::Matches($t, 'KIT:BEGIN second-brain-session')).Count
    $m = [regex]::Match($t, '\*\*Second brain path\*\*:\s*`([^`]*)`')
    Write-Host ("rule 15 blocks in your profile: " + $n)
    if ($m.Success -and $m.Groups[1].Value -ne '<SECOND_BRAIN_PATH>' -and (Test-Path $m.Groups[1].Value)) {
        Write-Host ("vault: " + $m.Groups[1].Value)
        $vc = Join-Path $env:USERPROFILE ".claude\skills\second-brain-query\scripts\vault_check.py"
        if (Test-Path $vc) { & python $vc status --vault $m.Groups[1].Value | Select-Object -Last 1 }
    }
    else { Write-Host "the second brain is off (no vault path in rule 11)" }
}

Step "Done"
Write-Host ("Clean Lab ready in " + $Lab)
Write-Host ("The built farm is in " + $FarmZip + "  (restore it by extracting that zip, outside the projects folder, only if you need it)")
Write-Host ""
Write-Host "Now:" -ForegroundColor Yellow
Write-Host "  1) Open UEFN with the project; wait for the editor and the MCP connection."
Write-Host ("  2) New terminal:  Set-Location '" + $Lab + "\Content' ; claude     (answer yes to the kit install)")
Write-Host "  3) Open http://127.0.0.1:8765/ (Docs page), start OBS, then in Cod:  /demo --auto"
if ($OpenUefn) { Invoke-Item (Join-Path $Lab ($LabName + ".uefnproject")) }
