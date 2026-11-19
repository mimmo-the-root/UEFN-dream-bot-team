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


if __name__ == "__main__":
    test_hit_before_reset_free()
    test_hit_after_reset_plan()
    test_weekly_over_50_free()
    test_weekly_under_50_plan()
    test_default_plan()
    print("All tests passed")