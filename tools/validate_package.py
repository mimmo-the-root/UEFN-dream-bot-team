#!/usr/bin/env python3
"""Reject a package command file that is missing a field of docs/PACKAGE-TEMPLATE.md.

Usage: python tools/validate_package.py <file>
Prints "MISSING FIELD: <name>" for each absent or empty required field; exits 1 if any.
"""
import sys

REQUIRED = ["id", "title", "risk", "needs_owner", "needs_mcp", "do", "report"]


def parse_fields(text):
    """Return {field: value} for every 'key: value' line (keys lowercased)."""
    fields = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields.setdefault(key.strip().lower(), value.strip())
    return fields


def missing_fields(text):
    """List the required fields that are absent or have an empty value."""
    fields = parse_fields(text)
    return [f for f in REQUIRED if not fields.get(f)]


def main(argv):
    if len(argv) != 2:
        print("usage: python tools/validate_package.py <file>")
        return 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print("FAIL cannot read %s: %s" % (argv[1], e))
        return 2
    missing = missing_fields(text)
    for f in missing:
        print("MISSING FIELD: %s" % f)
    if missing:
        return 1
    print("PASS %s" % argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
