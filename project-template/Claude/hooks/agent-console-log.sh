#!/bin/bash
# Claude/hooks/agent-console-log.sh — bash/macOS/Linux equivalent of agent-console-log.ps1. Read
# that file's header comment for the full explanation (why this only logs "start" now, why the
# tool name check accepts both "Task" and "Agent", and the FIFO queue mechanism used to
# attribute the later "stop" event to the right agent — see agent-console-stop.sh).
# Requires `jq` (a common package-manager install: `brew install jq` / `apt install jq`); if
# it's missing this script does nothing and exits cleanly rather than breaking the subagent
# call it's attached to.

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
payload="$(cat)"

# debug_log="$project_dir/Claude/logs/raw-agent-console-payloads.log"
# mkdir -p "$(dirname "$debug_log")"
# echo "$payload" >> "$debug_log"

tool_name=$(echo "$payload" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
if [ "$tool_name" != "Task" ] && [ "$tool_name" != "Agent" ]; then exit 0; fi

hook_event=$(echo "$payload" | jq -r '.hook_event_name // empty' 2>/dev/null)
[ "$hook_event" = "PreToolUse" ] || exit 0

agent=$(echo "$payload" | jq -r '.tool_input.subagent_type // "unknown"' 2>/dev/null)
desc=$(echo "$payload" | jq -r '.tool_input.description // ""' 2>/dev/null)
ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

log_dir="$project_dir/Claude/logs"
mkdir -p "$log_dir"
log_file="$log_dir/agent-console.jsonl"
queue_file="$log_dir/agent-console-active.json"

jq -nc --arg ts "$ts" --arg agent "$agent" --arg desc "$desc" \
  '{ts:$ts,event:"start",agent:$agent,desc:$desc}' >> "$log_file" 2>/dev/null

[ -f "$queue_file" ] || echo "[]" > "$queue_file"
tmp_queue="$queue_file.tmp"
jq --arg agent "$agent" --arg desc "$desc" '. + [{agent:$agent,desc:$desc}]' \
  "$queue_file" > "$tmp_queue" 2>/dev/null && mv "$tmp_queue" "$queue_file"

exit 0
