"""import_mechanics_dataset.py builds valid reference lessons from a mechanics dataset, one genre per lesson, without engine jargon."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tool"))
import import_mechanics_dataset as I
import skills_lib as S
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
def mech(id_, name, cat, genres, bugs=(), edge=(), bal=(), acc=(), core="core"):
    return {"id": id_, "name": name, "category": cat, "genres": list(genres), "common_bugs": list(bugs), "edge_cases": list(edge), "balancing_notes": list(bal),
            "accessibility_notes": list(acc), "scope_profile": {"mvp_role": core}}
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "data", "combat"))
    os.makedirs(os.path.join(d, "data", "ui_ux"))
    def w(sub, m): json.dump(m, open(os.path.join(d, "data", sub, m["id"].split(".")[1] + ".json"), "w"))
    w("combat", mech("combat.parry", "Parry", "combat", ["shooter"], bugs=["The parry window is checked after damage is applied, so the hit still lands on the player.",
        "The shield animation uses a Unity Animator state that never resets after an interrupted block, which is engine talk.", "Parry flag stays on after the round ends and the next round starts guarded."]))
    w("ui_ux", mech("ui_ux.menu", "Menu", "ui_ux", [], acc=["Every menu action can be reached with the same buttons a player uses in game, without a mouse."], core="optional"))
    r = I.build(d, 10, ours=["shooter", "survival"])
    sh = r["shooter"]
    check("a good bug and an accessibility note are kept, each in one genre only", any("parry window" in p["action"] for p in sh) and sum(1 for g in r.values() for p in g if "without a mouse" in p["action"]) == 1)
    check("engine talk is dropped", not any("Animator" in p["action"] for p in sh))
    check("every lesson passes the kit's own pattern gate", all(not S.validate_pattern(p) and p["tier"] == "reference" for p in sh))
    check("a genre that no mechanic names gets only accessibility lessons", all(p["section"] == "launch-checklist" for p in r["survival"]))
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
