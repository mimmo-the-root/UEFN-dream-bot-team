#!/bin/bash
# Alternative to after-playtest.ps1 for those with bash/WSL/Git Bash available instead of
# PowerShell (on "pure" Windows without bash, use after-playtest.ps1 - that's the default set
# in .claude/settings.json).
#
# The matcher in .claude/settings.json fires on EVERY call to mcp__unreal-mcp__call_tool
# (the unreal-mcp server uses a single dispatcher for all of its actions, not one tool per
# action). The real filter is here: we read the hook's JSON payload from stdin and proceed
# ONLY if this specific call is actually a play-session/game stop - otherwise we exit
# immediately, doing nothing (so as not to run qa-regression/planner-docs on every single
# MCP call, which would waste tokens).
#
# If this script never fires (or always fires), check the exact shape of the payload:
# uncomment the debug line below to log the raw payload once, look at
# Claude/logs/raw-hook-payloads.log, and adjust the grep pattern accordingly.

set -e
cd "${CLAUDE_PROJECT_DIR:-.}"

STDIN_PAYLOAD="$(cat)"

mkdir -p Claude/logs
# echo "$STDIN_PAYLOAD" >> Claude/logs/raw-hook-payloads.log

if ! echo "$STDIN_PAYLOAD" | grep -qiE 'stopgame|stopsession|stop_session|stop_game'; then
  exit 0
fi

LOG="Claude/logs/auto-postplaytest-$(date +%Y%m%d-%H%M%S).log"

echo "=== qa-regression (started $(date)) ===" >> "$LOG"
claude -p "A test play-session in this project just ended. Analyze logs and project state to find regressions and bugs not yet reported, compared to what's documented as working in Claude/docs/STATUS.md. Add whatever you find to Claude/docs/BUGS.md, under the Newly reported section." --agent qa-regression >> "$LOG" 2>&1 || echo "qa-regression returned an error, check the log." >> "$LOG"

echo "=== planner-docs (started $(date)) ===" >> "$LOG"
claude -p "qa-regression just analyzed the last play-session (see $LOG and Claude/docs/BUGS.md, Newly reported section). Update Claude/docs/STATUS.md with a new entry and reprioritize Claude/docs/BUGS.md." --agent planner-docs >> "$LOG" 2>&1 || echo "planner-docs returned an error, check the log." >> "$LOG"

echo "Automatic post-playtest check complete. Details in $LOG"
