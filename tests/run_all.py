#!/usr/bin/env python3
"""Run every tests/test_*.py, then the repo checks. Prints one line per step; details only on failure."""
import glob, os, subprocess, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
steps = [(os.path.basename(f), [sys.executable, f]) for f in sorted(glob.glob(os.path.join(root, "tests", "test_*.py")))]
steps += [("privacy_scan", [sys.executable, os.path.join(root, "tool", "privacy_scan.py")]),
          ("validate_skills", [sys.executable, os.path.join(root, "tool", "validate_skills.py")]),
          ("token_budget", [sys.executable, os.path.join(root, "tool", "token_budget.py")])]
bad = 0
for name, cmd in steps:
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    ok = r.returncode == 0
    print(("ok    " if ok else "FAIL  ") + name)
    if not ok:
        bad += 1
        print("\n".join((r.stdout + r.stderr).strip().splitlines()[-25:]))
print("%d/%d steps passed" % (len(steps) - bad, len(steps)))
sys.exit(1 if bad else 0)
