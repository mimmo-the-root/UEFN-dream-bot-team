#!/usr/bin/env python3
"""
Check RULES-10-LINES.md for the 6 required rules and line count.
Usage: python tools/check_rules.py
Exit 0 = ok, non-zero = missing fields.
"""
import re
import sys
from pathlib import Path

REQUIRED_RULES = [
    "one-line decisions",
    "branch per task",
    "free only",
    "parallel rule",
    "done only with pass",
    "work alone",
]

RULES_PATH = Path(__file__).parent.parent / "docs" / "RULES-10-LINES.md"


def check_rules_file(path: Path) -> tuple[int, list[str]]:
    """Return (line_count, missing_rules) for the rules file."""
    content = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    line_count = len(lines)
    missing = []

    for rule in REQUIRED_RULES:
        # Check if the rule text appears in any line
        if not any(rule.lower() in line.lower() for line in lines):
            missing.append(rule)

    return line_count, missing


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = RULES_PATH

    if not path.exists():
        print(f"file not found: {path}")
        return 2

    line_count, missing = check_rules_file(path)

    if line_count > 10:
        print(f"FAIL {path}")
        print(f" - line count {line_count} exceeds 10")
        return 1

    if missing:
        print(f"FAIL {path}")
        for rule in missing:
            print(f" - missing rule: {rule}")
        return 1

    print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
