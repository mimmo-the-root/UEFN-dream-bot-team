#!/bin/bash
# Claude/hooks/agent-console-stop.sh — bash/macOS/Linux equivalent of agent-console-stop.ps1.
# Read that file's header comment for the full explanation (SubagentStop is the real-completion
# signal, unlike PostToolUse on the dispatch tool itself; attribution via the FIFO queue written
# by agent-console-log.sh). Requires `jq`; exits quietly without it.

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cat >/dev/null  # drain stdin — the payload itself isn't needed here

log_dir="$project_dir/Claude/logs"
mkdir -p "$log_dir"
log_file="$log_dir/agent-console.jsonl"
queue_file="$log_dir/agent-console-active.json"

agent="unknown"
desc=""
if [ -f "$queue_file" ]; then
  agent=$(jq -r '.[0].agent // "unknown"' "$queue_file" 2>/dev/null) || agent="unknown"
  desc=$(jq -r '.[0].desc // ""' "$queue_file" 2>/dev/null) || desc=""
  tmp_queue="$queue_file.tmp"
  jq '.[1:]' "$queue_file" > "$tmp_queue" 2>/dev/null && mv "$tmp_queue" "$queue_file"
fi

ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq -nc --arg ts "$ts" --arg agent "$agent" --arg desc "$desc" \
  '{ts:$ts,event:"stop",agent:$agent,desc:$desc}' >> "$log_file" 2>/dev/null

exit 0
