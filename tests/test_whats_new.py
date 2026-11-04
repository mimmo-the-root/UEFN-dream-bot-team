"""After an update the kit says what changed in numbers (Got N features, N fixes and N other changes), from CHANGELOG.md."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "tool"))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import build_whats_new as B, kit_sync as K
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
log = "# Changelog\n\n## v2.0.0 — Two\n\n- **A new thing.** It adds a page.\n- **Broken button fixed.** It works again.\n- [other] **Tidy.** Renamed a folder.\n- [fix] **Tagged.** Anything.\n\n## v1.9.0 — One\n\n- **Plain.** Moved some text.\n"
d = B.build(log)["versions"]
check("bullets are counted by kind (words or explicit tag)", d["2.0.0"]["features"] == 1 and d["2.0.0"]["fixes"] == 2 and d["2.0.0"]["other"] == 1 and d["1.9.0"]["other"] == 1)
check("headlines are the bold lead of each bullet", d["2.0.0"]["headlines"][0] == "A new thing")
check("the shipped file is up to date with CHANGELOG.md", subprocess.run([sys.executable, os.path.join(ROOT, "tool", "build_whats_new.py"), "--check"]).returncode == 0)
with tempfile.TemporaryDirectory() as p:
    os.makedirs(os.path.join(p, "Claude", "reference"))
    json.dump({"versions": d}, open(os.path.join(p, "Claude", "reference", "whats-new.json"), "w"))
    t = K.whats_new(p, "1.9.0", "2.0.0")
    check("one version: its own counts", t.startswith("Got 1 feature, 2 fixes and 1 other change.") and "A new thing" in t)
    t = K.whats_new(p, "1.0.0", "2.0.0")
    check("several versions are added up", t.startswith("Got 1 feature, 2 fixes and 2 other changes.") and "(2 versions)" in t)
    check("nothing newer than the old version: empty", K.whats_new(p, "2.0.0", "2.0.0") == "")
    check("missing file: empty, never an error", K.whats_new(os.path.join(p, "x"), "1.0.0", "2.0.0") == "")
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
