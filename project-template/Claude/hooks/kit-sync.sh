#!/usr/bin/env bash
# Claude/hooks/kit-sync.sh - bash twin of kit-sync.ps1 (see there).
d="$(cd "$(dirname "$0")" && pwd)"
[ -f "$d/kit_sync.py" ] || exit 0
for py in python3 python; do command -v "$py" >/dev/null 2>&1 && { "$py" "$d/kit_sync.py"; exit 0; }; done
exit 0
