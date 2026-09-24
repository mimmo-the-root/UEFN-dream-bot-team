#!/bin/bash
# Claude/hooks/agent-console-log.sh — bash/macOS/Linux equivalent of agent-console-log.ps1. Read
# that file's header comment for the full explanation (why this only logs "start" now, why the
# tool name check accepts both "Task" and "Agent", and the FIFO-by-agent-type queue mechanism
# used to attribute the later "stop" event to the right agent — see agent-console-stop.sh).
# Requires `jq` (a common package-manager install: `brew install jq` / `apt install jq`); if
# it's missing this script does nothing and exits cleanly rather than breaking the subagent
# call it's attached to.
#
# PARITY NOTE (2026-09-17): this script had drifted out of sync with agent-console-log.ps1 — it
# never picked up the ts/TTL fix that agent-console-stop.ps1's queue reading also needed. Brought
# back to parity now that the kit is public and macOS/Linux users are expected. See
# agent-console-stop.ps1's header comment for the full history/real-repro notes (SubagentStop
# payload carries a reliable `agent_type`, phantom internal stop events during orchestrator
# polling, the FIFO-by-type match, and the orphaned-entry/no-expiry bug fixed here).
#
# Concurrency: this script and agent-console-stop.sh both read-modify-write
# agent-console-active.json and can run at the same instant for overlapping subagent
# invocations. Serialized with `flock` on a sibling lock file (the Windows side uses a named
# Mutex for the same reason — see agent-console-log.ps1).

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
lock_file="$log_dir/agent-console-active.lock"

jq -nc --arg ts "$ts" --arg agent "$agent" --arg desc "$desc" \
  '{ts:$ts,event:"start",agent:$agent,desc:$desc}' >> "$log_file" 2>/dev/null

[ -f "$queue_file" ] || echo "[]" > "$queue_file"

# BUG FIX (2026-09-17, real report — see agent-console-stop.ps1 header for the full repro): an
# orphaned queue entry (a `start` whose matching `stop` never arrived — crashed session, lost or
# misattributed SubagentStop) used to sit forever with no expiry, and could later get "resumed" by
# an unrelated real `stop` of the same agent type, stamping a stale description on it. Every queue
# entry now carries its own `ts`, and any entry older than 45 minutes (same threshold as the
# client-side STALE_ACTIVE_MS safety net in agent-console.html) is dropped before a new one is
# pushed.
max_age_seconds=$((45 * 60))

(
  flock -w 2 200 || exit 0  # best-effort: proceed unlocked rather than block a real subagent call
  tmp_queue="$queue_file.tmp.$$"
  jq --arg agent "$agent" --arg desc "$desc" --arg ts "$ts" --argjson maxage "$max_age_seconds" '
    (now - $maxage) as $cutoff
    | map(select(
        (.ts // empty) as $t
        | if $t == null or $t == "" then true
          else (($t | fromdateiso8601?) // 0) >= $cutoff
          end
      ))
    + [{agent:$agent, desc:$desc, ts:$ts}]
  ' "$queue_file" > "$tmp_queue" 2>/dev/null && mv "$tmp_queue" "$queue_file"
) 200>"$lock_file"

exit 0
