# Claude/hooks/ensure-brain.ps1
# Makes the second brain start by itself, the way the router and the console do: refreshes the profile hooks
# from the kit copy (no restart), fills rule 11 in ~/.claude/CLAUDE.md from SECOND_BRAIN or
# Claude/brain-vault.txt when it still holds the placeholder, then prints brain_brief.py start.
# Best effort, silent when the second brain is off. Writes Claude/logs/console-start.log. Always exits 0.
param([string]$ProjectDir = "")
try {
    $log = $null
    if ($ProjectDir) { $log = Join-Path $ProjectDir "Claude\logs\console-start.log" }
    function Log([string]$message) {
        if (-not $log) { return }
        try {
            $dir = Split-Path $log -Parent
            if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            Add-Content -LiteralPath $log -Value ("{0} brain: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message)
        } catch {}
    }
    $profile = $env:USERPROFILE
    $claudeDir = if ($env:UEFN_HOME) { $env:UEFN_HOME } else { Join-Path $profile ".claude" }
    $python = Get-Command py -ErrorAction SilentlyContinue
    $pythonArgs = @()
    if ($python) { $pythonExe = $python.Source; $pythonArgs = @("-3") }
    else { $pythonExe = "python" }

    $hotCandidates = @()
    if ($ProjectDir) { $hotCandidates += (Join-Path $ProjectDir "Claude\hooks\brain_hot.py") }
    $hotCandidates += (Join-Path $claudeDir "hooks\brain_hot.py")
    $hotCandidates += (Join-Path $claudeDir "kit-template\Claude\hooks\brain_hot.py")
    $hotCandidates += (Join-Path $PSScriptRoot "..\..\..\tools\brain_hot.py")
    foreach ($hot in $hotCandidates) {
        if (Test-Path -LiteralPath $hot) {
            try {
                & $pythonExe @pythonArgs $hot --home $claudeDir | Out-Null
                Log "hot update checked kit brain hooks"
            } catch { Log "hot update failed" }
            break
        }
    }

    $vault = $env:SECOND_BRAIN
    $vaultFile = ""
    if ($ProjectDir) { $vaultFile = Join-Path $ProjectDir "Claude\brain-vault.txt" }
    if ((-not $vault) -and $vaultFile -and (Test-Path -LiteralPath $vaultFile)) {
        $vault = (Get-Content -LiteralPath $vaultFile -Raw -ErrorAction SilentlyContinue)
        if ($vault) { $vault = $vault.Trim().Trim('"') }
    }
    if ((-not $vault) -or $vault -eq "<SECOND_BRAIN_PATH>" -or -not (Test-Path -LiteralPath $vault -PathType Container)) {
        Log "second brain off or vault missing"
        exit 0
    }

    $rules = Join-Path $claudeDir "CLAUDE.md"
    if (Test-Path -LiteralPath $rules) {
        try {
            $text = [System.IO.File]::ReadAllText($rules)
            $pattern = '(?m)^(?<before>.*\*\*Second brain path\*\*:\s*`)(?<path>[^`]*)(?<after>`.*)$'
            $found = [regex]::Match($text, $pattern)
            if ($found.Success -and $found.Groups['path'].Value -like '*SECOND_BRAIN_PATH*') {
                $backup = $rules + ".backup"
                [System.IO.File]::Copy($rules, $backup, $true)
                $start = $text.Substring(0, $found.Index)
                $end = $text.Substring($found.Index + $found.Length)
                $updated = $start + $found.Groups['before'].Value + $vault + $found.Groups['after'].Value + $end
                [System.IO.File]::WriteAllText($rules, $updated, (New-Object System.Text.UTF8Encoding($false)))
                Log ("rule 11 vault path set to {0} (backup: CLAUDE.md.backup)" -f $vault)
            } else {
                Log "rule 11 already set or not a placeholder"
            }
        } catch { Log "rule 11 update failed" }
    }

    $briefCandidates = @()
    if ($ProjectDir) { $briefCandidates += (Join-Path $ProjectDir "Claude\hooks\brain_brief.py") }
    $briefCandidates += (Join-Path $claudeDir "kit-template\Claude\hooks\brain_brief.py")
    $briefCandidates += (Join-Path $claudeDir "hooks\brain_brief.py")
    foreach ($brief in $briefCandidates) {
        if (Test-Path -LiteralPath $brief) {
            try {
                & $pythonExe @pythonArgs $brief start
                Log "brain_brief start printed"
            } catch { Log "brain_brief start failed" }
            break
        }
    }
} catch {}
exit 0
