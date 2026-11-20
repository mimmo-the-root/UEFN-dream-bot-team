#!/usr/bin/env python3
"""Tests for tools/debug_log_rotate.py and the debug.max_lines setting (temp dirs only)."""
import os, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kit_config as kc  # noqa: E402
import debug_log_rotate as dr  # noqa: E402

fails = []


def check(c, m):
    if not c:
        fails.append(m)


with tempfile.TemporaryDirectory() as d:
    check(kc.get("debug.max_lines", d) == 2000, "default max_lines 2000")
    kc.set("debug.max_lines", 5, d)
    check(kc.get("debug.max_lines", d) == 5, "setting is saved")
    lg = os.path.join(d, "Claude", "logs", "task-status.log")
    os.makedirs(os.path.dirname(lg))
    with open(lg, "w", newline="\n") as f:
        f.write("".join("line %d\n" % i for i in range(12)))
    pl = os.path.join(d, "Claude", "plan", "PENDING-TESTS.md")
    os.makedirs(os.path.dirname(pl))
    with open(pl, "w", newline="\n") as f:
        f.write("# Pending\nheader\n\n" + "".join("row %d\n" % i for i in range(8)))
    res = dr.rotate(d, today="2026-01-02")
    check(len(res) == 2, "two files rotated: %s" % res)
    got = open(lg).read().split("\n")[:-1]
    check(got == ["line %d" % i for i in range(7, 12)], "log keeps last 5 lines")
    arc = open(os.path.join(d, "Claude", "logs", "archive", "task-status.log-2026-01-02.txt")).read()
    check("7 older lines" in arc and "line 0" in arc and "line 6" in arc, "archive summary and lines")
    pt = open(pl).read().split("\n")
    check(pt[:3] == ["# Pending", "header", ""] and pt[3:8] == ["row %d" % i for i in range(3, 8)], "md header kept")
    check(dr.rotate(d, today="2026-01-02") == [], "second run is a no-op")
    kc.set("debug.max_lines", 0, d)
    check(kc.load(d)[0]["debug"]["max_lines"] == 2000 and kc.validate(kc.load(d)[0]) == [], "bad value falls back")

if fails:
    print("FAIL:\n" + "\n".join(fails))
    sys.exit(1)
print("OK test_debug_log_rotate")
