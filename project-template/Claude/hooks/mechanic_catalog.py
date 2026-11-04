#!/usr/bin/env python3
"""mechanic_catalog.py - look up a game mechanic, and check a set of mechanics before building. Zero AI tokens; reads reference/mechanics-catalog.json.

  python Claude/hooks/mechanic_catalog.py find WORDS [--genre G] [--cat C]   the mechanics that match, one line each
  python Claude/hooks/mechanic_catalog.py show ID                           the card: purpose, parameters and ranges, edge cases, bugs, balance, accessibility, links, and how UEFN does it
  python Claude/hooks/mechanic_catalog.py check ID ID ID ...                missing systems and required mechanics, conflicts, cost and risk, a first slice to build

The "UEFN" line comes from reference/mechanics-uefn.json: what the kit has verified in the editor (a recipe, a device, a Verse way) or "not checked yet".
The catalog is advice for planning, not design truth: cost scores are not production estimates."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = [os.path.join(HERE, "..", "reference"), os.path.join(HERE, "..", "..", "Claude", "reference")]


def load(name):
    for d in REF:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return json.load(open(p, encoding="utf-8-sig"))
    return {}


def cat():
    return load("mechanics-catalog.json").get("mechanics", {})


def uefn(i):
    u = load("mechanics-uefn.json").get("mechanics", {}).get(i)
    if not u:
        return "not checked in UEFN yet"
    how = {"recipe": "recipe '%s'", "device": "device %s", "verse": "Verse: %s", "no": "no direct way: %s"}.get(u.get("how"), "%s") % (u.get("what") or u.get("recipe") or "")
    return how + ((" (" + u["note"] + ")") if u.get("note") else "") + ("" if u.get("verified") else " [not verified in the editor]")


def find(words, genre=None, category=None):
    c, ws, out = cat(), [w.lower() for w in words], []
    for i, e in c.items():
        if genre and genre not in e.get("g", []):
            continue
        if category and e.get("c") != category:
            continue
        hay = " ".join([i, e["n"]] + e.get("al", []) + [e.get("d", "")]).lower()
        score = sum((3 if w in (e["n"].lower() + " " + i) else 1) for w in ws if w in hay)
        if score or not ws:
            out.append((-score, i))
    return [i for _, i in sorted(out)][:20]


def card(i):
    e = cat().get(i)
    if not e:
        return "No mechanic %s. Try: find WORDS" % i
    L = ["%s  (%s)  %s" % (e["n"], i, ", ".join(e.get("g", [])[:6])), e.get("d", ""), "UEFN: " + uefn(i)]
    if e.get("s"):
        L.append("Needs: " + ", ".join(e["s"]))
    if e.get("p"):
        L.append("Parameters: " + "; ".join(e["p"]))
    for key, title in (("e", "Edge cases"), ("b", "Common bugs"), ("t", "Balance"), ("a", "Accessibility")):
        for x in e.get(key, []):
            L.append("%s: %s" % (title, x))
    if e.get("r"):
        L.append("Links: " + ", ".join("%s %s" % (t, tgt) for tgt, t in e["r"]))
    if e.get("k"):
        L.append("Cost: " + ", ".join("%s %s" % (k.replace("_", " "), v) for k, v in e["k"].items()))
    return "\n".join(L)


def check(ids):
    c = cat()
    unknown = [i for i in ids if i not in c]
    ids = [i for i in ids if i in c]
    sel = set(ids)
    L, hard, soft, missing, systems = [], [], [], [], {}
    for i in ids:
        e = c[i]
        for s in e.get("s", []):
            systems.setdefault(s, []).append(i)
        for tgt, t in e.get("r", []):
            if t == "requires" and tgt not in sel:
                missing.append((i, tgt))
            if tgt in sel and t == "conflicts_with":
                hard.append((i, tgt))
            if tgt in sel and t == "soft_conflicts_with":
                soft.append((i, tgt))
    if unknown:
        L.append("Unknown ids: " + ", ".join(unknown))
    if missing:
        L.append("Missing mechanics (required by one you chose): " + "; ".join("%s needs %s" % (a, b) for a, b in sorted(set(missing))))
    if hard:
        L.append("CONFLICTS: " + "; ".join("%s vs %s" % p for p in sorted(set(tuple(sorted(x)) for x in hard))))
    if soft:
        L.append("Decide who owns what (soft conflicts): " + "; ".join("%s / %s" % p for p in sorted(set(tuple(sorted(x)) for x in soft))))
    shared = sorted(s for s, v in systems.items() if len(v) > 1)
    if shared:
        L.append("Systems several of them share (build once): " + ", ".join(shared[:12]))
    sc = [c[i].get("k", {}) for i in ids]
    cost = sum(k.get("implementation_cost", 0) + k.get("tuning_cost", 0) for k in sc)
    risky = [i for i in ids if c[i].get("k", {}).get("networking_risk", 0) >= 4 or c[i].get("k", {}).get("save_load_risk", 0) >= 4]
    L.append("Cost: %d mechanics, implementation plus tuning %d (a rough guide, not hours)" % (len(ids), cost))
    if risky:
        L.append("Watch networking or save/load: " + ", ".join(risky))
    core = [i for i in ids if c[i].get("k", {}).get("mvp_role") == "core"]
    L.append("First slice to build: " + (", ".join(core) if core else ", ".join(ids[:3])))
    nu = [i for i in ids if uefn(i).startswith("not checked")]
    if nu:
        L.append("Not checked in UEFN yet: " + ", ".join(nu))
    return "\n".join(L)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    g = c_ = None
    if "--genre" in rest:
        g = rest[rest.index("--genre") + 1]; rest = [x for x in rest if x not in ("--genre", g)]
    if "--cat" in rest:
        c_ = rest[rest.index("--cat") + 1]; rest = [x for x in rest if x not in ("--cat", c_)]
    if not cat():
        print("No catalog: reference/mechanics-catalog.json is missing (run /kit-update).")
        return 1
    if cmd == "find":
        for i in find(rest, g, c_):
            e = cat()[i]
            print("%s | %s | %s" % (i, e["n"], e.get("d", "")[:110]))
    elif cmd == "show":
        print(card(rest[0]))
    elif cmd == "check":
        print(check(rest))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
