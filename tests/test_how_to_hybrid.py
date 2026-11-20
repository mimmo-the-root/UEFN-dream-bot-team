"""docs/HOW-TO-HYBRID.md: exists, short, names the 3 modes. Read-only."""
import os, sys
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
p = os.path.join(root, "docs", "HOW-TO-HYBRID.md")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
ok(os.path.isfile(p), "HOW-TO-HYBRID.md exists")
data = open(p, "rb").read()
ok(len(data) < 6000, "under 6000 bytes (%d)" % len(data))
t = data.decode("utf-8").lower()
ok(all(w in t for w in ("free", "paid", "mixed")), "mentions Free, Paid and Mixed")
ok(b"\r" not in data, "LF endings")
