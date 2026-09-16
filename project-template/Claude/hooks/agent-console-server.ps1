# Claude/hooks/agent-console-server.ps1
#
# Tiny local web server for the real-time "Agent Console" (Claude/hooks/agent-console.html).
# It does five things on http://127.0.0.1:<port>/ (default port 8765):
#   - "/"      serves agent-console.html as-is.
#   - "/log"   serves the current content of Claude/logs/agent-console.jsonl as a JSON array,
#              which the page polls once a second to animate agents in real time.
#   - "/tokens" serves the current content of Claude/logs/agent-console-tokens.json (or "{}" if
#              it doesn't exist yet) — the session's approximate cumulative token usage, see
#              agent-console-tokens.ps1 for how that file gets written.
#   - "/mcp"   serves the current content of Claude/logs/agent-console-mcp.jsonl as a JSON array
#              (same shape/pattern as "/log") — UEFN MCP server call start/stop events, see
#              agent-console-mcp.ps1.
#   - "/session" serves the current content of Claude/logs/agent-console-session.json (or
#              '{"active":false}' if it doesn't exist yet) — whether the main Claude Code
#              session is actively working or waiting on you, see agent-console-tokens.ps1 (sets
#              active:true) and agent-console-session-stop.ps1 (sets active:false).
#   - "/active-task" serves the current content of Claude/docs/.active-task (or "" if it doesn't
#              exist) — the ROADMAP task ID coder is currently working, per rule 13a in
#              ~/.claude/CLAUDE.md. Used only as a best-effort label on the console's miniflow
#              rail; the rail itself works fine without this file ever existing.
#   - "/whoami" serves '{"project":"<absolute path to this project's folder>",
#              "started_at":"<ISO timestamp this server process actually started>"}'. The
#              "project" field is how session-start-reminder.ps1/.sh tells "this port is already
#              serving THIS project" apart from "a different/stale project's server is still
#              bound here" when a new session starts. The "started_at" field is what the console
#              page itself uses for its "Session running for" stat — v1.44 fix: that stat used to
#              be computed from the OLDEST line in agent-console.jsonl, which persists across
#              restarts by design (it's meant to keep activity history), so after using the kit
#              across several sessions it kept showing hours/days of elapsed time even seconds
#              after a fresh restart — looked exactly like "the server never actually restarted"
#              even when it had. Using this server process's own real start time fixes that
#              without touching the history file at all.

#
# No external dependencies (pure .NET HttpListener, built into Windows PowerShell) — nothing to
# install. Run it from a terminal and leave it running while you work; Ctrl+C stops it.
#
#   powershell -ExecutionPolicy Bypass -File Claude\hooks\agent-console-server.ps1
#
# Then open http://127.0.0.1:8765/ in your browser (any browser — this is a real local web
# server, not a file:// page, so there's nothing special to configure). To use a different port:
#
#   powershell -ExecutionPolicy Bypass -File Claude\hooks\agent-console-server.ps1 -Port 9000

param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$htmlPath = Join-Path $root "agent-console.html"
$logsDir = Join-Path (Split-Path -Parent $root) "logs"
$logFile = Join-Path $logsDir "agent-console.jsonl"
$tokensFile = Join-Path $logsDir "agent-console-tokens.json"
$mcpFile = Join-Path $logsDir "agent-console-mcp.jsonl"
$sessionFile = Join-Path $logsDir "agent-console-session.json"
$docsDir = Join-Path (Split-Path -Parent $root) "docs"
$activeTaskFile = Join-Path $docsDir ".active-task"
$projectDir = Split-Path -Parent (Split-Path -Parent $root)
$serverStartedAt = (Get-Date).ToUniversalTime().ToString("o")

if (-not (Test-Path $htmlPath)) {
    Write-Error "agent-console.html not found next to this script (expected at $htmlPath)."
    exit 1
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:$Port/")
try {
    $listener.Start()
} catch {
    Write-Error "Could not start the server on port $Port (already in use? try -Port 9000). $_"
    exit 1
}

Write-Host "Agent Console running at http://127.0.0.1:$Port/  (Ctrl+C to stop)"

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        $response.Headers.Add("Access-Control-Allow-Origin", "*")

        try {
            if ($request.Url.AbsolutePath -eq "/log") {
                $lines = @()
                if (Test-Path $logFile) {
                    $lines = @(Get-Content -Path $logFile -Encoding UTF8 | Where-Object { $_.Trim() -ne "" })
                }
                $json = "[" + ($lines -join ",") + "]"
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } elseif ($request.Url.AbsolutePath -eq "/tokens") {
                $json = "{}"
                if (Test-Path $tokensFile) {
                    $content = (Get-Content -Path $tokensFile -Raw -Encoding UTF8).Trim()
                    if ($content) { $json = $content }
                }
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } elseif ($request.Url.AbsolutePath -eq "/mcp") {
                $lines = @()
                if (Test-Path $mcpFile) {
                    $lines = @(Get-Content -Path $mcpFile -Encoding UTF8 | Where-Object { $_.Trim() -ne "" })
                }
                $json = "[" + ($lines -join ",") + "]"
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } elseif ($request.Url.AbsolutePath -eq "/session") {
                $json = '{"active":false}'
                if (Test-Path $sessionFile) {
                    $content = (Get-Content -Path $sessionFile -Raw -Encoding UTF8).Trim()
                    if ($content) { $json = $content }
                }
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } elseif ($request.Url.AbsolutePath -eq "/active-task") {
                $text = ""
                if (Test-Path $activeTaskFile) {
                    $text = (Get-Content -Path $activeTaskFile -Raw -Encoding UTF8).Trim()
                }
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
                $response.ContentType = "text/plain; charset=utf-8"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } elseif ($request.Url.AbsolutePath -eq "/whoami") {
                $json = (@{ project = $projectDir; started_at = $serverStartedAt } | ConvertTo-Json -Compress)
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } else {
                $bytes = [System.IO.File]::ReadAllBytes($htmlPath)
                $response.ContentType = "text/html; charset=utf-8"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
        } catch {
            $response.StatusCode = 500
        } finally {
            $response.OutputStream.Close()
        }
    }
} finally {
    $listener.Stop()
    $listener.Close()
}
