# Claude/hooks/agent-console-log.ps1
#
# Logs the "start" half of a subagent invocation for the real-time Agent Console
# (Claude/hooks/agent-console.html), and pushes it onto a small FIFO queue
# (Claude/logs/agent-console-active.json) so the matching "stop" event — logged separately by
# agent-console-stop.ps1 on the SubagentStop hook — can attribute itself to the right
# agent/description.
#
# IMPORTANT — history: earlier versions of this kit logged BOTH "start" and "stop" from this
# same script, "stop" coming from PostToolUse on the Task/Agent tool. A real test showed that's
# wrong for a subagent dispatched to run in the BACKGROUND: the tool call returns (and
# PostToolUse fires) the moment the subagent is dispatched, not when it actually finishes — so
# the console showed "finished" a couple seconds after "started" while the agent was still
# genuinely working. `SubagentStop` is the hook Claude Code actually fires on real completion
# (foreground or background), so that's now the only source of "stop" events — see
# agent-console-stop.ps1. This script now only ever logs "start".
#
# Wired in .claude/settings.json as a PreToolUse hook, matched on "Task|Agent" — Claude Code's
# internal subagent-dispatch tool; the exact name has been observed to vary by Claude Code
# build/version (confirmed via a real payload capture: one setup used "Agent", not "Task"),
# hence matching both rather than assuming one.
#
# MUST NEVER block or fail a subagent call: every error is swallowed and the script always
# exits 0. A broken log/queue is a cosmetic problem; blocking a real subagent invocation because
# of a logging bug would not be.
#
# Concurrency note: overlapping subagent invocations mean this script and agent-console-stop.ps1
# can run at the same instant, both reading-modifying-writing agent-console-active.json. A real
# test confirmed the race is not theoretical: two concurrent writers produced a corrupted queue
# entry (fields serialized as 2-element arrays instead of scalars), which then permanently wedged
# the console's connection indicator on "DISCONNECTED" (agent-console.html now guards against that
# specific symptom too, but the fix here is to not corrupt the queue in the first place). A named
# Mutex now serializes the read-modify-write below across both scripts.
#
# PowerShell 5.1 gotcha (2026-08-28, real reproduction): DO NOT wrap `Get-Content -Raw |
# ConvertFrom-Json` in an outer `@(...)`. ConvertFrom-Json already returns a proper array for a
# JSON array of any length (0, 1, or many) when read via the pipe — wrapping that result in
# another `@()` was empirically shown to double-nest it (`Object[1]{ Object[N]{ real items } }`
# instead of `Object[N]{ real items }`), corrupting the queue's shape the moment a second entry
# was pushed. Read with a plain assignment and normalize only the null/non-array edge cases (see
# below) — never re-wrap an already-returned array.
#
# Troubleshooting: if the console never lights up, uncomment the two $debug lines below once,
# reproduce, and check Claude/logs/raw-agent-console-payloads.log for the exact field names —
# same approach as after-playtest.ps1 uses for the post-playtest hook. If a future Claude Code
# version renames the subagent-invocation tool to something other than "Task"/"Agent", that
# capture will show you the real name — add it to the check below and to settings.json's
# matcher the same way "Agent" was added.

$ErrorActionPreference = "Stop"
try {
    $projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
    $stdin = [Console]::In.ReadToEnd()

    # $debugLog = Join-Path $projectDir "Claude\logs\raw-agent-console-payloads.log"
    # New-Item -ItemType Directory -Force -Path (Split-Path $debugLog) | Out-Null
    # $stdin | Out-File -Append $debugLog

    $payload = $stdin | ConvertFrom-Json -ErrorAction Stop

    if ($payload.tool_name -ne "Task" -and $payload.tool_name -ne "Agent") { exit 0 }
    if ($payload.hook_event_name -ne "PreToolUse") { exit 0 }

    $agent = $payload.tool_input.subagent_type
    if (-not $agent) { $agent = "unknown" }
    $desc = $payload.tool_input.description
    if (-not $desc) { $desc = "" }

    $logDir = Join-Path $projectDir "Claude\logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $logFile = Join-Path $logDir "agent-console.jsonl"
    $queueFile = Join-Path $logDir "agent-console-active.json"

    $entry = [ordered]@{
        ts    = (Get-Date).ToUniversalTime().ToString("o")
        event = "start"
        agent = $agent
        desc  = $desc
    } | ConvertTo-Json -Compress

    Add-Content -Path $logFile -Value $entry -Encoding utf8

    # Push onto the FIFO queue that agent-console-stop.ps1 reads from — best-effort: a rare
    # lost/duplicated entry here just means one eventual "stop" gets attributed to the wrong
    # agent/description, not a crash (see agent-console.html's own note that this whole console
    # is a heuristic visualization, not a rigorous tracer). The Mutex below only prevents the
    # read-modify-write race from corrupting the file's JSON structure itself.
    $mutex = New-Object System.Threading.Mutex($false, "Local\AgentConsoleQueueMutex")
    $acquired = $mutex.WaitOne(2000)
    try {
        $queue = @()
        if (Test-Path $queueFile) {
            try {
                $parsed = Get-Content -Path $queueFile -Raw | ConvertFrom-Json
                if ($null -eq $parsed) { $queue = @() }
                elseif ($parsed -is [array]) { $queue = $parsed }
                else { $queue = @($parsed) }
            } catch { $queue = @() }
        }
        # BUG FIX (2026-09-17, real report): an orphaned queue entry — a `start` whose matching
        # `stop` never arrived (session crash/restart, or a lost/misattributed SubagentStop) —
        # used to sit forever with no expiry. A real log capture showed exactly this: a
        # qa-regression `start` from 7 days earlier was still in the queue and got "resumed" by
        # the NEXT real qa-regression `stop`, stamping the wrong (week-old) description on it and
        # leaving the actually-just-finished entry orphaned in turn — which is also how two
        # unrelated agents can show the same auto-clear timestamp: both are stale entries replayed
        # from the persisted log at once, not two real 45-minute timeouts landing together by
        # coincidence. Prune anything older than this before adding the new entry, matching the
        # 45-min STALE_ACTIVE_MS safety net already used client-side in agent-console.html.
        $maxAgeMin = 45
        $cutoff = (Get-Date).ToUniversalTime().AddMinutes(-$maxAgeMin)
        $queue = @($queue | Where-Object {
            $ts = $_.ts
            if (-not $ts) { return $true }  # older entries without a ts: keep, can't judge age
            try { ([datetime]$ts) -ge $cutoff } catch { $true }
        })
        $queue += [ordered]@{ agent = $agent; desc = $desc; ts = (Get-Date).ToUniversalTime().ToString("o") }
        ConvertTo-Json -InputObject $queue -Compress | Set-Content -Path $queueFile -Encoding utf8
    } finally {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
} catch {
    # Swallow everything — see the header comment above.
}
exit 0
