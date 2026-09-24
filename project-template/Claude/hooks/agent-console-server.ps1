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
#   - "/stats" serves agent-console-stats.html — the "Stats" tab, real island metrics from the
#              public Fortnite Ecosystem API.
#   - "/island-metrics" / "/island-info" (added v1.71.0) proxy api.fortnite.com/ecosystem/v1 for
#              the island code in Claude/docs/.island-code, with a 5-min/1-hour server-side cache
#              (memory + a logs/*.json fallback file) so a page reload or a 429 rate-limit still
#              shows the last good data instead of an empty page.
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
# --- v1.79.3 concurrency fix -------------------------------------------------------------------
# Before v1.79.3 this server handled exactly one HTTP request at a time: the main loop called
# $listener.GetContext() (blocks until a request arrives), handled that request FULLY and
# SYNCHRONOUSLY (including the "/island-metrics", "/island-info" and "/island-rankings" routes,
# which call out to the external Fortnite API with a 10s timeout), and only THEN looped back to
# accept the next connection. Claude/hooks/agent-console-docs.html fires 6-9 parallel fetch()
# calls on load; if any one of them (or a stray tab hitting the Stats page) landed on a slow/
# unreachable Fortnite API call, the entire server sat blocked on that ONE request for up to 10
# seconds, during which every other pending request from every other tab got no response at all.
# That was the actual cause of the Docs & Status console hanging on "loading..."/"connecting"
# indefinitely, intermittently. Fixed by keeping the accept loop itself synchronous (GetContext()
# is cheap — it only blocks waiting for a NEW connection, independent of how long previous
# requests take to handle) but dispatching each request's actual handling onto a small fixed-size
# RunspacePool (8 runspaces) instead of handling it inline, so the loop is free to accept and
# dispatch the next request immediately while a slow one is still in flight elsewhere. Every route
# keeps its exact prior response format/content-type/error handling — only the scheduling changed.
#
# No external dependencies (pure .NET HttpListener + System.Management.Automation.Runspaces, both
# built into Windows PowerShell 5.1 and PowerShell 7 — nothing to install). Run it from a terminal
# and leave it running while you work; Ctrl+C stops it.
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
# Whitelist for /doc?name=<key> — see agent-console-server.py's matching $DOC_FILES comment
# (added v1.78.0, fixes the Docs & Status console showing hardcoded sample markdown for docs that
# don't reflect the real project at all).
$docFiles = @{
    "status"    = "STATUS.md"
    "roadmap"   = "ROADMAP.md"
    "bugs"      = "BUGS.md"
    "spec"      = "SPEC.md"
    "retention" = "RETENTION-NOTES.md"
    "release"   = "RELEASE-READINESS.md"
}
$projectGenreFile = Join-Path $docsDir ".genre"
$islandCodeFile = Join-Path $docsDir ".island-code"
$statsHtmlPath = Join-Path $root "agent-console-stats.html"
$docsHtmlPath = Join-Path $root "agent-console-docs.html"
$flowHtmlPath = Join-Path $root "agent-console-flow.html"
$metricsCacheFile = Join-Path $logsDir "fortnite-metrics-cache.json"
$infoCacheFile = Join-Path $logsDir "fortnite-island-info-cache.json"
$rankingsCacheFile = Join-Path $logsDir "fortnite-island-rankings-cache.json"
$fortniteApiBase = "https://api.fortnite.com/ecosystem/v1"
$metricsCacheTtlSec = 300   # 5 minutes
$infoCacheTtlSec = 3600     # 1 hour — island title/tags change rarely
$rankingsCacheTtlSec = 300  # 5 minutes
$projectDir = Split-Path -Parent (Split-Path -Parent $root)
$serverStartedAt = (Get-Date).ToUniversalTime().ToString("o")
$genreSkillsDir = Join-Path $env:USERPROFILE ".claude\skills\genre"
$tagsKnownFile = Join-Path $genreSkillsDir "fortnite-tags-known.json"

if (-not (Test-Path $htmlPath)) {
    Write-Error "agent-console.html not found next to this script (expected at $htmlPath)."
    exit 1
}

# --- Shared state for the runspace pool -----------------------------------------------------
# Runspaces do NOT share this script's scope, so every piece of state a request handler needs
# (paths, config, and the Fortnite API's in-memory caches) is bundled into one synchronized
# hashtable and passed explicitly into each dispatched handler invocation. The cache fields are
# on the SAME synchronized hashtable (not per-runspace copies) so concurrent requests still share
# one real cache, same as the old single-threaded version did with its $script: variables.
$State = [hashtable]::Synchronized(@{
    HtmlPath            = $htmlPath
    LogFile             = $logFile
    TokensFile          = $tokensFile
    McpFile             = $mcpFile
    SessionFile         = $sessionFile
    DocsDir             = $docsDir
    ActiveTaskFile      = $activeTaskFile
    DocFiles            = $docFiles
    ProjectGenreFile    = $projectGenreFile
    IslandCodeFile      = $islandCodeFile
    StatsHtmlPath       = $statsHtmlPath
    DocsHtmlPath        = $docsHtmlPath
    FlowHtmlPath        = $flowHtmlPath
    MetricsCacheFile    = $metricsCacheFile
    InfoCacheFile       = $infoCacheFile
    RankingsCacheFile   = $rankingsCacheFile
    FortniteApiBase     = $fortniteApiBase
    MetricsCacheTtlSec  = $metricsCacheTtlSec
    InfoCacheTtlSec     = $infoCacheTtlSec
    RankingsCacheTtlSec = $rankingsCacheTtlSec
    ProjectDir          = $projectDir
    ServerStartedAt     = $serverStartedAt
    TagsKnownFile       = $tagsKnownFile
    # Fortnite API in-memory caches (shared, mutable — same role as the old $script:* variables)
    MetricsMemCache     = $null
    MetricsMemCacheAt   = [datetime]::MinValue
    InfoMemCache        = $null
    InfoMemCacheAt      = [datetime]::MinValue
    RankingsMemCache    = $null
    RankingsMemCacheAt  = [datetime]::MinValue
})

# --- The per-request handler, run inside a pooled runspace ----------------------------------
# Everything a single request needs — including the Fortnite API proxy/cache functions — lives
# in this one script block so it can be shipped whole into a runspace with AddScript(). $Context
# is this request's unique HttpListenerContext (never touched by any other runspace), and $State
# is the shared hashtable above.
$RequestHandler = {
    param($Context, $State)

    $request = $Context.Request
    $response = $Context.Response
    $response.Headers.Add("Access-Control-Allow-Origin", "*")

    function Get-IslandCode {
        if (Test-Path $State.IslandCodeFile) {
            $code = (Get-Content -Path $State.IslandCodeFile -Raw -Encoding UTF8).Trim()
            if ($code) { return $code }
        }
        return $null
    }

    function Update-KnownTags {
        param([string[]]$Tags, [string]$IslandCode)
        if (-not $Tags -or $Tags.Count -eq 0) { return }
        try {
            if (-not (Test-Path $State.TagsKnownFile)) { return }
            $data = Get-Content -Path $State.TagsKnownFile -Raw -Encoding UTF8 | ConvertFrom-Json
            $observed = @($data.observedOnIslands)
            $today = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
            $changed = $false
            foreach ($tag in $Tags) {
                $entry = $observed | Where-Object { $_.tag -eq $tag } | Select-Object -First 1
                if (-not $entry) {
                    $entry = [PSCustomObject]@{
                        tag = $tag; firstSeen = $today; lastSeen = $today
                        timesObserved = 1; islandsObservedOn = @($IslandCode)
                    }
                    $observed += $entry
                    $changed = $true
                } else {
                    if ($entry.lastSeen -ne $today) {
                        $entry.lastSeen = $today
                        $entry.timesObserved = $entry.timesObserved + 1
                        $changed = $true
                    }
                    if ($entry.islandsObservedOn -notcontains $IslandCode) {
                        $entry.islandsObservedOn = @($entry.islandsObservedOn) + $IslandCode
                        $changed = $true
                    }
                }
            }
            if ($changed) {
                $data.observedOnIslands = $observed
                ($data | ConvertTo-Json -Depth 10) | Set-Content -Path $State.TagsKnownFile -Encoding utf8
            }
        } catch {
            # best-effort — swallow any error, never break the info endpoint over this
        }
    }

    function Get-IslandMetricsJson {
        $now = [datetime]::UtcNow
        if ($State.MetricsMemCache -and ($now - $State.MetricsMemCacheAt).TotalSeconds -lt $State.MetricsCacheTtlSec) {
            return $State.MetricsMemCache
        }
        $code = Get-IslandCode
        if (-not $code) { return (@{ error = "no-island-code" } | ConvertTo-Json -Compress) }

        $toDt = [datetime]::UtcNow
        $fromDt = $toDt.AddDays(-7)
        $url = "$($State.FortniteApiBase)/islands/$code/metrics/day?from=$($fromDt.ToString('yyyy-MM-ddTHH:mm:ssZ'))&to=$($toDt.ToString('yyyy-MM-ddTHH:mm:ssZ'))"

        try {
            $payload = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
            $body = @{ payload = $payload; cachedAt = $now.ToString("o"); rateLimited = $false } | ConvertTo-Json -Depth 10 -Compress
            $State.MetricsMemCache = $body
            $State.MetricsMemCacheAt = $now
            Set-Content -Path $State.MetricsCacheFile -Value $body -Encoding utf8
            return $body
        } catch {
            $statusCode = $null
            if ($_.Exception.Response) { $statusCode = [int]$_.Exception.Response.StatusCode }
            if ($statusCode -eq 429 -and (Test-Path $State.MetricsCacheFile)) {
                $stale = Get-Content -Path $State.MetricsCacheFile -Raw -Encoding UTF8
                $obj = $stale | ConvertFrom-Json
                $obj.rateLimited = $true
                $body = $obj | ConvertTo-Json -Depth 10 -Compress
                $State.MetricsMemCache = $body
                $State.MetricsMemCacheAt = $now  # don't hammer the API again until TTL passes
                return $body
            }
            if (Test-Path $State.MetricsCacheFile) {
                return (Get-Content -Path $State.MetricsCacheFile -Raw -Encoding UTF8)
            }
            $msg = if ($statusCode) { "Fortnite API error $statusCode" } else { "could not reach the Fortnite API" }
            return (@{ error = $msg } | ConvertTo-Json -Compress)
        }
    }

    function Get-IslandInfoJson {
        $now = [datetime]::UtcNow
        if ($State.InfoMemCache -and ($now - $State.InfoMemCacheAt).TotalSeconds -lt $State.InfoCacheTtlSec) {
            return $State.InfoMemCache
        }
        $code = Get-IslandCode
        if (-not $code) { return (@{ error = "no-island-code" } | ConvertTo-Json -Compress) }

        try {
            $payload = Invoke-RestMethod -Uri "$($State.FortniteApiBase)/islands/$code" -Method Get -TimeoutSec 10
            $body = $payload | ConvertTo-Json -Depth 10 -Compress
            $State.InfoMemCache = $body
            $State.InfoMemCacheAt = $now
            Set-Content -Path $State.InfoCacheFile -Value $body -Encoding utf8
            if ($payload.tags) { Update-KnownTags -Tags @($payload.tags) -IslandCode $code }
            return $body
        } catch {
            if (Test-Path $State.InfoCacheFile) {
                return (Get-Content -Path $State.InfoCacheFile -Raw -Encoding UTF8)
            }
            return (@{ error = "could not reach the Fortnite API" } | ConvertTo-Json -Compress)
        }
    }

    function Get-IslandRankingsJson {
        $now = [datetime]::UtcNow
        if ($State.RankingsMemCache -and ($now - $State.RankingsMemCacheAt).TotalSeconds -lt $State.RankingsCacheTtlSec) {
            return $State.RankingsMemCache
        }
        $code = Get-IslandCode
        if (-not $code) { return (@{ error = "no-island-code" } | ConvertTo-Json -Compress) }

        $toDt = [datetime]::UtcNow
        $fromDt = $toDt.AddDays(-7)
        $url = "$($State.FortniteApiBase)/islands/$code/rankings?from=$($fromDt.ToString('yyyy-MM-ddTHH:mm:ssZ'))&to=$($toDt.ToString('yyyy-MM-ddTHH:mm:ssZ'))"

        try {
            $payload = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
            $body = @{ payload = $payload; cachedAt = $now.ToString("o"); rateLimited = $false } | ConvertTo-Json -Depth 10 -Compress
            $State.RankingsMemCache = $body
            $State.RankingsMemCacheAt = $now
            Set-Content -Path $State.RankingsCacheFile -Value $body -Encoding utf8
            return $body
        } catch {
            $statusCode = $null
            if ($_.Exception.Response) { $statusCode = [int]$_.Exception.Response.StatusCode }
            if ($statusCode -eq 429 -and (Test-Path $State.RankingsCacheFile)) {
                $stale = Get-Content -Path $State.RankingsCacheFile -Raw -Encoding UTF8
                $obj = $stale | ConvertFrom-Json
                $obj.rateLimited = $true
                $body = $obj | ConvertTo-Json -Depth 10 -Compress
                $State.RankingsMemCache = $body
                $State.RankingsMemCacheAt = $now
                return $body
            }
            if (Test-Path $State.RankingsCacheFile) {
                return (Get-Content -Path $State.RankingsCacheFile -Raw -Encoding UTF8)
            }
            $msg = if ($statusCode) { "Fortnite API error $statusCode" } else { "could not reach the Fortnite API" }
            return (@{ error = $msg } | ConvertTo-Json -Compress)
        }
    }

    try {
        if ($request.Url.AbsolutePath -eq "/log") {
            $lines = @()
            if (Test-Path $State.LogFile) {
                $lines = @(Get-Content -Path $State.LogFile -Encoding UTF8 | Where-Object { $_.Trim() -ne "" })
            }
            $json = "[" + ($lines -join ",") + "]"
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/tokens") {
            $json = "{}"
            if (Test-Path $State.TokensFile) {
                $content = (Get-Content -Path $State.TokensFile -Raw -Encoding UTF8).Trim()
                if ($content) { $json = $content }
            }
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/mcp") {
            $lines = @()
            if (Test-Path $State.McpFile) {
                $lines = @(Get-Content -Path $State.McpFile -Encoding UTF8 | Where-Object { $_.Trim() -ne "" })
            }
            $json = "[" + ($lines -join ",") + "]"
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/session") {
            $json = '{"active":false}'
            if (Test-Path $State.SessionFile) {
                $content = (Get-Content -Path $State.SessionFile -Raw -Encoding UTF8).Trim()
                if ($content) { $json = $content }
            }
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/active-task") {
            $text = ""
            if (Test-Path $State.ActiveTaskFile) {
                $text = (Get-Content -Path $State.ActiveTaskFile -Raw -Encoding UTF8).Trim()
            }
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
            $response.ContentType = "text/plain; charset=utf-8"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/doc") {
            $key = $request.QueryString["name"]
            $filename = if ($key) { $State.DocFiles[$key] } else { $null }
            if (-not $filename) {
                $json = (@{ error = "unknown doc key" } | ConvertTo-Json -Compress)
            } else {
                $docPath = Join-Path $State.DocsDir $filename
                $exists = Test-Path $docPath
                $content = ""
                # v1.79.4 fix: use .NET File.ReadAllText directly instead of Get-Content -Raw.
                # Get-Content can, under some PS host/pipeline edge cases, still bind as a line
                # array even with -Raw specified, which ConvertTo-Json then serializes as a JSON
                # array instead of a single string -- the client's .replace()/.trim() calls then
                # fail with "not a function" on real, large, real-world docs. ReadAllText always
                # returns exactly one string, unambiguously, and is faster on large files too.
                if ($exists) { $content = [System.IO.File]::ReadAllText($docPath, [System.Text.Encoding]::UTF8) }
                $json = (@{ name = $filename; exists = [bool]$exists; content = $content } | ConvertTo-Json -Compress)
            }
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/project-genre") {
            $text = ""
            if (Test-Path $State.ProjectGenreFile) {
                $text = (Get-Content -Path $State.ProjectGenreFile -Raw -Encoding UTF8).Trim()
            }
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
            $response.ContentType = "text/plain; charset=utf-8"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/whoami") {
            $json = (@{ project = $State.ProjectDir; started_at = $State.ServerStartedAt } | ConvertTo-Json -Compress)
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/island-metrics") {
            $json = Get-IslandMetricsJson
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/island-info") {
            $json = Get-IslandInfoJson
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/island-rankings") {
            $json = Get-IslandRankingsJson
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } elseif ($request.Url.AbsolutePath -eq "/stats" -or $request.Url.AbsolutePath -eq "/agent-console-stats.html") {
            if (-not (Test-Path $State.StatsHtmlPath)) {
                $response.StatusCode = 404
            } else {
                $bytes = [System.IO.File]::ReadAllBytes($State.StatsHtmlPath)
                $response.ContentType = "text/html; charset=utf-8"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
        } elseif ($request.Url.AbsolutePath -eq "/docs" -or $request.Url.AbsolutePath -eq "/agent-console-docs.html") {
            if (-not (Test-Path $State.DocsHtmlPath)) {
                $response.StatusCode = 404
            } else {
                $bytes = [System.IO.File]::ReadAllBytes($State.DocsHtmlPath)
                $response.ContentType = "text/html; charset=utf-8"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
        } elseif ($request.Url.AbsolutePath -eq "/flow" -or $request.Url.AbsolutePath -eq "/agent-console-flow.html") {
            if (-not (Test-Path $State.FlowHtmlPath)) {
                $response.StatusCode = 404
            } else {
                $bytes = [System.IO.File]::ReadAllBytes($State.FlowHtmlPath)
                $response.ContentType = "text/html; charset=utf-8"
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
        } else {
            $bytes = [System.IO.File]::ReadAllBytes($State.HtmlPath)
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

# --- Runspace pool: bounds concurrency to a small fixed number of workers -------------------
$MaxConcurrency = 8
$initialSessionState = [System.Management.Automation.Runspaces.InitialSessionState]::CreateDefault()
$runspacePool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool(1, $MaxConcurrency, $initialSessionState, $Host)
$runspacePool.Open()

# In-flight dispatches, so we can reap finished ones (Dispose them, EndInvoke to surface any
# terminating error from the handler itself) instead of leaking a PowerShell instance per request
# for the life of the process.
$inFlight = New-Object System.Collections.Generic.List[object]

function Complete-FinishedDispatches {
    param([bool]$WaitForAll = $false)
    for ($i = $inFlight.Count - 1; $i -ge 0; $i--) {
        $item = $inFlight[$i]
        if ($WaitForAll -or $item.AsyncResult.IsCompleted) {
            try {
                $item.PS.EndInvoke($item.AsyncResult) | Out-Null
            } catch {
                # A handler-level exception already resulted in a 500 inside its own try/catch;
                # this just prevents a stray exception from EndInvoke itself going unobserved.
            }
            $item.PS.Dispose()
            $inFlight.RemoveAt($i)
        }
    }
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
        # GetContext() only blocks waiting for a NEW connection to arrive — it does not wait for
        # any previously-accepted request to finish being handled, since handling now happens on
        # a pooled runspace, not inline here. This is what lets multiple in-flight requests
        # (including one stuck for up to 10s on a slow Fortnite API call) coexist without one
        # blocking the others.
        $context = $listener.GetContext()

        # Each request gets its own PowerShell instance bound to the shared pool; the pool caps
        # how many run at once (MaxConcurrency), so this never spawns unbounded threads even
        # under a burst of requests. $context is unique per request, so no two dispatches ever
        # touch the same HttpListenerContext/response.
        $ps = [System.Management.Automation.PowerShell]::Create()
        $ps.RunspacePool = $runspacePool
        [void]$ps.AddScript($RequestHandler).AddArgument($context).AddArgument($State)
        $asyncResult = $ps.BeginInvoke()
        $inFlight.Add([PSCustomObject]@{ PS = $ps; AsyncResult = $asyncResult })

        # Reap anything that's already finished so $inFlight (and its PowerShell instances) don't
        # grow unbounded over a long-running dev session.
        Complete-FinishedDispatches
    }
} finally {
    $listener.Stop()
    $listener.Close()
    # Let any still-running requests finish (they already have real client sockets open), then
    # dispose every PowerShell instance and close the pool so nothing is leaked on shutdown.
    Complete-FinishedDispatches -WaitForAll $true
    $runspacePool.Close()
    $runspacePool.Dispose()
}
