#!/usr/bin/env bash
# Claude/hooks/docs-lint.sh - bash twin of docs-lint.ps1 (see there).
d="$(cd "$(dirname "$0")" && pwd)"
[ -f "$d/docs_lint.py" ] || exit 0
for py in python3 python; do command -v "$py" >/dev/null 2>&1 && { "$py" "$d/docs_lint.py" --post-edit; exit $?; }; done
exit 0
