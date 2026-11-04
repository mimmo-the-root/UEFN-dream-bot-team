"""build_names_43.py translates old tool keys into the 43.00 map keys and reports what it cannot."""
import os, sys, json
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "tool"))
import build_names_43 as B
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
new = {"EditorToolset/GetCurrentLevel": {}, "VerseToolset/Delete": {}, "EditorToolset/Delete": {}, "VerseToolset/BuildAll": {}}
known = {"editor_toolset.toolsets.scene.SceneTools/get_current_level": {}, "ValkyrieToolset.VerseToolset/Delete": {}, "ValkyrieToolset.VerseToolset/BuildAll": {}, "X.Y/old_gone": {}}
r = B.build(known, new)
check("snake_case old name maps to the CamelCase new name", r["names"].get("editor_toolset.toolsets.scene.SceneTools/get_current_level") == "EditorToolset/GetCurrentLevel")
check("a shared name is resolved by the most specific toolset part", r["names"].get("ValkyrieToolset.VerseToolset/Delete") == "VerseToolset/Delete")
check("a tool with no match is listed as gone", r["gone"] == ["X.Y/old_gone"])
p = os.path.join(ROOT, "project-template", "Claude", "hooks", "mcp-names-43.json")
d = json.load(open(p, encoding="utf-8"))
check("the shipped table translates almost every known tool", d["count"] >= 370 and len(d["gone"]) <= 12 and not d["ambiguous"])
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
