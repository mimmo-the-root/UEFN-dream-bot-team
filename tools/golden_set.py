#!/usr/bin/env python3
"""Golden set: 20 small packages with known answers, deterministic checks (no LLM judge).

Usage:
  python3 tools/golden_set.py --model NAME='shell command' [--model ...] [--out result.json]
The command receives the prompt on stdin and prints the answer on stdout.
Library: run_golden(models) where models = {name: callable(prompt) -> str}.
"""
import argparse, json, os, re, subprocess, sys, time

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "golden_set.json")


def load_set(path=None):
    with open(path or DATA, encoding="utf-8") as f:
        return json.load(f)["packages"]


def _norm(s):
    return re.sub(r"[\s.!\"'`]+$", "", re.sub(r"^[\s\"'`]+", "", s)).strip().lower()


def check(answer, spec):
    """Return True if answer satisfies spec {type, value}."""
    t, v, a = spec["type"], spec["value"], (answer or "")
    if t == "equals":
        return _norm(a) == v.lower()
    if t == "equals_exact":
        return a.strip() == v
    if t == "contains":
        return v in a
    if t == "contains_all":
        return all(x in a for x in v.split("|"))
    if t == "regex":
        return re.search(v, a, re.M) is not None
    if t == "number":
        nums = re.findall(r"-?\d+(?:\.\d+)?", a)
        return len(nums) == 1 and float(nums[0]) == float(v)
    if t == "json_key":
        k, _, want = v.partition("=")
        m = re.search(r"\{.*\}", a, re.S)
        try:
            obj = json.loads(m.group(0)) if m else None
        except ValueError:
            return False
        return isinstance(obj, dict) and k in obj and json.dumps(obj[k]) == want
    raise ValueError("unknown check type: " + t)


def run_golden(models, packages=None):
    """models: {name: callable(prompt)->str}. Returns result dict with per-model pass counts."""
    packages = packages or load_set()
    out = {"total": len(packages), "models": {}}
    for name, fn in models.items():
        res, passed = [], 0
        for p in packages:
            try:
                ans, err = fn(p["prompt"]), None
                ok = check(ans if isinstance(ans, str) else str(ans), p["check"])
            except Exception as e:  # a failing model is a failed check, not a crash
                ok, err = False, "%s: %s" % (type(e).__name__, e)
            passed += ok
            res.append({"id": p["id"], "pass": bool(ok), **({"error": err} if err else {})})
        out["models"][name] = {"passed": passed, "total": len(packages), "results": res}
    return out


def command_model(cmd, timeout=120):
    def fn(prompt):
        r = subprocess.run(cmd, shell=True, input=prompt, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError("exit %d" % r.returncode)
        return r.stdout
    return fn


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", action="append", default=[], help="NAME=shell command (reads prompt on stdin)")
    ap.add_argument("--out", help="write result JSON to this path")
    a = ap.parse_args(argv)
    if not a.model:
        ap.error("at least one --model NAME=COMMAND is required")
    models = {}
    for m in a.model:
        n, sep, c = m.partition("=")
        if not sep or not n or not c:
            ap.error("bad --model %r, expected NAME=COMMAND" % m)
        models[n] = command_model(c)
    res = run_golden(models)
    res["generated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    for n, r in res["models"].items():
        print("%s: %d/%d" % (n, r["passed"], r["total"]))
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=1)
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
