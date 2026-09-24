<#
sync-skills.ps1
Uso PERSONALE — fuori dal kit, non va distribuito/rilasciato alla community.

Scopo: allineare le skill dal profilo utente (dove evolvono mentre lavori)
al progetto (da cui parte il rilascio su git), SENZA MAI sovrascrivere
automaticamente nulla. Ogni copia richiede conferma esplicita, e ogni
promozione viene loggata in un manifest cosi' la cronologia di cosa hai
rilasciato e quando resta tracciabile (e puo' finire su git insieme al
resto).

Percorsi di default (modificabili anche da riga di comando):
  Profilo (sorgente, evolve)  : C:\Users\mimmo\.claude\skills
  Progetto (destinazione, git): C:\UEFNDreamTeamBot\user-level-skills
  (C:\UEFNDreamTeamBot è il repo del kit stesso — le skill "di progetto" da
  rilasciare stanno sotto user-level-skills, non sotto Claude\skills, che
  invece è la struttura usata DENTRO ogni progetto UEFN che usa il kit)

Uso:
  .\sync-skills.ps1                       # mostra solo il riepilogo (dry-run, default)
  .\sync-skills.ps1 -Apply                # applica interattivamente (conferma per ogni skill)
  .\sync-skills.ps1 -Apply -All           # applica tutto senza chiedere skill per skill
  .\sync-skills.ps1 -ProfilePath "..." -ProjectPath "..."   # override percorsi

Nota: il confronto e' per HASH del contenuto (non per data), cosi' una skill
"toccata" ma non davvero modificata non risulta come cambiata.
#>

param(
    [string]$ProfilePath = "C:\Users\mimmo\.claude\skills",
    [string]$ProjectPath = "C:\UEFNDreamTeamBot\user-level-skills",
    [switch]$Apply,
    [switch]$All,
    # Cartelle sotto $ProfilePath da ignorare sempre: non sono skill vere, sono
    # bookkeeping interno di Claude Code (es. "synced" contiene solo cartelle
    # con GUID e file .bucket-* vuoti). Aggiungi qui altri nomi se ne scopri altri.
    [string[]]$ExcludeNames = @("synced")
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
    Write-Host "ERRORE: percorso profilo non trovato: $ProfilePath" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $ProjectPath)) {
    Write-Host "Il percorso progetto non esiste, lo creo: $ProjectPath" -ForegroundColor Yellow
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
        $status = "NUOVA"
    } elseif ($profileHash -ne $projectHash) {
        $status = "MODIFICATA"
    } else {
        $status = "INVARIATA"
    }

    $lastPromoted = if ($manifest.ContainsKey($skillName)) { $manifest[$skillName].lastPromotedAt } else { "mai" }

    $results += [PSCustomObject]@{
        Skill         = $skillName
        Stato         = $status
        ProfileHash   = if ($profileHash) { $profileHash.Substring(0,10) } else { "-" }
        ProjectHash   = if ($projectHash) { $projectHash.Substring(0,10) } else { "-" }
        UltimaPromo   = $lastPromoted
    }
}

Write-Host ""
Write-Host "=== Riepilogo sync skills ===" -ForegroundColor Cyan
Write-Host "Profilo : $ProfilePath"
Write-Host "Progetto: $ProjectPath"
Write-Host ""
$results | Format-Table -AutoSize

$toPromote = $results | Where-Object { $_.Stato -ne "INVARIATA" }

if ($toPromote.Count -eq 0) {
    Write-Host "Nessuna skill da promuovere. Tutto allineato." -ForegroundColor Green
    exit 0
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Modalita' dry-run (nessuna copia effettuata). Rilancia con -Apply per promuovere." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
foreach ($item in $toPromote) {
    $doPromote = $All
    if (-not $All) {
        $answer = Read-Host "Promuovere '$($item.Skill)' ($($item.Stato)) dal profilo al progetto? [s/N]"
        $doPromote = ($answer -eq "s" -or $answer -eq "S")
    }

    if ($doPromote) {
        $src = Join-Path $ProfilePath $item.Skill
        $dst = Join-Path $ProjectPath $item.Skill

        if (Test-Path $dst) {
            Remove-Item -Path $dst -Recurse -Force
        }
        Copy-Item -Path $src -Destination $dst -Recurse -Force

        $newHash = Get-FolderHash -FolderPath $dst
        $manifest[$item.Skill] = @{
            lastPromotedAt = (Get-Date -Format "yyyy-MM-dd HH:mm")
            hash           = $newHash
        }

        Write-Host "  -> Promossa: $($item.Skill)" -ForegroundColor Green
    } else {
        Write-Host "  -> Saltata: $($item.Skill)" -ForegroundColor DarkGray
    }
}

Save-Manifest -ManifestPath $manifestPath -Manifest $manifest
Write-Host ""
Write-Host "Manifest aggiornato: $manifestPath" -ForegroundColor Cyan
Write-Host "Fatto." -ForegroundColor Green
