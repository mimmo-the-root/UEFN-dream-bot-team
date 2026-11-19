#!/usr/bin/env python3
"""Acceptance tests for tools/swap_task.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SWAP_SCRIPT = REPO_ROOT / "tools" / "swap_task.py"

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
    """Create a temp project with ROADMAP.md."""
    docs = tmp / "docs"
    docs.mkdir(parents=True)
    (docs / "ROADMAP.md").write_text(
        "# ROADMAP\n\n"
        "| ID | Feature | Status | Acceptance criteria | Priority | Release | Kind | Source |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| T-050 | Task A | In progress | done | P1 | P0-R2 | feature | owner |\n"
        "| T-051 | Task B | To do | wait | P1 | P0-R2 | feature | owner |\n"
        "| T-052 | Task C | To do | wait | P1 | P0-R3 | feature | owner |\n",
        encoding="utf-8",
    )
    plan = tmp / "plan"
    plan.mkdir(parents=True)
    env = dict(__import__("os").environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run(env, args, cwd):
    result = subprocess.run(
        [sys.executable, str(SWAP_SCRIPT)] + args,
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    return result


def main():
    tmp = Path(tempfile.mkdtemp())
    env = make_env(tmp)

    # Test 1: Swap T-050 with T-051, T-050 goes to P0-R3, T-051 leaves
    r = run(env, ["T-050", "T-051", "P0-R3", "--from-release", ""], tmp)
    check("swap_task.py exits 0", r.returncode == 0)

    # Check the roadmap was updated
    roadmap = (tmp / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    row50 = [ln for ln in roadmap.splitlines() if ln.startswith("| T-050")][0]
    row51 = [ln for ln in roadmap.splitlines() if ln.startswith("| T-051")][0]
    check("T-050 release is P0-R3", "P0-R3" in row50)
    check("T-051 release is empty", "|  |" in row51 or "|    |" in row51 or "|  |" in row51.split("|")[6])

    # Test 2: Swap with --from-release
    r = run(env, ["T-051", "T-052", "P0-R2", "--from-release", "P0-R3"], tmp)
    check("swap with --from-release exits 0", r.returncode == 0)

    roadmap = (tmp / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    row51 = [ln for ln in roadmap.splitlines() if ln.startswith("| T-051")][0]
    row52 = [ln for ln in roadmap.splitlines() if ln.startswith("| T-052")][0]
    check("T-051 release is P0-R2", "P0-R2" in row51)
    check("T-052 release is P0-R3", "P0-R3" in row52)

    # Test 3: SWAP-LOG.md created
    swap_log = tmp / "plan" / "SWAP-LOG.md"
    check("SWAP-LOG.md created", swap_log.exists())
    if swap_log.exists():
        log_content = swap_log.read_text(encoding="utf-8")
        check("SWAP-LOG contains swap", "T-050" in log_content)

    print(f"\nPASS test_swap: {PASSED}/{PASSED + FAILED} cases")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())