#!/usr/bin/env python3
"""Tests for tools/dc_rows.py (T-028): table file -> ROADMAP rows on stdout, input untouched. Temp files only."""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "dc_rows.py")
TABLE = """# x
| Area | Source file | ID | Feature | Acceptance criteria | Priority | Release |
|---|---|---|---|---|---|---|
| a | s | T-120 | [Later] First | It works | P1 | P0-R12 |
| b | s | T-121 | [Owner][Later] Second | Owner confirms | P3 | P0-R20 |
"""


def run(*args):
    return subprocess.run([sys.executable, TOOL] + list(args), capture_output=True, text=True)


with tempfile.TemporaryDirectory() as tmp:
    p = os.path.join(tmp, "t.md")
    with open(p, "w", newline="\n") as f:
        f.write(TABLE)
    r = run(p)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert lines == [
        "| T-120 | [Later] First | To do - Later | It works | P1 | P0-R12 | feature | Director's Cut T-028 |",
        "| T-121 | [Owner][Later] Second | To do - Later | Owner confirms | P3 | P0-R20 | feature | Director's Cut T-028 |",
    ], lines
    assert all(len(l.strip("|").split("|")) == 8 for l in lines)
    with open(p, encoding="utf-8") as f:
        assert f.read() == TABLE  # input not modified
    bad = os.path.join(tmp, "bad.md")
    with open(bad, "w") as f:
        f.write(TABLE.replace("P0-R12", "R12"))
    r = run(bad)
    assert r.returncode == 2 and "bad release" in r.stderr
    nt = os.path.join(tmp, "none.md")
    with open(nt, "w") as f:
        f.write("no table here\n")
    assert run(nt).returncode == 2
print("dc_rows tests OK")
