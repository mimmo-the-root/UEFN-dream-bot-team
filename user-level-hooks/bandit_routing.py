"""Bandit routing (T-036): Thompson sampling per (package type, model). Pure and standard library only.

Reward of a try = accepted (0/1) divided by its cost (relative cost, >= COST_FLOOR). The arm keeps Beta(a, b) for
acceptance and a running mean cost; a model is scored as sampled acceptance / mean cost.
Stats live in bandit.json under DREAM_ROUTER_HOME. Deterministic with an injected rng (random.Random)."""
import json, os, random

COST_FLOOR = 0.01
FILE = "bandit.json"


def home():
    return os.environ.get("DREAM_ROUTER_HOME") or os.path.join(os.path.expanduser("~"), ".dream-router")


def _path(path=None):
    return path or os.path.join(home(), FILE)


def load(path=None):
    try:
        with open(_path(path), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save(stats, path=None):
    p = _path(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, indent=1, sort_keys=True)
    os.replace(tmp, p)


def _key(ptype, model):
    return "%s|%s" % (ptype or "default", model)


def arm(stats, ptype, model):
    return stats.get(_key(ptype, model)) or {"acc": 0, "rej": 0, "cost": 0.0, "n": 0}


def record(stats, ptype, model, accepted, cost=1.0):
    """Add one try to the stats (in place) and return them."""
    a = stats.setdefault(_key(ptype, model), {"acc": 0, "rej": 0, "cost": 0.0, "n": 0})
    a["acc" if accepted else "rej"] += 1
    a["n"] += 1
    a["cost"] = round(a["cost"] + (max(float(cost), COST_FLOOR) - a["cost"]) / a["n"], 6)
    return stats


def score(stats, ptype, model, rng):
    a = arm(stats, ptype, model)
    theta = rng.betavariate(1 + a["acc"], 1 + a["rej"])  # uniform Beta(1,1) prior: untried models still get explored
    return theta / (a["cost"] if a["n"] else 1.0)


def rank(stats, ptype, models, rng=None):
    """The models best first for this package type (Thompson sample of acceptance per cost)."""
    rng = rng or random.Random()
    scored = [(score(stats, ptype, m, rng), i, m) for i, m in enumerate(models)]
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [m for _, _, m in scored]


def pick(stats, ptype, models, rng=None):
    r = rank(stats, ptype, models, rng)
    return r[0] if r else None
