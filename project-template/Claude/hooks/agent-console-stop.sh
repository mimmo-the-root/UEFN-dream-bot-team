#!/bin/bash
# Claude/hooks/agent-console-stop.sh — bash/macOS/Linux equivalent of agent-console-stop.ps1.
# Read that file's header comment for the full explanation and real-repro history: SubagentStop
# is the real-completion signal (foreground or background), its payload carries a reliable
# `agent_type` (skip entirely — no log line — when it's empty: that marks a phantom internal
# stop fired by the orchestrating session's own idle/poll cycle, not a real subagent completion),
# and attribution is done by matching the OLDEST queued entry of that same agent type, not by
# blindly popping index 0.
#
# PARITY NOTE (2026-09-17): this script previously did NOT read the payload at all — it drained
# stdin and blindly popped queue index 0, i.e. it still had the bug the .ps1 side already fixed
# (phantom polling events and interleaved agent types would desync every attribution after the
# first mismatch). Rewritten now that the kit is public and macOS/Linux users are expected.
# Requires `jq`; exits quietly without it.
#
# Concurrency: this script and agent-console-log.sh both read-modify-write
# agent-console-active.json and can run at the same instant for overlapping subagent
# invocations — serialized with `flock` on a sibling lock file (same reason the Windows side
# uses a named Mutex).

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
payload="$(cat)"

# debug_log="$project_dir/Claude/logs/raw-agent-console-payloads.log"
# mkdir -p "$(dirname "$debug_log")"
# echo "$payload" >> "$debug_log"

hook_event=$(echo "$payload" | jq -r '.hook_event_name // empty' 2>/dev/null) || exit 0
[ "$hook_event" = "SubagentStop" ] || exit 0

# Phantom/internal stop (the orchestrating session's own idle-poll cycle, not a real dispatched
# subagent) — see the header comment. Skip entirely: no log line, don't touch the queue.
agent=$(echo "$payload" | jq -r '.agent_type // empty' 2>/dev/null)
[ -n "$agent" ] || exit 0

log_dir="$project_dir/Claude/logs"
mkdir -p "$log_dir"
log_file="$log_dir/agent-console.jsonl"
queue_file="$log_dir/agent-console-active.json"
lock_file="$log_dir/agent-console-active.lock"

desc=""
max_age_seconds=$((45 * 60))

if [ -f "$queue_file" ]; then
  (
    flock -w 2 200 || exit 0  # best-effort: never block on a stop event
    tmp_queue="$queue_file.tmp.$$"
    # BUG FIX (2026-09-17, real report): drop orphaned entries (a `start` whose real `stop` never
    # arrived) older than 45 minutes BEFORE matching — a real log capture showed a 7-day-old
    # orphaned `qa-regression` entry get "resumed" by the next real stop of that type, stamping a
    # week-old description on the just-finished task. Same threshold as the client-side
    # STALE_ACTIVE_MS safety net.
    # Then find the OLDEST remaining entry for THIS agent type (not index 0) — correct even when
    # a different agent type is also active/queued at the same time — pull its desc, and drop
    # that one entry from what gets written back.
    jq --arg agent "$agent" --argjson maxage "$max_age_seconds" '
      (now - $maxage) as $cutoff
      | map(select(
          (.ts // empty) as $t
          | if $t == null or $t == "" then true
            else (($t | fromdateiso8601?) // 0) >= $cutoff
            end
        )) as $fresh
      | ($fresh | map(.agent == $agent) | index(true)) as $idx
      | {
          desc: (if $idx != null then $fresh[$idx].desc else "" end),
          queue: (if $idx != null then ($fresh[:$idx] + $fresh[($idx+1):]) else $fresh end)
        }
    ' "$queue_file" > "$tmp_queue.result" 2>/dev/null

    if [ -s "$tmp_queue.result" ]; then
      desc=$(jq -r '.desc // ""' "$tmp_queue.result" 2>/dev/null)
      jq '.queue' "$tmp_queue.result" > "$tmp_queue" 2>/dev/null && mv "$tmp_queue" "$queue_file"
      echo "$desc" > "$log_dir/.agent-console-stop-desc.tmp"
    fi
    rm -f "$tmp_queue.result"
  ) 200>"$lock_file"
  desc=$(cat "$log_dir/.agent-console-stop-desc.tmp" 2>/dev/null || echo "")
  rm -f "$log_dir/.agent-console-stop-desc.tmp"
fi

ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq -nc --arg ts "$ts" --arg agent "$agent" --arg desc "$desc" \
  '{ts:$ts,event:"stop",agent:$agent,desc:$desc}' >> "$log_file" 2>/dev/null

exit 0
