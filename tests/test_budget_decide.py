#!/usr/bin/env python3
"""Tests for budget_decide.py (T-025 / pkg-214)."""

import sys
import time
from pathlib import Path

# Ensure tools module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.budget_decide import decide


def test_limit_hit_returns_free():
    state = {"limit": {"state": "hit"}, "budget": {}}
    assert decide(state) == "free"


def test_weekly_used_pct_above_50_returns_free():
    state = {"limit": {"state": "ok"}, "budget": {"weekly_used_pct": 50.0}}
    assert decide(state) == "free"

    state = {"limit": {"state": "ok"}, "budget": {"weekly_used_pct": 60.0}}
    assert decide(state) == "free"


def test_weekly_used_pct_below_50_returns_plan():
    state = {"limit": {"state": "ok"}, "budget": {"weekly_used_pct": 49.9}}
    assert decide(state) == "plan"

    state = {"limit": {"state": "ok"}, "budget": {"weekly_used_pct": 0.0}}
    assert decide(state) == "plan"


def test_weekly_used_pct_none_returns_plan():
    state = {"limit": {"state": "ok"}, "budget": {"weekly_used_pct": None}}
    assert decide(state) == "plan"

    state = {"limit": {"state": "ok"}, "budget": {}}
    assert decide(state) == "plan"


def test_limit_ok_and_low_usage_returns_plan():
    state = {"limit": {"state": "ok"}, "budget": {"weekly_used_pct": 30.0}}
    assert decide(state) == "plan"


def test_empty_state_returns_plan():
    state = {}
    assert decide(state) == "plan"


def test_limit_hit_overrides_low_usage():
    state = {"limit": {"state": "hit"}, "budget": {"weekly_used_pct": 10.0}}
    assert decide(state) == "free"


def test_after_reset_returns_plan():
    """After reset time with limit ok -> plan."""
    past = int(time.time()) - 3600  # 1 hour ago
    state = {"limit": {"state": "ok", "resets_at": past}, "budget": {"weekly_used_pct": 10.0}}
    assert decide(state) == "plan"


def test_before_reset_with_hit_returns_free():
    """Before reset time with limit hit -> free."""
    future = int(time.time()) + 3600  # 1 hour from now
    state = {"limit": {"state": "hit", "resets_at": future}, "budget": {}}
    assert decide(state) == "free"


def test_before_reset_with_ok_and_low_usage_returns_plan():
    """Before reset time but limit ok and low usage -> plan (in between)."""
    future = int(time.time()) + 3600  # 1 hour from now
    state = {"limit": {"state": "ok", "resets_at": future}, "budget": {"weekly_used_pct": 10.0}}
    assert decide(state) == "plan"


def test_iso_format_reset_time():
    """Reset time in ISO format."""
    from datetime import datetime, timezone, timedelta
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    state = {"limit": {"state": "ok", "resets_at": past.isoformat()}, "budget": {"weekly_used_pct": 10.0}}
    assert decide(state) == "plan"


def test_after_reset_with_hit_still_free():
    """After reset but limit still hit -> free."""
    past = int(time.time()) - 3600
    state = {"limit": {"state": "hit", "resets_at": past}, "budget": {}}
    assert decide(state) == "free"


def main():
    """Plain-script runner (no pytest): run every test_* function and print a verdict."""
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print("ok   %s" % name)
        except Exception as e:  # noqa: BLE001
            failed.append(name)
            print("FAIL %s: %s" % (name, e))
    if failed:
        print("\nFAILED: %s" % ", ".join(failed))
        return 1
    print("\nPASS budget_decide: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
