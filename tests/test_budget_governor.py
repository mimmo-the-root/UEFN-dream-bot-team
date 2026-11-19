#!/usr/bin/env python3
"""T-055 pkg-215: tests for tools/budget_governor.governor()

Decision matrix (from code):
1. limit.state == "hit" and reset not passed -> free
2. limit.state == "hit" and reset passed -> plan
3. budget.weekly_used_pct >= 50 -> free
4. default -> plan
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from budget_governor import governor


def mkstate(limit_state=None, resets_at=None, weekly_pct=None):
    s = {}
    if limit_state is not None:
        s["limit"] = {"state": limit_state}
        if resets_at is not None:
            s["limit"]["resets_at"] = resets_at
    if weekly_pct is not None:
        s["budget"] = {"weekly_used_pct": weekly_pct}
    return s


def test_hit_before_reset_free():
    now = int(__import__("time").time())
    assert governor(mkstate("hit", now + 3600, 10)) == "free", "limit hit before reset => free"


def test_hit_after_reset_plan():
    now = int(__import__("time").time())
    assert governor(mkstate("hit", now - 3600, 10)) == "plan", "limit hit after reset => plan"


def test_weekly_over_50_free():
    assert governor(mkstate(None, None, 50.0)) == "free", "weekly 50 => free"
    assert governor(mkstate(None, None, 99)) == "free", "weekly 99 => free"


def test_weekly_under_50_plan():
    assert governor(mkstate(None, None, 49)) == "plan", "weekly 49 => plan"
    assert governor(mkstate(None, None, 0)) == "plan", "weekly 0 => plan"


def test_default_plan():
    assert governor(mkstate()) == "plan", "no state => plan"


def test_flip_both_ways_on_a_temp_copy():
    """T-025: a simulated limit hit and a reset flip routing.json both ways; other keys kept; one log line per flip; no restart."""
    import json, tempfile, time
    from budget_governor import flip
    d = tempfile.mkdtemp()
    routing = os.path.join(d, "routing.json")
    log = os.path.join(d, "budget-governor.log")
    json.dump({"mode": "plan", "spread": True, "chain": ["a", "b"], "KEEP": 1}, open(routing, "w"))
    now = int(time.time())
    hit = {"limit": {"state": "hit", "resets_at": now + 3600}, "budget": {"weekly_used_pct": 10}}
    assert flip(d, routing, log, hit) == ("plan", "free", True)
    cfg = json.load(open(routing))
    assert cfg["mode"] == "free" and cfg["KEEP"] == 1 and cfg["chain"] == ["a", "b"], cfg
    assert flip(d, routing, log, hit) == ("free", "free", False), "no change = no flip and no log line"
    reset = {"limit": {"state": "hit", "resets_at": now - 60}, "budget": {"weekly_used_pct": 10}}
    assert flip(d, routing, log, reset) == ("free", "plan", True), "back to plan at the reset"
    lines = open(log).read().strip().split("\n")
    assert len(lines) == 2 and "plan -> free" in lines[0] and "free -> plan" in lines[1], lines
    for mode in ("safe", "auto"):  # the owner's choice is never overridden
        json.dump({"mode": mode}, open(routing, "w"))
        assert flip(d, routing, log, hit)[2] is False
        assert json.load(open(routing))["mode"] == mode
    assert not os.path.exists(routing + ".tmp")


if __name__ == "__main__":
    test_flip_both_ways_on_a_temp_copy()
    test_hit_before_reset_free()
    test_hit_after_reset_plan()
    test_weekly_over_50_free()
    test_weekly_under_50_plan()
    test_default_plan()
    print("All tests passed")