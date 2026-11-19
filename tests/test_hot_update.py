#!/usr/bin/env python3
"""Acceptance tests for hooks/hot_update.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HOOK = REPO_ROOT / "hooks" / "hot_update.py"

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
    """Create a temp project with hooks and docs skeleton."""
    import shutil
    hooks_src = REPO_ROOT / "project-template" / "Claude" / "hooks"
    hooks_dir = tmp / "Claude" / "hooks"
    shutil.copytree(hooks_src, hooks_dir)
    # Copy hot_update.py specifically
    shutil.copy(REPO_ROOT / "hooks" / "hot_update.py", hooks_dir / "hot_update.py")
    docs = tmp / "Claude" / "docs"
    docs.mkdir(parents=True)
    (docs / "ROADMAP.md").write_text(
        "# ROADMAP\n\n"
        "| T-050 | Task One | To do | P1 | - |\n"
        "| T-051 | Task Two | In progress | P1 | - |\n",
        encoding="utf-8",
    )
    plan = tmp / "Claude" / "plan"
    plan.mkdir(parents=True)
    (plan / "NUDGE.md").write_text(
        "# NUDGE — 2026-11-19\n\n"
        "Release: ibrido-0\n\n"
        "DECISION: hot_update.py writes HOT.md after each task change.\n",
        encoding="utf-8",
    )
    logs = tmp / "Claude" / "logs"
    logs.mkdir(parents=True)
    env = dict(__import__("os").environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return hooks_dir, env


def run(hooks_dir, env, args, cwd):
    # Run the hook in the temp directory so it can find the plan/ directory
    result = subprocess.run(
        [sys.executable, str(hooks_dir / "hot_update.py")] + args,
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    return result


def main():
    tmp = Path(tempfile.mkdtemp())
    hooks_dir, env = make_env(tmp)

    # Test 1: hot_update.py exits 0
    r = run(hooks_dir, env, [], tmp)
    check("hot_update.py exits 0", r.returncode == 0)

    # Test 2: HOT.md is created
    hot_file = tmp / "Claude" / "plan" / "HOT.md"
    if not hot_file.exists():
        check("HOT.md is created", False)
    else:
        check("HOT.md exists", True)

    # Test 3: HOT.md contains the current release
    if hot_file.exists():
        content = hot_file.read_text(encoding="utf-8", errors="replace")
        check("HOT.md contains release name", "ibrido-0" in content)

    # Test 4: HOT.md has tasks section
    if hot_file.exists():
        content = hot_file.read_text(encoding="utf-8", errors="replace")
        check("HOT.md has tasks section", "Tasks in flight:" in content)

    # Test 5: HOT.md contains last decision
    if hot_file.exists():
        content = hot_file.read_text(encoding="utf-8", errors="replace")
        check("HOT.md contains last decision", "hot_update.py writes HOT.md" in content)

    # Test 6: hot_update.py survives a session restart (just call it again)
    r = run(hooks_dir, env, [], tmp)
    check("hot_update.py can be called twice", r.returncode == 0)

    print(f"\nPASS test_hot_update: {PASSED}/{PASSED + FAILED} cases")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())