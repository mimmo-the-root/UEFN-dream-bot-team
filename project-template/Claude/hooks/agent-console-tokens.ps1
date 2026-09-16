# Claude/hooks/agent-console-tokens.ps1
#
# Feeds the Agent Console's "Tokens this session" stat. Wired in .claude/settings.json as a
# PostToolUse hook with NO matcher (fires after every single tool call, not just subagent
# dispatches) — token usage happens on every turn, not only when a subagent runs, so this needs
# a broader trigger than agent-console-log.ps1/agent-console-stop.ps1.
#
# EXPERIMENTAL / best-effort, more so than the rest of this console. It works by incrementally
# reading the session transcript file Claude Code itself writes (`transcript_path` in the hook
# payload — a JSONL file, one line per message) and summing whatever `usage` object it finds on
# each assistant message. This is NOT the official/guaranteed way to read token usage — there is
# no documented API for it — it's inferred from the transcript's on-disk shape, which could
# change between Claude Code versions. If the numbers look wrong or stay at zero, see the
# Troubleshooting note in SETUP-GUIDE.md section 5b; the fix is almost always adjusting the
# `$usage = ...` lookup below to match the real shape (uncomment the debug line to capture one
# raw transcript line and see for yourself).
#
# What "total" means here: the SUM of input_tokens + output_tokens + cache_read_input_tokens +
# cache_creation_input_tokens across every assistant turn seen so far this session. This is a
# rough proxy for activity, not a billing figure — Anthropic's API prices these four token kinds
# very differently (a cache read is far cheaper than a fresh input token), and input_tokens on
# each turn already reflects that turn's full context, not just what's "new" — so this number
# trends up quickly on a long session and shouldn't be read as "dollars spent." Treat it as "how
# much token activity has this session generated," nothing more precise than that.
#
# Reads incrementally (tracks a byte offset per transcript file already processed, in
# Claude/logs/agent-console-tokens-state.json) so a long session doesn't mean re-parsing an
# ever-growing file on every single tool call.
#
# MUST NEVER block or fail a tool call: every error is swallowed, script always exits 0.

$ErrorActionPreference = "Stop"
try {
    $projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
    $stdin = [Console]::In.ReadToEnd()

    # $debugLog = Join-Path $projectDir "Claude\logs\raw-agent-console-tokens-payload.log"
    # New-Item -ItemType Directory -Force -Path (Split-Path $debugLog) | Out-Null
    # $stdin | Out-File -Append $debugLog

    $payload = $stdin | ConvertFrom-Json -ErrorAction Stop
    $transcriptPath = $payload.transcript_path
    if (-not $transcriptPath -or -not (Test-Path $transcriptPath)) { exit 0 }

    $logDir = Join-Path $projectDir "Claude\logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $stateFile = Join-Path $logDir "agent-console-tokens-state.json"
    $outFile = Join-Path $logDir "agent-console-tokens.json"

    # Feeds the Agent Console's "YOU" node too, piggybacking on this hook rather than
    # registering a third always-fires PostToolUse command: ANY tool call (main session or a
    # subagent) means Claude is actively doing something right now, so mark the session active
    # on every invocation of this script. The matching "went idle" signal lives in
    # agent-console-session-stop.ps1 on the Stop hook (fires when the main session actually
    # yields back to you) — that's the one authoritative "idle" moment; this file only ever
    # asserts "active" from this side.
    try {
        $sessionFile = Join-Path $logDir "agent-console-session.json"
        [ordered]@{ active = $true; ts = (Get-Date).ToUniversalTime().ToString("o") } |
            ConvertTo-Json -Compress | Set-Content -Path $sessionFile -Encoding utf8
    } catch { }

    # State: { offsets: { "<transcript path>": <bytes already processed> },
    #          totals: { input, output, cache_read, cache_creation } }
    $state = $null
    if (Test-Path $stateFile) {
        try { $state = Get-Content -Path $stateFile -Raw | ConvertFrom-Json -ErrorAction Stop } catch { $state = $null }
    }
    if (-not $state) {
        $state = [pscustomobject]@{
            offsets = [pscustomobject]@{}
            totals  = [pscustomobject]@{ input = 0; output = 0; cache_read = 0; cache_creation = 0 }
        }
    }

    $prop = $state.offsets.PSObject.Properties[$transcriptPath]
    $startOffset = if ($prop) { [int64]$prop.Value } else { 0 }

    $fileLength = (Get-Item $transcriptPath).Length
    if ($fileLength -gt $startOffset) {
        $fs = [System.IO.File]::Open($transcriptPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $fs.Seek($startOffset, [System.IO.SeekOrigin]::Begin) | Out-Null
            $toRead = $fileLength - $startOffset
            $buffer = New-Object byte[] $toRead
            $readBytes = $fs.Read($buffer, 0, $toRead)
            $text = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $readBytes)
        } finally { $fs.Close() }

        $lastNewline = $text.LastIndexOf("`n")
        if ($lastNewline -ge 0) {
            $completeText = $text.Substring(0, $lastNewline)
            $consumedBytes = [System.Text.Encoding]::UTF8.GetByteCount($text.Substring(0, $lastNewline + 1))

            foreach ($line in ($completeText -split "`n")) {
                if ([string]::IsNullOrWhiteSpace($line)) { continue }
                try {
                    $obj = $line | ConvertFrom-Json -ErrorAction Stop
                    $usage = $null
                    if ($obj.message -and $obj.message.usage) { $usage = $obj.message.usage }
                    elseif ($obj.usage) { $usage = $obj.usage }
                    if ($usage) {
                        if ($usage.input_tokens) { $state.totals.input += [int64]$usage.input_tokens }
                        if ($usage.output_tokens) { $state.totals.output += [int64]$usage.output_tokens }
                        if ($usage.cache_read_input_tokens) { $state.totals.cache_read += [int64]$usage.cache_read_input_tokens }
                        if ($usage.cache_creation_input_tokens) { $state.totals.cache_creation += [int64]$usage.cache_creation_input_tokens }
                    }
                } catch { }
            }

            if ($prop) { $prop.Value = $startOffset + $consumedBytes }
            else { $state.offsets | Add-Member -NotePropertyName $transcriptPath -NotePropertyValue ($startOffset + $consumedBytes) -Force }
        }
    }

    $state | ConvertTo-Json -Compress -Depth 5 | Set-Content -Path $stateFile -Encoding utf8

    $total = $state.totals.input + $state.totals.output + $state.totals.cache_read + $state.totals.cache_creation
    $snapshot = [ordered]@{
        input          = $state.totals.input
        output         = $state.totals.output
        cache_read     = $state.totals.cache_read
        cache_creation = $state.totals.cache_creation
        total          = $total
        updated        = (Get-Date).ToUniversalTime().ToString("o")
    } | ConvertTo-Json -Compress
    Set-Content -Path $outFile -Value $snapshot -Encoding utf8
} catch {
    # Swallow everything — see the header comment above.
}
exit 0
