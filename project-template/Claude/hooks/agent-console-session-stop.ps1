# Claude/hooks/agent-console-session-stop.ps1
#
# Feeds the Agent Console's "YOU" node: marks the session idle (Claude yielded back to you,
# waiting for your next message) the moment the main session's own Stop hook fires. Paired with
# agent-console-tokens.ps1, which marks the session active on every tool call — this is the one
# authoritative "went idle" signal, since Stop only fires when the main agent is genuinely done
# producing a turn, not on every tool call the way PostToolUse does.
#
# Wired in .claude/settings.json as a second command under the existing "Stop" hook (alongside
# the STATUS.md reminder echo) — no matcher; Stop doesn't use one.
#
# MUST NEVER fail loudly: every error is swallowed, script always exits 0.

$ErrorActionPreference = "Stop"
try {
    $projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
    [Console]::In.ReadToEnd() | Out-Null

    $logDir = Join-Path $projectDir "Claude\logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $sessionFile = Join-Path $logDir "agent-console-session.json"

    [ordered]@{ active = $false; ts = (Get-Date).ToUniversalTime().ToString("o") } |
        ConvertTo-Json -Compress | Set-Content -Path $sessionFile -Encoding utf8
} catch {
    # Swallow everything — see the header comment above.
}
exit 0
