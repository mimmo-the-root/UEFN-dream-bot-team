import os, sys, json, tempfile, shutil
root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
tmp = tempfile.mkdtemp()
try:
    os.environ["UEFN_SKILLS_DIR"] = os.path.join(tmp, "skills")
    shutil.copytree(os.path.join(root, "user-level-skills", "genre", "materials"), os.path.join(tmp, "skills", "genre", "materials"))
    import skills_lib as L
    proj = os.path.join(tmp, "p", "Materials"); os.makedirs(proj)
    for n in ("M_A.uasset", "MI_A1.uasset", "MI_A2.uasset", "T_x.uasset"):
        open(os.path.join(proj, n), "w").close()
    t = L.detect_techniques(os.path.join(tmp, "p"))
    assert [x["slug"] for x in t["techniques"]] == ["materials"], t
    inv = L.materials_inventory(os.path.join(tmp, "p"))
    assert inv["totals"]["instance"] == 2 and inv["totals"]["parent"] == 1
    empty = os.path.join(tmp, "e"); os.makedirs(empty)
    assert L.detect_techniques(empty)["techniques"] == []
    pack = json.load(open(os.path.join(root, "user-level-skills", "genre", "materials", "official", "official-epic-materials.json"), encoding="utf-8"))
    for p in pack["patterns"]:
        assert p["id"] == L.pattern_id(p["variant"], p["condition"], p["action"]) and p["tier"] == "reference"
    r = L.merge_pack("materials", pack, "official-epic-materials", official=True)
    assert r["ok"] and r["new"] == len(pack["patterns"]), r
    print("materials skill tests OK")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# recipes
import tempfile as _t, shutil as _s
_tmp = _t.mkdtemp()
try:
    os.environ["UEFN_SKILLS_DIR"] = os.path.join(_tmp, "skills")
    _g = os.path.join(_tmp, "skills", "genre")
    _s.copytree(os.path.join(root, "user-level-skills", "genre", "materials"), os.path.join(_g, "materials"))
    import importlib, skills_lib as L2
    r = L2.recipes_list("materials", "ui")
    assert r["recipes"] and r["recipes"][0]["name"] == "ui-flat-shape"
    rec = {"name": "Glow Button", "parent": "M_UI_Shape_Rectangle", "steps": ["a", "b"], "use": "button"}
    assert L2.recipe_add("materials", rec, "Map A")["maps"] == 1
    assert L2.recipe_add("materials", rec, "map a")["maps"] == 1, "same map counts once"
    assert L2.recipe_add("materials", rec, "Map B")["maps"] == 2
    t = [x for x in L2.recipes_list("materials", "glow")["recipes"]][0]["tier"]
    assert t == "confirmed"
    assert not L2.recipe_add("materials", {"name": "x"}, "m")["ok"]
    print("recipes tests OK")
finally:
    _s.rmtree(_tmp, ignore_errors=True)

_tmp = _t.mkdtemp()
try:
    os.environ["UEFN_SKILLS_DIR"] = os.path.join(_tmp, "skills")
    import skills_lib as L3
    assert L3.needs_feeding("roguelike")["needs"] is True
    L3.init("roguelike") if hasattr(L3, "init") else None
    r = L3.needs_feeding("roguelike")
    assert r["needs"] is True and r["owner_backed"] == 0
    print("needs-feeding test OK")
finally:
    _s.rmtree(_tmp, ignore_errors=True)
