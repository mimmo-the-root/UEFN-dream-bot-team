#!/bin/bash
# Claude/hooks/skill-consult.sh — bash/macOS/Linux equivalent of skill-consult.ps1 (see that file).
# Needs only python3 (no jq); exits quietly without it. Never blocks or fails a tool call.
command -v python3 >/dev/null 2>&1 || exit 0
lib="${CLAUDE_PROJECT_DIR:-$(pwd)}/Claude/hooks/skills_lib.py"
[ -f "$lib" ] || exit 0
python3 "$lib" consult-hook >/dev/null 2>&1
exit 0
