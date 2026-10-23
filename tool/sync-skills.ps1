<#
sync-skills.ps1
PERSONAL use - outside the kit, not to be distributed or released to the community.

Purpose: align skills from the user profile (where they evolve while you work) to the
project (where the git release starts), WITHOUT EVER overwriting anything automatically.
Every copy needs explicit confirmation, and every promotion is logged in a manifest so the
history of what you released and when stays traceable (and can go to git with the rest).

Default paths (can be overridden on the command line):
  Profile (source, evolves)    : $env:USERPROFILE\.claude\skills
  Project (destination, git)   : <kit folder>\user-level-skills (the folder above tool\)
  (The kit folder is the kit repo itself - the "project" skills to release live under
  user-level-skills, not under Claude\skills, which is the structure used INSIDE every
  UEFN project that uses the kit)

Usage:
  .\sync-skills.ps1                       # summary only (dry-run, default)
  .\sync-skills.ps1 -Apply                # apply interactively (confirm for each skill)
  .\sync-skills.ps1 -Apply -All           # apply everything without asking skill by skill
  .\sync-skills.ps1 -ProfilePath "..." -ProjectPath "..."   # override paths

Note: the comparison is by content HASH (not by date), so a skill that was "touched" but not
really modified does not show up as changed.
#>

param(
    [string]$ProfilePath = (Join-Path $env:USERPROFILE ".claude\skills"),
    [string]$ProjectPath = (Join-Path (Split-Path -Parent $PSScriptRoot) "user-level-skills"),
    [switch]$Apply,
    [switch]$All,
    # Folders under $ProfilePath to always ignore: they are not real skills, they are
    # Claude Code internal bookkeeping (e.g. "synced" only holds GUID folders and empty
    # .bucket-* files). Add other names here if you find more.
    # "genre" is excluded on purpose (v1.81, Skill Harness): in your profile the genre skills hold
    # PRIVATE data from your maps (local/ folder: map names, task IDs, notes) and learned patterns.
    # They must never be promoted to the kit repo by a folder copy. The seed files in the repo are
    # edited by hand; patterns are shared only through `skills_lib.py export`, which runs a privacy
    # check first.
    [string[]]$ExcludeNames = @("synced", "genre")
)

$ErrorActionPreference = "Stop"

function Get-FolderHash {
    param([string]$FolderPath)
    if (-not (Test-Path $FolderPath)) { return $null }
    $files = Get-ChildItem -Path $FolderPath -Recurse -File | Sort-Object FullName
    if ($files.Count -eq 0) { return $null }
    $sb = New-Object System.Text.StringBuilder
    foreach ($f in $files) {
        $rel = $f.FullName.Substring($FolderPath.Length).TrimStart('\', '/')
        $fileHash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash
        [void]$sb.AppendLine("$rel|$fileHash")
    }
    $combined = $sb.ToString()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($combined)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha.ComputeHash($bytes)
    return [System.BitConverter]::ToString($hashBytes) -replace '-', ''
}

function Get-ManifestPath {
    param([string]$ProjectSkillsPath)
    return Join-Path $ProjectSkillsPath ".sync-manifest.json"
}

function Load-Manifest {
    param([string]$ManifestPath)
    if (Test-Path $ManifestPath) {
        return Get-Content $ManifestPath -Raw | ConvertFrom-Json -AsHashtable
    }
    return @{}
}

function Save-Manifest {
    param([string]$ManifestPath, [hashtable]$Manifest)
    $Manifest | ConvertTo-Json -Depth 10 | Set-Content -Path $ManifestPath -Encoding UTF8
}

if (-not (Test-Path $ProfilePath)) {
    Write-Host "ERROR: profile path not found: $ProfilePath" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $ProjectPath)) {
    Write-Host "The project path does not exist, creating it: $ProjectPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
}

$manifestPath = Get-ManifestPath -ProjectSkillsPath $ProjectPath
$manifest = Load-Manifest -ManifestPath $manifestPath

$profileSkills = Get-ChildItem -Path $ProfilePath -Directory |
    Where-Object { $ExcludeNames -notcontains $_.Name } |
    Sort-Object Name

$results = @()

foreach ($skillDir in $profileSkills) {
    $skillName = $skillDir.Name
    $profileSkillPath = $skillDir.FullName
    $projectSkillPath = Join-Path $ProjectPath $skillName

    $profileHash = Get-FolderHash -FolderPath $profileSkillPath
    $projectHash = Get-FolderHash -FolderPath $projectSkillPath

    $status = ""
    if ($null -eq $projectHash) {
        $status = "NEW"
    } elseif ($profileHash -ne $projectHash) {
        $status = "MODIFIED"
    } else {
        $status = "UNCHANGED"
    }

    $lastPromoted = if ($manifest.ContainsKey($skillName)) { $manifest[$skillName].lastPromotedAt } else { "never" }

    $results += [PSCustomObject]@{
        Skill         = $skillName
        Status        = $status
        ProfileHash   = if ($profileHash) { $profileHash.Substring(0,10) } else { "-" }
        ProjectHash   = if ($projectHash) { $projectHash.Substring(0,10) } else { "-" }
        LastPromoted  = $lastPromoted
    }
}

Write-Host ""
Write-Host "=== Skills sync summary ===" -ForegroundColor Cyan
Write-Host "Profile : $ProfilePath"
Write-Host "Project : $ProjectPath"
Write-Host ""
$results | Format-Table -AutoSize

$toPromote = $results | Where-Object { $_.Status -ne "UNCHANGED" }

if ($toPromote.Count -eq 0) {
    Write-Host "No skill to promote. Everything is aligned." -ForegroundColor Green
    exit 0
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry-run mode (nothing copied). Run again with -Apply to promote." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
foreach ($item in $toPromote) {
    $doPromote = $All
    if (-not $All) {
        $answer = Read-Host "Promote '$($item.Skill)' ($($item.Status)) from the profile to the project? [y/N]"
        $doPromote = ($answer -eq "y" -or $answer -eq "Y")
    }

    if ($doPromote) {
        $src = Join-Path $ProfilePath $item.Skill
        $dst = Join-Path $ProjectPath $item.Skill

        if (Test-Path $dst) {
            # Delete the old copy; if the system refuses, park it in _to_delete (the owner empties it).
            try { Remove-Item -Path $dst -Recurse -Force -ErrorAction Stop }
            catch {
                $parkRoot = Join-Path (Split-Path $ProjectPath -Parent) ("_to_delete\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
                New-Item -ItemType Directory -Force -Path $parkRoot | Out-Null
                Move-Item -Path $dst -Destination (Join-Path $parkRoot (Split-Path $dst -Leaf)) -Force
            }
        }
        Copy-Item -Path $src -Destination $dst -Recurse -Force

        $newHash = Get-FolderHash -FolderPath $dst
        $manifest[$item.Skill] = @{
            lastPromotedAt = (Get-Date -Format "yyyy-MM-dd HH:mm")
            hash           = $newHash
        }

        Write-Host "  -> Promoted: $($item.Skill)" -ForegroundColor Green
    } else {
        Write-Host "  -> Skipped: $($item.Skill)" -ForegroundColor DarkGray
    }
}

Save-Manifest -ManifestPath $manifestPath -Manifest $manifest
Write-Host ""
Write-Host "Manifest updated: $manifestPath" -ForegroundColor Cyan
Write-Host "Done." -ForegroundColor Green
