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


def flip(project_dir, routing_path, log_path=None, state=None):
    """Read LIMIT.json + budget.json (budget_read), decide plan or free (the decision above, which also returns to plan once
    the reset time has passed) and write the mode into routing.json: the other keys are kept, the file is written to a temp
    file and renamed. Only a routing.json that is already on "plan" or "free" is flipped: "auto" (plan, then free) and
    "safe" are the owner's choice and are left alone. Appends one log line per flip. Never prints or logs a key or token.
    Returns (old_mode, new_mode, flipped)."""
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    if state is None:
        from budget_read import read_budget_and_limit
        state = read_budget_and_limit(project_dir)
    new = governor(state)
    try:
        with open(routing_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        return None, new, False
    if not isinstance(cfg, dict):
        return None, new, False
    old = cfg.get("mode")
    if old not in ("plan", "free") or old == new:
        return old, new, False
    cfg["mode"] = new
    tmp = str(routing_path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=1)
    os.replace(tmp, routing_path)
    if log_path:
        pct = (state.get("budget") or {}).get("weekly_used_pct")
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("%s mode %s -> %s (limit=%s weekly_used_pct=%s)\n" % (
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), old, new,
                (state.get("limit") or {}).get("state"), pct))
    return old, new, True


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:  # python tools/budget_governor.py <project_dir> <routing.json> [log file]
        print(flip(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
    else:
        print(governor())
