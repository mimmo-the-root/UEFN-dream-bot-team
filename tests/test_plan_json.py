#!/usr/bin/env python3
"""Tests for tools/plan_json.py on a temp roadmap copy (never the real one)."""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOL = os.path.join(ROOT, "tools", "plan_json.py")
HEAD = "| ID | Feature | Status | Acceptance criteria | Priority | Release | Kind | Source |\r\n|---|---|---|---|---|---|---|---|\r\n"
GOOD = (HEAD
        + "| T-001 | [R1] a | Done - x | acc one | P1 | R1 | feature | o |\r\n"
        + "| T-002 | [R1] b | To do | run `python3 tests/test_x.py` and pass | P1 | R1 | feature | o |\r\n"
        + "| T-003 | [R1] c | In progress - 50% | plain acceptance | P2 | R1 | feature | o |\r\n")
BAD = GOOD + "| T-004 | [R1] d | To do |  | P2 | R1 | feature | o |\r\n"

fails = []


def run(*args):
    return subprocess.run([sys.executable, TOOL] + list(args), capture_output=True, text=True)


with tempfile.TemporaryDirectory() as d:
    road = os.path.join(d, "ROADMAP.md")
    out = os.path.join(d, "plan.json")
    with open(road, "w", newline="") as f:
        f.write(GOOD)
    r = run("build", "--roadmap", road, "--out", out)
    if r.returncode != 0:
        fails.append("build failed: " + r.stdout + r.stderr)
    else:
        plan = json.load(open(out, encoding="utf-8"))
        ids = [i["id"] for i in plan["items"]]
        if ids != ["T-002", "T-003"]:
            fails.append("open ids wrong: %r" % ids)
        elif plan["items"][0]["command"] != "python3 tests/test_x.py" or plan["items"][1]["command"] != "plain acceptance":
            fails.append("commands wrong: %r" % plan["items"])
    if run("check", "--roadmap", road).returncode != 0:
        fails.append("check should pass on good roadmap")
    with open(road, "w", newline="") as f:
        f.write(BAD)
    r = run("check", "--roadmap", road)
    if r.returncode == 0 or "T-004" not in r.stdout:
        fails.append("check should fail on empty acceptance: " + r.stdout)

if fails:
    print("FAIL test_plan_json")
    print("\n".join(fails))
    sys.exit(1)
print("ok test_plan_json")
