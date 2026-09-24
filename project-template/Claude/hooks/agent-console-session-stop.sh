#!/bin/bash
# Claude/hooks/agent-console-session-stop.sh — bash/macOS/Linux equivalent of
# agent-console-session-stop.ps1. Feeds the Agent Console's "YOU" node: marks the session idle
# (Claude yielded back to you, waiting for your next message) the moment the main session's own
# Stop hook fires. Paired with agent-console-tokens.sh, which marks the session active on every
# tool call — this is the one authoritative "went idle" signal, since Stop only fires when the
# main agent is genuinely done producing a turn, not on every tool call the way PostToolUse does.
#
# Wired in .claude/settings.json as a second command under the existing "Stop" hook (alongside
# the STATUS.md reminder echo) — no matcher; Stop doesn't use one. Requires `jq`; exits quietly
# without it (the console just won't show YOU going idle — everything else keeps working).
#
# MUST NEVER fail loudly: every error is swallowed, script always exits 0.

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cat >/dev/null  # drain stdin — the payload itself isn't needed here

log_dir="$project_dir/Claude/logs"
mkdir -p "$log_dir"
session_file="$log_dir/agent-console-session.json"

jq -nc --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" '{active:false,ts:$ts}' > "$session_file" 2>/dev/null

exit 0
