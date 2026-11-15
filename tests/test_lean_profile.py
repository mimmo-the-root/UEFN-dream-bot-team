"""Lean profile (v1.124.19): short base rules in ~/.claude/CLAUDE.md, full texts in kit-rules, old projects migrated."""
import os, re, subprocess, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S = os.path.join(root, "tool", "install-lean-profile.py"); MEM = os.path.join(root, "user-level-memory")
fails = 0
def ok(c, m):
    global fails; print(("PASS " if c else "FAIL ") + m); fails += 0 if c else 1
d = tempfile.mkdtemp(); f = os.path.join(d, "CLAUDE.md")
old = "# Base rules\r\n\r\n## 1. Project organization\r\nlong text\r\n\r\n## 11. Second brain\r\n**Second brain path**: `D:\\vault` (x)\r\n\r\n## 13. Plan-first\r\n### 13a. gates\r\nlong\r\n\r\n## 20. Mine\r\nmy rule\r\n"
open(f, "w", newline="").write(old)
out = subprocess.run([sys.executable, S, MEM, d], capture_output=True, text=True).stdout
t = open(f, newline="").read()
ok("replaced" in out and any(n.startswith("CLAUDE.md.before-lean-") for n in os.listdir(d)), "old rules replaced, backup written")
ok("KIT:BEGIN base-rules" in t and "## 20. Mine\r\nmy rule" in t and "long text" not in t and "13a. gates" not in t, "own section kept, old base rules gone")
ok("`D:\\vault`" in t and "\r\n" in t and "\n" not in t.replace("\r\n", ""), "second brain path and line endings kept")
ok(len(os.listdir(os.path.join(d, "kit-rules"))) == 13, "13 full rule files installed")
ok("current" in subprocess.run([sys.executable, S, MEM, d], capture_output=True, text=True).stdout and open(f, newline="").read() == t, "second run changes nothing")
core = open(os.path.join(MEM, "CLAUDE.md"), encoding="utf-8").read()
for n in re.findall(r"kit-rules/(\d\d-[\w-]+\.md)", core):
    ok(os.path.isfile(os.path.join(MEM, "rules", n)), "pointer %s exists" % n) if not os.path.isfile(os.path.join(MEM, "rules", n)) else None
tpl = open(os.path.join(root, "project-template", "CLAUDE.md"), encoding="utf-8").read()
missing = [n for n in re.findall(r"Claude/reference/rules/([\w-]+\.md)", tpl) if not os.path.isfile(os.path.join(root, "project-template", "Claude", "reference", "rules", n))]
ok(not missing, "every project rule pointer has its file %s" % missing)
ok(len(core) < 10000 and len(tpl) < 18000, "both CLAUDE.md stay short (%d, %d chars)" % (len(core), len(tpl)))
print("%d FAIL" % fails if fails else "ok lean profile"); sys.exit(1 if fails else 0)
