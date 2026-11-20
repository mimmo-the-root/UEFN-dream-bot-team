"""Shadow sampling (T-039): about 10% of free packages are also judged on the paid model, to measure the loss % per package type.
Pure and standard library only. Deterministic with an injected rng (random.Random).
Never samples when the budget governor says free-only. A hard cap per day bounds the paid spend.
Stats live in shadow.json under DREAM_ROUTER_HOME: {"types": {ptype: {"n", "loss"}}, "days": {"YYYY-MM-DD": count}}.
Loss of one sample is 0..1 (0 = the free answer was as good as the paid one, 1 = clearly worse)."""
import json, os, random, time

FILE = "shadow.json"
DEFAULT_RATE = 0.10
DEFAULT_DAILY_CAP = 20


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


def save(state, path=None):
    p = _path(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    os.replace(tmp, p)


def today(now=None):
    return time.strftime("%Y-%m-%d", time.localtime(now if now is not None else time.time()))


def used_today(state, day=None):
    return int((state.get("days") or {}).get(day or today(), 0))


def decide(state, ptype, free_only=False, rng=None, rate=DEFAULT_RATE, cap=DEFAULT_DAILY_CAP, day=None):
    """True = also judge this free package on the paid model. Counts the sample against today's cap when it says True."""
    if free_only:
        return False
    day = day or today()
    if used_today(state, day) >= int(cap):
        return False
    if float(rate) <= 0 or (rng or random).random() >= float(rate):
        return False
    days = state.setdefault("days", {})
    if len(days) > 30 and day not in days:  # keep the file small: old days drop out
        days.clear()
    days[day] = days.get(day, 0) + 1
    return True


def record(state, ptype, loss):
    """One judged sample of a package type; loss is clamped to 0..1."""
    t = state.setdefault("types", {}).setdefault(ptype or "default", {"n": 0, "loss": 0.0})
    t["n"] = int(t.get("n", 0)) + 1
    t["loss"] = float(t.get("loss", 0.0)) + min(1.0, max(0.0, float(loss)))
    return t


def report(state):
    """{ptype: {"n": samples, "loss_pct": mean loss in percent}}"""
    out = {}
    for k, t in sorted((state.get("types") or {}).items()):
        n = int(t.get("n", 0))
        out[k] = {"n": n, "loss_pct": round(100.0 * float(t.get("loss", 0.0)) / n, 1) if n else 0.0}
    return out
