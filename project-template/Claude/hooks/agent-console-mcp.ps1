# Claude/hooks/agent-console-mcp.ps1
#
# Feeds the Agent Console's "MCP Server" node — logs when the UEFN MCP server
# (mcp__unreal-mcp__call_tool) is called and by whom, so you can see it light up in real time
# and tell which bot (or the main/chief-of-staff session, if `agent_type` is absent from the
# payload) is currently talking to the editor.
#
# Wired in .claude/settings.json on BOTH PreToolUse and PostToolUse, matched on
# "mcp__unreal-mcp__call_tool" (same matcher after-playtest.ps1 already uses on PostToolUse —
# this is a second, independent hook command on the same matcher, not a replacement). Unlike
# subagent dispatch (Task/Agent), an MCP tool call is synchronous — it doesn't return until the
# call is actually done — so PreToolUse/PostToolUse is the right pair here (no SubagentStop
# involved, no background-dispatch timing trap).
#
# Writes to its own log, Claude/logs/agent-console-mcp.jsonl, kept separate from
# agent-console.jsonl (subagent start/stop) so the two event streams and their card/queue logic
# never mix.
#
# MUST NEVER block or fail a tool call: every error is swallowed, script always exits 0.
#
# Troubleshooting: the short "what was called" label below is guessed defensively from common
# field names (tool_input.tool / .action / .toolset) since the unreal-mcp dispatcher's exact
# payload shape isn't documented here — uncomment the two $debug lines once, make an MCP call,
# and check Claude/logs/raw-agent-console-mcp-payload.log to see the real shape and adjust the
# $label lookup below if it comes through empty/unhelpful.

$ErrorActionPreference = "Stop"
try {
    $projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
    $stdin = [Console]::In.ReadToEnd()

    # $debugLog = Join-Path $projectDir "Claude\logs\raw-agent-console-mcp-payload.log"
    # New-Item -ItemType Directory -Force -Path (Split-Path $debugLog) | Out-Null
    # $stdin | Out-File -Append $debugLog

    $payload = $stdin | ConvertFrom-Json -ErrorAction Stop

    $eventName = $null
    if ($payload.hook_event_name -eq "PreToolUse") { $eventName = "start" }
    elseif ($payload.hook_event_name -eq "PostToolUse") { $eventName = "stop" }
    if (-not $eventName) { exit 0 }

    $caller = $payload.agent_type
    if (-not $caller) { $caller = "chief-of-staff" }

    $ti = $payload.tool_input
    $label = $null
    foreach ($field in @("tool", "action", "toolset", "method", "command")) {
        if ($ti -and $ti.$field) { $label = [string]$ti.$field; break }
    }
    if (-not $label -and $ti) {
        try { $label = ($ti | ConvertTo-Json -Compress -Depth 2) } catch { $label = "" }
        if ($label -and $label.Length -gt 80) { $label = $label.Substring(0, 80) + "…" }
    }
    if (-not $label) { $label = "" }

    $logDir = Join-Path $projectDir "Claude\logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $logFile = Join-Path $logDir "agent-console-mcp.jsonl"

    $entry = [ordered]@{
        ts     = (Get-Date).ToUniversalTime().ToString("o")
        event  = $eventName
        caller = $caller
        label  = $label
    } | ConvertTo-Json -Compress

    Add-Content -Path $logFile -Value $entry -Encoding utf8
} catch {
    # Swallow everything — see the header comment above.
}
exit 0
