"""All console pages open in a real browser without errors (needs Playwright; skipped without it)."""
import os, subprocess, sys
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
try:
    import playwright  # noqa: F401
except ImportError:
    print("SKIP console_live (Playwright is not installed)")
    sys.exit(0)
r = subprocess.run([sys.executable, os.path.join(root, "tool", "shoot_consoles.py"), "--check-only"], capture_output=True, text=True)
print(r.stdout.strip())
print("PASS console pages open without errors" if r.returncode == 0 else "FAIL console pages")
sys.exit(r.returncode)
