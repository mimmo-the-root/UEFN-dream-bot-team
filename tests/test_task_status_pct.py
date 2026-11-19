#!/usr/bin/env python3
"""Tests for task_status.py progress rule (T-101): In progress needs --pct, Done keeps needing --gate-pass."""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "project-template", "Claude", "hooks", "task_status.py")
ROW = "| T-900 | Test row | To do | accept | P1 | P0-R2 | feature | test |"


def make_project(tmp):
    hooks = os.path.join(tmp, "Claude", "hooks")
    os.makedirs(hooks)
    os.makedirs(os.path.join(tmp, "Claude", "docs"))
    shutil.copy(SRC, os.path.join(hooks, "task_status.py"))
    with open(os.path.join(hooks, "docs_lint.py"), "w") as f:  # stub: the real lint is not under test here
        f.write("print('docs format OK')\n")
    with open(os.path.join(tmp, "Claude", "docs", "ROADMAP.md"), "w") as f:
        f.write("| ID | Feature | Status |\n|---|---|---|\n" + ROW + "\n")
    return os.path.join(hooks, "task_status.py"), os.path.join(tmp, "Claude", "docs", "ROADMAP.md")


def run(script, *args):
    r = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


def cell(road):
    for line in open(road, encoding="utf8"):
        if line.startswith("| T-900 |"):
            return line.split("|")[3].strip()
    return None


def test_in_progress_without_pct_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)
        code, out = run(script, "T-900", "In progress", "starting")
        assert code == 2, (code, out)
        assert "--pct" in out and "Milestones" in out
        assert cell(road) == "To do", cell(road)


def test_in_progress_with_pct_is_accepted():
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)
        code, out = run(script, "T-900", "In progress", "code written", "--pct", "30")
        assert code == 0, (code, out)
        assert cell(road).startswith("In progress - 30%"), cell(road)


def test_done_and_blocked_unchanged():
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)
        assert run(script, "T-900", "Done")[0] == 2
        assert run(script, "T-900", "Blocked", "waiting")[0] == 0
        assert cell(road).startswith("Blocked")
        assert run(script, "T-900", "Done", "ok", "--gate-pass")[0] == 0
        assert cell(road).startswith("Done")


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print("ok   %s" % name)
        except Exception as e:  # noqa: BLE001
            failed.append(name)
            print("FAIL %s: %s" % (name, e))
    if failed:
        print("\nFAILED: %s" % ", ".join(failed))
        return 1
    print("\nPASS task_status_pct: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
