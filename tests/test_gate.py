#!/usr/bin/env python3
"""Tests for tools/gate.py on temp files with fake commands."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import gate

ok = True
def check(name, cond):
    global ok
    print(("ok   " if cond else "FAIL ") + name)
    ok = ok and cond

with tempfile.TemporaryDirectory() as d:
    plan = {"items": [
        {"id": "T-1", "command": "python3 -c \"import sys; sys.exit(0)\""},
        {"id": "T-2", "command": "python3 -c \"import sys; sys.exit(1)\"", "tier": "T1", "outputs": ["o.txt"]},
        {"id": "T-3", "command": "rm -rf /tmp/never"},
    ]}
    cs = gate.build_contracts(plan)
    check("contract fields", set(cs[0]) == {"id", "inputs", "outputs", "acceptance", "tier"} and cs[0]["tier"] == "T2" and cs[1]["tier"] == "T1")
    st = os.path.join(d, "s.json")
    check("pass", gate.gate(cs[0], st, cwd=d)[0] == "PASS")
    check("dry-run prints only", gate.gate(cs[1], st, dry_run=True, cwd=d)[0] == "DRY-RUN" and not os.path.exists(st))
    v = [gate.gate(cs[1], st, cwd=d)[0] for _ in range(5)]
    check("fail,fail,blocked,blocked", v == ["FAIL", "FAIL", "BLOCKED", "BLOCKED", "BLOCKED"])
    check("counter in file", json.load(open(st))["T-2"] == 3)
    check("disallowed command fails", gate.gate(cs[2], st, cwd=d)[0] == "FAIL")
    open(os.path.join(d, "o.txt"), "w").close()
    cs[1]["acceptance"] = "python3 -c pass"
    check("blocked stays blocked", gate.gate(cs[1], st, cwd=d)[0] == "BLOCKED")
    cs[1]["id"] = "T-9"
    check("missing output then present", gate.gate(dict(cs[1], outputs=["nope"]), st, cwd=d)[0] == "FAIL"
          and gate.gate(cs[1], st, cwd=d)[0] == "PASS")
sys.exit(0 if ok else 1)
