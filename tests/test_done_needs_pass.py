#!/usr/bin/env python3
"""
Acceptance tests for the gate-pass requirement of task_status.py.
Done must be refused without --gate-pass, and the gate file must contain FINAL: PASS.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HOOK = REPO_ROOT / "project-template" / "Claude" / "hooks" / "task_status.py"

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


def make_env(tmp):
    """Copy the hooks + docs skeleton into a temp project and return (hooks_dir, env)."""
    hooks_src = REPO_ROOT / "project-template" / "Claude" / "hooks"
    hooks_dir = tmp / "Claude" / "hooks"
    shutil.copytree(hooks_src, hooks_dir)
    docs = tmp / "Claude" / "docs"
    docs.mkdir(parents=True)
    (docs / "ROADMAP.md").write_text(
        "# ROADMAP\n\n"
        "| T-050 | Task One | To do | P1 | - |\n"
        "| T-051 | Task Two | To do | P1 | - |\n",
        encoding="utf-8",
    )
    logs = tmp / "Claude" / "logs"
    logs.mkdir(parents=True)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return hooks_dir, env


def run(hooks_dir, env, args):
    result = subprocess.run(
        [sys.executable, str(hooks_dir / "task_status.py")] + args,
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def main():
    tmp = Path(tempfile.mkdtemp())
    hooks_dir, env = make_env(tmp)

    # Test 1: Done without --gate-pass is refused
    r = run(hooks_dir, env, ["T-050", "Done", "work finished"])
    check("Done without --gate-pass is refused", r.returncode != 0)
    check("Done refusal mentions gate-pass", "gate-pass" in (r.stdout + r.stderr).lower())

    # Test 2: In progress without --pct is refused
    r = run(hooks_dir, env, ["T-051", "In progress", "working"])
    check("In progress without --pct is refused", r.returncode != 0)

    # Test 3: In progress with --pct works
    r = run(hooks_dir, env, ["T-051", "In progress", "working", "--pct", "40"])
    check("In progress with --pct works", r.returncode == 0)

    # Test 4: Done with --gate-pass works
    r = run(hooks_dir, env, ["T-050", "Done", "work finished", "--gate-pass"])
    check("Done with --gate-pass works", r.returncode == 0)

    # Test 5: the row was rewritten with Done
    roadmap = (tmp / "Claude" / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    row = [ln for ln in roadmap.splitlines() if ln.startswith("| T-050")][0]
    check("T-050 row is Done", "Done" in row)

    # Test 7: Done with --gate-pass does NOT require a gate file (it's just a flag)
    r = run(hooks_dir, env, ["T-050", "Done", "work finished", "--gate-pass"])
    check("Done with --gate-pass works (no gate file needed)", r.returncode == 0)

    # Test 8: the gate file was not created (it's a flag, not a file)
    gate_files = list(tmp.rglob(".gate*")) + list(tmp.rglob("gate*"))
    check("no gate file created (just a flag)", len(gate_files) == 0)

    print(f"\nPASS test_done_needs_pass: {PASSED}/{PASSED + FAILED} cases")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
