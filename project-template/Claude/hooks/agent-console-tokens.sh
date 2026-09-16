#!/bin/bash
# Claude/hooks/agent-console-tokens.sh — bash/macOS/Linux equivalent of
# agent-console-tokens.ps1. See that file's header comment for the full explanation of what this
# does, why it's best-effort/experimental, and what "total" means. Less exercised than the
# PowerShell version (this kit's owner develops on Windows) — if the numbers look wrong, the fix
# is almost always adjusting the jq filter below to match the real transcript line shape
# (uncomment the debug lines to capture one raw payload and a transcript sample and look for
# yourself). Requires `jq`; exits quietly without it.
#
# Also feeds the Agent Console's "YOU" node: piggybacks on this always-fires-on-every-tool-call
# hook to mark the session active (Claude.md agent-console-session.json, active:true) rather than
# registering a third separate PostToolUse command — any tool call, main session or subagent,
# means Claude is actively doing something right now. The matching "went idle" signal lives in
# agent-console-session-stop.sh on the Stop hook (the one authoritative "idle" moment); this
# script only ever asserts "active" from this side.

set -uo pipefail
command -v jq >/dev/null 2>&1 || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
payload="$(cat)"

# debug_log="$project_dir/Claude/logs/raw-agent-console-tokens-payload.log"
# mkdir -p "$(dirname "$debug_log")"
# echo "$payload" >> "$debug_log"

transcript_path=$(echo "$payload" | jq -r '.transcript_path // empty' 2>/dev/null)
[ -n "$transcript_path" ] && [ -f "$transcript_path" ] || exit 0

log_dir="$project_dir/Claude/logs"
mkdir -p "$log_dir"
state_file="$log_dir/agent-console-tokens-state.json"
out_file="$log_dir/agent-console-tokens.json"

session_file="$log_dir/agent-console-session.json"
jq -nc --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" '{active:true,ts:$ts}' > "$session_file" 2>/dev/null || true

[ -f "$state_file" ] || echo '{"offsets":{},"totals":{"input":0,"output":0,"cache_read":0,"cache_creation":0}}' > "$state_file"

offset=$(jq -r --arg p "$transcript_path" '.offsets[$p] // 0' "$state_file" 2>/dev/null)
case "$offset" in ''|*[!0-9]*) offset=0 ;; esac

file_size=$(wc -c < "$transcript_path" | tr -d ' ')
[ "$file_size" -gt "$offset" ] || exit 0

# New bytes only, and only complete lines — drop a trailing partial line if the file doesn't
# currently end in a newline (it'll be picked up whole on the next call).
new_bytes=$(tail -c +"$((offset + 1))" "$transcript_path")
ends_with_newline=true
[ "$(tail -c 1 "$transcript_path" | wc -l | tr -d ' ')" = "0" ] && ends_with_newline=false
if [ "$ends_with_newline" = false ]; then
  new_bytes=$(printf '%s\n' "$new_bytes" | sed '$d')
fi
[ -n "$new_bytes" ] || exit 0

consumed=$(printf '%s\n' "$new_bytes" | wc -c | tr -d ' ')
new_offset=$((offset + consumed))

deltas=$(printf '%s\n' "$new_bytes" | jq -Rs '
  [splits("\n")] | map(select(length > 0)) | map(
    (try fromjson catch {}) as $obj |
    (($obj.message.usage) // $obj.usage // {}) as $u |
    {
      input: ($u.input_tokens // 0),
      output: ($u.output_tokens // 0),
      cache_read: ($u.cache_read_input_tokens // 0),
      cache_creation: ($u.cache_creation_input_tokens // 0)
    }
  ) | reduce .[] as $d ({input:0,output:0,cache_read:0,cache_creation:0};
    {input: (.input+$d.input), output: (.output+$d.output),
     cache_read: (.cache_read+$d.cache_read), cache_creation: (.cache_creation+$d.cache_creation)})
' 2>/dev/null)
[ -n "$deltas" ] || deltas='{"input":0,"output":0,"cache_read":0,"cache_creation":0}'

tmp_state="$state_file.tmp"
jq --arg p "$transcript_path" --argjson off "$new_offset" --argjson d "$deltas" '
  .offsets[$p] = $off |
  .totals.input += $d.input |
  .totals.output += $d.output |
  .totals.cache_read += $d.cache_read |
  .totals.cache_creation += $d.cache_creation
' "$state_file" > "$tmp_state" 2>/dev/null && mv "$tmp_state" "$state_file"

jq '{input:.totals.input,output:.totals.output,cache_read:.totals.cache_read,cache_creation:.totals.cache_creation,total:(.totals.input+.totals.output+.totals.cache_read+.totals.cache_creation),updated:(now|todate)}' \
  "$state_file" > "$out_file" 2>/dev/null

exit 0
