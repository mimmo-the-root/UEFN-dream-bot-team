#!/usr/bin/env bash
# Claude/hooks/island-code.sh - bash twin of island-code.ps1 (see there).
d="$(cd "$(dirname "$0")" && pwd)"
[ -f "$d/island_code_capture.py" ] || exit 0
for py in python3 python; do command -v "$py" >/dev/null 2>&1 && { "$py" "$d/island_code_capture.py"; exit 0; }; done
exit 0
