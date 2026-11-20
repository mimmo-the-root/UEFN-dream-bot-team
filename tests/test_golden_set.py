#!/usr/bin/env python3
"""Tests for tools/golden_set.py: fake models only, no network."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import golden_set as g

ANS = {
 "arith-add": "42", "arith-mul": "144", "arith-div": "18", "capital-it": "Rome.",
 "reverse": "esrev", "upper": "FORTNITE", "count-letters": "6", "sort-nums": "1, 3, 5, 9",
 "max-list": "19", "json-key": '{"ok": true}', "json-sum": '{"sum": 42}',
 "verse-func": "Add(A:int, B:int):int =", "verse-var": "var Score : int = 0",
 "verse-import": "using { /Fortnite.com/Devices }", "verse-log": "Print", "not-contains": "Red",
 "weekday": "Tuesday", "month-days": "28", "bool-logic": "False", "prefix-echo": "READY-7",
}

def main():
    pk = g.load_set()
    assert len(pk) == 20 and len({p["id"] for p in pk}) == 20
    assert set(ANS) == {p["id"] for p in pk}
    by = {p["prompt"]: ANS[p["id"]] for p in pk}
    good = lambda prompt: by[prompt]
    bad = lambda prompt: "I do not know"
    def flaky(prompt):
        if prompt == pk[0]["prompt"]:
            raise RuntimeError("boom")
        return by[prompt]
    r = g.run_golden({"good": good, "bad": bad, "flaky": flaky})
    assert r["models"]["good"]["passed"] == 20, r["models"]["good"]
    assert r["models"]["bad"]["passed"] == 0
    assert r["models"]["flaky"]["passed"] == 19
    assert "error" in r["models"]["flaky"]["results"][0]
    # check edge cases
    assert not g.check("42 and 43", {"type": "number", "value": "42"})
    assert not g.check('{"ok": "true"}', {"type": "json_key", "value": "ok=true"})
    # CLI with command model and --out
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "r.json")
        cmd = "%s -c \"print(42)\"" % sys.executable
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "golden_set.py"),
                            "--model", "const=" + cmd, "--out", out], capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr
        j = json.load(open(out))
        assert j["models"]["const"]["passed"] == 1 and j["total"] == 20, j["models"]["const"]["passed"]
        assert "const: 1/20" in p.stdout
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "golden_set.py")], capture_output=True, text=True)
    assert p.returncode != 0
    print("ok")

main()
