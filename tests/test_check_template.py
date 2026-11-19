#!/usr/bin/env python3
"""Unit tests for tools/check_template.py (work-package template validator)."""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOL = os.path.join(ROOT, "tools", "check_template.py")

fails = []


def run(content):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    try:
        r = subprocess.run([sys.executable, TOOL, path], capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout, r.stderr
    finally:
        os.unlink(path)


VALID = (
    "id: pkg-999\n"
    "title: Test package\n"
    "risk: low\n"
    "needs_owner: no\n"
    "needs_mcp: no\n"
    "do: do something useful\n"
    "report: max 2 lines\n"
    "approved: yes\n"
    "parallel: yes\n"
    "after: \n"
    "agent: general-purpose\n"
)

rc, out, err = run(VALID)
if rc != 0:
    fails.append("valid template rejected (rc=%d): %s" % (rc, out + err))

# Missing required field
rc, out, err = run("id: pkg-001\ntitle: T\nrisk: low\n")
if rc == 0:
    fails.append("missing required fields accepted")

# Invalid enum value
rc, out, err = run(
    "id: pkg-001\ntitle: T\nrisk: very-high\nneeds_owner: no\nneeds_mcp: no\ndo: x\nreport: y\n"
)
if rc == 0:
    fails.append("invalid risk enum accepted")

# Out-of-order required fields
rc, out, err = run(
    "title: T\nid: pkg-001\nrisk: low\nneeds_owner: no\nneeds_mcp: no\ndo: x\nreport: y\n"
)
if rc == 0:
    fails.append("out-of-order fields accepted")

if fails:
    print("FAIL test_check_template")
    for f in fails:
        print(" -", f)
    sys.exit(1)

print("PASS work-package template validator")
