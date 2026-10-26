#!/usr/bin/env python3
"""collect_mcp_evidence.py - the UEFN MCP recipes your own work proved join the kit at each release.

Run by publish.ps1 on the maintainer's computer (and by hand: `python tool/collect_mcp_evidence.py [--dry]`).
Reads what your work proved: the evidence store in your profile (~/.claude/mcp-evidence.json, which every UEFN call feeds as it happens, so a project deleted from the disk loses nothing) plus the ledgers still on disk (registered projects, Fab lab folders). It sets to "proven" in the
kit's recipes.json every recipe that worked at least once in real work or in a replay and is not proven there yet. Only the status of a
recipe changes: no arguments, paths or project names are read into the kit. It never lowers a status and never adds a recipe.
Then update-my-profile.cmd gives the new statuses to everybody who updates the kit.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("UEFN_KIT_REPO") or os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(HERE, "..")), "project-template", "Claude", "hooks"))
import recipes_status as RS

RECIPES = os.path.join(REPO, "user-level-skills", "mcp-tool-contracts", "references", "areas", "recipes.json")


def collect(dry=False, recipes_path=None, extra=()):
    path = recipes_path or RECIPES
    if not os.path.isfile(path):
        print("collect_mcp_evidence: no recipes file at %s (nothing to do)" % path)
        return []
    recipes = json.load(open(path, encoding="utf-8"))
    paths = RS.ledger_paths(extra)
    merged = RS.merge(recipes, RS.store_evidence(RS.sync(paths)))   # the profile store (kept when a project is deleted) plus the ledgers still on disk
    try:   # what the owner keeps private on the Skills page (UEFN MCP tab) never goes out
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "project-template", "Claude", "hooks"))
        import skills_lib
        held = set(skills_lib.load_hold()["mcp"])
    except Exception:
        held = set()
    new = sorted(k for k, v in merged.items() if v["status"] == "proven" and recipes[k].get("status") != "proven" and k not in held)
    for k in new:
        recipes[k]["status"] = "proven"
    if new and not dry:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)   # the same layout as the file in the repo, so a release only changes the status lines
    print("collect_mcp_evidence: %d ledger(s) read, %d recipe(s) %s proven" % (len(paths), len(new), "would become" if dry else "became"))
    for k in new[:10]:
        print("  + " + k)
    if len(new) > 10:
        print("  ... and %d more" % (len(new) - 10))
    return new


if __name__ == "__main__":
    collect(dry="--dry" in sys.argv[1:])
