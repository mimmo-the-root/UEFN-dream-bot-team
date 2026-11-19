#!/usr/bin/env python3
"""Tests for tools/validate_package.py: one valid file, one invalid file."""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOL = os.path.join(ROOT, "tools", "validate_package.py")
fails = []


def run(content):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    try:
        r = subprocess.run([sys.executable, TOOL, path], capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout + r.stderr
    finally:
        os.unlink(path)


VALID = ("id: pkg-999\ntitle: T\nrisk: low\nneeds_owner: no\nneeds_mcp: no\n"
         "do: something\nreport: max 2 lines\n")

rc, out = run(VALID)
if rc != 0:
    fails.append("valid file rejected: " + out)

rc, out = run(VALID.replace("needs_mcp: no\n", ""))
if rc == 0:
    fails.append("invalid file accepted")
if "MISSING FIELD: needs_mcp" not in out:
    fails.append("missing field not named: " + out)

if fails:
    print("FAIL test_validate_package")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("PASS package validator")
