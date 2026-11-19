#!/usr/bin/env python3
"""T-025 / pkg-215: budget_governor.py — flip routing mode between "plan" and "free" based on budget state.

The router (dream_router.py) calls governor() to ask which mode to use for the next request.
This keeps the budget decision in one place and makes it testable without touching the router.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

# Budget state file (written by budget_read.py / budget_decide.py consumers)
BUDGET_FILE = Path(__file__).resolve().parent.parent / "budget_state.json"

# Thresholds
WEEKLY_PCT_PLAN_MAX = 50.0  # at or above this, route free
RESET_GRACE_SECONDS = 0  # no grace: reset time is the switch point


def _now_ts():
    return int(time.time())


def _load_state():
    """Load budget state from disk; return {} if missing/unreadable."""
    try:
        with open(BUDGET_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _reset_passed(state):
    """True if the limit's reset time has already passed (now >= resets_at)."""
    limit = state.get("limit") or {}
    resets_at = limit.get("resets_at")
    if resets_at is None:
        return True  # no reset time = treat as reset
    if isinstance(resets_at, str):
        try:
            dt = datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp() <= _now_ts()
        except ValueError:
            return True
    try:
        return float(resets_at) <= _now_ts()
    except (TypeError, ValueError):
        return True


def governor(state=None):
    """Return "free" or "plan" for the current budget state.

    Decision order:
      1. limit hit -> free (no reset passed)
      2. limit hit + reset passed -> plan
      3. weekly_used_pct >= 50 -> free
      4. otherwise -> plan
    """
    if state is None:
        state = _load_state()
    if not isinstance(state, dict):
        return "plan"

    limit = state.get("limit") or {}
    budget = state.get("budget") or {}
    limit_state = limit.get("state")
    resets_at = limit.get("resets_at")
    passed = _reset_passed(state)

    # 1. limit hit before reset -> free
    if limit_state == "hit" and not passed:
        return "free"
    # 2. limit hit after reset -> plan
    if limit_state == "hit" and passed:
        return "plan"
    # 3. usage threshold
    pct = budget.get("weekly_used_pct")
    if pct is not None:
        try:
            if float(pct) >= WEEKLY_PCT_PLAN_MAX:
                return "free"
        except (TypeError, ValueError):
            pass
    # 4. default
    return "plan"


def governor_mode(state=None):
    """Alias kept for callers that want the explicit name."""
    return governor(state)


if __name__ == "__main__":
    print(governor())