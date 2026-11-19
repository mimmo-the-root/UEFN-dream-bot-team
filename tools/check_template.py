#!/usr/bin/env python3
"""Validate a work-package command template against the contract in docs/PACKAGE-TEMPLATE.md.

Usage: python tools/check_template.py <file>

Exits 0 when the file lists exactly the 7 required fields (in order) with valid values,
and all optional fields present are well-formed. Prints failures and exits non-zero otherwise.
"""
import sys

REQUIRED = ["id", "title", "risk", "needs_owner", "needs_mcp", "do", "report"]
FIELD_VALUES = {
    "risk": {"low", "medium", "high"},
    "needs_owner": {"yes", "no"},
    "needs_mcp": {"yes", "no"},
}


def read_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.readlines()
    except OSError as e:
        print("FAIL cannot read %s: %s" % (path, e))
        return None


def check(path):
    lines = read_lines(path)
    if lines is None:
        return False

    seen = {}
    order = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key in seen:
            print("FAIL duplicate field: %s" % key)
            return False
        seen[key] = value
        order.append(key)

    fails = []
    # All 7 required fields must be present.
    for field in REQUIRED:
        if field not in seen:
            fails.append("missing required field: %s" % field)

    # Required fields must appear in the correct relative order.
    required_positions = [i for i, k in enumerate(order) if k in REQUIRED]
    expected_order = [k for k in REQUIRED if k in seen]
    if [order[i] for i in required_positions] != expected_order:
        fails.append("required fields out of order (expected: %s)" % ", ".join(REQUIRED))

    # Optional fields, when present, must be well-formed.
    for key, value in seen.items():
        if key in FIELD_VALUES and value not in FIELD_VALUES[key]:
            fails.append("invalid value for %s: %r (expected one of %s)"
                         % (key, value, ", ".join(sorted(FIELD_VALUES[key]))))

    if fails:
        print("FAIL %s" % path)
        for f in fails:
            print(" - %s" % f)
        return False

    print("PASS %s" % path)
    return True


def main(argv):
    if len(argv) != 2:
        print("usage: python tools/check_template.py <file>")
        return 1
    ok = check(argv[1])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))