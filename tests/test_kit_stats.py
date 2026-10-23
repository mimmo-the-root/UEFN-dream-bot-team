"""The README badges read docs/kit-stats.json: it must match the repo (run tool/build_kit_stats.py if not)."""
import os, subprocess, sys
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
r = subprocess.run([sys.executable, os.path.join(root, "tool", "build_kit_stats.py"), "--check"], capture_output=True, text=True)
print(("PASS " if r.returncode == 0 else "FAIL ") + "docs/kit-stats.json matches the repo: " + r.stdout.strip())
sys.exit(r.returncode)
