#!/usr/bin/env python3
"""migrate_recipe_args.py - brings the argument names of the recipes to the names the 43.00 tools use (asset_path -> assetPath).

  python tool/migrate_recipe_args.py MAP_LATEST_JSON            what would change, and what needs a person
  python tool/migrate_recipe_args.py --fixed FILE.json            takes the worker's measured fixes (recipes-args43-fixed.json) into recipes.json
  python tool/migrate_recipe_args.py MAP_LATEST_JSON --write    adds `args43` and `tool43` to those recipes in recipes.json (the old `args` stay for UEFN before 43.00)

The map must hold argument names ("pn"): made by mcp_map.py of this kit (a map from before it is made again by itself at the next session start).
A recipe that sends a name the tool does not have and that is not a writing-style rename is listed, never guessed; replay it."""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import recipes_status as R  # noqa: E402

RECIPES = os.path.join(ROOT, "user-level-skills", "mcp-tool-contracts", "references", "areas", "recipes.json")


def merge_fixed(rec, fixed):
    """The worker's measured fixes ({recipe key: {tool43, args43, proof}}) go into the recipes whose key (before the #) matches. Returns the count."""
    n = 0
    import toolset_diff as td
    table = td.names_43()
    for k, v in fixed.items():
        for rk in rec:
            base = rk.split("#")[0]
            if rk == k or base == k.split("#")[0] or table.get(base) == v["tool43"] or rec[rk].get("tool43") == v["tool43"]:
                rec[rk]["args43"], rec[rk]["tool43"] = v["args43"], v["tool43"]
                n += 1
    return n


def main():
    if "--fixed" in sys.argv:
        f = sys.argv[sys.argv.index("--fixed") + 1]
        rec = json.load(open(RECIPES, encoding="utf-8"))
        n = merge_fixed(rec, json.load(open(f, encoding="utf-8")))
        json.dump(rec, open(RECIPES, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
        print("recipes.json: %d recipe(s) updated from %s" % (n, f))
        return 0
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    tools = json.load(open(sys.argv[1], encoding="utf-8")).get("tools", {})
    if not any("pn" in e for e in tools.values()):
        print("This map has no argument names yet: map again with the current kit (mcp_map.py --now).")
        return 1
    rec = json.load(open(RECIPES, encoding="utf-8"))
    res = R.arg_check(rec, tools)
    fixed = sum(1 for v in res.values() if v["fix"])
    left = {k: v for k, v in res.items() if v["unknown"]}
    for k, v in sorted(res.items()):
        print("%s: %s%s" % (k, ", ".join("%s -> %s" % kv for kv in v["fix"].items()), ("  NEEDS A PERSON: " + ", ".join(v["unknown"])) if v["unknown"] else ""))
    print("%d recipes with renamed arguments, %d with names that need a person" % (fixed, len(left)))
    if "--write" in sys.argv:
        for k, v in res.items():
            if v["fix"]:   # `args` stays for UEFN before 43.00; `args43` and `tool43` are what 43.00 and later use
                a = rec[k]["args"]
                rec[k]["args43"] = {v["fix"].get(n, n): x for n, x in a.items()}
                rec[k]["tool43"] = v["tool"]
        json.dump(rec, open(RECIPES, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
        print("recipes.json: args43 written for %d recipes" % sum(1 for v in res.values() if v["fix"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
