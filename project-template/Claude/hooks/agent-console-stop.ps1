# Claude/hooks/agent-console-stop.ps1
#
# Logs the "stop" half of a subagent invocation for the real-time Agent Console. Wired in
# .claude/settings.json as a SubagentStop hook — the hook Claude Code fires on a subagent's
# REAL completion, whether it ran in the foreground or was dispatched to the background (unlike
# PostToolUse on the dispatch tool itself, which fires as soon as the dispatch returns — see
# agent-console-log.ps1's header comment for the real test that showed why that was wrong for a
# backgrounded subagent).
#
# CORRECTION (2026-08-28, real payload capture) — earlier versions of this script assumed
# SubagentStop's payload carried nothing useful and attributed every stop by blindly popping the
# OLDEST entry off the FIFO queue. A real capture (overlapping coder + qa-regression, one of them
# a long multi-tool-call task) showed two things:
#   1. The payload DOES carry a reliable `agent_type` field directly (e.g. "coder",
#      "qa-regression") whenever this is a REAL dispatched-subagent completion — and `agent_id`
#      matches the id the Agent tool returned at dispatch time. No guessing needed for these.
#   2. Most of the noise wasn't queue mis-ordering at all: while a background subagent runs, the
#      orchestrating session's own idle/poll cycle ALSO fires SubagentStop events (payload has
#      `agent_type:""` and an `agent_id` that never appeared in any start event — confirmed by
#      `last_assistant_message` showing text like "aspetto le notifiche"/"aspetta il
#      completamento", and by a `session_crons` entry matching the orchestrator's own
#      ScheduleWakeup). A single long-running subagent produced several of these phantom events
#      before its own real completion. The old code treated every one of these as a real stop,
#      popped a real queue entry for it, and desynced every attribution after that point — hence
#      the flood of "unknown" cards and real agents stuck on WORKING until the 20-min auto-clear.
# Fix: trust `agent_type` when present (skip entirely, no log line at all, when it's empty — that
# marks a phantom/internal event, not a subagent completion) and use the queue only to recover
# the task `desc`, searching for the oldest QUEUED ENTRY OF THAT SAME AGENT TYPE rather than
# blindly popping index 0 — correct even with two different agent types overlapping. Still
# best-effort for two SIMULTANEOUS invocations of the very same agent type (picks the oldest of
# that type), like the rest of this console (see agent-console.html's own note).
#
# MUST NEVER fail loudly: every error is swallowed, script always exits 0.
#
# Concurrency note: this script and agent-console-log.ps1 both read-modify-write
# agent-console-active.json and can run at the same instant for overlapping subagent
# invocations. A real test confirmed the race is not theoretical — concurrent unsynchronized
# writes corrupted the queue file (fields serialized as arrays / turned up as null instead of
# the real scalar values), which then permanently broke the console's rendering loop. A named
# Mutex (shared with agent-console-log.ps1) now serializes the critical section below.
#
# PowerShell 5.1 gotcha (2026-08-28, real reproduction): DO NOT wrap `Get-Content -Raw |
# ConvertFrom-Json` in an outer `@(...)` — empirically shown to double-nest the result the moment
# the queue has 2+ entries (`Object[1]{ Object[N]{ real items } }` instead of `Object[N]{ real
# items }`), which silently broke the by-agent-type queue search below (every match failed, so
# `desc` came back empty even though the right agent/id was still resolved from the payload
# itself). See agent-console-log.ps1's matching header note for the full repro.

$ErrorActionPreference = "Stop"
try {
    $projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
    $stdin = [Console]::In.ReadToEnd()

    # $debugLog = Join-Path $projectDir "Claude\logs\raw-agent-console-payloads.log"
    # New-Item -ItemType Directory -Force -Path (Split-Path $debugLog) | Out-Null
    # $stdin | Out-File -Append $debugLog

    $payload = $stdin | ConvertFrom-Json -ErrorAction Stop
    if ($payload.hook_event_name -ne "SubagentStop") { exit 0 }

    # Phantom/internal stop (the orchestrating session's own idle-poll cycle, not a real
    # dispatched subagent) — see the header comment. Skip entirely: no log line, don't touch the
    # queue.
    $agent = $payload.agent_type
    if (-not $agent) { exit 0 }

    $logDir = Join-Path $projectDir "Claude\logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $logFile = Join-Path $logDir "agent-console.jsonl"
    $queueFile = Join-Path $logDir "agent-console-active.json"

    $desc = ""
    $mutex = New-Object System.Threading.Mutex($false, "Local\AgentConsoleQueueMutex")
    $acquired = $mutex.WaitOne(2000)
    try {
        if (Test-Path $queueFile) {
            $queue = @()
            try {
                $parsed = Get-Content -Path $queueFile -Raw | ConvertFrom-Json
                if ($null -eq $parsed) { $queue = @() }
                elseif ($parsed -is [array]) { $queue = $parsed }
                else { $queue = @($parsed) }
            } catch { $queue = @() }
            # BUG FIX (2026-09-17, real report): drop orphaned entries (a `start` whose real
            # `stop` never arrived — crashed session, lost/misattributed SubagentStop) before
            # matching. A real log capture showed a 7-day-old orphaned `qa-regression` entry get
            # "resumed" by the next real stop of that type, stamping a week-old description on the
            # just-finished task and shifting the desync onward. Same 45-min cutoff as the
            # client-side STALE_ACTIVE_MS safety net, applied here on the disk-side queue too.
            $maxAgeMin = 45
            $cutoff = (Get-Date).ToUniversalTime().AddMinutes(-$maxAgeMin)
            $queue = @($queue | Where-Object {
                $ts = $_.ts
                if (-not $ts) { return $true }  # older entries without a ts: keep, can't judge age
                try { ([datetime]$ts) -ge $cutoff } catch { $true }
            })
            # Find the oldest (non-expired) queued entry for THIS agent type (not just index 0) —
            # correct even when a different agent type is also active/queued at the same time.
            $matchIdx = -1
            for ($i = 0; $i -lt $queue.Count; $i++) {
                if ($queue[$i].agent -is [string] -and $queue[$i].agent -eq $agent) { $matchIdx = $i; break }
            }
            if ($matchIdx -ge 0) {
                if ($queue[$matchIdx].desc -is [string]) { $desc = $queue[$matchIdx].desc }
                $rest = @()
                for ($i = 0; $i -lt $queue.Count; $i++) {
                    if ($i -ne $matchIdx) { $rest += $queue[$i] }
                }
                ConvertTo-Json -InputObject $rest -Compress | Set-Content -Path $queueFile -Encoding utf8
            }
        }
    } finally {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }

    $entry = [ordered]@{
        ts    = (Get-Date).ToUniversalTime().ToString("o")
        event = "stop"
        agent = $agent
        desc  = $desc
    } | ConvertTo-Json -Compress

    Add-Content -Path $logFile -Value $entry -Encoding utf8
} catch {
    # Swallow everything — see the header comment above.
}
exit 0
