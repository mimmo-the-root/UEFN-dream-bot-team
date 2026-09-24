#!/bin/bash
# Claude/hooks/session-start-reminder.sh — bash/macOS/Linux equivalent of
# session-start-reminder.ps1. See that file's header comment for the full explanation of the
# v1.40 change: this no longer ASKS whether to start the console — it deterministically ensures
# the console server is running and correctly scoped to THIS project before Claude's very first
# reply, fixing the "switched UEFN projects and got left looking at the previous project's stale
# console" bug (every server now exposes /whoami, reporting which project folder it's actually
# serving, so a same-port server from a different project is recognized as stale and replaced
# instead of being mistaken for "already running").
#
# Requires `jq` and `curl`; if either is missing this exits quietly and CLAUDE.md's own reminder
# (the guaranteed fallback, see that file's "Rules for this project's agents" section) still
# covers it. Everything here is best-effort — any failure is swallowed, this must never block a
# session from starting.

set -uo pipefail

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
console_path="$project_dir/Claude/hooks/agent-console.html"
server_script="$project_dir/Claude/hooks/agent-console-server.py"
port=8765

# v1.70.4: wrong-launch-folder detector. This kit's scaffold lives inside the project's Content/
# folder (see SETUP-INSTRUCTIONS.md), so CLAUDE_PROJECT_DIR must point INSIDE Content/, not at the
# UEFN project's outer root. Launching claude from the wrong folder makes every hook in
# settings.json point at a Claude/hooks/ that doesn't exist there - they fail silently (no error
# surfaced), so the console never starts and Claude/logs/agent-console.jsonl never gets written,
# with nothing looking obviously broken until you notice the console is stale. This still fires
# even though the real Claude/hooks/ isn't where expected, by checking one level down at
# Content/Claude/hooks/ specifically to catch this exact mistake and say so up front, instead of
# failing quietly like everything else below would.
if [ ! -f "$console_path" ] && [ -f "$project_dir/Content/Claude/hooks/agent-console.html" ]; then
    warn_context="WARNING - wrong launch folder for this project. This kit's scaffold (Claude/hooks/, \
Claude/docs/, etc.) lives inside Content/, but this session was started from $project_dir, one \
level above it. Every hook in .claude/settings.json uses the CLAUDE_PROJECT_DIR environment \
variable to build the path to Claude/hooks/..., which does not exist at this level - so hooks are \
failing silently: the Agent Console will not start, and Claude/logs/agent-console.jsonl will not \
receive new events, with no visible error. Tell the owner plainly, in your very first reply, to \
close this session and relaunch claude from inside the Content folder (see \
Claude/SETUP-INSTRUCTIONS.md) - don't just proceed as if nothing's wrong."
    if command -v jq >/dev/null 2>&1; then
        jq -n --arg ctx "$warn_context" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$ctx}}'
    fi
fi

[ -f "$console_path" ] || exit 0
command -v jq >/dev/null 2>&1 || exit 0
command -v curl >/dev/null 2>&1 || exit 0

this_project=$(cd "$project_dir" 2>/dev/null && pwd)
[ -n "$this_project" ] || this_project="$project_dir"

already_correct=false
served_project=$(curl -s --max-time 2 "http://127.0.0.1:$port/whoami" 2>/dev/null | jq -r '.project // empty' 2>/dev/null)
if [ -n "$served_project" ] && [ "$served_project" = "$this_project" ]; then
    already_correct=true
fi

if [ "$already_correct" = false ]; then
    # Whatever's on the port (this project's own stale process, a different project's server, or
    # nothing at all) needs to go before we bind a fresh one — but only kill it if it actually
    # looks like one of our own server processes, never an unrelated program on that port.
    if command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null)
        for p in $pids; do
            pname=$(ps -p "$p" -o comm= 2>/dev/null)
            case "$pname" in
                *python*) kill -9 "$p" 2>/dev/null ;;
            esac
        done
        [ -n "$pids" ] && sleep 0.4
    fi

    nohup python3 "$server_script" > /dev/null 2>&1 &
    sleep 0.5  # give the fresh server a moment to bind before opening it
fi

# v1.43: also open the console in the owner's default browser automatically, every session — an
# explicit owner preference (previously this only mentioned the URL). Best-effort: tries the
# platform opener that's actually present (macOS `open`, Linux `xdg-open`), silently does nothing
# if neither exists (e.g. a headless box) rather than failing the hook.
if command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:$port/" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:$port/" >/dev/null 2>&1 || true
fi

context=$(cat <<EOF
This project's real-time Agent Console has already been started (or, if it was previously
serving a different project on this same port, restarted) automatically for THIS project, and
opened in the owner's default browser - no action needed from you and don't ask permission. Just
mention in your first reply that it's live at http://127.0.0.1:$port/ in case the owner closed
the tab or wants to reopen it. Only touch the console server yourself (stop/restart it) if the
owner reports a specific problem with it.
EOF
)

jq -n --arg ctx "$context" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$ctx}}'
exit 0
