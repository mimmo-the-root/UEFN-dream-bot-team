#!/usr/bin/env python3
"""Economy simulator for tycoon / arena style maps (v1.109). Lives in your profile (~/.claude/hooks).

  python economy_sim.py init <file.json>         write an example economy to fill in (never overwrites)
  python economy_sim.py run  <file.json> [--json] simulate a player who always buys the best-payback generator

The file describes the numbers you plan in the game:
  session_minutes      how long one visit is expected to last
  base_income_per_sec  income with nothing bought
  generators           [{name, base_cost, growth, income, max}] : cost of the n-th copy = base_cost * growth**n
  targets              [{name, cost}] : milestones, reached when the TOTAL EARNED passes the cost

It is a planning aid, not a prediction: real players click, wait, die and quit. Use it to see whether a milestone arrives in
minutes or in days, and which generator is never worth buying. Pure arithmetic, no AI, no editor.
"""
import json
import os
import sys

EXAMPLE = {
    "session_minutes": 15,
    "base_income_per_sec": 1,
    "generators": [
        {"name": "Drill", "base_cost": 10, "growth": 1.15, "income": 0.5, "max": 50},
        {"name": "Refinery", "base_cost": 200, "growth": 1.18, "income": 8, "max": 25},
    ],
    "targets": [
        {"name": "First upgrade", "cost": 100},
        {"name": "Rebirth", "cost": 20000},
    ],
}
HORIZON = 6 * 3600  # seconds simulated at most


def simulate(cfg, horizon=HORIZON):
    gens = [dict(g, owned=0) for g in cfg.get("generators", [])]
    income = float(cfg.get("base_income_per_sec", 0))
    bal = float(cfg.get("start_currency", 0))
    earned = 0.0
    targets = sorted(({"name": t["name"], "cost": float(t["cost"]), "t": None} for t in cfg.get("targets", [])), key=lambda x: x["cost"])
    first_buy = {}
    for sec in range(1, horizon + 1):
        bal += income
        earned += income
        for t in targets:
            if t["t"] is None and earned >= t["cost"]:
                t["t"] = sec
        # best payback among generators not at max; save for it when it is not affordable yet
        best = None
        for g in gens:
            if g["owned"] >= g.get("max", 10 ** 9) or g["income"] <= 0:
                continue
            cost = g["base_cost"] * g.get("growth", 1.0) ** g["owned"]
            pay = cost / g["income"]
            if best is None or pay < best[0]:
                best = (pay, g, cost)
        while best and bal >= best[2]:
            bal -= best[2]
            best[1]["owned"] += 1
            income += best[1]["income"]
            first_buy.setdefault(best[1]["name"], sec)
            best = None
            for g in gens:
                if g["owned"] >= g.get("max", 10 ** 9) or g["income"] <= 0:
                    continue
                cost = g["base_cost"] * g.get("growth", 1.0) ** g["owned"]
                pay = cost / g["income"]
                if best is None or pay < best[0]:
                    best = (pay, g, cost)
        if all(t["t"] is not None for t in targets) and sec >= 60:
            break
    return {"targets": targets, "generators": [{"name": g["name"], "owned": g["owned"], "first_buy": first_buy.get(g["name"])} for g in gens],
            "income_end": income, "seconds": sec}


def verdicts(cfg, res):
    """Plain-language flags. Empty list = nothing odd."""
    sess = float(cfg.get("session_minutes", 15)) * 60
    out = []
    for i, t in enumerate(res["targets"]):
        if t["t"] is None:
            out.append("'%s' is not reached in %d hours: the curve is too flat or the cost too high" % (t["name"], HORIZON // 3600))
        elif i > 0 and t["t"] < 0.1 * sess:  # the first milestone is meant to come early
            out.append("'%s' arrives after %s, in the first tenth of a visit: too easy to feel like a goal" % (t["name"], fmt(t["t"])))
        elif t["t"] > 3 * sess:
            out.append("'%s' needs %s, more than three visits: most players will quit first" % (t["name"], fmt(t["t"])))
    for g in res["generators"]:
        if g["first_buy"] is None:
            out.append("generator '%s' is never bought: its price is too high for what it gives" % g["name"])
    return out


def fmt(s):
    s = int(s)
    if s < 120:
        return "%ds" % s
    if s < 7200:
        return "%dm%02ds" % (s // 60, s % 60)
    return "%.1fh" % (s / 3600.0)


def main(argv):
    if len(argv) < 2 or argv[0] not in ("init", "run"):
        print(__doc__)
        return 2
    path = argv[1]
    if argv[0] == "init":
        if os.path.exists(path):
            print("%s already exists: left alone" % path)
            return 1
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(EXAMPLE, open(path, "w", encoding="utf-8", newline="\n"), indent=2)
        print("written: %s (example numbers: replace them with your game's)" % path)
        return 0
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print("cannot read %s: %s" % (path, e))
        return 2
    res = simulate(cfg)
    flags = verdicts(cfg, res)
    if "--json" in argv:
        print(json.dumps({"result": res, "flags": flags}, indent=2))
        return 0
    print("Simulated player: buys the best-payback generator, no clicks, no deaths. Visit length: %s." % fmt(float(cfg.get("session_minutes", 15)) * 60))
    for t in res["targets"]:
        print("  milestone %-20s cost %-10g reached after %s" % (t["name"], t["cost"], fmt(t["t"]) if t["t"] else "never"))
    for g in res["generators"]:
        print("  generator %-20s bought %-3d first at %s" % (g["name"], g["owned"], fmt(g["first_buy"]) if g["first_buy"] else "never"))
    print("flags: " + ("; ".join(flags) if flags else "none"))
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
