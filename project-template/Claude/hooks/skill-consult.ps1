# Claude/hooks/skill-consult.ps1
#
# Skill Harness (v1.82): counts how often the coder actually READS a genre skill, so the Skills page
# can show "Used by coder" and flag patterns that are never consulted. Wired in .claude/settings.json
# as a PreToolUse hook on "Read". It only does anything when the file being read is inside
# ~/.claude/skills/genre/<genre>/ (and not its private local/ folder); every other Read exits at once.
#
# MUST NEVER block or fail a tool call: every error is swallowed, always exits 0.

try {
    $raw = [Console]::In.ReadToEnd()
    if ($raw -notmatch '(?i)skills[\\/]+genre[\\/]') { exit 0 }
    $p = ($raw | ConvertFrom-Json).tool_input.file_path
    if (-not $p) { exit 0 }
    $projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
    $lib = Join-Path $projectDir "Claude\hooks\skills_lib.py"
    if (-not (Test-Path $lib)) { exit 0 }
    foreach ($py in @("python3", "python", "py")) {
        if (Get-Command $py -ErrorAction SilentlyContinue) {
            & $py $lib consult-path $p *> $null
            break
        }
    }
} catch { }
exit 0
