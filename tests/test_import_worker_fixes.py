"""import_worker_fixes.py lists and imports the fixes a worker made to kit files."""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tool"))
import import_worker_fixes as I
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
with tempfile.TemporaryDirectory() as d:
    base = os.path.join(d, "Claude", "relay", "fixes", "files")
    os.makedirs(os.path.join(base, "Claude", "hooks")); os.makedirs(os.path.join(base, ".claude"))
    real = os.path.join(I.ROOT, "project-template", "Claude", "hooks", "mcp_names.py")
    open(os.path.join(base, "Claude", "hooks", "mcp_names.py"), "w").write(open(real).read() + "\n# changed\n")
    open(os.path.join(base, "Claude", "hooks", "brand_new_hook.py"), "w").write("x = 1\n")
    open(os.path.join(base, ".claude", "settings.json"), "w").write("{}")
    open(os.path.join(base, "notes.txt"), "w").write("n")
    items = {i["rel"]: i["state"] for i in I.scan(d)}
    check("a changed kit file is found", items["Claude/hooks/mcp_names.py"] == "changed")
    check("a new file is found", items["Claude/hooks/brand_new_hook.py"] == "new file")
    check("settings.json and non-kit files are listed but skipped", items[".claude/settings.json"].startswith("skip") and items["notes.txt"].startswith("skip"))
    check("an empty project gives nothing", I.scan(os.path.join(d, "nope")) == [])
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
