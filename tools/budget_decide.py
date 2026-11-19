#!/usr/bin/env python3
"""Budget decision function.

Given the state from budget_read.py, returns 'plan' or 'free':
- 'free' when limit is hit OR weekly_used_pct >= 50
- 'plan' again after the reset time (when limit is no longer hit)
"""

from datetime import datetime, timezone


def decide(state: dict) -> str:
    """Decide whether to use plan or free models.

    Args:
        state: Dict with keys 'limit' and 'budget' from read_budget_and_limit().
               limit: dict with keys state, hit_at, resets_at, kind, session_id
               budget: dict with weekly_used_pct (float 0-100 or None)

    Returns:
        'plan' or 'free'
    """
    limit = state.get("limit", {})
    budget = state.get("budget", {})

    # Check if limit is currently hit
    limit_state = limit.get("state")
    if limit_state == "hit":
        return "free"

    # Check weekly used percentage
    weekly_used_pct = budget.get("weekly_used_pct")
    if weekly_used_pct is not None and weekly_used_pct >= 50.0:
        return "free"

    # If limit was hit but has reset (resets_at in the past), go back to plan
    resets_at = limit.get("resets_at")
    if resets_at:
        try:
            reset_time = None
            if isinstance(resets_at, (int, float)):
                reset_time = datetime.fromtimestamp(resets_at, tz=timezone.utc)
            elif isinstance(resets_at, str):
                reset_time = datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
            if reset_time and reset_time.tzinfo is None:
                reset_time = reset_time.replace(tzinfo=timezone.utc)
            if reset_time and datetime.now(timezone.utc) > reset_time:
                # Limit has reset, check if still hit
                if limit_state != "hit":
                    return "plan"
        except (ValueError, TypeError):
            pass

    # Default: plan
    return "plan"


if __name__ == "__main__":
    # Quick manual test
    test_cases = [
        ({"limit": {"state": "hit"}, "budget": {}}, "free"),
        ({"limit": {"state": "ok"}, "budget": {"weekly_used_pct": 60.0}}, "free"),
        ({"limit": {"state": "ok"}, "budget": {"weekly_used_pct": 30.0}}, "plan"),
        ({"limit": {"state": "hit", "resets_at": "2020-01-01T00:00:00Z"}, "budget": {}}, "free"),
        ({"limit": {"state": "ok", "resets_at": "2020-01-01T00:00:00Z"}, "budget": {}}, "plan"),
    ]

    for state, expected in test_cases:
        result = decide(state)
        status = "OK" if result == expected else "FAIL"
        print(f"{status}: decide({state}) = {result} (expected {expected})")