#!/usr/bin/env python3
"""
Check the DIRECTORS-CUT-RULES.md file exists and has the 4 required rules.
Usage: python tools/check_rules2.py
Exit 0 = ok, non-zero = missing rules.
"""
import sys
from pathlib import Path

RULES_PATH = Path(__file__).parent.parent / "docs" / "DIRECTORS-CUT-RULES.md"

REQUIRED_RULES = [
    "freeze at 20%",
    "two-sprint archive",
    "regret log",
    "reply in minutes",
]


def check_rules(path: Path) -> list:
    if not path.exists():
        return ["missing file"]
    content = path.read_text(encoding="utf-8")
    issues = []
    for rule in REQUIRED_RULES:
        if rule.lower() not in content.lower():
            issues.append(f"missing rule: {rule}")
    return issues


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = RULES_PATH

    if not path.exists():
        print(f"FAIL {path}")
        print(" - missing file")
        return 1

    issues = check_rules(path)
    if issues:
        print(f"FAIL {path}")
        for i in issues:
            print(f" - {i}")
        return 1

    print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())