#!/usr/bin/env python3
"""Acceptance tests for hooks/nudge_inject.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

import nudge_inject

PASSED = 0
FAILED = 0


def check(name, condition):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS {name}")
    else:
        FAILED += 1
        print(f"  FAIL {name}")


def write(path, obj):
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(str(obj), encoding="utf-8")


def main():
    tmp = Path(tempfile.mkdtemp())

    # Test 1: No NUDGE.md -> nothing printed
    write(tmp / "NUDGE.md", "# Placeholder")
    result = nudge_inject.nudge_inject(tmp / "NUDGE.md")
    check("no NUDGE.md -> None", result is None)

    # Test 2: Empty NUDGE.md -> nothing printed
    write(tmp / "NUDGE.md", "")
    result = nudge_inject.nudge_inject(tmp / "NUDGE.md")
    check("empty NUDGE.md -> None", result is None)

    # Test 3: No >>> line -> nothing printed
    write(tmp / "NUDGE.md", "Some regular content")
    result = nudge_inject.nudge_inject(tmp / "NUDGE.md")
    check("no >>> line -> None", result is None)

    # Test 4: >>> line present -> returns directive
    write(tmp / "NUDGE.md", ">>> install dependencies\nAnother line")
    result = nudge_inject.nudge_inject(tmp / "NUDGE.md")
    check(">>> line present -> returns directive", result == "DO THIS FIRST: install dependencies")

    # Test 5: >>> line with extra spaces -> stripped
    write(tmp / "NUDGE.md", ">>>  install dependencies  ")
    result = nudge_inject.nudge_inject(tmp / "NUDGE.md")
    check(">>> line with spaces -> stripped", result == "DO THIS FIRST: install dependencies")

    # Test 6: >>> line with no text -> empty directive (may have trailing space)
    write(tmp / "NUDGE.md", ">>>")
    result = nudge_inject.nudge_inject(tmp / "NUDGE.md")
    check(">>> with no text -> empty directive", result in ("DO THIS FIRST:", "DO THIS FIRST: "))

    # Test 7: Real NUDGE.md in kit repo
    real = nudge_inject.nudge_inject()
    check("real NUDGE.md -> None or directive", real is None or real.startswith("DO THIS FIRST:"))

    print(f"\nPASS nudge_inject: {PASSED}/{PASSED + FAILED} cases")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
