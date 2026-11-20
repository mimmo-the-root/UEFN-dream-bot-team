#!/usr/bin/env python3
"""Tests for the routing keys of tools/kit_config.py and tools/router_settings_sync.py (temp dirs only)."""
import json, os, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kit_config as kc  # noqa: E402
import router_settings_sync as rs  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


check(rs.build_payload(None) == {"mode": "auto", "safety_check": "short", "free_accept_edits": False, "spread": True, "chain": []}, "defaults payload")
check(rs.build_payload({"mode": "paid", "safety_check": "off", "chain": ["a", "b"], "spread": False, "free_accept_edits": True})
      == {"mode": "paid", "safety_check": "full", "free_accept_edits": True, "spread": False, "chain": ["a", "b"]}, "valid payload")
check(rs.build_payload({"safety_check": "mixed-safe"})["safety_check"] == "full", "mixed-safe maps to full")
p = rs.build_payload({"mode": "turbo", "spread": "yes", "chain": [1], "safety_check": "x"})
check(p == rs.build_payload({}), "invalid values fall back to defaults")
check(set(rs.build_payload({})) <= {"mode", "safety_check", "free_accept_edits", "spread", "chain", "enabled", "pinning", "safety_samples"}, "only fields the router accepts")

with tempfile.TemporaryDirectory() as d:
    kc.set("routing.mode", "free", d)
    check(kc.get("routing.mode", d) == "free", "set mode")
    try:
        kc.set("routing.safety_check", "off", d)
        check(False, "safety_check needs confirm")
    except PermissionError:
        pass
    kc.set("routing.safety_check", "mixed-safe", d, confirm=True)
    check(rs.payload_for_project(d)["mode"] == "free" and rs.payload_for_project(d)["safety_check"] == "full", "payload from project")
    p = kc.path(d)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"routing": {"mode": "bogus", "chain": "x"}}, f)
    cfg, note = kc.load(d)
    check(cfg["routing"]["mode"] == "auto" and cfg["routing"]["chain"] == [] and note, "invalid file values fall back with a note")

shipped = json.load(open(os.path.join(ROOT, "project-template", kc.REL), encoding="utf-8"))
check(shipped == kc.defaults() and not kc.validate(shipped), "template in step with defaults")

if fails:
    print("FAIL:\n" + "\n".join(fails))
    sys.exit(1)
print("ok")
