#!/bin/bash
# Claude/hooks/agent-console-mcp.sh — bash/macOS/Linux equivalent of agent-console-mcp.ps1. See
# that file's header comment for the full explanation: feeds the Agent Console's "MCP Server"
# node, logging when the UEFN MCP server (mcp__unreal-mcp__call_tool) is called and by whom (a
# bot's agent_type, or "chief-of-staff" if it's the main session), so the console can light that
# node up in real time and show a pulse from whichever bot made the call.
#
# Wired in .claude/settings.json on BOTH PreToolUse and PostToolUse, matched on
# "mcp__unreal-mcp__call_tool" (same matcher after-playtest.sh already uses on PostToolUse — this
# is a second, independent hook command on the same matcher, not a replacement). An MCP tool call
# is synchronous, so PreToolUse/PostToolUse is the right pair here (no SubagentStop involved).
#
# Writes to its own log, Claude/logs/agent-console-mcp.jsonl, kept separate from
# agent-console.jsonl so the two event streams never mix. Requires `jq`; exits quietly without it.
#
# MUST NEVER block or fail a tool call: every error is swallowed, script always exits 0.

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
payload="$(cat)"

# debug_log="$project_dir/Claude/logs/raw-agent-console-mcp-payload.log"
# mkdir -p "$(dirname "$debug_log")"
# echo "$payload" >> "$debug_log"

hook_event=$(echo "$payload" | jq -r '.hook_event_name // empty' 2>/dev/null)
case "$hook_event" in
  PreToolUse) event_name="start" ;;
  PostToolUse) event_name="stop" ;;
  *) exit 0 ;;
esac

caller=$(echo "$payload" | jq -r '.agent_type // empty' 2>/dev/null)
[ -n "$caller" ] || caller="chief-of-staff"

# Best-effort "what was called" label — the unreal-mcp dispatcher's exact payload shape isn't
# documented here, so this tries a few common field names before falling back to a trimmed dump
# of tool_input. If it comes through empty/unhelpful, uncomment the debug lines above, make an
# MCP call, and adjust the field list below to match what you actually see.
label=$(echo "$payload" | jq -r '
  (.tool_input // {}) as $ti |
  ($ti.tool // $ti.action // $ti.toolset // $ti.method // $ti.command // empty)
' 2>/dev/null)
if [ -z "$label" ]; then
  label=$(echo "$payload" | jq -c '.tool_input // {}' 2>/dev/null | cut -c1-80)
fi

log_dir="$project_dir/Claude/logs"
mkdir -p "$log_dir"
log_file="$log_dir/agent-console-mcp.jsonl"

jq -nc --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" --arg event "$event_name" \
  --arg caller "$caller" --arg label "$label" \
  '{ts:$ts,event:$event,caller:$caller,label:$label}' >> "$log_file" 2>/dev/null

exit 0
