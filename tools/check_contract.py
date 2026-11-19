#!/usr/bin/env python3
"""
Check the release contract page exists and is well-formed.
Usage: python tools/check_contract.py
Exit 0 = ok, non-zero = missing sections.
"""
import sys
from pathlib import Path

CONTRACT_PATH = Path(__file__).parent.parent / "docs" / "RELEASE-CONTRACT.md"

REQUIRED_SECTIONS = ["IN", "OUT", "NEXT", "Verification"]


def check_contract(path: Path) -> list:
    if not path.exists():
        return ["missing file"]
    content = path.read_text(encoding="utf-8")
    issues = []
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in content:
            issues.append(f"missing section: {section}")
    return issues


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = CONTRACT_PATH

    if not path.exists():
        print(f"FAIL {path}")
        print(" - missing file")
        return 1

    issues = check_contract(path)
    if issues:
        print(f"FAIL {path}")
        for i in issues:
            print(f" - {i}")
        return 1

    print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())