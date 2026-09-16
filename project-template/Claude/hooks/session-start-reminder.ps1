# Claude/hooks/session-start-reminder.ps1
#
# Fires once when a new Claude Code session starts on this project (wired in
# .claude/settings.json as a SessionStart hook, matcher "startup" — so it fires when you launch
# `claude` fresh, not every time you /clear or /compact mid-session).
#
# v1.40: no longer ASKS whether to start the console — it deterministically ensures the console
# server is running and correctly scoped to THIS project before Claude's very first reply, so
# there's no round-trip needed and nothing to remember to say yes to. This also fixes a real bug:
# port 8765 is the same for every project, so switching to a different UEFN project while a
# previous project's server was still bound left you looking at the WRONG project's stale data
# (it looked "already running" from the outside, so the old ask-only logic never touched it).
#
# How the fix works: every server instance now exposes "/whoami", reporting which project
# folder it's actually serving (see agent-console-server.ps1/.py). On session start:
#   1. If nothing answers /whoami on 8765 correctly for THIS project's folder, whatever is
#      currently bound to the port (this project's own stale process from a crashed session, or
#      a different project's server, or nothing at all) is treated as needing a fresh start.
#   2. Before starting a new one, kill whatever's listening on 8765 — but ONLY if it looks like
#      one of our own server processes (powershell/pwsh/python), never an unrelated program that
#      happens to be using that port.
#   3. Start a fresh server bound to THIS project's own agent-console-server.ps1, in the
#      background (detached, so it keeps running after this hook returns).
#   4. If the existing server already answered /whoami with THIS project's own folder, it's
#      already correctly running — left untouched, no restart needed just because a session
#      started.
#
# There's also a backup: `CLAUDE.md`'s own "Rules for this project's agents" section carries the
# same deterministic-start instruction in plain prose, since CLAUDE.md is always loaded reliably
# — this hook is the faster/earlier path when it works, CLAUDE.md is the guaranteed fallback
# either way.
#
# Only fires if this project actually has the optional Agent Console installed
# (Claude/hooks/agent-console.html) — silent no-op otherwise, so this is safe even on a project
# set up with an older version of the kit that predates the console. Everything here is
# best-effort: any failure along the way is swallowed (the console is optional, this must never
# block a session from starting), and Claude still gets a context note either way.
#
# v1.43: also opens the console in the owner's default browser automatically, every session —
# an explicit owner preference (previously it only mentioned the URL and left opening it up to
# you). Fires once per fresh `claude` launch, same as everything else in this hook (the "startup"
# matcher, not every /clear or /compact) — best-effort, wrapped the same way as the rest of this
# script, never blocks the session if it fails.

$ErrorActionPreference = "SilentlyContinue"
$projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
$consolePath = Join-Path $projectDir "Claude\hooks\agent-console.html"
$serverScript = Join-Path $projectDir "Claude\hooks\agent-console-server.ps1"
$port = 8765

# v1.70.4: wrong-launch-folder detector. This kit's scaffold lives inside the project's Content/
# folder (see SETUP-INSTRUCTIONS.md), so ${CLAUDE_PROJECT_DIR} must point INSIDE Content/, not at
# the UEFN project's outer root. Launching `claude` from the wrong folder makes every hook in
# settings.json point at a Claude/hooks/ that doesn't exist there — they fail silently (no error
# surfaced), so the console never starts, agent-console.jsonl never gets written, and nothing
# looks obviously broken until you notice the console is stale. If that's what happened, this
# still fires (SessionStart always runs) even though the real Claude/hooks/ isn't where expected —
# it looks one level down at Content/Claude/hooks/ specifically to catch this exact mistake and
# say so up front, instead of failing quietly like everything else would.
if (-not (Test-Path $consolePath)) {
    $nestedConsolePath = Join-Path $projectDir "Content\Claude\hooks\agent-console.html"
    if (Test-Path $nestedConsolePath) {
        $warnContext = @"
WARNING - wrong launch folder for this project. This kit's scaffold (Claude/hooks/, Claude/docs/,
etc.) lives inside Content/, but this session was started from $projectDir, one level above it.
Every hook in .claude/settings.json uses the CLAUDE_PROJECT_DIR environment variable to build the
path to Claude/hooks/..., which does not exist at this level - so hooks are failing silently, the
Agent Console will not start, and
Claude/logs/agent-console.jsonl will not receive new events, with no visible error. Tell the owner
plainly, in your very first reply, to close this session and relaunch claude from inside the
Content folder (see Claude/SETUP-INSTRUCTIONS.md) - dont just proceed as if nothing's wrong.
"@
        $warnOutput = [ordered]@{
            hookSpecificOutput = [ordered]@{
                hookEventName     = "SessionStart"
                additionalContext = $warnContext
            }
        } | ConvertTo-Json -Depth 5 -Compress
        Write-Output $warnOutput
    }
}

if (Test-Path $consolePath) {
    $thisProject = $projectDir
    try { $thisProject = (Resolve-Path $projectDir).Path } catch {}
    $thisProject = $thisProject.TrimEnd('\', '/')

    $alreadyCorrect = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$port/whoami" -TimeoutSec 2 -UseBasicParsing
        $who = $resp.Content | ConvertFrom-Json
        $servedProject = ([string]$who.project).TrimEnd('\', '/')
        if ($servedProject -eq $thisProject) {
            $alreadyCorrect = $true
        }
    } catch {
        # Nothing answered /whoami — either nothing's listening on 8765, or something is but it
        # isn't one of our servers (or is a stale/hung one). Either way, fall through to restart.
    }

    if (-not $alreadyCorrect) {
        try {
            $lines = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
            foreach ($line in $lines) {
                $procId = ($line -split '\s+')[-1]
                if ($procId -match '^\d+$') {
                    $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
                    if ($procName -match 'powershell|pwsh|python') {
                        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                        Start-Sleep -Milliseconds 400
                    }
                }
            }
        } catch {}

        try {
            Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$serverScript`"" -WindowStyle Hidden
        } catch {}
        Start-Sleep -Milliseconds 500  # give the fresh server a moment to bind before opening it
    }

    try {
        Start-Process "http://127.0.0.1:$port/"
    } catch {}

    $context = @"
This project's real-time Agent Console has already been started (or, if it was previously
serving a different project on this same port, restarted) automatically for THIS project, and
opened in the owner's default browser - no action needed from you and don't ask permission. Just
mention in your first reply that it's live at http://127.0.0.1:$port/ in case the owner closed
the tab or wants to reopen it. Only touch the console server yourself (stop/restart it) if the
owner reports a specific problem with it.
"@

    $output = [ordered]@{
        hookSpecificOutput = [ordered]@{
            hookEventName     = "SessionStart"
            additionalContext = $context
        }
    } | ConvertTo-Json -Depth 5 -Compress

    Write-Output $output
}
