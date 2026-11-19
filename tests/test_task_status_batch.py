#!/usr/bin/env python3
"""Tests for task_status.py batch mode: multiple updates in one call."""
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "project-template", "Claude", "hooks", "task_status.py")


def make_project(tmp):
    hooks = os.path.join(tmp, "Claude", "hooks")
    os.makedirs(hooks)
    os.makedirs(os.path.join(tmp, "Claude", "docs"))
    os.makedirs(os.path.join(tmp, "Claude", "logs"))
    shutil.copy(SRC, os.path.join(hooks, "task_status.py"))
    with open(os.path.join(hooks, "docs_lint.py"), "w") as f:
        f.write("print('docs format OK')\n")
    # Create a roadmap with 5 test tasks
    rows = "\n".join([
        "| T-900 | Test row 0 | To do | accept | P1 | P0-R2 | feature | test |",
        "| T-901 | Test row 1 | To do | accept | P1 | P0-R2 | feature | test |",
        "| T-902 | Test row 2 | To do | accept | P1 | P0-R2 | feature | test |",
        "| T-903 | Test row 3 | To do | accept | P1 | P0-R2 | feature | test |",
        "| T-904 | Test row 4 | To do | accept | P1 | P0-R2 | feature | test |",
    ])
    with open(os.path.join(tmp, "Claude", "docs", "ROADMAP.md"), "w") as f:
        f.write("| ID | Feature | Status |\n|---|---|---|\n" + rows + "\n")
    return os.path.join(hooks, "task_status.py"), os.path.join(tmp, "Claude", "docs", "ROADMAP.md")


def run(script, *args):
    r = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


def cell(road, tid):
    for line in open(road, encoding="utf8"):
        if line.startswith("| %s |" % tid):
            return line.split("|")[3].strip()
    return None


def test_batch_mode_5_updates():
    """Test batch mode with 5 updates completes in under 5 seconds."""
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)
        batch_file = os.path.join(tmp, "batch.txt")

        # Write 5 updates to batch file
        with open(batch_file, "w") as f:
            f.write("T-900|In progress|started|10|0\n")
            f.write("T-901|In progress|code written|30|0\n")
            f.write("T-902|In progress|test written|60|0\n")
            f.write("T-903|In progress|test passing|80|0\n")
            f.write("T-904|In progress|gate running|90|0\n")

        start = time.time()
        code, out = run(script, "--batch", batch_file)
        elapsed = time.time() - start

        print("Batch mode elapsed: %.2fs" % elapsed)

        assert code == 0, (code, out)
        assert elapsed < 5.0, "Batch mode took %.2fs, expected < 5s" % elapsed
        assert "Applied 5/5 updates" in out, out

        # Verify all updates applied
        assert cell(road, "T-900").startswith("In progress - 10%"), cell(road, "T-900")
        assert cell(road, "T-901").startswith("In progress - 30%"), cell(road, "T-901")
        assert cell(road, "T-902").startswith("In progress - 60%"), cell(road, "T-902")
        assert cell(road, "T-903").startswith("In progress - 80%"), cell(road, "T-903")
        assert cell(road, "T-904").startswith("In progress - 90%"), cell(road, "T-904")

        # Verify log entries
        log_path = os.path.join(tmp, "Claude", "logs", "task-status.log")
        log_lines = open(log_path, encoding="utf8").read().strip().split("\n")
        assert len(log_lines) == 5, "Expected 5 log lines, got %d" % len(log_lines)


def test_batch_mode_mixed_statuses():
    """Test batch mode with mixed valid and invalid lines."""
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)
        batch_file = os.path.join(tmp, "batch.txt")

        # Write mixed updates - 3 valid, 2 invalid
        with open(batch_file, "w") as f:
            f.write("T-900|In progress|started|10|0\n")
            f.write("INVALID|bad format\n")
            f.write("T-901|In progress|code written|30|0\n")
            f.write("T-902|InvalidStatus|note|50|0\n")
            f.write("T-903|In progress|test written|60|0\n")
            f.write("# comment line\n")
            f.write("\n")

        start = time.time()
        code, out = run(script, "--batch", batch_file)
        elapsed = time.time() - start

        print("Mixed batch elapsed: %.2fs" % elapsed)

        assert code == 0, (code, out)
        assert elapsed < 5.0, "Mixed batch took %.2fs, expected < 5s" % elapsed
        assert "Applied 3/4 updates" in out, out
        assert "ERRORS:" in out, out

        # Verify valid ones applied
        assert cell(road, "T-900").startswith("In progress - 10%"), cell(road, "T-900")
        assert cell(road, "T-901").startswith("In progress - 30%"), cell(road, "T-901")
        assert cell(road, "T-903").startswith("In progress - 60%"), cell(road, "T-903")

        # Invalid ones should not affect roadmap
        assert cell(road, "T-902") == "To do", cell(road, "T-902")
        assert cell(road, "T-904") == "To do", cell(road, "T-904")


def test_batch_mode_empty_file():
    """Test batch mode with empty file."""
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)
        batch_file = os.path.join(tmp, "batch.txt")

        with open(batch_file, "w") as f:
            f.write("")

        code, out = run(script, "--batch", batch_file)
        assert code == 0, (code, out)
        assert "no valid updates" in out


def test_batch_mode_nonexistent_file():
    """Test batch mode with nonexistent file."""
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)

        code, out = run(script, "--batch", os.path.join(tmp, "nonexistent.txt"))
        assert code == 2, (code, out)
        assert "not found" in out


def test_batch_mode_done_with_gate():
    """Test batch mode with Done status requiring gate=1."""
    with tempfile.TemporaryDirectory() as tmp:
        script, road = make_project(tmp)
        batch_file = os.path.join(tmp, "batch.txt")

        with open(batch_file, "w") as f:
            f.write("T-900|Done|finished|100|1\n")  # gate=1
            f.write("T-901|Done|no gate|100|0\n")   # gate=0 should fail

        code, out = run(script, "--batch", batch_file)
        assert code == 0, (code, out)
        assert "Applied 1/2 updates" in out, out
        assert "ERRORS:" in out, out
        assert "T-901" in out, out

        assert cell(road, "T-900").startswith("Done"), cell(road, "T-900")
        assert cell(road, "T-901") == "To do", cell(road, "T-901")


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print("ok   %s" % name)
        except Exception as e:
            failed.append(name)
            print("FAIL %s: %s" % (name, e))
    if failed:
        print("\nFAILED: %s" % ", ".join(failed))
        return 1
    print("\nPASS task_status_batch: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())