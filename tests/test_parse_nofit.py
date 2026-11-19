#!/usr/bin/env python3
"""Tests for tools/parse_nofit.py: a NOFIT result and a normal result."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from parse_nofit import parse_nofit  # noqa: E402

fails = []

r = parse_nofit("NOFIT: too big for context | SPLIT: pkg-a reads docs; pkg-b writes tool")
if not (r["nofit"] and r["reason"] == "too big for context" and r["split"] == ["pkg-a reads docs", "pkg-b writes tool"]):
    fails.append("NOFIT result misparsed: %r" % r)

r = parse_nofit("tools/x.py written\nacceptance: exit 0\nPASS gate: yes\n")
if r["nofit"]:
    fails.append("normal result flagged as NOFIT: %r" % r)

r = parse_nofit("done\nNOFIT: no time\n")
if not (r["nofit"] and r["reason"] == "no time" and r["split"] == []):
    fails.append("NOFIT without SPLIT misparsed: %r" % r)

if fails:
    print("FAIL test_parse_nofit")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("PASS NOFIT parser")
