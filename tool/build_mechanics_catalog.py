#!/usr/bin/env python3
"""build_mechanics_catalog.py - builds project-template/Claude/reference/mechanics-catalog.json from an open game-mechanics dataset (CC0 data).

  python tool/build_mechanics_catalog.py DATASET_DIR

One compact entry per mechanic: name, category, genres, one line of purpose, required systems, parameters with their typical range, the first few edge cases,
common bugs, balance and accessibility notes, typed relationships and the cost profile. Generic engine notes are left out. The UEFN column is NOT here:
it lives in reference/mechanics-uefn.json (made by hand and by the worker, from real devices and recipes)."""
import glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "project-template", "Claude", "reference", "mechanics-catalog.json")


def short(s, n):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def entry(m):
    e = {"n": m["name"], "al": m.get("aliases", [])[:4], "c": m["category"], "g": m.get("genres", []), "d": short(m.get("description", ""), 190),
         "s": m.get("required_systems", [])[:8],
         "p": ["%s: %s" % (p["name"], p.get("typical_range", "")) for p in m.get("parameters", [])[:6]],
         "e": [short(x, 170) for x in m.get("edge_cases", [])[:3]], "b": [short(x, 170) for x in m.get("common_bugs", [])[:3]],
         "t": [short(x, 170) for x in m.get("balancing_notes", [])[:2]], "a": [short(x, 170) for x in m.get("accessibility_notes", [])[:2]],
         "r": [[r["target"], r["type"]] for r in m.get("relationships", [])[:8]]}
    sp = m.get("scope_profile")
    if sp:
        e["k"] = {k: sp[k] for k in ("mvp_role", "implementation_cost", "tuning_cost", "networking_risk", "save_load_risk", "ui_risk") if k in sp}
    return {k: v for k, v in e.items() if v not in ([], {}, "")}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    mech = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(sys.argv[1], "data", "*", "*.json")))]
    cat = {m["id"]: entry(m) for m in mech}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"note": "Built by tool/build_mechanics_catalog.py from an open CC0 dataset. Keys: n name, al aliases, c category, g genres, d purpose, s required systems, p parameters with typical range, e edge cases, b common bugs, t balance, a accessibility, r relationships [target, type], k cost profile. Search it with python Claude/hooks/mechanic_catalog.py.",
               "count": len(cat), "mechanics": cat}, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, separators=(",", ":"))
    print("%d mechanics, %d KB" % (len(cat), os.path.getsize(OUT) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
