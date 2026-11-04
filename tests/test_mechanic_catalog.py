"""mechanic_catalog.py: find, show and check on the shipped catalog."""
import json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import mechanic_catalog as M
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
c = M.cat()
check("the catalog has 200+ mechanics with typed links and costs", len(c) >= 200 and sum(1 for e in c.values() if e.get("r")) > 150 and sum(1 for e in c.values() if e.get("k")) > 150)
check("find by words puts the named mechanic first", M.find(["parry"])[0] == "combat.parry" and "combat.block" in M.find(["parry", "block"]))
check("find can be narrowed by category", all(i.startswith("combat.") for i in M.find([], category="combat")))
card = M.card("combat.parry")
check("a card has ranges, edge cases, bugs and the UEFN line", "parry_active_window_ms" in card and "Edge cases:" in card and "Common bugs:" in card and "UEFN:" in card)
check("a verified UEFN way shows its recipe", "recipe 'currency and shop'" in M.card("economy.shop") and "not verified" not in M.card("economy.shop").split("UEFN:")[1].split("\n")[0])
check("a mechanic UEFN cannot do says so", "no direct way" in M.card("camera.screen_shake"))
r = M.check(["combat.parry", "combat.guard_break", "combat.invincibility_frames", "nope.x"])
check("check names unknown ids, soft conflicts, shared systems and a first slice", "Unknown ids: nope.x" in r and "soft conflicts" in r and "build once" in r and "First slice" in r)
u = json.load(open(os.path.join(ROOT, "project-template", "Claude", "reference", "mechanics-uefn.json")))["mechanics"]
check("every UEFN entry names a mechanic that exists", all(k in c for k in u))
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
