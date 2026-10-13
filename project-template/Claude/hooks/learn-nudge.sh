#!/usr/bin/env bash
# Claude/hooks/learn-nudge.sh - Stop: see learn-nudge.ps1.
dir="$(cd "$(dirname "$0")" && pwd)"
[ -f "$dir/learn_nudge.py" ] || exit 0
for py in python3 python; do
  command -v "$py" >/dev/null 2>&1 && { "$py" "$dir/learn_nudge.py"; exit 0; }
done
exit 0
