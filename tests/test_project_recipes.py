"""Maps & products: a recipe finds its Fab product again even when the agent named the product in its own words (hash of the name only is stored)."""
import json, os, sys, tempfile
d = tempfile.mkdtemp(); os.environ["UEFN_SKILLS_DIR"] = os.path.join(d, "skills"); os.environ["HOME"] = d; os.environ["USERPROFILE"] = d
os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(d, "lab")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import skills_lib as S
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
os.makedirs(os.path.join(d, ".claude")); os.makedirs(os.path.join(d, "lab", "root_Fab_Barrier_Material"))
json.dump({os.path.join(d, "root_Fab_Barrier_Material"): {"kind": "fab", "name": "root_Fab_Barrier_Material"}}, open(os.path.join(d, ".claude", "kit-projects.json"), "w"))
S.init_genre("materials")
rec = {"name": "barrier test recipe", "parent": "M_Base", "use": "a barrier", "steps": ["do it"], "params": []}
ok(S.recipe_add("materials", rec, "Barrier Material").get("ok"), "a recipe is saved with the product named in the agent's words")
row = [r for r in S.projects_overview() if r["name"] == "root_Fab_Barrier_Material"][0]
ok(row["kind"] == "fab" and row["recipes"] == 1 and row["pct"] == 100, "the product row counts it (root_ and underscores do not matter)")
ok(len(S.recipes_of("root_Fab_Barrier_Material")) == 1, "the This product tab finds it too")
ok(S.name_keys("root_FAB_rainbow") & S.name_keys("Rainbow"), "root_ and FAB are not part of the name")
print("OK")
